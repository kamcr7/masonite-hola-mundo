# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN Y SEGURIDAD
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
# BASE DE DATOS E INTERFAZ
# =========================================================
def init_db():
    conn = conectar_bd(); cur = conn.cursor(buffered=True)
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))")
    cur.execute("CREATE TABLE IF NOT EXISTS permisos_perfil (id INT AUTO_INCREMENT PRIMARY KEY, idPerfil INT, idModulo INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), imgUsuario LONGTEXT)")
    cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = 'admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES ('Administrador', 1)")
        pid = cur.lastrowid
        cur.execute("INSERT INTO usuarios (strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo) VALUES ('admin', %s, %s, 1, 'admin@clinica.com')", (pid, hash_password("123456")))
    conn.commit(); cur.close(); conn.close()

def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""<div style="background:#0f4573; color:white; padding:15px; display:flex; justify-content:space-between;">
            <div><a href="/dashboard" style="color:white; text-decoration:none; margin-right:20px;">Inicio</a></div>
            <div>Bienvenido, <b>{user['u']}</b> | <a href="/logout" style="color:white; text-decoration:none;">Salir</a></div>
        </div>"""
    return f"<html><head><title>{title}</title><style>body{{font-family:sans-serif; background:#f0f2f5; margin:0;}} .card{{background:white; padding:20px; margin:20px auto; max-width:900px; border-radius:8px; box-shadow:0 2px 5px rgba(0,0,0,0.1);}} .btn-bar{{background:#0f4573; padding:10px; display:flex; gap:20px; border-radius:4px;}} .btn-bar a{{color:white; text-decoration:none; font-weight:bold;}} table{{width:100%; border-collapse:collapse; margin-top:15px;}} th,td{{padding:10px; border:1px solid #ddd; text-align:left;}} .btn{{background:#0f4573; color:white; border:none; padding:8px 15px; cursor:pointer; border-radius:4px; margin:5px;}} input, select{{padding:8px; margin:5px 0; border:1px solid #ccc; border-radius:4px; width:100%; max-width:300px;}}</style></head><body>{nav}<div class='container'>{content}</div></body></html>"

# =========================================================
# APLICACIÓN PRINCIPAL
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()

    # --- RUTA: LOGIN ---
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:350px; text-align:center;"><h2>Clínica Santa Mónica</h2><form id="fL">
            <input type="text" name="u" placeholder="Usuario" required>
            <input type="password" name="p" placeholder="Contraseña" required>
            <button type="submit" class="btn" style="width:100%;">Entrar</button></form><div id="msg" style="color:red;"></div></div>
            <script>document.getElementById('fL').onsubmit=async(e)=>{{e.preventDefault(); const res=await fetch('/api/login',{{method:'POST', body:new FormData(e.target)}}); const d=await res.json(); if(d.ok) location.href='/dashboard'; else document.getElementById('msg').innerText=d.msg;}}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    # --- API: PROCESAR LOGIN ---
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [json.dumps({"ok":True}).encode("utf-8")]
        start_response("200 OK", [("Content-Type", "application/json")]); return [json.dumps({"ok":False, "msg":"Credenciales incorrectas"}).encode("utf-8")]

    # --- VERIFICAR JWT ---
    u_data = verify_jwt(environ)
    if not u_data: start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- DASHBOARD ---
    if path == "/dashboard":
        content = f"""<div class="card"><h3>Panel de Administración</h3><div class="btn-bar">
            <a href="/perfiles">Perfil</a><a href="/modulos">Módulo</a><a href="/permisos">Permisos-Perfil</a><a href="/usuarios">Usuario</a>
            </div></div>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Dashboard", content, u_data).encode("utf-8")]

    # --- CRUD PERFILES ---
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall(); cur.close(); conn.close()
        filas = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'Si' if r['bitAdministrador'] else 'No'}</td></tr>" for r in rows])
        content = f"""<div class='card'><h3>Gestión de Perfiles</h3>
            <form id='fP'><input name='n' placeholder='Nombre Perfil' required> <label><input type='checkbox' name='a'> Admin</label> <button class='btn'>Crear</button></form>
            <table><tr><th>ID</th><th>Nombre</th><th>Admin</th></tr>{filas}</table><br><a href='/dashboard' class='btn'>Volver</a></div>
            <script>document.getElementById('fP').onsubmit=async(e)=>{{e.preventDefault(); await fetch('/api/perfiles',{{method:'POST', body:new FormData(e.target)}}); location.reload();}}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Perfiles", content, u_data).encode("utf-8")]

    # --- CRUD MÓDULOS ---
    if path == "/modulos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM modulos"); rows = cur.fetchall(); cur.close(); conn.close()
        filas = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombreModulo']}</td></tr>" for r in rows])
        content = f"""<div class='card'><h3>Gestión de Módulos</h3>
            <form id='fM'><input name='n' placeholder='Nombre Módulo' required> <button class='btn'>Añadir</button></form>
            <table><tr><th>ID</th><th>Módulo</th></tr>{filas}</table><br><a href='/dashboard' class='btn'>Volver</a></div>
            <script>document.getElementById('fM').onsubmit=async(e)=>{{e.preventDefault(); await fetch('/api/modulos',{{method:'POST', body:new FormData(e.target)}}); location.reload();}}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Modulos", content, u_data).encode("utf-8")]

    # --- CRUD USUARIOS ---
    if path == "/usuarios":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True); cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id"); rows = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall(); cur.close(); conn.close()
        opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        filas = "".join([f"<tr><td><img src='{r.get('imgUsuario','')}' width='30'></td><td>{r['strNombreUsuario']}</td><td>{r['strNombrePerfil']}</td><td>{r['strCorreo']}</td></tr>" for r in rows])
        content = f"""<div class='card'><h3>Usuarios</h3>
            <form id='fU'><input name='u' placeholder='Usuario' required><input name='p' type='password' placeholder='Clave' required><input name='e' type='email' placeholder='Email'><select name='pid'>{opts}</select> Foto: <input type='file' id='f' accept='image/*'><button class='btn'>Registrar</button></form>
            <table><tr><th>Foto</th><th>Usuario</th><th>Perfil</th><th>Correo</th></tr>{filas}</table><br><a href='/dashboard' class='btn'>Volver</a></div>
            <script>document.getElementById('fU').onsubmit=async(e)=>{{e.preventDefault(); const fd=new FormData(e.target); const file=document.getElementById('f').files[0];
            if(file){{ const r=new FileReader(); r.onloadend=async()=>{{fd.append('img', r.result); await fetch('/api/usuarios',{{method:'POST', body:fd}}); location.reload();}}; r.readAsDataURL(file); }}
            else{{ await fetch('/api/usuarios',{{method:'POST', body:fd}}); location.reload(); }}}}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Usuarios", content, u_data).encode("utf-8")]

    # --- APIS DE PROCESAMIENTO ---
    if method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        conn = conectar_bd(); cur = conn.cursor()
        if path == "/api/perfiles":
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s, %s)", (fs.getvalue("n"), 1 if fs.getvalue("a") else 0))
        elif path == "/api/modulos":
            cur.execute("INSERT INTO modulos (strNombreModulo) VALUES (%s)", (fs.getvalue("n"),))
        elif path == "/api/usuarios":
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strCorreo, idEstadoUsuario, imgUsuario) VALUES (%s,%s,%s,%s,1,%s)", 
                (fs.getvalue("u"), hash_password(fs.getvalue("p")), fs.getvalue("pid"), fs.getvalue("e"), fs.getvalue("img")))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- LOGOUT ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]

    start_response("404 Not Found", [("Content-Type", "text/html")]); return [b"<h1>Error 404: Ruta no encontrada</h1>"]