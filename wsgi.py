# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_V4" # Cambia esto para invalidar sesiones viejas

def hash_password(p): return hashlib.sha256((p or "").encode("utf-8")).hexdigest()
def b64url_encode(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode("utf-8")

def jwt_encode(p):
    h = b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode("utf-8"))
    py = b64url_encode(json.dumps(p).encode("utf-8"))
    msg = f"{h}.{py}".encode("utf-8")
    s = hmac.new(JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
    return f"{h}.{py}.{b64url_encode(s)}"

def verify_jwt(env):
    try:
        C = cookies.SimpleCookie(); C.load(env.get('HTTP_COOKIE', ''))
        t = C.get('token').value if 'token' in C else None
        if not t: return None
        # Decodificación segura
        parts = t.split('.')
        if len(parts) != 3: return None
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode("utf-8"))
        # Validar expiración e integridad de datos
        if payload.get('exp', 0) > time.time() and 'idp' in payload:
            return payload
        return None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4', consume_results=True)

# =========================================================
# LAYOUT CON FILTRADO DE MENÚ
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        # Solo mostrar módulos donde blnVer = 1 para el perfil del usuario
        cur.execute("""
            SELECT m.* FROM modulos m 
            JOIN permisos p ON m.id = p.idModulo 
            WHERE p.idPerfil = %s AND p.blnVer = 1
        """, (user['idp'],))
        mods_db = cur.fetchall()
        cur.close(); conn.close()
        
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_db if m['strMenuPadre'] == padre])

        s_links, p1_links, p2_links = get_links("Seguridad"), get_links("Principal 1"), get_links("Principal 2")

        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        {f'<div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{s_links}</div></div>' if s_links else ''}
        {f'<div class="dropdown"><button class="dropbtn">Procesos 1 ▾</button><div class="dropdown-content">{p1_links}</div></div>' if p1_links else ''}
        {f'<div class="dropdown"><button class="dropbtn">Procesos 2 ▾</button><div class="dropdown-content">{p2_links}</div></div>' if p2_links else ''}
        </div><div class="nav-right"><span class="user-pill">{user["u"]}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
        body {{ font-family:sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
        .logo {{ color:var(--emerald); font-weight:bold; font-size:1.2rem; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; padding:10px; font-size:14px; }}
        .dropdown {{ position:relative; display:inline-block; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:15px; cursor:pointer; font-size:14px; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border:1px solid var(--border); border-radius:8px; z-index:100; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }}
        .dropdown-content a {{ color:white; padding:12px; text-decoration:none; display:block; font-size:13px; border-bottom: 1px solid #334155; }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .container {{ padding:40px; max-width:1100px; margin:0 auto; }}
        .card {{ background:var(--card); padding:25px; border-radius:12px; border:1px solid var(--border); }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%; }}
        .user-pill {{ color:var(--emerald); background: rgba(16, 185, 129, 0.1); padding: 5px 12px; border-radius: 20px; font-size: 13px; margin-right: 15px; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 15px; border-radius:8px; font-size:13px; }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
        th, td {{ padding:12px; border-bottom: 1px solid var(--border); text-align:left; }}
    </style>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # --- LÓGICA DE LOGIN ---
    if path == "/login":
        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
                u = fs.getvalue("u")
                p = hash_password(fs.getvalue("p"))
                
                conn = conectar_bd(); cur = conn.cursor(dictionary=True)
                cur.execute("SELECT id, strNombreUsuario, idPerfil FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
                user = cur.fetchone(); cur.close(); conn.close()
                
                if user:
                    # Guardamos 'idp' explícitamente en el token
                    tk = jwt_encode({"u": user['strNombreUsuario'], "idp": user['idPerfil'], "exp": time.time()+3600})
                    start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
                    return [b'{"ok":true}']
                else:
                    start_response("200 OK", [("Content-Type", "application/json")])
                    return [b'{"ok":false, "msg":"Credenciales inválidas"}']
            except Exception as e:
                start_response("200 OK", [("Content-Type", "application/json")])
                return [json.dumps({"ok":false, "msg": str(e)}).encode("utf-8")]

        content = """<div class="card" style="width:320px; margin:100px auto;">
            <h2 style="text-align:center; color:var(--emerald)">🏥 SISTEMA</h2>
            <input id="un" placeholder="Usuario">
            <input id="up" type="password" placeholder="Contraseña">
            <button class="btn-emerald" onclick="doLogin()">INGRESAR</button>
        </div>
        <script>
            async function doLogin() {{
                const f = new FormData();
                f.append("u", document.getElementById("un").value);
                f.append("p", document.getElementById("up").value);
                const r = await fetch("/login", {{method:"POST", body:f}});
                const d = await r.json();
                if(d.ok) location.href="/dashboard"; else alert(d.msg);
            }}
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    # --- PROTECCIÓN GENERAL ---
    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- LOGOUT ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")])
        return [b""]

    # --- DASHBOARD / INICIO ---
    if path == "/dashboard" or path == "/":
        content = f"<div class='card'><h2>Bienvenido, {u_data['u']}</h2><p>Selecciona una opción del menú superior para comenzar. Solo verás los módulos autorizados para tu perfil.</p></div>"
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Inicio", content, u_data).encode("utf-8")]

    # --- OTRAS RUTAS (Permisos, etc.) ---
    # Aquí irían tus otras rutas (/permisos, /usuarios...) 
    # El layout filtrará automáticamente el menú basándose en u_data['idp']
    content = f"<div class='card'><h2>Módulo: {path}</h2><p>Contenido en desarrollo...</p></div>"
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode("utf-8")]