import os
import psycopg2
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Tu DATABASE_URL (usa la misma que ya funciona)
    DATABASE_URL = os.environ.get('DATABASE_URL', "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway")
    
    # Función para conectar
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
    
    # === RUTA PARA BORRAR TODO ===
    if path == '/borrar' and method == 'GET':
        try:
            conn = conectar_bd()
            if conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM mensajes")
                conn.commit()
                cur.close()
                conn.close()
                mensaje = 'Todos los mensajes han sido borrados.'
            else:
                mensaje = 'No hay conexión a la base de datos.'
        except Exception as e:
            mensaje = f'Error: {str(e)}'
        
        html = f'''<h1>Borrar Mensajes</h1>
<p>{mensaje}</p>
<p><a href="/">← Volver al formulario</a></p>'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # === PÁGINA PRINCIPAL ===
    elif path == '/' and method == 'GET':
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
        
        # HTML con botón para borrar
        html = f'''<h1>Formulario</h1>

<form method="POST">
<p>Nombre: <input type="text" name="nombre" required></p>
<p>Mensaje: <textarea name="mensaje" rows="3" required></textarea></p>
<p><button type="submit">Enviar</button></p>
</form>

<hr>

<h3>Mensajes:</h3>
{mensajes_html}

<p><a href="/borrar" style="color:red;">⚠️ Borrar todos los mensajes</a></p>'''
        
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
            
            if not nombre or not mensaje:
                start_response('302 Found', [('Location', '/')])
                return [b'Redirecting...']
            
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
            
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except:
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
    
    else:
        html = '<h1>404</h1><a href="/">Inicio</a>'
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
