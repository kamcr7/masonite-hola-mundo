# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_FINAL_V1"

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
    conn = conectar_bd(); cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(100))")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(100), strPwd VARCHAR(255), strCorreo VARCHAR(100), strEstado VARCHAR(20), idPerfil INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(100), strRuta VARCHAR(100), strMenuPadre VARCHAR(50))")
    cur.execute("CREATE TABLE IF NOT EXISTS permisos (idPerfil INT, idModulo INT, blnCrear TINYINT, blnEditar TINYINT, blnEliminar TINYINT, blnVer TINYINT, PRIMARY KEY(idPerfil, idModulo))")
    conn.commit(); cur.close(); conn.close()

# =========================================================
# MAQUETACIÓN
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); mods_db = cur.fetchall()
        cur.close(); conn.close()
        
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_db if m['strMenuPadre'] == padre])

        seg_base = '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/usuarios">👥 Usuarios</a><a href="/permisos">🔐 Permisos</a>'
        
        nav = f"""<div class="top-nav">
            <div class="nav-container">
                <div class="nav-left">
                    <span class="logo">🏥 Clínica Santa Mónica</span>
                    <a href="/dashboard" class="nav-link">Inicio</a>
                    <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{seg_base}{get_links("Seguridad")}</div></div>
                    <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1") or '<a>(Vacio)</a>'}</div></div>
                    <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2") or '<a>(Vacio)</a>'}</div></div>
                </div>
                <div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div>
            </div>
        </div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; --blue-btn: #1e40af; }}
        body {{ font-family:sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
        .logo {{ color:var(--emerald); font-weight:bold; margin-right:20px; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; padding:10px; font-size:14px; }}
        .dropdown {{ position:relative; display:inline-block; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:15px; cursor:pointer; font-size:14px; font-family:inherit; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:160px; border:1px solid var(--border); border-radius:8px; z-index:100; }}
        .dropdown-content a {{ color:white; padding:12px; text-decoration:none; display:block; font-size:13px; }}
        .dropdown-content a:hover {{ background:#334155; }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .container {{ padding:40px; max-width:1000px; margin:0 auto; }}
        .card {{ background:var(--card); padding:25px; border-radius:12px; border:1px solid var(--border); }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
        th, td {{ padding:12px; border-bottom:1px solid var(--border); text-align:left; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:10px; width:100%; margin-bottom:10px; border-radius:6px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:8px; border-radius:4px; cursor:pointer; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; }}
        .modal-content {{ background:var(--card); width:400px; margin:10% auto; padding:30px; border-radius:15px; position:relative; }}
        .close-x {{ position:absolute; top:15px; right:20px; color:#94a3b8; cursor:pointer; font-size:20px; }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            if(res.ok) location.reload(); else alert("Error al procesar");
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# LÓGICA
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    inicializar_datos()
    u_data = verify_jwt(environ)

    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save_modulo':
                cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)", (p['data']['n'], p['data']['r'], p['data']['p']))
            conn.commit(); r = b'{"ok":true}'
        except Exception as e: r = json.dumps({"ok":False, "msg":str(e)}).encode()
        cur.close(); conn.close(); start_response("200 OK", [("Content-Type", "application/json")]); return [r]

    if not u_data:
        start_response("303 See Other", [("Location", "/dashboard")]); return [b""]

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/modulos":
        cur.execute("SELECT id, strNombreModulo, strMenuPadre FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Eliminar</button></td></tr>" for m in cur.fetchall()])
        content = f"""<div class='card'><h2>📦 Gestión de Módulos</h2><button class='btn-emerald' onclick="openM('mM')">+ Nuevo Módulo</button>
            <table><thead><tr><th>Nombre</th><th>Menú</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mM" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mM')">&times;</span><h3>Nuevo Módulo</h3>
            <input id="mn" placeholder="Nombre"><input id="mr" placeholder="Ruta (ej: /ventas)"><select id="mp"><option>Principal 1</option><option>Principal 2</option><option>Seguridad</option></select>
            <button class="btn-emerald" style="width:100%" onclick="runCrud('save_modulo','modulos',0,{{n:document.getElementById('mn').value, r:document.getElementById('mr').value, p:document.getElementById('mp').value}})">Guardar</button></div></div>"""

    elif path == "/permisos":
        pid = int(urllib.parse.parse_qs(environ.get('QUERY_STRING','')).get('p',['0'])[0])
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        # Modulos dinámicos + manuales de seguridad
        mods_manuales = [{'id': 100, 'n': 'Perfiles'}, {'id': 101, 'n': 'Módulos'}, {'id': 102, 'n': 'Usuarios'}, {'id': 103, 'n': 'Permisos'}]
        cur.execute("SELECT id, strNombreModulo as n FROM modulos"); mods_db = cur.fetchall()
        all_mods = mods_manuales + mods_db
        
        opts = "".join([f"<option value='{p['id']}' {'selected' if p['id']==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = "".join([f"<tr><td>{m['n']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in all_mods])
        
        table_html = f"<table><thead><tr><th>Módulo</th><th>Ver</th><th>Crear</th><th>Editar</th></tr></thead><tbody>{m_rows}</tbody></table><button class='btn-emerald' style='margin-top:20px; width:100%'>Guardar Cambios</button>" if pid > 0 else "<p style='text-align:center; padding:20px; color:#94a3b8;'>Selecciona un perfil para gestionar sus permisos.</p>"
        
        content = f"""<div class='card'><h2>🔐 Matriz de Permisos</h2><select onchange="location.href='?p='+this.value"><option value="0">-- Selecciona Perfil --</option>{opts}</select>{table_html}</div>"""

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"""<div class='card'><h2>👤 Perfiles</h2><button class='btn-emerald' onclick="openM('mP')">+ Nuevo Perfil</button>
            <table><thead><tr><th>ID</th><th>Nombre</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mP" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mP')">&times;</span><h3>Nuevo Perfil</h3><input id="pn" placeholder="Nombre"><button class="btn-emerald" style="width:100%" onclick="runCrud('save_perfil','perfiles',0,{{nombre:document.getElementById('pn').value}})">Guardar</button></div></div>"""

    else:
        content = f"<h2>Bienvenido</h2><p>Selecciona una opción del menú de Seguridad.</p>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]