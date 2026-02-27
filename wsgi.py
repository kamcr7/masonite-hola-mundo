# -*- coding: utf-8 -*-
import psycopg2
import base64
import imghdr
import urllib.request
import urllib.parse
import json
import cgi
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date, timedelta

# ✅ Pega tu URL de Neon aquí (la que me diste)
DATABASE_URL = "postgresql://neondb_owner:npg_V1CwlGHBK4Og@ep-crimson-recipe-ai9g12ym-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    headers = [('Content-Type', 'text/html; charset=utf-8')]

    # -------------------- helpers --------------------
    def navegacion():
        return """
<nav style="background:#343a40;padding:15px;margin:20px auto 30px;border-radius:10px;max-width:1100px;">
  <a href="/" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Inicio</a>
  <a href="/calculadora" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Calculadora</a>
  <a href="/formulario" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Formulario</a>
  <a href="/carrusel" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Carrusel</a>
  <a href="/nombre_recaptcha" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Registro</a>
  <a href="/crud_personas" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">CRUD Personas</a>
  <a href="/simular_404" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Simular 404</a>
</nav>
"""

    def conectar_bd():
        try:
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
        except:
            return None

    def validar_nombre_solo_letras(nombre):
        patron = r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$"
        return bool(re.fullmatch(patron, (nombre or "").strip()))

    def limpiar_espacios(texto):
        return " ".join((texto or "").strip().split())

    def parsear_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    def calcular_edad(fecha_nac):
        if not fecha_nac:
            return None
        hoy = date.today()
        return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))

    def html_escape(s):
        s = (s or "")
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = s.replace('"', "&quot;").replace("'", "&#39;")
        return s

    def page(title, body_html):
        return """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>__TITLE__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body{font-family:Arial;margin:0;background:#f5f7fb;}
    .container{max-width:1100px;margin:0 auto 40px;background:white;padding:34px;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,.08);}
    h1{text-align:left;margin-top:0;}
    .ok{background:#d4edda;color:#155724;padding:12px;border-radius:10px;margin:15px 0;}
    .bad{background:#f8d7da;color:#721c24;padding:12px;border-radius:10px;margin:15px 0;}
    .info{background:#e7f3ff;color:#0b4f9c;padding:12px;border-radius:10px;margin:15px 0;border-left:4px solid #007bff;}
    input,textarea,select{width:100%;padding:12px;margin:8px 0;border:1px solid #e5e7eb;border-radius:12px;font-size:16px;box-sizing:border-box;background:#f8fafc;}
    input:focus,textarea:focus,select:focus{outline:none;border-color:#93c5fd;box-shadow:0 0 0 4px rgba(59,130,246,.15);background:#fff;}
    button{padding:12px 14px;border:none;border-radius:12px;font-weight:bold;cursor:pointer;}
    .btn-primary{background:#22c55e;color:white;}
    .btn-blue{background:#2563eb;color:white;}
    .btn-danger{background:#ef4444;color:white;}
    .btn-muted{background:#eef2ff;color:#4f46e5;}
    .btn-danger:hover{background:#dc2626;}
    hr{margin:30px 0;border:none;border-top:2px solid #f1f5f9;}
    .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
    .card{background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);}
    .table-wrap{background:#fff;border:1px solid #eef2f7;border-radius:16px;overflow:hidden;box-shadow:0 12px 35px rgba(16,24,40,.06);}
    table{width:100%;border-collapse:collapse;}
    th,td{padding:14px 14px;border-bottom:1px solid #eef2f7;text-align:left;}
    th{background:#f8fafc;color:#64748b;font-size:13px;letter-spacing:.02em;text-transform:uppercase;}
    tr:hover td{background:#fbfdff;}
    .actions{display:flex;gap:10px;flex-wrap:wrap;}
    .pill{display:inline-flex;gap:8px;align-items:center;padding:10px 12px;background:#fff;border:1px solid #e5e7eb;border-radius:999px;}
    .iconbtn{width:42px;height:42px;border-radius:999px;border:1px solid #e5e7eb;background:#fff;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;}
    .iconbtn:hover{background:#f8fafc;}
    .modal-backdrop{position:fixed;inset:0;background:rgba(15,23,42,.45);display:none;align-items:center;justify-content:center;padding:18px;z-index:1000;}
    .modal{width:min(720px, 96vw);background:#fff;border-radius:18px;box-shadow:0 30px 80px rgba(0,0,0,.25);overflow:hidden;}
    .modal-head{display:flex;align-items:center;justify-content:space-between;padding:18px 18px;border-bottom:1px solid #eef2f7;}
    .modal-body{padding:18px;}
    .modal-foot{display:flex;justify-content:flex-end;gap:10px;padding:18px;border-top:1px solid #eef2f7;}
    .btn-round{border-radius:999px;padding:10px 16px;}

    /* ✅ PAGINACIÓN con flechas (estilo similar a tu 2da imagen) */
    .pager-bar{
      margin-top:18px;
      display:flex;
      justify-content:center;
      align-items:center;
      gap:12px;
      padding:14px 12px;
      background:#f1f5f9;
      border:1px solid #e5e7eb;
      border-radius:16px;
      flex-wrap:wrap;
    }
    .pager-btn{
      width:48px;height:48px;
      border-radius:12px;
      border:1px solid #c7d2fe;
      background:#dbeafe;
      color:#1d4ed8;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      text-decoration:none;
      font-weight:900;
      user-select:none;
    }
    .pager-btn:hover{filter:brightness(.98);}
    .pager-btn.disabled{
      opacity:.45;
      pointer-events:none;
    }
    .pager-info{
      background:#fff;
      border:1px solid #e5e7eb;
      border-radius:999px;
      padding:12px 18px;
      font-weight:800;
      color:#334155;
      display:inline-flex;
      align-items:center;
      gap:10px;
      box-shadow:0 8px 18px rgba(16,24,40,.08);
    }
    .pager-pages{
      display:flex;
      gap:8px;
      align-items:center;
      flex-wrap:wrap;
      justify-content:center;
    }
    .pager-page{
      min-width:44px;
      height:44px;
      border-radius:999px;
      border:1px solid #e5e7eb;
      background:#fff;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      text-decoration:none;
      font-weight:800;
      color:#4f46e5;
      padding:0 14px;
    }
    .pager-page.active{
      background:#4f46e5;
      color:#fff;
      border-color:#4f46e5;
    }

    @media(max-width:900px){
      .grid2{grid-template-columns:1fr;}
      th:nth-child(2), td:nth-child(2){display:none;}
    }
    @media(max-width:700px){
      th,td{padding:12px 10px;}
      .container{padding:18px;}
      .actions{gap:8px;}
    }
  </style>
</head>
<body>
__NAV__
<div class="container">
__BODY__
</div>
</body>
</html>""".replace("__TITLE__", title).replace("__NAV__", navegacion()).replace("__BODY__", body_html)

    # =========================================================
    # INICIO (MEJOR DISEÑO)
    # =========================================================
    if path == "/" and method == "GET":
        body = """
<div style="
  background:linear-gradient(135deg, rgba(79,70,229,.10), rgba(37,99,235,.06));
  border:1px solid #e5e7eb;
  border-radius:18px;
  padding:22px;
  margin-top:6px;
">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
    <div>
      <h1 style="margin:0;font-size:34px;">Aplicación</h1>
      <p style="margin:6px 0 0;color:#6b7280;">Elige una sección para continuar.</p>
    </div>

    <div style="
      display:flex;gap:10px;align-items:center;flex-wrap:wrap;
      background:#ffffffcc;border:1px solid #e5e7eb;border-radius:999px;
      padding:10px 12px;
    ">
      <span style="font-size:18px;">🚀</span>
      <span style="font-weight:800;color:#374151;">Acceso rápido</span>
      <a href="/crud_personas" style="
        text-decoration:none;
        background:#4f46e5;color:#fff;
        padding:10px 14px;border-radius:999px;
        font-weight:800;
        display:inline-flex;gap:8px;align-items:center;
      ">Ir a CRUD Personas →</a>
    </div>
  </div>

  <div style="
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
    gap:16px;
    margin-top:18px;
  ">
    <a href="/calculadora" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#eef2ff;border:1px solid #e0e7ff;display:flex;align-items:center;justify-content:center;font-size:20px;">🧮</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Calculadora</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Suma y división con validación</div>
            </div>
          </div>
          <div style="color:#4f46e5;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/formulario" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#ecfeff;border:1px solid #cffafe;display:flex;align-items:center;justify-content:center;font-size:20px;">📝</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Formulario</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Imagen + fecha válida + correo</div>
            </div>
          </div>
          <div style="color:#2563eb;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/carrusel" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#fff7ed;border:1px solid #ffedd5;display:flex;align-items:center;justify-content:center;font-size:20px;">🖼️</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Carrusel</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Sube y administra imágenes</div>
            </div>
          </div>
          <div style="color:#f97316;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/nombre_recaptcha" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#f0fdf4;border:1px solid #dcfce7;display:flex;align-items:center;justify-content:center;font-size:20px;">✅</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Registro</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">reCAPTCHA + máximo 30 letras</div>
            </div>
          </div>
          <div style="color:#16a34a;font-weight:900;">→</div>
        </div>
      </div>
    </a>

  </div>
</div>
"""
        html = page("Inicio", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CRUD PERSONAS (con paginación)
    # =========================================================
    if path == "/crud_personas":
        hoy = date.today()
        max_fecha = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")

        # Crear tabla si no existe (NO borra registros)
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                CREATE TABLE IF NOT EXISTS crud_personas (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(120) NOT NULL,
                    email VARCHAR(160) NOT NULL,
                    fecha_nacimiento DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                conn.commit()
                cur.close()
                conn.close()
            except:
                pass

        # Paginación
        page_size = 4
        page_number = int((parse_qs(environ.get("QUERY_STRING", "")).get("page", [1]))[0])
        if page_number < 1:
            page_number = 1
        offset = (page_number - 1) * page_size

        # PRG acciones
        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)
                action = (fs.getvalue("action") or "").strip()

                # agregar
                if action == "add":
                    nombre = limpiar_espacios(fs.getvalue("nombre") or "")
                    email = (fs.getvalue("email") or "").strip()
                    fecha_str = (fs.getvalue("fecha_nacimiento") or "").strip()

                    errores = []
                    if not nombre:
                        errores.append("Nombre es requerido")
                    elif not validar_nombre_solo_letras(nombre):
                        errores.append("Nombre solo debe tener letras y espacios")

                    if not email:
                        errores.append("Email es requerido")
                    elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
                        errores.append("Email inválido")

                    fecha_nac = parsear_fecha(fecha_str)
                    if not fecha_nac:
                        errores.append("Fecha de nacimiento inválida")
                    else:
                        if fecha_nac >= hoy:
                            errores.append("La fecha debe ser anterior a hoy (no hoy ni futura)")

                    if not errores:
                        conn = conectar_bd()
                        if conn:
                            cur = conn.cursor()
                            cur.execute(
                                "INSERT INTO crud_personas (nombre,email,fecha_nacimiento) VALUES (%s,%s,%s)",
                                (nombre, email, fecha_nac)
                            )
                            conn.commit()
                            cur.close()
                            conn.close()

                    start_response("303 See Other", [('Location', '/crud_personas')] + headers)
                    return [b""]

                # eliminar
                if action == "delete":
                    pid = (fs.getvalue("id") or "").strip()
                    if pid.isdigit():
                        conn = conectar_bd()
                        if conn:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM crud_personas WHERE id=%s", (int(pid),))
                            conn.commit()
                            cur.close()
                            conn.close()

                    start_response("303 See Other", [('Location', '/crud_personas')] + headers)
                    return [b""]

            except:
                start_response("303 See Other", [('Location', '/crud_personas')] + headers)
                return [b""]

        # GET: obtener datos de la página y aplicar filtros
        qs = parse_qs(environ.get("QUERY_STRING", ""))
        q = (qs.get("q", [""])[0])
        where = []
        params = []

        if q:
            where.append("(LOWER(nombre) LIKE %s OR LOWER(email) LIKE %s)")
            params.append("%" + q.lower() + "%")
            params.append("%" + q.lower() + "%")

        sql_where = (" WHERE " + " AND ".join(where)) if where else ""

        rows = []
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    f"SELECT id, nombre, email, fecha_nacimiento FROM crud_personas {sql_where} "
                    f"ORDER BY id DESC LIMIT {page_size} OFFSET {offset}",
                    tuple(params)
                )
                rows = cur.fetchall()
                cur.close()
                conn.close()
            except:
                rows = []

        # tabla html
        tbody = ""
        for (pid, nombre, email, fn) in rows:
            tbody += """
<tr>
  <td><b>__N__</b></td>
  <td>__E__</td>
  <td>__F__</td>
  <td>
    <div class="actions">
      <button class="btn-muted btn-round" type="button"
        onclick="openEdit('__ID__','__NJS__','__EJS__','__F__')">Editar</button>
      <form method="POST" onsubmit="return confirm('¿Eliminar este registro?');" style="display:inline;">
        <input type="hidden" name="action" value="delete">
        <input type="hidden" name="id" value="__ID__">
        <button class="btn-danger btn-round" type="submit">Eliminar</button>
      </form>
    </div>
  </td>
</tr>
""".replace("__ID__", str(pid))\
   .replace("__N__", html_escape(nombre))\
   .replace("__E__", html_escape(email))\
   .replace("__F__", str(fn))\
   .replace("__NJS__", html_escape(nombre).replace("\\","\\\\").replace("'","\\'"))\
   .replace("__EJS__", html_escape(email).replace("\\","\\\\").replace("'","\\'"))

        if not tbody:
            tbody = "<tr><td colspan='4' style='color:#64748b;'>No hay registros.</td></tr>"

        # ✅ total_count con filtro (para que las páginas correspondan a la búsqueda)
        total_count = 0
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT COUNT(*) FROM crud_personas {sql_where}", tuple(params))
                total_count = cur.fetchone()[0]
                cur.close()
                conn.close()
            except:
                pass

        total_pages = (total_count + page_size - 1) // page_size
        if total_pages < 1:
            total_pages = 1
        if page_number > total_pages:
            page_number = total_pages

        # ✅ construir links conservando q
        q_param = ""
        if q:
            q_param = "&q=" + urllib.parse.quote(q)

        def page_link(p):
            return f"/crud_personas?page={p}{q_param}"

        # ✅ PAGINACIÓN con flechas + números (como tu 2da imagen)
        first_disabled = "disabled" if page_number <= 1 else ""
        prev_disabled  = "disabled" if page_number <= 1 else ""
        next_disabled  = "disabled" if page_number >= total_pages else ""
        last_disabled  = "disabled" if page_number >= total_pages else ""

        first_href = page_link(1) if page_number > 1 else "#"
        prev_href  = page_link(page_number - 1) if page_number > 1 else "#"
        next_href  = page_link(page_number + 1) if page_number < total_pages else "#"
        last_href  = page_link(total_pages) if page_number < total_pages else "#"

        # rango de páginas visible (para no llenar de 200 botones si hay muchos)
        start_p = max(1, page_number - 3)
        end_p = min(total_pages, page_number + 3)

        pages_html = ""
        for i in range(start_p, end_p + 1):
            active = "active" if i == page_number else ""
            pages_html += f'<a class="pager-page {active}" href="{page_link(i)}">{i}</a>'

        pagination = f"""
<div class="pager-bar">
  <a class="pager-btn {first_disabled}" href="{first_href}" title="Primera">⏮</a>
  <a class="pager-btn {prev_disabled}" href="{prev_href}" title="Anterior">◀</a>

  <div class="pager-info">Página {page_number} / {total_pages}</div>

  <div class="pager-pages">
    {pages_html}
  </div>

  <a class="pager-btn {next_disabled}" href="{next_href}" title="Siguiente">▶</a>
  <a class="pager-btn {last_disabled}" href="{last_href}" title="Última">⏭</a>
</div>
"""

        # UI filtros
        qesc = html_escape(q)

        body = """
<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
  <div>
    <h1 style="margin:0;">Usuarios</h1>
    <div style="color:#64748b;margin-top:6px;">CRUD Personas (Nombre, Email, Fecha de nacimiento)</div>
  </div>

  <button class="btn-blue btn-round" type="button" onclick="openAdd()">＋ Nuevo</button>
</div>

<div style="margin-top:18px;display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;">
  <form method="GET" style="flex:1;min-width:280px;">
    <div class="pill" style="width:100%;justify-content:space-between;">
      <div style="display:flex;gap:10px;align-items:center;flex:1;">
        <span style="font-size:18px;">🔎</span>
        <input name="q" value="__Q__" placeholder="Buscar por nombre o email..." style="border:none;background:transparent;margin:0;padding:0;box-shadow:none;outline:none;flex:1;">
      </div>
      <button class="iconbtn" type="submit" title="Buscar / aplicar">✓</button>
    </div>
  </form>
</div>

<div style="margin-top:18px;" class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>NOMBRE</th>
        <th>EMAIL</th>
        <th>FECHA DE NACIMIENTO</th>
        <th>ACCIONES</th>
      </tr>
    </thead>
    <tbody>
      __TBODY__
    </tbody>
  </table>
</div>

<div style="margin-top:18px;display:flex;justify-content:center;">
  __PAGINATION__
</div>
""".replace("__TBODY__", tbody)\
   .replace("__Q__", qesc)\
   .replace("__PAGINATION__", pagination)

        html = page("CRUD Personas", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # fallback simple
    html = page("404", "<h1>404</h1><p>No encontrado.</p>")
    start_response("404 Not Found", headers)
    return [html.encode("utf-8")]