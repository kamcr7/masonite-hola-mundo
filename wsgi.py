import os
import psycopg2
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # === 1. OBTENER DATABASE_URL DE RAILWAY ===
    # IMPORTANTE: Esta debe ser TU contraseña real
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Si no está en variables, usar la directa (como backup)
    if not DATABASE_URL:
        DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
        print("⚠️ Usando DATABASE_URL directa (no en variables)")
    else:
        print("✅ Usando DATABASE_URL de Railway Variables")
    
    print(f"🔗 Conectando a PostgreSQL...")
    
    try:
        # === 2. CONECTAR A POSTGRESQL ===
        result = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=result.hostname,
            database=result.path[1:],
            user=result.username,
            password=result.password,
            port=result.port,
            connect_timeout=5
        )
        print("✅ Conexión PostgreSQL exitosa")
        
        cur = conn.cursor()
        
        # === 3. CREAR TABLA SI NO EXISTE ===
        cur.execute('''
            CREATE TABLE IF NOT EXISTS mensajes (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100),
                mensaje TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # === 4. PROCESAR FORMULARIO (POST) ===
        if method == 'POST':
            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                
                from urllib.parse import parse_qs
                params = parse_qs(post_data)
                nombre = params.get('nombre', [''])[0].strip()
                mensaje = params.get('mensaje', [''])[0].strip()
                
                if nombre and mensaje:
                    cur.execute(
                        "INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)",
                        (nombre, mensaje)
                    )
                    print(f"💾 Guardado: {nombre}")
                    
            except Exception as e:
                print(f"⚠️ Error POST: {e}")
        
        # === 5. OBTENER MENSAJES ===
        cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY fecha DESC")
        mensajes = cur.fetchall()
        print(f"📊 Total mensajes: {len(mensajes)}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        # === 6. GENERAR HTML ===
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
        
    except Exception as e:
        print(f"❌ Error PostgreSQL: {e}")
        html = f'''<h1>Error de conexión</h1>
        <p>No se pudo conectar a la base de datos.</p>
        <p><small>Error: {str(e)[:100]}</small></p>'''
    
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [html.encode('utf-8')]
