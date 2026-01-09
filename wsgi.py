import psycopg2

def application(environ, start_response):
    # === REEMPLAZA ESTO CON TU CONTRASEÑA REAL ===
    CONTRASEÑA_REAL = "YmbYQizQXChKLoqdVAORJvZiJMDCbLTt"  # ← PON AQUÍ TU CONTRASEÑA REAL
    
    # === NO MODIFIQUES NADA DEBAJO ===
    DATABASE_URL = f"postgresql://postgres:{CONTRASEÑA_REAL}@interchange.proxy.rlwy.net:31359/railway"
    
    print(f"🔗 Conectando a: interchange.proxy.rlwy.net:31359")
    
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        print("✅ Conexión exitosa a PostgreSQL")
        
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
        print("✅ Tabla 'mensajes' creada/verificada")
        
        # Procesar formulario si es POST
        if environ['REQUEST_METHOD'] == 'POST':
            try:
                # Leer datos del formulario
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
                
                # Extraer nombre y mensaje
                from urllib.parse import parse_qs
                params = parse_qs(post_data)
                nombre = params.get('nombre', [''])[0].strip()
                mensaje = params.get('mensaje', [''])[0].strip()
                
                if nombre and mensaje:
                    # Insertar en BD
                    cur.execute(
                        "INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)",
                        (nombre, mensaje)
                    )
                    print(f"💾 Mensaje guardado: {nombre}")
                
            except Exception as e:
                print(f"⚠️ Error procesando formulario: {e}")
        
        # Obtener todos los mensajes
        cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY fecha DESC")
        mensajes = cur.fetchall()
        print(f"📊 Mensajes en BD: {len(mensajes)}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Generar HTML con formulario y mensajes
        html = '''<h1>Formulario con PostgreSQL</h1>
        
<form method="POST">
<p><strong>Nombre:</strong><br>
<input type="text" name="nombre" required></p>

<p><strong>Mensaje:</strong><br>
<textarea name="mensaje" rows="3" required></textarea></p>

<p><button type="submit">Enviar Mensaje</button></p>
</form>

<hr>

<h3>Mensajes guardados:</h3>'''
        
        if mensajes:
            html += '<ul>'
            for nombre, mensaje, fecha in mensajes:
                fecha_str = str(fecha)[:16]
                html += f'<li><strong>{nombre}</strong> ({fecha_str}): {mensaje}</li>'
            html += '</ul>'
        else:
            html += '<p>No hay mensajes aún. ¡Envía el primero!</p>'
        
        html += '''<p><small>✅ PostgreSQL conectado correctamente</small></p>'''
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        html = f'''<h1>❌ Error de conexión</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <p>Verifica que la contraseña sea correcta en el código.</p>
        <p><small>Contraseña usada: {CONTRASEÑA_REAL[:3]}...</small></p>'''
    
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [html.encode('utf-8')]
