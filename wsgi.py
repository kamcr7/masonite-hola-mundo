# -*- coding: utf-8 -*-
import os
import re
import cgi
import json
import hmac
import time
import base64
import hashlib
import urllib.request
import urllib.parse
from urllib.parse import parse_qs, urlparse
from datetime import datetime, date

import psycopg2

# =========================================================
# CONFIG
# =========================================================
DATABASE_URL = "postgresql://neondb_owner:npg_V1CwlGHBK4Og@ep-crimson-recipe-ai9g12ym-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

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

def validar_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", (email or "").strip()))

def validar_celular(cel):
    return bool(re.fullmatch(r"^\d{10,15}$", (cel or "").strip()))

def validar_usuario(usuario):
    return bool(re.fullmatch(r"^[A-Za-z0-9_.-]{3,30}$", (usuario or "").strip()))

def validar_texto_simple(texto, max_len=120):
    texto = limpiar_espacios(texto)
    return bool(texto) and len(texto) <= max_len

def hash_password(password):
    password = password or ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def b64url_decode(data):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))

def jwt_encode(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def jwt_decode(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_signature = hmac.new(
            JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
        ).digest()

        if not hmac.compare_digest(expected_signature, b64url_decode(signature_b64)):
            return None

        payload = json.loads(b64url_decode(payload_b64).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except:
        return None

def parse_cookies(environ):
    cookie_header = environ.get("HTTP_COOKIE", "")
    cookies = {}
    for item in cookie_header.split(";"):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            cookies[k] = v
    return cookies

def make_cookie(name, value, max_age=None, path="/", http_only=True):
    cookie = f"{name}={value}; Path={path}; SameSite=Lax"
    if max_age is not None:
        cookie += f"; Max-Age={max_age}"
    if http_only:
        cookie += "; HttpOnly"
    return ("Set-Cookie", cookie)

def redirect(start_response, location, extra_headers=None):
    headers = [("Location", location)]
    if extra_headers:
        headers.extend(extra_headers)
    start_response("303 See Other", headers)
    return [b""]

def json_response(start_response, data, status="200 OK"):
    body = json.dumps(data).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8")])
    return [body]

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

def verificar_recaptcha(token):
    try:
        data = urllib.parse.urlencode({
            "secret": RECAPTCHA_SECRET_KEY,
            "response": token or ""
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return bool(result.get("success"))
    except:
        return False

def conectar_bd():
    result = urlparse(DATABASE_URL)
    return psycopg2.connect(
        host=result.hostname,
        database=result.path[1:],
        user=result.username,
        password=result.password,
        port=result.port,
        connect_timeout=8,
        sslmode="require"
    )


# =========================================================
# BD
# =========================================================
def init_db():
    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS perfiles (
        id SERIAL PRIMARY KEY,
        strNombrePerfil VARCHAR(120) NOT NULL UNIQUE,
        bitAdministrador BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS modulos (
        id SERIAL PRIMARY KEY,
        strNombreModulo VARCHAR(120) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        strNombreUsuario VARCHAR(50) NOT NULL UNIQUE,
        idPerfil INTEGER NOT NULL REFERENCES perfiles(id),
        strPwd VARCHAR(255) NOT NULL,
        idEstadoUsuario INTEGER NOT NULL DEFAULT 1, -- 1 activo, 0 inactivo
        strCorreo VARCHAR(150) NOT NULL,
        strNumeroCelular VARCHAR(20) NOT NULL,
        strImagenBase64 TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS permisos_perfil (
        id SERIAL PRIMARY KEY,
        idModulo INTEGER NOT NULL REFERENCES modulos(id) ON DELETE CASCADE,
        idPerfil INTEGER NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
        bitAgregar BOOLEAN NOT NULL DEFAULT FALSE,
        bitEditar BOOLEAN NOT NULL DEFAULT FALSE,
        bitConsulta BOOLEAN NOT NULL DEFAULT FALSE,
        bitEliminar BOOLEAN NOT NULL DEFAULT FALSE,
        bitDetalle BOOLEAN NOT NULL DEFAULT FALSE,
        UNIQUE (idModulo, idPerfil)
    )
    """)

    # seed mínimo
    cur.execute("SELECT COUNT(*) FROM perfiles")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO perfiles (strNombrePerfil, bitAdministrador)
        VALUES
        ('ADMINISTRADOR', TRUE),
        ('RECEPCION', FALSE)
        """)

    cur.execute("SELECT COUNT(*) FROM modulos")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO modulos (strNombreModulo)
        VALUES
        ('CONFIGURACIÓN'),
        ('PERFIL'),
        ('PERMISOS PERFIL'),
        ('USUARIO')
        """)

    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id FROM perfiles WHERE strNombrePerfil='ADMINISTRADOR'")
        perfil_admin = cur.fetchone()[0]

        cur.execute("""
        INSERT INTO usuarios (
            strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo, strNumeroCelular
        )
        VALUES (%s, %s, %s, 1, %s, %s)
        """, ("admin", perfil_admin, hash_password("admin123"), "admin@clinica.com", "7710000000"))

    # dar permisos completos al admin
    cur.execute("SELECT id FROM perfiles WHERE strNombrePerfil='ADMINISTRADOR'")
    perfil_admin = cur.fetchone()[0]
    cur.execute("SELECT id FROM modulos")
    mods = cur.fetchall()

    for (mid,) in mods:
        cur.execute("""
        INSERT INTO permisos_perfil (
            idModulo, idPerfil, bitAgregar, bitEditar, bitConsulta, bitEliminar, bitDetalle
        )
        VALUES (%s, %s, TRUE, TRUE, TRUE, TRUE, TRUE)
        ON CONFLICT (idModulo, idPerfil) DO NOTHING
        """, (mid, perfil_admin))

    conn.commit()
    cur.close()
    conn.close()


# =========================================================
# AUTENTICACIÓN Y PERMISOS
# =========================================================
def usuario_actual(environ):
    cookies = parse_cookies(environ)
    token = cookies.get("token", "")
    payload = jwt_decode(token)
    if not payload:
        return None
    return payload

def login_requerido(environ, start_response):
    user = usuario_actual(environ)
    if not user:
        redirect(start_response, "/login")
        return None
    return user

def obtener_permisos_usuario(user_id, perfil_id):
    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute("SELECT bitAdministrador FROM perfiles WHERE id=%s", (perfil_id,))
    row = cur.fetchone()
    is_admin = bool(row and row[0])

    permisos = {}
    if is_admin:
        cur.execute("SELECT id, strNombreModulo FROM modulos ORDER BY id")
        for mid, nombre in cur.fetchall():
            permisos[nombre] = {
                "idModulo": mid,
                "agregar": True,
                "editar": True,
                "consultar": True,
                "eliminar": True,
                "detalle": True
            }
    else:
        cur.execute("""
        SELECT m.id, m.strNombreModulo,
               p.bitAgregar, p.bitEditar, p.bitConsulta, p.bitEliminar, p.bitDetalle
        FROM permisos_perfil p
        INNER JOIN modulos m ON m.id = p.idModulo
        WHERE p.idPerfil = %s
        ORDER BY m.id
        """, (perfil_id,))
        for row in cur.fetchall():
            permisos[row[1]] = {
                "idModulo": row[0],
                "agregar": bool(row[2]),
                "editar": bool(row[3]),
                "consultar": bool(row[4]),
                "eliminar": bool(row[5]),
                "detalle": bool(row[6]),
            }

    cur.close()
    conn.close()
    return permisos

def tiene_permiso(environ, modulo_nombre, accion="consultar"):
    user = usuario_actual(environ)
    if not user:
        return False
    permisos = obtener_permisos_usuario(user["uid"], user["perfil_id"])
    mod = permisos.get(modulo_nombre)
    if not mod:
        return False
    return bool(mod.get(accion, False))

def proteger_modulo(environ, start_response, modulo_nombre, accion="consultar"):
    user = login_requerido(environ, start_response)
    if not user:
        return None
    if not tiene_permiso(environ, modulo_nombre, accion):
        redirect(start_response, "/login")
        return None
    return user


# =========================================================
# UI
# =========================================================
def render_layout(title, content, user=None, breadcrumbs=None):
    breadcrumbs = breadcrumbs or []
    crumbs = '<a href="/dashboard">Inicio</a>'
    for item in breadcrumbs:
        crumbs += f' <span style="color:#7c8aa5;">/</span> <span>{html_escape(item)}</span>'

    menu_html = ""
    if user:
        permisos = obtener_permisos_usuario(user["uid"], user["perfil_id"])
        seguridad_sub = []
        for nombre, ruta in [
            ("Perfil", "/seguridad/perfil"),
            ("Permisos Perfil", "/seguridad/permisos-perfil"),
            ("Usuario", "/seguridad/usuario"),
        ]:
            if permisos.get(nombre.upper()) or permisos.get(nombre) or user.get("is_admin"):
                seguridad_sub.append(f'<a href="{ruta}">{nombre}</a>')

        if seguridad_sub:
            menu_html = f"""
            <div class="topbar">
              <div class="menu-wrap">
                <a class="menu-item" href="/dashboard">Inicio</a>
                <div class="dropdown">
                  <button class="menu-item dropbtn">Seguridad</button>
                  <div class="dropdown-content">
                    {''.join(seguridad_sub)}
                  </div>
                </div>
                <a class="menu-item" href="/principal1">Principal 1</a>
                <a class="menu-item" href="/principal2">Principal 2</a>
              </div>
              <div class="userbox">
                <span>{html_escape(user["usuario"])}</span>
                <a href="/logout">Salir</a>
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
    .topbar{{
      background:#0f4573;color:#fff;display:flex;justify-content:space-between;align-items:center;
      padding:0 10px;border-top:6px solid #58a74a;
    }}
    .menu-wrap{{display:flex;align-items:center;gap:0;}}
    .menu-item,.dropbtn{{
      color:#fff;text-decoration:none;padding:16px 18px;display:inline-block;background:transparent;border:none;
      font-size:16px;cursor:pointer;
    }}
    .menu-item:hover,.dropbtn:hover{{background:#164f80;}}
    .dropdown{{position:relative;display:inline-block;}}
    .dropdown-content{{
      display:none;position:absolute;background:#0f4573;min-width:230px;z-index:99;
      box-shadow:0 4px 12px rgba(0,0,0,.15);
    }}
    .dropdown-content a{{color:#fff;padding:12px 18px;text-decoration:none;display:block;}}
    .dropdown-content a:hover{{background:#164f80;}}
    .dropdown:hover .dropdown-content{{display:block;}}
    .userbox{{display:flex;align-items:center;gap:12px;padding-right:10px;}}
    .userbox a{{color:#fff;text-decoration:none;font-weight:bold;}}
    .title-row{{display:flex;align-items:center;gap:12px;margin-bottom:8px;}}
    .title-icon{{font-size:42px;line-height:1;}}
    .title-text{{font-size:28px;font-weight:normal;}}
    .green-line{{height:5px;background:#58a74a;margin:10px 0 26px;}}
    .breadcrumbs{{font-size:14px;color:#516277;margin-bottom:16px;}}
    .breadcrumbs a{{text-decoration:none;color:#0f4573;}}
    .panel{{background:transparent;padding:0;}}
    .section-label{{font-weight:bold;font-size:18px;margin:18px 0 12px;}}
    .form-row{{display:flex;align-items:center;gap:14px;margin:10px 0;flex-wrap:wrap;}}
    .form-row label{{width:110px;font-size:18px;}}
    .input,.select{{
      height:38px;border:2px solid #434343;border-radius:7px;padding:6px 10px;background:#fff;min-width:240px;
      font-size:16px;
    }}
    .input-lg{{width:460px;max-width:100%;}}
    .select{{appearance:none;background-image:linear-gradient(45deg,transparent 50%, #333 50%), linear-gradient(135deg, #333 50%, transparent 50%);
             background-position:calc(100% - 18px) 14px, calc(100% - 8px) 14px;background-size:10px 10px,10px 10px;background-repeat:no-repeat;padding-right:36px;}}
    .btn{{
      border:none;border-radius:8px;padding:11px 24px;font-size:18px;cursor:pointer;color:#fff;
      background:#58a74a;text-decoration:none;display:inline-block;
    }}
    .btn:hover{{filter:brightness(.96);}}
    .btn.secondary{{background:#737373;}}
    .btn.blue{{background:#184a78;}}
    .btn.small{{padding:8px 16px;font-size:16px;}}
    .search-box{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;}}
    table{{width:100%;border-collapse:collapse;background:#fff;}}
    th,td{{border:1px solid #a8a8a8;padding:12px 10px;text-align:center;}}
    th{{background:#0f4573;color:#fff;font-size:16px;}}
    td.left{{text-align:left;}}
    .table-wrap{{overflow:auto;}}
    .actions{{display:flex;gap:10px;justify-content:flex-end;margin-top:20px;flex-wrap:wrap;}}
    .msg-ok{{background:#d9f2d4;border:1px solid #7dbb6d;color:#24551e;padding:12px 14px;border-radius:8px;margin-bottom:15px;}}
    .msg-bad{{background:#fde2e2;border:1px solid #d88b8b;color:#7f1d1d;padding:12px 14px;border-radius:8px;margin-bottom:15px;}}
    .pager{{display:flex;justify-content:center;gap:8px;align-items:center;margin-top:16px;flex-wrap:wrap;}}
    .pager a,.pager span{{padding:8px 12px;border-radius:20px;border:1px solid #bbb;background:#fff;text-decoration:none;color:#184a78;}}
    .pager .active{{background:#184a78;color:#fff;}}
    .login-wrap{{min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px;}}
    .login-card{{width:860px;max-width:100%;background:#efefef;padding:24px 30px 40px;}}
    .login-head{{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;}}
    .logo-box{{display:flex;align-items:center;gap:12px;}}
    .logo-mark{{font-size:46px;}}
    .brand-title{{font-size:16px;color:#58a74a;font-weight:bold;}}
    .brand-name{{font-size:22px;color:#184a78;font-weight:bold;}}
    .welcome{{font-size:64px;font-weight:bold;color:#090979;line-height:1;}}
    .login-form{{max-width:700px;margin:36px auto 0;}}
    .login-grid{{display:grid;grid-template-columns:180px 1fr;gap:18px 18px;align-items:center;}}
    .login-grid label{{font-size:28px;}}
    .login-grid .input{{height:38px;width:100%;font-size:18px;}}
    .login-actions{{display:flex;justify-content:flex-end;margin-top:20px;}}
    .muted{{color:#4d5a68;}}
    .checkbox-cell input{{width:20px;height:20px;}}
    .img-preview{{width:60px;height:60px;border-radius:50%;object-fit:cover;border:2px solid #ddd;background:#fff;}}
    .plus-btn{{font-size:26px;width:42px;height:38px;padding:0;display:inline-flex;align-items:center;justify-content:center;}}
    @media(max-width:768px){{
      .login-grid{{grid-template-columns:1fr;}}
      .login-grid label{{font-size:22px;}}
      .welcome{{font-size:42px;}}
      .form-row label{{width:100%;}}
      .input-lg{{width:100%;}}
      .topbar{{flex-direction:column;align-items:stretch;}}
      .menu-wrap{{flex-wrap:wrap;}}
    }}
  </style>
</head>
<body>
  {menu_html}
  <div class="page">
    {'' if not user else f'<div class="breadcrumbs">{crumbs}</div>'}
    {content}
  </div>
</body>
</html>
"""

def page_error(msg):
    return render_layout(
        "Error",
        f"""
        <div class="title-row">
          <div class="title-icon">⚠️</div>
          <div class="title-text">Error</div>
        </div>
        <div class="green-line"></div>
        <div class="msg-bad">{html_escape(msg)}</div>
        <a class="btn blue" href="/login">Volver</a>
        """
    )

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

            <form id="loginForm" class="login-form">
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

def dashboard_html(user):
    return render_layout(
        "Dashboard",
        f"""
        <div class="title-row">
          <div class="title-icon">🏥</div>
          <div class="title-text">Sistema Corporativo - Clínica Santa Mónica</div>
        </div>
        <div class="green-line"></div>

        <div class="msg-ok">
          Bienvenido, <b>{html_escape(user["usuario"])}</b>.
        </div>

        <div class="panel">
          <p class="muted">Desde el menú superior puedes entrar a Seguridad y a los demás módulos permitidos por tu perfil.</p>
        </div>
        """,
        user=user,
        breadcrumbs=["Dashboard"]
    )

def paginacion_html(base_url, page_number, total_pages):
    if total_pages < 1:
        total_pages = 1

    links = []
    if page_number > 1:
        links.append(f'<a href="{base_url}?page=1">⏮</a>')
        links.append(f'<a href="{base_url}?page={page_number-1}">◀</a>')

    ini = max(1, page_number - 2)
    fin = min(total_pages, page_number + 2)
    for i in range(ini, fin + 1):
        if i == page_number:
            links.append(f'<span class="active">{i}</span>')
        else:
            links.append(f'<a href="{base_url}?page={i}">{i}</a>')

    if page_number < total_pages:
        links.append(f'<a href="{base_url}?page={page_number+1}">▶</a>')
        links.append(f'<a href="{base_url}?page={total_pages}">⏭</a>')

    return f'<div class="pager">{"".join(links)}</div>'


# =========================================================
# PANTALLA USUARIO
# =========================================================
def usuario_page(environ, user):
    qs = parse_qs(environ.get("QUERY_STRING", ""))
    page_number = max(1, int((qs.get("page", ["1"])[0] or "1")))
    q_usuario = limpiar_espacios(qs.get("usuario", [""])[0])
    q_perfil = (qs.get("perfil", [""])[0] or "").strip()
    q_estado = (qs.get("estado", [""])[0] or "").strip()

    offset = (page_number - 1) * PAGE_SIZE

    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute("SELECT id, strNombrePerfil FROM perfiles ORDER BY strNombrePerfil")
    perfiles = cur.fetchall()

    where = []
    params = []

    if q_usuario:
        where.append("LOWER(u.strNombreUsuario) LIKE %s")
        params.append("%" + q_usuario.lower() + "%")
    if q_perfil.isdigit():
        where.append("u.idPerfil = %s")
        params.append(int(q_perfil))
    if q_estado in ("0", "1"):
        where.append("u.idEstadoUsuario = %s")
        params.append(int(q_estado))

    sql_where = " WHERE " + " AND ".join(where) if where else ""

    cur.execute(f"""
    SELECT COUNT(*)
    FROM usuarios u
    INNER JOIN perfiles p ON p.id = u.idPerfil
    {sql_where}
    """, tuple(params))
    total = cur.fetchone()[0]
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    cur.execute(f"""
    SELECT u.id, u.strNombreUsuario, p.strNombrePerfil, 
           CASE WHEN u.idEstadoUsuario=1 THEN 'ACTIVO' ELSE 'INACTIVO' END,
           CASE WHEN u.idEstadoUsuario=1 THEN 'VIGENTE' ELSE 'BAJA' END,
           COALESCE(u.strImagenBase64, '')
    FROM usuarios u
    INNER JOIN perfiles p ON p.id = u.idPerfil
    {sql_where}
    ORDER BY u.id DESC
    LIMIT %s OFFSET %s
    """, tuple(params + [PAGE_SIZE, offset]))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    perfil_opts = ['<option value="">Seleccione</option>']
    for pid, nombre in perfiles:
        sel = "selected" if str(pid) == q_perfil else ""
        perfil_opts.append(f'<option {sel} value="{pid}">{html_escape(nombre)}</option>')

    tbody = ""
    for uid, usuario, perfil, estado, estado_registro, imagen in rows:
        avatar = "data:image/png;base64," + imagen if imagen else ""
        img_html = f'<img src="{avatar}" class="img-preview">' if avatar else ""
        tbody += f"""
        <tr>
          <td class="left">{img_html} {html_escape(usuario)}</td>
          <td>{html_escape(perfil)}</td>
          <td>INTERNO</td>
          <td>{html_escape(estado)}</td>
          <td>{html_escape(estado_registro)}</td>
          <td><a class="btn small blue" href="/seguridad/usuario/editar?id={uid}">✎</a></td>
          <td>
            <form method="POST" action="/seguridad/usuario/eliminar" onsubmit="return confirm('¿Eliminar usuario?');">
              <input type="hidden" name="id" value="{uid}">
              <button class="btn small secondary" type="submit">🗑</button>
            </form>
          </td>
        </tr>
        """

    if not tbody:
        tbody = "<tr><td colspan='7'>No hay resultados.</td></tr>"

    base_url = f"/seguridad/usuario"
    pagination = paginacion_html(base_url, page_number, total_pages)

    return render_layout(
        "Usuario",
        f"""
        <div class="title-row">
          <div class="title-icon">👤</div>
          <div class="title-text">Usuario</div>
        </div>
        <div class="green-line"></div>

        <form method="GET" class="panel">
          <div class="form-row">
            <label>Usuario:</label>
            <input class="input" type="text" name="usuario" value="{html_escape(q_usuario)}">
            <button class="btn" type="submit">Buscar</button>
            <a class="btn" href="/seguridad/usuario">Limpiar</a>
          </div>

          <div class="form-row">
            <label>Perfil:</label>
            <select class="select" name="perfil">
              {''.join(perfil_opts)}
            </select>
          </div>

          <div class="form-row">
            <label>Estado:</label>
            <select class="select" name="estado">
              <option value="">Seleccione</option>
              <option value="1" {"selected" if q_estado=="1" else ""}>Activo</option>
              <option value="0" {"selected" if q_estado=="0" else ""}>Inactivo</option>
            </select>
          </div>
        </form>

        <div style="margin:20px 0 8px;">
          <a class="btn plus-btn" href="/seguridad/usuario/nuevo">＋</a>
        </div>

        <div class="section-label">[Resultados]</div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Perfil</th>
                <th>Tipo Usuario</th>
                <th>Estado</th>
                <th>Estado Registro</th>
                <th>Editar</th>
                <th>Eliminar</th>
              </tr>
            </thead>
            <tbody>
              {tbody}
            </tbody>
          </table>
        </div>

        {pagination}

        <div class="actions">
          <a class="btn blue" href="/dashboard">Menú</a>
        </div>
        """,
        user=user,
        breadcrumbs=["Seguridad", "Usuario"]
    )


# =========================================================
# PANTALLA NUEVO / EDITAR USUARIO
# =========================================================
def usuario_form_page(user, editar=False, data=None, msg="", bad=False):
    data = data or {}
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("SELECT id, strNombrePerfil FROM perfiles ORDER BY strNombrePerfil")
    perfiles = cur.fetchall()
    cur.close()
    conn.close()

    perfil_opts = ['<option value="">Seleccione</option>']
    selected_perfil = str(data.get("idPerfil", ""))
    for pid, nombre in perfiles:
        sel = "selected" if str(pid) == selected_perfil else ""
        perfil_opts.append(f'<option {sel} value="{pid}">{html_escape(nombre)}</option>')

    alert = ""
    if msg:
        alert = f'<div class="{"msg-bad" if bad else "msg-ok"}">{html_escape(msg)}</div>'

    action_url = "/seguridad/usuario/guardar" if not editar else "/seguridad/usuario/actualizar"

    return render_layout(
        "Usuario",
        f"""
        <div class="title-row">
          <div class="title-icon">👤</div>
          <div class="title-text">{'Editar Usuario' if editar else 'Nuevo Usuario'}</div>
        </div>
        <div class="green-line"></div>

        {alert}

        <form method="POST" action="{action_url}" enctype="multipart/form-data">
          <input type="hidden" name="id" value="{html_escape(str(data.get('id','')))}">

          <div class="form-row">
            <label>Usuario:</label>
            <input class="input input-lg" type="text" name="strNombreUsuario" maxlength="30" value="{html_escape(data.get('strNombreUsuario',''))}" required>
          </div>

          <div class="form-row">
            <label>Perfil:</label>
            <select class="select input-lg" name="idPerfil" required>
              {''.join(perfil_opts)}
            </select>
          </div>

          <div class="form-row">
            <label>Correo:</label>
            <input class="input input-lg" type="email" name="strCorreo" maxlength="150" value="{html_escape(data.get('strCorreo',''))}" required>
          </div>

          <div class="form-row">
            <label>Celular:</label>
            <input class="input input-lg" type="text" name="strNumeroCelular" maxlength="15" value="{html_escape(data.get('strNumeroCelular',''))}" required>
          </div>

          <div class="form-row">
            <label>Estado:</label>
            <select class="select input-lg" name="idEstadoUsuario" required>
              <option value="1" {"selected" if str(data.get("idEstadoUsuario","1"))=="1" else ""}>Activo</option>
              <option value="0" {"selected" if str(data.get("idEstadoUsuario","1"))=="0" else ""}>Inactivo</option>
            </select>
          </div>

          <div class="form-row">
            <label>Contraseña:</label>
            <input class="input input-lg" type="password" name="strPwd" maxlength="50" {"required" if not editar else ""}>
          </div>

          <div class="form-row">
            <label>Imagen:</label>
            <input class="input input-lg" type="file" name="imagen" accept="image/*">
          </div>

          <div class="actions">
            <button class="btn" type="submit">Guardar</button>
            <a class="btn secondary" href="/seguridad/usuario">Cancelar</a>
          </div>
        </form>
        """,
        user=user,
        breadcrumbs=["Seguridad", "Usuario", "Editar" if editar else "Nuevo"]
    )


# =========================================================
# PANTALLA PERMISOS PERFIL
# =========================================================
def permisos_perfil_page(user, perfil_id=None, msg=""):
    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute("SELECT id, strNombrePerfil FROM perfiles ORDER BY strNombrePerfil")
    perfiles = cur.fetchall()

    if not perfil_id and perfiles:
        perfil_id = perfiles[0][0]

    cur.execute("""
    SELECT m.id, m.strNombreModulo,
           COALESCE(p.bitAgregar, FALSE),
           COALESCE(p.bitEditar, FALSE),
           COALESCE(p.bitEliminar, FALSE),
           COALESCE(p.bitConsulta, FALSE),
           COALESCE(p.bitDetalle, FALSE)
    FROM modulos m
    LEFT JOIN permisos_perfil p
      ON p.idModulo = m.id AND p.idPerfil = %s
    ORDER BY m.id
    """, (perfil_id,))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    alert = f'<div class="msg-ok">{html_escape(msg)}</div>' if msg else ""

    perfil_opts = []
    for pid, nombre in perfiles:
        sel = "selected" if int(pid) == int(perfil_id) else ""
        perfil_opts.append(f'<option {sel} value="{pid}">{html_escape(nombre)}</option>')

    tbody = ""
    for mid, nombre, agregar, editar, eliminar, consultar, detalle in rows:
        tbody += f"""
        <tr>
          <td class="left">{html_escape(nombre)}</td>
          <td class="checkbox-cell"><input type="checkbox" name="agregar_{mid}" {"checked" if agregar else ""}></td>
          <td class="checkbox-cell"><input type="checkbox" name="editar_{mid}" {"checked" if editar else ""}></td>
          <td class="checkbox-cell"><input type="checkbox" name="eliminar_{mid}" {"checked" if eliminar else ""}></td>
          <td class="checkbox-cell"><input type="checkbox" name="consultar_{mid}" {"checked" if consultar else ""}></td>
          <td class="checkbox-cell"><input type="checkbox" name="detalle_{mid}" {"checked" if detalle else ""}></td>
          <td class="checkbox-cell">☰</td>
        </tr>
        """

    return render_layout(
        "Permisos Perfil",
        f"""
        <div class="title-row">
          <div class="title-icon">🧑‍💼</div>
          <div class="title-text">Permisos Perfil</div>
        </div>
        <div class="green-line"></div>

        {alert}

        <div class="section-label">[Datos Perfil]</div>
        <form method="GET" action="/seguridad/permisos-perfil">
          <div class="form-row">
            <label>Perfil:</label>
            <select class="select" name="perfil_id" style="width:960px;max-width:100%;">
              {''.join(perfil_opts)}
            </select>
            <button class="btn" type="submit">Buscar</button>
          </div>
        </form>

        <div class="section-label">[Módulos web]</div>
        <form id="frmPermisos">
          <input type="hidden" name="perfil_id" value="{perfil_id}">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Módulo</th>
                  <th>Agregar</th>
                  <th>Editar</th>
                  <th>Eliminar</th>
                  <th>Consultar</th>
                  <th>Detalle</th>
                  <th>Extra</th>
                </tr>
              </thead>
              <tbody>
                {tbody}
              </tbody>
            </table>
          </div>

          <div class="actions">
            <button class="btn" type="submit">Guardar</button>
            <a class="btn secondary" href="/dashboard">Cancelar</a>
          </div>
        </form>

        <div id="permMsg"></div>

        <script>
        document.getElementById('frmPermisos').addEventListener('submit', async (e) => {{
          e.preventDefault();
          const fd = new FormData(e.target);

          const r = await fetch('/api/permisos-perfil/guardar', {{
            method: 'POST',
            body: fd
          }});

          const data = await r.json();
          const box = document.getElementById('permMsg');

          if (data.ok) {{
            box.innerHTML = '<div class="msg-ok">' + data.message + '</div>';
          }} else {{
            box.innerHTML = '<div class="msg-bad">' + data.message + '</div>';
          }}
        }});
        </script>
        """,
        user=user,
        breadcrumbs=["Seguridad", "Permisos Perfil"]
    )


# =========================================================
# PERFIL (BÁSICO)
# =========================================================
def perfil_page(environ, user):
    qs = parse_qs(environ.get("QUERY_STRING", ""))
    page_number = max(1, int((qs.get("page", ["1"])[0] or "1")))
    q = limpiar_espacios(qs.get("q", [""])[0])
    offset = (page_number - 1) * PAGE_SIZE

    conn = conectar_bd()
    cur = conn.cursor()

    where = ""
    params = []
    if q:
        where = "WHERE LOWER(strNombrePerfil) LIKE %s"
        params.append("%" + q.lower() + "%")

    cur.execute(f"SELECT COUNT(*) FROM perfiles {where}", tuple(params))
    total = cur.fetchone()[0]
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    cur.execute(f"""
    SELECT id, strNombrePerfil, bitAdministrador
    FROM perfiles
    {where}
    ORDER BY id DESC
    LIMIT %s OFFSET %s
    """, tuple(params + [PAGE_SIZE, offset]))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    tbody = ""
    for pid, nombre, admin in rows:
        tbody += f"""
        <tr>
          <td>{pid}</td>
          <td class="left">{html_escape(nombre)}</td>
          <td>{"Sí" if admin else "No"}</td>
          <td><a class="btn small blue" href="/seguridad/perfil/editar?id={pid}">Editar</a></td>
        </tr>
        """
    if not tbody:
        tbody = "<tr><td colspan='4'>No hay registros.</td></tr>"

    return render_layout(
        "Perfil",
        f"""
        <div class="title-row">
          <div class="title-icon">🪪</div>
          <div class="title-text">Perfil</div>
        </div>
        <div class="green-line"></div>

        <form method="GET">
          <div class="form-row">
            <label>Perfil:</label>
            <input class="input" type="text" name="q" value="{html_escape(q)}">
            <button class="btn" type="submit">Buscar</button>
            <a class="btn" href="/seguridad/perfil">Limpiar</a>
          </div>
        </form>

        <div style="margin:20px 0 8px;">
          <a class="btn plus-btn" href="/seguridad/perfil/nuevo">＋</a>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre Perfil</th>
                <th>Administrador</th>
                <th>Editar</th>
              </tr>
            </thead>
            <tbody>{tbody}</tbody>
          </table>
        </div>

        {paginacion_html('/seguridad/perfil', page_number, total_pages)}
        """,
        user=user,
        breadcrumbs=["Seguridad", "Perfil"]
    )


# =========================================================
# APP
# =========================================================
def application(environ, start_response):
    try:
        init_db()

        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")

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
            captcha_token = data.get("g-recaptcha-response", "")

            if not validar_usuario(usuario):
                return json_response(start_response, {"ok": False, "message": "Usuario inválido."})

            if not password:
                return json_response(start_response, {"ok": False, "message": "Contraseña requerida."})

            if not verificar_recaptcha(captcha_token):
                return json_response(start_response, {"ok": False, "message": "Captcha inválido."})

            conn = conectar_bd()
            cur = conn.cursor()
            cur.execute("""
            SELECT u.id, u.strNombreUsuario, u.strPwd, u.idEstadoUsuario, u.idPerfil, p.bitAdministrador
            FROM usuarios u
            INNER JOIN perfiles p ON p.id = u.idPerfil
            WHERE u.strNombreUsuario = %s
            """, (usuario,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                return json_response(start_response, {"ok": False, "message": "Usuario no existe."})

            uid, uname, pwd_hash, estado, perfil_id, is_admin = row

            if int(estado) != 1:
                return json_response(start_response, {"ok": False, "message": "Usuario inactivo."})

            if pwd_hash != hash_password(password):
                return json_response(start_response, {"ok": False, "message": "Contraseña incorrecta."})

            payload = {
                "uid": uid,
                "usuario": uname,
                "perfil_id": perfil_id,
                "is_admin": bool(is_admin),
                "exp": int(time.time()) + JWT_EXPIRE_SECONDS
            }
            token = jwt_encode(payload)

            start_response("200 OK", [
                ("Content-Type", "application/json; charset=utf-8"),
                make_cookie("token", token, max_age=JWT_EXPIRE_SECONDS)
            ])
            return [json.dumps({"ok": True}).encode("utf-8")]

        # ---------------- LOGOUT ----------------
        if path == "/logout":
            return redirect(start_response, "/login", [
                make_cookie("token", "", max_age=0)
            ])

        # ---------------- DASHBOARD ----------------
        if path == "/dashboard":
            user = login_requerido(environ, start_response)
            if not user:
                return [b""]
            html = dashboard_html(user)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]

        # ---------------- PERFIL ----------------
        if path == "/seguridad/perfil":
            user = proteger_modulo(environ, start_response, "PERFIL", "consultar")
            if not user:
                return [b""]
            html = perfil_page(environ, user)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]

        # ---------------- USUARIO LISTA ----------------
        if path == "/seguridad/usuario":
            user = proteger_modulo(environ, start_response, "USUARIO", "consultar")
            if not user:
                return [b""]
            html = usuario_page(environ, user)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]

        # ---------------- NUEVO USUARIO ----------------
        if path == "/seguridad/usuario/nuevo":
            user = proteger_modulo(environ, start_response, "USUARIO", "agregar")
            if not user:
                return [b""]
            html = usuario_form_page(user, editar=False)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]

        # ---------------- GUARDAR USUARIO ----------------
        if path == "/seguridad/usuario/guardar" and method == "POST":
            user = proteger_modulo(environ, start_response, "USUARIO", "agregar")
            if not user:
                return [b""]

            fs, data = get_form_data(environ)

            nombre = limpiar_espacios(data.get("strNombreUsuario", ""))
            idPerfil = (data.get("idPerfil", "") or "").strip()
            correo = limpiar_espacios(data.get("strCorreo", ""))
            celular = limpiar_espacios(data.get("strNumeroCelular", ""))
            estado = (data.get("idEstadoUsuario", "1") or "1").strip()
            pwd = data.get("strPwd", "")

            errores = []
            if not validar_usuario(nombre):
                errores.append("Usuario inválido. Usa solo letras, números, punto, guion o guion bajo.")
            if not idPerfil.isdigit():
                errores.append("Perfil inválido.")
            if not validar_email(correo):
                errores.append("Correo inválido.")
            if not validar_celular(celular):
                errores.append("Número celular inválido.")
            if estado not in ("0", "1"):
                errores.append("Estado inválido.")
            if len(pwd) < 6:
                errores.append("La contraseña debe tener al menos 6 caracteres.")

            imagen_b64 = ""
            imagen = data.get("imagen")
            if hasattr(imagen, "filename") and imagen.filename:
                content = imagen.file.read()
                if len(content) > 2 * 1024 * 1024:
                    errores.append("La imagen no debe superar 2MB.")
                else:
                    imagen_b64 = base64.b64encode(content).decode("utf-8")

            if errores:
                html = usuario_form_page(
                    user, editar=False,
                    data=data,
                    msg="; ".join(errores),
                    bad=True
                )
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [html.encode("utf-8")]

            conn = conectar_bd()
            cur = conn.cursor()
            try:
                cur.execute("""
                INSERT INTO usuarios (
                    strNombreUsuario, idPerfil, strPwd, idEstadoUsuario,
                    strCorreo, strNumeroCelular, strImagenBase64
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (
                    nombre, int(idPerfil), hash_password(pwd), int(estado),
                    correo, celular, imagen_b64
                ))
                conn.commit()
            except psycopg2.Error:
                conn.rollback()
                cur.close()
                conn.close()
                html = usuario_form_page(
                    user, editar=False, data=data,
                    msg="No se pudo guardar. El usuario puede estar repetido.",
                    bad=True
                )
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [html.encode("utf-8")]

            cur.close()
            conn.close()
            return redirect(start_response, "/seguridad/usuario")

        # ---------------- EDITAR USUARIO ----------------
        if path == "/seguridad/usuario/editar":
            user = proteger_modulo(environ, start_response, "USUARIO", "editar")
            if not user:
                return [b""]

            qs = parse_qs(environ.get("QUERY_STRING", ""))
            uid = (qs.get("id", [""])[0] or "").strip()
            if not uid.isdigit():
                html = page_error("ID de usuario inválido.")
                start_response("400 Bad Request", [("Content-Type", "text/html; charset=utf-8")])
                return [html.encode("utf-8")]

            conn = conectar_bd()
            cur = conn.cursor()
            cur.execute("""
            SELECT id, strNombreUsuario, idPerfil, strCorreo, strNumeroCelular, idEstadoUsuario
            FROM usuarios WHERE id=%s
            """, (int(uid),))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                html = page_error("Usuario no encontrado.")
                start_response("404 Not Found", [("Content-Type", "text/html; charset=utf-8")])
                return [html.encode("utf-8")]

            data = {
                "id": row[0],
                "strNombreUsuario": row[1],
                "idPerfil": row[2],
                "strCorreo": row[3],
                "strNumeroCelular": row[4],
                "idEstadoUsuario": row[5]
            }
            html = usuario_form_page(user, editar=True, data=data)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]

        # ---------------- ACTUALIZAR USUARIO ----------------
        if path == "/seguridad/usuario/actualizar" and method == "POST":
            user = proteger_modulo(environ, start_response, "USUARIO", "editar")
            if not user:
                return [b""]

            fs, data = get_form_data(environ)

            uid = (data.get("id", "") or "").strip()
            nombre = limpiar_espacios(data.get("strNombreUsuario", ""))
            idPerfil = (data.get("idPerfil", "") or "").strip()
            correo = limpiar_espacios(data.get("strCorreo", ""))
            celular = limpiar_espacios(data.get("strNumeroCelular", ""))
            estado = (data.get("idEstadoUsuario", "1") or "1").strip()
            pwd = data.get("strPwd", "")

            errores = []
            if not uid.isdigit():
                errores.append("ID inválido.")
            if not validar_usuario(nombre):
                errores.append("Usuario inválido.")
            if not idPerfil.isdigit():
                errores.append("Perfil inválido.")
            if not validar_email(correo):
                errores.append("Correo inválido.")
            if not validar_celular(celular):
                errores.append("Número celular inválido.")
            if estado not in ("0", "1"):
                errores.append("Estado inválido.")

            imagen_b64 = None
            imagen = data.get("imagen")
            if hasattr(imagen, "filename") and imagen.filename:
                content = imagen.file.read()
                if len(content) > 2 * 1024 * 1024:
                    errores.append("La imagen no debe superar 2MB.")
                else:
                    imagen_b64 = base64.b64encode(content).decode("utf-8")

            if errores:
                html = usuario_form_page(user, editar=True, data=data, msg="; ".join(errores), bad=True)
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [html.encode("utf-8")]

            conn = conectar_bd()
            cur = conn.cursor()
            try:
                if pwd and imagen_b64 is not None:
                    cur.execute("""
                    UPDATE usuarios
                    SET strNombreUsuario=%s, idPerfil=%s, strPwd=%s, idEstadoUsuario=%s,
                        strCorreo=%s, strNumeroCelular=%s, strImagenBase64=%s
                    WHERE id=%s
                    """, (nombre, int(idPerfil), hash_password(pwd), int(estado), correo, celular, imagen_b64, int(uid)))
                elif pwd:
                    cur.execute("""
                    UPDATE usuarios
                    SET strNombreUsuario=%s, idPerfil=%s, strPwd=%s, idEstadoUsuario=%s,
                        strCorreo=%s, strNumeroCelular=%s
                    WHERE id=%s
                    """, (nombre, int(idPerfil), hash_password(pwd), int(estado), correo, celular, int(uid)))
                elif imagen_b64 is not None:
                    cur.execute("""
                    UPDATE usuarios
                    SET strNombreUsuario=%s, idPerfil=%s, idEstadoUsuario=%s,
                        strCorreo=%s, strNumeroCelular=%s, strImagenBase64=%s
                    WHERE id=%s
                    """, (nombre, int(idPerfil), int(estado), correo, celular, imagen_b64, int(uid)))
                else:
                    cur.execute("""
                    UPDATE usuarios
                    SET strNombreUsuario=%s, idPerfil=%s, idEstadoUsuario=%s,
                        strCorreo=%s, strNumeroCelular=%s
                    WHERE id=%s
                    """, (nombre, int(idPerfil), int(estado), correo, celular, int(uid)))

                conn.commit()
            except psycopg2.Error:
                conn.rollback()
                cur.close()
                conn.close()
                html = usuario_form_page(user, editar=True, data=data, msg="No se pudo actualizar.", bad=True)
                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [html.encode("utf-8")]

            cur.close()
            conn.close()
            return redirect(start_response, "/seguridad/usuario")

        # ---------------- ELIMINAR USUARIO ----------------
        if path == "/seguridad/usuario/eliminar" and method == "POST":
            user = proteger_modulo(environ, start_response, "USUARIO", "eliminar")
            if not user:
                return [b""]
            fs, data = get_form_data(environ)
            uid = (data.get("id", "") or "").strip()
            if uid.isdigit():
                conn = conectar_bd()
                cur = conn.cursor()
                cur.execute("DELETE FROM usuarios WHERE id=%s", (int(uid),))
                conn.commit()
                cur.close()
                conn.close()
            return redirect(start_response, "/seguridad/usuario")

        # ---------------- PERMISOS PERFIL ----------------
        if path == "/seguridad/permisos-perfil":
            user = proteger_modulo(environ, start_response, "PERMISOS PERFIL", "consultar")
            if not user:
                return [b""]
            qs = parse_qs(environ.get("QUERY_STRING", ""))
            perfil_id = (qs.get("perfil_id", [""])[0] or "").strip()
            if not perfil_id.isdigit():
                perfil_id = None
            else:
                perfil_id = int(perfil_id)
            html = permisos_perfil_page(user, perfil_id=perfil_id)
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]

        # ---------------- API GUARDAR PERMISOS ----------------
        if path == "/api/permisos-perfil/guardar" and method == "POST":
            user = proteger_modulo(environ, start_response, "PERMISOS PERFIL", "editar")
            if not user:
                return [b""]

            fs, data = get_form_data(environ)
            perfil_id = (data.get("perfil_id", "") or "").strip()
            if not perfil_id.isdigit():
                return json_response(start_response, {"ok": False, "message": "Perfil inválido."})

            perfil_id = int(perfil_id)

            conn = conectar_bd()
            cur = conn.cursor()
            cur.execute("SELECT id FROM modulos ORDER BY id")
            modulos = [r[0] for r in cur.fetchall()]

            try:
                for mid in modulos:
                    agregar = f"agregar_{mid}" in data
                    editar = f"editar_{mid}" in data
                    eliminar = f"eliminar_{mid}" in data
                    consultar = f"consultar_{mid}" in data
                    detalle = f"detalle_{mid}" in data

                    cur.execute("""
                    INSERT INTO permisos_perfil (
                        idModulo, idPerfil, bitAgregar, bitEditar, bitConsulta, bitEliminar, bitDetalle
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (idModulo, idPerfil)
                    DO UPDATE SET
                        bitAgregar=EXCLUDED.bitAgregar,
                        bitEditar=EXCLUDED.bitEditar,
                        bitConsulta=EXCLUDED.bitConsulta,
                        bitEliminar=EXCLUDED.bitEliminar,
                        bitDetalle=EXCLUDED.bitDetalle
                    """, (mid, perfil_id, agregar, editar, consultar, eliminar, detalle))

                conn.commit()
            except:
                conn.rollback()
                cur.close()
                conn.close()
                return json_response(start_response, {"ok": False, "message": "No se pudieron guardar los permisos."})

            cur.close()
            conn.close()
            return json_response(start_response, {"ok": True, "message": "Permisos guardados correctamente."})

        # ---------------- PANTALLAS ESTÁTICAS ----------------
        if path == "/principal1":
            user = login_requerido(environ, start_response)
            if not user:
                return [b""]
            html = render_layout(
                "Principal 1",
                """
                <div class="title-row"><div class="title-icon">📁</div><div class="title-text">Principal 1</div></div>
                <div class="green-line"></div>
                <div class="actions">
                  <button class="btn">Agregar</button>
                  <button class="btn blue">Editar</button>
                  <button class="btn secondary">Eliminar</button>
                </div>
                """,
                user=user,
                breadcrumbs=["Principal 1"]
            )
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]

        if path == "/principal2":
            user = login_requerido(environ, start_response)
            if not user:
                return [b""]
            html = render_layout(
                "Principal 2",
                """
                <div class="title-row"><div class="title-icon">📁</div><div class="title-text">Principal 2</div></div>
                <div class="green-line"></div>
                <div class="actions">
                  <button class="btn">Agregar</button>
                  <button class="btn blue">Editar</button>
                  <button class="btn secondary">Eliminar</button>
                </div>
                """,
                user=user,
                breadcrumbs=["Principal 2"]
            )
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [html.encode("utf-8")]

        # ---------------- 404 ----------------
        html = page_error("La página solicitada no existe.")
        start_response("404 Not Found", [("Content-Type", "text/html; charset=utf-8")])
        return [html.encode("utf-8")]

    except Exception as e:
        html = page_error(f"Ocurrió un error interno: {str(e)}")
        start_response("500 Internal Server Error", [("Content-Type", "text/html; charset=utf-8")])
        return [html.encode("utf-8")]