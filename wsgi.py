import os
from masonite import Application

app = Application()
application = app  # Para gunicorn

@app.route('/')
def welcome():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Masonite Minimal</title></head>
    <body style="text-align:center;margin-top:100px;">
    <h1>✅ Masonite funcionando</h1>
    <p>Versión mínima en Render.com</p>
    </body>
    </html>
    '''

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    from masonite.servers import Server
    Server().start(app, host='0.0.0.0', port=port)
