# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@mysql.railway.internal:3306/railway')
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_SECURITY"

def hash_password(p): return hashlib.sha256((p or "").encode("utf-8")).hexdigest()
def b64url_encode(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode("utf-8")

def jwt_encode(p):
    h = b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode("utf-8"))
    py = b64url_encode(json.dumps(p).encode("utf-8"))
    s = hmac.new(JWT_SECRET.encode("utf-8"), f"{h}.{py}".encode("utf-8"), hashlib.sha256).digest()
    return f"{h}.{py}.{b64url_encode(s)}"

def verify_jwt(env):
    try:
        C = cookies.SimpleCookie(); C.load(env.get('HTTP_COOKIE', ''))
        t = C.get('token').value if 'token' in C else None
        if not t: return None
        p = json.loads(base64.urlsafe_b64decode(t.split('.')[1] + "==").decode("utf-8"))
        return p if p['exp'] > time.time() else None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

# =========================================================
# MAQUETACIÓN
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        menu_html = ""
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = f'<a href="/usuarios">👥 Usuarios</a>' if m_padre == "Seguridad" else ""
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        nav = f"""<div class="top-nav"><div class="nav-left"><span class="logo">🛡️ Clínica</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div><div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none; margin-left:10px;">Salir</a></div></div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 20px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b;}}
        .nav-left{{display:flex; gap:15px;}}
        .nav-link, .dropbtn{{color:#94a3b8; text-decoration:none; background:none; border:none; cursor:pointer;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:160px; border:1px solid #334155;}}
        .dropdown-content a{{color:white; padding:10px; display:block; text-decoration:none;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:20px;}}
        .card{{background:#1e293b; border-radius:8px; padding:20px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer;}}
        table{{width:100%; border-collapse:collapse; margin-top:15px;}}
        th, td{{text-align:left; padding:12px; border-bottom:1px solid #334155;}}
        input{{background:#0f172a; border:1px solid #334155; color:white; padding:8px; width:100%; margin-bottom:10px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # 🚨 RESCATE ROBUSTO: Intenta insertar el admin probando varios nombres de columna
    if path == "/login" or path == "/":
        try:
            conn = conectar_bd(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM usuarios")
            if cur.fetchone()[0] == 0:
                # Intentamos insertar solo con 'usuario' y 'password' que son los más comunes
                try: cur.execute("INSERT INTO usuarios (nombre_usuario, password) VALUES (%s, %s)", ('admin', hash_password('123456')))
                except: cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd) VALUES (%s, %s)", ('admin', hash_password('123456')))
                conn.commit()
            cur.close(); conn.close()
        except: pass

    # LOGIN
    if path in ["/", "/login"] and method == "GET":
        content = """<div class='card' style='max-width:300px; margin:80px auto; text-align:center;'>
            <h2>Login</h2><form id='fL'>
            <input name='u' placeholder='Usuario'>
            <input name='p' type='password' placeholder='Clave'>
            <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" style="transform:scale(0.8); margin-bottom:10px;"></div>
            <button type='button' onclick='doLogin()' class='btn-blue' style="width:100%">Entrar</button></form></div>
            <script>async function doLogin(){
                const res=await fetch('/api/login',{method:'POST', body:new FormData(document.getElementById('fL'))});
                const d=await res.json(); if(d.ok) location.href='/usuarios'; else alert('Error: Usuario no encontrado o columnas mal configuradas');
            }</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        # Búsqueda flexible de columnas
        cur.execute("SHOW COLUMNS FROM usuarios")
        cols = [c['Field'] for c in cur.fetchall()]
        u_col = 'nombre_usuario' if 'nombre_usuario' in cols else 'strNombreUsuario'
        p_col = 'password' if 'password' in cols else 'strPwd'
        
        cur.execute(f"SELECT * FROM usuarios WHERE {u_col}=%s AND {p_col}=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- GESTIÓN DE USUARIOS (EVITANDO ERRORES DE COLUMNA) ---
    if path == "/usuarios":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios")
        usrs = cur.fetchall()
        
        rows = ""
        for u in usrs:
            # Usamos .get() para que si la columna no existe, no explote el programa
            nom = u.get('nombre_usuario') or u.get('strNombreUsuario') or "N/A"
            mail = u.get('correo') or u.get('strCorreo') or "-"
            rows += f"<tr><td>{nom}</td><td>{mail}</td><td>Activo</td></tr>"

        content = f"<div class='card'><h2>Gestión de Usuarios</h2><table><tr><th>Usuario</th><th>Correo</th><th>Estado</th></tr>{rows}</table></div>"
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Usuarios", content, u_data).encode("utf-8")]

    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]
    
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Inicio", "<div class='card'><h2>Bienvenido</h2></div>", u_data).encode("utf-8")]