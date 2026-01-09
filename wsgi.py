import sys
print(f"Python: {sys.version}")

try:
    import psycopg2
    print(f"✅ psycopg2: {psycopg2.__version__}")
except:
    print("❌ psycopg2 NO instalado")
    
print("=== FIN ===")

def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Check Railway logs']
