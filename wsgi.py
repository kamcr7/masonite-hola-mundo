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
    @media(max-width:900px){
      .grid2{grid-template-columns:1fr;}
      th:nth-child(2), td:nth-child(2){display:none;} /* en móvil oculta email si quieres (pero lo dejo visible abajo) */
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
    # CRUD PERSONAS
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
                            cur.execute("INSERT INTO crud_personas (nombre,email,fecha_nacimiento) VALUES (%s,%s,%s)", (nombre, email, fecha_nac))
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

        # Paginación
        page_size = 4  # Número de usuarios por página
        page_number = int((parse_qs(environ.get("QUERY_STRING", "")).get("page", [1]))[0])  # Página actual
        offset = (page_number - 1) * page_size

        # GET: filtros
        qs = parse_qs(environ.get("QUERY_STRING", ""))
        q = (qs.get("q", [""])[0] or "").strip()

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
                cur.execute("SELECT id, nombre, email, fecha_nacimiento FROM crud_personas" + sql_where + " ORDER BY id DESC LIMIT %s OFFSET %s", tuple(params + [page_size, offset]))
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

        # UI filtros
        qesc = html_escape(q)

        # Paginación
        total_rows = 0
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM crud_personas" + sql_where, tuple(params))
                total_rows = cur.fetchone()[0]
                cur.close()
                conn.close()
            except:
                total_rows = 0

        total_pages = (total_rows + page_size - 1) // page_size  # Cálculo de total de páginas
        pagination_html = ""
        for i in range(1, total_pages + 1):
            pagination_html += f'<a href="/crud_personas?page={i}" style="padding:5px; margin:5px; text-decoration:none;">{i}</a>'

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

      <button class="iconbtn" type="submit" title="Buscar / aplicar">
        ✓
      </button>
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

<div style="margin-top:10px;">
  __PAGINACION__
</div>

<script>
function openAdd(){
  document.getElementById('modalTitle').innerText = 'Nuevo usuario';
  document.getElementById('actionField').value = 'add';
  document.getElementById('idField').value = '';
  document.getElementById('nombreField').value = '';
  document.getElementById('emailField').value = '';
  document.getElementById('fechaField').value = '';
  showModal();
}
</script>
""".replace("__TBODY__", tbody)\
   .replace("__Q__", qesc)\
   .replace("__PAGINACION__", pagination_html)

        html = page("CRUD Personas", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # 404 REAL
    # =========================================================
    body = """
<h1 style="color:#ef4444;font-size:54px;margin-bottom:10px;">404</h1>
<h2>Página no encontrada</h2>
<p>La ruta solicitada <code>%s</code> no existe.</p>
<a href="/" style="display:inline-block;margin-top:20px;padding:12px 22px;background:#2563eb;color:white;text-decoration:none;border-radius:999px;font-weight:bold;">Volver al Inicio</a>
""" % html_escape(path)

    html = page("404", body)
    start_response("404 Not Found", headers)
    return [html.encode("utf-8")]
