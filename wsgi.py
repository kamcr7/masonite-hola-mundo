import os
import psycopg2
import requests
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # 1. CONFIGURACIÓN
    SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # 2. CONEXIÓN A POSTGRESQL
    def conectar_db():
        if not DATABASE_URL:
            return None
        try:
            result = urlparse(DATABASE_URL)
            conn = psycopg2.connect(
                host=result.hostname,
                database=result.path[1:],
                user=result.username,
                password=result.password,
                port=result.port
            )
            return conn
        except Exception as e:
            print(f"Error BD: {e}")
            return None
    
    # 3. CREAR TABLA SI NO EXISTE
    conn = conectar_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100),
                    mensaje TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cur.close()
            conn.close()
            print("Tabla creada/verificada")
        except Exception as e:
            print(f"Error creando tabla: {e}")
    
    # 4. SI ES POST (ENVIAR MENSAJE)
    if path == '/' and method == 'POST':
        try:
            # Leer datos del formulario
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            
            # Extraer nombre y mensaje
            from urllib.parse import parse_qs
            params = parse_qs(post_data)
            nombre = params.get('nombre', [''])[0]
            mensaje = params.get('mensaje', [''])[0]
            
            # Guardar en BD
            if nombre and mensaje:
                conn = conectar_db()
                if conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)",
                        (nombre, mensaje)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    print(f"Mensaje guardado: {nombre}")
            
            # Redirigir a la página principal (GET)
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except Exception as e:
            print(f"Error POST: {e}")
    
    # 5. PÁGINA PRINCIPAL (GET) - MUESTRA FORMULARIO Y MENSAJES
    elif path == '/' and method == 'GET':
        # Obtener mensajes de la BD
        mensajes_html = ''
        conn = conectar_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY fecha DESC")
                rows = cur.fetchall()
                cur.close()
                conn.close()
                
                if rows:
                    mensajes_html = '<h3>Mensajes:</h3><ul>'
                    for nombre, mensaje, fecha in rows:
                        fecha_str = str(fecha)[:19]  # Formato simple
                        mensajes_html += f'<li>{nombre} ({fecha_str}): {mensaje}</li>'
                    mensajes_html += '</ul>'
                else:
                    mensajes_html = '<p>No hay mensajes aún.</p>'
            except Exception as e:
                print(f"Error obteniendo mensajes: {e}")
                mensajes_html = '<p>Error cargando mensajes.</p>'
        
        # HTML completo
        html = f'''<h1>Formulario</h1>
<form method="POST">
<p>Nombre: <input type="text" name="nombre"></p>
<p>Mensaje: <textarea name="mensaje" rows="3"></textarea></p>
<div class="g-recaptcha" data-sitekey="{SITE_KEY}"></div>
<script src="https://www.google.com/recaptcha/api.js"></script>
<p><button type="submit">Enviar</button></p>
</form>
<hr>
{mensajes_html}'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # 6. PÁGINA NO ENCONTRADA
    else:
        html = '<h1>404</h1><a href="/">Inicio</a>'
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
