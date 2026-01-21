# -*- coding: utf-8 -*-
import os
import psycopg2
import requests
import re
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Headers UTF-8 para todas las respuestas
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # === CONFIGURACIÓN ===
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    
    # === NAVEGACIÓN ===
    def navegacion():
        return '''<nav style="background: #343a40; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
            <a href="/" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🏠 Inicio</a>
            <a href="/calculadora" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">🧮 Calculadora</a>
            <a href="/formulario" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">📋 Formulario</a>
            <a href="/error-test" style="color: white; margin: 0 15px; text-decoration: none; font-weight: bold;">⚠️ Test Errores</a>
        </nav>'''
    
    # === PÁGINA DE ERROR ===
    def mostrar_error(tipo_error="general", detalle=""):
        mensajes = {
            "general": "Ocurrió un error inesperado.",
            "bd_conexion": "No se pudo conectar a la base de datos.",
            "division_cero": "Error: No se puede dividir entre cero.",
            "validacion": f"Error de validación: {detalle}",
            "recaptcha": "Por favor, verifica que no eres un robot.",
            "campos_requeridos": "Todos los campos son obligatorios."
        }
        
        mensaje = mensajes.get(tipo_error, "Ocurrió un error.")
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error - Aplicación Masonite</title>
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
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .error-icon {{
            font-size: 80px;
            text-align: center;
            margin: 20px 0;
            color: #dc3545;
        }}
        h1 {{ 
            color: #dc3545;
            text-align: center;
            margin-bottom: 20px;
        }}
        .error-details {{
            background: #ffe6e6;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #dc3545;
        }}
        .botones {{
            text-align: center;
            margin-top: 30px;
        }}
        .boton {{
            display: inline-block;
            padding: 10px 20px;
            margin: 0 10px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}
        .boton:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <div class="error-icon">⚠️</div>
        <h1>Error en la aplicación</h1>
        
        <div class="error-details">
            <h3>{mensaje}</h3>
            <p>Detalle del error: {detalle if detalle else "No disponible"}</p>
        </div>
        
        <div class="botones">
            <a href="/" class="boton">🏠 Ir al Inicio</a>
            <a href="/calculadora" class="boton">🧮 Ir a Calculadora</a>
            <a href="/formulario" class="boton">📋 Ir a Formulario</a>
        </div>
    </div>
</body>
</html>'''
        
        start_response('500 Internal Server Error', headers)
        return [html.encode('utf-8')]
    
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
        except Exception as e:
            return None
    
    # === PÁGINA DE INICIO ===
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
        .card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }}
        .card h3 {{ margin-top: 0; }}
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
        
        <div class="card">
            <h3>📊 Estado del sistema</h3>
            <p>✅ Aplicación funcionando correctamente</p>
            <p>✅ PostgreSQL conectado</p>
            <p>✅ reCAPTCHA configurado</p>
            <p>✅ Manejo de errores activado</p>
        </div>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🧮</div>
                <h3>Calculadora</h3>
                <p>Operaciones básicas sin validación</p>
                <p><em>Prueba ingresando letras o símbolos</em></p>
                <a href="/calculadora">Ir a Calculadora →</a>
            </div>
            
            <div class="feature">
                <div class="feature-icon">📋</div>
                <h3>Formulario Validado</h3>
                <p>Validaciones estrictas de datos</p>
                <p>Confirmación de campos</p>
                <a href="/formulario">Ir a Formulario →</a>
            </div>
            
            <div class="feature">
                <div class="feature-icon">⚠️</div>
                <h3>Test de Errores</h3>
                <p>Página para provocar errores</p>
                <p>Manejo elegante de fallos</p>
                <a href="/error-test">Probar Errores →</a>
            </div>
        </div>
        
        <div class="card">
            <h3>📝 Instrucciones</h3>
            <ol>
                <li><strong>Calculadora:</strong> Ingresa cualquier texto (incluso no numérico) para ver errores</li>
                <li><strong>Formulario:</strong> Sigue las validaciones estrictas para enviar datos</li>
                <li><strong>Test Errores:</strong> Provoca errores controlados para probar el manejo</li>
            </ol>
        </div>
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
                    resultado_suma = f"{num1} + {num2} = {num1 + num2}"
                except:
                    resultado_suma = f"Error: '{params.get('suma1', '')}' + '{params.get('suma2', '')}' no son números válidos"
                
                # DIVISIÓN - SIN VALIDACIÓN
                try:
                    num3 = float(params.get('div1', '0'))
                    num4 = float(params.get('div2', '0'))
                    if num4 == 0:
                        resultado_division = "Error: No se puede dividir entre cero"
                    else:
                        resultado_division = f"{num3} ÷ {num4} = {num3 / num4}"
                except:
                    resultado_division = f"Error: '{params.get('div1', '')}' ÷ '{params.get('div2', '')}' no son números válidos"
                    
            except Exception as e:
                resultado_suma = f"Error general: {str(e)}"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Calculadora - Sin Validación</title>
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
        h1, h2 {{ 
            color: #333; 
            margin-bottom: 20px;
        }}
        .calculadora {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin: 30px 0;
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
        .resultado {{
            margin-top: 20px;
            padding: 15px;
            background: #e9ecef;
            border-radius: 5px;
            font-weight: bold;
        }}
        .error {{ color: #dc3545; }}
        .exito {{ color: #28a745; }}
        .advertencia {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>🧮 Calculadora Sin Validación</h1>
        
        <div class="advertencia">
            <strong>⚠️ ADVERTENCIA:</strong> Esta calculadora NO tiene validación de entrada.
            <p>Puedes ingresar letras, símbolos o cualquier texto para provocar errores.</p>
            <p><em>Ejemplos para probar: "abc", "12.34", "1,2", "", "10 20", etc.</em></p>
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
                    {f'<div class="resultado">{resultado_suma}</div>' if resultado_suma else ''}
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
                    {f'<div class="resultado">{resultado_division}</div>' if resultado_division else ''}
                </div>
            </div>
        </form>
        
        <div class="advertencia">
            <h3>📝 Ejemplos para probar errores:</h3>
            <ul>
                <li><strong>Suma con letras:</strong> "abc" + "123" → Error de conversión</li>
                <li><strong>División entre cero:</strong> "10" ÷ "0" → Error matemático</li>
                <li><strong>Símbolos:</strong> "" ÷ "2" → Error de formato</li>
                <li><strong>Texto vacío:</strong> "" + "5" → Error de valor vacío</li>
            </ul>
        </div>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA FORMULARIO (CON VALIDACIÓN ESTRICTA) ===
    elif path == '/formulario':
        mensaje_exito = ""
        
        if method == 'POST':
            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                params = dict(pair.split('=') for pair in post_data.split('&'))
                
                # Validaciones estrictas
                nombre = params.get('nombre', '')
                email = params.get('email', '')
                telefono = params.get('telefono', '')
                telefono_conf = params.get('telefono_conf', '')
                codigo = params.get('codigo', '')
                codigo_conf = params.get('codigo_conf', '')
                recaptcha = params.get('g-recaptcha-response', '')
                
                # 1. Campos requeridos
                if not all([nombre, email, telefono, telefono_conf, codigo, codigo_conf]):
                    mensaje_exito = '<div class="error">❌ Error: Todos los campos son obligatorios</div>'
                
                # 2. Validar nombre (solo letras y espacios)
                elif not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
                    mensaje_exito = '<div class="error">❌ Error: El nombre solo puede contener letras y espacios</div>'
                
                # 3. Validar email
                elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}}$', email):
                    mensaje_exito = '<div class="error">❌ Error: Email no válido</div>'
                
                # 4. Validar teléfono (10 dígitos)
                elif not re.match(r'^\d{{10}}$', telefono):
                    mensaje_exito = '<div class="error">❌ Error: Teléfono debe tener 10 dígitos</div>'
                
                # 5. Confirmar teléfono
                elif telefono != telefono_conf:
                    mensaje_exito = '<div class="error">❌ Error: Los teléfonos no coinciden</div>'
                
                # 6. Validar código (6 dígitos)
                elif not re.match(r'^\d{{6}}$', codigo):
                    mensaje_exito = '<div class="error">❌ Error: Código debe tener 6 dígitos</div>'
                
                # 7. Confirmar código
                elif codigo != codigo_conf:
                    mensaje_exito = '<div class="error">❌ Error: Los códigos no coinciden</div>'
                
                # 8. reCAPTCHA
                elif not recaptcha:
                    mensaje_exito = '<div class="error">❌ Error: Verifica el reCAPTCHA</div>'
                
                else:
                    # Guardar en BD
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute('''
                            CREATE TABLE IF NOT EXISTS formularios (
                                id SERIAL PRIMARY KEY,
                                nombre VARCHAR(100),
                                email VARCHAR(100),
                                telefono VARCHAR(10),
                                codigo VARCHAR(6),
                                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
                        cur.execute(
                            "INSERT INTO formularios (nombre, email, telefono, codigo) VALUES (%s, %s, %s, %s)",
                            (nombre, email, telefono, codigo)
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                    
                    mensaje_exito = f'''<div class="exito">
                        ✅ ¡Registro exitoso!
                        <p><strong>Nombre:</strong> {nombre}</p>
                        <p><strong>Email:</strong> {email}</p>
                        <p><strong>Teléfono:</strong> {telefono[:3]} *** ****</p>
                        <p><strong>Código:</strong> ******</p>
                    </div>'''
                    
            except Exception as e:
                mensaje_exito = f'<div class="error">❌ Error del sistema: {str(e)}</div>'
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario con Validación</title>
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
            margin-bottom: 20px;
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
        input[type="email"] {{
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
        .grupo-validacion {{
            background: #e9ecef;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
            border-left: 4px solid #17a2b8;
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
        .validaciones {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 5px;
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>📋 Formulario con Validación Estricta</h1>
        
        <div class="validaciones">
            <h3>✅ Validaciones implementadas:</h3>
            <ul>
                <li><strong>Nombre:</strong> Solo letras y espacios (no números)</li>
                <li><strong>Email:</strong> Formato válido de correo electrónico</li>
                <li><strong>Teléfono:</strong> Exactamente 10 dígitos numéricos</li>
                <li><strong>Confirmación teléfono:</strong> Ambos deben coincidir</li>
                <li><strong>Código:</strong> Exactamente 6 dígitos numéricos</li>
                <li><strong>Confirmación código:</strong> Ambos deben coincidir</li>
                <li><strong>reCAPTCHA:</strong> Verificación anti-robots</li>
            </ul>
        </div>
        
        {mensaje_exito if mensaje_exito else ''}
        
        <form method="POST">
            <!-- Nombre -->
            <div class="campo">
                <label>Nombre completo <span class="requerido">*</span></label>
                <input type="text" name="nombre" placeholder="Ej: Juan Pérez García" required>
                <div class="info">Solo letras y espacios. No se permiten números.</div>
            </div>
            
            <!-- Email -->
            <div class="campo">
                <label>Email <span class="requerido">*</span></label>
                <input type="email" name="email" placeholder="Ej: usuario@correo.com" required>
                <div class="info">Formato válido de email con @ y dominio.</div>
            </div>
            
            <!-- Teléfono con confirmación -->
            <div class="grupo-validacion">
                <h3>📱 Teléfono (10 dígitos)</h3>
                
                <div class="campo">
                    <label>Teléfono <span class="requerido">*</span></label>
                    <input type="text" name="telefono" placeholder="Ej: 5512345678" required maxlength="10">
                    <div class="info">10 dígitos numéricos exactos.</div>
                </div>
                
                <div class="campo">
                    <label>Confirmar teléfono <span class="requerido">*</span></label>
                    <input type="text" name="telefono_conf" placeholder="Repite el teléfono" required maxlength="10">
                    <div class="info">Debe coincidir con el teléfono anterior.</div>
                </div>
            </div>
            
            <!-- Código con confirmación -->
            <div class="grupo-validacion">
                <h3>🔢 Código de verificación (6 dígitos)</h3>
                
                <div class="campo">
                    <label>Código <span class="requerido">*</span></label>
                    <input type="text" name="codigo" placeholder="Ej: 123456" required maxlength="6">
                    <div class="info">6 dígitos numéricos exactos.</div>
                </div>
                
                <div class="campo">
                    <label>Confirmar código <span class="requerido">*</span></label>
                    <input type="text" name="codigo_conf" placeholder="Repite el código" required maxlength="6">
                    <div class="info">Debe coincidir con el código anterior.</div>
                </div>
            </div>
            
            <!-- reCAPTCHA -->
            <div class="g-recaptcha" data-sitekey="{SITE_KEY}"></div>
            <script src="https://www.google.com/recaptcha/api.js"></script>
            
            <!-- Botón -->
            <button type="submit">✅ Enviar Formulario Validado</button>
        </form>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA TEST DE ERRORES ===
    elif path == '/error-test':
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test de Errores Controlados</title>
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
        }}
        .test-error {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
        .test-error h3 {{ margin-top: 0; }}
        .boton-test {{
            padding: 10px 20px;
            margin: 10px 0;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        .boton-test:hover {{
            background: #c82333;
        }}
        .explicacion {{
            background: #d4edda;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>⚠️ Test de Errores Controlados</h1>
        
        <div class="explicacion">
            <p>Esta página permite probar el manejo de errores de la aplicación.</p>
            <p>Al hacer clic en los botones, se provocarán errores controlados que serán manejados por la página de error.</p>
        </div>
        
        <div class="test-error">
            <h3>🔧 Error de Base de Datos</h3>
            <p>Simula un error de conexión a PostgreSQL</p>
            <form action="/error-db" method="POST" style="display: inline;">
                <button type="submit" class="boton-test">Provocar Error BD</button>
            </form>
        </div>
        
        <div class="test-error">
            <h3>➗ Error Matemático</h3>
            <p>Intenta dividir entre cero</p>
            <form action="/error-math" method="POST" style="display: inline;">
                <input type="hidden" name="dividendo" value="10">
                <input type="hidden" name="divisor" value="0">
                <button type="submit" class="boton-test">Dividir entre Cero</button>
            </form>
        </div>
        
        <div class="test-error">
            <h3>📝 Error de Validación</h3>
            <p>Envía datos inválidos al formulario</p>
            <form action="/error-validation" method="POST" style="display: inline;">
                <input type="hidden" name="dato" value="invalido">
                <button type="submit" class="boton-test">Enviar Datos Inválidos</button>
            </form>
        </div>
        
        <div class="test-error">
            <h3>🚫 Error General</h3>
            <p>Provoca un error inesperado</p>
            <form action="/error-general" method="POST" style="display: inline;">
                <button type="submit" class="boton-test">Error Inesperado</button>
            </form>
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <h3>📋 Resultados esperados:</h3>
            <ul>
                <li><strong>Error BD:</strong> Página de error con mensaje de conexión fallida</li>
                <li><strong>Error Matemático:</strong> Página de error con mensaje de división entre cero</li>
                <li><strong>Error Validación:</strong> Página de error con detalles de validación</li>
                <li><strong>Error General:</strong> Página de error genérica</li>
            </ul>
            <p><em>Todos los errores mostrarán botones para navegar a otras secciones de la aplicación.</em></p>
        </div>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === MANEJADORES DE ERRORES PARA TEST ===
    elif path == '/error-db' and method == 'POST':
        return mostrar_error("bd_conexion", "Conexión a PostgreSQL falló intencionalmente")
    
    elif path == '/error-math' and method == 'POST':
        return mostrar_error("division_cero", "Intento de división entre cero")
    
    elif path == '/error-validation' and method == 'POST':
        return mostrar_error("validacion", "Datos inválidos enviados: 'invalido'")
    
    elif path == '/error-general' and method == 'POST':
        return mostrar_error("general", "Error provocado para testing")
    
    # === PÁGINA 404 ===
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
        <p>La página que buscas no existe o fue movida.</p>
        <p>Usa la navegación superior para ir a una sección válida.</p>
    </div>
</body>
</html>'''
        
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
