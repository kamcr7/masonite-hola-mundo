def application(environ, start_response):
    html = '''<h1>Prueba de Conexión</h1>
    <p>Si ves esto, la app funciona.</p>
    <p>Ahora revisa Railway Logs para ver los mensajes de conexión.</p>'''
    
    print("=== PRUEBA: App cargada ===")
    
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [html.encode('utf-8')]
