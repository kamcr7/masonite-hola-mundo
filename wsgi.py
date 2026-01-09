import os
import psycopg2
import requests
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Configuración
    SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # Conexión a PostgreSQL
    def get_db():
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
        except:
            return None
    
    # Crear tabla
    def init_db():
        conn = get_db()
        if not conn:
            return
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
        except:
            pass
    
    # Verificar reCAPTCHA
    def verify_recaptcha(token):
        if not token:
            return False
        if SECRET_KEY == '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe':
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
    
    # Página principal - Muestra formulario Y mensajes
    if path == '/' and method == 'GET':
        init_db()
        
        # Obtener mensajes
        mensajes_html = ''
        conn = get_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY fecha DESC")
                rows = cur.fetchall()
                cur.close()
                conn.close()
                
                if rows:
                    mensajes_html = '<h3>Mensajes enviados:</h3><ul>'
                    for nombre, mensaje, fecha in rows:
                        if isinstance(fecha, str):
                            fecha_str = fecha
                        else:
                            fecha_str = fecha.strftime('%Y-%m-%d %H:%M')
                        mensajes_html += f'<li><strong>{nombre}</strong> ({fecha_str}): {mensaje}</li>'
                    mensajes_html += '</ul>'
                else:
                    mensajes_html = '<p>No hay mensajes aún.</p>'
            except:
                mensajes_html = '<p>Error cargando mensajes.</p>'
        
        html = f'''<h1>Formulario con reCAPTCHA</h1>

<form method="POST" action="/">
<p>Nombre: <input type="text" name="nombre" required></p>
<p>Mensaje: <textarea name="mensaje" rows="3" required></textarea></p>

<div class="g-recaptcha" data-sitekey="{SITE_KEY}"></div>
<script src="https://www.google.com/recaptcha/api.js"></script>

<p><button type="submit">Enviar</button></p>
</form>

<hr>

{mensajes_html}'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # Procesar formulario (misma ruta '/')
    elif path == '/' and method == 'POST':
        try:
            # Leer datos POST
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            
            # Parsear
            from urllib.parse import parse_qs
            params = parse_qs(post_data)
            
            nombre = params.get('nombre', [''])[0].strip()
            mensaje = params.get('mensaje', [''])[0].strip()
            recaptcha_token = params.get('g-recaptcha-response', [''])[0]
            
            # Validar
            if not nombre or not mensaje:
                html = '<h1>Error: Nombre y mensaje son requeridos</h1><a href="/">Volver</a>'
                start_response('200 OK', [('Content-Type', 'text/html')])
                return [html.encode('utf-8')]
            
            # Verificar reCAPTCHA
            if not verify_recaptcha(recaptcha_token):
                html = '<h1>Error: Verifica el reCAPTCHA</h1><a href="/">Volver</a>'
                start_response('200 OK', [('Content-Type', 'text/html')])
                return [html.encode('utf-8')]
            
            # Guardar en BD
            conn = get_db()
            if conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)",
                    (nombre, mensaje)
                )
                conn.commit()
                cur.close()
                conn.close()
            
            # Redirigir a la misma página (GET)
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except Exception as e:
            html = f'<h1>Error</h1><p>{str(e)}</p><a href="/">Volver</a>'
            start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
    
    # Página no encontrada
    else:
        html = '<h1>404 - Pagina no encontrada</h1><a href="/">Inicio</a>'
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
