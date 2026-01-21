# -*- coding: utf-8 -*-
import os
import psycopg2
import re
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Headers UTF-8
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # === CONFIGURACIÓN ===
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    
    # === NAVEGACIÓN SIMPLE ===
    def navegacion():
        return '''<div style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none;">🏠 Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none;">🧮 Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none;">📋 Formulario</a>
        </div>'''
    
    # === CONEXIÓN BD ===
    def conectar_bd():
        try:
            result = urlparse(DATABASE_URL)
            conn = psycopg2.connect(
                host=result.hostname,
                database=result.path[1:],
                user=result.username,
                password=result.password,
                port=result.port,
                connect_timeout=5
            )
            return conn
        except Exception as e:
            print(f"Error BD: {e}")
            return None
    
    # === PÁGINA DE INICIO ===
    if path == '/' and method == 'GET':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inicio - Aplicación</title>
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
        .menu {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .opcion {{
            background: #e9ecef;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            text-decoration: none;
            color: #333;
            transition: transform 0.3s;
        }}
        .opcion:hover {{
            transform: translateY(-5px);
            background: #dee2e6;
        }}
        .opcion h3 {{ margin-top: 0; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>🚀 Aplicación con Formulario y Calculadora</h1>
        
        <div class="menu">
            <a href="/calculadora" class="opcion">
                <div style="font-size: 40px; margin-bottom: 15px;">🧮</div>
                <h3>Calculadora</h3>
                <p>Operaciones sin validación</p>
                <p><em>Prueba ingresando letras</em></p>
            </a>
            
            <a href="/formulario" class="opcion">
                <div style="font-size: 40px; margin-bottom: 15px;">📋</div>
                <h3>Formulario Simple</h3>
                <p>Nombre, Edad, Email</p>
                <p><em>Sube imagen y guarda en BD</em></p>
            </a>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 30px;">
            <h3>📝 Características:</h3>
            <ul>
                <li><strong>Formulario:</strong> Campos simples con validación básica</li>
                <li><strong>Calculadora:</strong> Sin validación para provocar errores</li>
                <li><strong>Base de datos:</strong> PostgreSQL para guardar registros</li>
                <li><strong>Muestra registros:</strong> Lista de datos enviados</li>
            </ul>
        </div>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA FORMULARIO SIMPLE ===
    elif path == '/formulario':
        mensaje = ""
        
        if method == 'POST':
            try:
                # Leer datos del formulario
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                
                # Parsear datos simples (application/x-www-form-urlencoded)
                from urllib.parse import parse_qs
                params = parse_qs(post_data)
                
                nombre = params.get('nombre', [''])[0].strip()
                edad = params.get('edad', [''])[0].strip()
                email = params.get('email', [''])[0].strip()
                email_confirmar = params.get('email_confirmar', [''])[0].strip()
                
                # Validaciones MUY básicas
                if not nombre:
                    mensaje = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">❌ El nombre es requerido</div>'
                elif not edad or not edad.isdigit():
                    mensaje = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">❌ La edad debe ser un número</div>'
                elif not email:
                    mensaje = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">❌ El email es requerido</div>'
                elif email != email_confirmar:
                    mensaje = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">❌ Los emails no coinciden</div>'
                else:
                    # Guardar en PostgreSQL
                    conn = conectar_bd()
                    if conn:
                        try:
                            cur = conn.cursor()
                            # Crear tabla si no existe
                            cur.execute('''
                                CREATE TABLE IF NOT EXISTS usuarios (
                                    id SERIAL PRIMARY KEY,
                                    nombre VARCHAR(100),
                                    edad INTEGER,
                                    email VARCHAR(100),
                                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            ''')
                            
                            # Insertar datos
                            cur.execute(
                                "INSERT INTO usuarios (nombre, edad, email) VALUES (%s, %s, %s)",
                                (nombre, int(edad), email)
                            )
                            
                            conn.commit()
                            cur.close()
                            conn.close()
                            
                            mensaje = f'''<div style="background: #d4edda; color: #155724; padding: 20px; border-radius: 5px; margin: 20px 0;">
                                ✅ ¡Registro exitoso!
                                <p><strong>Nombre:</strong> {nombre}</p>
                                <p><strong>Edad:</strong> {edad} años</p>
                                <p><strong>Email:</strong> {email}</p>
                                <p><small>Registro guardado en base de datos</small></p>
                            </div>'''
                            
                        except Exception as e:
                            mensaje = f'<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">❌ Error al guardar en BD: {str(e)}</div>'
                    else:
                        mensaje = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">❌ Error de conexión a la base de datos</div>'
                        
            except Exception as e:
                mensaje = f'<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">❌ Error: {str(e)}</div>'
        
        # Obtener registros existentes
        registros_html = ''
        try:
            conn = conectar_bd()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT nombre, edad, email, fecha FROM usuarios ORDER BY fecha DESC LIMIT 20")
                registros = cur.fetchall()
                cur.close()
                conn.close()
                
                if registros:
                    registros_html = '<h3>📋 Registros guardados:</h3><table style="width: 100%; border-collapse: collapse; margin: 20px 0;">'
                    registros_html += '''
                        <tr style="background: #343a40; color: white;">
                            <th style="padding: 10px; text-align: left;">Nombre</th>
                            <th style="padding: 10px; text-align: left;">Edad</th>
                            <th style="padding: 10px; text-align: left;">Email</th>
                            <th style="padding: 10px; text-align: left;">Fecha</th>
                        </tr>
                    '''
                    
                    for i, (nombre, edad, email, fecha) in enumerate(registros):
                        color = '#f8f9fa' if i % 2 == 0 else '#e9ecef'
                        fecha_str = str(fecha)[:16]
                        registros_html += f'''
                            <tr style="background: {color};">
                                <td style="padding: 10px; border: 1px solid #dee2e6;">{nombre}</td>
                                <td style="padding: 10px; border: 1px solid #dee2e6;">{edad}</td>
                                <td style="padding: 10px; border: 1px solid #dee2e6;">{email}</td>
                                <td style="padding: 10px; border: 1px solid #dee2e6;">{fecha_str}</td>
                            </tr>
                        '''
                    
                    registros_html += '</table>'
                    registros_html += f'<p><em>Total registros: {len(registros)}</em></p>'
                else:
                    registros_html = '<p style="color: #6c757d; margin: 20px 0;">No hay registros aún. ¡Sé el primero!</p>'
            else:
                registros_html = '<p style="color: #dc3545; margin: 20px 0;">⚠️ Base de datos no disponible</p>'
        except:
            registros_html = '<p style="color: #dc3545; margin: 20px 0;">⚠️ Error cargando registros</p>'
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario Simple</title>
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
        button {{
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
        button:hover {{
            background: #218838;
        }}
        hr {{
            margin: 40px 0;
            border: none;
            border-top: 1px solid #dee2e6;
        }}
        .instrucciones {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 10px;
            border: 1px solid #dee2e6;
            text-align: left;
        }}
        th {{
            background: #343a40;
            color: white;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>📋 Formulario Simple</h1>
        
        <div class="instrucciones">
            <p><strong>⚠️ Nota:</strong> El campo de imagen se muestra pero NO se guarda (solo para demostración).</p>
            <p>Los datos de nombre, edad y email sí se guardan en la base de datos PostgreSQL.</p>
        </div>
        
        {mensaje}
        
        <form method="POST" enctype="application/x-www-form-urlencoded">
            <!-- Nombre -->
            <div class="campo">
                <label>Nombre completo <span class="requerido">*</span></label>
                <input type="text" name="nombre" placeholder="Ej: Juan Pérez" required>
                <div class="info">Tu nombre completo</div>
            </div>
            
            <!-- Edad -->
            <div class="campo">
                <label>Edad <span class="requerido">*</span></label>
                <input type="number" name="edad" placeholder="Ej: 25" required min="1" max="120">
                <div class="info">Edad en años (solo números)</div>
            </div>
            
            <!-- Email -->
            <div class="campo">
                <label>Email <span class="requerido">*</span></label>
                <input type="email" name="email" placeholder="Ej: usuario@ejemplo.com" required>
                <div class="info">Cualquier formato de email válido</div>
            </div>
            
            <!-- Confirmar Email -->
            <div class="campo">
                <label>Confirmar Email <span class="requerido">*</span></label>
                <input type="email" name="email_confirmar" placeholder="Repite tu email" required>
                <div class="info">Debe coincidir con el email anterior</div>
            </div>
            
            <!-- Imagen (solo visual, no funcional) -->
            <div class="campo">
                <label>Subir imagen (opcional)</label>
                <input type="file" name="imagen" accept="image/*">
                <div class="info">Formato: JPG, PNG, GIF (no se guarda, solo demostración)</div>
            </div>
            
            <!-- Botón -->
            <button type="submit">✅ Enviar Formulario</button>
        </form>
        
        <hr>
        
        {registros_html}
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA CALCULADORA (SIN VALIDACIÓN) ===
    elif path == '/calculadora':
        resultado_suma = ""
        resultado_division = ""
        
        if method == 'POST':
            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                params = dict(pair.split('=') for pair in post_data.split('&'))
                
                # SUMA - SIN VALIDACIÓN
                try:
                    num1 = float(params.get('suma1', '0'))
                    num2 = float(params.get('suma2', '0'))
                    resultado_suma = f"<div style='background: #d4edda; padding: 15px; border-radius: 5px; margin: 10px 0;'><strong>✅ Resultado:</strong> {num1} + {num2} = {num1 + num2}</div>"
                except:
                    valor1 = params.get('suma1', 'vacío')
                    valor2 = params.get('suma2', 'vacío')
                    resultado_suma = f"<div style='background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0;'><strong>❌ Error suma:</strong> '{valor1}' + '{valor2}' no son números válidos</div>"
                
                # DIVISIÓN - SIN VALIDACIÓN
                try:
                    num3 = float(params.get('div1', '0'))
                    num4 = float(params.get('div2', '0'))
                    if num4 == 0:
                        resultado_division = f"<div style='background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0;'><strong>❌ Error:</strong> No se puede dividir entre cero</div>"
                    else:
                        resultado_division = f"<div style='background: #d4edda; padding: 15px; border-radius: 5px; margin: 10px 0;'><strong>✅ Resultado:</strong> {num3} ÷ {num4} = {num3 / num4}</div>"
                except:
                    valor3 = params.get('div1', 'vacío')
                    valor4 = params.get('div2', 'vacío')
                    resultado_division = f"<div style='background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0;'><strong>❌ Error división:</strong> '{valor3}' ÷ '{valor4}' no son números válidos</div>"
                    
            except Exception as e:
                resultado_suma = f"<div style='background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0;'><strong>❌ Error general:</strong> {str(e)}</div>"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Calculadora Sin Validación</title>
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
            margin-bottom: 30px;
            text-align: center;
        }}
        .calculadora {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin: 30px 0;
        }}
        @media (max-width: 600px) {{
            .calculadora {{
                grid-template-columns: 1fr;
            }}
        }}
        .operacion {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
        }}
        .suma {{ border-left: 4px solid #28a745; }}
        .division {{ border-left: 4px solid #dc3545; }}
        .campo {{
            margin: 15px 0;
        }}
        input[type="text"] {{
            width: 90%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }}
        button {{
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }}
        .advertencia {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
        .ejemplos {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>🧮 Calculadora Sin Validación</h1>
        
        <div class="advertencia">
            <strong>⚠️ ADVERTENCIA:</strong> Esta calculadora NO tiene validación.
            <p>Puedes ingresar letras, símbolos o cualquier texto para provocar errores.</p>
        </div>
        
        <form method="POST">
            <div class="calculadora">
                <!-- SUMA -->
                <div class="operacion suma">
                    <h2>➕ Suma</h2>
                    <div class="campo">
                        <label>Primer número:</label>
                        <input type="text" name="suma1" placeholder="Ej: 10 o 'abc'">
                    </div>
                    <div class="campo">
                        <label>Segundo número:</label>
                        <input type="text" name="suma2" placeholder="Ej: 5 o 'xyz'">
                    </div>
                    <button type="submit">Calcular Suma</button>
                    {resultado_suma}
                </div>
                
                <!-- DIVISIÓN -->
                <div class="operacion division">
                    <h2>➗ División</h2>
                    <div class="campo">
                        <label>Dividendo:</label>
                        <input type="text" name="div1" placeholder="Ej: 20 o 'hola'">
                    </div>
                    <div class="campo">
                        <label>Divisor:</label>
                        <input type="text" name="div2" placeholder="Ej: 4 o 'mundo'">
                    </div>
                    <button type="submit">Calcular División</button>
                    {resultado_division}
                </div>
            </div>
        </form>
        
        <div class="ejemplos">
            <h3>📝 Ejemplos para probar:</h3>
            <ul>
                <li><strong>Suma normal:</strong> "10" + "5" → Resultado: 15</li>
                <li><strong>Suma con letras:</strong> "abc" + "123" → Error</li>
                <li><strong>División normal:</strong> "20" ÷ "4" → Resultado: 5</li>
                <li><strong>División entre cero:</strong> "10" ÷ "0" → Error</li>
                <li><strong>Texto vacío:</strong> "" + "5" → Error</li>
            </ul>
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
    <title>404 - No encontrado</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 40px auto; 
            padding: 20px;
            background: #f8f9fa;
            text-align: center;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .icono {{ font-size: 80px; margin: 20px 0; }}
        h1 {{ color: #6c757d; }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="icono">🔍</div>
        <h1>404 - Página no encontrada</h1>
        <p>La página que buscas no existe.</p>
        <p><a href="/" style="color: #007bff;">Volver al inicio</a></p>
    </div>
</body>
</html>'''
        
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
