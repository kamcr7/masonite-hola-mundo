import os
import psycopg2
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # === PÁGINA DE ERROR (cuando algo falle) ===
    def mostrar_error(mensaje="Ocurrió un error"):
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Error - Masonite App</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            text-align: center; 
            margin-top: 100px; 
            padding: 20px;
        }}
        .error-container {{
            max-width: 500px;
            margin: 0 auto;
            padding: 30px;
            border: 1px solid #ffcccc;
            background: #fff5f5;
            border-radius: 10px;
        }}
        .robot {{
            font-size: 60px;
            margin: 20px 0;
        }}
        h1 {{ color: #cc0000; }}
        .mensaje {{ 
            margin: 20px 0; 
            color: #666; 
            line-height: 1.6;
        }}
        .boton {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="robot">🤖</div>
        <h1>¡Ups! Algo salió mal</h1>
        <div class="mensaje">
            {mensaje}
            <p>Nuestro equipo de robots está trabajando para solucionarlo.</p>
            <p>Por favor, inténtalo de nuevo en unos momentos.</p>
        </div>
        <a href="/" class="boton">Volver al inicio</a>
    </div>
</body>
</html>'''
        
        start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # === CONEXIÓN A POSTGRESQL ===
    def conectar_bd():
        try:
            # Tu contraseña real
            DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
            
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
            print(f"❌ Error conexión BD: {e}")
            return None
    
    # === PÁGINA PRINCIPAL ===
    if path == '/' and method == 'GET':
        try:
            conn = conectar_bd()
            if not conn:
                return mostrar_error("No se pudo conectar a la base de datos.")
            
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
            
            # Generar HTML normal
            html = '''<h1>Formulario</h1>

<form method="POST">
<p>Nombre: <input type="text" name="nombre" required></p>
<p>Mensaje: <textarea name="mensaje" rows="3" required></textarea></p>
<p><button type="submit">Enviar</button></p>
</form>

<hr>

<h3>Mensajes:</h3>'''
            
            if mensajes:
                html += '<ul>'
                for nombre, mensaje, fecha in mensajes:
                    fecha_str = str(fecha)[:16]
                    html += f'<li><strong>{nombre}</strong> ({fecha_str}): {mensaje}</li>'
                html += '</ul>'
            else:
                html += '<p>No hay mensajes aún.</p>'
            
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
            
        except Exception as e:
            return mostrar_error("Error al cargar los datos.")
    
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
            
            # Validar
            if not nombre or not mensaje:
                return mostrar_error("Nombre y mensaje son requeridos.")
            
            # Guardar en BD
            conn = conectar_bd()
            if not conn:
                return mostrar_error("Error al guardar el mensaje.")
            
            cur = conn.cursor()
            cur.execute("INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)", (nombre, mensaje))
            conn.commit()
            cur.close()
            conn.close()
            
            # Redirigir
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except Exception as e:
            return mostrar_error("Error al procesar el formulario.")
    
    # === PÁGINA NO ENCONTRADA ===
    else:
        def mostrar_404():
            html = '''<!DOCTYPE html>
<html>
<head>
    <title>Página no encontrada</title>
    <style>
        body {{ text-align: center; margin-top: 100px; }}
        .robot {{ font-size: 80px; }}
        h1 {{ color: #666; }}
    </style>
</head>
<body>
    <div class="robot">🔍</div>
    <h1>Página no encontrada</h1>
    <p>La página que buscas no existe.</p>
    <a href="/">Volver al inicio</a>
</body>
</html>'''
            
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
        
        return mostrar_404()
