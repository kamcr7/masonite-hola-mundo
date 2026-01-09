import psycopg2

def application(environ, start_response):
    # TU DATABASE_URL DIRECTA (copia desde Railway)
    DATABASE_URL = "postgresql://postgres:TU_CONTRASEÑA_REAL@interchange.proxy.rlwy.net:31359/railway"
    
    print(f"🔗 Usando DATABASE_URL directa")
    
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        print("🎉 ¡CONEXIÓN DIRECTA EXITOSA!")
        
        # Crear tabla y insertar prueba
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS prueba (
                id SERIAL PRIMARY KEY,
                mensaje TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute("INSERT INTO prueba (mensaje) VALUES ('Test desde Railway')")
        conn.commit()
        
        cur.execute("SELECT COUNT(*) FROM prueba")
        count = cur.fetchone()[0]
        print(f"📊 Registros en tabla prueba: {count}")
        
        cur.close()
        conn.close()
        
        html = f'<h1>✅ ¡Conexión exitosa!</h1><p>PostgreSQL funcionando. Registros: {count}</p>'
        
    except Exception as e:
        print(f"❌ Error: {e}")
        html = f'<h1>❌ Error conexión</h1><p>{str(e)}</p>'
    
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [html.encode('utf-8')]
