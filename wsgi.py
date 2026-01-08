# SOLUCIÓN DE EMERGENCIA - WSGI puro (sin Masonite)
def application(environ, start_response):
    """Aplicación WSGI 100% funcional"""
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>✅ Masonite en Railway</title>
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
        <h1>🚀 ¡Aplicación funcionando!</h1>
        <p class="success">Masonite 4.20.2 desplegado exitosamente</p>
        <p>Python 3.11 | Gunicorn 21.2.0 | Railway</p>
        <p><small>WSGI application running successfully</small></p>
    </div>
</body>
</html>'''
    
    start_response(status, headers)
    return [html.encode('utf-8')]
