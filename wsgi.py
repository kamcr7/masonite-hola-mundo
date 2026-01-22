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
from datetime import datetime, date
import re

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Headers UTF-8
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # === CONFIGURACIÓN ===
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    
    # === CONFIGURACIÓN RECAPTCHA ===
    RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"  # Clave de prueba (funciona en localhost)
    RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"  # Secreto de prueba
    # Para producción, obtén tus propias claves en: https://www.google.com/recaptcha/admin
    
    # === NAVEGACIÓN ===
    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Formulario</a>
            <a href="/carrusel" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Carrusel</a>
            <a href="/pagina_error" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">Página Error</a>
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
    
    # === FUNCIÓN PARA CALCULAR EDAD DESDE FECHA DE NACIMIENTO ===
    def calcular_edad(fecha_nacimiento_str):
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            hoy = date.today()
            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            return edad
        except:
            return None
    
    # === FUNCIÓN PARA VALIDAR RECAPTCHA ===
    def validar_recaptcha(recaptcha_response):
        try:
            # URL de verificación de reCAPTCHA
            url = 'https://www.google.com/recaptcha/api/siteverify'
            
            # Datos a enviar
            data = urllib.parse.urlencode({
                'secret': RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response
            }).encode()
            
            # Crear request
            req = urllib.request.Request(url, data=data)
            
            # Enviar request y obtener respuesta
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode())
            
            # Retornar si es válido
            return result.get('success', False)
            
        except Exception as e:
            print(f"Error validando reCAPTCHA: {e}")
            return False
    
    # === FUNCIÓN PARA VALIDAR NOMBRE (solo letras y espacios) ===
    def validar_nombre(nombre):
        # Expresión regular que solo permite letras (incluyendo acentos) y espacios
        patron = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$')
        return bool(patron.match(nombre)) if nombre else False
    
    # === PÁGINA CARRUSEL (modificada para solo mostrar imágenes) ===
    if path == '/carrusel':
        mensaje = ""
        
        # Procesar POST (agregar nueva imagen al carrusel)
        if method == 'POST':
            try:
                # Parsear formulario multipart
                fs = cgi.FieldStorage(
                    fp=environ['wsgi.input'],
                    environ=environ,
                    keep_blank_values=True
                )
                
                # Verificar si es para eliminar
                eliminar_id = fs.getvalue('eliminar_id', '').strip()
                if eliminar_id:
                    # ELIMINAR IMAGEN
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
                    # AGREGAR NUEVA IMAGEN
                    titulo = fs.getvalue('titulo', '').strip()
                    descripcion = fs.getvalue('descripcion', '').strip()
                    
                    # Obtener archivo
                    imagen_file = fs['imagen']
                    imagen_data = None
                    imagen_nombre = ""
                    imagen_tipo = ""
                    
                    if imagen_file.filename:
                        imagen_nombre = imagen_file.filename
                        imagen_data = imagen_file.file.read()
                        # Determinar tipo de imagen
                        try:
                            imagen_tipo = imghdr.what(None, h=imagen_data)
                            if not imagen_tipo:
                                imagen_tipo = "desconocido"
                        except:
                            imagen_tipo = "desconocido"
                    
                    # Validaciones
                    errores = []
                    
                    if not titulo:
                        errores.append("Título es requerido")
                    
                    if not imagen_data:
                        errores.append("Debe subir una imagen")
                    elif len(imagen_data) > 5 * 1024 * 1024:  # 5MB máximo
                        errores.append("La imagen es demasiado grande (máximo 5MB)")
                    elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                        errores.append("Solo se permiten imágenes JPG, PNG o GIF")
                    
                    if errores:
                        mensaje = f'''<div class="error">
                            <h3>Errores encontrados:</h3>
                            <ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul>
                        </div>'''
                    else:
                        # Guardar en PostgreSQL
                        conn = conectar_bd()
                        if conn:
                            try:
                                cur = conn.cursor()
                                
                                # Crear tabla si no existe
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
                                
                                # Insertar datos
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
        
        # Obtener imágenes del carrusel
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
                    # Carrusel de imágenes
                    imagenes_html += '''
                    <div class="carrusel-container">
                        <h3>Carrusel de Imágenes</h3>
                        <div class="carrusel" id="carrusel">
                    '''
                    
                    for i, img in enumerate(imagenes):
                        id_img, titulo_img, desc_img, img_nombre, img_tipo, fecha = img
                        
                        # Obtener imagen en base64 para mostrar
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
                            # Determinar si es la primera imagen (activa)
                            activa = "active" if i == 0 else ""
                            
                            # MODIFICACIÓN: Solo mostrar la imagen, sin texto ni botón eliminar
                            imagenes_html += f'''
                            <div class="carrusel-item {activa}" data-id="{id_img}">
                                <div class="imagen-contenedor">
                                    <img src="data:image/{img_tipo};base64,{img_base64}" 
                                         alt="{titulo_img}"
                                         class="carrusel-imagen">
                                    <!-- Se removió la sección de información y el botón eliminar -->
                                </div>
                            </div>
                            '''
                    
                    imagenes_html += '''
                        </div>
                        
                        <!-- Controles del carrusel -->
                        <div class="carrusel-controls">
                            <button class="carrusel-btn prev" onclick="carruselPrev()">◀</button>
                            <div class="carrusel-indicators" id="indicators"></div>
                            <button class="carrusel-btn next" onclick="carruselNext()">▶</button>
                        </div>
                    </div>
                    '''
                    
                    # Contador de imágenes
                    imagenes_html += f'''
                    <div class="contador-imagenes">
                        <p>Total de imágenes en el carrusel: <strong>{len(imagenes)}</strong></p>
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
        
        # HTML del carrusel
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Carrusel de Imágenes</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 1000px; 
            margin: 40px auto; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #333; 
            text-align: center;
            margin-bottom: 40px;
        }}
        .carrusel-container {{
            margin: 40px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        .carrusel {{
            position: relative;
            overflow: hidden;
            border-radius: 10px;
            background: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .carrusel-item {{
            display: none;
            padding: 30px;
            text-align: center;
        }}
        .carrusel-item.active {{
            display: block;
        }}
        .imagen-contenedor {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
        }}
        @media (min-width: 768px) {{
            .imagen-contenedor {{
                flex-direction: row;
                align-items: center;
                justify-content: center;
            }}
        }}
        .carrusel-imagen {{
            max-width: 100%;
            max-height: 500px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .carrusel-controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding: 10px;
        }}
        .carrusel-btn {{
            background: #007bff;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .carrusel-btn:hover {{
            background: #0056b3;
        }}
        .carrusel-indicators {{
            display: flex;
            gap: 10px;
            justify-content: center;
            flex: 1;
        }}
        .indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ccc;
            cursor: pointer;
            transition: background 0.3s;
        }}
        .indicator.active {{
            background: #007bff;
        }}
        .contador-imagenes {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 5px;
        }}
        .sin-imagenes {{
            text-align: center;
            padding: 60px 20px;
            background: #e9ecef;
            border-radius: 10px;
            margin: 40px 0;
        }}
        .sin-imagenes-icon {{
            font-size: 60px;
            margin-bottom: 20px;
        }}
        .form-agregar {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin-top: 40px;
        }}
        .campo {{
            margin: 20px 0;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }}
        input[type="text"],
        textarea,
        input[type="file"],
        input[type="date"] {{
            width: 95%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }}
        textarea {{
            min-height: 100px;
            resize: vertical;
        }}
        .requerido {{ color: #dc3545; }}
        .info {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
        }}
        .btn-agregar {{
            padding: 15px 30px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            width: 100%;
            margin-top: 20px;
        }}
        .btn-agregar:hover {{
            background: #218838;
        }}
        .btn-eliminar {{
            padding: 8px 15px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn-eliminar:hover {{
            background: #c82333;
        }}
        .exito {{
            background: #d4edda;
            color: #155724;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        .error {{
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #dc3545;
        }}
        .instrucciones {{
            background: #fff3cd;
            color: #856404;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
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
                <li>Elimina imágenes haciendo click en "Eliminar"</li>
                <li>Cada imagen puede tener un título y descripción</li>
            </ul>
        </div>
        
        {mensaje if mensaje else ''}
        
        {imagenes_html}
        
        <div class="form-agregar">
            <h3>Agregar Nueva Imagen al Carrusel</h3>
            <form method="POST" enctype="multipart/form-data">
                <div class="campo">
                    <label>Título de la imagen <span class="requerido">*</span></label>
                    <input type="text" name="titulo" placeholder="Ej: Paisaje de montaña" required>
                    <div class="info">Un título descriptivo para la imagen</div>
                </div>
                
                <div class="campo">
                    <label>Descripción (opcional)</label>
                    <textarea name="descripcion" placeholder="Describe la imagen..."></textarea>
                    <div class="info">Información adicional sobre la imagen</div>
                </div>
                
                <div class="campo">
                    <label>Seleccionar imagen <span class="requerido">*</span></label>
                    <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
                    <div class="info">Formatos: JPG, PNG, GIF (máximo 5MB)</div>
                </div>
                
                <button type="submit" class="btn-agregar">Agregar al Carrusel</button>
            </form>
        </div>
    </div>
    
    <script>
        // Variables del carrusel
        let currentSlide = 0;
        const slides = document.querySelectorAll('.carrusel-item');
        const indicatorsContainer = document.getElementById('indicators');
        
        // Crear indicadores
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
        
        // Mostrar slide específico
        function showSlide(index) {{
            if (slides.length === 0) return;
            
            // Asegurar que el índice esté dentro de los límites
            if (index >= slides.length) {{
                currentSlide = 0;
            }} else if (index < 0) {{
                currentSlide = slides.length - 1;
            }} else {{
                currentSlide = index;
            }}
            
            // Ocultar todos los slides
            slides.forEach(slide => {{
                slide.classList.remove('active');
            }});
            
            // Mostrar slide actual
            slides[currentSlide].classList.add('active');
            
            // Actualizar indicadores
            const indicators = document.querySelectorAll('.indicator');
            indicators.forEach((indicator, i) => {{
                indicator.classList.toggle('active', i === currentSlide);
            }});
        }}
        
        // Slide siguiente
        function carruselNext() {{
            showSlide(currentSlide + 1);
        }}
        
        // Slide anterior
        function carruselPrev() {{
            showSlide(currentSlide - 1);
        }}
        
        // Ir a slide específico
        function goToSlide(index) {{
            showSlide(index);
        }}
        
        // Auto-avance del carrusel (cada 5 segundos)
        let carruselInterval;
        function iniciarAutoPlay() {{
            if (slides.length > 1) {{
                carruselInterval = setInterval(carruselNext, 5000);
            }}
        }}
        
        function detenerAutoPlay() {{
            if (carruselInterval) {{
                clearInterval(carruselInterval);
            }}
        }}
        
        // Inicializar carrusel
        document.addEventListener('DOMContentLoaded', function() {{
            crearIndicadores();
            iniciarAutoPlay();
            
            // Pausar auto-play cuando el mouse está sobre el carrusel
            const carrusel = document.getElementById('carrusel');
            if (carrusel) {{
                carrusel.addEventListener('mouseenter', detenerAutoPlay);
                carrusel.addEventListener('mouseleave', iniciarAutoPlay);
            }}
            
            // Navegación con teclado
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowLeft') {{
                    carruselPrev();
                }} else if (e.key === 'ArrowRight') {{
                    carruselNext();
                }}
            }});
        }});
        
        // Confirmar eliminación
        function confirmarEliminacion(id) {{
            return confirm('¿Estás seguro de que quieres eliminar esta imagen del carrusel?');
        }}
    </script>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA PRINCIPAL (actualizada) ===
    if path == '/' and method == 'GET':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inicio - Aplicación Masonite</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 40px auto; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #333; 
            text-align: center;
            margin-bottom: 30px;
        }}
        .features {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .feature {{
            background: #e9ecef;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .feature-icon {{
            font-size: 40px;
            margin-bottom: 15px;
        }}
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
            
            <div class="feature">
                <div class="feature-icon">!</div>
                <h3>Página Error</h3>
                <p>Página especial para probar el manejo de errores</p>
                <a href="/pagina_error">Ir a Página Error →</a>
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
    
    # === PÁGINA CALCULADORA (sin cambios) ===
    elif path == '/calculadora':
        resultado_suma = ""
        resultado_division = ""
        
        # Procesar formulario de calculadora
        if method == 'POST':
            try:
                # Obtener datos del formulario
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                if content_length > 0:
                    post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                    params = parse_qs(post_data)
                    
                    # PROCESAR SUMA
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
                    
                    # PROCESAR DIVISIÓN
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
        
        # HTML de la calculadora
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Calculadora</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 900px; 
            margin: 40px auto; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .container {{ 
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #333; 
            text-align: center;
            margin-bottom: 40px;
        }}
        .calculadora-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }}
        .operacion {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            border-left: 4px solid;
        }}
        .suma {{ border-color: #28a745; }}
        .division {{ border-color: #dc3545; }}
        .operacion h2 {{
            margin-top: 0;
            color: #333;
            text-align: center;
        }}
        .campo {{
            margin: 15px 0;
        }}
        .campo label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }}
        input[type="text"] {{
            width: 90%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }}
        .btn-calcular {{
            padding: 12px 25px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            margin-top: 10px;
        }}
        .btn-calcular:hover {{
            background: #0056b3;
        }}
        .resultado-exito {{
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            border-left: 4px solid #28a745;
        }}
        .resultado-error {{
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            border-left: 4px solid #dc3545;
        }}
        @media (max-width: 768px) {{
            .calculadora-grid {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Calculadora</h1>
        
        <div class="calculadora-grid">
            <!-- SUMA -->
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
            
            <!-- DIVISIÓN -->
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
        
        <div style="text-align: center; margin-top: 40px;">
            <p><strong>Nota:</strong> Cada operación se calcula por separado. Usa el botón correspondiente a cada operación.</p>
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
        
        # Si es GET, mostrar formulario de confirmación
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Borrar Registros</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 600px; 
            margin: 50px auto; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .advertencia {{
            background: #fff3cd;
            color: #856404;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
            border-left: 4px solid #ffc107;
        }}
        .advertencia-icon {{
            font-size: 40px;
            margin-bottom: 15px;
        }}
        .botones {{
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }}
        .btn-borrar {{
            background: #dc3545;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
        }}
        .btn-cancelar {{
            background: #6c757d;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
        }}
        .btn-borrar:hover {{ background: #c82333; }}
        .btn-cancelar:hover {{ background: #5a6268; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="advertencia">
            <div class="advertencia-icon">⚠</div>
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
    
    # === PÁGINA FORMULARIO CON MEJORAS ===
    elif path == '/formulario':
        mensaje = ""
        registro_exitoso = False
        datos_registro = {}
        
        # Procesar POST (formulario con archivos y reCAPTCHA)
        if method == 'POST':
            try:
                # Parsear formulario multipart
                fs = cgi.FieldStorage(
                    fp=environ['wsgi.input'],
                    environ=environ,
                    keep_blank_values=True
                )
                
                # Obtener campos
                nombre = fs.getvalue('nombre', '').strip()
                fecha_nacimiento = fs.getvalue('fecha_nacimiento', '').strip()
                correo = fs.getvalue('correo', '').strip()
                correo_confirmar = fs.getvalue('correo_confirmar', '').strip()
                recaptcha_response = fs.getvalue('g-recaptcha-response', '').strip()
                
                # Obtener archivo
                imagen_file = fs['imagen']
                imagen_data = None
                imagen_nombre = ""
                imagen_tipo = ""
                
                if imagen_file.filename:
                    imagen_nombre = imagen_file.filename
                    imagen_data = imagen_file.file.read()
                    # Determinar tipo de imagen
                    try:
                        imagen_tipo = imghdr.what(None, h=imagen_data)
                        if not imagen_tipo:
                            imagen_tipo = "desconocido"
                    except:
                        imagen_tipo = "desconocido"
                
                # Validaciones 
                errores = []
                
                if not nombre:
                    errores.append("Nombre es requerido")
                elif not validar_nombre(nombre):
                    errores.append("El nombre solo puede contener letras y espacios")
                
                if not fecha_nacimiento:
                    errores.append("Fecha de nacimiento es requerida")
                else:
                    edad = calcular_edad(fecha_nacimiento)
                    if edad is None:
                        errores.append("Fecha de nacimiento inválida")
                    elif edad < 1:
                        errores.append("La fecha de nacimiento debe ser anterior a la fecha actual")
                    elif edad > 120:
                        errores.append("La edad calculada no puede ser mayor a 120 años")
                
                if not correo:
                    errores.append("Correo es requerido")
                elif correo != correo_confirmar:
                    errores.append("Los correos no coinciden")
                
                if not imagen_data:
                    errores.append("Debe subir una imagen")
                elif len(imagen_data) > 5 * 1024 * 1024:  # 5MB máximo
                    errores.append("La imagen es demasiado grande (máximo 5MB)")
                elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                    errores.append("Solo se permiten imágenes JPG, PNG o GIF")
                
                # Validar reCAPTCHA
                if not recaptcha_response:
                    errores.append("Por favor, completa el reCAPTCHA")
                else:
                    if not validar_recaptcha(recaptcha_response):
                        errores.append("El reCAPTCHA no es válido. Por favor, inténtalo de nuevo.")
                
                if not errores:
                    # Calcular edad desde fecha de nacimiento
                    edad = calcular_edad(fecha_nacimiento)
                    
                    # Guardar en PostgreSQL
                    conn = conectar_bd()
                    if conn:
                        try:
                            cur = conn.cursor()
                            
                            # Crear tabla si no existe
                            cur.execute('''
                                CREATE TABLE IF NOT EXISTS formulario_simple (
                                    id SERIAL PRIMARY KEY,
                                    nombre VARCHAR(100),
                                    edad INTEGER,
                                    fecha_nacimiento DATE,
                                    correo VARCHAR(100),
                                    imagen_nombre VARCHAR(255),
                                    imagen_tipo VARCHAR(20),
                                    imagen_data BYTEA,
                                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            ''')
                            
                            # Insertar datos
                            cur.execute(
                                """INSERT INTO formulario_simple 
                                   (nombre, edad, fecha_nacimiento, correo, imagen_nombre, imagen_tipo, imagen_data) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                (nombre, edad, fecha_nacimiento, correo, imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                            )
                            
                            conn.commit()
                            cur.close()
                            conn.close()
                            
                            # Guardar datos para mostrar en mensaje
                            datos_registro = {
                                'nombre': nombre,
                                'fecha_nacimiento': fecha_nacimiento,
                                'edad': edad,
                                'correo': correo,
                                'imagen_nombre': imagen_nombre,
                                'imagen_tipo': imagen_tipo.upper()
                            }
                            
                            registro_exitoso = True
                            
                        except Exception as e:
                            mensaje = f'<div class="error">Error al guardar en BD: {str(e)}</div>'
                    else:
                        mensaje = '<div class="error">Error de conexión a la base de datos</div>'
                else:
                    # Mostrar errores si los hay
                    mensaje = f'''<div class="error">
                        <h3>Errores encontrados:</h3>
                        <ul>{"".join(f'<li>{e}</li>' for e in errores)}</ul>
                    </div>'''
                        
            except Exception as e:
                mensaje = f'<div class="error">Error procesando formulario: {str(e)}</div>'
        
        # Obtener registros anteriores
        registros_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, edad, fecha_nacimiento, correo, imagen_nombre, imagen_tipo, fecha 
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
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h3>📋 Registros guardados:</h3>
                            <a href="/borrar_registros" style="background: #dc3545; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 14px;">
                                🗑️ Borrar todos los registros
                            </a>
                        </div>
                        <div class="lista-registros">
                    '''
                    
                    for reg in registros:
                        id_reg, nombre_reg, edad_reg, fecha_nacimiento_reg, correo_reg, img_nombre, img_tipo, fecha = reg
                        fecha_str = str(fecha)[:16]
                        fecha_nacimiento_str = str(fecha_nacimiento_reg) if fecha_nacimiento_reg else "No registrada"
                        
                        # Obtener imagen en base64 para mostrar
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
                                             style="max-width: 150px; max-height: 150px; border-radius: 5px;">
                                        <p><small>{img_nombre}</small></p>
                                    </div>'''
                            except:
                                img_html = '<p><small>Imagen no disponible</small></p>'
                        
                        registros_html += f'''<div class="registro">
                            <div class="registro-info">
                                <h4>{nombre_reg}</h4>
                                <p><strong>Edad:</strong> {edad_reg} años</p>
                                <p><strong>Fecha de nacimiento:</strong> {fecha_nacimiento_str}</p>
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
        else:
            registros_html = '<p class="error">No hay conexión a la base de datos</p>'
        
        # Mostrar mensaje de éxito si se registró correctamente
        if registro_exitoso:
            mensaje = f'''<div class="exito">
                <h3>✅ ¡Registro exitoso!</h3>
                <p><strong>Nombre:</strong> {datos_registro['nombre']}</p>
                <p><strong>Fecha de nacimiento:</strong> {datos_registro['fecha_nacimiento']}</p>
                <p><strong>Edad calculada:</strong> {datos_registro['edad']} años</p>
                <p><strong>Correo:</strong> {datos_registro['correo']}</p>
                <p><strong>Imagen:</strong> {datos_registro['imagen_nombre']} ({datos_registro['imagen_tipo']})</p>
            </div>'''
        
        # HTML del formulario CON MEJORAS
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario con Imágenes y reCAPTCHA</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 900px; 
            margin: 40px auto; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #333; 
            margin-bottom: 30px;
            text-align: center;
        }}
        .campo {{
            margin: 20px 0;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }}
        input[type="text"],
        input[type="email"],
        input[type="date"],
        input[type="file"] {{
            width: 95%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            transition: border 0.3s;
        }}
        input.invalido {{
            border: 2px solid #dc3545;
            background-color: #fff8f8;
        }}
        input.valido {{
            border: 2px solid #28a745;
            background-color: #f8fff8;
        }}
        .requerido {{ color: #dc3545; }}
        .info {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
        }}
        button[type="submit"] {{
            padding: 12px 30px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
            width: 100%;
            transition: background 0.3s;
        }}
        button[type="submit"]:hover {{
            background: #218838;
        }}
        button[type="submit"]:disabled {{
            background: #6c757d;
            cursor: not-allowed;
        }}
        .exito {{
            background: #d4edda;
            color: #155724;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        .exito h3 {{
            margin-top: 0;
            color: #155724;
        }}
        .error {{
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #dc3545;
        }}
        .error-message {{
            color: #dc3545;
            font-size: 12px;
            margin-top: 5px;
            display: none;
        }}
        hr {{
            margin: 40px 0;
            border: none;
            border-top: 2px solid #dee2e6;
        }}
        .registros {{
            margin-top: 40px;
        }}
        .registro {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #007bff;
        }}
        .registro-info {{
            flex: 1;
        }}
        .imagen-preview {{
            text-align: center;
            margin-left: 20px;
        }}
        .lista-registros {{
            max-height: 500px;
            overflow-y: auto;
            padding: 10px;
        }}
        .form-group {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .sin-registros {{
            text-align: center;
            padding: 30px;
            background: #e9ecef;
            border-radius: 8px;
            color: #6c757d;
        }}
        .recaptcha-info {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }}
        .recaptcha-container {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            text-align: center;
        }}
        .g-recaptcha {{
            display: inline-block;
        }}
        .recaptcha-nota {{
            font-size: 12px;
            color: #6c757d;
            margin-top: 10px;
            text-align: center;
        }}
        @media (max-width: 768px) {{
            .form-group {{
                grid-template-columns: 1fr;
            }}
            .registro {{
                flex-direction: column;
                text-align: center;
            }}
            .imagen-preview {{
                margin-left: 0;
                margin-top: 15px;
            }}
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>Formulario con Imágenes y reCAPTCHA</h1>
        
        <div class="recaptcha-info">
            <strong>Protección reCAPTCHA:</strong>
            <p>Para prevenir spam y abusos, este formulario está protegido con Google reCAPTCHA.</p>
            <p>Debes completar el reCAPTCHA antes de enviar el formulario.</p>
        </div>
        
        {mensaje if mensaje else ''}
        
        <form method="POST" enctype="multipart/form-data" id="formulario" onsubmit="return validarFormulario()">
            <div class="form-group">
                <!-- Columna izquierda -->
                <div>
                    <!-- Nombre (solo letras) -->
                    <div class="campo">
                        <label>Nombre completo <span class="requerido">*</span></label>
                        <input type="text" name="nombre" id="nombre" placeholder="Ej: Juan Pérez" required
                               oninput="validarNombre(this)"
                               onblur="validarNombre(this)">
                        <div class="info">Solo letras y espacios (no se permiten números)</div>
                        <div class="error-message" id="error-nombre">El nombre solo puede contener letras y espacios</div>
                    </div>
                    
                    <!-- FECHA DE NACIMIENTO -->
                    <div class="campo">
                        <label>Fecha de nacimiento <span class="requerido">*</span></label>
                        <input type="date" name="fecha_nacimiento" id="fecha_nacimiento" required 
                               onchange="validarFecha(this)"
                               max="{date.today().strftime('%Y-%m-%d')}">
                        <div class="info">Selecciona tu fecha de nacimiento (se calculará tu edad automáticamente)</div>
                        <div class="error-message" id="error-fecha">Fecha de nacimiento inválida</div>
                    </div>
                </div>
                
                <!-- Columna derecha -->
                <div>
                    <!-- Correo -->
                    <div class="campo">
                        <label>Correo electrónico <span class="requerido">*</span></label>
                        <input type="email" name="correo" id="correo" placeholder="Ej: usuario@correo.com" required
                               oninput="validarCorreo(this)"
                               onblur="validarCorreo(this)">
                        <div class="info">Cualquier correo válido</div>
                        <div class="error-message" id="error-correo">Correo electrónico inválido</div>
                    </div>
                    
                    <!-- Confirmar Correo -->
                    <div class="campo">
                        <label>Confirmar correo <span class="requerido">*</span></label>
                        <input type="email" name="correo_confirmar" id="correo_confirmar" placeholder="Repite tu correo" required
                               oninput="validarConfirmacionCorreo(this)"
                               onblur="validarConfirmacionCorreo(this)">
                        <div class="info">Debe coincidir con el correo anterior</div>
                        <div class="error-message" id="error-correo-confirmar">Los correos no coinciden</div>
                    </div>
                </div>
            </div>
            
            <!-- Imagen -->
            <div class="campo">
                <label>Subir imagen <span class="requerido">*</span></label>
                <input type="file" name="imagen" id="imagen" accept="image/jpeg,image/png,image/gif" required
                       onchange="validarImagen(this)">
                <div class="info">Formatos aceptados: JPG, PNG, GIF (máximo 5MB)</div>
                <div class="error-message" id="error-imagen">Imagen inválida o muy grande (máximo 5MB)</div>
            </div>
            
            <!-- reCAPTCHA -->
            <div class="recaptcha-container">
                <div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}"></div>
                <div class="recaptcha-nota">
                    Este sitio está protegido por reCAPTCHA y se aplican la 
                    <a href="https://policies.google.com/privacy" target="_blank">Política de privacidad</a> y 
                    <a href="https://policies.google.com/terms" target="_blank">Términos de servicio</a> de Google.
                </div>
                <div class="error-message" id="error-recaptcha">Por favor, completa el reCAPTCHA</div>
            </div>
            
            <!-- Botón -->
            <button type="submit" id="btn-submit">Enviar Formulario</button>
        </form>
        
        <hr>
        
        {registros_html}
    </div>
    
    <script>
        // Expresión regular para validar nombre (solo letras y espacios)
        const nombreRegex = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$/;
        
        // Función para validar nombre
        function validarNombre(input) {{
            const valor = input.value.trim();
            const errorElement = document.getElementById('error-nombre');
            
            if (valor === '') {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else if (!nombreRegex.test(valor)) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else {{
                input.classList.remove('invalido');
                input.classList.add('valido');
                errorElement.style.display = 'none';
                return true;
            }}
        }}
        
        // Función para validar fecha
        function validarFecha(input) {{
            const valor = input.value;
            const errorElement = document.getElementById('error-fecha');
            const hoy = new Date();
            const fechaSeleccionada = new Date(valor);
            
            if (!valor) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else if (fechaSeleccionada > hoy) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else {{
                // Calcular edad
                const diffMs = hoy - fechaSeleccionada;
                const edad = Math.floor(diffMs / (1000 * 60 * 60 * 24 * 365.25));
                
                if (edad < 1 || edad > 120) {{
                    input.classList.remove('valido');
                    input.classList.add('invalido');
                    errorElement.style.display = 'block';
                    return false;
                }} else {{
                    input.classList.remove('invalido');
                    input.classList.add('valido');
                    errorElement.style.display = 'none';
                    return true;
                }}
            }}
        }}
        
        // Función para validar correo
        function validarCorreo(input) {{
            const valor = input.value.trim();
            const errorElement = document.getElementById('error-correo');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (!valor) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else if (!emailRegex.test(valor)) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else {{
                input.classList.remove('invalido');
                input.classList.add('valido');
                errorElement.style.display = 'none';
                
                // Validar también la confirmación
                const confirmacion = document.getElementById('correo_confirmar');
                if (confirmacion.value) {{
                    validarConfirmacionCorreo(confirmacion);
                }}
                
                return true;
            }}
        }}
        
        // Función para validar confirmación de correo
        function validarConfirmacionCorreo(input) {{
            const valor = input.value.trim();
            const correoOriginal = document.getElementById('correo').value.trim();
            const errorElement = document.getElementById('error-correo-confirmar');
            
            if (!valor) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else if (valor !== correoOriginal) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else {{
                input.classList.remove('invalido');
                input.classList.add('valido');
                errorElement.style.display = 'none';
                return true;
            }}
        }}
        
        // Función para validar imagen
        function validarImagen(input) {{
            const errorElement = document.getElementById('error-imagen');
            
            if (!input.files || input.files.length === 0) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }}
            
            const archivo = input.files[0];
            const tiposPermitidos = ['image/jpeg', 'image/png', 'image/gif'];
            const tamanoMaximo = 5 * 1024 * 1024; // 5MB
            
            if (!tiposPermitidos.includes(archivo.type)) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else if (archivo.size > tamanoMaximo) {{
                input.classList.remove('valido');
                input.classList.add('invalido');
                errorElement.style.display = 'block';
                return false;
            }} else {{
                input.classList.remove('invalido');
                input.classList.add('valido');
                errorElement.style.display = 'none';
                return true;
            }}
        }}
        
        // Función para validar reCAPTCHA
        function validarRecaptcha() {{
            const recaptchaResponse = grecaptcha.getResponse();
            const errorElement = document.getElementById('error-recaptcha');
            
            if (!recaptchaResponse) {{
                errorElement.style.display = 'block';
                return false;
            }} else {{
                errorElement.style.display = 'none';
                return true;
            }}
        }}
        
        // Función para validar todo el formulario
        function validarFormulario() {{
            // Validar todos los campos
            const nombreValido = validarNombre(document.getElementById('nombre'));
            const fechaValida = validarFecha(document.getElementById('fecha_nacimiento'));
            const correoValido = validarCorreo(document.getElementById('correo'));
            const correoConfirmValido = validarConfirmacionCorreo(document.getElementById('correo_confirmar'));
            const imagenValida = validarImagen(document.getElementById('imagen'));
            const recaptchaValido = validarRecaptcha();
            
            // Verificar si todos son válidos
            const formularioValido = nombreValido && fechaValida && correoValido && correoConfirmValido && imagenValida && recaptchaValido;
            
            if (!formularioValido) {{
                // Deshabilitar envío si hay errores
                const submitBtn = document.getElementById('btn-submit');
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'Corrige los errores';
                
                // Re-habilitar después de 2 segundos
                setTimeout(() => {{
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Enviar Formulario';
                }}, 2000);
                
                return false;
            }}
            
            // Si todo está válido, proceder con el envío
            const submitBtn = document.getElementById('btn-submit');
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Enviando...';
            
            return true;
        }}
        
        // Inicializar cuando carga la página
        window.onload = function() {{
            // Establecer fecha máxima como hoy
            const fechaInput = document.getElementById('fecha_nacimiento');
            const today = new Date().toISOString().split('T')[0];
            fechaInput.setAttribute('max', today);
            
            // Configurar reCAPTCHA
            if (typeof grecaptcha !== 'undefined') {{
                grecaptcha.ready(function() {{
                    // Validar reCAPTCHA cuando cambia
                    const recaptchaElement = document.querySelector('.g-recaptcha');
                    if (recaptchaElement) {{
                        const observer = new MutationObserver(function() {{
                            validarRecaptcha();
                        }});
                        
                        observer.observe(recaptchaElement, {{ 
                            attributes: true, 
                            attributeFilter: ['data-sitekey', 'data-callback', 'data-expired-callback'] 
                        }});
                    }}
                }});
            }}
            
            // Validar todos los campos al cargar si tienen valores
            const campos = ['nombre', 'fecha_nacimiento', 'correo', 'correo_confirmar', 'imagen'];
            campos.forEach(campoId => {{
                const campo = document.getElementById(campoId);
                if (campo && campo.value) {{
                    if (campoId === 'nombre') validarNombre(campo);
                    else if (campoId === 'fecha_nacimiento') validarFecha(campo);
                    else if (campoId === 'correo') validarCorreo(campo);
                    else if (campoId === 'correo_confirmar') validarConfirmacionCorreo(campo);
                    else if (campoId === 'imagen') validarImagen(campo);
                }}
            }});
        }};
        
        // Prevenir que se escriban números en el campo nombre
        document.getElementById('nombre')?.addEventListener('keypress', function(e) {{
            // Solo permitir letras, espacios y teclas de control
            const charCode = e.charCode;
            const charStr = String.fromCharCode(charCode);
            
            // Permitir teclas de control (backspace, delete, tab, etc.)
            if (charCode === 0 || charCode === 8 || charCode === 9 || charCode === 13) {{
                return;
            }}
            
            // Permitir espacios
            if (charCode === 32) {{
                return;
            }}
            
            // Solo permitir letras (incluyendo mayúsculas y minúsculas)
            if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñÜü]$/.test(charStr)) {{
                e.preventDefault();
            }}
        }});
        
        // Limpiar el formulario después de un envío exitoso (si hay mensaje de éxito)
        document.addEventListener('DOMContentLoaded', function() {{
            const mensajeExito = document.querySelector('.exito');
            if (mensajeExito) {{
                // Limpiar formulario después de 5 segundos
                setTimeout(() => {{
                    document.getElementById('formulario').reset();
                    
                    // Limpiar clases de validación
                    const campos = document.querySelectorAll('input, textarea');
                    campos.forEach(campo => {{
                        campo.classList.remove('valido', 'invalido');
                    }});
                    
                    // Ocultar mensajes de error
                    const mensajesError = document.querySelectorAll('.error-message');
                    mensajesError.forEach(mensaje => {{
                        mensaje.style.display = 'none';
                    }});
                    
                    // Resetear reCAPTCHA
                    if (typeof grecaptcha !== 'undefined' && grecaptcha.reset) {{
                        grecaptcha.reset();
                    }}
                }}, 5000);
            }}
        }});
    </script>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA ESPECIAL DE ERROR (nueva página) ===
    elif path == '/pagina_error':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Página de Error - Aplicación Masonite</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 1000px; 
            margin: 40px auto; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #dc3545; 
            text-align: center;
            margin-bottom: 40px;
            font-size: 36px;
        }}
        .error-header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .error-icon {{
            font-size: 80px;
            color: #dc3545;
            margin-bottom: 20px;
        }}
        .error-content {{
            background: #f8d7da;
            border-radius: 10px;
            padding: 30px;
            margin: 30px 0;
            border-left: 5px solid #dc3545;
        }}
        .error-content h3 {{
            color: #721c24;
            margin-top: 0;
        }}
        .error-list {{
            background: #f5c6cb;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .test-section {{
            background: #e7f3ff;
            padding: 30px;
            border-radius: 10px;
            margin: 40px 0;
            border-left: 5px solid #007bff;
        }}
        .test-buttons {{
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 20px;
        }}
        .btn-test {{
            padding: 12px 25px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
            display: inline-block;
        }}
        .btn-test:hover {{
            background: #0056b3;
        }}
        .btn-danger {{
            background: #dc3545;
        }}
        .btn-danger:hover {{
            background: #c82333;
        }}
        .instructions {{
            background: #fff3cd;
            padding: 25px;
            border-radius: 8px;
            margin: 30px 0;
            border-left: 4px solid #ffc107;
        }}
        .instructions h3 {{
            color: #856404;
            margin-top: 0;
        }}
        .status-codes {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }}
        .status-code {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .status-code h4 {{
            margin: 0;
            color: #333;
        }}
        .code-404 {{ border-left: 4px solid #dc3545; }}
        .code-500 {{ border-left: 4px solid #fd7e14; }}
        .code-403 {{ border-left: 4px solid #ffc107; }}
        .code-200 {{ border-left: 4px solid #28a745; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="error-header">
            <div class="error-icon">!</div>
            <h1>Página de Manejo de Errores</h1>
            <p>Esta es una página especial para probar el manejo de errores en la aplicación</p>
        </div>
        
        <div class="instructions">
            <h3>¿Qué es esta página?</h3>
            <p>Esta página está diseñada específicamente para probar el manejo de errores en la aplicación. 
            Aquí puedes simular diferentes tipos de errores y ver cómo responde el sistema.</p>
        </div>
        
        <div class="error-content">
            <h3>Tipos de Errores Comunes</h3>
            <p>En cualquier aplicación web, pueden ocurrir diferentes tipos de errores:</p>
            
            <div class="status-codes">
                <div class="status-code code-404">
                    <h4>404 - No Encontrado</h4>
                    <p>La página solicitada no existe</p>
                </div>
                <div class="status-code code-500">
                    <h4>500 - Error Interno</h4>
                    <p>Error en el servidor</p>
                </div>
                <div class="status-code code-403">
                    <h4>403 - Prohibido</h4>
                    <p>Acceso no autorizado</p>
                </div>
                <div class="status-code code-200">
                    <h4>200 - Éxito</h4>
                    <p>Solicitud completada</p>
                </div>
            </div>
        </div>
        
        <div class="test-section">
            <h3>Pruebas de Error</h3>
            <p>Haz clic en los botones de abajo para probar diferentes escenarios:</p>
            
            <div class="test-buttons">
                <a href="/ruta_inexistente" class="btn-test btn-danger">Probar Error 404</a>
                <button onclick="simularError500()" class="btn-test">Simular Error 500</button>
                <button onclick="mostrarAlerta()" class="btn-test">Mostrar Alerta</button>
                <a href="/" class="btn-test">Volver al Inicio</a>
            </div>
        </div>
        
        <div class="error-content">
            <h3>¿Cómo funciona el manejo de errores?</h3>
            <p>Esta aplicación utiliza un sistema de manejo de errores que:</p>
            <ul>
                <li><strong>Detecta rutas no existentes</strong> y muestra una página 404 personalizada</li>
                <li><strong>Registra errores en la consola</strong> para diagnóstico</li>
                <li><strong>Protege al usuario</strong> de ver mensajes de error técnicos</li>
                <li><strong>Mantiene la navegación</strong> incluso cuando ocurren errores</li>
            </ul>
        </div>
        
        <div class="instructions">
            <h3>Consejos para Usuarios</h3>
            <ul>
                <li>Si encuentras un error 404, verifica que la URL sea correcta</li>
                <li>Los errores 500 son problemas del servidor - contacta al administrador</li>
                <li>Siempre puedes usar la navegación superior para volver a páginas funcionales</li>
                <li>Esta página de pruebas es segura y no afecta el funcionamiento normal</li>
            </ul>
        </div>
    </div>
    
    <script>
        function simularError500() {{
            // Esto simula un error 500 pero en realidad no lo provoca
            alert('En un escenario real, esto provocaría un error 500 del servidor.\\n\\nEn esta página de prueba, solo mostramos esta alerta para simular el comportamiento.');
        }}
        
        function mostrarAlerta() {{
            alert('Esta es una alerta de prueba.\\n\\nLas alertas JavaScript son diferentes de los errores HTTP y se manejan en el cliente.');
        }}
        
        // Configurar fecha máxima en formularios de fecha si existen
        window.onload = function() {{
            const fechaInputs = document.querySelectorAll('input[type="date"]');
            const today = new Date().toISOString().split('T')[0];
            fechaInputs.forEach(input => {{
                if (!input.max) {{
                    input.setAttribute('max', today);
                }}
            }});
        }};
    </script>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA 404 (para rutas no existentes) ===
    else:
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>404 - Página no encontrada</title>
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
        h1 {{ 
            color: #dc3545; 
            font-size: 48px;
            margin-bottom: 20px;
        }}
        h2 {{
            color: #333;
            margin-bottom: 30px;
        }}
        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 5px;
            margin: 30px 0;
            border-left: 4px solid #dc3545;
            text-align: left;
        }}
        .btn-volver {{
            display: inline-block;
            padding: 15px 30px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            margin-top: 20px;
            transition: background 0.3s;
        }}
        .btn-volver:hover {{
            background: #0056b3;
        }}
        .btn-error-page {{
            display: inline-block;
            padding: 15px 30px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            margin-top: 20px;
            margin-left: 15px;
            transition: background 0.3s;
        }}
        .btn-error-page:hover {{
            background: #218838;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>404</h1>
        <h2>Página no encontrada</h2>
        
        <div class="error-message">
            <p><strong>Lo sentimos, la página que buscas no existe.</strong></p>
            <p>La ruta solicitada <code>{path}</code> no se encuentra en este servidor.</p>
            <p>Posibles causas:</p>
            <ul>
                <li>La URL puede estar mal escrita</li>
                <li>La página ha sido movida o eliminada</li>
                <li>Has seguido un enlace incorrecto</li>
            </ul>
        </div>
        
        <p>Puedes regresar a la página de inicio o visitar nuestra página especial de manejo de errores.</p>
        
        <div>
            <a href="/" class="btn-volver">Volver al Inicio</a>
            <a href="/pagina_error" class="btn-error-page">Ir a Página de Errores</a>
        </div>
    </div>
</body>
</html>'''
        
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
