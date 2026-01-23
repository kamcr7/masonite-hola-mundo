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
import io
import re
from datetime import datetime, date

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    # Headers UTF-8
    headers = [('Content-Type', 'text/html; charset=utf-8')]

    # === CONFIGURACIÓN ===
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"

    # === CONFIGURACIÓN RECAPTCHA ===
    RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"  # Clave de prueba
    RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"  # Secreto de prueba

    # === NAVEGACIÓN ===
    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Formulario</a>
            <a href="/carrusel" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Carrusel</a>
        </nav>'''

    # === FUNCIONES COMUNES ===
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

    # === VALIDACIONES (NOMBRE SOLO LETRAS) ===
    def validar_nombre_solo_letras(nombre: str) -> bool:
        # Solo letras (incluye acentos/ñ) y espacios. NO números, NO símbolos.
        patron = r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$"
        return bool(re.fullmatch(patron, nombre))

    # === FECHA NACIMIENTO / EDAD ===
    def parsear_fecha_nacimiento(fecha_str: str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    def calcular_edad_desde_fecha(fecha_nac: date) -> int:
        hoy = date.today()
        edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
        return edad

    # === FUNCIÓN PARA VALIDAR RECAPTCHA ===
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

    # === PÁGINA CARRUSEL (solo imágenes) ===
    if path == '/carrusel':
        mensaje = ""

        if method == 'POST':
            try:
                fs = cgi.FieldStorage(
                    fp=environ['wsgi.input'],
                    environ=environ,
                    keep_blank_values=True
                )

                eliminar_id = fs.getvalue('eliminar_id', '').strip()
                if eliminar_id:
                    conn = conectar_bd()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM carrusel_imagenes WHERE id = %s", (eliminar_id,))
                            conn.commit()
                            cur.close()
                            conn.close()
                            mensaje = f'''<div class="exito">
                                <h3>Imagen eliminada</h3>
                                <p>La imagen ha sido eliminada del carrusel.</p>
                            </div>'''
                        except Exception as e:
                            mensaje = f'<div class="error">Error al eliminar: {str(e)}</div>'
                else:
                    titulo = fs.getvalue('titulo', '').strip()
                    descripcion = fs.getvalue('descripcion', '').strip()

                    imagen_file = fs['imagen']
                    imagen_data = None
                    imagen_nombre = ""
                    imagen_tipo = ""

                    if imagen_file.filename:
                        imagen_nombre = imagen_file.filename
                        imagen_data = imagen_file.file.read()
                        try:
                            imagen_tipo = imghdr.what(None, h=imagen_data)
                            if not imagen_tipo:
                                imagen_tipo = "desconocido"
                        except:
                            imagen_tipo = "desconocido"

                    errores = []

                    if not titulo:
                        errores.append("Título es requerido")

                    if not imagen_data:
                        errores.append("Debe subir una imagen")
                    elif len(imagen_data) > 5 * 1024 * 1024:
                        errores.append("La imagen es demasiado grande (máximo 5MB)")
                    elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                        errores.append("Solo se permiten imágenes JPG, PNG o GIF")

                    if errores:
                        mensaje = f'''<div class="error">
                            <h3>Errores encontrados:</h3>
                            <ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul>
                        </div>'''
                    else:
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
                                    <h3>¡Imagen agregada al carrusel!</h3>
                                    <p><strong>Título:</strong> {titulo}</p>
                                    <p><strong>Imagen:</strong> {imagen_nombre} ({imagen_tipo.upper()})</p>
                                </div>'''

                            except Exception as e:
                                mensaje = f'<div class="error">Error al guardar: {str(e)}</div>'
                        else:
                            mensaje = '<div class="error">Error de conexión a la base de datos</div>'

            except Exception as e:
                mensaje = f'<div class="error">Error procesando formulario: {str(e)}</div>'

        # Obtener imágenes
        imagenes_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, titulo, descripcion, imagen_nombre, imagen_tipo, fecha 
                    FROM carrusel_imagenes 
                    ORDER BY fecha DESC
                """)
                imagenes = cur.fetchall()
                cur.close()
                conn.close()

                if imagenes:
                    imagenes_html += '''
                    <div class="carrusel-container">
                        <h3>Carrusel de Imágenes</h3>
                        <div class="carrusel" id="carrusel">
                    '''

                    for i, img in enumerate(imagenes):
                        id_img, titulo_img, desc_img, img_nombre, img_tipo, fecha = img

                        img_base64 = ""
                        conn2 = conectar_bd()
                        if conn2:
                            try:
                                cur2 = conn2.cursor()
                                cur2.execute("SELECT imagen_data FROM carrusel_imagenes WHERE id = %s", (id_img,))
                                img_data = cur2.fetchone()[0]
                                cur2.close()
                                conn2.close()

                                if img_data:
                                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                            except:
                                pass

                        if img_base64:
                            activa = "active" if i == 0 else ""
                            imagenes_html += f'''
                            <div class="carrusel-item {activa}" data-id="{id_img}">
                                <div class="imagen-contenedor">
                                    <img src="data:image/{img_tipo};base64,{img_base64}" 
                                         alt="{titulo_img}"
                                         class="carrusel-imagen">
                                </div>
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

                    imagenes_html += f'''
                    <div class="contador-imagenes">
                        <p>Total de imágenes en el carrusel: <strong>{len(imagenes)}</strong></p>
                    </div>
                    '''

                    imagenes_html += '''
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="/pagina_no_existe" class="btn-error-404">
                            Ir a Página 404
                        </a>
                    </div>
                    '''
                else:
                    imagenes_html = '''
                    <div class="sin-imagenes">
                        <div class="sin-imagenes-icon"></div>
                        <h3>No hay imágenes en el carrusel</h3>
                        <p>Agrega tu primera imagen usando el formulario de abajo.</p>
                    </div>
                    '''

            except Exception as e:
                imagenes_html = f'<p class="error">Error cargando imágenes: {str(e)}</p>'
        else:
            imagenes_html = '<p class="error">No hay conexión a la base de datos</p>'

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Carrusel de Imágenes</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 40px; }}
        .carrusel-container {{ margin: 40px 0; padding: 20px; background: #f8f9fa; border-radius: 10px; }}
        .carrusel {{ position: relative; overflow: hidden; border-radius: 10px; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .carrusel-item {{ display: none; padding: 30px; text-align: center; }}
        .carrusel-item.active {{ display: block; }}
        .imagen-contenedor {{ display: flex; flex-direction: column; align-items: center; gap: 20px; }}
        .carrusel-imagen {{ max-width: 100%; max-height: 500px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        .carrusel-controls {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; padding: 10px; }}
        .carrusel-btn {{ background: #007bff; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
        .carrusel-btn:hover {{ background: #0056b3; }}
        .carrusel-indicators {{ display: flex; gap: 10px; justify-content: center; flex: 1; }}
        .indicator {{ width: 12px; height: 12px; border-radius: 50%; background: #ccc; cursor: pointer; transition: background 0.3s; }}
        .indicator.active {{ background: #007bff; }}
        .contador-imagenes {{ text-align: center; margin: 20px 0; padding: 15px; background: #e7f3ff; border-radius: 5px; }}
        .btn-error-404 {{ display: inline-block; padding: 15px 30px; background: #dc3545; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; text-decoration: none; transition: background 0.3s; }}
        .btn-error-404:hover {{ background: #c82333; color: white; text-decoration: none; }}
        .sin-imagenes {{ text-align: center; padding: 60px 20px; background: #e9ecef; border-radius: 10px; margin: 40px 0; }}
        .form-agregar {{ background: #f8f9fa; padding: 30px; border-radius: 10px; margin-top: 40px; }}
        .campo {{ margin: 20px 0; }}
        label {{ display: block; margin-bottom: 8px; font-weight: bold; color: #555; }}
        input[type="text"], textarea, input[type="file"] {{ width: 95%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
        textarea {{ min-height: 100px; resize: vertical; }}
        .requerido {{ color: #dc3545; }}
        .info {{ font-size: 14px; color: #6c757d; margin-top: 5px; }}
        .btn-agregar {{ padding: 15px 30px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 18px; font-weight: bold; width: 100%; margin-top: 20px; }}
        .btn-agregar:hover {{ background: #218838; }}
        .exito {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545; }}
        .instrucciones {{ background: #fff3cd; color: #856404; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Carrusel de Imágenes</h1>

        {mensaje if mensaje else ''}

        {imagenes_html}

        <div class="form-agregar">
            <h3>Agregar Nueva Imagen al Carrusel</h3>
            <form method="POST" enctype="multipart/form-data">
                <div class="campo">
                    <label>Título de la imagen <span class="requerido">*</span></label>
                    <input type="text" name="titulo" placeholder="Ej: Paisaje de montaña" required>
                </div>
                <div class="campo">
                    <label>Descripción (opcional)</label>
                    <textarea name="descripcion" placeholder="Describe la imagen..."></textarea>
                </div>
                <div class="campo">
                    <label>Seleccionar imagen <span class="requerido">*</span></label>
                    <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
                </div>
                <button type="submit" class="btn-agregar">Agregar al Carrusel</button>
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
                const indicator = document.createElement('div');
                indicator.className = 'indicator';
                if (i === currentSlide) indicator.classList.add('active');
                indicator.onclick = () => goToSlide(i);
                indicatorsContainer.appendChild(indicator);
            }}
        }}

        function showSlide(index) {{
            if (slides.length === 0) return;
            if (index >= slides.length) currentSlide = 0;
            else if (index < 0) currentSlide = slides.length - 1;
            else currentSlide = index;

            slides.forEach(slide => slide.classList.remove('active'));
            slides[currentSlide].classList.add('active');

            const indicators = document.querySelectorAll('.indicator');
            indicators.forEach((indicator, i) => indicator.classList.toggle('active', i === currentSlide));
        }}

        function carruselNext() {{ showSlide(currentSlide + 1); }}
        function carruselPrev() {{ showSlide(currentSlide - 1); }}
        function goToSlide(index) {{ showSlide(index); }}

        let carruselInterval;
        function iniciarAutoPlay() {{
            if (slides.length > 1) carruselInterval = setInterval(carruselNext, 5000);
        }}
        function detenerAutoPlay() {{
            if (carruselInterval) clearInterval(carruselInterval);
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            crearIndicadores();
            iniciarAutoPlay();
            const carrusel = document.getElementById('carrusel');
            if (carrusel) {{
                carrusel.addEventListener('mouseenter', detenerAutoPlay);
                carrusel.addEventListener('mouseleave', iniciarAutoPlay);
            }}
        }});
    </script>
</body>
</html>'''

        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # === PÁGINA PRINCIPAL ===
    if path == '/' and method == 'GET':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inicio - Aplicación Masonite</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
        .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .feature {{ background: #e9ecef; padding: 20px; border-radius: 8px; text-align: center; }}
        .feature-icon {{ font-size: 40px; margin-bottom: 15px; }}
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
                <p>Operaciones básicas de suma y división</p>
                <a href="/calculadora">Ir a Calculadora →</a>
            </div>

            <div class="feature">
                <div class="feature-icon">✓</div>
                <h3>Formulario con Imágenes</h3>
                <p>Registra datos y sube imágenes</p>
                <a href="/formulario">Ir a Formulario →</a>
            </div>

            <div class="feature">
                <div class="feature-icon">▢</div>
                <h3>Carrusel de Imágenes</h3>
                <p>Galería interactiva de imágenes</p>
                <a href="/carrusel">Ir a Carrusel →</a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px; padding: 20px; background: #e7f3ff; border-radius: 8px;">
            <h3>Seguridad mejorada</h3>
            <p>Ahora el formulario cuenta con protección reCAPTCHA para prevenir spam.</p>
        </div>
    </div>
</body>
</html>'''

        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # === PÁGINA CALCULADORA ===
    elif path == '/calculadora':
        resultado_suma = ""
        resultado_division = ""

        if method == 'POST':
            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                if content_length > 0:
                    post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                    params = parse_qs(post_data)

                    # SUMA
                    try:
                        suma1 = params.get('suma1', [''])[0]
                        suma2 = params.get('suma2', [''])[0]
                        if suma1 and suma2:
                            num1 = float(suma1)
                            num2 = float(suma2)
                            resultado_suma = f"<div class='resultado-exito'><strong>Resultado:</strong> {num1} + {num2} = {num1 + num2}</div>"
                        else:
                            resultado_suma = "<div class='resultado-error'>Ingresa ambos números para la suma</div>"
                    except ValueError:
                        resultado_suma = "<div class='resultado-error'>Error: Ingresa números válidos para la suma</div>"
                    except Exception as e:
                        resultado_suma = f"<div class='resultado-error'>Error en suma: {str(e)}</div>"

                    # DIVISIÓN
                    try:
                        div1 = params.get('div1', [''])[0]
                        div2 = params.get('div2', [''])[0]
                        if div1 and div2:
                            num3 = float(div1)
                            num4 = float(div2)
                            if num4 == 0:
                                resultado_division = "<div class='resultado-error'>Error: No se puede dividir entre cero</div>"
                            else:
                                resultado_division = f"<div class='resultado-exito'><strong>Resultado:</strong> {num3} ÷ {num4} = {num3 / num4:.2f}</div>"
                        else:
                            resultado_division = "<div class='resultado-error'>Ingresa ambos números para la división</div>"
                    except ValueError:
                        resultado_division = "<div class='resultado-error'>Error: Ingresa números válidos para la división</div>"
                    except Exception as e:
                        resultado_division = f"<div class='resultado-error'>Error en división: {str(e)}</div>"

            except Exception as e:
                resultado_suma = f"<div class='resultado-error'>Error general: {str(e)}</div>"

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Calculadora</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 40px; }}
        .calculadora-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }}
        .operacion {{ background: #f8f9fa; padding: 30px; border-radius: 8px; border-left: 4px solid; }}
        .suma {{ border-color: #28a745; }}
        .division {{ border-color: #dc3545; }}
        .operacion h2 {{ margin-top: 0; color: #333; text-align: center; }}
        .campo {{ margin: 15px 0; }}
        .campo label {{ display: block; margin-bottom: 8px; font-weight: bold; color: #555; }}
        input[type="text"] {{ width: 90%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
        .btn-calcular {{ padding: 12px 25px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; margin-top: 10px; }}
        .btn-calcular:hover {{ background: #0056b3; }}
        .resultado-exito {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 4px solid #28a745; }}
        .resultado-error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 4px solid #dc3545; }}
        @media (max-width: 768px) {{ .calculadora-grid {{ grid-template-columns: 1fr; gap: 20px; }} }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Calculadora</h1>

        <div class="calculadora-grid">
            <div class="operacion suma">
                <h2>Suma</h2>
                <form method="POST">
                    <div class="campo">
                        <label>Primer número:</label>
                        <input type="text" name="suma1" placeholder="Ej: 10" required>
                    </div>
                    <div class="campo">
                        <label>Segundo número:</label>
                        <input type="text" name="suma2" placeholder="Ej: 5" required>
                    </div>
                    <button type="submit" class="btn-calcular">Calcular Suma</button>
                </form>
                {resultado_suma if resultado_suma else ''}
            </div>

            <div class="operacion division">
                <h2>División</h2>
                <form method="POST">
                    <div class="campo">
                        <label>Dividendo:</label>
                        <input type="text" name="div1" placeholder="Ej: 10" required>
                    </div>
                    <div class="campo">
                        <label>Divisor:</label>
                        <input type="text" name="div2" placeholder="Ej: 2" required>
                    </div>
                    <button type="submit" class="btn-calcular">Calcular División</button>
                </form>
                {resultado_division if resultado_division else ''}
            </div>
        </div>
    </div>
</body>
</html>'''

        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # === BORRAR REGISTROS (sin cambios) ===
    elif path == '/borrar_registros':
        if method == 'POST':
            try:
                conn = conectar_bd()
                if conn:
                    cur = conn.cursor()
                    cur.execute('DELETE FROM formulario_simple')
                    conn.commit()
                    cur.close()
                    conn.close()
                    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Registros Borrados</title></head>
<body>{navegacion()}<h2>Todos los registros han sido borrados</h2><a href="/formulario">Volver</a></body></html>'''
                else:
                    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Error</title></head>
<body>{navegacion()}<h2>Error de conexión</h2><a href="/formulario">Volver</a></body></html>'''
                start_response('200 OK', headers)
                return [html.encode('utf-8')]
            except Exception as e:
                html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Error</title></head>
<body>{navegacion()}<h2>Error al borrar registros</h2><p>{str(e)}</p><a href="/formulario">Volver</a></body></html>'''
                start_response('200 OK', headers)
                return [html.encode('utf-8')]

        html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Borrar Registros</title></head>
<body>{navegacion()}<h2>¿Borrar TODOS los registros?</h2>
<form method="POST" action="/borrar_registros"><button type="submit">Sí, borrar</button></form>
<a href="/formulario">Cancelar</a></body></html>'''
        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # === FORMULARIO (NOMBRE SOLO LETRAS + FECHA NACIMIENTO) ===
    elif path == '/formulario':
        mensaje = ""

        if method == 'POST':
            try:
                fs = cgi.FieldStorage(
                    fp=environ['wsgi.input'],
                    environ=environ,
                    keep_blank_values=True
                )

                nombre = fs.getvalue('nombre', '').strip()
                fecha_nacimiento_str = fs.getvalue('fecha_nacimiento', '').strip()
                correo = fs.getvalue('correo', '').strip()
                correo_confirmar = fs.getvalue('correo_confirmar', '').strip()
                recaptcha_response = fs.getvalue('g-recaptcha-response', '').strip()

                imagen_file = fs['imagen']
                imagen_data = None
                imagen_nombre = ""
                imagen_tipo = ""

                if imagen_file.filename:
                    imagen_nombre = imagen_file.filename
                    imagen_data = imagen_file.file.read()
                    try:
                        imagen_tipo = imghdr.what(None, h=imagen_data)
                        if not imagen_tipo:
                            imagen_tipo = "desconocido"
                    except:
                        imagen_tipo = "desconocido"

                errores = []

                # NOMBRE: SOLO LETRAS
                if not nombre:
                    errores.append("Nombre es requerido")
                elif not validar_nombre_solo_letras(nombre):
                    errores.append("Nombre solo debe contener letras y espacios (sin números ni símbolos)")

                # FECHA NACIMIENTO
                fecha_nacimiento = None
                if not fecha_nacimiento_str:
                    errores.append("Fecha de nacimiento es requerida")
                else:
                    fecha_nacimiento = parsear_fecha_nacimiento(fecha_nacimiento_str)
                    if not fecha_nacimiento:
                        errores.append("Fecha de nacimiento no es válida")
                    else:
                        hoy = date.today()
                        if fecha_nacimiento > hoy:
                            errores.append("La fecha de nacimiento no puede ser futura")
                        else:
                            edad_calc = calcular_edad_desde_fecha(fecha_nacimiento)
                            if edad_calc < 0 or edad_calc > 120:
                                errores.append("La fecha de nacimiento no corresponde a una edad válida (0 a 120)")

                # CORREO
                if not correo:
                    errores.append("Correo es requerido")
                elif correo != correo_confirmar:
                    errores.append("Los correos no coinciden")

                # IMAGEN
                if not imagen_data:
                    errores.append("Debe subir una imagen")
                elif len(imagen_data) > 5 * 1024 * 1024:
                    errores.append("La imagen es demasiado grande (máximo 5MB)")
                elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                    errores.append("Solo se permiten imágenes JPG, PNG o GIF")

                # reCAPTCHA
                if not recaptcha_response:
                    errores.append("Por favor, completa el reCAPTCHA")
                else:
                    if not validar_recaptcha(recaptcha_response):
                        errores.append("El reCAPTCHA no es válido. Por favor, inténtalo de nuevo.")

                if errores:
                    mensaje = f'''<div class="error">
                        <h3>Errores encontrados:</h3>
                        <ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul>
                    </div>'''
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
                            # Por si ya existía tabla vieja:
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
                                <p style="margin-top: 10px; color: #28a745; font-size: 14px;">
                                    <strong>reCAPTCHA verificado correctamente</strong>
                                </p>
                            </div>'''
                        except Exception as e:
                            mensaje = f'<div class="error">Error al guardar en BD: {str(e)}</div>'
                    else:
                        mensaje = '<div class="error">Error de conexión a la base de datos</div>'

            except Exception as e:
                mensaje = f'<div class="error">Error procesando formulario: {str(e)}</div>'

        # Obtener registros
        registros_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, fecha_nacimiento, correo, imagen_nombre, imagen_tipo, fecha
                    FROM formulario_simple 
                    ORDER BY fecha DESC 
                    LIMIT 10
                """)
                registros = cur.fetchall()
                cur.close()
                conn.close()

                if registros:
                    registros_html = '''
                    <div class="registros">
                        <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom: 20px;">
                            <h3>Registros guardados:</h3>
                            <a href="/borrar_registros" style="background:#dc3545; color:white; padding:8px 15px; text-decoration:none; border-radius:5px; font-size:14px;">
                                Borrar todos los registros
                            </a>
                        </div>
                        <div class="lista-registros">
                    '''

                    for reg in registros:
                        id_reg, nombre_reg, fecha_nac_reg, correo_reg, img_nombre, img_tipo, fecha_registro = reg
                        fecha_str = str(fecha_registro)[:16]
                        fecha_nac_str = str(fecha_nac_reg) if fecha_nac_reg else ""
                        edad_reg = calcular_edad_desde_fecha(fecha_nac_reg) if fecha_nac_reg else ""

                        img_html = ""
                        conn2 = conectar_bd()
                        if conn2:
                            try:
                                cur2 = conn2.cursor()
                                cur2.execute("SELECT imagen_data FROM formulario_simple WHERE id = %s", (id_reg,))
                                img_data = cur2.fetchone()[0]
                                cur2.close()
                                conn2.close()
                                if img_data:
                                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                                    img_html = f'''<div class="imagen-preview">
                                        <img src="data:image/{img_tipo};base64,{img_base64}" 
                                             alt="{img_nombre}" 
                                             style="max-width:150px; max-height:150px; border-radius:5px;">
                                        <p><small>{img_nombre}</small></p>
                                    </div>'''
                            except:
                                img_html = '<p><small>Imagen no disponible</small></p>'

                        registros_html += f'''<div class="registro">
                            <div class="registro-info">
                                <h4>{nombre_reg}</h4>
                                <p><strong>Fecha de nacimiento:</strong> {fecha_nac_str}</p>
                                <p><strong>Edad:</strong> {str(edad_reg) + " años" if edad_reg != "" else "No disponible"}</p>
                                <p><strong>Correo:</strong> {correo_reg}</p>
                                <p><small>Registrado: {fecha_str}</small></p>
                            </div>
                            {img_html}
                        </div>'''

                    registros_html += '</div></div>'
                else:
                    registros_html = '<div class="sin-registros"><p>No hay registros aún. ¡Sé el primero en registrarte!</p></div>'

            except Exception as e:
                registros_html = f'<p class="error">Error cargando registros: {str(e)}</p>'
        else:
            registros_html = '<p class="error">No hay conexión a la base de datos</p>'

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario con Imágenes y reCAPTCHA</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-bottom: 30px; text-align: center; }}
        .campo {{ margin: 20px 0; }}
        label {{ display:block; margin-bottom: 8px; font-weight:bold; color:#555; }}
        input[type="text"], input[type="email"], input[type="date"], input[type="file"] {{
            width: 95%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px;
        }}
        .requerido {{ color:#dc3545; }}
        .info {{ font-size: 14px; color: #6c757d; margin-top: 5px; }}
        button[type="submit"] {{ padding: 12px 30px; background:#28a745; color:white; border:none; border-radius:5px; cursor:pointer; font-size:16px; margin-top:20px; width:100%; }}
        button[type="submit"]:hover {{ background:#218838; }}
        .exito {{ background:#d4edda; color:#155724; padding:20px; border-radius:5px; margin:20px 0; border-left:4px solid #28a745; }}
        .error {{ background:#f8d7da; color:#721c24; padding:20px; border-radius:5px; margin:20px 0; border-left:4px solid #dc3545; }}
        hr {{ margin:40px 0; border:none; border-top:2px solid #dee2e6; }}
        .registro {{ display:flex; justify-content:space-between; align-items:center; background:#f8f9fa; padding:20px; border-radius:8px; margin:15px 0; border-left:4px solid #007bff; }}
        .imagen-preview {{ text-align:center; margin-left:20px; }}
        .lista-registros {{ max-height:500px; overflow-y:auto; padding:10px; }}
        .form-group {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
        .sin-registros {{ text-align:center; padding:30px; background:#e9ecef; border-radius:8px; color:#6c757d; }}
        .recaptcha-info {{ background:#e7f3ff; padding:15px; border-radius:5px; margin:20px 0; border-left:4px solid #007bff; }}
        .recaptcha-container {{ margin:20px 0; padding:20px; background:#f8f9fa; border-radius:5px; text-align:center; }}
        .g-recaptcha {{ display:inline-block; }}
        .recaptcha-nota {{ font-size:12px; color:#6c757d; margin-top:10px; text-align:center; }}
        @media (max-width:768px) {{
            .form-group {{ grid-template-columns:1fr; }}
            .registro {{ flex-direction:column; text-align:center; }}
            .imagen-preview {{ margin-left:0; margin-top:15px; }}
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Formulario con Imágenes y reCAPTCHA</h1>

        <div class="recaptcha-info">
            <strong>Protección reCAPTCHA:</strong>
            <p>Debes completar el reCAPTCHA antes de enviar el formulario.</p>
        </div>

        {mensaje if mensaje else ''}

        <form method="POST" enctype="multipart/form-data" id="formulario">
            <div class="form-group">
                <div>
                    <div class="campo">
                        <label>Nombre completo <span class="requerido">*</span></label>

                        <!-- ✅ BLOQUEO EN FRONTEND: NO PERMITE NÚMEROS NI SÍMBOLOS -->
                        <input type="text"
                               name="nombre"
                               placeholder="Ej: Juan Pérez"
                               required
                               oninput="this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g, '')">

                        <div class="info">Solo letras y espacios</div>
                    </div>

                    <div class="campo">
                        <label>Fecha de nacimiento <span class="requerido">*</span></label>
                        <input type="date" name="fecha_nacimiento" required>
                        <div class="info">Selecciona tu fecha de nacimiento</div>
                    </div>
                </div>

                <div>
                    <div class="campo">
                        <label>Correo electrónico <span class="requerido">*</span></label>
                        <input type="email" name="correo" placeholder="Ej: usuario@correo.com" required>
                    </div>

                    <div class="campo">
                        <label>Confirmar correo <span class="requerido">*</span></label>
                        <input type="email" name="correo_confirmar" placeholder="Repite tu correo" required>
                    </div>
                </div>
            </div>

            <div class="campo">
                <label>Subir imagen <span class="requerido">*</span></label>
                <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
                <div class="info">Formatos aceptados: JPG, PNG, GIF (máximo 5MB)</div>
            </div>

            <div class="recaptcha-container">
                <div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}"></div>
                <div class="recaptcha-nota">
                    Este sitio está protegido por reCAPTCHA y se aplican la
                    <a href="https://policies.google.com/privacy" target="_blank">Política de privacidad</a> y
                    <a href="https://policies.google.com/terms" target="_blank">Términos de servicio</a> de Google.
                </div>
            </div>

            <button type="submit" id="btn-submit">Enviar Formulario</button>
        </form>

        <hr>

        {registros_html}
    </div>

    <script>
        document.getElementById('formulario').addEventListener('submit', function(e) {{
            const recaptchaResponse = grecaptcha.getResponse();
            if (recaptchaResponse.length === 0) {{
                e.preventDefault();
                alert('Por favor, completa el reCAPTCHA antes de enviar el formulario.');
                return false;
            }}
            const submitBtn = document.getElementById('btn-submit');
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Enviando...';
            return true;
        }});

        window.onload = function() {{
            const submitBtn = document.getElementById('btn-submit');
            if (submitBtn) {{
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Enviar Formulario';
            }}
        }};
    </script>
</body>
</html>'''

        start_response('200 OK', headers)
        return [html.encode('utf-8')]

    # === 404 ===
    else:
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>404 - Página no encontrada</title>
</head>
<body>
    {navegacion()}
    <h1>404</h1>
    <p>Página no encontrada: <code>{path}</code></p>
    <a href="/">Volver al Inicio</a>
</body>
</html>'''
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
