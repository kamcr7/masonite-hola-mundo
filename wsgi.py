import psycopg2

def application(environ, start_response):
    # REEMPLAZA ESTA CONTRASEÑA con la REAL
    CONTRASEÑA_REAL = "TU_CONTRASEÑA_AQUI"  # ← ¡PONLA AQUÍ!
    
    if CONTRASEÑA_REAL == "TU_CONTRASEÑA_AQUI":
        html = '''<h1>⚠️ Configura la contraseña</h1>
        <p>Reemplaza "TU_CONTRASEÑA_AQUI" en el código con tu contraseña real.</p>
        <p>Busca en Railway → Data → PostgreSQL → Raw psql command</p>'''
    else:
        DATABASE_URL = f"postgresql://postgres:{CONTRASEÑA_REAL}@interchange.proxy.rlwy.net:31359/railway"
        
        try:
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
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
            
            # Contar mensajes
            cur.execute("SELECT COUNT(*) FROM mensajes")
            count = cur.fetchone()[0]
            
            conn.commit()
            cur.close()
            conn.close()
            
            html = f'''<h1>✅ ¡CONEXIÓN EXITOSA!</h1>
            <p>PostgreSQL funcionando correctamente.</p>
            <p>Mensajes en BD: {count}</p>
            <form method="POST">
                <p>Nombre: <input type="text" name="nombre"></p>
                <p>Mensaje: <textarea name="mensaje"></textarea></p>
                <button>Enviar</button>
            </form>'''
            
        except Exception as e:
            html = f'''<h1>❌ Error de conexión</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>DATABASE_URL usada:</strong> postgresql://postgres:***@interchange.proxy.rlwy.net:31359/railway</p>
            <p>Verifica que la contraseña sea correcta.</p>'''
    
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [html.encode('utf-8')]
