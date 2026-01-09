import os
import psycopg2
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # 1. TU DATABASE_URL DE RAILWAY
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    print(f"🔗 DATABASE_URL recibida: {DATABASE_URL[:50]}...")
    
    # 2. CONEXIÓN A TU POSTGRESQL ESPECÍFICA
    def conectar_db():
        if not DATABASE_URL:
            print("❌ No hay DATABASE_URL")
            return None
        
        try:
            # Tu conexión específica
            result = urlparse(DATABASE_URL)
            print(f"🌐 Conectando a: {result.hostname}:{result.port}")
            
            conn = psycopg2.connect(
                host=result.hostname,
                database=result.path[1:],  # Quita el "/" inicial
                user=result.username,
                password=result.password,
                port=result.port
            )
            print("✅ ¡CONEXIÓN EXITOSA a PostgreSQL!")
            return conn
            
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {str(e)}")
            return None
    
    # 3. CREAR TABLA
    def crear_tabla():
        conn = conectar_db()
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
            print("✅ Tabla 'mensajes' creada/verificada")
            return True
        except Exception as e:
            print(f"❌ Error creando tabla: {e}")
            return False
    
    # 4. PÁGINA PRINCIPAL - FORMULARIO Y MENSAJES
    if path == '/' and method == 'GET':
        # Crear tabla si no existe
        crear_tabla()
        
        # Obtener mensajes
        mensajes_html = ''
        conn = conectar_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY fecha DESC LIMIT 20")
                rows = cur.fetchall()
                cur.close()
                conn.close()
                
                print(f"📊 Encontrados {len(rows)} mensajes")
                
                if rows:
                    mensajes_html = '<h3>Mensajes guardados:</h3><ul>'
                    for nombre, mensaje, fecha in rows:
                        fecha_str = str(fecha)[:16]  # Formato simple
                        mensajes_html += f'<li><strong>{nombre}</strong> ({fecha_str}): {mensaje}</li>'
                    mensajes_html += '</ul>'
                else:
                    mensajes_html = '<p>No hay mensajes aún. ¡Envía el primero!</p>'
                    
            except Exception as e:
                print(f"❌ Error leyendo mensajes: {e}")
                mensajes_html = '<p>Error leyendo base de datos.</p>'
        else:
            mensajes_html = '<p>No hay conexión a la base de datos.</p>'
        
        # HTML SIMPLE
        html = f'''<h1>Formulario Simple</h1>

<form method="POST">
<p><strong>Nombre:</strong><br>
<input type="text" name="nombre" size="40" required></p>

<p><strong>Mensaje:</strong><br>
<textarea name="mensaje" rows="4" cols="50" required></textarea></p>

<p><button type="submit">Guardar Mensaje</button></p>
</form>

<hr>

{mensajes_html}'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # 5. PROCESAR FORMULARIO
    elif path == '/' and method == 'POST':
        print("📨 Recibiendo mensaje...")
        
        try:
            # Leer datos
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            
            # Extraer
            from urllib.parse import parse_qs
            params = parse_qs(post_data)
            nombre = params.get('nombre', [''])[0].strip()
            mensaje = params.get('mensaje', [''])[0].strip()
            
            print(f"👤 Nombre: '{nombre}', Mensaje: '{mensaje}'")
            
            # Validar
            if not nombre or not mensaje:
                print("⚠️ Campos vacíos")
                html = '<h1>Error: Campos requeridos</h1><a href="/">Volver</a>'
                start_response('200 OK', [('Content-Type', 'text/html')])
                return [html.encode('utf-8')]
            
            # Guardar en BD
            conn = conectar_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)",
                        (nombre, mensaje)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    print(f"💾 Mensaje guardado en PostgreSQL")
                except Exception as e:
                    print(f"❌ Error guardando: {e}")
            else:
                print("⚠️ No se pudo conectar a BD para guardar")
            
            # Redirigir
            print("🔄 Redirigiendo...")
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except Exception as e:
            print(f"🔥 Error: {e}")
            html = f'<h1>Error del servidor</h1><p>{str(e)}</p><a href="/">Volver</a>'
            start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
            return [html.encode('utf-8')]
    
    # 6. 404
    else:
        html = '<h1>404</h1><a href="/">Inicio</a>'
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
