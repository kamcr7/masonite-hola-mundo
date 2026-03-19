# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@mysql.railway.internal:3306/railway')
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_SECURITY"

def hash_password(p): return hashlib.sha256((p or "").encode("utf-8")).hexdigest()
def b64url_encode(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode("utf-8")
def jwt_encode(p):
    h = b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode("utf-8"))
    py = b64url_encode(json.dumps(p).encode("utf-8"))
    s = hmac.new(JWT_SECRET.encode("utf-8"), f"{h}.{py}".encode("utf-8"), hashlib.sha256).digest()
    return f"{h}.{py}.{b64url_encode(s)}"

def verify_jwt(env):
    C = cookies.SimpleCookie(); C.load(env.get('HTTP_COOKIE', ''))
    t = C.get('token').value if 'token' in C else None
    if not t: return None
    try:
        p = json.loads(base64.urlsafe_b64decode(t.split('.')[1] + "==").decode("utf-8"))
        return p if p['exp'] > time.time() else None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

# =========================================================
# INICIALIZACIÓN
# =========================================================
def init_db():
    conn = conectar_bd(); cur = conn.cursor(buffered=True)
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))")
    cur.execute("CREATE TABLE IF NOT EXISTS permisos_perfil (id INT AUTO_INCREMENT PRIMARY KEY, idPerfil INT, idModulo INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), imgUsuario LONGTEXT)")
    
    cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = 'admin'")
    if not cur.fetchone():
        cur.execute("INSERT IGNORE INTO perfiles (id, strNombrePerfil, bitAdministrador) VALUES (1, 'Administrador', 1)")
        cur.execute("INSERT INTO usuarios (strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo) VALUES ('admin', 1, %s, 1, 'admin@clinica.com')", (hash_password("123456"),))
    conn.commit(); cur.close(); conn.close()

def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""<div style="background:#0f4573; color:white; padding:15px; display:flex; justify-content:space-between; align-items:center;">
            <div><a href="/dashboard" style="color:white; text-decoration:none; margin-right:20px;">Inicio</a></div>
            <div>Bienvenido, <b>{user['u']}</b> | <a href="/logout" style="color:white; text-decoration:none;">Salir</a></div>
        </div>"""
    return f"<html><head><title>{title}</title><style>body{{font-family:sans-serif; background:#f0f2f5; margin:0;}} .card{{background:white; padding:20px; margin:20px auto; max-width:900px; border-radius:8px; box-shadow:0 2px 5px rgba(0,0,0,0.1);}} .btn-bar{{background:#0f4573; padding:10px; display:flex; gap:20px; border-radius:4px; margin-bottom:20px;}} .btn-bar a{{color:white; text-decoration:none; font-weight:bold;}} table{{width:100%; border-collapse:collapse; margin-top:15px; background:white;}} th,td{{padding:12px; border:1px solid #ddd; text-align:left;}} th{{background:#eee;}} .btn{{background:#0f4573; color:white; border:none; padding:10px 15px; cursor:pointer; border-radius:4px;}} input, select{{padding:10px; border:1px solid #ccc; border-radius:4px; width:200px;}}</style></head><body>{nav}<div class='container'>{content}</div></body></html>"

# =========================================================
# LÓGICA DE RUTAS
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()

    # --- LOGIN ---
    if path in ["/", "/login"]:
        if method == "GET":
            content = """<div class="card" style="max-width:300px; text-align:center; margin-top:100px;"><h2>Login Clínica</h2><form id="fL">
                <input type="text" name="u" placeholder="Usuario" style="width:100%; margin-bottom:10px;" required><br>
                <input type="password" name="p" placeholder="Contraseña" style="width:100%; margin-bottom:10px;" required><br>
                <button type="submit" class="btn" style="width:100%;">Entrar</button></form><div id="msg" style="color:red; margin-top:10px;"></div></div>
                <script>document.getElementById('fL').onsubmit=async(e)=>{{e.preventDefault(); const res=await fetch('/api/login',{{method:'POST', body:new FormData(e.target)}}); const d=await res.json(); if(d.ok) location.href='/dashboard'; else document.getElementById('msg').innerText=d.msg;}}</script>"""
            start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [json.dumps({"ok":True}).encode("utf-8")]
        start_response("200 OK", [("Content-Type", "application/json")]); return [json.dumps({"ok":False, "msg":"Error"}).encode("utf-8")]

    # --- PROTECCIÓN DE RUTAS ---
    u_data = verify_jwt(environ)
    if not u_data: start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- DASHBOARD ---
    if path == "/dashboard":
        content = f"""<div class="card"><h3>Panel Principal</h3><div class="btn-bar">
            <a href="/perfiles">Perfil</a><a href="/modulos">Módulo</a><a href="/permisos">Permisos-Perfil</a><a href="/usuarios">Usuario</a>
            </div><p>Seleccione una opción del menú superior.</p></div>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Dashboard", content, u_data).encode("utf-8")]

    # --- CRUD GENÉRICO (API POST) ---
    if path.startswith("/api/save_") and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        conn = conectar_bd(); cur = conn.cursor()
        if path == "/api/save_perfil":
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s, %s)", (fs.getvalue("n"), 1 if fs.getvalue("a") else 0))
        elif path == "/api/save_modulo":
            cur.execute("INSERT INTO modulos (strNombreModulo) VALUES (%s)", (fs.getvalue("n"),))
        elif path == "/api/save_permiso":
            cur.execute("INSERT INTO permisos_perfil (idPerfil, idModulo) VALUES (%s, %s)", (fs.getvalue("pid"), fs.getvalue("mid")))
        elif path == "/api/save_usuario":
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strCorreo, idEstadoUsuario, imgUsuario) VALUES (%s,%s,%s,%s,1,%s)", 
                (fs.getvalue("u"), hash_password(fs.getvalue("p")), fs.getvalue("pid"), fs.getvalue("e"), fs.getvalue("img")))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTAS CRUD ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    
    if path == "/perfiles":
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall()
        tbl = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{r['bitAdministrador']}</td></tr>" for r in rows])
        form = "<form id='f'><input name='n' placeholder='Nombre' required> Admin: <input type='checkbox' name='a'> <button class='btn'>Guardar</button></form>"
        api = "/api/save_perfil"

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall()
        tbl = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombreModulo']}</td></tr>" for r in rows])
        form = "<form id='f'><input name='n' placeholder='Nombre Módulo' required> <button class='btn'>Guardar</button></form>"
        api = "/api/save_modulo"

    elif path == "/permisos":
        cur.execute("SELECT pp.id, p.strNombrePerfil, m.strNombreModulo FROM permisos_perfil pp JOIN perfiles p ON pp.idPerfil=p.id JOIN modulos m ON pp.idModulo=m.id"); rows = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); ps = cur.fetchall()
        cur.execute("SELECT id, strNombreModulo FROM modulos"); ms = cur.fetchall()
        tbl = "".join([f"<tr><td>{r['strNombrePerfil']}</td><td>{r['strNombreModulo']}</td></tr>" for r in rows])
        opt_p = "".join([f"<option value='{x['id']}'>{x['strNombrePerfil']}</option>" for x in ps])
        opt_m = "".join([f"<option value='{x['id']}'>{x['strNombreModulo']}</option>" for x in ms])
        form = f"<form id='f'><select name='pid'>{opt_p}</select> <select name='mid'>{opt_m}</select> <button class='btn'>Asignar</button></form>"
        api = "/api/save_permiso"

    elif path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil=p.id"); rows = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); ps = cur.fetchall()
        tbl = "".join([f"<tr><td><img src='{r.get('imgUsuario','')}' width='30'></td><td>{r['strNombreUsuario']}</td><td>{r['strNombrePerfil']}</td></tr>" for r in rows])
        opt_p = "".join([f"<option value='{x['id']}'>{x['strNombrePerfil']}</option>" for x in ps])
        form = f"<form id='f'><input name='u' placeholder='Usuario' required><input name='p' type='password' placeholder='Clave'><select name='pid'>{opt_p}</select><input type='file' id='file'> <button class='btn'>Registrar</button></form>"
        api = "/api/save_usuario"
    else:
        cur.close(); conn.close()
        if path == "/logout": start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0")]); return [b""]
        start_response("404 Not Found", []); return [b"Not Found"]

    cur.close(); conn.close()
    
    content = f"""<div class="card"><h3>{path[1:].capitalize()}</h3>
        <div class="btn-bar"><a href="/perfiles">Perfil</a><a href="/modulos">Módulo</a><a href="/permisos">Permisos-Perfil</a><a href="/usuarios">Usuario</a></div>
        {form}<table>{tbl}</table></div>
        <script>document.getElementById('f').onsubmit=async(e)=>{{
            e.preventDefault(); const fd=new FormData(e.target);
            const fl=document.getElementById('file');
            if(fl && fl.files[0]){{
                const r=new FileReader(); r.onloadend=async()=>{{ fd.append('img', r.result); await fetch('{api}',{{method:'POST', body:fd}}); location.reload(); }}; r.readAsDataURL(fl.files[0]);
            }} else {{ await fetch('{api}',{{method:'POST', body:fd}}); location.reload(); }}
        }}</script>"""
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout(path[1:], content, u_data).encode("utf-8")]