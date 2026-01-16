import os
import psycopg2
import requests
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # === CONFIGURACIÓN ===
    # PostgreSQL (usa TU contraseña)
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    
    # reCAPTCHA (claves de prueba que funcionan siempre)
    SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    
    # === PÁGINA DE ERROR AMIGABLE ===
    def mostrar_error(tipo_error="general"):
        mensajes = {
            "general": "Ocurrió un error inesperado.",
            "bd_conexion": "No se pudo conectar a la base de datos.",
            "bd_guardar": "Error al guardar el mensaje.",
            "bd_cargar": "Error al cargar los mensajes.",
            "campos_vacios": "Nombre y mensaje son requeridos.",
            "recaptcha": "Por favor, verifica que no eres un robot.",
            "recaptcha_fallo": "La verificación de reCAPTCHA falló."
        }
        
        mensaje = mensajes.get(tipo_error, "Ocurrió un error.")
        robot = "🤖" if "recaptcha" in tipo_error else "😕"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Error - Masonite App</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            text-align: center; 
            margin-top: 80px; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .error-box {{
            max-width: 500px;
            margin: 0 auto;
            padding: 40px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .robot {{
            font-size: 70px;
            margin: 0 0 20px 0;
        }}
        h1 {{ 
            color: #dc3545;
            margin: 0 0 15px 0;
        }}
        .mensaje {{ 
            color: #6c757d; 
            font-size: 18px;
            line-height: 1.5;
            margin: 0 0 25px 0;
        }}
        .boton {{
            display: inline-block;
            padding: 12px 30px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 16px;
            border: none;
            cursor: pointer;
        }}
        .boton:hover {{
            background: #0056b3;
        }}
        .info {{
            margin-top: 30px;
            padding: 15px;
            background: #e9ecef;
            border-radius: 5px;
            font-size: 14px;
            color: #495057;
        }}
    </style>
</head>
<body>
    <div class="error-box">
        <div class="robot">{robot}</div>
        <h1>¡Ups! Algo salió mal</h1>
        <div class="mensaje">
            {mensaje}
            <p>Nuestro equipo está trabajando para solucionarlo.</p>
        </div>
        <a href="/" class="boton">Volver al inicio</a>
        
        <div class="info">
            <p>Si el problema persiste, por favor intenta más tarde.</p>
        </div>
    </div>
</body>
</html>'''
        
        start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # === PÁGINA 404 ===
    def mostrar_404():
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Página no encontrada</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            margin-top: 100px; 
            background: #f8f9fa;
        }
        .icono { font-size: 80px; margin-bottom: 20px; }
        h1 { color: #6c757d; }
        .boton {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="icono">🔍</div>
    <h1>Página no encontrada</h1>
    <p>La página que buscas no existe o fue movida.</p>
    <a href="/" class="boton">Volver al inicio</a>
</body>
</html>'''
        
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # === CONEXIÓN POSTGRESQL ===
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
            print(f"❌ Error BD: {e}")
            return None
    
    # === VERIFICAR RECAPTCHA ===
    def verificar_recaptcha(token):
        if not token:
            return False
        
        # Con claves de prueba, siempre válido
        if SECRET_KEY == "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe":
            return True
        
        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={'secret': SECRET_KEY, 'response': token},
                timeout=5
            )
            return response.json().get('success', False)
        except:
            return False
    
    # === PÁGINA PRINCIPAL ===
    if path == '/' and method == 'GET':
        try:
            conn = conectar_bd()
            if not conn:
                return mostrar_error("bd_conexion")
            
            cur = conn.cursor()
            
            # Crear tabla si no existe
            cur.execute('''
                CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100),
                    mensaje TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Obtener mensajes
            cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY fecha DESC")
            mensajes = cur.fetchall()
            
            conn.commit()
            cur.close()
            conn.close()
            
            # HTML normal
            html = f'''<h1>Formulario con reCAPTCHA</h1>

<form method="POST">
<p>Nombre: <input type="text" name="nombre" required></p>
<p>Mensaje: <textarea name="mensaje" rows="3" required></textarea></p>

<div class="g-recaptcha" data-sitekey="{SITE_KEY}"></div>
<script src="https://www.google.com/recaptcha/api.js"></script>

<p><button type="submit">Enviar Mensaje</button></p>
</form>

<hr>

<h3>Mensajes guardados:</h3>'''
            
            if mensajes:
                html += '<ul>'
                for nombre, mensaje, fecha in mensajes:
                    fecha_str = str(fecha)[:16]
                    html += f'<li><strong>{nombre}</strong> ({fecha_str}): {mensaje}</li>'
                html += '</ul>'
            else:
                html += '<p>No hay mensajes aún. ¡Sé el primero!</p>'
            
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
            
        except Exception as e:
            print(f"❌ Error GET: {e}")
            return mostrar_error("bd_cargar")
    
    # === PROCESAR FORMULARIO ===
    elif path == '/' and method == 'POST':
        try:
            # Leer datos
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            
            from urllib.parse import parse_qs
            params = parse_qs(post_data)
            
            nombre = params.get('nombre', [''])[0].strip()
            mensaje = params.get('mensaje', [''])[0].strip()
            recaptcha_token = params.get('g-recaptcha-response', [''])[0]
            
            # Validar campos
            if not nombre or not mensaje:
                return mostrar_error("campos_vacios")
            
            # Verificar reCAPTCHA
            if not verificar_recaptcha(recaptcha_token):
                return mostrar_error("recaptcha_fallo")
            
            # Guardar en BD
            conn = conectar_bd()
            if not conn:
                return mostrar_error("bd_conexion")
            
            cur = conn.cursor()
            cur.execute("INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)", (nombre, mensaje))
            conn.commit()
            cur.close()
            conn.close()
            
            # Redirigir
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except Exception as e:
            print(f"❌ Error POST: {e}")
            return mostrar_error("bd_guardar")
    
    # === PÁGINA NO ENCONTRADA ===
    else:
        return mostrar_404()
