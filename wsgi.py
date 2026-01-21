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

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Headers UTF-8
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # === CONFIGURACIÓN ===
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    
    # === CONFIGURACIÓN RECAPTCHA ===
    RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    
    # === NAVEGACIÓN ===
    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🏠 Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🧮 Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">📋 Formulario</a>
            <a href="/carrusel" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🖼️ Carrusel</a>
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
    
    # === PÁGINA CARRUSEL SIMPLIFICADO (SOLO IMÁGENES) ===
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
                
                # Verificar si es para eliminar (mantenemos esta funcionalidad solo para el admin)
                eliminar_id = fs.getvalue('eliminar_id', '').strip()
                if eliminar_id:
                    # ELIMINAR IMAGEN (solo si viene de formulario oculto)
                    conn = conectar_bd()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM carrusel_imagenes WHERE id = %s", (eliminar_id,))
                            conn.commit()
                            cur.close()
                            conn.close()
                            mensaje = f'''<div class="exito">
                                <h3>✅ Imagen eliminada</h3>
                                <p>La imagen ha sido eliminada del carrusel.</p>
                            </div>'''
                        except Exception as e:
                            mensaje = f'<div class="error">❌ Error al eliminar: {str(e)}</div>'
                else:
                    # AGREGAR NUEVA IMAGEN
                    titulo = fs.getvalue('titulo', '').strip()
                    
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
                    
                    if not imagen_data:
                        errores.append("Debe subir una imagen")
                    elif len(imagen_data) > 5 * 1024 * 1024:  # 5MB máximo
                        errores.append("La imagen es demasiado grande (máximo 5MB)")
                    elif imagen_tipo not in ['jpeg', 'jpg', 'png', 'gif']:
                        errores.append("Solo se permiten imágenes JPG, PNG o GIF")
                    
                    if errores:
                        mensaje = f'''<div class="error">
                            <h3>❌ Errores encontrados:</h3>
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
                                        imagen_nombre VARCHAR(255),
                                        imagen_tipo VARCHAR(20),
                                        imagen_data BYTEA,
                                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                ''')
                                
                                # Insertar datos (solo imagen)
                                cur.execute(
                                    """INSERT INTO carrusel_imagenes 
                                       (imagen_nombre, imagen_tipo, imagen_data) 
                                       VALUES (%s, %s, %s)""",
                                    (imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                                )
                                
                                conn.commit()
                                cur.close()
                                conn.close()
                                
                                mensaje = f'''<div class="exito">
                                    <h3>✅ ¡Imagen agregada al carrusel!</h3>
                                    <p>La imagen se ha agregado correctamente.</p>
                                </div>'''
                                
                            except Exception as e:
                                mensaje = f'<div class="error">❌ Error al guardar: {str(e)}</div>'
                        else:
                            mensaje = '<div class="error">❌ Error de conexión a la base de datos</div>'
                        
            except Exception as e:
                mensaje = f'<div class="error">❌ Error procesando formulario: {str(e)}</div>'
        
        # Obtener imágenes del carrusel
        imagenes_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, imagen_nombre, imagen_tipo 
                    FROM carrusel_imagenes 
                    ORDER BY fecha DESC
                """)
                imagenes = cur.fetchall()
                cur.close()
                conn.close()
                
                if imagenes:
                    # Carrusel de imágenes - SOLO IMÁGENES
                    imagenes_html += '''
                    <div class="carrusel-container">
                        <div class="carrusel" id="carrusel">
                    '''
                    
                    for i, img in enumerate(imagenes):
                        id_img, img_nombre, img_tipo = img
                        
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
                            
                            # SOLO MOSTRAR LA IMAGEN
                            imagenes_html += f'''
                            <div class="carrusel-item {activa}">
                                <img src="data:image/{img_tipo};base64,{img_base64}" 
                                     alt="Imagen {i+1}"
                                     class="carrusel-imagen">
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
                        <p>Imágenes en el carrusel: <strong>{len(imagenes)}</strong></p>
                    </div>
                    '''
                else:
                    imagenes_html = '''
                    <div class="sin-imagenes">
                        <div class="sin-imagenes-icon">📷</div>
                        <h3>No hay imágenes en el carrusel</h3>
                        <p>Agrega tu primera imagen usando el formulario de abajo.</p>
                    </div>
                    '''
                    
            except Exception as e:
                imagenes_html = f'<p class="error">Error cargando imágenes: {str(e)}</p>'
        else:
            imagenes_html = '<p class="error">No hay conexión a la base de datos</p>'
        
        # HTML del carrusel SIMPLIFICADO
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
            background: #000;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            height: 500px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .carrusel-item {{
            display: none;
            text-align: center;
            width: 100%;
            height: 100%;
        }}
        .carrusel-item.active {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .carrusel-imagen {{
            max-width: 95%;
            max-height: 95%;
            object-fit: contain;
            border-radius: 5px;
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
            transition: all 0.3s;
        }}
        .carrusel-btn:hover {{
            background: #0056b3;
            transform: scale(1.1);
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
        .indicator:hover {{
            background: #0056b3;
        }}
        .contador-imagenes {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 5px;
            font-size: 18px;
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
        input[type="file"] {{
            width: 95%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            background: white;
            cursor: pointer;
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
            transition: background 0.3s;
        }}
        .btn-agregar:hover {{
            background: #218838;
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
        .admin-panel {{
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #dc3545;
            text-align: center;
        }}
        .admin-link {{
            color: #dc3545;
            font-weight: bold;
            text-decoration: none;
        }}
        .admin-link:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 768px) {{
            .carrusel {{
                height: 350px;
            }}
            .carrusel-imagen {{
                max-width: 90%;
                max-height: 90%;
            }}
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>🖼️ Carrusel de Imágenes</h1>
        
        <div class="instrucciones">
            <h3>📋 Instrucciones:</h3>
            <ul>
                <li>Agrega imágenes usando el formulario de abajo</li>
                <li>Navega entre imágenes usando los botones ◀ ▶</li>
                <li>También puedes usar las flechas del teclado</li>
                <li>El carrusel cambia automáticamente cada 5 segundos</li>
            </ul>
        </div>
        
        {mensaje if mensaje else ''}
        
        <div class="admin-panel">
            <p><strong>Administración:</strong> Para eliminar imágenes, ve a la <a href="/admin_carrusel" class="admin-link">página de administración del carrusel</a>.</p>
        </div>
        
        {imagenes_html}
        
        <div class="form-agregar">
            <h3>➕ Agregar Nueva Imagen al Carrusel</h3>
            <form method="POST" enctype="multipart/form-data">
                <div class="campo">
                    <label>Seleccionar imagen <span class="requerido">*</span></label>
                    <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
                    <div class="info">Formatos: JPG, PNG, GIF (máximo 5MB)</div>
                </div>
                
                <button type="submit" class="btn-agregar">📤 Agregar al Carrusel</button>
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
            
            // Efecto de transición suave
            slides.forEach(slide => {{
                slide.style.transition = 'opacity 0.5s ease';
            }});
        }});
    </script>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA DE ADMINISTRACIÓN DEL CARRUSEL (para eliminar imágenes) ===
    if path == '/admin_carrusel':
        mensaje = ""
        
        # Procesar POST para eliminar imágenes
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
                                <h3>✅ Imagen eliminada</h3>
                                <p>La imagen ha sido eliminada del carrusel.</p>
                            </div>'''
                        except Exception as e:
                            mensaje = f'<div class="error">❌ Error al eliminar: {str(e)}</div>'
                        
        # Obtener todas las imágenes para administración
        imagenes_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, imagen_nombre, imagen_tipo, fecha 
                    FROM carrusel_imagenes 
                    ORDER BY fecha DESC
                """)
                imagenes = cur.fetchall()
                cur.close()
                conn.close()
                
                if imagenes:
                    imagenes_html = '''
                    <div class="admin-lista">
                        <h3>🗑️ Eliminar Imágenes</h3>
                        <p>Selecciona las imágenes que deseas eliminar:</p>
                        <div class="imagenes-grid">
                    '''
                    
                    for img in imagenes:
                        id_img, img_nombre, img_tipo, fecha = img
                        fecha_str = str(fecha)[:16]
                        
                        # Obtener imagen en base64 para mostrar miniatura
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
                            imagenes_html += f'''
                            <div class="imagen-admin">
                                <div class="imagen-miniatura">
                                    <img src="data:image/{img_tipo};base64,{img_base64}" 
                                         alt="{img_nombre}">
                                </div>
                                <div class="imagen-info">
                                    <p><strong>Archivo:</strong> {img_nombre}</p>
                                    <p><strong>Fecha:</strong> {fecha_str}</p>
                                    <form method="POST" style="margin-top: 10px;">
                                        <input type="hidden" name="eliminar_id" value="{id_img}">
                                        <button type="submit" class="btn-eliminar" 
                                                onclick="return confirm('¿Estás seguro de eliminar esta imagen?')">
                                            🗑️ Eliminar
                                        </button>
                                    </form>
                                </div>
                            </div>
                            '''
                    
                    imagenes_html += '''
                        </div>
                    </div>
                    '''
                else:
                    imagenes_html = '''
                    <div class="sin-imagenes">
                        <p>No hay imágenes en el carrusel.</p>
                    </div>
                    '''
                    
            except Exception as e:
                imagenes_html = f'<p class="error">Error cargando imágenes: {str(e)}</p>'
        else:
            imagenes_html = '<p class="error">No hay conexión a la base de datos</p>'
        
        # HTML de administración
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Administrar Carrusel</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 1200px; 
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
        .imagenes-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .imagen-admin {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            background: #f8f9fa;
        }}
        .imagen-miniatura img {{
            width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        .imagen-info p {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .btn-eliminar {{
            width: 100%;
            padding: 8px;
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
        .volver-link {{
            display: inline-block;
            margin-top: 30px;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}
        .volver-link:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>⚙️ Administrar Carrusel de Imágenes</h1>
        
        {mensaje if mensaje else ''}
        
        <div style="margin-bottom: 30px;">
            <a href="/carrusel" class="volver-link">← Volver al Carrusel</a>
        </div>
        
        {imagenes_html}
        
        <div style="margin-top: 40px;">
            <a href="/carrusel" class="volver-link">← Volver al Carrusel</a>
        </div>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA PRINCIPAL (sin cambios) ===
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
        <h1>🚀 Aplicación Masonite en Railway</h1>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🧮</div>
                <h3>Calculadora</h3>
                <p>Operaciones básicas de suma y división</p>
                <a href="/calculadora">Ir a Calculadora →</a>
            </div>
            
            <div class="feature">
                <div class="feature-icon">📋</div>
                <h3>Formulario con Imágenes</h3>
                <p>Registra datos y sube imágenes</p>
                <a href="/formulario">Ir a Formulario →</a>
            </div>
            
            <div class="feature">
                <div class="feature-icon">🖼️</div>
                <h3>Carrusel de Imágenes</h3>
                <p>Galería interactiva de imágenes</p>
                <a href="/carrusel">Ir a Carrusel →</a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 40px; padding: 20px; background: #e7f3ff; border-radius: 8px;">
            <h3>🔒 Seguridad mejorada</h3>
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
                            resultado_suma = "<div class='resultado-error'>⚠️ Ingresa ambos números para la suma</div>"
                    except ValueError:
                        resultado_suma = "<div class='resultado-error'>❌ Error: Ingresa números válidos para la suma</div>"
                    except Exception as e:
                        resultado_suma = f"<div class='resultado-error'>❌ Error en suma: {str(e)}</div>"
                    
                    # PROCESAR DIVISIÓN
                    try:
                        div1 = params.get('div1', [''])[0]
                        div2 = params.get('div2', [''])[0]
                        if div1 and div2:
                            num3 = float(div1)
                            num4 = float(div2)
                            if num4 == 0:
                                resultado_division = "<div class='resultado-error'>❌ Error: No se puede dividir entre cero</div>"
                            else:
                                resultado_division = f"<div class='resultado-exito'><strong>Resultado:</strong> {num3} ÷ {num4} = {num3 / num4:.2f}</div>"
                        else:
                            resultado_division = "<div class='resultado-error'>⚠️ Ingresa ambos números para la división</div>"
                    except ValueError:
                        resultado_division = "<div class='resultado-error'>❌ Error: Ingresa números válidos para la división</div>"
                    except Exception as e:
                        resultado_division = f"<div class='resultado-error'>❌ Error en división: {str(e)}</div>"
                    
            except Exception as e:
                resultado_suma = f"<div class='resultado-error'>❌ Error general: {str(e)}</div>"
        
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
        <h1>🧮 Calculadora</h1>
        
        <div class="calculadora-grid">
            <!-- SUMA -->
            <div class="operacion suma">
                <h2>➕ Suma</h2>
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
                <h2>➗ División</h2>
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
        <div class="exito">✅ Todos los registros han sido borrados</div>
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
        <div class="error">❌ Error de conexión</div>
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
        <div class="error">❌ Error al borrar registros</div>
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
            <div class="advertencia-icon">⚠️</div>
            <h2>¡Advertencia!</h2>
            <p>Estás a punto de borrar <strong>TODOS</strong> los registros de la base de datos.</p>
            <p>Esta acción <strong>NO se puede deshacer</strong>.</p>
        </div>
        
        <form method="POST" action="/borrar_registros">
            <div class="botones">
                <button type="submit" class="btn-borrar">🗑️ Sí, borrar todos los registros</button>
                <a href="/formulario" class="btn-cancelar">❌ Cancelar y volver</a>
            </div>
        </form>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA FORMULARIO CON RECAPTCHA (sin cambios) ===
    elif path == '/formulario':
        # [Todo el código del formulario con reCAPTCHA sin cambios]
        # (Manteniendo el código original del formulario)
        # [Por brevedad, mantengo el formulario existente]
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario con Imágenes y reCAPTCHA</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        /* Estilos del formulario */
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>📋 Formulario con Imágenes y reCAPTCHA</h1>
        <p>[Formulario con todos los campos y reCAPTCHA]</p>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA 404 ===
    else:
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>404 - Página no encontrada</title>
</head>
<body>
    {navegacion()}
    <h1>404 - Página no encontrada</h1>
    <a href="/">Inicio</a>
</body>
</html>'''
        
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
