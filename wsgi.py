# -*- coding: utf-8 -*-
import os
import psycopg2
import base64
import imghdr
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
    
    # === NAVEGACIÓN ===
    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🏠 Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🧮 Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">📋 Formulario</a>
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
    
    # === PÁGINA PRINCIPAL ===
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
        </div>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA CALCULADORA (COMPLETA) ===
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
    
    # === BORRAR REGISTROS ===
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
    
    # === PÁGINA FORMULARIO SIMPLIFICADO ===
    elif path == '/formulario':
        mensaje = ""
        
        # Procesar POST (formulario con archivos)
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
                edad = fs.getvalue('edad', '').strip()
                correo = fs.getvalue('correo', '').strip()
                correo_confirmar = fs.getvalue('correo_confirmar', '').strip()
                
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
                
                # Validaciones simples
                errores = []
                
                if not nombre:
                    errores.append("Nombre es requerido")
                
                if not edad:
                    errores.append("Edad es requerida")
                elif not edad.isdigit():
                    errores.append("Edad debe ser un número")
                
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
                                CREATE TABLE IF NOT EXISTS formulario_simple (
                                    id SERIAL PRIMARY KEY,
                                    nombre VARCHAR(100),
                                    edad INTEGER,
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
                                   (nombre, edad, correo, imagen_nombre, imagen_tipo, imagen_data) 
                                   VALUES (%s, %s, %s, %s, %s, %s)""",
                                (nombre, int(edad), correo, imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                            )
                            
                            conn.commit()
                            cur.close()
                            conn.close()
                            
                            mensaje = f'''<div class="exito">
                                <h3>✅ ¡Registro exitoso!</h3>
                                <p><strong>Nombre:</strong> {nombre}</p>
                                <p><strong>Edad:</strong> {edad} años</p>
                                <p><strong>Correo:</strong> {correo}</p>
                                <p><strong>Imagen:</strong> {imagen_nombre} ({imagen_tipo.upper()})</p>
                            </div>'''
                            
                        except Exception as e:
                            mensaje = f'<div class="error">❌ Error al guardar en BD: {str(e)}</div>'
                    else:
                        mensaje = '<div class="error">❌ Error de conexión a la base de datos</div>'
                        
            except Exception as e:
                mensaje = f'<div class="error">❌ Error procesando formulario: {str(e)}</div>'
        
        # Obtener registros anteriores
        registros_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre, edad, correo, imagen_nombre, imagen_tipo, fecha 
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
                            <h3>📝 Registros guardados:</h3>
                            <a href="/borrar_registros" style="background: #dc3545; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 14px;">
                                🗑️ Borrar todos los registros
                            </a>
                        </div>
                        <div class="lista-registros">
                    '''
                    
                    for reg in registros:
                        id_reg, nombre_reg, edad_reg, correo_reg, img_nombre, img_tipo, fecha = reg
                        fecha_str = str(fecha)[:16]
                        
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
        
        # HTML del formulario
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario con Imágenes</title>
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
        input[type="number"],
        input[type="file"] {{
            width: 95%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
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
        }}
        button[type="submit"]:hover {{
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
        <h1>📋 Formulario Simple con Imágenes</h1>
        
        {mensaje if mensaje else ''}
        
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <!-- Columna izquierda -->
                <div>
                    <!-- Nombre -->
                    <div class="campo">
                        <label>Nombre completo <span class="requerido">*</span></label>
                        <input type="text" name="nombre" placeholder="Ej: Juan Pérez" required>
                        <div class="info">Tu nombre completo</div>
                    </div>
                    
                    <!-- Edad -->
                    <div class="campo">
                        <label>Edad <span class="requerido">*</span></label>
                        <input type="number" name="edad" placeholder="Ej: 25" min="1" max="120" required>
                        <div class="info">Entre 1 y 120 años</div>
                    </div>
                </div>
                
                <!-- Columna derecha -->
                <div>
                    <!-- Correo -->
                    <div class="campo">
                        <label>Correo electrónico <span class="requerido">*</span></label>
                        <input type="email" name="correo" placeholder="Ej: usuario@correo.com" required>
                        <div class="info">Cualquier correo válido</div>
                    </div>
                    
                    <!-- Confirmar Correo -->
                    <div class="campo">
                        <label>Confirmar correo <span class="requerido">*</span></label>
                        <input type="email" name="correo_confirmar" placeholder="Repite tu correo" required>
                        <div class="info">Debe coincidir con el correo anterior</div>
                    </div>
                </div>
            </div>
            
            <!-- Imagen -->
            <div class="campo">
                <label>Subir imagen <span class="requerido">*</span></label>
                <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
                <div class="info">Formatos aceptados: JPG, PNG, GIF (máximo 5MB)</div>
            </div>
            
            <!-- Botón -->
            <button type="submit">📤 Enviar Formulario</button>
        </form>
        
        <hr>
        
        {registros_html}
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
