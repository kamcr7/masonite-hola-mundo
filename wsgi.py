# -*- coding: utf-8 -*-
import os
import psycopg2
import base64
import imghdr
import urllib.parse
from urllib.parse import urlparse, parse_qs
import cgi
from datetime import datetime
import re

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    
    # === NAVEGACIÓN ===
    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Formulario</a>
            <a href="/carrusel" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Carrusel</a>
            <a href="/pagina_error" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Página Error</a>
        </nav>'''
    
    # === FUNCIONES ===
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
    
    def validar_nombre(nombre):
        patron = r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s\'-]+$'
        return bool(re.match(patron, nombre)) and len(nombre) >= 2
    
    def calcular_edad(fecha_nacimiento_str):
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d')
            hoy = datetime.now()
            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            return edad
        except:
            return None
    
    # === CARRUSEL ===
    if path == '/carrusel':
        mensaje = ""
        
        if method == 'POST':
            try:
                fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)
                
                eliminar_id = fs.getvalue('eliminar_id', '').strip()
                if eliminar_id:
                    conn = conectar_bd()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM carrusel_imagenes WHERE id = %s", (eliminar_id,))
                            conn.commit()
                            mensaje = '''<div class="exito"><h3>Imagen eliminada</h3><p>La imagen ha sido eliminada del carrusel.</p></div>'''
                        except:
                            mensaje = '<div class="error">Error al eliminar</div>'
                        finally:
                            if conn: conn.close()
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
                            imagen_tipo = imghdr.what(None, h=imagen_data) or "desconocido"
                        except:
                            imagen_tipo = "desconocido"
                    
                    errores = []
                    if not titulo: errores.append("Título es requerido")
                    if not imagen_data: errores.append("Debe subir una imagen")
                    elif len(imagen_data) > 5 * 1024 * 1024: errores.append("La imagen es demasiado grande (máximo 5MB)")
                    elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']: errores.append("Solo se permiten imágenes JPG, PNG o GIF")
                    
                    if errores:
                        mensaje = f'''<div class="error"><h3>Errores encontrados:</h3><ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul></div>'''
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
                                    """INSERT INTO carrusel_imagenes (titulo, descripcion, imagen_nombre, imagen_tipo, imagen_data) 
                                       VALUES (%s, %s, %s, %s, %s)""",
                                    (titulo, descripcion, imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                                )
                                conn.commit()
                                mensaje = f'''<div class="exito"><h3>¡Imagen agregada al carrusel!</h3><p><strong>Título:</strong> {titulo}</p><p><strong>Imagen:</strong> {imagen_nombre} ({imagen_tipo.upper()})</p></div>'''
                            except Exception as e:
                                mensaje = f'<div class="error">Error al guardar: {str(e)}</div>'
                            finally:
                                if conn: conn.close()
                        else:
                            mensaje = '<div class="error">Error de conexión a la base de datos</div>'
                        
            except Exception as e:
                mensaje = f'<div class="error">Error procesando formulario: {str(e)}</div>'
        
        imagenes_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, titulo, descripcion, imagen_nombre, imagen_tipo, fecha FROM carrusel_imagenes ORDER BY fecha DESC")
                imagenes = cur.fetchall()
                
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
                                if img_data:
                                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                            except:
                                pass
                            finally:
                                if conn2: conn2.close()
                        
                        if img_base64:
                            activa = "active" if i == 0 else ""
                            imagenes_html += f'''
                            <div class="carrusel-item {activa}" data-id="{id_img}">
                                <div class="imagen-contenedor">
                                    <img src="data:image/{img_tipo};base64,{img_base64}" alt="{titulo_img}" class="carrusel-imagen">
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
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="/pagina_error" class="btn-error-404">Ir a Página de Error de Prueba</a>
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
            finally:
                if conn: conn.close()
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
        .carrusel-imagen {{ max-width: 100%; max-height: 500px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        .carrusel-controls {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; padding: 10px; }}
        .carrusel-btn {{ background: #007bff; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; font-size: 20px; cursor: pointer; }}
        .carrusel-btn:hover {{ background: #0056b3; }}
        .carrusel-indicators {{ display: flex; gap: 10px; justify-content: center; flex: 1; }}
        .indicator {{ width: 12px; height: 12px; border-radius: 50%; background: #ccc; cursor: pointer; }}
        .indicator.active {{ background: #007bff; }}
        .contador-imagenes {{ text-align: center; margin: 20px 0; padding: 15px; background: #e7f3ff; border-radius: 5px; }}
        .btn-error-404 {{ display: inline-block; padding: 15px 30px; background: #ffc107; color: #212529; border-radius: 5px; font-size: 16px; font-weight: bold; text-decoration: none; }}
        .btn-error-404:hover {{ background: #e0a800; }}
        .sin-imagenes {{ text-align: center; padding: 60px 20px; background: #e9ecef; border-radius: 10px; margin: 40px 0; }}
        .form-agregar {{ background: #f8f9fa; padding: 30px; border-radius: 10px; margin-top: 40px; }}
        .campo {{ margin: 20px 0; }}
        label {{ display: block; margin-bottom: 8px; font-weight: bold; color: #555; }}
        input, textarea {{ width: 95%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
        textarea {{ min-height: 100px; resize: vertical; }}
        .btn-agregar {{ padding: 15px 30px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 18px; width: 100%; margin-top: 20px; }}
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
        <div class="instrucciones">
            <h3>Instrucciones:</h3>
            <ul>
                <li>Agrega imágenes usando el formulario de abajo</li>
                <li>Navega entre imágenes usando los botones ◀ ▶</li>
                <li>Prueba el botón "Ir a Página de Error" para ver una página de prueba</li>
            </ul>
        </div>
        {mensaje if mensaje else ''}
        {imagenes_html}
        <div class="form-agregar">
            <h3>Agregar Nueva Imagen al Carrusel</h3>
            <form method="POST" enctype="multipart/form-data">
                <div class="campo">
                    <label>Título de la imagen *</label>
                    <input type="text" name="titulo" placeholder="Ej: Paisaje de montaña" required>
                </div>
                <div class="campo">
                    <label>Descripción (opcional)</label>
                    <textarea name="descripcion" placeholder="Describe la imagen..."></textarea>
                </div>
                <div class="campo">
                    <label>Seleccionar imagen *</label>
                    <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
                    <div style="font-size: 14px; color: #6c757d; margin-top: 5px;">Formatos: JPG, PNG, GIF (máximo 5MB)</div>
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
            if (index >= slides.length) {{ currentSlide = 0; }}
            else if (index < 0) {{ currentSlide = slides.length - 1; }}
            else {{ currentSlide = index; }}
            
            slides.forEach(slide => slide.classList.remove('active'));
            slides[currentSlide].classList.add('active');
            
            const indicators = document.querySelectorAll('.indicator');
            indicators.forEach((indicator, i) => indicator.classList.toggle('active', i === currentSlide));
        }}
        
        function carruselNext() {{ showSlide(currentSlide + 1); }}
        function carruselPrev() {{ showSlide(currentSlide - 1); }}
        function goToSlide(index) {{ showSlide(index); }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            crearIndicadores();
            let carruselInterval;
            if (slides.length > 1) {{
                carruselInterval = setInterval(carruselNext, 5000);
                const carrusel = document.getElementById('carrusel');
                if (carrusel) {{
                    carrusel.addEventListener('mouseenter', () => clearInterval(carruselInterval));
                    carrusel.addEventListener('mouseleave', () => carruselInterval = setInterval(carruselNext, 5000));
                }}
            }}
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowLeft') carruselPrev();
                else if (e.key === 'ArrowRight') carruselNext();
            }});
        }});
    </script>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === INICIO ===
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
        .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
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
                <h3>Formulario</h3>
                <p>Registra datos con validación de nombre y fecha</p>
                <a href="/formulario">Ir a Formulario →</a>
            </div>
            <div class="feature">
                <div class="feature-icon">▢</div>
                <h3>Carrusel</h3>
                <p>Galería interactiva de imágenes</p>
                <a href="/carrusel">Ir a Carrusel →</a>
            </div>
            <div class="feature">
                <div class="feature-icon">⚠</div>
                <h3>Página Error</h3>
                <p>Página de prueba con mensaje</p>
                <a href="/pagina_error">Ir a Página Error →</a>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === CALCULADORA ===
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
                        if suma1 and suma2:
                            num1 = float(suma1)
                            num2 = float(suma2)
                            resultado_suma = f"<div class='resultado-exito'><strong>Resultado:</strong> {num1} + {num2} = {num1 + num2}</div>"
                        else:
                            resultado_suma = "<div class='resultado-error'>Ingresa ambos números para la suma</div>"
                    except ValueError:
                        resultado_suma = "<div class='resultado-error'>Error: Ingresa números válidos para la suma</div>"
                    
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
        label {{ display: block; margin-bottom: 8px; font-weight: bold; color: #555; }}
        input[type="text"] {{ width: 90%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
        .btn-calcular {{ padding: 12px 25px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }}
        .resultado-exito {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        .resultado-error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        @media (max-width: 768px) {{ .calculadora-grid {{ grid-template-columns: 1fr; }} }}
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
                    <div class="campo"><label>Primer número:</label><input type="text" name="suma1" placeholder="Ej: 10" required></div>
                    <div class="campo"><label>Segundo número:</label><input type="text" name="suma2" placeholder="Ej: 5" required></div>
                    <button type="submit" class="btn-calcular">Calcular Suma</button>
                </form>
                {resultado_suma if resultado_suma else ''}
            </div>
            <div class="operacion division">
                <h2>División</h2>
                <form method="POST">
                    <div class="campo"><label>Dividendo:</label><input type="text" name="div1" placeholder="Ej: 10" required></div>
                    <div class="campo"><label>Divisor:</label><input type="text" name="div2" placeholder="Ej: 2" required></div>
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
    
    # === BORRAR REGISTROS ===
    elif path == '/borrar_registros':
        if method == 'POST':
            try:
                conn = conectar_bd()
                if conn:
                    cur = conn.cursor()
                    cur.execute('DELETE FROM formulario_simple')
                    conn.commit()
                    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Registros Borrados</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; text-align: center; }}
        .exito {{ color: #28a745; font-size: 24px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="exito">Todos los registros han sido borrados</div>
        <p>Se han eliminado todos los registros de la base de datos.</p>
        <a href="/formulario" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px;">Volver al formulario</a>
    </div>
</body>
</html>'''
                else:
                    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; text-align: center; }}
        .error {{ color: #dc3545; font-size: 24px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="error">Error de conexión</div>
        <p>No se pudo conectar a la base de datos.</p>
        <a href="/formulario" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px;">Volver al formulario</a>
    </div>
</body>
</html>'''
                
                start_response('200 OK', headers)
                return [html.encode('utf-8')]
                
            except Exception as e:
                html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; text-align: center; }}
        .error {{ color: #dc3545; font-size: 24px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="error">Error al borrar registros</div>
        <p>Error: {str(e)}</p>
        <a href="/formulario" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px;">Volver al formulario</a>
    </div>
</body>
</html>'''
                
                start_response('200 OK', headers)
                return [html.encode('utf-8')]
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Borrar Registros</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .advertencia {{ background: #fff3cd; color: #856404; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
        .botones {{ display: flex; gap: 15px; justify-content: center; margin-top: 30px; }}
        .btn-borrar {{ background: #dc3545; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
        .btn-cancelar {{ background: #6c757d; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; text-decoration: none; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="advertencia">
            <h2>¡Advertencia!</h2>
            <p>Estás a punto de borrar <strong>TODOS</strong> los registros de la base de datos.</p>
            <p>Esta acción <strong>NO se puede deshacer</strong>.</p>
        </div>
        <form method="POST" action="/borrar_registros">
            <div class="botones">
                <button type="submit" class="btn-borrar">Sí, borrar todos los registros</button>
                <a href="/formulario" class="btn-cancelar">Cancelar y volver</a>
            </div>
        </form>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === FORMULARIO (MODIFICADO) ===
    elif path == '/formulario':
        mensaje = ""
        
        if method == 'POST':
            try:
                fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, keep_blank_values=True)
                
                nombre = fs.getvalue('nombre', '').strip()
                fecha_nacimiento = fs.getvalue('fecha_nacimiento', '').strip()
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
                if not nombre: errores.append("Nombre es requerido")
                elif not validar_nombre(nombre): errores.append("El nombre solo puede contener letras, espacios y algunos caracteres especiales")
                
                if not fecha_nacimiento: errores.append("Fecha de nacimiento es requerida")
                else:
                    edad = calcular_edad(fecha_nacimiento)
                    if edad is None: errores.append("Fecha de nacimiento no válida")
                    elif edad < 1: errores.append("La fecha de nacimiento debe ser válida (edad mínima: 1 año)")
                    elif edad > 120: errores.append("La fecha de nacimiento debe ser válida (edad máxima: 120 años)")
                
                if not correo: errores.append("Correo es requerido")
                elif correo != correo_confirmar: errores.append("Los correos no coinciden")
                
                if not imagen_data: errores.append("Debe subir una imagen")
                elif len(imagen_data) > 5 * 1024 * 1024: errores.append("La imagen es demasiado grande (máximo 5MB)")
                elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']: errores.append("Solo se permiten imágenes JPG, PNG o GIF")
                
                if errores:
                    mensaje = f'''<div class="error"><h3>Errores encontrados:</h3><ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul></div>'''
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
                                    edad INTEGER,
                                    correo VARCHAR(100),
                                    imagen_nombre VARCHAR(255),
                                    imagen_tipo VARCHAR(20),
                                    imagen_data BYTEA,
                                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            ''')
                            cur.execute(
                                """INSERT INTO formulario_simple (nombre, fecha_nacimiento, edad, correo, imagen_nombre, imagen_tipo, imagen_data) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                (nombre, fecha_nacimiento, edad, correo, imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                            )
                            conn.commit()
                            mensaje = f'''<div class="exito">
                                <h3>¡Registro exitoso!</h3>
                                <p><strong>Nombre:</strong> {nombre}</p>
                                <p><strong>Fecha de Nacimiento:</strong> {fecha_nacimiento}</p>
                                <p><strong>Edad calculada:</strong> {edad} años</p>
                                <p><strong>Correo:</strong> {correo}</p>
                                <p><strong>Imagen:</strong> {imagen_nombre} ({imagen_tipo.upper()})</p>
                            </div>'''
                        except Exception as e:
                            mensaje = f'<div class="error">Error al guardar en BD: {str(e)}</div>'
                        finally:
                            if conn: conn.close()
                    else:
                        mensaje = '<div class="error">Error de conexión a la base de datos</div>'
                        
            except Exception as e:
                mensaje = f'<div class="error">Error procesando formulario: {str(e)}</div>'
        
        registros_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, nombre, fecha_nacimiento, edad, correo, imagen_nombre, imagen_tipo, fecha FROM formulario_simple ORDER BY fecha DESC LIMIT 10")
                registros = cur.fetchall()
                
                if registros:
                    registros_html = '''
                    <div class="registros">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h3>Registros guardados:</h3>
                            <a href="/borrar_registros" style="background: #dc3545; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 14px;">
                                Borrar todos los registros
                            </a>
                        </div>
                        <div class="lista-registros">
                    '''
                    
                    for reg in registros:
                        id_reg, nombre_reg, fecha_nacimiento_reg, edad_reg, correo_reg, img_nombre, img_tipo, fecha = reg
                        fecha_str = str(fecha)[:16]
                        fecha_nacimiento_str = str(fecha_nacimiento_reg)
                        
                        img_html = ""
                        conn2 = conectar_bd()
                        if conn2:
                            try:
                                cur2 = conn2.cursor()
                                cur2.execute("SELECT imagen_data FROM formulario_simple WHERE id = %s", (id_reg,))
                                img_data = cur2.fetchone()[0]
                                if img_data:
                                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                                    img_html = f'''<div class="imagen-preview">
                                        <img src="data:image/{img_tipo};base64,{img_base64}" style="max-width: 150px; max-height: 150px; border-radius: 5px;">
                                        <p><small>{img_nombre}</small></p>
                                    </div>'''
                            except:
                                img_html = '<p><small>Imagen no disponible</small></p>'
                            finally:
                                if conn2: conn2.close()
                        
                        registros_html += f'''<div class="registro">
                            <div class="registro-info">
                                <h4>{nombre_reg}</h4>
                                <p><strong>Fecha Nacimiento:</strong> {fecha_nacimiento_str}</p>
                                <p><strong>Edad:</strong> {edad_reg} años</p>
                                <p><strong>Correo:</strong> {correo_reg}</p>
                                <p><small>Registrado: {fecha_str}</small></p>
                            </div>
                            {img_html}
                        </div>'''
                    
                    registros_html += '</div></div>'
                else:
                    registros_html = '''
                    <div class="sin-registros">
                        <p>No hay registros aún. ¡Sé el primero en registrarte!</p>
                    </div>
                    '''
                    
            except Exception as e:
                registros_html = f'<p class="error">Error cargando registros: {str(e)}</p>'
            finally:
                if conn: conn.close()
        else:
            registros_html = '<p class="error">No hay conexión a la base de datos</p>'
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario con Imágenes</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-bottom: 30px; text-align: center; }}
        .campo {{ margin: 20px 0; }}
        label {{ display: block; margin-bottom: 8px; font-weight: bold; color: #555; }}
        input, textarea {{ width: 95%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
        button[type="submit"] {{ padding: 12px 30px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }}
        button[type="submit"]:hover {{ background: #218838; }}
        .exito {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        hr {{ margin: 40px 0; border-top: 2px solid #dee2e6; }}
        .registro {{ display: flex; justify-content: space-between; align-items: center; background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 15px 0; }}
        .registro-info {{ flex: 1; }}
        .form-group {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 768px) {{ .form-group {{ grid-template-columns: 1fr; }} .registro {{ flex-direction: column; }} }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Formulario con Imágenes</h1>
        {mensaje if mensaje else ''}
        <form method="POST" enctype="multipart/form-data" id="formulario">
            <div class="form-group">
                <div>
                    <div class="campo">
                        <label>Nombre completo *</label>
                        <input type="text" name="nombre" id="nombre" placeholder="Ej: Juan Pérez" required oninput="validarNombre(this)">
                        <div style="font-size: 14px; color: #6c757d; margin-top: 5px;">Solo letras, espacios y algunos caracteres especiales</div>
                        <div id="nombre-error" style="color: #dc3545; font-size: 14px; display: none;"></div>
                    </div>
                    <div class="campo">
                        <label>Fecha de Nacimiento *</label>
                        <input type="date" name="fecha_nacimiento" id="fecha_nacimiento" required>
                        <div style="font-size: 14px; color: #6c757d; margin-top: 5px;">Se calculará tu edad automáticamente</div>
                    </div>
                </div>
                <div>
                    <div class="campo">
                        <label>Correo electrónico *</label>
                        <input type="email" name="correo" placeholder="Ej: usuario@correo.com" required>
                    </div>
                    <div class="campo">
                        <label>Confirmar correo *</label>
                        <input type="email" name="correo_confirmar" placeholder="Repite tu correo" required>
                    </div>
                </div>
            </div>
            <div class="campo">
                <label>Subir imagen *</label>
                <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
                <div style="font-size: 14px; color: #6c757d; margin-top: 5px;">Formatos: JPG, PNG, GIF (máximo 5MB)</div>
            </div>
            <button type="submit" id="btn-submit">Enviar Formulario</button>
        </form>
        <hr>
        {registros_html}
    </div>
    <script>
        function validarNombre(input) {{
            const nombre = input.value;
            const errorDiv = document.getElementById('nombre-error');
            const patron = /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s\\'-]+$/;
            
            if (nombre.length > 0 && !patron.test(nombre)) {{
                errorDiv.textContent = 'Solo letras, espacios y algunos caracteres especiales.';
                errorDiv.style.display = 'block';
                input.style.borderColor = '#dc3545';
            }} else {{
                errorDiv.style.display = 'none';
                input.style.borderColor = '#ddd';
            }}
        }}
        
        document.getElementById('formulario').addEventListener('submit', function(e) {{
            const nombre = document.getElementById('nombre').value;
            const fechaNacimiento = document.getElementById('fecha_nacimiento').value;
            let errores = [];
            
            const patron = /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s\\'-]+$/;
            if (!patron.test(nombre)) {{
                errores.push('El nombre solo puede contener letras, espacios y algunos caracteres especiales.');
            }}
            
            if (!fechaNacimiento) {{
                errores.push('La fecha de nacimiento es requerida.');
            }} else {{
                const fechaNac = new Date(fechaNacimiento);
                const hoy = new Date();
                let edad = hoy.getFullYear() - fechaNac.getFullYear();
                const mes = hoy.getMonth() - fechaNac.getMonth();
                if (mes < 0 || (mes === 0 && hoy.getDate() < fechaNac.getDate())) edad--;
                if (edad < 1) errores.push('Edad mínima: 1 año.');
                else if (edad > 120) errores.push('Edad máxima: 120 años.');
            }}
            
            if (errores.length > 0) {{
                e.preventDefault();
                alert('Errores:\\n\\n' + errores.join('\\n'));
                return false;
            }}
            
            document.getElementById('btn-submit').disabled = true;
            document.getElementById('btn-submit').innerHTML = 'Enviando...';
            return true;
        }});
        
        window.onload = function() {{
            const fechaInput = document.getElementById('fecha_nacimiento');
            if (fechaInput) {{
                const hoy = new Date();
                fechaInput.max = hoy.toISOString().split('T')[0];
            }}
        }};
    </script>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA DE ERROR DE PRUEBA ===
    elif path == '/pagina_error':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Página de Error de Prueba</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; margin-bottom: 40px; }}
        .mensaje-error {{ background: #fff3cd; color: #856404; padding: 30px; border-radius: 10px; margin: 30px 0; text-align: center; }}
        .contenido {{ background: #e9ecef; padding: 30px; border-radius: 10px; margin: 30px 0; }}
        .btn-volver {{ display: inline-block; padding: 15px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }}
        .btn-volver:hover {{ background: #0056b3; }}
        .botones-container {{ text-align: center; margin-top: 40px; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Página de Error de Prueba</h1>
        <div class="mensaje-error">
            <h2>⚠ Esta es una página de prueba para errores</h2>
            <p>Esta página está diseñada para simular y probar el manejo de errores en la aplicación.</p>
            <p><strong>Nota:</strong> Este no es un error real, es solo una página de demostración.</p>
        </div>
        <div class="contenido">
            <h3>Propósito de esta página:</h3>
            <p>Esta página sirve para probar el manejo de rutas en la aplicación y demostrar el diseño de páginas.</p>
            <p>El formulario ahora tiene validación para que el nombre solo acepte letras y el campo de edad se cambió a fecha de nacimiento.</p>
        </div>
        <div class="botones-container">
            <a href="/" class="btn-volver">Volver al Inicio</a>
            <a href="/formulario" class="btn-volver">Ir al Formulario</a>
            <a href="/carrusel" class="btn-volver">Ir al Carrusel</a>
            <a href="/calculadora" class="btn-volver">Ir a la Calculadora</a>
        </div>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA 404 REAL ===
    else:
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>404 - Página no encontrada</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 100px auto; padding: 40px; background: #f8f9fa; }}
        .container {{ background: white; padding: 60px; border-radius: 10px; box-shadow: 0 2px 20px rgba(0,0,0,0.1); text-align: center; }}
        h1 {{ color: #dc3545; font-size: 48px; margin-bottom: 20px; }}
        .error-message {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; margin: 30px 0; }}
        .btn-volver {{ display: inline-block; padding: 15px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>404</h1>
        <h2>Página no encontrada - Error Real</h2>
        <div class="error-message">
            <p><strong>¡Error real!</strong> La página que buscas no existe en el servidor.</p>
            <p>La ruta solicitada <code>{path}</code> no se encuentra.</p>
            <p>Si querías ver la página de prueba, ve a <a href="/pagina_error">/pagina_error</a></p>
        </div>
        <a href="/" class="btn-volver">Volver al Inicio</a>
    </div>
</body>
</html>'''
        
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
