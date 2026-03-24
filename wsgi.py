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
# REPARACIÓN Y ESTRUCTURA
# =========================================================
def inicializar_datos():
    try:
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(100))")
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(100), strPwd VARCHAR(255), strCorreo VARCHAR(100), strEstado VARCHAR(20))")
        cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(100), strRuta VARCHAR(100))")
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        print(f"Error de estructura: {e}")

# =========================================================
# RENDERIZADO GLOBAL
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
                            <a href="/usuarios">👥 Usuarios</a>
                        </div>
                    </div>
                </div>
                <div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div>
            </div>
        </div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
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
        table {{ width:100%; border-collapse:collapse; }}
        th {{ text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid var(--border); }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:0.95rem; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; }}
        input {{ background:#0f172a; border:1px solid var(--border); color:white; padding:10px; border-radius:8px; width:100%; margin-bottom:10px; }}
        /* Modal simple */
        .modal {{ display:none; position:fixed; z-index:200; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.7); }}
        .modal-content {{ background:var(--card); margin:10% auto; padding:20px; border:1px solid var(--border); width:400px; border-radius:12px; }}
    </style>
    <script>
        function showModal(id) {{ document.getElementById(id).style.display = 'block'; }}
        function hideModal(id) {{ document.getElementById(id).style.display = 'none'; }}

        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ action, table, id, data }})
            }});
            const result = await res.json();
            if(result.ok) location.reload(); else alert('Error: ' + result.msg);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    inicializar_datos()
    u_data = verify_jwt(environ)

    # API CRUD (Procesa todos los guardados y eliminaciones)
    if path == "/api/crud" and method == "POST":
        try:
            payload = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
            conn = conectar_bd(); cur = conn.cursor()
            
            if payload['action'] == 'delete':
                cur.execute(f"DELETE FROM {payload['table']} WHERE id = %s", (payload['id'],))
            
            elif payload['action'] == 'save_perfil':
                cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (payload['data']['nombre'],))
            
            elif payload['action'] == 'save_usuario':
                p_hash = hash_password(payload['data']['pwd'])
                cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, strCorreo, strEstado) VALUES (%s, %s, %s, 'Activo')", 
                           (payload['data']['u'], p_hash, payload['data']['m']))
            
            elif payload['action'] == 'save_modulo':
                cur.execute("INSERT INTO modulos (strNombreModulo, strRuta) VALUES (%s, %s)", 
                           (payload['data']['n'], payload['data']['r']))

            conn.commit(); cur.close(); conn.close()
            start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']
        except Exception as e:
            start_response("200 OK", [("Content-Type", "application/json")]); return [json.dumps({"ok":false, "msg":str(e)}).encode()]

    # VISTAS
    if not u_data and path not in ["/login", "/api/login"]:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    # --- PANTALLA USUARIOS ---
    if path == "/usuarios":
        cur.execute("SELECT * FROM usuarios")
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strEstado']}</td><td><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</button></td></tr>" for u in cur.fetchall()])
        content = f"""<h2>👥 Gestión de Usuarios</h2>
            <div class='card'>
                <button class='btn-emerald' onclick="showModal('mU')">+ Nuevo Usuario</button>
                <table><thead><tr><th>Usuario</th><th>Correo</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table>
            </div>
            <div id="mU" class="modal"><div class="modal-content">
                <h3>Nuevo Usuario</h3>
                <input id="u_u" placeholder="Nombre de Usuario">
                <input id="u_m" placeholder="Correo">
                <input id="u_p" type="password" placeholder="Contraseña">
                <button class="btn-emerald" onclick="runCrud('save_usuario','usuarios',0,{{u:document.getElementById('u_u').value, m:document.getElementById('u_m').value, pwd:document.getElementById('u_p').value}})">Guardar</button>
                <button onclick="hideModal('mU')">Cancelar</button>
            </div></div>"""

    # --- PANTALLA MÓDULOS ---
    elif path == "/modulos":
        try:
            cur.execute("SELECT * FROM modulos")
            mods = cur.fetchall()
            rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Eliminar</button></td></tr>" for m in mods])
        except: rows = "<tr><td colspan='3'>Error: Falta columna strRuta. Añádela en Railway.</td></tr>"
        
        content = f"""<h2>📦 Módulos del Sistema</h2>
            <div class='card'>
                <button class='btn-emerald' onclick="showModal('mM')">+ Nuevo Módulo</button>
                <table><thead><tr><th>Nombre</th><th>Ruta</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table>
            </div>
            <div id="mM" class="modal"><div class="modal-content">
                <h3>Nuevo Módulo</h3>
                <input id="m_n" placeholder="Nombre (Ej: Inventario)">
                <input id="m_r" placeholder="Ruta (Ej: /inventario)">
                <button class="btn-emerald" onclick="runCrud('save_modulo','modulos',0,{{n:document.getElementById('m_n').value, r:document.getElementById('m_r').value}})">Guardar</button>
                <button onclick="hideModal('mM')">Cancelar</button>
            </div></div>"""

    elif path == "/perfiles":
        # (Lógica de perfiles similar a la que ya te funciona)
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"<h2>👤 Perfiles</h2><div class='card'><button class='btn-emerald' onclick=\"showModal('mP')\">+ Nuevo Perfil</button><table><thead><tr><th>ID</th><th>Perfil</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div><div id='mP' class='modal'><div class='modal-content'><h3>Nuevo Perfil</h3><input id='p_n' placeholder='Nombre'><button class='btn-emerald' onclick=\"runCrud('save_perfil','perfiles',0,{{nombre:document.getElementById('p_n').value}})\">Guardar</button><button onclick=\"hideModal('mP')\">Cancelar</button></div></div>"

    else:
        content = "<h2>Bienvenido</h2><p>Selecciona una opción del menú.</p>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]