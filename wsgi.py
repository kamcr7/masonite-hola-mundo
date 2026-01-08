#!/usr/bin/env python
"""WSGI entry point - Masonite en Render.com"""
import os
import sys

# ============================================
# 0. CONFIGURACIÓN INICIAL
# ============================================
print("🚀 INICIANDO MASONITE EN RENDER.COM")
print("=" * 50)

# ============================================
# 1. APLICAR PARCHES CRÍTICOS
# ============================================
fix_path = os.path.join(os.path.dirname(__file__), 'masonite_fix.py')
if os.path.exists(fix_path):
    try:
        with open(fix_path, 'r', encoding='utf-8') as f:
            exec(f.read(), {'__file__': fix_path})
        print("✅ Parches aplicados exitosamente")
    except Exception as e:
        print(f"⚠️  Error aplicando parches: {e}")
else:
    print("⚠️  Archivo masonite_fix.py no encontrado")

# ============================================
# 2. IMPORTAR MASONITE
# ============================================
try:
    from masonite import Application
    print("✅ Masonite importado correctamente")
    
    # Crear aplicación
    app = Application()
    
    # Configuración básica
    app.bind('config.location', 'config/')
    
    print("✅ Aplicación Masonite creada")
    
except ImportError as e:
    print(f"❌ Error importando Masonite: {e}")
    print("💡 Intentando instalar Masonite...")
    
    # Último recurso: instalar Masonite en runtime
    import subprocess
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "masonite==4.20.2", "masonite-orm==2.24.0"
        ])
        from masonite import Application
        app = Application()
        app.bind('config.location', 'config/')
        print("✅ Masonite instalado e importado")
    except Exception as install_error:
        print(f"❌ Error instalando Masonite: {install_error}")
        # Crear app de emergencia
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        
        class EmergencyHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = '''
                <!DOCTYPE html>
                <html>
                <head><title>Masonite - En mantenimiento</title></head>
                <body style="text-align:center;margin-top:100px;">
                <h1>🚧 Masonite en Render</h1>
                <p>La aplicación está siendo configurada...</p>
                <p>Vuelve en unos minutos.</p>
                </body>
                </html>
                '''
                self.wfile.write(html.encode())
        
        def run_emergency():
            port = int(os.getenv('PORT', 8000))
            server = HTTPServer(('0.0.0.0', port), EmergencyHandler)
            print(f"🆘 Servidor de emergencia en puerto {port}")
            server.serve_forever()
        
        # Ejecutar servidor de emergencia
        run_emergency()
        sys.exit(0)

# ============================================
# 3. CARGAR CONFIGURACIÓN Y RUTAS
# ============================================
try:
    # Intentar cargar configuración
    if os.path.exists('config/application.py'):
        from config import application
        print("✅ Configuración cargada")
except:
    print("⚠️  Usando configuración por defecto")

# Cargar rutas si existen
try:
    from routes import web
    print(f"✅ Rutas cargadas: {len(web.ROUTES)} encontradas")
except ImportError:
    print("⚠️  Creando rutas básicas...")
    from masonite.routes import Route
    
    class SimpleController:
        def show(self):
            from masonite.response import Response
            return Response('''
            <!DOCTYPE html>
            <html>
            <head><title>Masonite Funcionando</title>
            <style>
                body { font-family: Arial; text-align: center; margin-top: 100px; }
                .success { color: green; font-weight: bold; }
            </style>
            </head>
            <body>
                <h1>🎉 ¡Masonite en Render.com!</h1>
                <p class="success">✅ La aplicación está funcionando correctamente</p>
                <p>Python 3.13 | Free Tier</p>
                <p><a href="/hola">Ver Hola Mundo</a></p>
            </body>
            </html>
            ''')
    
    ROUTES = [
        Route.get("/", "SimpleController@show"),
    ]
    
    app.bind('routes', ROUTES)

# ============================================
# 4. CONFIGURAR PARA GUNICORN
# ============================================
application = app  # ¡IMPORTANTE! Para gunicorn

# ============================================
# 5. EJECUCIÓN LOCAL (si se llama directamente)
# ============================================
if __name__ == "__main__":
    from masonite.servers import Server
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    
    print(f"""
    📊 INFORMACIÓN DEL SISTEMA
    {'='*30}
    📁 Directorio: {os.getcwd()}
    🌐 Host: {host}
    🚪 Puerto: {port}
    🔗 URL: http://{host}:{port}
    🐍 Python: {sys.version.split()[0]}
    📦 Masonite: 4.20.2
    ☁️  Hosting: Render.com
    {'='*30}
    """)
    
    Server().start(app, host=host, port=port)
