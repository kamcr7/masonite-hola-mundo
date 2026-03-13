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

def hash_password(password):
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()

def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def jwt_encode(payload):
    header_b64 = b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    payload_b64 = b64url_encode(json.dumps(payload).encode("utf-8"))
    sig = hmac.new(JWT_SECRET.encode("utf-8"), f"{header_b64}.{payload_b64}".encode("utf-8"), hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{b64url_encode(sig)}"

def verify_jwt(environ):
    C = cookies.SimpleCookie()
    C.load(environ.get('HTTP_COOKIE', ''))
    token = C.get('token').value if 'token' in C else None
    if not token: return None
    try:
        parts = token.split('.')
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode("utf-8"))
        return payload if payload['exp'] > time.time() else None
    except: return None

def conectar_bd():
    try:
        res = urllib.parse.urlparse(DB_URL)
        return mysql.connector.connect(
            host=res.hostname, port=res.port, user=res.username,
            password=res.password, database=res.path[1:], charset='utf8mb4'
        )
    except: return None

# =========================================================
# INICIALIZACIÓN DE BD (CORRECCIÓN UNREAD RESULT)
# =========================================================
def init_db():
    conn = conectar_bd()
    if not conn: return
    try:
        # Usamos buffered=True para evitar el error de "Unread result"
        cur = conn.cursor(dictionary=True, buffered=True)
        
        # Crear tablas base
        cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150))")
        conn.commit()

        # Verificar columna idEstadoUsuario
        cur.execute("SHOW COLUMNS FROM usuarios LIKE 'idEstadoUsuario'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE usuarios ADD COLUMN idEstadoUsuario INT DEFAULT 1")
            conn.commit()
        
        # Buscar admin
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = 'admin'")
        admin = cur.fetchone()
        
        if not admin:
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES ('Administrador', 1)")
            p_id = cur.lastrowid
            cur.execute("INSERT INTO usuarios (strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo) VALUES ('admin', %s, %s, 1, 'admin@clinica.com')", (p_id, hash_password("123456")))
            conn.commit()
        else:
            cur.execute("UPDATE usuarios SET idEstadoUsuario = 1 WHERE strNombreUsuario = 'admin'")
            conn.commit()
            
        cur.close()
    finally:
        conn.close()

# =========================================================
# RENDERIZADO
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""<div style="background:#0f4573; color:white; padding:15px; display:flex; justify-content:space-between;">
            <div><a href="/dashboard" style="color:white; text-decoration:none; margin-right:20px;">Inicio</a><a href="/seguridad" style="color:white; text-decoration:none;">Seguridad</a></div>
            <div>Bienvenido, <b>{user.get('u', 'admin')}</b> | <a href="/logout" style="color:white; text-decoration:none;">Salir</a></div>
        </div>"""
    
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body {{ font-family: sans-serif; margin: 0; background: #f0f2f5; }}
        .card {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 900px; margin: 20px auto; }}
        .btn-bar {{ background: #0f4573; color: white; padding: 12px; display: flex; gap: 35px; margin-top: 15px; }}
        .btn-bar a {{ color: white; text-decoration: none; font-weight: bold; }}
    </style></head><body>{nav}<div class="container">{content}</div></body></html>"""

# =========================================================
# APLICACIÓN WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    
    # Solo inicializar BD en rutas principales para no saturar
    if path in ["/", "/login", "/dashboard"]:
        init_db()

    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:350px; text-align:center;">
            <h2>Clínica Santa Mónica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" style="width:100%; padding:10px; margin:5px 0;" required>
                <input type="password" name="p" placeholder="Contraseña" style="width:100%; padding:10px; margin:5px 0;" required>
                <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                <button type="submit" style="width:100%; padding:10px; background:#0f4573; color:white; border:none; margin-top:10px; cursor:pointer;">Entrar</button>
            </form><div id="msg" style="color:red; margin-top:10px;"></div></div>
            <script>document.getElementById('fL').onsubmit = async (e) => { e.preventDefault(); 
            const res = await fetch('/api/login', {method:'POST', body:new FormData(e.target)});
            const d = await res.json(); if(d.ok) location.href='/dashboard'; else document.getElementById('msg').innerText=d.msg; }</script>"""
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u_in, p_in = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        
        conn = conectar_bd()
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = %s", (u_in,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user and user.get('strPwd') == p_in:
            estado = user.get('idEstadoUsuario', 1)
            if int(estado) != 1:
                res = {"ok": False, "msg": "Usuario inactivo"}
            else:
                tk = jwt_encode({"u": u_in, "exp": time.time() + 3600})
                start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
                return [json.dumps({"ok": True}).encode("utf-8")]
        else:
            res = {"ok": False, "msg": "Credenciales inválidas"}
        start_response("200 OK", [("Content-Type", "application/json")])
        return [json.dumps(res).encode("utf-8")]

    u_data = verify_jwt(environ)
    if not u_data:
        start_response("303 See Other", [("Location", "/login")])
        return [b""]

    if path == "/dashboard":
        content = f"""<div class="card">
            <p style="font-size: 14px;">🏥 Sistema Corporativo - Clínica Santa Mónica</p>
            <h3>Bienvenido, <b>{u_data['u']}</b>.</h3>
            <div class="btn-bar">
                <a href="/perfiles">Perfil</a><a href="/modulos">Módulo</a>
                <a href="/permisos">Permisos-Perfil</a><a href="/usuarios">Usuario</a>
            </div></div>"""
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Dashboard", content, u_data).encode("utf-8")]

    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")])
        return [b""]

    start_response("404 Not Found", [("Content-Type", "text/html")])
    return [render_layout("Error", "<h1>404</h1>", u_data).encode("utf-8")]