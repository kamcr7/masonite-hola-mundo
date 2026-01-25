# -*- coding: utf-8 -*-
import os
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
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Formulario</a>
            <a href="/carrusel" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Carrusel</a>
            <a href="/nombre_recaptcha" style="color: white; margin: 0 12px; text-decoration: none; font-weight: bold;">Nombre + reCAPTCHA</a>
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
        except Exception as e:
            print(f"Error validando reCAPTCHA: {e}")
            return False

    # =========================
    # ======== CARRUSEL =======
    # =========================
    if path == '/carrusel':
        mensaje = ""

        if method == 'POST':
            try:
                fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)

                eliminar_id = (fs.getvalue('eliminar_id') or '').strip()
                if eliminar_id:
                    conn = conectar_bd()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM carrusel_imagenes WHERE id = %s", (eliminar_id,))
                            conn.commit()
                            cur.close()
                            conn.close()
                            mensaje = "<div class='exito'><h3>Imagen eliminada</h3><p>Se eliminó correctamente.</p></div>"
                        except Exception as e:
                            mensaje = f"<div class='error'>Error al eliminar: {str(e)}</div>"
                    else:
                        mensaje = "<div class='error'>Error de conexión a la base de datos</div>"
                else:
                    imagen_file = fs['imagen']
                    imagen_data = None
                    imagen_nombre = ""
                    imagen_tipo = ""

                    if hasattr(imagen_file, "filename") and imagen_file.filename:
                        imagen_nombre = imagen_file.filename
                        imagen_data = imagen_file.file.read()
                        try:
                            imagen_tipo = imghdr.what(None, h=imagen_data) or "desconocido"
                        except:
                            imagen_tipo = "desconocido"

                    errores = []
                    if not imagen_data:
                        errores.append("Debe subir una imagen")
                    elif len(imagen_data) > 5 * 1024 * 1024:
                        errores.append("La imagen es demasiado grande (máximo 5MB)")
                    elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                        errores.append("Solo se permiten imágenes JPG, PNG o GIF")

                    if errores:
                        mensaje = f'''<div class="error"><h3>Errores encontrados:</h3>
                            <ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul></div>'''
                    else:
                        titulo = imagen_nombre if imagen_nombre else "Imagen"
                        descripcion = ""

                        conn = conectar_bd()
                        if conn:
                            try:
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
                                    """INSERT INTO carrusel_imagenes
                                       (titulo, descripcion, imagen_nombre, imagen_tipo, imagen_data)
                                       VALUES (%s, %s, %s, %s, %s)""",
                                    (titulo, descripcion, imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                                )
                                conn.commit()
                                cur.close()
                                conn.close()

                                mensaje = f'''<div class="exito">
                                    <h3>¡Imagen agregada!</h3>
                                    <p><strong>Imagen:</strong> {imagen_nombre} ({imagen_tipo.upper()})</p>
                                </div>'''
                            except Exception as e:
                                mensaje = f'<div class="error">Error al guardar: {str(e)}</div>'
                        else:
                            mensaje = '<div class="error">Error de conexión a la base de datos</div>'
            except Exception as e:
                mensaje = f'<div class="error">Error procesando formulario: {str(e)}</div>'

        # Obtener imágenes
        imagenes = []
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, titulo, imagen_tipo, fecha
                    FROM carrusel_imagenes
                    ORDER BY fecha DESC
                """)
                imagenes = cur.fetchall()
                cur.close()
                conn.close()
            except:
                imagenes = []

        imagenes_html = ""
        if imagenes:
            imagenes_html += '''
            <div class="carrusel-container">
                <h3>Carrusel de Imágenes</h3>
                <div class="carrusel" id="carrusel">
            '''

            for i, img in enumerate(imagenes):
                id_img, titulo_img, img_tipo, fecha = img

                img_base64 = ""
                conn2 = conectar_bd()
                if conn2:
                    try:
                        cur2 = conn2.cursor()
                        cur2.execute("SELECT imagen_data, imagen_nombre FROM carrusel_imagenes WHERE id = %s", (id_img,))
                        row = cur2.fetchone()
                        cur2.close()
                        conn2.close()
                        if row and row[0]:
                            img_data = row[0]
                            img_nombre = row[1] if row[1] else ""
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                        else:
                            img_nombre = ""
                    except:
                        img_nombre = ""

                if img_base64:
                    activa = "active" if i == 0 else ""
                    imagenes_html += f'''
                    <div class="carrusel-item {activa}">
                        <img src="data:image/{img_tipo};base64,{img_base64}" class="carrusel-imagen" alt="{titulo_img}">
                        <form method="POST" style="margin-top: 15px;" onsubmit="return confirm('¿Eliminar esta imagen?');">
                            <input type="hidden" name="eliminar_id" value="{id_img}">
                            <button type="submit" class="btn-eliminar">Eliminar</button>
                        </form>
                    </div>
                    '''

            imagenes_html += '''
                </div>
                <div class="carrusel-controls">
                    <button class="carrusel-btn prev" onclick="carruselPrev()">◀</button>
                    <div class="carrusel-indicators" id="indicators"></div>
                    <button class="carrusel-btn next" onclick="carruselNext()">▶</button>
                </div>
            </div>
            '''
        else:
            imagenes_html = '''
            <div class="sin-imagenes">
                <h3>No hay imágenes en el carrusel</h3>
                <p>Agrega tu primera imagen usando el formulario de abajo.</p>
            </div>
            '''

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Carrusel</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ text-align:center; margin-bottom:30px; }}
        .carrusel-container {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px; }}
        .carrusel {{ position: relative; overflow: hidden; border-radius: 10px; background: white; }}
        .carrusel-item {{ display:none; text-align:center; padding:20px; }}
        .carrusel-item.active {{ display:block; }}
        .carrusel-imagen {{ max-width:100%; max-height:520px; border-radius:10px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        .carrusel-controls {{ display:flex; justify-content:space-between; align-items:center; margin-top: 15px; }}
        .carrusel-btn {{ background:#007bff; color:white; border:none; border-radius:50%; width:50px; height:50px; font-size:20px; cursor:pointer; }}
        .carrusel-btn:hover {{ background:#0056b3; }}
        .carrusel-indicators {{ display:flex; gap:10px; justify-content:center; flex:1; }}
        .indicator {{ width:12px; height:12px; border-radius:50%; background:#ccc; cursor:pointer; }}
        .indicator.active {{ background:#007bff; }}
        .form-agregar {{ background:#f8f9fa; padding: 25px; border-radius: 10px; margin-top: 30px; }}
        .campo {{ margin: 15px 0; }}
        label {{ font-weight: bold; display:block; margin-bottom:8px; }}
        input[type="file"] {{ width: 95%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; background:white; }}
        .btn-agregar {{ width:100%; padding: 14px; background:#28a745; color:white; border:none; border-radius:6px; font-weight:bold; font-size:16px; cursor:pointer; }}
        .btn-agregar:hover {{ background:#218838; }}
        .btn-eliminar {{ padding: 10px 18px; background:#dc3545; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer; }}
        .btn-eliminar:hover {{ background:#c82333; }}
        .exito {{ background:#d4edda; color:#155724; padding:15px; border-radius:6px; border-left:4px solid #28a745; margin: 15px 0; }}
        .error {{ background:#f8d7da; color:#721c24; padding:15px; border-radius:6px; border-left:4px solid #dc3545; margin: 15px 0; }}
        .sin-imagenes {{ text-align:center; padding: 30px; background:#e9ecef; border-radius:10px; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Carrusel de Imágenes</h1>
        {mensaje if mensaje else ''}
        {imagenes_html}

        <div class="form-agregar">
            <h3>Agregar imagen</h3>
            <form method="POST" enctype="multipart/form-data">
                <div class="campo">
                    <label>Seleccionar imagen *</label>
                    <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
                </div>
                <button class="btn-agregar" type="submit">Agregar</button>
            </form>
        </div>
    </div>

    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.carrusel-item');
        const indicatorsContainer = document.getElementById('indicators');

        function crearIndicadores() {{
            if (!indicatorsContainer || slides.length === 0) return;
            indicatorsContainer.innerHTML = '';
            for (let i = 0; i < slides.length; i++) {{
                const d = document.createElement('div');
                d.className = 'indicator';
                if (i === currentSlide) d.classList.add('active');
                d.onclick = () => goToSlide(i);
                indicatorsContainer.appendChild(d);
            }}
        }}

        function showSlide(index) {{
            if (slides.length === 0) return;
            if (index >= slides.length) currentSlide = 0;
            else if (index < 0) currentSlide = slides.length - 1;
            else currentSlide = index;

            slides.forEach(s => s.classList.remove('active'));
            slides[currentSlide].classList.add('active');

            const inds = document.querySelectorAll('.indicator');
            inds.forEach((ind, i) => ind.classList.toggle('active', i === currentSlide));
        }}

        function carruselNext() {{ showSlide(currentSlide + 1); }}
        function carruselPrev() {{ showSlide(currentSlide - 1); }}
        function goToSlide(i) {{ showSlide(i); }}

        document.addEventListener('DOMContentLoaded', function() {{
            crearIndicadores();
            showSlide(0);
        }});
    </script>
</body>
</html>'''

        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # =========================================
    # ========= SIMULAR 404 (SIN RECUADRO) =====
    # =========================================
    if path == '/simular_404':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Simulación 404</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 100px auto;
            padding: 40px;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 60px;
            border-radius: 10px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            text-align: center;
        }}
        h1 {{ color: #dc3545; font-size: 48px; margin-bottom: 10px; }}
        h2 {{ color: #333; margin-bottom: 20px; }}
        p {{ color:#555; font-size:16px; line-height:1.5; }}
        .btn {{
            display: inline-block;
            margin-top: 25px;
            padding: 14px 26px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
        }}
        .btn:hover {{ background:#0056b3; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>404</h1>
        <h2>Simulación de página no encontrada</h2>
        <p>Esta ruta <code>/simular_404</code> existe, pero responde como <strong>404</strong> para que pruebes tu pantalla.</p>
        <a href="/" class="btn">Volver al Inicio</a>
    </div>
</body>
</html>'''
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]

    # ==================================================
    # ===== NOMBRE + reCAPTCHA (sin cambios) ============
    # ==================================================
    if path == '/nombre_recaptcha':
        mensaje = ""

        if method == 'POST':
            try:
                fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)

                nombre = fs.getvalue('nombre', '').strip()
                recaptcha_response = fs.getvalue('g-recaptcha-response', '').strip()

                errores = []
                if not nombre:
                    errores.append("Nombre es requerido")
                elif not validar_nombre_solo_letras(nombre):
                    errores.append("Nombre solo debe contener letras y espacios (sin números ni símbolos)")

                if not recaptcha_response:
                    errores.append("Por favor, completa el reCAPTCHA")
                elif not validar_recaptcha(recaptcha_response):
                    errores.append("El reCAPTCHA no es válido. Intenta de nuevo.")

                if errores:
                    mensaje = f'''<div class="error"><h3>Errores:</h3>
                        <ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul></div>'''
                else:
                    conn = conectar_bd()
                    if conn:
                        try:
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

                            mensaje = f'''<div class="exito">
                                <h3>¡Nombre guardado!</h3>
                                <p><strong>Nombre:</strong> {nombre}</p>
                            </div>'''
                        except Exception as e:
                            mensaje = f'<div class="error">Error guardando en BD: {str(e)}</div>'
                    else:
                        mensaje = '<div class="error">Error de conexión a la base de datos</div>'
            except Exception as e:
                mensaje = f'<div class="error">Error procesando formulario: {str(e)}</div>'

        lista_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT nombre, fecha FROM nombres_recaptcha ORDER BY fecha DESC LIMIT 15")
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    items = ""
                    for n, f in rows:
                        items += f"<li><strong>{n}</strong> <small style='color:#6c757d;'>({str(f)[:16]})</small></li>"
                    lista_html = f"""
                    <div class="lista">
                        <h3>Nombres ingresados (últimos 15)</h3>
                        <ul>{items}</ul>
                    </div>
                    """
                else:
                    lista_html = "<div class='lista'><p>No hay nombres aún.</p></div>"
            except Exception as e:
                lista_html = f"<div class='error'>Error cargando nombres: {str(e)}</div>"
        else:
            lista_html = "<div class='error'>No hay conexión a la base de datos</div>"

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Nombre + reCAPTCHA</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ text-align:center; margin-bottom:25px; }}
        .campo {{ margin: 18px 0; }}
        label {{ font-weight:bold; display:block; margin-bottom:8px; }}
        input[type="text"] {{ width: 95%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; }}
        .recaptcha-container {{ margin: 20px 0; padding: 18px; background: #f8f9fa; border-radius: 8px; text-align:center; }}
        .btn {{ width: 100%; padding: 14px; border:none; border-radius: 6px; background:#28a745; color:white; font-size: 16px; font-weight:bold; cursor:pointer; }}
        .btn:hover {{ background:#218838; }}
        .exito {{ background:#d4edda; color:#155724; padding:15px; border-radius:6px; border-left:4px solid #28a745; margin: 15px 0; }}
        .error {{ background:#f8d7da; color:#721c24; padding:15px; border-radius:6px; border-left:4px solid #dc3545; margin: 15px 0; }}
        .lista {{ margin-top: 30px; padding: 20px; background:#f8f9fa; border-radius:10px; }}
        ul {{ margin: 10px 0 0; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Solo Nombre + reCAPTCHA</h1>

        {mensaje if mensaje else ''}

        <form method="POST">
            <div class="campo">
                <label>Nombre *</label>
                <input type="text"
                       name="nombre"
                       placeholder="Ej: Juan Pérez"
                       required
                       oninput="this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g, '')">
            </div>

            <div class="recaptcha-container">
                <div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}"></div>
            </div>

            <button class="btn" type="submit">Guardar nombre</button>
        </form>

        {lista_html}
    </div>
</body>
</html>'''

        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # =========================
    # ========= INICIO =========
    # =========================
    if path == '/' and method == 'GET':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inicio</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
        .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .feature {{ background: #e9ecef; padding: 20px; border-radius: 8px; text-align: center; }}
        .feature-icon {{ font-size: 40px; margin-bottom: 15px; }}
        .btn-error-404 {{
            display: inline-block; padding: 14px 26px; background: #dc3545; color: white;
            border-radius: 6px; text-decoration: none; font-weight: bold;
        }}
        .btn-error-404:hover {{ background:#c82333; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Aplicación Masonite en Railway</h1>

        <div class="features">
            <div class="feature">
                <div class="feature-icon">+</div>
                <h3>Calculadora</h3>
                <p>Operaciones básicas</p>
                <a href="/calculadora">Ir →</a>
            </div>

            <div class="feature">
                <div class="feature-icon">✓</div>
                <h3>Formulario</h3>
                <p>Registra datos y sube imagen (SIN reCAPTCHA)</p>
                <a href="/formulario">Ir →</a>
            </div>

            <div class="feature">
                <div class="feature-icon">▢</div>
                <h3>Carrusel</h3>
                <p>Sube imágenes al carrusel</p>
                <a href="/carrusel">Ir →</a>
            </div>

            <div class="feature">
                <div class="feature-icon">🔒</div>
                <h3>Nombre + reCAPTCHA</h3>
                <p>Solo guarda nombres con reCAPTCHA</p>
                <a href="/nombre_recaptcha">Ir →</a>
            </div>
        </div>

        <div style="text-align:center; margin-top: 20px;">
            <a class="btn-error-404" href="/simular_404">Simular pantalla 404</a>
        </div>
    </div>
</body>
</html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # =========================
    # ======== CALCULADORA =====
    # =========================
    elif path == '/calculadora':
        resultado_suma = ""
        resultado_division = ""

        if method == 'POST':
            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                if content_length > 0:
                    post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                    params = parse_qs(post_data)

                    try:
                        suma1 = params.get('suma1', [''])[0]
                        suma2 = params.get('suma2', [''])[0]
                        num1 = float(suma1)
                        num2 = float(suma2)
                        resultado_suma = f"<div class='resultado-exito'><strong>Resultado:</strong> {num1} + {num2} = {num1 + num2}</div>"
                    except:
                        resultado_suma = "<div class='resultado-error'>Ingresa números válidos para la suma</div>"

                    try:
                        div1 = params.get('div1', [''])[0]
                        div2 = params.get('div2', [''])[0]
                        num3 = float(div1)
                        num4 = float(div2)
                        if num4 == 0:
                            resultado_division = "<div class='resultado-error'>No se puede dividir entre cero</div>"
                        else:
                            resultado_division = f"<div class='resultado-exito'><strong>Resultado:</strong> {num3} ÷ {num4} = {num3 / num4:.2f}</div>"
                    except:
                        resultado_division = "<div class='resultado-error'>Ingresa números válidos para la división</div>"
            except Exception as e:
                resultado_suma = f"<div class='resultado-error'>Error: {str(e)}</div>"

        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Calculadora</title></head>
<body>{navegacion()}<div style="max-width:900px;margin:40px auto;background:white;padding:30px;border-radius:10px;">
<h1 style="text-align:center;">Calculadora</h1>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
<div style="background:#f8f9fa;padding:20px;border-radius:10px;border-left:4px solid #28a745;">
<h2>Suma</h2>
<form method="POST">
<input name="suma1" placeholder="Ej: 10" required style="width:95%;padding:10px;margin:8px 0;">
<input name="suma2" placeholder="Ej: 5" required style="width:95%;padding:10px;margin:8px 0;">
<button style="width:100%;padding:12px;background:#007bff;color:white;border:none;border-radius:6px;">Calcular</button>
</form>{resultado_suma}
</div>
<div style="background:#f8f9fa;padding:20px;border-radius:10px;border-left:4px solid #dc3545;">
<h2>División</h2>
<form method="POST">
<input name="div1" placeholder="Ej: 10" required style="width:95%;padding:10px;margin:8px 0;">
<input name="div2" placeholder="Ej: 2" required style="width:95%;padding:10px;margin:8px 0;">
<button style="width:100%;padding:12px;background:#007bff;color:white;border:none;border-radius:6px;">Calcular</button>
</form>{resultado_division}
</div>
</div></div></body></html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # ==========================================
    # ========= FORMULARIO SIN reCAPTCHA ========
    # ==========================================
    elif path == '/formulario':
        mensaje = ""

        if method == 'POST':
            try:
                fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)

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
                    errores.append("Nombre solo debe contener letras y espacios (sin números ni símbolos)")

                fecha_nacimiento = None
                if not fecha_nacimiento_str:
                    errores.append("Fecha de nacimiento es requerida")
                else:
                    fecha_nacimiento = parsear_fecha_nacimiento(fecha_nacimiento_str)
                    if not fecha_nacimiento:
                        errores.append("Fecha de nacimiento no es válida")
                    else:
                        if fecha_nacimiento > date.today():
                            errores.append("La fecha de nacimiento no puede ser futura")
                        else:
                            edad_calc = calcular_edad_desde_fecha(fecha_nacimiento)
                            if edad_calc < 0 or edad_calc > 120:
                                errores.append("La fecha no corresponde a una edad válida (0 a 120)")

                if not correo:
                    errores.append("Correo es requerido")
                elif correo != correo_confirmar:
                    errores.append("Los correos no coinciden")

                if not imagen_data:
                    errores.append("Debe subir una imagen")
                elif len(imagen_data) > 5 * 1024 * 1024:
                    errores.append("La imagen es demasiado grande (máximo 5MB)")
                elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                    errores.append("Solo se permiten imágenes JPG, PNG o GIF")

                if errores:
                    mensaje = f'''<div class="error"><h3>Errores:</h3>
                        <ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul></div>'''
                else:
                    conn = conectar_bd()
                    if conn:
                        try:
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
                            cur.execute('ALTER TABLE formulario_simple ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE;')

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
                            mensaje = f'''<div class="exito">
                                <h3>¡Registro exitoso!</h3>
                                <p><strong>Nombre:</strong> {nombre}</p>
                                <p><strong>Fecha de nacimiento:</strong> {fecha_nacimiento_str}</p>
                                <p><strong>Edad:</strong> {edad_mostrar} años</p>
                                <p><strong>Correo:</strong> {correo}</p>
                                <p><strong>Imagen:</strong> {imagen_nombre} ({imagen_tipo.upper()})</p>
                            </div>'''
                        except Exception as e:
                            mensaje = f'<div class="error">Error al guardar en BD: {str(e)}</div>'
                    else:
                        mensaje = '<div class="error">Error de conexión a la base de datos</div>'
            except Exception as e:
                mensaje = f'<div class="error">Error procesando formulario: {str(e)}</div>'

        html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Formulario</title></head>
<body>{navegacion()}<div style="max-width:900px;margin:40px auto;background:white;padding:30px;border-radius:10px;">
<h1 style="text-align:center;">Formulario (sin reCAPTCHA)</h1>{mensaje}
<form method="POST" enctype="multipart/form-data">
<input name="nombre" placeholder="Nombre" required
 oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')"
 style="width:95%;padding:10px;margin:8px 0;">
<input type="date" name="fecha_nacimiento" required style="width:95%;padding:10px;margin:8px 0;">
<input type="email" name="correo" placeholder="Correo" required style="width:95%;padding:10px;margin:8px 0;">
<input type="email" name="correo_confirmar" placeholder="Confirmar correo" required style="width:95%;padding:10px;margin:8px 0;">
<input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required style="width:95%;padding:10px;margin:8px 0;">
<button style="width:100%;padding:12px;background:#28a745;color:white;border:none;border-radius:6px;font-weight:bold;">Guardar</button>
</form></div></body></html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # =========================
    # ========== 404 ===========
    # =========================
    else:
        html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>404</title></head>
<body>{navegacion()}<div style="max-width:800px;margin:80px auto;background:white;padding:50px;border-radius:10px;text-align:center;">
<h1 style="color:#dc3545;font-size:48px;">404</h1>
<h2>Página no encontrada</h2>
<p>La ruta solicitada <code>{path}</code> no existe.</p>
<a href="/" style="display:inline-block;padding:12px 22px;background:#007bff;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">Volver al Inicio</a>
</div></body></html>'''
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
