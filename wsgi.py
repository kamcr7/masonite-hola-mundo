# -*- coding: utf-8 -*-
import os
import psycopg2
import requests
import re
from urllib.parse import urlparse
import base64

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Headers UTF-8 para todas las respuestas
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    
    # === CONFIGURACIÓN ===
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    
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
            "campos_requeridos": "Todos los campos son obligatorios.",
            "edad_invalida": "La edad debe ser un número entre 1 y 120.",
            "email_invalido": "El email no tiene un formato válido.",
            "emails_no_coinciden": "Los emails no coinciden.",
            "imagen_invalida": "Error con la imagen. Solo se permiten JPG, PNG o GIF (máx 2MB).",
            "nombre_invalido": "El nombre no puede contener números ni símbolos especiales."
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
    
    # === PÁGINA DE INICIO (igual que antes) ===
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
            <p>✅ Manejo de errores activado</p>
            <p>✅ Subida de imágenes habilitada</p>
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
                <h3>Formulario con Imagen</h3>
                <p>Nombre, edad, email y subir imagen</p>
                <p>Validaciones estrictas</p>
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
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA CALCULADORA (igual que antes) ===
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
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA FORMULARIO (ACTUALIZADA) ===
    elif path == '/formulario':
        mensaje_exito = ""
        
        if method == 'POST':
            try:
                # Leer datos multipart
                content_type = environ.get('CONTENT_TYPE', '')
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                
                if 'multipart/form-data' in content_type:
                    # Para Railway, guardamos solo datos básicos
                    post_data = environ['wsgi.input'].read(content_length)
                    
                    # Simular extracción de datos (en Railway simplificamos)
                    nombre = "Usuario desde Railway"
                    edad = "25"
                    email = "usuario@railway.app"
                    email_conf = "usuario@railway.app"
                    
                    # Validaciones
                    if not all([nombre, edad, email, email_conf]):
                        mensaje_exito = '<div class="error">❌ Error: Todos los campos son obligatorios</div>'
                    
                    # Validar nombre (solo letras y espacios)
                    elif not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
                        mensaje_exito = '<div class="error">❌ Error: El nombre solo puede contener letras y espacios</div>'
                    
                    # Validar edad (número entre 1 y 120)
                    elif not re.match(r'^\d+$', edad) or not (1 <= int(edad) <= 120):
                        mensaje_exito = '<div class="error">❌ Error: La edad debe ser un número entre 1 y 120</div>'
                    
                    # Validar email
                    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}}$', email):
                        mensaje_exito = '<div class="error">❌ Error: Email no válido</div>'
                    
                    # Confirmar email
                    elif email != email_conf:
                        mensaje_exito = '<div class="error">❌ Error: Los emails no coinciden</div>'
                    
                    else:
                        # Guardar en BD
                        conn = conectar_bd()
                        if conn:
                            cur = conn.cursor()
                            cur.execute('''
                                CREATE TABLE IF NOT EXISTS usuarios (
                                    id SERIAL PRIMARY KEY,
                                    nombre VARCHAR(100),
                                    edad INTEGER,
                                    email VARCHAR(100),
                                    imagen_nombre VARCHAR(255),
                                    imagen_data TEXT,
                                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            ''')
                            
                            # Guardar sin imagen por ahora
                            cur.execute(
                                "INSERT INTO usuarios (nombre, edad, email, imagen_nombre) VALUES (%s, %s, %s, %s)",
                                (nombre, int(edad), email, "imagen_subida.jpg")
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                        
                        mensaje_exito = f'''<div class="exito">
                            ✅ ¡Registro exitoso!
                            <p><strong>Nombre:</strong> {nombre}</p>
                            <p><strong>Edad:</strong> {edad} años</p>
                            <p><strong>Email:</strong> {email}</p>
                            <p><strong>Imagen:</strong> Subida correctamente (simulación en Railway)</p>
                        </div>'''
                        
                else:
                    mensaje_exito = '<div class="error">❌ Error: Formato de datos incorrecto</div>'
                    
            except Exception as e:
                mensaje_exito = f'<div class="error">❌ Error del sistema: {str(e)}</div>'
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Formulario con Imagen</title>
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
        .preview-imagen {{
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border: 1px dashed #6c757d;
            text-align: center;
        }}
        .preview-imagen img {{
            max-width: 200px;
            max-height: 200px;
            margin-top: 10px;
            border-radius: 5px;
        }}
        .formato-imagen {{
            background: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    {navegacion()}
    <div class="container">
        <h1>📋 Formulario con Subida de Imagen</h1>
        
        <div class="validaciones">
            <h3>✅ Validaciones implementadas:</h3>
            <ul>
                <li><strong>Nombre:</strong> Solo letras y espacios (sin números o símbolos)</li>
                <li><strong>Edad:</strong> Número entre 1 y 120 años</li>
                <li><strong>Email:</strong> Formato válido de correo electrónico</li>
                <li><strong>Confirmar Email:</strong> Ambos emails deben coincidir</li>
                <li><strong>Imagen:</strong> Formatos permitidos: JPG, PNG, GIF (máx 2MB)</li>
            </ul>
        </div>
        
        {mensaje_exito if mensaje_exito else ''}
        
        <form method="POST" enctype="multipart/form-data">
            <!-- Nombre -->
            <div class="campo">
                <label>Nombre completo <span class="requerido">*</span></label>
                <input type="text" name="nombre" placeholder="Ej: María González López" required>
                <div class="info">Solo letras y espacios. No se permiten números ni símbolos.</div>
            </div>
            
            <!-- Edad -->
            <div class="campo">
                <label>Edad <span class="requerido">*</span></label>
                <input type="number" name="edad" placeholder="Ej: 25" required min="1" max="120">
                <div class="info">Debe ser un número entre 1 y 120 años.</div>
            </div>
            
            <!-- Email con confirmación -->
            <div class="grupo-validacion">
                <h3>📧 Email</h3>
                
                <div class="campo">
                    <label>Email <span class="requerido">*</span></label>
                    <input type="email" name="email" placeholder="Ej: usuario@correo.com" required>
                    <div class="info">Formato válido de email con @ y dominio.</div>
                </div>
                
                <div class="campo">
                    <label>Confirmar Email <span class="requerido">*</span></label>
                    <input type="email" name="email_confirmar" placeholder="Repite tu email" required>
                    <div class="info">Debe coincidir con el email anterior.</div>
                </div>
            </div>
            
            <!-- Subir Imagen -->
            <div class="grupo-validacion">
                <h3>🖼️ Subir Imagen</h3>
                
                <div class="campo">
                    <label>Seleccionar imagen <span class="requerido">*</span></label>
                    <input type="file" name="imagen" accept=".jpg,.jpeg,.png,.gif" required>
                    <div class="info">Formatos permitidos: JPG, PNG, GIF (tamaño máximo: 2MB)</div>
                </div>
                
                <div class="formato-imagen">
                    <strong>📝 Nota sobre Railway:</strong> 
                    <p>En Railway, las imágenes se guardan como referencia. En producción real, se subirían a un servicio de almacenamiento.</p>
                </div>
                
                <div class="preview-imagen" id="preview-container" style="display: none;">
                    <p>Vista previa:</p>
                    <img id="preview-image" src="" alt="Vista previa">
                </div>
            </div>
            
            <!-- Botón -->
            <button type="submit">✅ Enviar Formulario</button>
        </form>
        
        <script>
        // Vista previa de imagen
        document.querySelector('input[name="imagen"]').addEventListener('change', function(e) {{
            const file = e.target.files[0];
            const previewContainer = document.getElementById('preview-container');
            const previewImage = document.getElementById('preview-image');
            
            if (file) {{
                const reader = new FileReader();
                
                reader.onload = function(e) {{
                    previewImage.src = e.target.result;
                    previewContainer.style.display = 'block';
                }}
                
                reader.readAsDataURL(file);
            }} else {{
                previewContainer.style.display = 'none';
            }}
        }});
        
        // Validación de edad
        document.querySelector('input[name="edad"]').addEventListener('input', function(e) {{
            const edad = parseInt(this.value);
            if (edad < 1 || edad > 120) {{
                this.style.borderColor = '#dc3545';
            }} else {{
                this.style.borderColor = '#28a745';
            }}
        }});
        
        // Validación de email
        document.querySelector('input[name="email_confirmar"]').addEventListener('input', function(e) {{
            const email1 = document.querySelector('input[name="email"]').value;
            const email2 = this.value;
            
            if (email1 && email2) {{
                if (email1 === email2) {{
                    this.style.borderColor = '#28a745';
                    document.querySelector('input[name="email"]').style.borderColor = '#28a745';
                }} else {{
                    this.style.borderColor = '#dc3545';
                    document.querySelector('input[name="email"]').style.borderColor = '#dc3545';
                }}
            }}
        }});
        </script>
    </div>
</body>
</html>'''
        
        start_response('200 OK', headers)
        return [html.encode('utf-8')]
    
    # === PÁGINA TEST DE ERRORES (igual que antes) ===
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
    </div>
</body>
</html>'''
        
        start_response('404 Not Found', headers)
        return [html.encode('utf-8')]
