# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# Configuración de Conexión
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@mysql.railway.internal:3306/railway')
JWT_SECRET = "CLAVE_MAESTRA_2026"

def hash_password(p): return hashlib.sha256((p or "").encode("utf-8")).hexdigest()
def b64url_encode(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode("utf-8")

def jwt_encode(p):
    h = b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode("utf-8"))
    py = b64url_encode(json.dumps(p).encode("utf-8"))
    s = hmac.new(JWT_SECRET.encode("utf-8"), f"{h}.{py}".encode("utf-8"), hashlib.sha256).digest()
    return f"{h}.{py}.{b64url_encode(s)}"

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

# =========================================================
# FUNCIÓN DE REPARACIÓN DE TABLA (EJECUCIÓN AUTOMÁTICA)
# =========================================================
def reparar_y_crear_admin():
    try:
        conn = conectar_bd(); cur = conn.cursor()
        # 1. Aseguramos que la tabla tenga la estructura que el código espera
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                strNombreUsuario VARCHAR(100) NOT NULL,
                strPwd VARCHAR(255) NOT NULL,
                strCorreo VARCHAR(100),
                strEstado VARCHAR(20) DEFAULT 'Activo'
            )
        """)
        # 2. Limpiamos si hay basura y creamos el admin de cero
        cur.execute("DELETE FROM usuarios WHERE strNombreUsuario = 'admin'")
        cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, strEstado) VALUES (%s, %s, %s)", 
                   ('admin', hash_password('123456'), 'Activo'))
        conn.commit()
        cur.close(); conn.close()
        return True
    except Exception as e:
        return str(e)

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    # Intentar reparar la base de datos en cada carga de login para asegurar acceso
    if path in ["/", "/login"]:
        reparar_y_crear_admin()

    # VISTA DE LOGIN
    if path in ["/", "/login"] and method == "GET":
        html = """
        <html><body style="background:#0f172a; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
            <div style="background:#1e293b; padding:40px; border-radius:10px; border:1px solid #334155; width:300px; text-align:center;">
                <h2 style="color:#38bdf8;">Clínica Santa Mónica</h2>
                <p style="font-size:0.8rem; color:#94a3b8;">Acceso de Rescate Activado</p>
                <form action="/api/login" method="POST">
                    <input name="u" value="admin" style="width:100%; padding:10px; margin:10px 0; border-radius:5px; border:1px solid #334155; background:#0f172a; color:white;">
                    <input name="p" type="password" placeholder="Contraseña" style="width:100%; padding:10px; margin:10px 0; border-radius:5px; border:1px solid #334155; background:#0f172a; color:white;">
                    <button type="submit" style="width:100%; padding:10px; background:#2563eb; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">INGRESAR</button>
                </form>
            </div>
        </body></html>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [html.encode("utf-8")]

    # PROCESO DE LOGIN
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u = fs.getvalue("u")
        p = hash_password(fs.getvalue("p"))
        
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        # Buscamos con los nombres de columna exactos que acabamos de crear arriba
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("303 See Other", [("Location", "/dashboard"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [b""]
        else:
            start_response("200 OK", [("Content-Type", "text/html")]); 
            return [b"Error: No se pudo validar el usuario. Revisa los logs de Railway."]

    # DASHBOARD SIMPLE (Para probar que entraste)
    if path == "/dashboard":
        start_response("200 OK", [("Content-Type", "text/html")])
        return [b"<h1>BIENVENIDO ADMIN</h1><p>Has ingresado correctamente. <a href='/login'>Cerrar sesion</a></p>"]

    start_response("404 Not Found", []); return [b"Pagina no encontrada"]