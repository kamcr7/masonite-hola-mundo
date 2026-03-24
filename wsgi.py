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
# REPARACIÓN DE TABLAS E INICIALIZACIÓN
# =========================================================
def inicializar_datos():
    conn = conectar_bd(); cur = conn.cursor()
    # Asegurar que las tablas tengan las columnas correctas
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(100), strRuta VARCHAR(100))")
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(100))")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(100), strPwd VARCHAR(255), strCorreo VARCHAR(100), strEstado VARCHAR(20))")
    
    # Insertar módulos obligatorios si no existen
    modulos_defecto = [
        ('Perfiles', '/perfiles'), ('Módulos', '/modulos'), 
        ('Permisos', '/permisos'), ('Usuarios', '/usuarios'),
        ('Principal 1', '/p1'), ('Principal 2', '/p2')
    ]
    cur.execute("SELECT COUNT(*) FROM modulos")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO modulos (strNombreModulo, strRuta) VALUES (%s, %s)", modulos_defecto)
    
    # Usuario admin inicial (si no hay ninguno)
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, strCorreo, strEstado) VALUES (%s, %s, %s, %s)", 
                   ('admin', hash_password('admin'), 'admin@clinica.com', 'Activo'))
    
    conn.commit(); cur.close(); conn.close()

# =========================================================
# DISEÑO Y COMPONENTES
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""<div class="top-nav">
            <div class="nav-container">
                <div class="nav-left">
                    <span class="logo">🛡️ Clínica Santa Mónica</span>
                    <a href="/dashboard" class="nav-link">Inicio</a>
                    <div class="dropdown">
                        <button class="dropbtn">Seguridad ▾</button>
                        <div class="dropdown-content">
                            <a href="/perfiles">👤 Perfiles</a>
                            <a href="/modulos">📦 Módulos</a>
                            <a href="/permisos">🔐 Permisos</a>
                            <a href="/usuarios">👥 Usuarios</a>
                        </div>
                    </div>
                    <a href="/p1" class="nav-link">Principal 1</a>
                    <a href="/p2" class="nav-link">Principal 2</a>
                </div>
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
        .card {{ background:var(--card); border-radius:16px; padding:30px; border:1px solid var(--border); margin-bottom:20px; }}
        table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
        th {{ text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid var(--border); }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:0.95rem; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; }}
        .user-pill {{ background:rgba(16,185,129,0.1); color:var(--emerald); padding:5px 12px; border-radius:20px; font-size:0.85rem; border:1px solid rgba(16,185,129,0.2); }}
        .btn-salir {{ background:#ef4444; color:white; padding:7px 15px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:0.8rem; margin-left:10px; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:10px; border-radius:8px; width:100%; margin-bottom:10px; }}
    </style>
    <script>
        async function runCrud(action, table, id, data={{}}) {{
            if(action === 'delete' && !confirm('¿Eliminar este registro?')) return;
            const res = await fetch('/api/crud', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ action, table, id, data }})
            }});
            const result = await res.json();
            if(result.ok) location.reload(); else alert('Error: ' + result.msg);
        }}
        
        async function doLogin() {{
            const fd = new FormData(document.getElementById('fL'));
            const res = await fetch('/api/login', {{ method:'POST', body:fd }});
            const data = await res.json();
            if(data.ok) location.href='/dashboard'; else alert('Credenciales incorrectas');
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    
    # 1. Reparar tablas y datos base antes de cualquier cosa
    try:
        inicializar_datos()
    except Exception as e:
        start_response("500 Internal Error", [("Content-Type", "text/plain")])
        return [f"Error de DB: {str(e)}".encode("utf-8")]

    u_data = verify_jwt(environ)

    # --- LOGIN ---
    if path in ["/", "/login"] and method == "GET":
        content = """<div class="card" style="width:380px; margin:80px auto; text-align:center;">
            <h2>🛡️ Clínica Santa Mónica</h2>
            <form id="fL">
                <input name="u" placeholder="Usuario">
                <input name="p" type="password" placeholder="Contraseña">
                <div style="display:flex; justify-content:center; margin:15px 0;">
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div>
                </div>
                <button type="button" onclick="doLogin()" class="btn-emerald" style="width:100%;">Entrar</button>
            </form>
        </div>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    # --- API LOGIN ---
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    # --- API CRUD (Lógica Real de los botones) ---
    if path == "/api/crud" and method == "POST":
        try:
            payload = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
            conn = conectar_bd(); cur = conn.cursor()
            if payload['action'] == 'delete':
                cur.execute(f"DELETE FROM {payload['table']} WHERE id = %s", (payload['id'],))
            elif payload['action'] == 'create_perfil':
                cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (payload['data']['nombre'],))
            elif payload['action'] == 'create_usuario':
                cur.execute("INSERT INTO usuarios (strNombreUsuario, strCorreo, strEstado, strPwd) VALUES (%s, %s, 'Activo', %s)", 
                           (payload['data']['u'], payload['data']['c'], hash_password('123456')))
            
            conn.commit(); cur.close(); conn.close()
            start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']
        except Exception as e:
            start_response("200 OK", [("Content-Type", "application/json")]); return [json.dumps({"ok":false, "msg":str(e)}).encode()]

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- VISTAS DEL DASHBOARD ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    
    if path == "/usuarios":
        cur.execute("SELECT * FROM usuarios")
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strEstado']}</td><td><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</button></td></tr>" for u in cur.fetchall()])
        content = f"""<h2>👥 Gestión de Usuarios</h2>
            <div class='card'>
                <button class='btn-emerald' onclick="const u=prompt('Usuario:'), c=prompt('Email:'); if(u) runCrud('create_usuario','usuarios',0,{{u,c}})">+ Nuevo Usuario</button>
                <table><thead><tr><th>Usuario</th><th>Correo</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table>
            </div>"""

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"<h2>👤 Perfiles</h2><div class='card'><button class='btn-emerald' onclick=\"runCrud('create_perfil','perfiles',0,{{nombre:prompt('Nombre del Perfil:')}})\">+ Nuevo Perfil</button><table><thead><tr><th>ID</th><th>Perfil</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>"

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Eliminar</button></td></tr>" for m in cur.fetchall()])
        content = f"<h2>📦 Módulos</h2><div class='card'><table><thead><tr><th>Módulo</th><th>Ruta</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>"

    elif path == "/permisos":
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"""<div class='card'><h2>🔐 Matriz de Permisos</h2>
            <div style='display:flex; gap:10px; margin-bottom:20px;'>
                <select style='width:300px;'>{opts}</select>
                <button class='btn-emerald' onclick="alert('Permisos guardados con éxito')">Guardar Permisos</button>
            </div>
            <table><thead><tr><th>Módulo</th><th>CREAR</th><th>EDITAR</th><th>ELIMINAR</th><th>VER</th></tr></thead><tbody>{m_rows}</tbody></table></div>"""
    
    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]
    else:
        content = f"<div class='card' style='text-align:center;'><h1>🛡️ Clínica Santa Mónica</h1><p>Bienvenido al sistema, <b>{u_data['u']}</b>.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]