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

DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"

RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    headers = [('Content-Type', 'text/html; charset=utf-8')]

    # -------------------- helpers --------------------
    def navegacion():
        return """
<nav style="background:#343a40;padding:15px;margin:20px auto 30px;border-radius:5px;max-width:1100px;">
  <a href="/" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Inicio</a>
  <a href="/calculadora" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Calculadora</a>
  <a href="/formulario" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Formulario</a>
  <a href="/carrusel" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Carrusel</a>
  <a href="/nombre_recaptcha" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Registro</a>
  <a href="/crud_productos" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">CRUD Productos</a>
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
                connect_timeout=5
            )
        except:
            return None

    def validar_nombre_solo_letras(nombre):
        patron = r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$"
        return bool(re.fullmatch(patron, (nombre or "").strip()))

    def limpiar_espacios(nombre):
        # quita espacios duplicados y recorta
        return " ".join((nombre or "").strip().split())

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

    def page(title, body_html):
        return """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>__TITLE__</title>
  <style>
    body{font-family:Arial;margin:0;background:#f8f9fa;}
    .container{max-width:1000px;margin:0 auto 40px;background:white;padding:40px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.1);}
    h1{text-align:center;margin-top:0;}
    .ok{background:#d4edda;color:#155724;padding:12px;border-radius:6px;margin:15px 0;}
    .bad{background:#f8d7da;color:#721c24;padding:12px;border-radius:6px;margin:15px 0;}
    .info{background:#e7f3ff;color:#0b4f9c;padding:12px;border-radius:6px;margin:15px 0;border-left:4px solid #007bff;}
    input,textarea{width:95%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;font-size:16px;}
    button{padding:12px;border:none;border-radius:6px;font-weight:bold;cursor:pointer;}
    .btn-primary{background:#28a745;color:white;width:100%;}
    .btn-blue{background:#007bff;color:white;width:100%;}
    .btn-danger{background:#dc3545;color:white;}
    .btn-danger:hover{background:#c82333;}
    hr{margin:30px 0;border:none;border-top:2px solid #eee;}
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
    # INICIO
    # =========================================================
    if path == "/" and method == "GET":
        body = """
<h1>Aplicación</h1>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:25px;">
  <div style="background:#e9ecef;padding:18px;border-radius:10px;text-align:center;">
    <h3>Calculadora</h3>
    <a href="/calculadora">Ir →</a>
  </div>
  <div style="background:#e9ecef;padding:18px;border-radius:10px;text-align:center;">
    <h3>Formulario</h3>
    <a href="/formulario">Ir →</a>
  </div>
  <div style="background:#e9ecef;padding:18px;border-radius:10px;text-align:center;">
    <h3>Carrusel</h3>
    <a href="/carrusel">Ir →</a>
  </div>
  <div style="background:#e9ecef;padding:18px;border-radius:10px;text-align:center;">
    <h3>Registro</h3>
    <a href="/nombre_recaptcha">Ir →</a>
  </div>
  <div style="background:#e9ecef;padding:18px;border-radius:10px;text-align:center;">
    <h3>CRUD Productos</h3>
    <a href="/crud_productos">Ir →</a>
  </div>
</div>
<div style="text-align:center;margin-top:25px;">
  <a href="/simular_404" style="display:inline-block;padding:12px 22px;background:#dc3545;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">Simular pantalla 404</a>
</div>
"""
        html = page("Inicio", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CALCULADORA (solo números)
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
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
  <div style="background:#f8f9fa;padding:20px;border-radius:10px;">
    <h3>Suma</h3>
    <form method="POST">
      <input type="number" step="any" name="suma1" placeholder="10" required>
      <input type="number" step="any" name="suma2" placeholder="5" required>
      <button class="btn-blue" type="submit">Calcular</button>
    </form>
    __SUMA__
  </div>

  <div style="background:#f8f9fa;padding:20px;border-radius:10px;">
    <h3>División</h3>
    <form method="POST">
      <input type="number" step="any" name="div1" placeholder="10" required>
      <input type="number" step="any" name="div2" placeholder="2" required>
      <button class="btn-blue" type="submit">Calcular</button>
    </form>
    __DIV__
  </div>
</div>

<style>
@media(max-width:768px){
  .container > div[style*="grid-template-columns:1fr 1fr"]{grid-template-columns:1fr !important;}
}
</style>
""".replace("__SUMA__", resultado_suma).replace("__DIV__", resultado_div)

        html = page("Calculadora", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # FORMULARIO + PRG (POST -> Redirect -> GET)
    #   - Fecha nacimiento: NO permite hoy ni futuras
    # =========================================================
    if path == "/formulario":
        mensaje = ""
        hoy = date.today()
        max_fecha = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")  # ayer

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

                # borrar todo
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
                        items += "<div style='background:#fff;padding:12px;border-radius:8px;margin:10px 0;border-left:4px solid #007bff;'><b>%s</b> — Edad: %s — %s<br><small>%s</small></div>" % (n, edad, c, str(f)[:16])
                    registros_html = """
<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
  <h3 style="margin:0;">Registros guardados</h3>
  <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros del formulario?');">
    <input type="hidden" name="borrar_todo" value="1">
    <button class="btn-danger" type="submit">Borrar registros</button>
  </form>
</div>
<div style="background:#f8f9fa;padding:15px;border-radius:10px;margin-top:10px;">
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

<form method="POST" enctype="multipart/form-data">
  <label><b>Nombre</b></label>
  <input name="nombre" placeholder="Nombre" required oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">

  <label><b>Fecha de nacimiento</b></label>
  <input type="date" name="fecha_nacimiento" max="__MAX__" required>
  <small>Debe ser anterior a hoy.</small>

  <label><b>Correo</b></label>
  <input type="email" name="correo" placeholder="Correo" required>

  <label><b>Confirmar correo</b></label>
  <input type="email" name="correo_confirmar" placeholder="Confirmar correo" required>

  <label><b>Imagen</b></label>
  <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>

  <button class="btn-primary" type="submit">Guardar</button>
</form>

<hr>
__REGS__
""".replace("__MENSAJE__", mensaje).replace("__REGS__", registros_html).replace("__MAX__", max_fecha)

        html = page("Formulario", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # REGISTRO + PRG + MAX 30 LETRAS
    # =========================================================
    if path == "/nombre_recaptcha":
        mensaje = ""

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

                # borrar todo -> PRG
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
                        # guardamos máximo 30 en DB también
                        cur.execute("CREATE TABLE IF NOT EXISTS nombres_recaptcha (id SERIAL PRIMARY KEY, nombre VARCHAR(30), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("INSERT INTO nombres_recaptcha (nombre) VALUES (%s)", (nombre[:30],))
                        conn.commit()
                        cur.close()
                        conn.close()

                    # PRG: evita duplicado por refresh
                    start_response("303 See Other", [('Location', '/nombre_recaptcha')] + headers)
                    return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        # lista
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
                    lista = "<ul>" + "".join("<li><b>%s</b> <small>(%s)</small></li>" % (n, str(f)[:16]) for (n, f) in rows) + "</ul>"
                else:
                    lista = "<p>No hay nombres aún.</p>"
            except Exception as e:
                lista = "<div class='bad'>Error cargando: %s</div>" % str(e)
        else:
            lista = "<div class='bad'>No hay conexión a BD</div>"

        body = """
<h1>Registro</h1>
<div class="info">Máximo 30 letras. Si escribes más, no se guardará.</div>
__MENSAJE__

<script src="https://www.google.com/recaptcha/api.js" async defer></script>

<form method="POST">
  <label><b>Nombre</b></label>
  <input name="nombre" placeholder="Nombre" required maxlength="30"
         oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">

  <div style="background:#f8f9fa;padding:15px;border-radius:10px;margin:15px 0;text-align:center;">
    <div class="g-recaptcha" data-sitekey="__SITEKEY__"></div>
  </div>

  <button class="btn-primary" type="submit">Guardar</button>
</form>

<hr>

<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
  <h3 style="margin:0;">Nombres ingresados (últimos 15)</h3>
  <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros de Registro?');">
    <input type="hidden" name="borrar_todo" value="1">
    <button class="btn-danger" type="submit">Borrar registros</button>
  </form>
</div>

<div style="background:#f8f9fa;padding:15px;border-radius:10px;margin-top:10px;">
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
<h1 style="color:#dc3545;font-size:54px;margin-bottom:10px;">404</h1>
<h2>Página no encontrada</h2>
<p>Esta ruta existe, pero responde como <b>404</b> para probar tu pantalla.</p>
<a href="/" style="display:inline-block;margin-top:20px;padding:12px 22px;background:#007bff;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">Volver al Inicio</a>
"""
        html = page("Simular 404", body)
        start_response("404 Not Found", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CARRUSEL + PRG
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
  <img src="data:image/__TYPE__;base64,__B64__" style="max-width:100%;max-height:520px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.2);">
  <form method="POST" onsubmit="return confirm('¿Eliminar esta imagen?');" style="margin-top:12px;">
    <input type="hidden" name="eliminar_id" value="__ID__">
    <button class="btn-danger" type="submit">Eliminar</button>
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

<div id="wrap">
__SLIDES__
</div>

<div style="display:flex;justify-content:space-between;align-items:center;margin-top:15px;">
  <button class="btn-blue" style="width:60px;border-radius:50%;height:50px;font-size:20px;" onclick="prev()">◀</button>
  <button class="btn-blue" style="width:60px;border-radius:50%;height:50px;font-size:20px;" onclick="next()">▶</button>
</div>

<hr>

<h3>Agregar imagen</h3>
<form method="POST" enctype="multipart/form-data">
  <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
  <button class="btn-primary" type="submit">Agregar</button>
</form>

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
    # CRUD PRODUCTOS (NUEVA PANTALLA) + PRG
    #   - Crear / Editar / Eliminar / Listar
    # =========================================================
    if path == "/crud_productos":
        mensaje = ""

        # Crear tabla si no existe
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS productos (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(80) NOT NULL,
                        precio NUMERIC(10,2) NOT NULL,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                cur.close()
                conn.close()
            except:
                try:
                    conn.close()
                except:
                    pass

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)
                accion = (fs.getvalue("accion") or "").strip()

                # ELIMINAR
                if accion == "eliminar":
                    pid = (fs.getvalue("id") or "").strip()
                    if pid.isdigit():
                        conn = conectar_bd()
                        if conn:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM productos WHERE id=%s", (pid,))
                            conn.commit()
                            cur.close()
                            conn.close()

                    start_response("303 See Other", [('Location', '/crud_productos')] + headers)
                    return [b""]

                # CREAR
                if accion == "crear":
                    nombre = (fs.getvalue("nombre") or "").strip()
                    precio_str = (fs.getvalue("precio") or "").strip()

                    errores = []
                    if not nombre:
                        errores.append("El nombre es requerido.")
                    if len(nombre) > 80:
                        errores.append("El nombre no puede pasar de 80 caracteres.")

                    try:
                        precio = float(precio_str)
                        if precio < 0:
                            errores.append("El precio no puede ser negativo.")
                    except:
                        errores.append("El precio debe ser un número válido.")

                    if errores:
                        mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                    else:
                        conn = conectar_bd()
                        if conn:
                            cur = conn.cursor()
                            cur.execute("INSERT INTO productos (nombre, precio) VALUES (%s, %s)", (nombre, precio))
                            conn.commit()
                            cur.close()
                            conn.close()

                        start_response("303 See Other", [('Location', '/crud_productos')] + headers)
                        return [b""]

                # EDITAR
                if accion == "editar":
                    pid = (fs.getvalue("id") or "").strip()
                    nombre = (fs.getvalue("nombre") or "").strip()
                    precio_str = (fs.getvalue("precio") or "").strip()

                    errores = []
                    if not pid.isdigit():
                        errores.append("ID inválido.")
                    if not nombre:
                        errores.append("El nombre es requerido.")
                    if len(nombre) > 80:
                        errores.append("El nombre no puede pasar de 80 caracteres.")

                    try:
                        precio = float(precio_str)
                        if precio < 0:
                            errores.append("El precio no puede ser negativo.")
                    except:
                        errores.append("El precio debe ser un número válido.")

                    if errores:
                        mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                    else:
                        conn = conectar_bd()
                        if conn:
                            cur = conn.cursor()
                            cur.execute("UPDATE productos SET nombre=%s, precio=%s WHERE id=%s", (nombre, precio, pid))
                            conn.commit()
                            cur.close()
                            conn.close()

                        start_response("303 See Other", [('Location', '/crud_productos')] + headers)
                        return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        # GET: listar productos
        productos_html = "<p>No hay productos aún.</p>"
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, nombre, precio, fecha FROM productos ORDER BY id DESC")
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    items = ""
                    for (pid, nombre, precio, fecha_reg) in rows:
                        items += """
<div style="background:#f8f9fa;padding:14px;border-radius:10px;margin:12px 0;border-left:4px solid #007bff;">
  <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;">
    <div>
      <b>#__ID__</b> — <b>__NOMBRE__</b><br>
      <small>Precio: <b>$__PRECIO__</b> — __FECHA__</small>
    </div>

    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <button class="btn-blue" style="width:auto;padding:10px 14px;" type="button"
        onclick="toggleEdit('__ID__')">Editar</button>

      <form method="POST" onsubmit="return confirm('¿Eliminar este producto?');">
        <input type="hidden" name="accion" value="eliminar">
        <input type="hidden" name="id" value="__ID__">
        <button class="btn-danger" type="submit">Eliminar</button>
      </form>
    </div>
  </div>

  <div id="edit___ID__" style="display:none;margin-top:12px;padding-top:12px;border-top:1px solid #ddd;">
    <form method="POST">
      <input type="hidden" name="accion" value="editar">
      <input type="hidden" name="id" value="__ID__">
      <input name="nombre" value="__NOMBRE__" maxlength="80" required>
      <input name="precio" value="__PRECIO__" required>
      <button class="btn-primary" type="submit">Guardar cambios</button>
    </form>
  </div>
</div>
""".replace("__ID__", str(pid)).replace("__NOMBRE__", str(nombre)).replace("__PRECIO__", str(precio)).replace("__FECHA__", str(fecha_reg)[:16])
                    productos_html = items
            except Exception as e:
                productos_html = "<div class='bad'>Error cargando productos: %s</div>" % str(e)
        else:
            productos_html = "<div class='bad'>No hay conexión a BD</div>"

        body = """
<h1>CRUD Productos</h1>
__MENSAJE__

<div style="background:#f8f9fa;padding:18px;border-radius:10px;">
  <h3>Agregar producto</h3>
  <form method="POST">
    <input type="hidden" name="accion" value="crear">

    <label><b>Nombre</b></label>
    <input name="nombre" placeholder="Ej: Laptop" maxlength="80" required>

    <label><b>Precio</b></label>
    <input name="precio" placeholder="Ej: 199.99" required>

    <button class="btn-primary" type="submit">Guardar</button>
  </form>
</div>

<hr>

<h3>Listado</h3>
__LISTA__

<script>
function toggleEdit(id) {
  var el = document.getElementById('edit_' + id);
  if(!el) return;
  el.style.display = (el.style.display === 'none' || el.style.display === '') ? 'block' : 'none';
}
</script>
""".replace("__MENSAJE__", mensaje).replace("__LISTA__", productos_html)

        html = page("CRUD Productos", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # 404 REAL
    # =========================================================
    body = """
<h1 style="color:#dc3545;font-size:54px;margin-bottom:10px;">404</h1>
<h2>Página no encontrada</h2>
<p>La ruta solicitada <code>%s</code> no existe.</p>
<a href="/" style="display:inline-block;margin-top:20px;padding:12px 22px;background:#007bff;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">Volver al Inicio</a>
""" % path

    html = page("404", body)
    start_response("404 Not Found", headers)
    return [html.encode("utf-8")]
