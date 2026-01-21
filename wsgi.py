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
    
    # === ELIMINAR TODOS LOS DATOS (solo primera vez) ===
    if path == '/resetear':
        try:
            conn = conectar_bd()
            if conn:
                cur = conn.cursor()
                cur.execute('DROP TABLE IF EXISTS formulario_registros')
                conn.commit()
                cur.close()
                conn.close()
                
                html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Base de datos resetada</title>
</head>
<body>
    <h1>Base de datos resetada correctamente</h1>
    <p>Todos los registros han sido eliminados.</p>
    <a href="/formulario">Volver al formulario</a>
</body>
</html>'''
                
                start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
                return [html.encode('utf-8')]
        except Exception as e:
            print(f"Error resetando BD: {e}")
    
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # === NAVEGACIÓN ===
    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🏠 Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🧮 Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">📋 Formulario</a>
            <a href="/resetear" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold; background: #dc3545; padding: 5px 10px; border-radius: 3px;">🗑️ Resetear BD</a>
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
                    SELECT id, nombre, edad, correo, imagen_nombre, fecha 
                    FROM formulario_registros 
                    ORDER BY fecha DESC 
                    LIMIT 20
                ''')
                registros = cur.fetchall()
                cur.close()
                conn.close()
                
                if registros:
                    registros_html = '''
                    <div class="registros-container">
                        <h3>📋 Registros guardados:</h3>
                        <div class="registros-lista">
                    '''
                    
                    for id_reg, nombre_reg, edad_reg, correo_reg, imagen_nombre, fecha in registros:
                        fecha_str = str(fecha)[:16]
                        
                        # Construir la ruta de la imagen
                        imagen_url = f"/imagen/{id_reg}"
                        
                        registros_html += f'''
                        <div class="registro-item">
                            <div class="registro-header">
                                <div class="registro-info">
                                    <h4>{nombre_reg}</h4>
                                    <div class="datos">
                                        <div><strong>Edad:</strong> {edad_reg} años</div>
                                        <div><strong>Correo:</strong> {correo_reg}</div>
                                    </div>
                                </div>
                                <div class="registro-fecha">
                                    <small>Registrado: {fecha_str}</small>
                                </div>
                            </div>
                            
                            <div class="registro-imagen">
                                <div class="imagen-container">
                                    <img src="{imagen_url}" alt="{imagen_nombre}" 
                                         onerror="this.style.display='none'; this.parentElement.innerHTML='<p style=\'color:#999\'>Imagen no disponible</p>';">
                                </div>
                                <div class="imagen-info">
                                    <p><strong>Archivo:</strong> {imagen_nombre}</p>
                                    <div class="imagen-enlaces">
                                        <a href="{imagen_url}" target="_blank" class="btn-ver">👁️ Ver imagen completa</a>
                                        <a href="{imagen_url}" download="{imagen_nombre}" class="btn-descargar">📥 Descargar imagen</a>
                                    </div>
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
                        <div class="sin-registros-icon">📭</div>
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
        .registros-lista {{
            margin-top: 20px;
        }}
        .registro-item {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .registro-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .registro-info h4 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 20px;
        }}
        .datos div {{
            margin: 5px 0;
            color: #555;
        }}
        .registro-fecha small {{
            color: #6c757d;
            font-size: 12px;
        }}
        .registro-imagen {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }}
        .imagen-container {{
            flex: 0 0 200px;
            height: 150px;
            background: #f8f9fa;
            border-radius: 5px;
            overflow: hidden;
            border: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .imagen-container img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        .imagen-info {{
            flex: 1;
        }}
        .imagen-info p {{
            margin: 0 0 10px 0;
            color: #555;
        }}
        .imagen-enlaces {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .btn-ver, .btn-descargar {{
            padding: 8px 15px;
            border-radius: 5px;
            text-decoration: none;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }}
        .btn-ver {{
            background: #007bff;
            color: white;
        }}
        .btn-descargar {{
            background: #28a745;
            color: white;
        }}
        .btn-ver:hover {{
            background: #0056b3;
        }}
        .btn-descargar:hover {{
            background: #218838;
        }}
        .sin-registros {{
            text-align: center;
            padding: 40px;
            background: #e9ecef;
            border-radius: 8px;
            color: #6c757d;
            font-size: 18px;
        }}
        .sin-registros-icon {{
            font-size: 50px;
            margin-bottom: 15px;
        }}
        .error-bd {{
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            margin: 20px 0;
        }}
        .imagen-info-form {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #007bff;
        }}
        .reset-warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>📝 Formulario de Registro</h1>
        
        <div class="reset-warning">
            <strong>⚠️ Nota:</strong> Si las imágenes antiguas no se muestran, usa el botón "Resetear BD" en el menú para limpiar la base de datos.
        </div>
        
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
                
                <div class="imagen-info-form">
                    <strong>📸 Información sobre la imagen:</strong>
                    <p>• Formatos aceptados: JPG, PNG, GIF, BMP, etc.</p>
                    <p>• Tamaño máximo: 5MB</p>
                    <p>• La imagen se guardará en la base de datos</p>
                    <p>• Se mostrará directamente en la página</p>
                </div>
                
                <button type="submit">✅ Enviar Formulario</button>
            </form>
        </div>
        
        {registros_html}
    </div>
    
    <script>
        // Manejar errores de imágenes
        document.addEventListener('DOMContentLoaded', function() {{
            const imagenes = document.querySelectorAll('.imagen-container img');
            imagenes.forEach(img => {{
                img.onerror = function() {{
                    this.style.display = 'none';
                    this.parentElement.innerHTML = '<p style="color:#999; text-align:center;">Imagen no disponible</p>';
                }};
            }});
        }});
    </script>
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
