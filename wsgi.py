import os
import psycopg2
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # 1. CONFIGURACIÓN SIMPLE
    SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # 2. FUNCIÓN PARA CONECTAR A POSTGRESQL
    def conectar_db():
        if not DATABASE_URL:
            print("❌ No hay DATABASE_URL")
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
            print("✅ Conectado a PostgreSQL")
            return conn
        except Exception as e:
            print(f"❌ Error BD: {e}")
            return None
    
    # 3. SI ES POST (ENVIAR MENSAJE) - SIN VERIFICAR RECAPTCHA
    if path == '/' and method == 'POST':
        print("📨 Recibiendo POST...")
        try:
            # Leer datos del formulario
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            print(f"📝 Datos POST: {post_data[:100]}...")
            
            # Extraer nombre y mensaje
            from urllib.parse import parse_qs
            params = parse_qs(post_data)
            nombre = params.get('nombre', [''])[0].strip()
            mensaje = params.get('mensaje', [''])[0].strip()
            print(f"👤 Nombre: {nombre}, Mensaje: {mensaje}")
            
            # Validar
            if not nombre or not mensaje:
                print("⚠️ Nombre o mensaje vacío")
                html = '<h1>Error: Nombre y mensaje son requeridos</h1><a href="/">Volver</a>'
                start_response('200 OK', [('Content-Type', 'text/html')])
                return [html.encode('utf-8')]
            
            # Guardar en BD
            conn = conectar_db()
            if conn:
                try:
                    # Crear tabla si no existe
                    cur = conn.cursor()
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
                    print(f"💾 Guardado: {nombre} - {mensaje}")
                except Exception as e:
                    print(f"❌ Error guardando: {e}")
            
            # Redirigir a la página principal
            print("🔄 Redirigiendo a /")
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except Exception as e:
            print(f"🔥 Error POST: {e}")
            html = f'<h1>Error</h1><p>{str(e)}</p><a href="/">Volver</a>'
            start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
    
    # 4. PÁGINA PRINCIPAL (GET) - MUESTRA FORMULARIO Y MENSAJES
    elif path == '/' and method == 'GET':
        print("🏠 Página principal cargando...")
        
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
                
                print(f"📊 Mensajes encontrados: {len(rows)}")
                
                if rows:
                    mensajes_html = '<h3>Mensajes guardados:</h3><ul>'
                    for nombre, mensaje, fecha in rows:
                        fecha_str = str(fecha)[:19]  # Formato simple
                        mensajes_html += f'<li><strong>{nombre}</strong> ({fecha_str}): {mensaje}</li>'
                    mensajes_html += '</ul>'
                else:
                    mensajes_html = '<p>No hay mensajes aún. ¡Envía el primero!</p>'
            except Exception as e:
                print(f"❌ Error obteniendo mensajes: {e}")
                mensajes_html = '<p>Error cargando mensajes de la base de datos.</p>'
        else:
            mensajes_html = '<p>No hay conexión a la base de datos.</p>'
        
        # HTML completo SIN reCAPTCHA temporalmente
        html = f'''<h1>Formulario de Prueba</h1>
<p>Envía un mensaje (reCAPTCHA desactivado temporalmente):</p>

<form method="POST">
<p><strong>Nombre:</strong><br>
<input type="text" name="nombre" size="40"></p>

<p><strong>Mensaje:</strong><br>
<textarea name="mensaje" rows="4" cols="50"></textarea></p>

<p><button type="submit">Guardar Mensaje</button></p>
</form>

<hr>

{mensajes_html}

<p><small>Nota: reCAPTCHA desactivado para pruebas.</small></p>'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # 5. PÁGINA NO ENCONTRADA
    else:
        html = '<h1>404 - Página no encontrada</h1><a href="/">Ir al inicio</a>'
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
