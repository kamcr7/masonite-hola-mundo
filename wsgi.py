import os
import psycopg2
import requests
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Configuración reCAPTCHA
    SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # Conexión PostgreSQL
    def conectar_db():
        if not DATABASE_URL:
            return None
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
    
    # Verificar reCAPTCHA
    def verificar_recaptcha(token):
        if not token:
            return False
        
        # Si son claves de prueba, siempre válido
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
    
    # Página principal - TODO en una página
    if path == '/' and method == 'GET':
        # Obtener mensajes guardados
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
                        fecha_str = str(fecha)[:16]
                        mensajes_html += f'<li><strong>{nombre}</strong> ({fecha_str}): {mensaje}</li>'
                    mensajes_html += '</ul>'
                else:
                    mensajes_html = '<p>No hay mensajes.</p>'
            except:
                mensajes_html = '<p>Error cargando mensajes.</p>'
        
        # HTML simple
        html = f'''<h1>Formulario con reCAPTCHA</h1>

<form method="POST">
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
    
    # Procesar formulario
    elif path == '/' and method == 'POST':
        try:
            # Leer datos
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            
            # Extraer
            from urllib.parse import parse_qs
            params = parse_qs(post_data)
            
            nombre = params.get('nombre', [''])[0].strip()
            mensaje = params.get('mensaje', [''])[0].strip()
            recaptcha_token = params.get('g-recaptcha-response', [''])[0]
            
            # Validar campos
            if not nombre or not mensaje:
                html = '<h1>Error</h1><p>Nombre y mensaje son requeridos.</p><a href="/">Volver</a>'
                start_response('200 OK', [('Content-Type', 'text/html')])
                return [html.encode('utf-8')]
            
            # Verificar reCAPTCHA
            if not verificar_recaptcha(recaptcha_token):
                html = '<h1>Error</h1><p>Por favor verifica el reCAPTCHA.</p><a href="/">Volver</a>'
                start_response('200 OK', [('Content-Type', 'text/html')])
                return [html.encode('utf-8')]
            
            # Guardar en PostgreSQL
            conn = conectar_db()
            if conn:
                try:
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
                    
                    # Insertar mensaje
                    cur.execute(
                        "INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)",
                        (nombre, mensaje)
                    )
                    
                    conn.commit()
                    cur.close()
                    conn.close()
                except:
                    pass
            
            # Redirigir a la página principal
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except Exception as e:
            html = f'<h1>Error</h1><p>{str(e)}</p><a href="/">Volver</a>'
            start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
    
    # Página no encontrada
    else:
        html = '<h1>404</h1><p><a href="/">Inicio</a></p>'
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
