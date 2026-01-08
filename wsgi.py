from masonite.app import App

# Crea la aplicación
application = App()

# Configura una ruta básica
@application.get('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>✅ Masonite en Railway</title>
        <style>
            body {
                text-align: center;
                margin-top: 100px;
                font-family: Arial, sans-serif;
            }
            h1 {
                color: #2ecc71;
            }
        </style>
    </head>
    <body>
        <h1>🚀 ¡Masonite funcionando en Railway!</h1>
        <p>La aplicación se ha desplegado correctamente.</p>
        <p><small>Python 3.11 | Masonite 4.20.2</small></p>
    </body>
    </html>
    '''
