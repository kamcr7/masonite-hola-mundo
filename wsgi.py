import os
import psycopg2
import requests
from urllib.parse import urlparse
from datetime import datetime

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # ========== CONFIGURACIÓN ==========
    # reCAPTCHA desde Railway Variables
    SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
    
    # PostgreSQL desde Railway Variables
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # ========== FUNCIONES ==========
    
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
        except Exception as e:
            print(f"Database error: {e}")
            return None
    
    # Crear tabla si no existe
    def init_database():
        conn = get_db()
        if not conn:
            return False
        
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
            return True
        except:
            return False
    
    # Verificar reCAPTCHA
    def verify_recaptcha(token):
        if not token:
            return False
        
        # Claves de prueba siempre válidas
        if SECRET_KEY == '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe':
            return True
        
        # Verificar con Google
        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={'secret': SECRET_KEY, 'response': token},
                timeout=5
            )
            return response.json().get('success', False)
        except:
            return False
    
    # ========== RUTAS ==========
    
    # Página principal - Formulario simple
    if path == '/' and method == 'GET':
        # Inicializar BD
        init_database()
        
        html = f'''<h1>Formulario con reCAPTCHA y PostgreSQL</h1>

<form method="POST" action="/enviar">
<p><input type="text" name="nombre" placeholder="Tu nombre" required></p>
<p><textarea name="mensaje" placeholder="Tu mensaje" rows="3" required></textarea></p>

<div class="g-recaptcha" data-sitekey="{SITE_KEY}"></div>
<script src="https://www.google.com/recaptcha/api.js"></script>

<p><button type="submit">Enviar</button></p>
</form>

<p><a href="/ver">Ver mensajes guardados</a></p>
<p><a href="/borrar">Borrar todos los mensajes</a></p>'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # Procesar formulario
    elif path == '/enviar' and method == 'POST':
        try:
            # Leer datos POST
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            
            # Parsear datos
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
            
            # Guardar en PostgreSQL
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
            
            # Éxito
            html = f'''<h1>✅ Mensaje enviado</h1>
<p>Gracias {nombre}, tu mensaje ha sido guardado.</p>
<p><a href="/">Enviar otro</a> | <a href="/ver">Ver todos</a></p>'''
            
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
            
        except Exception as e:
            html = f'<h1>Error</h1><p>{str(e)}</p><a href="/">Volver</a>'
            start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
    
    # Ver mensajes guardados
    elif path == '/ver' and method == 'GET':
        mensajes = []
        conn = get_db()
        
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY fecha DESC")
                
                for row in cur.fetchall():
                    fecha = row[2]
                    if isinstance(fecha, str):
                        fecha_str = fecha
                    else:
                        fecha_str = fecha.strftime('%Y-%m-%d %H:%M')
                    
                    mensajes.append(f'<li><b>{row[0]}</b> ({fecha_str}): {row[1]}</li>')
                
                cur.close()
                conn.close()
            except Exception as e:
                mensajes = [f'<li>Error: {str(e)}</li>']
        
        if not mensajes:
            lista = '<p>No hay mensajes aún.</p>'
        else:
            lista = f'<ul>{"".join(mensajes)}</ul>'
        
        html = f'''<h1>📝 Mensajes guardados</h1>
{lista}
<p><a href="/">← Volver al formulario</a></p>'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # Borrar todos los mensajes (para testing)
    elif path == '/borrar' and method == 'GET':
        conn = get_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM mensajes")
                conn.commit()
                cur.close()
                conn.close()
                mensaje = '✅ Todos los mensajes borrados.'
            except Exception as e:
                mensaje = f'❌ Error: {str(e)}'
        else:
            mensaje = '❌ No hay conexión a la base de datos.'
        
        html = f'''<h1>Borrar mensajes</h1>
<p>{mensaje}</p>
<p><a href="/">← Volver</a></p>'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # Página no encontrada
    else:
        html = '<h1>404</h1><p><a href="/">Inicio</a></p>'
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
