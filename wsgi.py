# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
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
# MAQUETACIÓN GLOBAL
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        menu_html = ""
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos</a><a href="/usuarios">👥 Usuarios</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        
        nav = f"""<div class="top-nav">
            <div class="nav-container">
                <div class="nav-left"><span class="logo">🛡️ Clínica Santa Mónica</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div>
                <div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div>
            </div>
        </div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        :root {{ --bg: #0f172a; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
        body {{ font-family:'Segoe UI', sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#0b1120; height:65px; border-bottom:1px solid var(--border); position:sticky; top:0; z-index:100; }}
        .nav-container {{ max-width:1400px; margin:0 auto; display:flex; justify-content:space-between; align-items:center; height:100%; padding:0 20px; }}
        .logo {{ font-weight:bold; color:var(--emerald); font-size:1.2rem; margin-right:20px; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; font-size:0.9rem; padding:10px; }}
        .dropdown {{ position:relative; display:inline-block; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:22px 12px; cursor:pointer; font-size:0.9rem; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border-radius:8px; border:1px solid var(--border); box-shadow:0 10px 15px rgba(0,0,0,0.4); }}
        .dropdown-content a {{ color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem; }}
        .dropdown-content a:hover {{ background:#334155; color:var(--emerald); }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .container {{ padding:40px 20px; max-width:1100px; margin:0 auto; }}
        .card {{ background:var(--card); border-radius:16px; padding:30px; border:1px solid var(--border); box-shadow:0 4px 6px rgba(0,0,0,0.1); margin-bottom:20px; }}
        table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
        th {{ text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid var(--border); }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:0.95rem; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-outline {{ background:transparent; border:1px solid var(--border); color:#94a3b8; padding:6px 12px; border-radius:6px; cursor:pointer; margin-right:5px; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; }}
        .user-pill {{ background:rgba(16,185,129,0.1); color:var(--emerald); padding:5px 12px; border-radius:20px; font-size:0.85rem; border:1px solid rgba(16,185,129,0.2); }}
        .btn-salir {{ background:#ef4444; color:white; padding:7px 15px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:0.8rem; margin-left:10px; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:10px; border-radius:8px; width:100%; box-sizing:border-box; }}
    </style>
    <script>
        function setAll() {{ document.querySelectorAll('input[type="checkbox"]').forEach(c => c.checked = true); }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # LOGIN
    if path in ["/", "/login"] and method == "GET":
        content = """<div class="card" style="width:400px; margin:80px auto; text-align:center;">
            <div style="font-size:40px; margin-bottom:10px;">🛡️</div>
            <h2>Acceso al Sistema</h2>
            <form id="fL">
                <input name="u" type="text" placeholder="Usuario" style="margin-bottom:15px;" required>
                <input name="p" type="password" placeholder="Contraseña" style="margin-bottom:15px;" required>
                <div style="margin-bottom:20px; display:flex; justify-content:center;">
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div>
                </div>
                <button type="button" onclick="doLogin()" class="btn-emerald" style="width:100%;">Iniciar Sesión</button>
            </form>
        </div>
        <script>
            async function doLogin() {
                const c = grecaptcha.getResponse(); 
                if(!c) { alert("Completa el captcha"); return; }
                const form = document.getElementById('fL');
                const res = await fetch('/api/login', { method:'POST', body:new FormData(form) });
                const data = await res.json(); 
                if(data.ok) location.href='/dashboard'; else alert('Usuario o clave incorrectos');
            }
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    # API LOGIN (CORREGIDO)
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)
        u = fs.getvalue("u")
        p = hash_password(fs.getvalue("p"))
        
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

    # VISTAS CON CRUD Y SELECCIÓN
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/usuarios":
        cur.execute("SELECT * FROM usuarios")
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strEstado']}</td><td><button class='btn-outline'>Editar</button><button class='btn-red'>Borrar</button></td></tr>" for u in cur.fetchall()])
        content = f"<h2>👥 Gestión de Usuarios</h2><div class='card'><button class='btn-emerald'>+ Nuevo Usuario</button><table><thead><tr><th>Usuario</th><th>Correo</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>"

    elif path == "/perfiles":
        # Simulación de tabla perfiles si no existe, o consulta real
        try: cur.execute("SELECT * FROM perfiles")
        except: cur.execute("SELECT 1 as id, 'ADMINISTRADOR' as strNombrePerfil UNION SELECT 2, 'VENTAS'")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-outline'>Editar</button></td></tr>" for p in cur.fetchall()])
        content = f"<h2>👤 Perfiles</h2><div class='card'><button class='btn-emerald'>+ Nuevo Perfil</button><table><thead><tr><th>ID</th><th>Perfil</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>"

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td><button class='btn-red'>Eliminar</button></td></tr>" for m in cur.fetchall()])
        content = f"<h2>📦 Módulos</h2><div class='card'><table><thead><tr><th>Nombre</th><th>Ruta</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>"

    elif path == "/permisos":
        # Selector de perfil solicitado
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        # Perfiles para el selector
        try: cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        except: perfs = [{'id':1, 'strNombrePerfil':'ADMINISTRADOR'}, {'id':2, 'strNombrePerfil':'VENTAS'}]
        
        opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = "".join([f"<tr><td><b>{m['strNombreModulo']}</b></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        
        content = f"""<div class="card">
            <h2>🔐 Matriz de Permisos</h2>
            <div style="display:flex; gap:20px; align-items:center; background:var(--bg); padding:15px; border-radius:10px; margin-bottom:20px;">
                <div style="flex:1">
                    <label style="font-size:0.8rem; color:#94a3b8;">Seleccionar Perfil para Autorizar:</label>
                    <select>{opts}</select>
                </div>
                <button onclick="setAll()" class="btn-emerald">Marcar Todos</button>
                <button class="btn-emerald" style="background:#2563eb;">Guardar Permisos</button>
            </div>
            <table><thead><tr><th>Módulo</th><th>Crear</th><th>Editar</th><th>Eliminar</th><th>Ver</th></tr></thead><tbody>{m_rows}</tbody></table>
        </div>"""
    
    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]
    
    else:
        content = f"<div class='card' style='text-align:center;'><h1>🏠 Dashboard</h1><p>Sesión activa: <b>{u_data['u']}</b></p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]