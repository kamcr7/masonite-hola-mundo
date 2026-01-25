# -*- coding: utf-8 -*-
import psycopg2
import base64
import imghdr
import urllib.request
import urllib.parse
import json
from urllib.parse import urlparse, parse_qs
import cgi
import re
from datetime import datetime, date

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    headers = [('Content-Type', 'text/html; charset=utf-8')]

    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin: 20px auto 30px; border-radius: 5px; max-width: 1100px;">
            <a href="/" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Formulario</a>
            <a href="/carrusel" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Carrusel</a>
            <a href="/nombre_recaptcha" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Registro</a>
            <a href="/simular_404" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Simular 404</a>
        </nav>'''

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

    def validar_nombre_solo_letras(nombre: str) -> bool:
        patron = r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$"
        return bool(re.fullmatch(patron, nombre))

    def parsear_fecha_nacimiento(fecha_str: str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    def calcular_edad_desde_fecha(fecha_nac: date) -> int:
        hoy = date.today()
        return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))

    def validar_recaptcha(recaptcha_response):
        try:
            url = 'https://www.google.com/recaptcha/api/siteverify'
            data = urllib.parse.urlencode({
                'secret': RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response
            }).encode()
            req = urllib.request.Request(url, data=data)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode())
            return result.get('success', False)
        except:
            return False

    # =========================
    # ========= INICIO =========
    # =========================
    if path == '/' and method == 'GET':
        html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Inicio</title>
<style>
body {{ font-family: Arial, sans-serif; margin:0; background:#f8f9fa; }}
.container {{ max-width: 900px; margin: 0 auto 40px; background:white; padding:40px; border-radius:10px; box-shadow:0 2px 10px rgba(0,0,0,0.1); }}
h1 {{ text-align:center; }}
.features {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin-top:25px; }}
.feature {{ background:#e9ecef; padding:18px; border-radius:10px; text-align:center; }}
.btn404 {{ display:inline-block; margin-top:20px; padding:12px 22px; background:#dc3545; color:white; text-decoration:none; border-radius:6px; font-weight:bold; }}
.btn404:hover {{ background:#c82333; }}
</style>
</head>
<body>
{navegacion()}
<div class="container">
  <h1>Aplicación</h1>
  <div class="features">
    <div class="feature"><h3>Calculadora</h3><a href="/calculadora">Ir →</a></div>
    <div class="feature"><h3>Formulario</h3><a href="/formulario">Ir →</a></div>
    <div class="feature"><h3>Carrusel</h3><a href="/carrusel">Ir →</a></div>
    <div class="feature"><h3>Registro</h3><a href="/nombre_recaptcha">Ir →</a></div>
  </div>
  <div style="text-align:center;">
    <a class="btn404" href="/simular_404">Simular pantalla 404</a>
  </div>
</div>
</body></html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # ===========================
    # ======== CALCULADORA =======
    # ===========================
    if path == '/calculadora':
        resultado_suma = ""
        resultado_division = ""

        if method == 'POST':
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            if content_length > 0:
                post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                params = parse_qs(post_data)

                try:
                    num1 = float(params.get('suma1', [''])[0])
                    num2 = float(params.get('suma2', [''])[0])
                    resultado_suma = f"<div class='ok'>Resultado: {num1} + {num2} = {num1 + num2}</div>"
                except:
                    resultado_suma = "<div class='bad'>Ingresa SOLO números válidos para la suma</div>"

                try:
                    num3 = float(params.get('div1', [''])[0])
                    num4 = float(params.get('div2', [''])[0])
                    if num4 == 0:
                        resultado_division = "<div class='bad'>No se puede dividir entre cero</div>"
                    else:
                        resultado_division = f"<div class='ok'>Resultado: {num3} ÷ {num4} = {num3 / num4:.2f}</div>"
                except:
                    resultado_division = "<div class='bad'>Ingresa SOLO números válidos para la división</div>"

        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Calculadora</title>
<style>
body{{font-family:Arial;margin:0;background:#f8f9fa;}}
.container{{max-width:900px;margin:0 auto 40px;background:white;padding:40px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;}}
.box{{background:#f8f9fa;padding:20px;border-radius:10px;}}
input{{width:95%;padding:10px;margin:8px 0;}}
button{{width:100%;padding:12px;background:#007bff;color:white;border:none;border-radius:6px;font-weight:bold;}}
.ok{{background:#d4edda;color:#155724;padding:10px;border-radius:6px;margin-top:10px;}}
.bad{{background:#f8d7da;color:#721c24;padding:10px;border-radius:6px;margin-top:10px;}}
@media(max-width:768px){{.grid{{grid-template-columns:1fr;}}}}
</style></head>
<body>
{navegacion()}
<div class="container">
<h1 style="text-align:center;">Calculadora</h1>
<div class="grid">
  <div class="box">
    <h3>Suma</h3>
    <form method="POST">
      <!-- SOLO NÚMEROS -->
      <input type="number" step="any" name="suma1" placeholder="10" required>
      <input type="number" step="any" name="suma2" placeholder="5" required>
      <button>Calcular</button>
    </form>
    {resultado_suma}
  </div>
  <div class="box">
    <h3>División</h3>
    <form method="POST">
      <!-- SOLO NÚMEROS -->
      <input type="number" step="any" name="div1" placeholder="10" required>
      <input type="number" step="any" name="div2" placeholder="2" required>
      <button>Calcular</button>
    </form>
    {resultado_division}
  </div>
</div>
</div>
</body></html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # =========================
    # ========= FORMULARIO =====
    # =========================
    if path == '/formulario':
        mensaje = ""

        if method == 'POST':
            try:
                fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)

                # BOTÓN BORRAR REGISTROS
                if (fs.getvalue('borrar_todo') or '').strip() == '1':
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("DELETE FROM formulario_simple")
                        conn.commit()
                        cur.close()
                        conn.close()
                        mensaje = "<div class='ok'><b>Listo:</b> registros eliminados.</div>"
                    else:
                        mensaje = "<div class='bad'>Sin conexión a BD</div>"
                else:
                    nombre = fs.getvalue('nombre', '').strip()
                    fecha_nacimiento_str = fs.getvalue('fecha_nacimiento', '').strip()
                    correo = fs.getvalue('correo', '').strip()
                    correo_confirmar = fs.getvalue('correo_confirmar', '').strip()

                    imagen_file = fs['imagen']
                    imagen_data = None
                    imagen_nombre = ""
                    imagen_tipo = ""

                    if imagen_file.filename:
                        imagen_nombre = imagen_file.filename
                        imagen_data = imagen_file.file.read()
                        try:
                            imagen_tipo = imghdr.what(None, h=imagen_data) or "desconocido"
                        except:
                            imagen_tipo = "desconocido"

                    errores = []
                    if not nombre:
                        errores.append("Nombre es requerido")
                    elif not validar_nombre_solo_letras(nombre):
                        errores.append("Nombre solo debe tener letras y espacios")

                    fecha_nacimiento = None
                    if not fecha_nacimiento_str:
                        errores.append("Fecha de nacimiento es requerida")
                    else:
                        fecha_nacimiento = parsear_fecha_nacimiento(fecha_nacimiento_str)
                        if not fecha_nacimiento:
                            errores.append("Fecha de nacimiento no válida")
                        elif fecha_nacimiento > date.today():
                            errores.append("La fecha no puede ser futura")

                    if not correo:
                        errores.append("Correo es requerido")
                    elif correo != correo_confirmar:
                        errores.append("Los correos no coinciden")

                    if not imagen_data:
                        errores.append("Debe subir una imagen")
                    elif len(imagen_data) > 5 * 1024 * 1024:
                        errores.append("La imagen es demasiado grande (máximo 5MB)")
                    elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                        errores.append("Solo se permiten JPG/PNG/GIF")

                    if errores:
                        mensaje = "<div class='bad'><ul>" + "".join(f"<li>{e}</li>" for e in errores) + "</ul></div>"
                    else:
                        conn = conectar_bd()
                        if conn:
                            cur = conn.cursor()
                            cur.execute('''
                                CREATE TABLE IF NOT EXISTS formulario_simple (
                                    id SERIAL PRIMARY KEY,
                                    nombre VARCHAR(100),
                                    fecha_nacimiento DATE,
                                    correo VARCHAR(100),
                                    imagen_nombre VARCHAR(255),
                                    imagen_tipo VARCHAR(20),
                                    imagen_data BYTEA,
                                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            ''')
                            cur.execute("ALTER TABLE formulario_simple ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE;")

                            cur.execute(
                                """INSERT INTO formulario_simple
                                   (nombre, fecha_nacimiento, correo, imagen_nombre, imagen_tipo, imagen_data)
                                   VALUES (%s, %s, %s, %s, %s, %s)""",
                                (nombre, fecha_nacimiento, correo, imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                            )
                            conn.commit()
                            cur.close()
                            conn.close()

                            edad_mostrar = calcular_edad_desde_fecha(fecha_nacimiento)
                            mensaje = f"<div class='ok'><b>Guardado:</b> {nombre} (Edad: {edad_mostrar})</div>"
                        else:
                            mensaje = "<div class='bad'>Sin conexión a BD</div>"
            except Exception as e:
                mensaje = f"<div class='bad'>Error: {str(e)}</div>"

        # ---- mostrar registros ----
        registros_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, fecha_nacimiento, correo, fecha
                    FROM formulario_simple
                    ORDER BY fecha DESC
                    LIMIT 10
                """)
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    items = ""
                    for r in rows:
                        rid, n, fn, c, f = r
                        edad = calcular_edad_desde_fecha(fn) if fn else ""
                        items += f"<div class='item'><b>{n}</b> — Edad: {edad} — {c}<br><small>{str(f)[:16]}</small></div>"
                    registros_html = f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
                      <h3 style="margin:0;">Registros guardados</h3>
                      <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros?');">
                        <input type="hidden" name="borrar_todo" value="1">
                        <button class="danger" type="submit">Borrar registros</button>
                      </form>
                    </div>
                    <div class='list'>{items}</div>
                    """
                else:
                    registros_html = "<p>No hay registros aún.</p>"
            except Exception as e:
                registros_html = f"<div class='bad'>Error cargando registros: {str(e)}</div>"
        else:
            registros_html = "<div class='bad'>Sin conexión a BD</div>"

        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Formulario</title>
<style>
body{{font-family:Arial;margin:0;background:#f8f9fa;}}
.container{{max-width:900px;margin:0 auto 40px;background:white;padding:40px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}}
input{{width:95%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;}}
button{{width:100%;padding:12px;background:#28a745;color:white;border:none;border-radius:6px;font-weight:bold;}}
.ok{{background:#d4edda;color:#155724;padding:12px;border-radius:6px;margin:15px 0;}}
.bad{{background:#f8d7da;color:#721c24;padding:12px;border-radius:6px;margin:15px 0;}}
.list{{background:#f8f9fa;padding:15px;border-radius:10px;margin-top:10px;}}
.item{{background:white;padding:12px;border-radius:8px;margin:10px 0;border-left:4px solid #007bff;}}
.danger{{width:auto;padding:10px 14px;background:#dc3545;}}
.danger:hover{{background:#c82333;}}
</style></head>
<body>
{navegacion()}
<div class="container">
<h1 style="text-align:center;">Formulario</h1>
{mensaje}
<form method="POST" enctype="multipart/form-data">
  <input name="nombre" placeholder="Nombre" required
         oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">
  <input type="date" name="fecha_nacimiento" required>
  <input type="email" name="correo" placeholder="Correo" required>
  <input type="email" name="correo_confirmar" placeholder="Confirmar correo" required>
  <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
  <button type="submit">Guardar</button>
</form>
<hr style="margin:30px 0;">
{registros_html}
</div>
</body></html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # =========================
    # ======== REGISTRO =======
    # =========================
    if path == '/nombre_recaptcha':
        mensaje = ""

        if method == 'POST':
            try:
                fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)

                # BOTÓN BORRAR REGISTROS
                if (fs.getvalue('borrar_todo') or '').strip() == '1':
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("DELETE FROM nombres_recaptcha")
                        conn.commit()
                        cur.close()
                        conn.close()
                        mensaje = "<div class='ok'>Registros eliminados.</div>"
                    else:
                        mensaje = "<div class='bad'>Sin conexión a BD</div>"
                else:
                    nombre = fs.getvalue('nombre', '').strip()
                    recaptcha_response = fs.getvalue('g-recaptcha-response', '').strip()

                    errores = []
                    if not nombre:
                        errores.append("Nombre es requerido")
                    elif not validar_nombre_solo_letras(nombre):
                        errores.append("Nombre solo debe tener letras y espacios")

                    if not recaptcha_response:
                        errores.append("Completa el reCAPTCHA")
                    elif not validar_recaptcha(recaptcha_response):
                        errores.append("reCAPTCHA inválido")

                    if errores:
                        mensaje = "<div class='bad'><ul>" + "".join(f"<li>{e}</li>" for e in errores) + "</ul></div>"
                    else:
                        conn = conectar_bd()
                        if conn:
                            cur = conn.cursor()
                            cur.execute('''
                                CREATE TABLE IF NOT EXISTS nombres_recaptcha (
                                    id SERIAL PRIMARY KEY,
                                    nombre VARCHAR(100),
                                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            ''')
                            cur.execute("INSERT INTO nombres_recaptcha (nombre) VALUES (%s)", (nombre,))
                            conn.commit()
                            cur.close()
                            conn.close()
                            mensaje = "<div class='ok'>Registro guardado</div>"
                        else:
                            mensaje = "<div class='bad'>Sin conexión a BD</div>"
            except Exception as e:
                mensaje = f"<div class='bad'>Error: {str(e)}</div>"

        # lista
        lista_html = ""
        conn = conectar_bd()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT nombre, fecha FROM nombres_recaptcha ORDER BY fecha DESC LIMIT 15")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            if rows:
                lista_html = "<ul>" + "".join(
                    f"<li><b>{n}</b> <small>({str(f)[:16]})</small></li>" for n, f in rows
                ) + "</ul>"
            else:
                lista_html = "<p>No hay nombres aún.</p>"

        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Registro</title>
<script src="https://www.google.com/recaptcha/api.js" async defer></script>
<style>
body{{font-family:Arial;margin:0;background:#f8f9fa;}}
.container{{max-width:900px;margin:0 auto 40px;background:white;padding:40px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}}
input{{width:95%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;}}
button{{width:100%;padding:12px;background:#28a745;color:white;border:none;border-radius:6px;font-weight:bold;}}
.ok{{background:#d4edda;color:#155724;padding:12px;border-radius:6px;margin:15px 0;}}
.bad{{background:#f8d7da;color:#721c24;padding:12px;border-radius:6px;margin:15px 0;}}
.recap{{background:#f8f9fa;padding:15px;border-radius:10px;margin:15px 0;text-align:center;}}
.danger{{width:auto;padding:10px 14px;background:#dc3545;border-radius:6px;border:none;color:white;font-weight:bold;cursor:pointer;}}
.danger:hover{{background:#c82333;}}
.headerRow{{display:flex;justify-content:space-between;align-items:center;gap:10px;}}
</style></head>
<body>
{navegacion()}
<div class="container">
<h1 style="text-align:center;">Registro</h1>
{mensaje}
<form method="POST">
  <input name="nombre" placeholder="Nombre" required
         oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">
  <div class="recap"><div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}"></div></div>
  <button type="submit">Guardar</button>
</form>

<hr style="margin:30px 0;">

<div class="headerRow">
  <h3 style="margin:0;">Nombres ingresados (últimos 15)</h3>
  <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros de Registro?');">
    <input type="hidden" name="borrar_todo" value="1">
    <button class="danger" type="submit">Borrar registros</button>
  </form>
</div>

{lista_html}
</div>
</body></html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # =========================
    # ======= SIMULAR 404 ======
    # =========================
    if path == '/simular_404':
        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Simular 404</title>
<style>
body{{font-family:Arial;margin:0;background:#f8f9fa;}}
.container{{max-width:800px;margin:0 auto 40px;background:white;padding:60px;border-radius:10px;box-shadow:0 2px 20px rgba(0,0,0,0.1);text-align:center;}}
.btn{{display:inline-block;margin-top:20px;padding:12px 22px;background:#007bff;color:white;text-decoration:none;border-radius:6px;font-weight:bold;}}
</style></head>
<body>
{navegacion()}
<div class="container">
  <h1 style="color:#dc3545;font-size:48px;">404</h1>
  <h2>Simulación de página no encontrada</h2>
  <p>Esta ruta existe, pero responde como <b>404</b>.</p>
  <a class="btn" href="/">Volver al Inicio</a>
</div>
</body></html>'''
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]

    # =========================
    # ========= CARRUSEL =======
    # =========================
    if path == '/carrusel':
        mensaje = ""

        if method == 'POST':
            fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)

            eliminar_id = (fs.getvalue('eliminar_id') or '').strip()
            if eliminar_id:
                conn = conectar_bd()
                if conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM carrusel_imagenes WHERE id = %s", (eliminar_id,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    mensaje = "<div class='ok'>Imagen eliminada</div>"
            else:
                imagen_file = fs['imagen']
                imagen_data = None
                imagen_nombre = ""
                imagen_tipo = ""

                if imagen_file.filename:
                    imagen_nombre = imagen_file.filename
                    imagen_data = imagen_file.file.read()
                    imagen_tipo = imghdr.what(None, h=imagen_data) or "desconocido"

                errores = []
                if not imagen_data:
                    errores.append("Debe subir una imagen")
                elif len(imagen_data) > 5 * 1024 * 1024:
                    errores.append("Máximo 5MB")
                elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                    errores.append("Solo JPG/PNG/GIF")

                if errores:
                    mensaje = "<div class='bad'><ul>" + "".join(f"<li>{e}</li>" for e in errores) + "</ul></div>"
                else:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute('''
                            CREATE TABLE IF NOT EXISTS carrusel_imagenes (
                                id SERIAL PRIMARY KEY,
                                titulo VARCHAR(100),
                                descripcion TEXT,
                                imagen_nombre VARCHAR(255),
                                imagen_tipo VARCHAR(20),
                                imagen_data BYTEA,
                                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
                        cur.execute(
                            """INSERT INTO carrusel_imagenes (titulo, descripcion, imagen_nombre, imagen_tipo, imagen_data)
                               VALUES (%s, %s, %s, %s, %s)""",
                            (imagen_nombre or "Imagen", "", imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                        mensaje = "<div class='ok'>Imagen agregada</div>"

        # leer imágenes
        imagenes = []
        conn = conectar_bd()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id, imagen_tipo, fecha FROM carrusel_imagenes ORDER BY fecha DESC")
            imagenes = cur.fetchall()
            cur.close()
            conn.close()

        slides = ""
        if imagenes:
            for i, (img_id, img_tipo, f) in enumerate(imagenes):
                conn2 = conectar_bd()
                cur2 = conn2.cursor()
                cur2.execute("SELECT imagen_data FROM carrusel_imagenes WHERE id=%s", (img_id,))
                data = cur2.fetchone()[0]
                cur2.close()
                conn2.close()
                b64 = base64.b64encode(data).decode('utf-8')
                active = "active" if i == 0 else ""
                slides += f'''
                <div class="slide {active}">
                  <img src="data:image/{img_tipo};base64,{b64}">
                  <form method="POST" onsubmit="return confirm('¿Eliminar esta imagen?');">
                    <input type="hidden" name="eliminar_id" value="{img_id}">
                    <button class="del">Eliminar</button>
                  </form>
                </div>
                '''
        else:
            slides = "<p>No hay imágenes.</p>"

        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Carrusel</title>
<style>
body{{font-family:Arial;margin:0;background:#f8f9fa;}}
.container{{max-width:1000px;margin:0 auto 40px;background:white;padding:40px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}}
.ok{{background:#d4edda;color:#155724;padding:12px;border-radius:6px;margin:15px 0;}}
.bad{{background:#f8d7da;color:#721c24;padding:12px;border-radius:6px;margin:15px 0;}}
.slide{{display:none;text-align:center;}}
.slide.active{{display:block;}}
img{{max-width:100%;max-height:520px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.2);}}
.controls{{display:flex;justify-content:space-between;align-items:center;margin-top:15px;}}
.btn{{background:#007bff;color:white;border:none;border-radius:50%;width:50px;height:50px;font-size:20px;cursor:pointer;}}
.del{{margin-top:12px;padding:10px 18px;background:#dc3545;color:white;border:none;border-radius:6px;font-weight:bold;cursor:pointer;}}
.form{{background:#f8f9fa;padding:20px;border-radius:10px;margin-top:25px;}}
input[type=file]{{width:95%;padding:10px;background:white;border:1px solid #ddd;border-radius:6px;}}
.add{{width:100%;padding:12px;background:#28a745;color:white;border:none;border-radius:6px;font-weight:bold;margin-top:10px;}}
</style></head>
<body>
{navegacion()}
<div class="container">
<h1 style="text-align:center;">Carrusel</h1>
{mensaje}
<div id="wrap">{slides}</div>
<div class="controls">
  <button class="btn" onclick="prev()">◀</button>
  <button class="btn" onclick="next()">▶</button>
</div>

<div class="form">
  <h3>Agregar imagen</h3>
  <form method="POST" enctype="multipart/form-data">
    <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
    <button class="add">Agregar</button>
  </form>
</div>
</div>

<script>
let idx = 0;
const slides = document.querySelectorAll('.slide');
function show(i){
  if(slides.length===0) return;
  slides.forEach(s=>s.classList.remove('active'));
  idx = (i+slides.length)%slides.length;
  slides[idx].classList.add('active');
}
function next(){ show(idx+1); }
function prev(){ show(idx-1); }
document.addEventListener('DOMContentLoaded', ()=>show(0));
</script>

</body></html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # =========================
    # ========== 404 ===========
    # =========================
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>404</title>
<style>
body{{font-family:Arial;margin:0;background:#f8f9fa;}}
.container{{max-width:800px;margin:0 auto 40px;background:white;padding:60px;border-radius:10px;box-shadow:0 2px 20px rgba(0,0,0,0.1);text-align:center;}}
.btn{{display:inline-block;margin-top:20px;padding:12px 22px;background:#007bff;color:white;text-decoration:none;border-radius:6px;font-weight:bold;}}
</style></head>
<body>
{navegacion()}
<div class="container">
  <h1 style="color:#dc3545;font-size:48px;">404</h1>
  <h2>Página no encontrada</h2>
  <p>La ruta solicitada <code>{path}</code> no existe.</p>
  <a class="btn" href="/">Volver al Inicio</a>
</div>
</body></html>'''
    start_response('404 Not Found', headers)
    return [html.encode('utf-8')]
