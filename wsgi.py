# -*- coding: utf-8 -*-
import hashlib
import json
import hmac
import time
import urllib.parse
import urllib.request
import cgi
from datetime import datetime
import mysql.connector
import os
from urllib.parse import urlparse

# =========================================================
# CONFIG
# =========================================================
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@nozomi.proxy.rlyw.net:28752/railway')

# =========================================================
# CONEXIÓN A LA BASE DE DATOS MYSQL
# =========================================================
def conectar_bd():
    try:
        # Usamos el URL de la base de datos para obtener la información necesaria
        result = urlparse(DB_URL)

        # Asegurarnos de que result.path tenga el nombre de la base de datos sin '/'
        db_name = result.path[1:] if result.path.startswith('/') else result.path  # Eliminar '/' al principio, si existe

        conn = mysql.connector.connect(
            host=result.hostname,
            port=result.port,
            user=result.username,
            password=result.password,
            database=db_name
        )
        print("Conexión exitosa a la base de datos MySQL.")
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar con la base de datos: {err}")
        return None

# =========================================================
# INIT DB (Crear usuario ADMIN por defecto)
# =========================================================
def init_db():
    conn = conectar_bd()
    if conn is None:
        return  # Si no se pudo conectar, no continuamos

    cur = conn.cursor()

    # Crear tabla usuarios si no existe
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        strNombreUsuario VARCHAR(50) NOT NULL UNIQUE,
        strPwd VARCHAR(255) NOT NULL,
        strCorreo VARCHAR(150) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Insertar usuario admin si no existe
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO usuarios (strNombreUsuario, strPwd, strCorreo)
        VALUES ('admin', %s, 'admin@example.com')
        """, (hash_password("123456"),))  # admin con contraseña 123456

    conn.commit()
    cur.close()
    conn.close()

# =========================================================
# FUNCIONES DE REDIRECCIÓN
# =========================================================
def redirect(start_response, location, extra_headers=None):
    headers = [("Location", location)]
    if extra_headers:
        headers.extend(extra_headers)
    start_response("303 See Other", headers)
    return [b""]  # Redirige al login

def get_form_data(environ):
    fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)
    data = {}
    if hasattr(fs, "list") and fs.list:
        for item in fs.list:
            if item.filename:
                data[item.name] = item
            else:
                data[item.name] = item.value
    return fs, data

# =========================================================
# RENDER HTML PARA LOGIN
# =========================================================
def login_html(msg=""):
    alert = f'<div class="msg-bad">{html_escape(msg)}</div>' if msg else ""
    return render_layout(
        "Login",
        f"""
        <div class="login-wrap">
          <div class="login-card">
            <div class="login-head">
              <div class="logo-box">
                <div class="logo-mark">🩺</div>
                <div>
                  <div class="brand-title">Clínica De Especialidades</div>
                  <div class="brand-name">Santa Mónica</div>
                </div>
              </div>
              <div class="welcome">Bienvenido</div>
            </div>
            <div class="green-line"></div>

            {alert}

            <form id="loginForm" class="login-form" method="POST" action="/api/login">
              <div class="login-grid">
                <label>Usuario:</label>
                <input class="input" type="text" name="usuario" maxlength="30" required>

                <label>Contraseña:</label>
                <input class="input" type="password" name="password" maxlength="50" required>
              </div>

              <div style="margin-top:20px;display:flex;justify-content:flex-end;">
                <div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}"></div>
              </div>

              <div class="login-actions">
                <button class="btn" type="submit">Ingresar</button>
              </div>
            </form>

            <div id="loginMsg" style="margin-top:14px;"></div>
          </div>
        </div>

        <script>
        const form = document.getElementById('loginForm');
        const msg = document.getElementById('loginMsg');

        form.addEventListener('submit', async (e) => {{
          e.preventDefault();
          msg.innerHTML = '';

          const fd = new FormData(form);
          const captcha = (window.grecaptcha && grecaptcha.getResponse) ? grecaptcha.getResponse() : '';
          fd.append('g-recaptcha-response', captcha);

          const r = await fetch('/api/login', {{
            method: 'POST',
            body: fd
          }});
          const data = await r.json();

          if (data.ok) {{
            window.location.href = '/dashboard';
          }} else {{
            msg.innerHTML = '<div class="msg-bad">' + data.message + '</div>';
          }}
        }}); 
        </script>
        """
    )

# =========================================================
# RENDER LAYOUT (DASHBOARD)
# =========================================================
def dashboard_html(user):
    return render_layout(
        "Bienvenido",
        f"""
        <div class="title-row">
          <div class="title-icon">🏥</div>
          <div class="title-text">Sistema Corporativo - Clínica Santa Mónica</div>
        </div>
        <div class="green-line"></div>

        <div class="msg-ok">
          Bienvenido, <b>{html_escape(user["usuario"])}</b>.
        </div>

        <div class="topbar">
          <div class="menu-wrap">
            <a class="menu-item" href="/perfil">Perfil</a>
            <a class="menu-item" href="/modulos">Módulo</a>
            <a class="menu-item" href="/permisos-perfil">Permisos-Perfil</a>
            <a class="menu-item" href="/usuarios">Usuario</a>
          </div>
        </div>
        """,
        user=user
    )

def render_layout(title, content, user=None):
    menu_html = ""
    if user:
        menu_html = f"""
        <div class="topbar">
          <div class="menu-wrap">
            <a class="menu-item" href="/dashboard">Inicio</a>
            <a class="menu-item" href="/seguridad">Seguridad</a>
            <a class="menu-item" href="/logout">Salir</a>
          </div>
        </div>
        """
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_escape(title)}</title>
  <script src="https://www.google.com/recaptcha/api.js" async defer></script>
  <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;font-family:Arial,Helvetica,sans-serif;background:#efefef;color:#111;}}
    .page{{max-width:1280px;margin:0 auto;padding:18px 22px 40px;}}
    .topbar{{background:#0f4573;color:#fff;display:flex;justify-content:space-between;align-items:center;}}
    .menu-wrap{{display:flex;align-items:center;gap:10px;}}
    .menu-item{{color:#fff;text-decoration:none;padding:16px;}}
    .btn{{padding:12px 24px;background:#58a74a;color:#fff;cursor:pointer;text-decoration:none;border-radius:5px;}}
    .msg-bad{{color:#d88b8b;background:#fde2e2;padding:12px 14px;margin:12px 0;border-radius:5px;}}
    .login-wrap{{display:flex;justify-content:center;align-items:center;height:100vh;background:#f2f2f2;}}
    .login-card{{padding:24px;background:white;border-radius:10px;box-shadow:0 4px 12px rgba(0,0,0,0.1);width:400px;}}
    .input{{padding:12px;width:100%;margin:12px 0;border:1px solid #ccc;border-radius:5px;}}
  </style>
</head>
<body>
  {menu_html}
  <div class="page">
    {content}
  </div>
</body>
</html>
""" 

# =========================================================
# INIT DB AND RUTAS
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    # Initialize database with admin user
    init_db()

    # ---------------- LOGIN VIEW ----------------
    if path in ("/", "/login") and method == "GET":
        html = login_html()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [html.encode("utf-8")]

    # ---------------- API LOGIN ----------------
    if path == "/api/login" and method == "POST":
        fs, data = get_form_data(environ)
        usuario = limpiar_espacios(data.get("usuario", ""))
        password = data.get("password", "")

        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario = %s", (usuario,))
        row = cur.fetchone()

        if not row or row[2] != hash_password(password):  # Asumiendo que row[2] es la contraseña
            return json_response(start_response, {"ok": False, "message": "Usuario o contraseña incorrectos."})

        token = jwt_encode({
            "uid": row[0],
            "usuario": row[1],
            "exp": int(time.time()) + JWT_EXPIRE_SECONDS
        })

        start_response("200 OK", [
            ("Content-Type", "application/json; charset=utf-8"),
            make_cookie("token", token, max_age=JWT_EXPIRE_SECONDS)
        ])
        return [json.dumps({"ok": True}).encode("utf-8")]

    # ---------------- DASHBOARD ----------------
    if path == "/dashboard":
        # Aquí iría la lógica para mostrar la página de dashboard después de login
        html = dashboard_html({"usuario": "admin"})
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [html.encode("utf-8")]

    return redirect(start_response, "/login") 