import os
import psycopg2
from urllib.parse import urlparse

def application(environ, start_response):
    print("=== VERIFICACIÓN DATABASE_URL ===")
    
    # 1. Obtener TODAS las variables que comienzan con DATABASE o PG
    print("🔍 Buscando variables de base de datos...")
    for key in sorted(os.environ.keys()):
        if 'DATABASE' in key or key.startswith('PG'):
            value = os.environ[key]
            if 'PASS' in key or 'PASSWORD' in key:
                print(f"{key}: {'*' * len(value)}")
            else:
                print(f"{key}: {value}")
    
    # 2. Obtener DATABASE_URL específicamente
    DATABASE_URL = os.environ.get('DATABASE_URL')
    print(f"\n📋 DATABASE_URL encontrada: {'SI' if DATABASE_URL else 'NO'}")
    
    # 3. Si existe, analizarla
    if DATABASE_URL:
        print(f"🔗 Longitud: {len(DATABASE_URL)} caracteres")
        
        # Mostrar partes (ocultando contraseña)
        try:
            result = urlparse(DATABASE_URL)
            print(f"🌐 Host: {result.hostname}")
            print(f"🚪 Puerto: {result.port}")
            print(f"🗄️  Base de datos: {result.path[1:]}")
            print(f"👤 Usuario: {result.username}")
            print(f"🔐 Contraseña: {'*' * len(result.password) if result.password else 'NONE'}")
        except:
            print("⚠️ No se pudo parsear DATABASE_URL")
        
        # 4. Intentar conexión REAL
        print("\n🔄 Intentando conexión REAL...")
        try:
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
            print("🎉 ¡CONEXIÓN EXITOSA!")
            
            # Probar consulta simple
            cur = conn.cursor()
            cur.execute("SELECT 1 as test, current_timestamp as hora")
            resultado = cur.fetchone()
            print(f"✅ Consulta prueba: {resultado}")
            
            cur.close()
            conn.close()
            print("🔒 Conexión cerrada")
            
        except psycopg2.OperationalError as e:
            print(f"❌ Error de conexión: {e}")
        except Exception as e:
            print(f"❌ Error general: {type(e).__name__}: {e}")
    else:
        print("❌ DATABASE_URL NO está en las variables de entorno")
        print("💡 Verifica en Railway → Shared Variables")
    
    print("=== FIN VERIFICACIÓN ===")
    
    # HTML con resultados
    html = '''<h1>Verificación PostgreSQL</h1>
    <p>Revisa Railway Logs para ver los resultados.</p>
    <p>Busca "=== VERIFICACIÓN DATABASE_URL ==="</p>
    <h3>Posibles problemas:</h3>
    <ol>
    <li>DATABASE_URL no existe en Shared Variables</li>
    <li>DATABASE_URL tiene formato incorrecto</li>
    <li>La base de datos PostgreSQL no está corriendo</li>
    </ol>'''
    
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [html.encode('utf-8')]
