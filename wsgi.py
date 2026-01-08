from masonite.foundation import Application, Bootstrapper
from masonite.response import Response
from masonite.routes import Route

# Crea la aplicación
app = Application()

# Configuración básica
app.bind('request', {})
app.bind('response', Response)

# Define una ruta simple
@app.get('/')
def home(request):
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>✅ Masonite 4 en Railway</title>
        <style>
            body { text-align: center; margin-top: 100px; font-family: Arial; }
            h1 { color: #2ecc71; }
            .success { color: #27ae60; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🚀 ¡Éxito Total!</h1>
        <p class="success">Masonite 4.20.2 funcionando en Railway</p>
        <p>Python 3.11 | Gunicorn 21.2.0</p>
        <p><small>Despliegue completado correctamente</small></p>
    </body>
    </html>
    '''

# WSGI entry point
application = app
