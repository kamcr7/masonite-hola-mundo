# -*- coding: utf-8 -*-
import hashlib
import json
import hmac
import time
import urllib.parse
import cgi
import mysql.connector
import os
import base64
from http import cookies # IMPORTANTE: Reemplaza a cgi.SimpleCookie

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@mysql.railway.internal:3306/railway')
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_SECURITY"
JWT_EXPIRE_SECONDS = 3600 
PAGE_SIZE = 5

# =========================================================
# SEGURIDAD Y TOKEN (JWT)
# =========================================================
def hash_password(password):
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()

def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def jwt_encode(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = b64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = b64url_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{b64url_encode(signature)}"

def verify_jwt(environ):
    # Corrección: Uso de http.cookies en lugar de cgi.SimpleCookie
    C = cookies.SimpleCookie()
    C.load(environ.get('HTTP_COOKIE', ''))
    token = C.get('token').value if 'token' in C else None
    
    if not token: return None
    try:
        parts = token.split('.')
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode("utf-8"))
        if payload['exp'] < time.time(): return None
        return payload
    except Exception as e:
        print(f"Error JWT: {e}")
        return None

# =========================================================
# BASE DE DATOS
# =========================================================
def conectar_bd():
    try:
        res = urllib.parse.urlparse(DB_URL)
        return mysql.connector.connect(
            host=res.hostname, port=res.port, user=res.username,
            password=res.password, database=res.path[1:],
            charset='utf8mb4',
            collation='utf8mb4_general_ci'
        )
    except: return None

def init_db():
    conn = conectar_bd()
    if not conn: return
    cur = conn.cursor()
    # Módulo Perfil
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
    # Módulo Módulo
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))")
    # Módulo Usuario
    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, 
        strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), 
        strNumeroCelular VARCHAR(20), imgUsuario LONGTEXT)""")
    # Módulo PermisosPerfil
    cur.execute("""CREATE TABLE IF NOT EXISTS permisos_perfil (
        id INT AUTO_INCREMENT PRIMARY KEY, idModulo INT, idPerfil INT, 
        bitAgregar TINYINT(1), bitEditar TINYINT(1), bitConsulta TINYINT(1), 
        bitEliminar TINYINT(1), bitDetalle TINYINT(1))""")
    
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES ('Administrador', 1)")
        cur.execute("INSERT INTO usuarios (strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo) VALUES ('admin', 1, %s, 1, 'admin@clinica.com')", (hash_password("123456"),))
    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# RENDERIZADO
# =========================================================
def render_layout(title, content, user=None, breadcrumbs=None):
    nav_html = ""
    bc_html = ""
    if user:
        nav_html = f"""
        <div class="top-nav">
            <div class="nav-links">
                <a href="/dashboard">Inicio</a>
                <a href="/logout" style="color:#ff8888">Salir</a>
            </div>
            <div class="user-badge">Hola, <strong>{user.get('usuario', 'Usuario')}</strong></div>
        </div>"""
        
        steps = [("Inicio", "/dashboard")]
        if breadcrumbs: steps.extend(breadcrumbs)
        
        links = [f'<a href="{u}">{t}</a>' for t, u in steps]
        bc_html = f'<div class="bc">{" / ".join(links)}</div>'

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <script src="https://www.google.com/recaptcha/api.js" async defer></script>
        <style>
            :root {{ --main: #0f4573; --bg: #f0f2f5; --white: #ffffff; --green: #58a74a; }}
            body {{ font-family: sans-serif; margin: 0; background: var(--bg); }}
            .top-nav {{ background: var(--main); color: white; padding: 15px 25px; display: flex; justify-content: space-between; }}
            .nav-links a {{ color: white; text-decoration: none; margin-right: 15px; }}
            .bc {{ background: white; padding: 10px 25px; border-bottom: 1px solid #ddd; }}
            .bc a {{ color: var(--main); text-decoration: none; }}
            .container {{ padding: 25px; max-width: 1000px; margin: auto; }}
            .card {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .btn {{ padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer; text-decoration: none; display: inline-block; background: var(--main); color: white; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #eee; text-align: left; }}
        </style>
    </head>
    <body>
        {nav_html}{bc_html}
        <div class="container">{content}</div>
    </body>
    </html>
    """

# =========================================================
# APLICACIÓN WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    query = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
    
    init_db()

    # --- LOGIN ---
    if path in ["/", "/login"] and method == "GET":
        content = """
        <div style="max-width: 350px; margin: 80px auto;" class="card">
            <h2 style="text-align:center;">Clínica Santa Mónica</h2>
            <form id="formL">
                <input type="text" name="u" placeholder="Usuario" style="width:100%; padding:10px; margin:5px 0;" required>
                <input type="password" name="p" placeholder="Contraseña" style="width:100%; padding:10px; margin:5px 0;" required>
                <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                <button type="submit" class="btn" style="width:100%; margin-top:10px;">Entrar</button>
            </form>
            <div id="m" style="color:red; margin-top:10px; text-align:center;"></div>
        </div>
        <script>
            document.getElementById('formL').onsubmit = async (e) => {
                e.preventDefault();
                const res = await fetch('/api/login', { method: 'POST', body: new FormData(e.target) });
                const data = await res.json();
                if(data.ok) location.href = '/dashboard';
                else document.getElementById('m').innerText = data.msg;
            };
        </script>
        """
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Login", content).encode("utf-8")]

    # --- API LOGIN ---
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u_in = fs.getvalue("u")
        p_in = hash_password(fs.getvalue("p", ""))
        
        conn = conectar_bd()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = %s", (u_in,))
        user = cur.fetchone()
        
        # Corrección del KeyError: Verificamos existencia antes de acceder
        if user and user.get('strPwd') == p_in:
            if int(user.get('idEstadoUsuario', 0)) != 1:
                res = {"ok": False, "msg": "Usuario inactivo o sin permisos"}
            else:
                token = jwt_encode({"uid": user['id'], "usuario": u_in, "exp": time.time() + JWT_EXPIRE_SECONDS})
                start_response("200 OK", [
                    ("Content-Type", "application/json"),
                    ("Set-Cookie", f"token={token}; Path=/; HttpOnly")
                ])
                return [json.dumps({"ok": True}).encode("utf-8")]
        else:
            res = {"ok": False, "msg": "Usuario o clave incorrecta"}
        
        start_response("200 OK", [("Content-Type", "application/json")])
        return [json.dumps(res).encode("utf-8")]

    # --- PROTECCIÓN DE RUTAS ---
    session = verify_jwt(environ)
    if not session and path != "/favicon.ico":
        start_response("303 See Other", [("Location", "/login")])
        return [b""]

    # --- DASHBOARD ---
    if path == "/dashboard":
        content = f"""
        <div class="card">
            <h1>Bienvenido</h1>
            <p>Seleccione una opción del menú:</p>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                <a href="/perfiles" class="btn">Perfiles</a>
                <a href="/modulos" class="btn">Módulos</a>
                <a href="/permisos" class="btn">Permisos</a>
                <a href="/usuarios" class="btn">Usuarios</a>
            </div>
        </div>
        """
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Bienvenido", content, session).encode("utf-8")]

    # --- SALIR ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")])
        return [b""]

    # --- 404 ---
    start_response("404 Not Found", [("Content-Type", "text/html")])
    return [render_layout("Error", "<h1>404</h1><p>No encontrado</p>", session).encode("utf-8")]