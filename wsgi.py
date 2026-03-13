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
# INICIALIZACIÓN DE BD
# =========================================================
def init_db():
    conn = conectar_bd()
    if not conn: return
    try:
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150))")
        
        cur.execute("SHOW COLUMNS FROM usuarios LIKE 'idEstadoUsuario'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE usuarios ADD COLUMN idEstadoUsuario INT DEFAULT 1")
        
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = 'admin'")
        admin = cur.fetchone()
        if not admin:
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES ('Administrador', 1)")
            p_id = cur.lastrowid
            cur.execute("INSERT INTO usuarios (strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo) VALUES ('admin', %s, %s, 1, 'admin@clinica.com')", (p_id, hash_password("123456")))
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
        body {{ font-family: sans-serif; margin: 0; background: #f0f2f5; color: #333; }}
        .card {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 1000px; margin: 20px auto; }}
        .btn-bar {{ background: #0f4573; color: white; padding: 12px; display: flex; gap: 35px; margin-top: 15px; border-radius: 4px; }}
        .btn-bar a {{ color: white; text-decoration: none; font-weight: bold; }}
        .btn {{ padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer; color: white; text-decoration: none; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #0f4573; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f9f9f9; }}
        input[type="text"], input[type="password"] {{ width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
    </style></head><body>{nav}<div class="container">{content}</div></body></html>"""

# =========================================================
# APLICACIÓN WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    
    init_db()

    # --- LOGIN ---
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:400px; text-align:center; margin-top:100px;">
            <h2 style="color:#0f4573;">Clínica Santa Mónica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" required>
                <input type="password" name="p" placeholder="Contraseña" required>
                <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" style="display:inline-block; margin:10px 0;"></div>
                <button type="submit" class="btn" style="background:#0f4573; width:100%; font-size:16px;">Entrar</button>
            </form><div id="msg" style="color:red; margin-top:15px; font-weight:bold;"></div></div>
            <script>document.getElementById('fL').onsubmit = async (e) => { e.preventDefault(); 
            const res = await fetch('/api/login', {method:'POST', body:new FormData(e.target)});
            const d = await res.json(); if(d.ok) location.href='/dashboard'; else document.getElementById('msg').innerText=d.msg; }</script>"""
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Login", content).encode("utf-8")]

    # --- API LOGIN ---
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u_in, p_in = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = %s", (u_in,))
        user = cur.fetchone()
        cur.close(); conn.close()
        if user and user.get('strPwd') == p_in:
            tk = jwt_encode({"u": u_in, "exp": time.time() + 3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [json.dumps({"ok": True}).encode("utf-8")]
        start_response("200 OK", [("Content-Type", "application/json")])
        return [json.dumps({"ok": False, "msg": "Credenciales inválidas"}).encode("utf-8")]

    # --- SEGURIDAD ---
    u_data = verify_jwt(environ)
    if not u_data:
        start_response("303 See Other", [("Location", "/login")])
        return [b""]

    # --- DASHBOARD ---
    if path == "/dashboard":
        content = f"""<div class="card">
            <p style="font-size: 14px; color: #666;">🏥 Sistema Corporativo - Clínica Santa Mónica</p>
            <h3 style="margin: 10px 0;">Bienvenido, <b style="color:#0f4573;">{u_data['u']}</b>.</h3>
            <div class="btn-bar">
                <a href="/perfiles">Perfil</a><a href="/modulos">Módulo</a>
                <a href="/permisos">Permisos-Perfil</a><a href="/usuarios">Usuario</a>
            </div></div>"""
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Dashboard", content, u_data).encode("utf-8")]

    # --- CRUD PERFILES ---
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute("SELECT * FROM perfiles")
        rows = cur.fetchall()
        cur.close(); conn.close()
        
        tr_html = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'Admin' if r['bitAdministrador'] else 'User'}</td><td>"
                          f"<button class='btn' style='background:#f39c12; margin-right:5px;' onclick='ed({r['id']},\"{r['strNombrePerfil']}\",{r['bitAdministrador']})'>Editar</button>"
                          f"<button class='btn' style='background:#e74c3c;' onclick='del({r['id']})'>Borrar</button></td></tr>" for r in rows])

        content = f"""<div class="card"><h3>Gestión de Perfiles</h3>
            <button class="btn" style="background:#27ae60;" onclick="showM()">+ Nuevo Perfil</button>
            <table><tr><th>ID</th><th>Nombre</th><th>Tipo</th><th>Acciones</th></tr>{tr_html}</table></div>
            <div id="mP" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5);">
                <div class="card" style="width:350px; margin:100px auto;">
                    <h4 id="mT">Nuevo Perfil</h4>
                    <form id="fP"><input type="hidden" name="id" id="pI">
                        <input type="text" name="n" id="pN" placeholder="Nombre" required>
                        <label><input type="checkbox" name="a" id="pA"> Administrador</label>
                        <div style="margin-top:15px;"><button type="submit" class="btn" style="background:#0f4573;">Guardar</button>
                        <button type="button" class="btn" style="background:#95a5a6;" onclick="hideM()">Cancelar</button></div>
                    </form></div></div>
            <script>
                const showM = () => {{ document.getElementById('mP').style.display='block'; document.getElementById('mT').innerText='Nuevo Perfil'; }};
                const hideM = () => {{ document.getElementById('mP').style.display='none'; document.getElementById('fP').reset(); }};
                const ed = (id, n, a) => {{ showM(); document.getElementById('mT').innerText='Editar'; document.getElementById('pI').value=id; document.getElementById('pN').value=n; document.getElementById('pA').checked=a==1; }};
                document.getElementById('fP').onsubmit = async (e) => {{ e.preventDefault(); await fetch('/api/perfiles', {{method:'POST', body:new FormData(e.target)}}); location.reload(); }};
                const del = async (id) => {{ if(confirm('¿Borrar?')) {{ await fetch('/api/perfiles/del?id='+id); location.reload(); }} }};
            </script>"""
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Perfiles", content, u_data).encode("utf-8")]

    # --- API PERFILES ---
    if path == "/api/perfiles" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        p_id, name, is_a = fs.getvalue("id"), fs.getvalue("n"), (1 if fs.getvalue("a") else 0)
        conn = conectar_bd(); cur = conn.cursor()
        if p_id: cur.execute("UPDATE perfiles SET strNombrePerfil=%s, bitAdministrador=%s WHERE id=%s", (name, is_a, p_id))
        else: cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s, %s)", (name, is_a))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")])
        return [b'{"ok":true}']

    if path == "/api/perfiles/del":
        p_id = cgi.parse_qs(environ.get('QUERY_STRING', '')).get('id', [None])[0]
        if p_id:
            conn = conectar_bd(); cur = conn.cursor()
            cur.execute("DELETE FROM perfiles WHERE id=%s", (p_id,))
            conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")])
        return [b'{"ok":true}']

    # --- LOGOUT ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")])
        return [b""]

    start_response("404 Not Found", [("Content-Type", "text/html")])
    return [render_layout("Error", "<h1>404</h1>", u_data).encode("utf-8")]