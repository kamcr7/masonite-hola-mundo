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
    try:
        C = cookies.SimpleCookie(); C.load(env.get('HTTP_COOKIE', ''))
        t = C.get('token').value if 'token' in C else None
        if not t: return None
        parts = t.split('.')
        p = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode("utf-8"))
        return p if p['exp'] > time.time() else None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

def init_db():
    conn = conectar_bd(); cur = conn.cursor(buffered=True)
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))")
    cur.execute("CREATE TABLE IF NOT EXISTS permisos_perfil (id INT AUTO_INCREMENT PRIMARY KEY, idPerfil INT, idModulo INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), imgUsuario LONGTEXT)")
    conn.commit(); cur.close(); conn.close()

def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""<div style="background:#0f4573; color:white; padding:15px; display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; gap:20px;">
                <a href="/dashboard" style="color:white; text-decoration:none; font-weight:bold;">🏠 Inicio</a>
                <a href="/perfiles" style="color:white; text-decoration:none;">Perfiles</a>
                <a href="/modulos" style="color:white; text-decoration:none;">Módulos</a>
                <a href="/permisos" style="color:white; text-decoration:none;">Permisos</a>
                <a href="/usuarios" style="color:white; text-decoration:none;">Usuarios</a>
            </div>
            <div><b>{user['u']}</b> | <a href="/logout" style="color:#ff7675; text-decoration:none;">Salir</a></div>
        </div>"""
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:sans-serif; background:#f0f2f5; margin:0;}} 
        .card{{background:white; padding:25px; margin:20px auto; max-width:900px; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,0.1);}}
        table{{width:100%; border-collapse:collapse; margin-top:15px;}} 
        th,td{{padding:12px; border:1px solid #ddd; text-align:left;}}
        th{{background:#0f4573; color:white;}}
        .btn{{background:#0f4573; color:white; border:none; padding:10px 20px; cursor:pointer; border-radius:4px; font-weight:bold;}}
        .btn-del{{background:#e74c3c; color:white; border:none; padding:5px 10px; cursor:pointer; border-radius:4px;}}
        input, select{{padding:10px; border:1px solid #ccc; border-radius:4px; margin:5px 0;}}
        .form-group{{background:#f9f9f9; padding:15px; border-radius:8px; border:1px solid #eee; margin-bottom:20px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# APP PRINCIPAL
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()

    # --- LOGIN ---
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:320px; text-align:center; margin-top:80px;">
            <h2 style="color:#0f4573;">Clínica Santa Mónica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" style="width:100%;" required>
                <input type="password" name="p" placeholder="Contraseña" style="width:100%;" required>
                <div style="margin:15px 0; display:flex; justify-content:center;">
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                </div>
                <button type="button" id="btnIn" class="btn" style="width:100%;">Entrar</button>
            </form><div id="msg" style="color:red; margin-top:10px;"></div></div>
            <script>
                document.getElementById('btnIn').onclick = async () => {
                    const captcha = grecaptcha.getResponse();
                    if(!captcha) { document.getElementById('msg').innerText = "Resuelve el captcha"; return; }
                    const fd = new FormData(document.getElementById('fL'));
                    const res = await fetch('/api/login', {method:'POST', body:fd});
                    const d = await res.json();
                    if(d.ok) window.location.replace('/dashboard');
                    else { document.getElementById('msg').innerText = d.msg; grecaptcha.reset(); }
                };
            </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [json.dumps({"ok":True}).encode("utf-8")]
        start_response("200 OK", [("Content-Type", "application/json")]); return [json.dumps({"ok":False, "msg":"Credenciales incorrectas"}).encode("utf-8")]

    # --- SEGURIDAD ---
    u_data = verify_jwt(environ)
    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API GUARDAR ---
    if path.startswith("/api/save_") and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        conn = conectar_bd(); cur = conn.cursor()
        if path == "/api/save_perfiles":
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s,%s)", (fs.getvalue("n"), 1 if fs.getvalue("a") else 0))
        elif path == "/api/save_modulos":
            cur.execute("INSERT INTO modulos (strNombreModulo) VALUES (%s)", (fs.getvalue("n"),))
        elif path == "/api/save_permisos":
            cur.execute("INSERT INTO permisos_perfil (idPerfil, idModulo) VALUES (%s,%s)", (fs.getvalue("pid"), fs.getvalue("mid")))
        elif path == "/api/save_usuarios":
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strCorreo, idEstadoUsuario, imgUsuario) VALUES (%s,%s,%s,%s,1,%s)", 
                (fs.getvalue("u"), hash_password(fs.getvalue("p")), fs.getvalue("pid"), fs.getvalue("e"), fs.getvalue("img")))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- LOGOUT ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0")]); return [b""]

    # --- VISTAS CRUD ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    form = ""; tbl = ""; title = ""
    
    if path == "/dashboard":
        title = "Dashboard"; content = "<h3>Bienvenido al Sistema de Gestión</h3><p>Use el menú superior para navegar.</p>"
    
    elif path == "/perfiles":
        title = "Gestión de Perfiles"
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall()
        form = "<form id='f'><input name='n' placeholder='Nombre del Perfil' required> Admin: <input type='checkbox' name='a'> <button class='btn'>Añadir Perfil</button></form>"
        tbl = "<table><tr><th>ID</th><th>Nombre</th><th>Admin</th></tr>" + "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'S' if r['bitAdministrador'] else 'N'}</td></tr>" for r in rows]) + "</table>"
    
    elif path == "/modulos":
        title = "Gestión de Módulos"
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall()
        form = "<form id='f'><input name='n' placeholder='Nombre del Módulo' required> <button class='btn'>Añadir Módulo</button></form>"
        tbl = "<table><tr><th>ID</th><th>Módulo</th></tr>" + "".join([f"<tr><td>{r['id']}</td><td>{r['strNombreModulo']}</td></tr>" for r in rows]) + "</table>"
        
    elif path == "/permisos":
        title = "Asignación de Permisos"
        cur.execute("SELECT pp.id, p.strNombrePerfil, m.strNombreModulo FROM permisos_perfil pp JOIN perfiles p ON pp.idPerfil=p.id JOIN modulos m ON pp.idModulo=m.id"); rows = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        cur.execute("SELECT id, strNombreModulo FROM modulos"); mods = cur.fetchall()
        opt_p = "".join([f"<option value='{x['id']}'>{x['strNombrePerfil']}</option>" for x in perfs])
        opt_m = "".join([f"<option value='{x['id']}'>{x['strNombreModulo']}</option>" for x in mods])
        form = f"<form id='f'>Perfil: <select name='pid'>{opt_p}</select> Módulo: <select name='mid'>{opt_m}</select> <button class='btn'>Asignar Permiso</button></form>"
        tbl = "<table><tr><th>Perfil</th><th>Módulo Permitido</th></tr>" + "".join([f"<tr><td>{r['strNombrePerfil']}</td><td>{r['strNombreModulo']}</td></tr>" for r in rows]) + "</table>"

    elif path == "/usuarios":
        title = "Gestión de Usuarios"
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil=p.id"); rows = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        opt_p = "".join([f"<option value='{x['id']}'>{x['strNombrePerfil']}</option>" for x in perfs])
        form = f"<form id='f'><input name='u' placeholder='Usuario' required><input name='p' type='password' placeholder='Clave'><input name='e' type='email' placeholder='Correo'><select name='pid'>{opt_p}</select> Foto: <input type='file' id='img_file'><button class='btn'>Crear Usuario</button></form>"
        tbl = "<table><tr><th>Foto</th><th>Usuario</th><th>Perfil</th><th>Correo</th></tr>" + "".join([f"<tr><td><img src='{r.get('imgUsuario','')}' width='30' style='border-radius:50%'></td><td>{r['strNombreUsuario']}</td><td>{r['strNombrePerfil']}</td><td>{r['strCorreo']}</td></tr>" for r in rows]) + "</table>"

    if path != "/dashboard":
        content = f"<div class='form-group'><h4>Agregar Nuevo</h4>{form}</div><h3>Listado</h3>{tbl}"
    
    cur.close(); conn.close()
    
    full_body = f"<div class='card'><h2>{title}</h2>{content}</div>"
    # JS MÁGICO QUE MANEJA TODOS LOS FORMULARIOS Y FOTOS
    script = f"""<script>
        if(document.getElementById('f')) {{
            document.getElementById('f').onsubmit = async (e) => {{
                e.preventDefault();
                const fd = new FormData(e.target);
                const fileInput = document.getElementById('img_file');
                if(fileInput && fileInput.files[0]) {{
                    const reader = new FileReader();
                    reader.onloadend = async () => {{
                        fd.append('img', reader.result);
                        await fetch('/api/save' + window.location.pathname, {{method:'POST', body:fd}});
                        location.reload();
                    }};
                    reader.readAsDataURL(fileInput.files[0]);
                }} else {{
                    await fetch('/api/save' + window.location.pathname, {{method:'POST', body:fd}});
                    location.reload();
                }}
            }};
        }}
    </script>"""
    
    start_response("200 OK", [("Content-Type", "text/html")]); return [(render_layout(title, full_body, u_data) + script).encode("utf-8")]