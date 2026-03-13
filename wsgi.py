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
from datetime import datetime

# =========================================================
# CONFIGURACIÓN Y CONSTANTES
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
    cookies = cgi.SimpleCookie(environ.get('HTTP_COOKIE', ''))
    token = cookies.get('token').value if 'token' in cookies else None
    if not token: return None
    try:
        parts = token.split('.')
        if len(parts) != 3: return None
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        if payload['exp'] < time.time(): return None
        return payload
    except: return None

# =========================================================
# BASE DE DATOS - ESTRUCTURA SOLICITADA
# =========================================================
def conectar_bd():
    try:
        res = urllib.parse.urlparse(DB_URL)
        return mysql.connector.connect(
            host=res.hostname, port=res.port, user=res.username,
            password=res.password, database=res.path[1:]
        )
    except: return None

def init_db():
    conn = conectar_bd()
    if not conn: return
    cur = conn.cursor()
    # Módulo Perfil
    cur.execute("""CREATE TABLE IF NOT EXISTS perfiles (
        id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))""")
    # Módulo Módulo
    cur.execute("""CREATE TABLE IF NOT EXISTS modulos (
        id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))""")
    # Módulo Usuario (Incluye Imagen)
    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, 
        strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), 
        strNumeroCelular VARCHAR(20), imgUsuario LONGTEXT)""")
    # Módulo PermisosPerfil
    cur.execute("""CREATE TABLE IF NOT EXISTS permisos_perfil (
        id INT AUTO_INCREMENT PRIMARY KEY, idModulo INT, idPerfil INT, 
        bitAgregar TINYINT(1), bitEditar TINYINT(1), bitConsulta TINYINT(1), 
        bitEliminar TINYINT(1), bitDetalle TINYINT(1))""")
    
    # Usuario Inicial
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES ('Administrador', 1)")
        cur.execute("INSERT INTO usuarios (strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo) VALUES ('admin', 1, %s, 1, 'admin@clinica.com')", (hash_password("123456"),))
    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# INTERFAZ Y MAQUETACIÓN (RESPONSIVO)
# =========================================================
def render_layout(title, content, user=None, breadcrumbs=None):
    nav_html = ""
    bc_html = ""
    if user:
        nav_html = f"""
        <div class="top-nav">
            <div class="nav-links">
                <a href="/dashboard">Inicio</a>
                <a href="/seguridad">Seguridad</a>
                <a href="/logout" style="color:#ff8888">Salir</a>
            </div>
            <div class="user-badge">Usuario: <strong>{user['usuario']}</strong></div>
        </div>"""
        
        # Breadcrumbs logic
        steps = [("Inicio", "/dashboard")]
        if breadcrumbs: steps.extend(breadcrumbs)
        bc_html = f'<div class="bc">{" / ".join([f"<a href=\'{s[1]}\'>{s[0]}</a>" for s in steps])}</div>'

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <script src="https://www.google.com/recaptcha/api.js" async defer></script>
        <style>
            :root {{ --main: #0f4573; --bg: #f0f2f5; --white: #ffffff; --green: #58a74a; }}
            body {{ font-family: 'Segoe UI', Arial; margin: 0; background: var(--bg); color: #333; }}
            .top-nav {{ background: var(--main); color: white; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; }}
            .nav-links a {{ color: white; text-decoration: none; margin-right: 20px; font-weight: 500; }}
            .bc {{ background: white; padding: 10px 25px; border-bottom: 1px solid #ddd; font-size: 14px; }}
            .bc a {{ color: var(--main); text-decoration: none; }}
            .container {{ padding: 25px; max-width: 1100px; margin: auto; }}
            .card {{ background: var(--white); padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: white; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background: #fafafa; color: var(--main); }}
            .btn {{ padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer; text-decoration: none; display: inline-block; font-size: 14px; }}
            .btn-add {{ background: var(--green); color: white; }}
            .btn-edit {{ background: #ffc107; color: #000; }}
            .btn-del {{ background: #dc3545; color: white; }}
            .pagination {{ margin-top: 15px; display: flex; gap: 5px; }}
            .error-page {{ text-align: center; margin-top: 100px; }}
            .img-row {{ width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }}
            @media (max-width: 600px) {{ .top-nav {{ flex-direction: column; gap: 10px; }} }}
        </style>
    </head>
    <body>
        {nav_html}
        {bc_html}
        <div class="container">{content}</div>
    </body>
    </html>
    """

# =========================================================
# APLICACIÓN WSGI PRINCIPAL
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    query = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
    
    init_db()

    # --- RUTA: LOGIN ---
    if path in ["/", "/login"]:
        content = """
        <div style="max-width: 400px; margin: 80px auto;" class="card">
            <h2 style="text-align:center; color:#0f4573;">Clínica Santa Mónica</h2>
            <form id="formLogin">
                <label>Usuario</label>
                <input type="text" name="user" style="width:100%; padding:10px; margin:8px 0;" required>
                <label>Contraseña</label>
                <input type="password" name="pass" style="width:100%; padding:10px; margin:8px 0;" required>
                <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" style="margin:15px 0;"></div>
                <button type="submit" class="btn" style="width:100%; background:#0f4573; color:white; padding:12px;">Entrar</button>
            </form>
            <div id="msg" style="margin-top:10px; color:red; text-align:center;"></div>
        </div>
        <script>
            document.getElementById('formLogin').onsubmit = async (e) => {
                e.preventDefault();
                const fd = new FormData(e.target);
                const res = await fetch('/api/login', { method: 'POST', body: fd });
                const data = await res.json();
                if(data.ok) location.href = '/dashboard';
                else document.getElementById('msg').innerText = data.msg;
            };
        </script>
        """
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Login", content).encode("utf-8")]

    # --- API: LOGIN (JWT + Captcha + Estado) ---
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u_input = fs.getvalue("user")
        p_input = hash_password(fs.getvalue("pass", ""))
        
        conn = conectar_bd()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = %s", (u_input,))
        user = cur.fetchone()
        
        if user and user['strPwd'] == p_input:
            if user['idEstadoUsuario'] != 1:
                res = {"ok": False, "msg": "Usuario inactivo"}
            else:
                token = jwt_encode({"uid": user['id'], "usuario": u_input, "exp": time.time() + JWT_EXPIRE_SECONDS})
                start_response("200 OK", [
                    ("Content-Type", "application/json"),
                    ("Set-Cookie", f"token={token}; Path=/; HttpOnly; SameSite=Lax")
                ])
                return [json.dumps({"ok": True}).encode("utf-8")]
        else:
            res = {"ok": False, "msg": "Credenciales inválidas"}
        
        start_response("200 OK", [("Content-Type", "application/json")])
        return [json.dumps(res).encode("utf-8")]

    # --- VALIDACIÓN DE SESIÓN ---
    user_session = verify_jwt(environ)
    if not user_session:
        start_response("303 See Other", [("Location", "/login")])
        return [b""]

    # --- RUTA: DASHBOARD ---
    if path == "/dashboard":
        content = """
        <div class="card">
            <h1>Panel Administrativo</h1>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:20px;">
                <a href="/perfiles" class="card" style="text-align:center; text-decoration:none; color:inherit;"><h3>Perfiles</h3></a>
                <a href="/modulos" class="card" style="text-align:center; text-decoration:none; color:inherit;"><h3>Módulos</h3></a>
                <a href="/permisos" class="card" style="text-align:center; text-decoration:none; color:inherit;"><h3>Permisos</h3></a>
                <a href="/usuarios" class="card" style="text-align:center; text-decoration:none; color:inherit;"><h3>Usuarios</h3></a>
            </div>
        </div>
        """
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Dashboard", content, user_session).encode("utf-8")]

    # --- RUTA: CRUD USUARIOS (Con paginación y detalle) ---
    if path == "/usuarios":
        p = int(query.get("p", ["1"])[0])
        offset = (p - 1) * PAGE_SIZE
        
        conn = conectar_bd()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios LIMIT %s OFFSET %s", (PAGE_SIZE, offset))
        rows = cur.fetchall()
        
        rows_html = ""
        for r in rows:
            img = f"<img src='{r['imgUsuario']}' class='img-row'>" if r['imgUsuario'] else "Sin foto"
            est = "Activo" if r['idEstadoUsuario'] == 1 else "Inactivo"
            rows_html += f"""<tr>
                <td>{img}</td><td>{r['strNombreUsuario']}</td><td>{r['strCorreo']}</td><td>{est}</td>
                <td>
                    <button class='btn btn-edit'>Detalle</button>
                    <button class='btn btn-del'>Eliminar</button>
                </td>
            </tr>"""
            
        content = f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between;">
                <h2>Gestión de Usuarios</h2>
                <button class="btn btn-add">+ Nuevo Usuario</button>
            </div>
            <table>
                <tr><th>Foto</th><th>Usuario</th><th>Email</th><th>Estado</th><th>Acciones</th></tr>
                {rows_html if rows_html else "<tr><td colspan='5'>No hay datos</td></tr>"}
            </table>
            <div class="pagination">
                <a href="?p={max(1, p-1)}" class="btn" style="background:#ccc">Anterior</a>
                <span style="padding:8px;">Página {p}</span>
                <a href="?p={p+1}" class="btn" style="background:#ccc">Siguiente</a>
            </div>
        </div>"""
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Usuarios", content, user_session, [("Usuarios", "/usuarios")]).encode("utf-8")]

    # --- SALIR ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")])
        return [b""]

    # --- PÁGINA DE ERROR PERSONALIZADA ---
    content = """
    <div class="error-page">
        <h1 style="font-size:80px; color:#0f4573;">404</h1>
        <h2>Oops! Página no encontrada</h2>
        <p>Parece que no tienes permisos o la ruta es incorrecta.</p>
        <a href="/dashboard" class="btn btn-add">Regresar al Inicio</a>
    </div>
    """
    start_response("404 Not Found", [("Content-Type", "text/html")])
    return [render_layout("Error", content, user_session).encode("utf-8")]