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

    def validar_recaptcha(recaptcha_response):
        try:
            url = "https://www.google.com/recaptcha/api/siteverify"
            data = urllib.parse.urlencode({
                "secret": RECAPTCHA_SECRET_KEY,
                "response": recaptcha_response
            }).encode("utf-8")
            req = urllib.request.Request(url, data=data)
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode("utf-8"))
            return bool(result.get("success", False))
        except:
            return False

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

    <a href="/crud_personas" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#eef2ff;border:1px solid #e0e7ff;display:flex;align-items:center;justify-content:center;font-size:20px;">👤</div>
            <div>
              <div style="font-weight:900;font-size:18px;">CRUD Personas</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Alta, edición, borrado + filtros</div>
            </div>
          </div>
          <div style="color:#4f46e5;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/simular_404" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #fee2e2;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#fee2e2;border:1px solid #fecaca;display:flex;align-items:center;justify-content:center;font-size:20px;">⚠️</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Simular 404</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Prueba tu pantalla de error</div>
            </div>
          </div>
          <div style="color:#ef4444;font-weight:900;">→</div>
        </div>
      </div>
    </a>

  </div>
</div>

<style>
.homecard{transition:transform .12s ease, box-shadow .12s ease, border-color .12s ease;}
.homecard:hover{transform:translateY(-2px);box-shadow:0 18px 48px rgba(16,24,40,.10);border-color:#dbeafe;}
</style>
"""
        html = page("Inicio", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CALCULADORA
    # =========================================================
    if path == "/calculadora":
        resultado_suma = ""
        resultado_div = ""

        if method == "POST":
            try:
                content_length = int(environ.get("CONTENT_LENGTH", "0") or "0")
                post_data = environ["wsgi.input"].read(content_length).decode("utf-8") if content_length > 0 else ""
                params = parse_qs(post_data)

                try:
                    num1 = float(params.get("suma1", [""])[0])
                    num2 = float(params.get("suma2", [""])[0])
                    resultado_suma = "<div class='ok'>Resultado: %s + %s = %s</div>" % (num1, num2, (num1 + num2))
                except:
                    resultado_suma = "<div class='bad'>Ingresa SOLO números válidos para la suma</div>"

                try:
                    num3 = float(params.get("div1", [""])[0])
                    num4 = float(params.get("div2", [""])[0])
                    if num4 == 0:
                        resultado_div = "<div class='bad'>No se puede dividir entre cero</div>"
                    else:
                        resultado_div = "<div class='ok'>Resultado: %s ÷ %s = %.2f</div>" % (num3, num4, (num3 / num4))
                except:
                    resultado_div = "<div class='bad'>Ingresa SOLO números válidos para la división</div>"
            except Exception as e:
                resultado_suma = "<div class='bad'>Error: %s</div>" % str(e)

        body = """
<h1>Calculadora</h1>
<div class="grid2">
  <div class="card">
    <h3 style="margin-top:0;">Suma</h3>
    <form method="POST">
      <input type="number" step="any" name="suma1" placeholder="10" required>
      <input type="number" step="any" name="suma2" placeholder="5" required>
      <button class="btn-blue" style="width:100%;" type="submit">Calcular</button>
    </form>
    __SUMA__
  </div>

  <div class="card">
    <h3 style="margin-top:0;">División</h3>
    <form method="POST">
      <input type="number" step="any" name="div1" placeholder="10" required>
      <input type="number" step="any" name="div2" placeholder="2" required>
      <button class="btn-blue" style="width:100%;" type="submit">Calcular</button>
    </form>
    __DIV__
  </div>
</div>
""".replace("__SUMA__", resultado_suma).replace("__DIV__", resultado_div)

        html = page("Calculadora", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # FORMULARIO
    # =========================================================
    if path == "/formulario":
        mensaje = ""
        hoy = date.today()
        max_fecha = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")  # ayer

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

                if (fs.getvalue("borrar_todo") or "").strip() == "1":
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS formulario_simple (id SERIAL PRIMARY KEY, nombre VARCHAR(100), fecha_nacimiento DATE, correo VARCHAR(120), imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("DELETE FROM formulario_simple")
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/formulario')] + headers)
                    return [b""]

                nombre = (fs.getvalue("nombre") or "").strip()
                fecha_str = (fs.getvalue("fecha_nacimiento") or "").strip()
                correo = (fs.getvalue("correo") or "").strip()
                correo2 = (fs.getvalue("correo_confirmar") or "").strip()

                errores = []
                if not nombre:
                    errores.append("Nombre es requerido")
                elif not validar_nombre_solo_letras(nombre):
                    errores.append("Nombre solo debe tener letras y espacios")

                fecha_nac = None
                if not fecha_str:
                    errores.append("Fecha de nacimiento es requerida")
                else:
                    fecha_nac = parsear_fecha(fecha_str)
                    if not fecha_nac:
                        errores.append("Fecha de nacimiento inválida")
                    else:
                        if fecha_nac >= hoy:
                            errores.append("La fecha de nacimiento no puede ser la de hoy ni una futura")

                if not correo:
                    errores.append("Correo es requerido")
                elif correo != correo2:
                    errores.append("Los correos no coinciden")

                imagen_data = None
                imagen_nombre = ""
                imagen_tipo = ""

                if "imagen" not in fs:
                    errores.append("Debe subir una imagen")
                else:
                    imagen_file = fs["imagen"]
                    if not getattr(imagen_file, "filename", ""):
                        errores.append("Debe subir una imagen")
                    else:
                        imagen_nombre = imagen_file.filename
                        imagen_data = imagen_file.file.read()
                        imagen_tipo = imghdr.what(None, h=imagen_data) or "desconocido"
                        if len(imagen_data) > 5 * 1024 * 1024:
                            errores.append("La imagen es demasiado grande (máximo 5MB)")
                        if imagen_tipo not in ["jpeg", "jpg", "png", "gif"]:
                            errores.append("Solo JPG, PNG o GIF")

                if errores:
                    mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                else:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS formulario_simple (id SERIAL PRIMARY KEY, nombre VARCHAR(100), fecha_nacimiento DATE, correo VARCHAR(120), imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute(
                            "INSERT INTO formulario_simple (nombre, fecha_nacimiento, correo, imagen_nombre, imagen_tipo, imagen_data) VALUES (%s,%s,%s,%s,%s,%s)",
                            (nombre, fecha_nac, correo, imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                        )
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/formulario')] + headers)
                    return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        registros_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS formulario_simple (id SERIAL PRIMARY KEY, nombre VARCHAR(100), fecha_nacimiento DATE, correo VARCHAR(120), imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                cur.execute("SELECT nombre, fecha_nacimiento, correo, fecha FROM formulario_simple ORDER BY fecha DESC LIMIT 10")
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    items = ""
                    for (n, fn, c, f) in rows:
                        edad = calcular_edad(fn)
                        items += "<div style='background:#fff;padding:12px;border-radius:12px;margin:10px 0;border-left:4px solid #3b82f6;'><b>%s</b> — Edad: %s — %s<br><small style=\"color:#64748b;\">%s</small></div>" % (html_escape(n), edad, html_escape(c), str(f)[:16])
                    registros_html = """
<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
  <h3 style="margin:0;">Registros guardados</h3>
  <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros del formulario?');">
    <input type="hidden" name="borrar_todo" value="1">
    <button class="btn-danger btn-round" type="submit">Borrar registros</button>
  </form>
</div>
<div style="background:#f8fafc;padding:15px;border-radius:14px;margin-top:10px;border:1px solid #eef2f7;">
__ITEMS__
</div>
""".replace("__ITEMS__", items)
                else:
                    registros_html = "<p>No hay registros aún.</p>"
            except Exception as e:
                registros_html = "<div class='bad'>Error cargando registros: %s</div>" % str(e)
        else:
            registros_html = "<div class='bad'>No hay conexión a BD</div>"

        body = """
<h1>Formulario</h1>
__MENSAJE__

<div class="card">
<form method="POST" enctype="multipart/form-data">
  <label><b>Nombre</b></label>
  <input name="nombre" placeholder="Nombre" required oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">

  <label><b>Fecha de nacimiento</b></label>
  <input type="date" name="fecha_nacimiento" max="__MAX__" required>
  <small style="color:#64748b;">Debe ser anterior a hoy.</small>

  <label><b>Correo</b></label>
  <input type="email" name="correo" placeholder="Correo" required>

  <label><b>Confirmar correo</b></label>
  <input type="email" name="correo_confirmar" placeholder="Confirmar correo" required>

  <label><b>Imagen</b></label>
  <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>

  <button class="btn-primary" style="width:100%;margin-top:10px;" type="submit">Guardar</button>
</form>
</div>

<hr>
__REGS__
""".replace("__MENSAJE__", mensaje).replace("__REGS__", registros_html).replace("__MAX__", max_fecha)

        html = page("Formulario", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # REGISTRO reCAPTCHA
    # =========================================================
    if path == "/nombre_recaptcha":
        mensaje = ""

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

                if (fs.getvalue("borrar_todo") or "").strip() == "1":
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS nombres_recaptcha (id SERIAL PRIMARY KEY, nombre VARCHAR(30), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("DELETE FROM nombres_recaptcha")
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/nombre_recaptcha')] + headers)
                    return [b""]

                nombre_raw = (fs.getvalue("nombre") or "")
                nombre = limpiar_espacios(nombre_raw)
                rec = (fs.getvalue("g-recaptcha-response") or "").strip()

                errores = []
                if not nombre:
                    errores.append("Debes escribir un nombre para poder agregar.")
                else:
                    if not validar_nombre_solo_letras(nombre):
                        errores.append("Nombre solo debe tener letras y espacios")
                    if len(nombre) > 30:
                        errores.append("Solo se permiten 30 letras máximo (no se aceptan más de 30 caracteres).")

                if not rec:
                    errores.append("Completa el reCAPTCHA")
                elif not validar_recaptcha(rec):
                    errores.append("reCAPTCHA inválido")

                if errores:
                    mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                else:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS nombres_recaptcha (id SERIAL PRIMARY KEY, nombre VARCHAR(30), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("INSERT INTO nombres_recaptcha (nombre) VALUES (%s)", (nombre[:30],))
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/nombre_recaptcha')] + headers)
                    return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        lista = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS nombres_recaptcha (id SERIAL PRIMARY KEY, nombre VARCHAR(30), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                cur.execute("SELECT nombre, fecha FROM nombres_recaptcha ORDER BY fecha DESC LIMIT 15")
                rows = cur.fetchall()
                cur.close()
                conn.close()
                if rows:
                    lista = "<ul>" + "".join("<li><b>%s</b> <small style=\"color:#64748b;\">(%s)</small></li>" % (html_escape(n), str(f)[:16]) for (n, f) in rows) + "</ul>"
                else:
                    lista = "<p>No hay nombres aún.</p>"
            except Exception as e:
                lista = "<div class='bad'>Error cargando: %s</div>" % str(e)
        else:
            lista = "<div class='bad'>No hay conexión a BD</div>"

        body = """
<h1>Registro</h1>
<div class="info">Máximo 30 letras.</div>
__MENSAJE__

<script src="https://www.google.com/recaptcha/api.js" async defer></script>

<div class="card">
<form method="POST">
  <label><b>Nombre</b></label>
  <input name="nombre" placeholder="Nombre" required maxlength="30"
         oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">

  <div style="background:#f8fafc;padding:15px;border-radius:14px;margin:15px 0;text-align:center;border:1px solid #eef2f7;">
    <div class="g-recaptcha" data-sitekey="__SITEKEY__"></div>
  </div>

  <button class="btn-primary" style="width:100%;" type="submit">Guardar</button>
</form>
</div>

<hr>

<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
  <h3 style="margin:0;">Nombres ingresados (últimos 15)</h3>
  <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros de Registro?');">
    <input type="hidden" name="borrar_todo" value="1">
    <button class="btn-danger btn-round" type="submit">Borrar registros</button>
  </form>
</div>

<div style="background:#f8fafc;padding:15px;border-radius:14px;margin-top:10px;border:1px solid #eef2f7;">
__LISTA__
</div>
""".replace("__MENSAJE__", mensaje).replace("__LISTA__", lista).replace("__SITEKEY__", RECAPTCHA_SITE_KEY)

        html = page("Registro", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # SIMULAR 404
    # =========================================================
    if path == "/simular_404":
        body = """
<h1 style="color:#ef4444;font-size:54px;margin-bottom:10px;">404</h1>
<h2>Página no encontrada</h2>
<p>Esta ruta existe, pero responde como <b>404</b> para probar tu pantalla.</p>
<a href="/" style="display:inline-block;margin-top:20px;padding:12px 22px;background:#2563eb;color:white;text-decoration:none;border-radius:999px;font-weight:bold;">Volver al Inicio</a>
"""
        html = page("Simular 404", body)
        start_response("404 Not Found", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CARRUSEL
    # =========================================================
    if path == "/carrusel":
        mensaje = ""

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

                eliminar_id = (fs.getvalue("eliminar_id") or "").strip()
                if eliminar_id:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS carrusel_imagenes (id SERIAL PRIMARY KEY, imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("DELETE FROM carrusel_imagenes WHERE id=%s", (eliminar_id,))
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/carrusel')] + headers)
                    return [b""]

                if "imagen" not in fs:
                    mensaje = "<div class='bad'>Debes seleccionar una imagen</div>"
                else:
                    img_file = fs["imagen"]
                    if not getattr(img_file, "filename", ""):
                        mensaje = "<div class='bad'>Debes seleccionar una imagen</div>"
                    else:
                        img_nombre = img_file.filename
                        img_data = img_file.file.read()
                        img_tipo = imghdr.what(None, h=img_data) or "desconocido"

                        errores = []
                        if len(img_data) > 5 * 1024 * 1024:
                            errores.append("Máximo 5MB")
                        if img_tipo not in ["jpeg", "jpg", "png", "gif"]:
                            errores.append("Solo JPG, PNG o GIF")

                        if errores:
                            mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                        else:
                            conn = conectar_bd()
                            if conn:
                                cur = conn.cursor()
                                cur.execute("CREATE TABLE IF NOT EXISTS carrusel_imagenes (id SERIAL PRIMARY KEY, imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                                cur.execute(
                                    "INSERT INTO carrusel_imagenes (imagen_nombre, imagen_tipo, imagen_data) VALUES (%s,%s,%s)",
                                    (img_nombre, img_tipo, psycopg2.Binary(img_data))
                                )
                                conn.commit()
                                cur.close()
                                conn.close()

                            start_response("303 See Other", [('Location', '/carrusel')] + headers)
                            return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        slides = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS carrusel_imagenes (id SERIAL PRIMARY KEY, imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                cur.execute("SELECT id, imagen_tipo, imagen_data FROM carrusel_imagenes ORDER BY fecha DESC")
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    i = 0
                    for (img_id, img_tipo, img_data) in rows:
                        b64 = base64.b64encode(img_data).decode("utf-8")
                        active = "active" if i == 0 else ""
                        slides += """
<div class="slide __ACTIVE__">
  <img src="data:image/__TYPE__;base64,__B64__" style="max-width:100%;max-height:520px;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.18);">
  <form method="POST" onsubmit="return confirm('¿Eliminar esta imagen?');" style="margin-top:12px;">
    <input type="hidden" name="eliminar_id" value="__ID__">
    <button class="btn-danger btn-round" type="submit">Eliminar</button>
  </form>
</div>
""".replace("__ACTIVE__", active).replace("__TYPE__", img_tipo).replace("__B64__", b64).replace("__ID__", str(img_id))
                        i += 1
                else:
                    slides = "<p>No hay imágenes aún.</p>"
            except Exception as e:
                slides = "<div class='bad'>Error cargando carrusel: %s</div>" % str(e)

        body = """
<h1>Carrusel</h1>
__MENSAJE__

<div id="wrap" class="card">
__SLIDES__
</div>

<div style="display:flex;justify-content:space-between;align-items:center;margin-top:15px;">
  <button class="btn-blue" style="width:60px;border-radius:50%;height:50px;font-size:20px;" onclick="prev()">◀</button>
  <button class="btn-blue" style="width:60px;border-radius:50%;height:50px;font-size:20px;" onclick="next()">▶</button>
</div>

<hr>

<h3>Agregar imagen</h3>
<div class="card">
<form method="POST" enctype="multipart/form-data">
  <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
  <button class="btn-primary" style="width:100%;" type="submit">Agregar</button>
</form>
</div>

<style>
.slide{display:none;text-align:center;}
.slide.active{display:block;}
</style>

<script>
var idx = 0;
function show(i){
  var slides = document.querySelectorAll('.slide');
  if(!slides || slides.length===0) return;
  for(var k=0;k<slides.length;k++){ slides[k].classList.remove('active'); }
  idx = (i + slides.length) % slides.length;
  slides[idx].classList.add('active');
}
function next(){ show(idx+1); }
function prev(){ show(idx-1); }
document.addEventListener('DOMContentLoaded', function(){ show(0); });
</script>
""".replace("__MENSAJE__", mensaje).replace("__SLIDES__", slides)

        html = page("Carrusel", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CRUD PERSONAS (nuevo diseño + modal + filtro fechas)
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

                # editar
                if action == "edit":
                    pid = (fs.getvalue("id") or "").strip()
                    nombre = limpiar_espacios(fs.getvalue("nombre") or "")
                    email = (fs.getvalue("email") or "").strip()
                    fecha_str = (fs.getvalue("fecha_nacimiento") or "").strip()

                    errores = []
                    if not pid.isdigit():
                        errores.append("ID inválido")

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
                            cur.execute("UPDATE crud_personas SET nombre=%s, email=%s, fecha_nacimiento=%s WHERE id=%s", (nombre, email, fecha_nac, int(pid)))
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

                start_response("303 See Other", [('Location', '/crud_personas')] + headers)
                return [b""]

            except:
                start_response("303 See Other", [('Location', '/crud_personas')] + headers)
                return [b""]

        # GET: filtros
        qs = parse_qs(environ.get("QUERY_STRING", ""))
        q = (qs.get("q", [""])[0] or "").strip()
        fdesde = (qs.get("desde", [""])[0] or "").strip()
        fhasta = (qs.get("hasta", [""])[0] or "").strip()

        where = []
        params = []

        if q:
            where.append("(LOWER(nombre) LIKE %s OR LOWER(email) LIKE %s)")
            params.append("%" + q.lower() + "%")
            params.append("%" + q.lower() + "%")

        d1 = parsear_fecha(fdesde) if fdesde else None
        d2 = parsear_fecha(fhasta) if fhasta else None

        if d1 and d2:
            where.append("(fecha_nacimiento BETWEEN %s AND %s)")
            params.append(d1)
            params.append(d2)
        elif d1 and not d2:
            where.append("(fecha_nacimiento >= %s)")
            params.append(d1)
        elif d2 and not d1:
            where.append("(fecha_nacimiento <= %s)")
            params.append(d2)

        sql_where = (" WHERE " + " AND ".join(where)) if where else ""

        rows = []
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, nombre, email, fecha_nacimiento FROM crud_personas" + sql_where + " ORDER BY id DESC LIMIT 200", tuple(params))
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
        desdev = html_escape(fdesde)
        hastav = html_escape(fhasta)

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

      <button class="iconbtn" type="button" title="Filtrar por fecha" onclick="toggleFilter()">
        ▾
      </button>

      <button class="iconbtn" type="submit" title="Buscar / aplicar">
        ✓
      </button>
    </div>

    <div id="filtroFecha" style="display:none;margin-top:10px;" class="card">
      <div class="grid2">
        <div>
          <label><b>Desde</b></label>
          <input type="date" name="desde" value="__DESDE__" max="__MAX__">
        </div>
        <div>
          <label><b>Hasta</b></label>
          <input type="date" name="hasta" value="__HASTA__" max="__MAX__">
        </div>
      </div>
      <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:10px;flex-wrap:wrap;">
        <a href="/crud_personas" class="btn-round" style="text-decoration:none;background:#f1f5f9;color:#0f172a;padding:10px 14px;border-radius:999px;border:1px solid #e5e7eb;">Limpiar</a>
        <button class="btn-blue btn-round" type="submit">Aplicar</button>
      </div>
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

<!-- Modal Backdrop -->
<div class="modal-backdrop" id="modalBg" onclick="closeModal(event)">
  <div class="modal" onclick="event.stopPropagation()">
    <div class="modal-head">
      <div style="font-weight:900;font-size:20px;" id="modalTitle">Nuevo usuario</div>
      <button class="iconbtn" type="button" onclick="hideModal()">✕</button>
    </div>
    <form method="POST" id="modalForm">
      <input type="hidden" name="action" id="actionField" value="add">
      <input type="hidden" name="id" id="idField" value="">

      <div class="modal-body">
        <div class="grid2">
          <div>
            <label><b>Nombre</b></label>
            <input name="nombre" id="nombreField" placeholder="Ej: Juan Perez" required
              oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">
          </div>
          <div>
            <label><b>Email</b></label>
            <input type="email" name="email" id="emailField" placeholder="ejemplo@correo.com" required>
          </div>
        </div>

        <div style="margin-top:8px;">
          <label><b>Fecha de nacimiento</b></label>
          <input type="date" name="fecha_nacimiento" id="fechaField" required max="__MAX__">
          <small style="color:#64748b;">Debe ser anterior a hoy.</small>
        </div>
      </div>

      <div class="modal-foot">
        <button class="btn-muted btn-round" type="button" onclick="hideModal()">Cancelar</button>
        <button class="btn-blue btn-round" type="submit">Guardar</button>
      </div>
    </form>
  </div>
</div>

<script>
function toggleFilter(){
  var el = document.getElementById('filtroFecha');
  if(!el) return;
  el.style.display = (el.style.display === 'none' || el.style.display === '') ? 'block' : 'none';
}
function openAdd(){
  document.getElementById('modalTitle').innerText = 'Nuevo usuario';
  document.getElementById('actionField').value = 'add';
  document.getElementById('idField').value = '';
  document.getElementById('nombreField').value = '';
  document.getElementById('emailField').value = '';
  document.getElementById('fechaField').value = '';
  showModal();
}
function openEdit(id,n,e,f){
  document.getElementById('modalTitle').innerText = 'Editar usuario';
  document.getElementById('actionField').value = 'edit';
  document.getElementById('idField').value = id;
  document.getElementById('nombreField').value = n;
  document.getElementById('emailField').value = e;
  document.getElementById('fechaField').value = f;
  showModal();
}
function showModal(){
  document.getElementById('modalBg').style.display = 'flex';
}
function hideModal(){
  document.getElementById('modalBg').style.display = 'none';
}
function closeModal(ev){
  hideModal();
}
// abre el filtro si ya hay valores
(function(){
  var desde = "__DESDE__";
  var hasta = "__HASTA__";
  if((desde && desde.trim()) || (hasta && hasta.trim())){
    var el = document.getElementById('filtroFecha');
    if(el) el.style.display = 'block';
  }
})();
</script>
""".replace("__TBODY__", tbody)\
   .replace("__Q__", qesc)\
   .replace("__DESDE__", desdev)\
   .replace("__HASTA__", hastav)\
   .replace("__MAX__", max_fecha)

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
