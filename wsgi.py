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

def inicializar_datos():
    try:
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(100))")
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(100), strPwd VARCHAR(255), strCorreo VARCHAR(100), strEstado VARCHAR(20), idPerfil INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(100), strRuta VARCHAR(100), strMenuPadre VARCHAR(50))")
        cur.execute("CREATE TABLE IF NOT EXISTS permisos (idPerfil INT, idModulo INT, blnCrear TINYINT, blnEditar TINYINT, blnEliminar TINYINT, blnVer TINYINT, PRIMARY KEY(idPerfil, idModulo))")
        conn.commit(); cur.close(); conn.close()
    except: pass

# =========================================================
# RENDERIZADO
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        # Menú básico para evitar errores si las columnas no existen
        nav = f"""<div class="top-nav">
            <div class="nav-container">
                <div class="nav-left">
                    <span class="logo">🛡️ Clínica</span>
                    <a href="/dashboard" class="nav-link">Inicio</a>
                    <div class="dropdown">
                        <button class="dropbtn">Seguridad ▾</button>
                        <div class="dropdown-content">
                            <a href="/perfiles">👤 Perfiles</a>
                            <a href="/modulos">📦 Módulos</a>
                            <a href="/usuarios">👥 Usuarios</a>
                            <a href="/permisos">🔐 Permisos</a>
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
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:22px 12px; cursor:pointer; font-size:0.9rem; font-family:inherit; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border-radius:8px; border:1px solid var(--border); box-shadow:0 10px 15px rgba(0,0,0,0.4); z-index:1000;}}
        .dropdown-content a {{ color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem; }}
        .dropdown-content a:hover {{ background:#334155; color:var(--emerald); }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .container {{ padding:40px 20px; max-width:1100px; margin:0 auto; }}
        .card {{ background:var(--card); border-radius:16px; padding:30px; border:1px solid var(--border); margin-bottom:20px; }}
        table {{ width:100%; border-collapse:collapse; }}
        th {{ text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid var(--border); }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:0.95rem; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-outline {{ background:transparent; border:1px solid var(--border); color:#94a3b8; padding:6px 12px; border-radius:6px; cursor:pointer; margin-right:5px; text-decoration:none; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; }}
        .btn-salir {{ background:#ef4444; color:white; padding:7px 15px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:0.8rem; margin-left:10px; }}
        .user-pill {{ background:rgba(16,185,129,0.1); color:var(--emerald); padding:5px 12px; border-radius:20px; font-size:0.85rem; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:10px; border-radius:8px; width:100%; margin-bottom:10px; box-sizing: border-box; }}
        .modal {{ display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.7); }}
        .modal-content {{ background:var(--card); margin:10% auto; padding:25px; border:1px solid var(--border); width:400px; border-radius:16px; }}
    </style>
    <script>
        function openM(id, tid=0, name='', extra='') {{ 
            const m = document.getElementById(id); m.style.display = 'block';
            if(tid) {{ 
                m.querySelector('[name="id"]').value = tid; 
                if(name) m.querySelector('[name="nombre"]').value = name;
                if(extra && m.id === 'mM') m.querySelector('[name="ruta"]').value = extra;
            }}
        }}
        function closeM(id) {{ document.getElementById(id).style.display = 'none'; }}

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
# APLICACIÓN
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    inicializar_datos()
    u_data = verify_jwt(environ)

    # --- LOGIN ---
    if path in ["/", "/login"] and method == "GET":
        content = """<div class="card" style="width:350px; margin:100px auto; text-align:center;">
            <h2 style="color:var(--emerald)">Iniciar Sesión</h2>
            <form id="fL">
                <input name="u" placeholder="Usuario" required>
                <input name="p" type="password" placeholder="Contraseña" required>
                <button type="button" onclick="doLogin()" class="btn-emerald" style="width:100%; margin-top:10px;">Entrar</button>
            </form>
        </div>
        <script>
            async function doLogin() {
                const fd = new FormData(document.getElementById('fL'));
                const res = await fetch('/api/login', { method:'POST', body:fd });
                const data = await res.json();
                if(data.ok) location.href='/dashboard'; else alert('Acceso denegado');
            }
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    # --- API LOGIN ---
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p"))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    # --- API CRUD ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save_perfil':
                if p['id']: cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (p['data']['nombre'], p['id']))
                else: cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['nombre'],))
            elif p['action'] == 'save_modulo':
                cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s, %s, %s)", (p['data']['n'], p['data']['r'], p['data']['p']))
            conn.commit(); r = b'{"ok":true}'
        except Exception as e: r = json.dumps({"ok":false, "msg":str(e)}).encode()
        cur.close(); conn.close(); start_response("200 OK", [("Content-Type", "application/json")]); return [r]

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-outline' onclick=\"openM('mP',{p['id']},'{p['strNombrePerfil']}')\">Editar</button><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"""<div class='card'><h2>👤 Perfiles</h2><button class='btn-emerald' onclick="openM('mP')">+ Nuevo Perfil</button>
            <table><thead><tr><th>ID</th><th>Perfil</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mP" class="modal"><div class="modal-content"><h3>Perfil</h3><input type="hidden" name="id" value="0"><input name="nombre" placeholder="Nombre del Perfil">
            <button class="btn-emerald" onclick="runCrud('save_perfil','perfiles',document.querySelector('#mP [name=id]').value, {{nombre:document.querySelector('#mP [name=nombre]').value}})">Guardar</button>
            <button onclick="closeM('mP')">Cancelar</button></div></div>"""

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td>{m.get('strMenuPadre','--')}</td><td><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button></td></tr>" for m in cur.fetchall()])
        content = f"""<div class='card'><h2>📦 Módulos</h2><button class='btn-emerald' onclick="openM('mM')">+ Nuevo Módulo</button>
            <table><thead><tr><th>Nombre</th><th>Ruta</th><th>Menu</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mM" class="modal"><div class="modal-content"><h3>Nuevo Módulo</h3>
            <input name="nombre" placeholder="Nombre"><input name="ruta" placeholder="Ruta">
            <select name="padre"><option>Seguridad</option><option>Principal 1</option><option>Principal 2</option><option>Prueba</option></select>
            <button class="btn-emerald" onclick="runCrud('save_modulo','modulos',0,{{n:document.querySelector('#mM [name=nombre]').value, r:document.querySelector('#mM [name=ruta]').value, p:document.querySelector('#mM [name=padre]').value}})">Guardar</button>
            <button onclick="closeM('mM')">Cancelar</button></div></div>"""

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0")]); return [b""]
    else:
        content = f"<h2>Bienvenido {u_data['u']}</h2><p>Selecciona una opción en Seguridad.</p>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]