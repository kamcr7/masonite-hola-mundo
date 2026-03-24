# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_SISTEMA_EMPRESA_2026"

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
# MAQUETACIÓN GLOBAL CON DISEÑO PREMIUM
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        # Menús con diseño de tu captura image_c6efc7.png
        menu_html = ""
        for m_padre in ["Seguridad", "Principal 1", "Principal 2", "prueba"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a><a href="/usuarios">👥 Usuarios</a><a href="/permisos">🔐 Permisos</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        
        nav = f"""<div class="top-nav">
            <div class="nav-container">
                <div class="nav-left"><span class="logo">🏢 EMPRESA</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div>
                <div class="nav-right">
                    <span class="user-pill">{user['u']}</span>
                    <a href="/logout" class="btn-salir">Salir</a>
                </div>
            </div>
        </div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        :root {{ --bg: #0f172a; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
        body {{ font-family:'Segoe UI', sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        
        /* NAVBAR */
        .top-nav {{ background:#0b1120; height:65px; border-bottom:1px solid var(--border); position:sticky; top:0; z-index:100; }}
        .nav-container {{ max-width:1400px; margin:0 auto; display:flex; justify-content:space-between; align-items:center; height:100%; padding:0 20px; }}
        .nav-left {{ display:flex; gap:10px; align-items:center; }}
        .logo {{ font-weight:bold; color:var(--emerald); font-size:1.2rem; margin-right:20px; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; font-size:0.9rem; padding:10px; }}
        
        /* DROPDOWNS */
        .dropdown {{ position:relative; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:22px 12px; cursor:pointer; font-size:0.9rem; font-family:inherit; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border-radius:8px; border:1px solid var(--border); box-shadow:0 10px 15px rgba(0,0,0,0.4); }}
        .dropdown-content a {{ color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem; }}
        .dropdown-content a:hover {{ background:#334155; color:var(--emerald); }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .dropdown:hover .dropbtn {{ color:white; }}

        .btn-salir {{ background:#ef4444; color:white; padding:7px 15px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:0.8rem; margin-left:10px; }}
        .user-pill {{ background:rgba(16,185,129,0.1); color:var(--emerald); padding:5px 12px; border-radius:20px; font-size:0.85rem; border:1px solid rgba(16,185,129,0.2); }}

        /* CONTENEDORES */
        .container {{ padding:40px 20px; max-width:1100px; margin:0 auto; }}
        .card {{ background:var(--card); border-radius:16px; padding:30px; border:1px solid var(--border); box-shadow:0 4px 6px rgba(0,0,0,0.1); }}
        
        /* TABLAS (image_c6f006.png style) */
        table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
        th {{ text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid var(--border); }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:0.95rem; }}
        .btn-action {{ color:#38bdf8; text-decoration:none; margin-right:15px; font-weight:600; font-size:0.85rem; }}
        .btn-delete {{ color:#ef4444; text-decoration:none; font-weight:600; font-size:0.85rem; }}
        
        /* LOGIN ESPECIFICO */
        .login-card {{ width:400px; margin:80px auto; text-align:center; }}
        .icon-circle {{ background:rgba(16,185,129,0.1); width:60px; height:60px; border-radius:14px; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; color:var(--emerald); font-size:24px; border:1px solid rgba(16,185,129,0.3); }}
        .test-box {{ background:rgba(16,185,129,0.05); border:1px solid rgba(16,185,129,0.2); border-radius:10px; padding:15px; margin-bottom:20px; text-align:left; font-size:0.85rem; }}
        input {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; border-radius:8px; width:100%; margin-bottom:15px; box-sizing:border-box; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:12px; width:100%; border-radius:8px; cursor:pointer; font-weight:bold; }}
    </style>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # PANTALLA 1: LOGIN
    if path in ["/", "/login"] and method == "GET":
        content = """<div class="card login-card">
            <div class="icon-circle">🛡️</div>
            <h2 style="margin:0;">Sistema de Gestión</h2>
            <p style="color:#94a3b8; margin-bottom:25px;">Ingresa tus credenciales</p>
            <div class="test-box">
                <b style="color:var(--emerald); display:block; margin-bottom:5px;">Acceso Rápido:</b>
                Usuario: <code style="color:white;">admin</code> | Clave: <code style="color:white;">123</code>
            </div>
            <form id="fL">
                <input name="u" placeholder="Usuario" required>
                <input name="p" type="password" placeholder="Contraseña" required>
                <div style="margin-bottom:20px; display:flex; justify-content:center;">
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div>
                </div>
                <button type="button" onclick="doLogin()" class="btn-emerald">Iniciar Sesión</button>
            </form>
        </div>
        <script>
            async function doLogin() {
                const c = grecaptcha.getResponse(); 
                if(!c) { alert("Completa el captcha"); return; }
                const res = await fetch('/api/login', { method:'POST', body:new FormData(document.getElementById('fL')) });
                const data = await res.json(); 
                if(data.ok) location.href='/dashboard'; else alert('Error de acceso');
            }
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Acceso", content).encode("utf-8")]

    # API LOGIN
    if path == "/api/login":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly; SameSite=Lax")])
            return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # PANTALLA 2: DASHBOARD (image_c6efc7.png style)
    if path == "/dashboard":
        content = f"""<div class="card" style="text-align:center; max-width:600px; margin:40px auto;">
            <div style="background:rgba(16,185,129,0.1); width:80px; height:80px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; font-size:32px;">👤</div>
            <h1 style="margin:0; font-size:1.8rem;">Bienvenido al Sistema</h1>
            <h2 style="color:var(--emerald); margin:10px 0;">{u_data['u']} - <span style="color:#94a3b8; font-size:1.1rem;">ADMINISTRADOR</span></h2>
            <p style="color:#94a3b8;">Selecciona un módulo en el menú superior para comenzar.</p>
        </div>"""

    # PANTALLA 3: USUARIOS / PERFILES (image_c6f006.png style)
    elif path == "/perfiles" or path == "/usuarios":
        title_text = "Gestión de Usuarios" if path == "/usuarios" else "Gestión de Perfiles"
        btn_text = "+ Nuevo Usuario" if path == "/usuarios" else "+ Nuevo Perfil"
        
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios" if path == "/usuarios" else "SELECT 'ADMINISTRADOR' as nom UNION SELECT 'VENTAS' UNION SELECT 'Edelion'")
        rows_data = cur.fetchall(); cur.close(); conn.close()
        
        rows_html = ""
        for r in rows_data:
            name = r.get('strNombreUsuario') or r.get('nom')
            rows_html += f"<tr><td>{name}</td><td style='text-align:right;'><a href='#' class='btn-action'>Editar</a><a href='#' class='btn-delete'>Eliminar</a></td></tr>"

        content = f"""<div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h2 style="margin:0;">{title_text}</h2>
                <button class="btn-emerald" style="width:auto; padding:8px 20px;">{btn_text}</button>
            </div>
            <table><thead><tr><th>Nombre</th><th style="text-align:right;">Acciones</th></tr></thead>
            <tbody>{rows_html}</tbody></table>
        </div>"""

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]

    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]