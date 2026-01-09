import os
import psycopg2
import requests
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # === CONFIGURACIÓN ===
    # PostgreSQL (usa TU contraseña)
    DATABASE_URL = os.environ.get('DATABASE_URL', "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway")
    
    # reCAPTCHA (usa claves de Railway o las de prueba)
    SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    
    # === CONEXIÓN POSTGRESQL ===
    def conectar_bd():
        try:
            result = urlparse(DATABASE_URL)
            return psycopg2.connect(
                host=result.hostname,
                database=result.path[1:],
                user=result.username,
                password=result.password,
                port=result.port
            )
        except:
            return None
    
    # === PÁGINA PRINCIPAL ===
    if path == '/' and method == 'GET':
        # Obtener mensajes
        mensajes_html = ''
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY fecha DESC")
                rows = cur.fetchall()
                
                if rows:
                    mensajes_html = '<ul>'
                    for nombre, mensaje, fecha in rows:
                        fecha_str = str(fecha)[:16]
                        mensajes_html += f'<li><strong>{nombre}</strong> ({fecha_str}): {mensaje}</li>'
                    mensajes_html += '</ul>'
                else:
                    mensajes_html = '<p>No hay mensajes.</p>'
                
                cur.close()
                conn.close()
            except:
                mensajes_html = '<p>Error cargando mensajes.</p>'
        
        # HTML con reCAPTCHA
        html = f'''<h1>Formulario con reCAPTCHA</h1>

<form method="POST">
<p>Nombre: <input type="text" name="nombre" required></p>
<p>Mensaje: <textarea name="mensaje" rows="3" required></textarea></p>

<div class="g-recaptcha" data-sitekey="{SITE_KEY}"></div>
<script src="https://www.google.com/recaptcha/api.js"></script>

<p><button type="submit">Enviar</button></p>
</form>

<hr>

<h3>Mensajes:</h3>
{mensajes_html}'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
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
                html = '<h1>Error</h1><p>Campos requeridos.</p><a href="/">Volver</a>'
                start_response('200 OK', [('Content-Type', 'text/html')])
                return [html.encode('utf-8')]
            
            # Guardar en BD
            conn = conectar_bd()
            if conn:
                cur = conn.cursor()
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS mensajes (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(100),
                        mensaje TEXT,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cur.execute("INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)", (nombre, mensaje))
                conn.commit()
                cur.close()
                conn.close()
            
            # Redirigir
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except:
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
    
    else:
        html = '<h1>404</h1><a href="/">Inicio</a>'
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
