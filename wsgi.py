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
from http import cookies 

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
    C = cookies.SimpleCookie()
    C.load(environ.get('HTTP_COOKIE', ''))
    token = C.get('token').value if 'token' in C else None
    if not token: return None
    try:
        parts = token.split('.')
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode("utf-8"))
        if payload['exp'] < time.time(): return None
        return payload
    except: return None

# =========================================================
# BASE DE DATOS - INICIALIZACIÓN FORZADA
# =========================================================
def conectar_bd():
    try:
        res = urllib.parse.urlparse(DB_URL)
        return mysql.connector.connect(
            host=res.hostname, port=res.port, user=res.username,
            password=res.password, database=res.path[1:],
            charset='utf8mb4', collation='utf8mb4_general_ci'
        )
    except: return None

def init_db():
    conn = conectar_bd()
    if not conn: return
    cur = conn.cursor(dictionary=True)
    
    # Crear tablas
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))")
    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, 
        strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), 
        strNumeroCelular VARCHAR(20), imgUsuario LONGTEXT)""")
    
    # Verificar si el admin ya existe y si su estado es correcto
    cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = 'admin'")
    admin = cur.fetchone()
    
    if not admin:
        # Insertar perfil y usuario desde cero
        cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES ('Administrador', 1)")
        perfil_id = cur.lastrowid
        cur.execute("""INSERT INTO usuarios 
            (strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo) 
            VALUES ('admin', %s, %s, 1, 'admin@clinica.com')""", (perfil_id, hash_password("123456")))
    elif admin['idEstadoUsuario'] != 1:
        # CORRECCIÓN: Si el admin existe pero está inactivo, lo activamos
        cur.execute("UPDATE usuarios SET idEstadoUsuario = 1 WHERE strNombreUsuario = 'admin'")
    
    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# INTERFAZ
# =========================================================
def render_layout(title, content, user=None, breadcrumbs=None):
    nav_html = ""
    bc_html = ""
    if user:
        nav_html = f"""
        <div class="top-nav" style="background:#0f4573; color:white; padding:15px; display:flex; gap:20px;">
            <a href="/dashboard" style="color:white; text-decoration:none;">Inicio</a>
            <a href="/seguridad" style="color:white; text-decoration:none;">Seguridad</a>
            <a href="/logout" style="color:white; text-decoration:none; margin-left:auto;">Salir</a>
        </div>"""
        
        steps = [("Inicio", "/dashboard")]
        if breadcrumbs: steps.extend(breadcrumbs)
        links = [f'<a href="{u}">{t}</a>' for t, u in steps]
        bc_html = f'<div style="padding:10px 20px; background:#fff; border-bottom:1px solid #ddd;">{" / ".join(links)}</div>'

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><title>{title}</title>
        <script src="https://www.google.com/recaptcha/api.js" async defer></script>
        <style>
            body {{ font-family: sans-serif; margin: 0; background: #f0f2f5; }}
            .container {{ padding: 20px; }}
            .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
            .btn {{ padding: 10px 20px; background: #0f4573; color: white; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; }}
            .menu-bar {{ background: #0f4573; color: white; padding: 10px; margin-top: 20px; display: flex; gap: 40px; justify-content: center; }}
            .menu-bar a {{ color: white; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        {nav_html}{bc_html}
        <div class="container">{content}</div>
    </body>
    </html>
    """

# =========================================================
# WSGI APP
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    
    init_db()

    if path in ["/", "/login"]:
        content = """
        <div style="max-width: 400px; margin: 80px auto; text-align:center;" class="card">
            <h2>Clínica Santa Mónica</h2>
            <form id="formLogin">
                <input type="text" name="u" placeholder="Usuario" style="width:90%; padding:10px; margin:10px;" required>
                <input type="password" name="p" placeholder="Contraseña" style="width:90%; padding:10px; margin:10px;" required>
                <div style="display:inline-block;" class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                <button type="submit" class="btn" style="width:95%; margin-top:15px;">Entrar</button>
            </form>
            <div id="msg" style="color:red; margin-top:15px; font-weight:bold;"></div>
        </div>
        <script>
            document.getElementById('formLogin').onsubmit = async (e) => {
                e.preventDefault();
                const res = await fetch('/api/login', { method: 'POST', body: new FormData(e.target) });
                const data = await res.json();
                if(data.ok) location.href = '/dashboard';
                else document.getElementById('msg').innerText = data.msg;
            };
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u_in, p_in = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        
        conn = conectar_bd()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = %s", (u_in,))
        user = cur.fetchone()
        
        if user and user['strPwd'] == p_in:
            # Aquí está la validación que te fallaba
            if int(user['idEstadoUsuario']) != 1:
                res = {"ok": False, "msg": "Usuario inactivo o sin permisos"}
            else:
                token = jwt_encode({"u": u_in, "exp": time.time() + 3600})
                start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={token}; Path=/; HttpOnly")])
                return [json.dumps({"ok": True}).encode("utf-8")]
        else:
            res = {"ok": False, "msg": "Usuario o contraseña incorrectos"}
        
        start_response("200 OK", [("Content-Type", "application/json")])
        return [json.dumps(res).encode("utf-8")]

    user_data = verify_jwt(environ)
    if not user_data:
        start_response("303 See Other", [("Location", "/login")])
        return [b""]

    if path == "/dashboard":
        content = f"""
        <div class="card">
            <p>Sistema Corporativo - Clínica Santa Mónica</p>
            <h3>Bienvenido, <strong>{user_data['u']}</strong>.</h3>
            <div class="menu-bar">
                <a href="/perfiles">Perfil</a>
                <a href="/modulos">Módulo</a>
                <a href="/permisos">Permisos-Perfil</a>
                <a href="/usuarios">Usuario</a>
            </div>
        </div>"""
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Dashboard", content, user_data).encode("utf-8")]

    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")])
        return [b""]

    # Página de Error
    start_response("404 Not Found", [("Content-Type", "text/html")])
    return [render_layout("Error", "<div class='card'><h2>Error 404</h2><p>Página no encontrada.</p></div>", user_data).encode("utf-8")]