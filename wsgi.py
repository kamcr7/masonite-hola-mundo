# -*- coding: utf-8 -*-
import os
import psycopg2
import re
import base64
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # === CONFIGURACIÓN ===
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    
    # === CONEXIÓN BD ===
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
        except Exception as e:
            print(f"Error BD: {e}")
            return None
    
    # === RUTAS PARA IMÁGENES ===
    if path.startswith('/imagen/'):
        try:
            conn = conectar_bd()
            if not conn:
                start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
                return [b'Error de conexion a la base de datos']
            
            cur = conn.cursor()
            imagen_id = path.split('/')[-1]
            cur.execute('SELECT imagen_nombre, imagen_data FROM formulario_registros WHERE id = %s', (imagen_id,))
            resultado = cur.fetchone()
            cur.close()
            conn.close()
            
            if resultado and resultado[1]:
                nombre_imagen, datos_imagen = resultado
                extension = nombre_imagen.split('.')[-1].lower() if '.' in nombre_imagen else 'jpg'
                
                content_type = 'image/jpeg'
                if extension == 'png':
                    content_type = 'image/png'
                elif extension == 'gif':
                    content_type = 'image/gif'
                elif extension == 'bmp':
                    content_type = 'image/bmp'
                elif extension == 'webp':
                    content_type = 'image/webp'
                
                headers = [
                    ('Content-Type', content_type),
                    ('Content-Length', str(len(datos_imagen))),
                    ('Cache-Control', 'max-age=3600')
                ]
                start_response('200 OK', headers)
                return [datos_imagen]
            else:
                start_response('404 Not Found', [('Content-Type', 'text/plain')])
                return [b'Imagen no encontrada']
                
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [b'Error al cargar la imagen']
    
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # === NAVEGACIÓN ===
    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🏠 Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🧮 Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">📋 Formulario</a>
        </nav>'''
    
    # === PÁGINA DE ERROR ===
    def mostrar_error(mensaje):
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error</title>
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
        .error-icon {{ font-size: 70px; text-align: center; margin: 20px 0; color: #dc3545; }}
        h1 {{ color: #dc3545; text-align: center; margin-bottom: 20px; }}
        .boton {{ 
            display: inline-block; padding: 10px 20px; margin: 0 10px; 
            background: #007bff; color: white; text-decoration: none; border-radius: 5px;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="error-icon">⚠️</div>
        <h1>Error en el formulario</h1>
        <p style="text-align: center; font-size: 18px; color: #6c757d;">{mensaje}</p>
        <div style="text-align: center; margin-top: 30px;">
            <a href="/formulario" class="boton">Volver al formulario</a>
        </div>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA FORMULARIO ===
    if path == '/formulario':
        mensaje_exito = ""
        nombre_guardado = ""
        edad_guardada = ""
        correo_guardado = ""
        
        if method == 'POST':
            try:
                # Obtener el tipo de contenido
                content_type = environ.get('CONTENT_TYPE', '')
                
                if 'multipart/form-data' in content_type:
                    # Leer datos multipart
                    import cgi
                    form = cgi.FieldStorage(
                        fp=environ['wsgi.input'],
                        environ=environ,
                        keep_blank_values=True
                    )
                    
                    # Obtener campos del formulario
                    nombre = form.getvalue('nombre', '').strip()
                    edad = form.getvalue('edad', '').strip()
                    correo = form.getvalue('correo', '').strip()
                    correo_confirmar = form.getvalue('correo_confirmar', '').strip()
                    
                    # Obtener archivo de imagen
                    imagen_file = form['imagen']
                    imagen_data = None
                    imagen_filename = ""
                    
                    if imagen_file.filename:
                        imagen_filename = imagen_file.filename
                        # Leer imagen como bytes
                        imagen_data = imagen_file.file.read()
                        if len(imagen_data) > 5 * 1024 * 1024:  # 5MB límite
                            return mostrar_error("La imagen es demasiado grande (máximo 5MB)")
                    
                    # Validaciones básicas
                    if not nombre:
                        return mostrar_error("El nombre es requerido")
                    
                    if not edad:
                        return mostrar_error("La edad es requerida")
                    elif not edad.isdigit():
                        return mostrar_error("La edad debe ser un número")
                    elif int(edad) < 1 or int(edad) > 120:
                        return mostrar_error("La edad debe estar entre 1 y 120 años")
                    
                    if not correo:
                        return mostrar_error("El correo es requerido")
                    elif '@' not in correo:
                        return mostrar_error("El correo debe contener @")
                    
                    if correo != correo_confirmar:
                        return mostrar_error("Los correos no coinciden")
                    
                    if not imagen_filename:
                        return mostrar_error("Debes seleccionar una imagen")
                    
                    # Guardar en PostgreSQL
                    conn = conectar_bd()
                    if not conn:
                        return mostrar_error("Error de conexión a la base de datos")
                    
                    cur = conn.cursor()
                    
                    # Crear tabla si no existe
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS formulario_registros (
                            id SERIAL PRIMARY KEY,
                            nombre VARCHAR(100),
                            edad INTEGER,
                            correo VARCHAR(100),
                            imagen_nombre VARCHAR(255),
                            imagen_data BYTEA,
                            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Insertar registro
                    cur.execute(
                        """
                        INSERT INTO formulario_registros 
                        (nombre, edad, correo, imagen_nombre, imagen_data) 
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (nombre, int(edad), correo, imagen_filename, imagen_data)
                    )
                    
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    # Guardar valores para mostrar en el formulario
                    nombre_guardado = nombre
                    edad_guardada = edad
                    correo_guardado = correo
                    
                    mensaje_exito = f'''
                    <div class="exito">
                        <div class="exito-icon">✅</div>
                        <h3>¡Registro exitoso!</h3>
                        <p><strong>Nombre:</strong> {nombre}</p>
                        <p><strong>Edad:</strong> {edad} años</p>
                        <p><strong>Correo:</strong> {correo}</p>
                        <p><strong>Imagen:</strong> {imagen_filename}</p>
                        <p style="margin-top: 15px; font-size: 14px; color: #28a745;">
                            Tu registro ha sido guardado correctamente.
                        </p>
                    </div>
                    '''
                    
                else:
                    return mostrar_error("Formato de formulario no válido")
                    
            except Exception as e:
                print(f"Error POST: {e}")
                return mostrar_error(f"Error al procesar el formulario: {str(e)}")
        
        # Obtener registros existentes
        registros_html = ""
        try:
            conn = conectar_bd()
            if conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT id, nombre, edad, correo, imagen_nombre, imagen_data, fecha 
                    FROM formulario_registros 
                    ORDER BY fecha DESC 
                    LIMIT 10
                ''')
                registros = cur.fetchall()
                cur.close()
                conn.close()
                
                if registros:
                    registros_html = '''
                    <div class="registros-container">
                        <h3>📋 Registros guardados:</h3>
                        <div class="registros-grid">
                    '''
                    
                    for id_reg, nombre_reg, edad_reg, correo_reg, imagen_nombre, imagen_data, fecha in registros:
                        fecha_str = str(fecha)[:16]
                        imagen_html = ""
                        
                        if imagen_nombre and imagen_data:
                            # Mostrar la imagen si existe
                            imagen_html = f'''
                            <div class="imagen-preview">
                                <a href="/imagen/{id_reg}" target="_blank">
                                    <img src="/imagen/{id_reg}" alt="{imagen_nombre}" 
                                         style="max-width: 100%; max-height: 150px; border-radius: 5px; margin-top: 10px;">
                                </a>
                                <p style="font-size: 12px; color: #666; margin-top: 5px;">
                                    <strong>Archivo:</strong> {imagen_nombre}<br>
                                    <a href="/imagen/{id_reg}" target="_blank" style="color: #007bff;">Ver imagen completa</a>
                                </p>
                            </div>
                            '''
                        else:
                            imagen_html = '<p style="color: #999; font-style: italic;">Sin imagen</p>'
                        
                        registros_html += f'''
                        <div class="registro-card">
                            <div class="registro-header">
                                <span class="registro-icon">👤</span>
                                <h4>{nombre_reg}</h4>
                            </div>
                            <div class="registro-body">
                                <p><strong>Edad:</strong> {edad_reg} años</p>
                                <p><strong>Correo:</strong> {correo_reg}</p>
                                {imagen_html}
                                <p style="margin-top: 10px;"><small>Registrado: {fecha_str}</small></p>
                                <div style="margin-top: 10px;">
                                    <a href="/imagen/{id_reg}" target="_blank" 
                                       style="background: #007bff; color: white; padding: 5px 10px; border-radius: 3px; 
                                              text-decoration: none; font-size: 12px;">
                                        📥 Descargar imagen
                                    </a>
                                </div>
                            </div>
                        </div>
                        '''
                    
                    registros_html += '''
                        </div>
                    </div>
                    '''
                else:
                    registros_html = '''
                    <div class="sin-registros">
                        <p>No hay registros aún. ¡Sé el primero en registrarte!</p>
                    </div>
                    '''
            else:
                registros_html = '''
                <div class="error-bd">
                    <p>⚠️ No se pudo conectar a la base de datos para mostrar registros.</p>
                </div>
                '''
        except Exception as e:
            print(f"Error obteniendo registros: {e}")
            registros_html = f'''
            <div class="error-bd">
                <p>⚠️ Error cargando registros: {str(e)}</p>
            </div>
            '''
        
        # HTML del formulario
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario de Registro</title>
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
            margin-bottom: 30px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 15px;
        }}
        .form-section {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
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
        input[type="number"],
        input[type="file"] {{
            width: 95%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            background: white;
        }}
        input[type="file"] {{
            padding: 8px;
            background: #e9ecef;
            cursor: pointer;
        }}
        .requerido {{ 
            color: #dc3545;
            font-size: 18px;
        }}
        .info {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
            font-style: italic;
        }}
        .exito {{
            background: #d4edda;
            color: #155724;
            padding: 25px;
            border-radius: 8px;
            margin: 25px 0;
            border-left: 5px solid #28a745;
        }}
        .exito-icon {{
            font-size: 40px;
            text-align: center;
            margin-bottom: 15px;
        }}
        .exito h3 {{
            color: #155724;
            margin-top: 0;
            text-align: center;
        }}
        button {{
            width: 100%;
            padding: 15px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            margin-top: 20px;
            transition: background 0.3s;
        }}
        button:hover {{
            background: #218838;
        }}
        .registros-container {{
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #dee2e6;
        }}
        .registros-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .registro-card {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .registro-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}
        .registro-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .registro-icon {{
            font-size: 24px;
            margin-right: 15px;
        }}
        .registro-header h4 {{
            margin: 0;
            color: #333;
        }}
        .registro-body p {{
            margin: 8px 0;
            color: #555;
        }}
        .registro-body small {{
            color: #6c757d;
            font-size: 12px;
        }}
        .imagen-preview {{
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }}
        .imagen-preview img {{
            transition: transform 0.2s;
        }}
        .imagen-preview img:hover {{
            transform: scale(1.05);
        }}
        .sin-registros {{
            text-align: center;
            padding: 40px;
            background: #e9ecef;
            border-radius: 8px;
            color: #6c757d;
            font-size: 18px;
        }}
        .error-bd {{
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            margin: 20px 0;
        }}
        .imagen-info {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #007bff;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>📝 Formulario de Registro</h1>
        
        {mensaje_exito if mensaje_exito else ''}
        
        <div class="form-section">
            <h2>Nuevo Registro</h2>
            <form method="POST" enctype="multipart/form-data">
                <!-- Nombre -->
                <div class="campo">
                    <label>Nombre completo <span class="requerido">*</span></label>
                    <input type="text" name="nombre" placeholder="Ej: Juan Pérez" required value="{nombre_guardado}">
                    <div class="info">Escribe tu nombre completo</div>
                </div>
                
                <!-- Edad -->
                <div class="campo">
                    <label>Edad <span class="requerido">*</span></label>
                    <input type="number" name="edad" placeholder="Ej: 25" min="1" max="120" required value="{edad_guardada}">
                    <div class="info">Debe ser un número entre 1 y 120</div>
                </div>
                
                <!-- Correo -->
                <div class="campo">
                    <label>Correo electrónico <span class="requerido">*</span></label>
                    <input type="email" name="correo" placeholder="Ej: usuario@correo.com" required value="{correo_guardado}">
                    <div class="info">Cualquier correo con formato válido</div>
                </div>
                
                <!-- Confirmar Correo -->
                <div class="campo">
                    <label>Confirmar correo <span class="requerido">*</span></label>
                    <input type="email" name="correo_confirmar" placeholder="Repite tu correo" required>
                    <div class="info">Debe coincidir con el correo anterior</div>
                </div>
                
                <!-- Imagen -->
                <div class="campo">
                    <label>Imagen <span class="requerido">*</span></label>
                    <input type="file" name="imagen" accept="image/*" required>
                    <div class="info">Selecciona una imagen (JPG, PNG, GIF, etc.)</div>
                </div>
                
                <div class="imagen-info">
                    <strong>📸 Información sobre la imagen:</strong>
                    <p>• Formatos aceptados: JPG, PNG, GIF, BMP, etc.</p>
                    <p>• Tamaño máximo: 5MB</p>
                    <p>• La imagen se guardará en la base de datos</p>
                    <p>• Se mostrará una miniatura en el listado de registros</p>
                </div>
                
                <button type="submit">✅ Enviar Formulario</button>
            </form>
        </div>
        
        {registros_html}
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
                post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                params = dict(pair.split('=') for pair in post_data.split('&'))
                
                # SUMA
                try:
                    num1 = float(params.get('suma1', '0'))
                    num2 = float(params.get('suma2', '0'))
                    resultado_suma = f"{num1} + {num2} = {num1 + num2}"
                except:
                    resultado_suma = f"Error: Entrada no válida para suma"
                
                # DIVISIÓN
                try:
                    num3 = float(params.get('div1', '0'))
                    num4 = float(params.get('div2', '0'))
                    if num4 == 0:
                        resultado_division = "Error: No se puede dividir entre cero"
                    else:
                        resultado_division = f"{num3} ÷ {num4} = {num3 / num4}"
                except:
                    resultado_division = f"Error: Entrada no válida para división"
                    
            except Exception as e:
                resultado_suma = f"Error general: {str(e)}"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Calculadora</title>
    <style>
        body {{ max-width: 800px; margin: 40px auto; padding: 20px; background: #f8f9fa; font-family: Arial; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-bottom: 30px; text-align: center; }}
        .calculadora {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin: 30px 0; }}
        .operacion {{ background: #f8f9fa; padding: 25px; border-radius: 8px; }}
        .suma {{ border-left: 4px solid #28a745; }} .division {{ border-left: 4px solid #dc3545; }}
        .campo {{ margin: 15px 0; }}
        input[type="text"] {{ width: 90%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
        button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
        .resultado {{ margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 5px; font-weight: bold; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>🧮 Calculadora</h1>
        <form method="POST">
            <div class="calculadora">
                <div class="operacion suma">
                    <h2>➕ Suma</h2>
                    <div class="campo"><input type="text" name="suma1" placeholder="Número 1"></div>
                    <div class="campo"><input type="text" name="suma2" placeholder="Número 2"></div>
                    <button>Calcular</button>
                    {f'<div class="resultado">{resultado_suma}</div>' if resultado_suma else ''}
                </div>
                <div class="operacion division">
                    <h2>➗ División</h2>
                    <div class="campo"><input type="text" name="div1" placeholder="Dividendo"></div>
                    <div class="campo"><input type="text" name="div2" placeholder="Divisor"></div>
                    <button>Calcular</button>
                    {f'<div class="resultado">{resultado_division}</div>' if resultado_division else ''}
                </div>
            </div>
        </form>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA DE INICIO ===
    elif path == '/':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inicio</title>
    <style>
        body {{ max-width: 800px; margin: 40px auto; padding: 20px; background: #f8f9fa; font-family: Arial; }}
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
        <h1>🚀 Aplicación Masonite en Railway</h1>
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🧮</div>
                <h3>Calculadora</h3>
                <p>Operaciones básicas</p>
                <a href="/calculadora">Ir →</a>
            </div>
            <div class="feature">
                <div class="feature-icon">📋</div>
                <h3>Formulario</h3>
                <p>Registro con imagen</p>
                <a href="/formulario">Ir →</a>
            </div>
        </div>
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
    <title>404</title>
</head>
<body>
    {navegacion()}
    <h1>404 - Página no encontrada</h1>
    <a href="/">Inicio</a>
</body>
</html>'''
        
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
