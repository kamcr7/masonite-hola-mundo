import os
import sys

# Aplicar parche
try:
    exec(open('masonite_fix.py').read())
except:
    pass

from masonite import Application
app = Application()
application = app

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Masonite Render</title>
    <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-r from-blue-500 to-purple-600 min-h-screen flex items-center justify-center">
    <div class="bg-white/90 p-12 rounded-3xl text-center">
    <h1 class="text-4xl font-bold mb-4">🎉 ¡Masonite en Render!</h1>
    <p class="text-xl mb-6">Funcionando con Python 3.13</p>
    <p class="text-green-600 font-bold">✅ DEPLOY EXITOSO</p>
    </div>
    </body>
    </html>
    '''

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    from masonite.servers import Server
    Server().start(app, host='0.0.0.0', port=port)
