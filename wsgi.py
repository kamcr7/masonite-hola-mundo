# -*- coding: utf-8 -*-
import hashlib
import json
import hmac
import time
import urllib.parse
import urllib.request
import cgi
from datetime import datetime
from urllib.parse import parse_qs
import mysql.connector
import os
import base64

# =========================================================
# CONFIG
# =========================================================
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@mysql.railway.internal:3306/railway')

RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

JWT_SECRET = "CAMBIA_ESTA_LLAVE_SUPER_SECRETA_2026"
JWT_EXPIRE_SECONDS = 60 * 60 * 8  # 8 horas
PAGE_SIZE = 5

# =========================================================
# HELPERS GENERALES
# =========================================================
def html_escape(s):
    s = s or ""
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&#39;")
    )

def limpiar_espacios(texto):
    return " ".join((texto or "").strip().split())

def hash_password(password):
    password = password or ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# =========================================================
# FUNCIONES DE ENCODING DE JWT
# =========================================================
def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def jwt_encode(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    
    signature_b64 = b64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

# =========================================================
# CONEXIÓN A LA BASE DE DATOS MYSQL
# =========================================================
def conectar_bd():
    try:
        result = urllib.parse.urlparse(DB_URL)
        
        conn = mysql.connector.connect(
            host=result.hostname,
            port=result.port,
            user=result.username,
            password=result.password,
            database=result.path[1:]
        )
        print("Conexión exitosa a la base de datos MySQL.")
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar con la base de datos: {err}")
        return None

# =========================================================
# FUNCIONES DE REDIRECCIÓN
# =========================================================
def redirect(start_response, location, extra_headers=None):
    headers = [("Location", location)]
    if extra_headers:
        headers.extend(extra_headers)
    start_response("303 See Other", headers)
    return [b""]

# =========================================================
# FUNCIONES DE VALIDACIÓN DE JWT
# =========================================================
def verify_jwt(environ):
    token = environ.get('HTTP_COOKIE', "").split("=")[-1]
    if not token:
        return None

    parts = token.split(".")
    if len(parts) != 3:
        return None

    payload_b64 = parts[1]
    try:
        payload = json.loads(b64url_encode(payload_b64).encode("utf-8").decode("utf-8"))
        if payload["exp"] < time.time():
            return None
        return payload
    except Exception as e:
        print(e)
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        idEstadoUsuario INT NOT NULL DEFAULT 1
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
# FUNCIONES DE OBTENER DATOS DEL FORMULARIO
# =========================================================
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
# FUNCION PARA CREAR COOKIES
# =========================================================
def make_cookie(name, value, max_age=None, path="/", http_only=True):
    cookie = f"{name}={value}; Path={path}; SameSite=Lax"
    if max_age is not None:
        cookie += f"; Max-Age={max_age}"
    if http_only:
        cookie += "; HttpOnly"
    return ("Set-Cookie", cookie)

# =========================================================
# FUNCIONES CRUD PARA USUARIOS
# =========================================================
def crear_usuario(nombre, correo, celular, contrasena, estado):
    conn = conectar_bd()
    if conn is None:
        return None
    cur = conn.cursor()
    
    # Insertar nuevo usuario
    cur.execute("""
    INSERT INTO usuarios (strNombreUsuario, strCorreo, strNumeroCelular, strPwd, idEstadoUsuario)
    VALUES (%s, %s, %s, %s, %s)
    """, (nombre, correo, celular, hash_password(contrasena), estado))
    
    conn.commit()
    cur.close()
    conn.close()

def obtener_usuarios(page=1):
    conn = conectar_bd()
    if conn is None:
        return None
    cur = conn.cursor()
    
    # Paginación para 5 usuarios por página
    offset = (page - 1) * 5
    cur.execute("SELECT * FROM usuarios LIMIT 5 OFFSET %s", (offset,))
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return usuarios

def editar_usuario(usuario_id, nombre, correo, celular, contrasena, estado):
    conn = conectar_bd()
    if conn is None:
        return None
    cur = conn.cursor()
    
    # Actualizar usuario
    cur.execute("""
    UPDATE usuarios
    SET strNombreUsuario = %s, strCorreo = %s, strNumeroCelular = %s, strPwd = %s, idEstadoUsuario = %s
    WHERE id = %s
    """, (nombre, correo, celular, hash_password(contrasena), estado, usuario_id))
    
    conn.commit()
    cur.close()
    conn.close()

def eliminar_usuario(usuario_id):
    conn = conectar_bd()
    if conn is None:
        return None
    cur = conn.cursor()
    
    # Eliminar usuario
    cur.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
    
    conn.commit()
    cur.close()
    conn.close()

def obtener_detalle_usuario(usuario_id):
    conn = conectar_bd()
    if conn is None:
        return None
    cur = conn.cursor()
    
    # Obtener detalles de un usuario
    cur.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return usuario

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
# HELPERS EXTRA PARA CRUD
# =========================================================
def json_response(start_response, data, status="200 OK"):
    start_response(status, [("Content-Type", "application/json; charset=utf-8")])
    return [json.dumps(data).encode("utf-8")]

def qint(v, default=1):
    try:
        return int(v)
    except:
        return default

def qs_get(environ, key, default=""):
    qs = parse_qs(environ.get("QUERY_STRING", ""))
    return (qs.get(key, [default])[0] or default)

def paginacion_html(base_url, page, total_rows):
    total_pages = max(1, (total_rows + PAGE_SIZE - 1) // PAGE_SIZE)
    html = '<div style="margin-top:18px;display:flex;gap:8px;flex-wrap:wrap;">'

    if page > 1:
        html += f'<a href="{base_url}?page=1" style="padding:8px 12px;background:#0f4573;color:#fff;text-decoration:none;border-radius:6px;">«</a>'
        html += f'<a href="{base_url}?page={page-1}" style="padding:8px 12px;background:#0f4573;color:#fff;text-decoration:none;border-radius:6px;">‹</a>'

    ini = max(1, page - 2)
    fin = min(total_pages, page + 2)

    for i in range(ini, fin + 1):
        bg = "#1f7ae0" if i == page else "#ffffff"
        color = "#ffffff" if i == page else "#0f4573"
        html += f'<a href="{base_url}?page={i}" style="padding:8px 12px;background:{bg};color:{color};text-decoration:none;border:1px solid #0f4573;border-radius:6px;">{i}</a>'

    if page < total_pages:
        html += f'<a href="{base_url}?page={page+1}" style="padding:8px 12px;background:#0f4573;color:#fff;text-decoration:none;border-radius:6px;">›</a>'
        html += f'<a href="{base_url}?page={total_pages}" style="padding:8px 12px;background:#0f4573;color:#fff;text-decoration:none;border-radius:6px;">»</a>'

    html += "</div>"
    return html

def ensure_extra_tables():
    conn = conectar_bd()
    if not conn:
        return
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS permisos_perfil (
        id INT AUTO_INCREMENT PRIMARY KEY,
        idModulo INT NOT NULL,
        idPerfil INT NOT NULL,
        bitAgregar TINYINT(1) DEFAULT 0,
        bitEditar TINYINT(1) DEFAULT 0,
        bitConsulta TINYINT(1) DEFAULT 0,
        bitEliminar TINYINT(1) DEFAULT 0,
        bitDetalle TINYINT(1) DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu_modulo (
        id INT AUTO_INCREMENT PRIMARY KEY,
        idMenu INT,
        idModulo INT
    )
    """)

    # insertar módulos base si no existen
    cur.execute("SELECT COUNT(*) FROM modulos")
    total_mod = cur.fetchone()[0]
    if total_mod == 0:
        cur.execute("INSERT INTO modulos (strNombreModulo) VALUES ('Perfil')")
        cur.execute("INSERT INTO modulos (strNombreModulo) VALUES ('Módulo')")
        cur.execute("INSERT INTO modulos (strNombreModulo) VALUES ('Permisos-Perfil')")
        cur.execute("INSERT INTO modulos (strNombreModulo) VALUES ('Usuario')")

    conn.commit()
    cur.close()
    conn.close()

def get_dict_cursor():
    conn = conectar_bd()
    if not conn:
        return None, None
    return conn, conn.cursor(dictionary=True)

def upload_to_base64(file_item):
    if not file_item or not getattr(file_item, "filename", ""):
        return ""
    try:
        content = file_item.file.read()
        if not content:
            return ""
        return base64.b64encode(content).decode("utf-8")
    except:
        return ""

def top_actions_bar():
    return """
    <div style="background:#0f4573;color:white;padding:10px;display:flex;gap:30px;margin-top:15px;">
        <a href="/perfiles" style="color:white;text-decoration:none;">Perfil</a>
        <a href="/modulos" style="color:white;text-decoration:none;">Módulo</a>
        <a href="/permisos" style="color:white;text-decoration:none;">Permisos-Perfil</a>
        <a href="/usuarios" style="color:white;text-decoration:none;">Usuario</a>
    </div>
    """

# =========================================================
# PÁGINAS CRUD
# =========================================================
def page_dashboard(user_info):
    content = f"""
    <div class="card">
        <p>Sistema Corporativo - Clínica Santa Mónica</p>
        <h3>Bienvenido, <b>{html_escape(user_info['u'])}</b>.</h3>
        <p>Selecciona un módulo del menú Seguridad.</p>
        {top_actions_bar()}
    </div>
    """
    return render_layout("Dashboard", content, user_info, [("Dashboard", "/dashboard")])

def page_perfiles(user_info, page=1):
    conn, cur = get_dict_cursor()
    rows = []
    total = 0
    if conn:
        cur.execute("SELECT COUNT(*) c FROM perfiles")
        total = cur.fetchone()["c"]
        offset = (page - 1) * PAGE_SIZE
        cur.execute("SELECT * FROM perfiles ORDER BY id DESC LIMIT %s OFFSET %s", (PAGE_SIZE, offset))
        rows = cur.fetchall()
        cur.close()
        conn.close()

    trs = ""
    for r in rows:
        trs += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{html_escape(r['strNombrePerfil'])}</td>
            <td>{"Sí" if int(r['bitAdministrador']) == 1 else "No"}</td>
            <td>
                <a href="/perfiles/detalle?id={r['id']}">Detalle</a> |
                <a href="/perfiles/editar?id={r['id']}">Editar</a> |
                <form method="POST" action="/perfiles/eliminar" style="display:inline;" onsubmit="return confirm('¿Eliminar perfil?');">
                    <input type="hidden" name="id" value="{r['id']}">
                    <button type="submit">Eliminar</button>
                </form>
            </td>
        </tr>
        """
    if not trs:
        trs = "<tr><td colspan='4'>Sin registros</td></tr>"

    content = f"""
    <div class="card">
        <h2>CRUD Perfil</h2>
        <p><a href="/perfiles/nuevo">+ Nuevo perfil</a></p>
        <table border="1" cellpadding="8" cellspacing="0" width="100%">
            <tr><th>ID</th><th>Nombre Perfil</th><th>Administrador</th><th>Acciones</th></tr>
            {trs}
        </table>
        {paginacion_html('/perfiles', page, total)}
    </div>
    """
    return render_layout("Perfiles", content, user_info, [("Dashboard", "/dashboard"), ("Perfiles", "/perfiles")])

def page_perfil_form(user_info, row=None, error=""):
    row = row or {"id": "", "strNombrePerfil": "", "bitAdministrador": 0}
    checked = "checked" if int(row.get("bitAdministrador", 0)) == 1 else ""
    action = "/perfiles/guardar" if not row.get("id") else "/perfiles/actualizar"
    err = f"<div style='color:red;margin-bottom:10px;'>{html_escape(error)}</div>" if error else ""
    content = f"""
    <div class="card">
        <h2>{'Editar' if row.get('id') else 'Nuevo'} Perfil</h2>
        {err}
        <form method="POST" action="{action}">
            <input type="hidden" name="id" value="{row.get('id','')}">
            <p>Nombre Perfil</p>
            <input type="text" name="strNombrePerfil" value="{html_escape(row.get('strNombrePerfil',''))}" style="width:100%;padding:10px;" required>
            <p><label><input type="checkbox" name="bitAdministrador" value="1" {checked}> Administrador</label></p>
            <p>
                <button type="submit">Guardar</button>
                <a href="/perfiles">Cancelar</a>
            </p>
        </form>
    </div>
    """
    return render_layout("Perfil", content, user_info, [("Dashboard", "/dashboard"), ("Perfiles", "/perfiles")])

def page_perfil_detalle(user_info, row):
    content = f"""
    <div class="card">
        <h2>Detalle Perfil</h2>
        <p><b>ID:</b> {row['id']}</p>
        <p><b>Nombre:</b> {html_escape(row['strNombrePerfil'])}</p>
        <p><b>Administrador:</b> {"Sí" if int(row['bitAdministrador']) == 1 else "No"}</p>
        <p><a href="/perfiles">Volver</a></p>
    </div>
    """
    return render_layout("Detalle Perfil", content, user_info, [("Dashboard", "/dashboard"), ("Perfiles", "/perfiles")])

def page_modulos(user_info, page=1):
    conn, cur = get_dict_cursor()
    rows = []
    total = 0
    if conn:
        cur.execute("SELECT COUNT(*) c FROM modulos")
        total = cur.fetchone()["c"]
        offset = (page - 1) * PAGE_SIZE
        cur.execute("SELECT * FROM modulos ORDER BY id DESC LIMIT %s OFFSET %s", (PAGE_SIZE, offset))
        rows = cur.fetchall()
        cur.close()
        conn.close()

    trs = ""
    for r in rows:
        trs += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{html_escape(r['strNombreModulo'])}</td>
            <td>
                <a href="/modulos/detalle?id={r['id']}">Detalle</a> |
                <a href="/modulos/editar?id={r['id']}">Editar</a> |
                <form method="POST" action="/modulos/eliminar" style="display:inline;" onsubmit="return confirm('¿Eliminar módulo?');">
                    <input type="hidden" name="id" value="{r['id']}">
                    <button type="submit">Eliminar</button>
                </form>
            </td>
        </tr>
        """
    if not trs:
        trs = "<tr><td colspan='3'>Sin registros</td></tr>"

    content = f"""
    <div class="card">
        <h2>CRUD Módulo</h2>
        <p><a href="/modulos/nuevo">+ Nuevo módulo</a></p>
        <table border="1" cellpadding="8" cellspacing="0" width="100%">
            <tr><th>ID</th><th>Nombre Módulo</th><th>Acciones</th></tr>
            {trs}
        </table>
        {paginacion_html('/modulos', page, total)}
    </div>
    """
    return render_layout("Módulos", content, user_info, [("Dashboard", "/dashboard"), ("Módulos", "/modulos")])

def page_modulo_form(user_info, row=None, error=""):
    row = row or {"id": "", "strNombreModulo": ""}
    action = "/modulos/guardar" if not row.get("id") else "/modulos/actualizar"
    err = f"<div style='color:red;margin-bottom:10px;'>{html_escape(error)}</div>" if error else ""
    content = f"""
    <div class="card">
        <h2>{'Editar' if row.get('id') else 'Nuevo'} Módulo</h2>
        {err}
        <form method="POST" action="{action}">
            <input type="hidden" name="id" value="{row.get('id','')}">
            <p>Nombre Módulo</p>
            <input type="text" name="strNombreModulo" value="{html_escape(row.get('strNombreModulo',''))}" style="width:100%;padding:10px;" required>
            <p>
                <button type="submit">Guardar</button>
                <a href="/modulos">Cancelar</a>
            </p>
        </form>
    </div>
    """
    return render_layout("Módulo", content, user_info, [("Dashboard", "/dashboard"), ("Módulos", "/modulos")])

def page_modulo_detalle(user_info, row):
    content = f"""
    <div class="card">
        <h2>Detalle Módulo</h2>
        <p><b>ID:</b> {row['id']}</p>
        <p><b>Nombre:</b> {html_escape(row['strNombreModulo'])}</p>
        <p><a href="/modulos">Volver</a></p>
    </div>
    """
    return render_layout("Detalle Módulo", content, user_info, [("Dashboard", "/dashboard"), ("Módulos", "/modulos")])

def page_permisos(user_info, page=1):
    conn, cur = get_dict_cursor()
    rows = []
    total = 0
    perfiles = []
    modulos = []
    if conn:
        cur.execute("SELECT id, strNombrePerfil FROM perfiles ORDER BY strNombrePerfil")
        perfiles = cur.fetchall()
        cur.execute("SELECT id, strNombreModulo FROM modulos ORDER BY strNombreModulo")
        modulos = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) c
            FROM permisos_perfil pp
            INNER JOIN perfiles p ON p.id=pp.idPerfil
            INNER JOIN modulos m ON m.id=pp.idModulo
        """)
        total = cur.fetchone()["c"]

        offset = (page - 1) * PAGE_SIZE
        cur.execute("""
            SELECT pp.*, p.strNombrePerfil, m.strNombreModulo
            FROM permisos_perfil pp
            INNER JOIN perfiles p ON p.id=pp.idPerfil
            INNER JOIN modulos m ON m.id=pp.idModulo
            ORDER BY pp.id DESC
            LIMIT %s OFFSET %s
        """, (PAGE_SIZE, offset))
        rows = cur.fetchall()
        cur.close()
        conn.close()

    trs = ""
    for r in rows:
        trs += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{html_escape(r['strNombrePerfil'])}</td>
            <td>{html_escape(r['strNombreModulo'])}</td>
            <td>{r['bitAgregar']}</td>
            <td>{r['bitEditar']}</td>
            <td>{r['bitConsulta']}</td>
            <td>{r['bitEliminar']}</td>
            <td>{r['bitDetalle']}</td>
            <td>
                <a href="/permisos/detalle?id={r['id']}">Detalle</a> |
                <a href="/permisos/editar?id={r['id']}">Editar</a> |
                <form method="POST" action="/permisos/eliminar" style="display:inline;" onsubmit="return confirm('¿Eliminar permiso?');">
                    <input type="hidden" name="id" value="{r['id']}">
                    <button type="submit">Eliminar</button>
                </form>
            </td>
        </tr>
        """
    if not trs:
        trs = "<tr><td colspan='9'>Sin registros</td></tr>"

    content = f"""
    <div class="card">
        <h2>CRUD Permisos-Perfil</h2>
        <p><a href="/permisos/nuevo">+ Nuevo permiso</a></p>
        <table border="1" cellpadding="6" cellspacing="0" width="100%">
            <tr>
                <th>ID</th><th>Perfil</th><th>Módulo</th><th>Agregar</th><th>Editar</th>
                <th>Consultar</th><th>Eliminar</th><th>Detalle</th><th>Acciones</th>
            </tr>
            {trs}
        </table>
        {paginacion_html('/permisos', page, total)}
    </div>
    """
    return render_layout("Permisos", content, user_info, [("Dashboard", "/dashboard"), ("Permisos", "/permisos")])

def page_permiso_form(user_info, row=None, error=""):
    row = row or {
        "id": "", "idPerfil": "", "idModulo": "",
        "bitAgregar": 0, "bitEditar": 0, "bitConsulta": 0, "bitEliminar": 0, "bitDetalle": 0
    }

    conn, cur = get_dict_cursor()
    perfiles = []
    modulos = []
    if conn:
        cur.execute("SELECT id, strNombrePerfil FROM perfiles ORDER BY strNombrePerfil")
        perfiles = cur.fetchall()
        cur.execute("SELECT id, strNombreModulo FROM modulos ORDER BY strNombreModulo")
        modulos = cur.fetchall()
        cur.close()
        conn.close()

    perfiles_opts = ""
    for p in perfiles:
        sel = "selected" if str(p["id"]) == str(row.get("idPerfil", "")) else ""
        perfiles_opts += f'<option value="{p["id"]}" {sel}>{html_escape(p["strNombrePerfil"])}</option>'

    modulos_opts = ""
    for m in modulos:
        sel = "selected" if str(m["id"]) == str(row.get("idModulo", "")) else ""
        modulos_opts += f'<option value="{m["id"]}" {sel}>{html_escape(m["strNombreModulo"])}</option>'

    action = "/permisos/guardar" if not row.get("id") else "/permisos/actualizar"
    err = f"<div style='color:red;margin-bottom:10px;'>{html_escape(error)}</div>" if error else ""

    def ck(v):
        return "checked" if int(v) == 1 else ""

    content = f"""
    <div class="card">
        <h2>{'Editar' if row.get('id') else 'Nuevo'} Permiso</h2>
        {err}
        <form method="POST" action="{action}">
            <input type="hidden" name="id" value="{row.get('id','')}">

            <p>Perfil</p>
            <select name="idPerfil" style="width:100%;padding:10px;" required>{perfiles_opts}</select>

            <p>Módulo</p>
            <select name="idModulo" style="width:100%;padding:10px;" required>{modulos_opts}</select>

            <p><label><input type="checkbox" name="bitAgregar" value="1" {ck(row.get("bitAgregar",0))}> Agregar</label></p>
            <p><label><input type="checkbox" name="bitEditar" value="1" {ck(row.get("bitEditar",0))}> Editar</label></p>
            <p><label><input type="checkbox" name="bitConsulta" value="1" {ck(row.get("bitConsulta",0))}> Consultar</label></p>
            <p><label><input type="checkbox" name="bitEliminar" value="1" {ck(row.get("bitEliminar",0))}> Eliminar</label></p>
            <p><label><input type="checkbox" name="bitDetalle" value="1" {ck(row.get("bitDetalle",0))}> Detalle</label></p>

            <p>
                <button type="submit">Guardar</button>
                <a href="/permisos">Cancelar</a>
            </p>
        </form>
    </div>
    """
    return render_layout("Permisos", content, user_info, [("Dashboard", "/dashboard"), ("Permisos", "/permisos")])

def page_permiso_detalle(user_info, row):
    content = f"""
    <div class="card">
        <h2>Detalle Permiso</h2>
        <p><b>ID:</b> {row['id']}</p>
        <p><b>ID Perfil:</b> {row['idPerfil']}</p>
        <p><b>ID Módulo:</b> {row['idModulo']}</p>
        <p><b>Agregar:</b> {row['bitAgregar']}</p>
        <p><b>Editar:</b> {row['bitEditar']}</p>
        <p><b>Consultar:</b> {row['bitConsulta']}</p>
        <p><b>Eliminar:</b> {row['bitEliminar']}</p>
        <p><b>Detalle:</b> {row['bitDetalle']}</p>
        <p><a href="/permisos">Volver</a></p>
    </div>
    """
    return render_layout("Detalle Permiso", content, user_info, [("Dashboard", "/dashboard"), ("Permisos", "/permisos")])

def page_usuarios(user_info, page=1):
    conn, cur = get_dict_cursor()
    rows = []
    total = 0
    if conn:
        cur.execute("SELECT COUNT(*) c FROM usuarios")
        total = cur.fetchone()["c"]
        offset = (page - 1) * PAGE_SIZE
        cur.execute("""
            SELECT u.*, p.strNombrePerfil
            FROM usuarios u
            LEFT JOIN perfiles p ON p.id=u.idPerfil
            ORDER BY u.id DESC
            LIMIT %s OFFSET %s
        """, (PAGE_SIZE, offset))
        rows = cur.fetchall()
        cur.close()
        conn.close()

    trs = ""
    for r in rows:
        img_html = ""
        if r.get("imgUsuario"):
            img_html = f'<img src="data:image/png;base64,{r["imgUsuario"]}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;"> '

        trs += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{img_html}{html_escape(r['strNombreUsuario'])}</td>
            <td>{html_escape(r.get('strNombrePerfil') or '')}</td>
            <td>{html_escape(r.get('strCorreo') or '')}</td>
            <td>{html_escape(r.get('strNumeroCelular') or '')}</td>
            <td>{r.get('idEstadoUsuario',1)}</td>
            <td>
                <a href="/usuarios/detalle?id={r['id']}">Detalle</a> |
                <a href="/usuarios/editar?id={r['id']}">Editar</a> |
                <form method="POST" action="/usuarios/eliminar" style="display:inline;" onsubmit="return confirm('¿Eliminar usuario?');">
                    <input type="hidden" name="id" value="{r['id']}">
                    <button type="submit">Eliminar</button>
                </form>
            </td>
        </tr>
        """
    if not trs:
        trs = "<tr><td colspan='7'>Sin registros</td></tr>"

    content = f"""
    <div class="card">
        <h2>CRUD Usuario</h2>
        <p><a href="/usuarios/nuevo">+ Nuevo usuario</a></p>
        <table border="1" cellpadding="6" cellspacing="0" width="100%">
            <tr>
                <th>ID</th><th>Usuario</th><th>Perfil</th><th>Correo</th>
                <th>Celular</th><th>Estado</th><th>Acciones</th>
            </tr>
            {trs}
        </table>
        {paginacion_html('/usuarios', page, total)}
    </div>
    """
    return render_layout("Usuarios", content, user_info, [("Dashboard", "/dashboard"), ("Usuarios", "/usuarios")])

def page_usuario_form(user_info, row=None, error=""):
    row = row or {
        "id": "", "strNombreUsuario": "", "idPerfil": "", "strCorreo": "",
        "strNumeroCelular": "", "idEstadoUsuario": 1
    }

    conn, cur = get_dict_cursor()
    perfiles = []
    if conn:
        cur.execute("SELECT id, strNombrePerfil FROM perfiles ORDER BY strNombrePerfil")
        perfiles = cur.fetchall()
        cur.close()
        conn.close()

    perfiles_opts = ""
    for p in perfiles:
        sel = "selected" if str(p["id"]) == str(row.get("idPerfil", "")) else ""
        perfiles_opts += f'<option value="{p["id"]}" {sel}>{html_escape(p["strNombrePerfil"])}</option>'

    action = "/usuarios/guardar" if not row.get("id") else "/usuarios/actualizar"
    err = f"<div style='color:red;margin-bottom:10px;'>{html_escape(error)}</div>" if error else ""

    content = f"""
    <div class="card">
        <h2>{'Editar' if row.get('id') else 'Nuevo'} Usuario</h2>
        {err}
        <form method="POST" action="{action}" enctype="multipart/form-data">
            <input type="hidden" name="id" value="{row.get('id','')}">

            <p>Usuario</p>
            <input type="text" name="strNombreUsuario" value="{html_escape(row.get('strNombreUsuario',''))}" style="width:100%;padding:10px;" required>

            <p>Perfil</p>
            <select name="idPerfil" style="width:100%;padding:10px;" required>{perfiles_opts}</select>

            <p>Correo</p>
            <input type="email" name="strCorreo" value="{html_escape(row.get('strCorreo',''))}" style="width:100%;padding:10px;" required>

            <p>Celular</p>
            <input type="text" name="strNumeroCelular" value="{html_escape(row.get('strNumeroCelular',''))}" style="width:100%;padding:10px;" required>

            <p>Contraseña</p>
            <input type="password" name="strPwd" style="width:100%;padding:10px;" {'required' if not row.get('id') else ''}>

            <p>Estado</p>
            <select name="idEstadoUsuario" style="width:100%;padding:10px;">
                <option value="1" {"selected" if str(row.get("idEstadoUsuario","1")) == "1" else ""}>Activo</option>
                <option value="0" {"selected" if str(row.get("idEstadoUsuario","1")) == "0" else ""}>Inactivo</option>
            </select>

            <p>Imagen</p>
            <input type="file" name="imgUsuario" accept="image/*">

            <p>
                <button type="submit">Guardar</button>
                <a href="/usuarios">Cancelar</a>
            </p>
        </form>
    </div>
    """
    return render_layout("Usuario", content, user_info, [("Dashboard", "/dashboard"), ("Usuarios", "/usuarios")])

def page_usuario_detalle(user_info, row):
    img_html = ""
    if row.get("imgUsuario"):
        img_html = f'<p><img src="data:image/png;base64,{row["imgUsuario"]}" style="max-width:160px;border-radius:10px;"></p>'

    content = f"""
    <div class="card">
        <h2>Detalle Usuario</h2>
        {img_html}
        <p><b>ID:</b> {row['id']}</p>
        <p><b>Usuario:</b> {html_escape(row['strNombreUsuario'])}</p>
        <p><b>Perfil:</b> {row.get('idPerfil','')}</p>
        <p><b>Correo:</b> {html_escape(row.get('strCorreo') or '')}</p>
        <p><b>Celular:</b> {html_escape(row.get('strNumeroCelular') or '')}</p>
        <p><b>Estado:</b> {row.get('idEstadoUsuario',1)}</p>
        <p><a href="/usuarios">Volver</a></p>
    </div>
    """
    return render_layout("Detalle Usuario", content, user_info, [("Dashboard", "/dashboard"), ("Usuarios", "/usuarios")])

# =========================================================
# APP PRINCIPAL - REEMPLAZA TU application POR ESTA
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    init_db()
    ensure_extra_tables()

    # LOGIN
    if path in ["/", "/login"] and method == "GET":
        content = """<div class="card" style="max-width:350px; text-align:center;">
            <h2>Clínica Santa Mónica</h2>
            <form id="fL">
            <input type="text" name="u" placeholder="Usuario" style="width:100%; padding:10px; margin:5px 0;" required>
            <input type="password" name="p" placeholder="Contraseña" style="width:100%; padding:10px; margin:5px 0;" required>
            <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
            <button type="submit" style="width:100%; padding:10px; background:#0f4573; color:white; border:none; margin-top:10px;">Entrar</button>
            </form>
            <div id="msg" style="color:red; margin-top:10px;"></div>
            </div>
            <script>
            document.getElementById('fL').onsubmit = async (e) => {
                e.preventDefault();
                const fd = new FormData(e.target);
                const res = await fetch('/api/login', {method:'POST', body:fd});
                const d = await res.json();
                if(d.ok) location.href='/dashboard';
                else document.getElementById('msg').innerText=d.msg;
            }
            </script>"""
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u_in = fs.getvalue("u")
        p_in = hash_password(fs.getvalue("p", ""))

        conn, cur = get_dict_cursor()
        if not conn:
            return json_response(start_response, {"ok": False, "msg": "Sin conexión a BD"})

        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s", (u_in,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and user.get("strPwd") == p_in:
            if int(user.get("idEstadoUsuario", 1)) != 1:
                return json_response(start_response, {"ok": False, "msg": "Usuario inactivo"})

            tk = jwt_encode({"u": u_in, "exp": time.time() + 3600})
            start_response("200 OK", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")
            ])
            return [json.dumps({"ok": True}).encode("utf-8")]

        return json_response(start_response, {"ok": False, "msg": "Credenciales inválidas"})

    # PROTECCIÓN
    user_info = verify_jwt(environ)
    if not user_info:
        if path.startswith("/api/"):
            return json_response(start_response, {"ok": False, "msg": "No autorizado"}, "401 Unauthorized")
        start_response("303 See Other", [("Location", "/login")])
        return [b""]

    # DASHBOARD
    if path == "/dashboard":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_dashboard(user_info).encode("utf-8")]

    # LOGOUT
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")])
        return [b""]

    # PERFILES
    if path == "/perfiles":
        page = qint(qs_get(environ, "page", "1"), 1)
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_perfiles(user_info, page).encode("utf-8")]

    if path == "/perfiles/nuevo":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_perfil_form(user_info).encode("utf-8")]

    if path == "/perfiles/guardar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        nombre = (fs.getvalue("strNombrePerfil") or "").strip()
        admin = 1 if fs.getvalue("bitAdministrador") == "1" else 0
        if not nombre:
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [page_perfil_form(user_info, error="Nombre requerido").encode("utf-8")]
        conn, cur = get_dict_cursor()
        cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s, %s)", (nombre, admin))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/perfiles")

    if path == "/perfiles/editar":
        pid = qint(qs_get(environ, "id", "0"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("SELECT * FROM perfiles WHERE id=%s", (pid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_perfil_form(user_info, row=row).encode("utf-8")]

    if path == "/perfiles/actualizar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        pid = qint(fs.getvalue("id"), 0)
        nombre = (fs.getvalue("strNombrePerfil") or "").strip()
        admin = 1 if fs.getvalue("bitAdministrador") == "1" else 0
        conn, cur = get_dict_cursor()
        cur.execute("UPDATE perfiles SET strNombrePerfil=%s, bitAdministrador=%s WHERE id=%s", (nombre, admin, pid))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/perfiles")

    if path == "/perfiles/eliminar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        pid = qint(fs.getvalue("id"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("DELETE FROM perfiles WHERE id=%s", (pid,))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/perfiles")

    if path == "/perfiles/detalle":
        pid = qint(qs_get(environ, "id", "0"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("SELECT * FROM perfiles WHERE id=%s", (pid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_perfil_detalle(user_info, row).encode("utf-8")]

    # MODULOS
    if path == "/modulos":
        page = qint(qs_get(environ, "page", "1"), 1)
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_modulos(user_info, page).encode("utf-8")]

    if path == "/modulos/nuevo":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_modulo_form(user_info).encode("utf-8")]

    if path == "/modulos/guardar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        nombre = (fs.getvalue("strNombreModulo") or "").strip()
        conn, cur = get_dict_cursor()
        cur.execute("INSERT INTO modulos (strNombreModulo) VALUES (%s)", (nombre,))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/modulos")

    if path == "/modulos/editar":
        mid = qint(qs_get(environ, "id", "0"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("SELECT * FROM modulos WHERE id=%s", (mid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_modulo_form(user_info, row=row).encode("utf-8")]

    if path == "/modulos/actualizar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        mid = qint(fs.getvalue("id"), 0)
        nombre = (fs.getvalue("strNombreModulo") or "").strip()
        conn, cur = get_dict_cursor()
        cur.execute("UPDATE modulos SET strNombreModulo=%s WHERE id=%s", (nombre, mid))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/modulos")

    if path == "/modulos/eliminar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        mid = qint(fs.getvalue("id"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("DELETE FROM modulos WHERE id=%s", (mid,))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/modulos")

    if path == "/modulos/detalle":
        mid = qint(qs_get(environ, "id", "0"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("SELECT * FROM modulos WHERE id=%s", (mid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_modulo_detalle(user_info, row).encode("utf-8")]

    # PERMISOS
    if path == "/permisos":
        page = qint(qs_get(environ, "page", "1"), 1)
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_permisos(user_info, page).encode("utf-8")]

    if path == "/permisos/nuevo":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_permiso_form(user_info).encode("utf-8")]

    if path == "/permisos/guardar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        idPerfil = qint(fs.getvalue("idPerfil"), 0)
        idModulo = qint(fs.getvalue("idModulo"), 0)
        a = 1 if fs.getvalue("bitAgregar") == "1" else 0
        e = 1 if fs.getvalue("bitEditar") == "1" else 0
        c = 1 if fs.getvalue("bitConsulta") == "1" else 0
        el = 1 if fs.getvalue("bitEliminar") == "1" else 0
        d = 1 if fs.getvalue("bitDetalle") == "1" else 0
        conn, cur = get_dict_cursor()
        cur.execute("""
            INSERT INTO permisos_perfil (idModulo, idPerfil, bitAgregar, bitEditar, bitConsulta, bitEliminar, bitDetalle)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (idModulo, idPerfil, a, e, c, el, d))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/permisos")

    if path == "/permisos/editar":
        pid = qint(qs_get(environ, "id", "0"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("SELECT * FROM permisos_perfil WHERE id=%s", (pid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_permiso_form(user_info, row=row).encode("utf-8")]

    if path == "/permisos/actualizar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        pid = qint(fs.getvalue("id"), 0)
        idPerfil = qint(fs.getvalue("idPerfil"), 0)
        idModulo = qint(fs.getvalue("idModulo"), 0)
        a = 1 if fs.getvalue("bitAgregar") == "1" else 0
        e = 1 if fs.getvalue("bitEditar") == "1" else 0
        c = 1 if fs.getvalue("bitConsulta") == "1" else 0
        el = 1 if fs.getvalue("bitEliminar") == "1" else 0
        d = 1 if fs.getvalue("bitDetalle") == "1" else 0
        conn, cur = get_dict_cursor()
        cur.execute("""
            UPDATE permisos_perfil
            SET idModulo=%s, idPerfil=%s, bitAgregar=%s, bitEditar=%s, bitConsulta=%s, bitEliminar=%s, bitDetalle=%s
            WHERE id=%s
        """, (idModulo, idPerfil, a, e, c, el, d, pid))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/permisos")

    if path == "/permisos/eliminar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        pid = qint(fs.getvalue("id"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("DELETE FROM permisos_perfil WHERE id=%s", (pid,))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/permisos")

    if path == "/permisos/detalle":
        pid = qint(qs_get(environ, "id", "0"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("SELECT * FROM permisos_perfil WHERE id=%s", (pid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_permiso_detalle(user_info, row).encode("utf-8")]

    # USUARIOS
    if path == "/usuarios":
        page = qint(qs_get(environ, "page", "1"), 1)
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_usuarios(user_info, page).encode("utf-8")]

    if path == "/usuarios/nuevo":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_usuario_form(user_info).encode("utf-8")]

    if path == "/usuarios/guardar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        nombre = (fs.getvalue("strNombreUsuario") or "").strip()
        idPerfil = qint(fs.getvalue("idPerfil"), 0)
        correo = (fs.getvalue("strCorreo") or "").strip()
        celular = (fs.getvalue("strNumeroCelular") or "").strip()
        pwd = (fs.getvalue("strPwd") or "").strip()
        estado = qint(fs.getvalue("idEstadoUsuario"), 1)
        img_b64 = upload_to_base64(fs["imgUsuario"]) if "imgUsuario" in fs else ""

        conn, cur = get_dict_cursor()
        cur.execute("""
            INSERT INTO usuarios (strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo, strNumeroCelular, imgUsuario)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (nombre, idPerfil, hash_password(pwd), estado, correo, celular, img_b64))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/usuarios")

    if path == "/usuarios/editar":
        uid = qint(qs_get(environ, "id", "0"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("SELECT * FROM usuarios WHERE id=%s", (uid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_usuario_form(user_info, row=row).encode("utf-8")]

    if path == "/usuarios/actualizar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        uid = qint(fs.getvalue("id"), 0)
        nombre = (fs.getvalue("strNombreUsuario") or "").strip()
        idPerfil = qint(fs.getvalue("idPerfil"), 0)
        correo = (fs.getvalue("strCorreo") or "").strip()
        celular = (fs.getvalue("strNumeroCelular") or "").strip()
        pwd = (fs.getvalue("strPwd") or "").strip()
        estado = qint(fs.getvalue("idEstadoUsuario"), 1)
        img_b64 = upload_to_base64(fs["imgUsuario"]) if "imgUsuario" in fs else ""

        conn, cur = get_dict_cursor()
        if img_b64 and pwd:
            cur.execute("""
                UPDATE usuarios
                SET strNombreUsuario=%s, idPerfil=%s, strPwd=%s, idEstadoUsuario=%s, strCorreo=%s, strNumeroCelular=%s, imgUsuario=%s
                WHERE id=%s
            """, (nombre, idPerfil, hash_password(pwd), estado, correo, celular, img_b64, uid))
        elif img_b64:
            cur.execute("""
                UPDATE usuarios
                SET strNombreUsuario=%s, idPerfil=%s, idEstadoUsuario=%s, strCorreo=%s, strNumeroCelular=%s, imgUsuario=%s
                WHERE id=%s
            """, (nombre, idPerfil, estado, correo, celular, img_b64, uid))
        elif pwd:
            cur.execute("""
                UPDATE usuarios
                SET strNombreUsuario=%s, idPerfil=%s, strPwd=%s, idEstadoUsuario=%s, strCorreo=%s, strNumeroCelular=%s
                WHERE id=%s
            """, (nombre, idPerfil, hash_password(pwd), estado, correo, celular, uid))
        else:
            cur.execute("""
                UPDATE usuarios
                SET strNombreUsuario=%s, idPerfil=%s, idEstadoUsuario=%s, strCorreo=%s, strNumeroCelular=%s
                WHERE id=%s
            """, (nombre, idPerfil, estado, correo, celular, uid))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/usuarios")

    if path == "/usuarios/eliminar" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        uid = qint(fs.getvalue("id"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("DELETE FROM usuarios WHERE id=%s", (uid,))
        conn.commit()
        cur.close(); conn.close()
        return redirect(start_response, "/usuarios")

    if path == "/usuarios/detalle":
        uid = qint(qs_get(environ, "id", "0"), 0)
        conn, cur = get_dict_cursor()
        cur.execute("SELECT * FROM usuarios WHERE id=%s", (uid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [page_usuario_detalle(user_info, row).encode("utf-8")]

    # 404
    start_response("404 Not Found", [("Content-Type", "text/html; charset=utf-8")])
    return [render_layout("Error", "<div class='card'><h1>404</h1><p>Página no encontrada</p></div>", user_info).encode("utf-8")]