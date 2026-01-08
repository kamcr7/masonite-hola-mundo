from masonite import Application
app = Application()
application = app

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Masonite Railway</title>
    <style>body{text-align:center;margin-top:100px;}</style>
    </head>
    <body>
    <h1>✅ Masonite en Railway</h1>
    <p>Configuración mínima exitosa</p>
    </body>
    </html>
    '''
