# SOLUCIÓN DEFINITIVA - Masonite 4 en Railway
# Esta versión inicializa la aplicación CORRECTAMENTE

from masonite.foundation import Application
from masonite.response import Response
from masonite.routes import Route

# 1. Crear aplicación e inicializar servicios esenciales
app = Application()

# 2. Registrar servicios básicos que Masonite necesita
from masonite.providers import (
    RouteProvider,
    ViewProvider,
    SessionProvider,
    ResponseProvider,
    RequestProvider,
    ServerProvider
)

# 3. Registrar los providers necesarios
app.register_providers([
    RouteProvider,
    ViewProvider, 
    SessionProvider,
    ResponseProvider,
    RequestProvider,
    ServerProvider
])

# 4. Inicializar los providers
for provider in app.get_providers():
    provider(app).register()
    provider(app).boot()

# 5. AHORA podemos obtener el router
router = app.make('router')

# 6. Añadir ruta
router.add(Route.get('/', lambda request: Response('''
<!DOCTYPE html>
<html>
<head>
    <title>✅ Masonite 4 en Railway</title>
    <style>
        body {
            text-align: center;
            margin-top: 100px;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
        }
        .success {
            color: #2ecc71;
            font-weight: bold;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 ¡Éxito Total!</h1>
        <p class="success">Masonite 4.20.2 funcionando en Railway</p>
        <p>Python 3.11 | Gunicorn 21.2.0</p>
        <p><small>Despliegue completado correctamente</small></p>
    </div>
</body>
</html>
''')))

# 7. WSGI entry point
application = app
