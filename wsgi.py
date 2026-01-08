def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    
    html = '''<h1>Hola Mundo</h1>
<p>Masonite en Railway</p>'''
    
    start_response(status, headers)
    return [html.encode('utf-8')]
