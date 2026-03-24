# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_FINAL_FIX_V2"

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
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4', consume_results=True)

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
            links = [f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_db if m.get('strMenuPadre') == padre]
            return "".join(links)

        seg_links = f'<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/usuarios">👥 Usuarios</a><a href="/permisos">🔐 Permisos</a>{get_links("Seguridad")}'
        
        nav = f"""<div class="top-nav">
            <div class="nav-container">
                <div class="nav-left">
                    <span class="logo">🏥 Clínica Santa Mónica</span>
                    <a href="/dashboard" class="nav-link">Inicio</a>
                    <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{seg_links}</div></div>
                    <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1") or '<a>(Vacio)</a>'}</div></div>
                    <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2") or '<a>(Vacio)</a>'}</div></div>
                </div>
                <div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div>
            </div>
        </div>"""
    else:
        nav = '<div class="top-nav"><div class="nav-container"><span class="logo">🏥 Clínica Santa Mónica</span><a href="/login" class="nav-link">Acceder</a></div></div>'
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; --blue-btn: #1e40af; }}
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
        table {{ width:100%; border-collapse:collapse; margin-top:20px; background: #0f172a; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding:15px; border-bottom:1px solid var(--border); text-align:left; }}
        th {{ background: #1e293b; color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-blue {{ background:var(--blue-btn); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:8px 12px; border-radius:6px; cursor:pointer; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; }}
        .modal-content {{ background:white; color: #1e293b; width:450px; margin:10% auto; padding:30px; border-radius:15px; position:relative; }}
        .modal-content h3 {{ margin-top:0; color: #1e293b; font-size: 1.5rem; }}
        .modal-content input, .modal-content select {{ background: #f8fafc; border: 1px solid #cbd5e1; color: #1e293b; }}
        .close-x {{ position:absolute; top:15px; right:20px; color:#64748b; cursor:pointer; font-size:24px; }}
        .btn-salir {{ background: #ef4444; color:white; text-decoration:none; padding:8px 15px; border-radius:8px; font-size: 13px; }}
        .label-req {{ font-weight: bold; margin-bottom: 5px; display: block; font-size: 14px; color: #1e293b; }}
        .label-req::after {{ content: " *"; color: #ef4444; }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        function toggleAll() {{ document.querySelectorAll('tbody input[type="checkbox"]').forEach(i => i.checked = !i.checked); }}
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            const r = await res.json();
            if(r.ok) location.reload(); else alert("Error: " + r.msg);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR PRINCIPAL
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    inicializar_datos()
    u_data = verify_jwt(environ)

    # Rutas públicas
    if path == "/login":
        content = '<div class="card" style="width:350px; margin:100px auto;"><h2>Iniciar Sesión</h2><form id="fL"><input name="u" placeholder="Usuario"><input name="p" type="password" placeholder="Contraseña"><button type="button" class="btn-emerald" style="width:100%" onclick="doLogin()">Entrar</button></form></div><script>async function doLogin(){{ const r=await fetch("/api/login",{{method:"POST",body:new FormData(document.getElementById("fL"))}}); const d=await r.json(); if(d.ok)location.href="/dashboard"; else alert("Datos incorrectos");}}</script>'
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode()]

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

    # Protección de rutas
    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API CRUD ---
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

    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    # --- VISTAS ---
    if path == "/modulos":
        mods_fijos = [
            {'id': '-', 'strNombreModulo': 'Perfiles', 'strRuta': '/perfiles', 'strMenuPadre': 'Seguridad'},
            {'id': '-', 'strNombreModulo': 'Módulos', 'strRuta': '/modulos', 'strMenuPadre': 'Seguridad'},
            {'id': '-', 'strNombreModulo': 'Usuarios', 'strRuta': '/usuarios', 'strMenuPadre': 'Seguridad'},
            {'id': '-', 'strNombreModulo': 'Permisos', 'strRuta': '/permisos', 'strMenuPadre': 'Seguridad'},
            {'id': '-', 'strNombreModulo': 'Principal 1', 'strRuta': '#', 'strMenuPadre': 'Sistema'},
            {'id': '-', 'strNombreModulo': 'Principal 2', 'strRuta': '#', 'strMenuPadre': 'Sistema'}
        ]
        cur.execute("SELECT * FROM modulos"); mods_db = cur.fetchall()
        rows = ""
        for m in mods_fijos + mods_db:
            btn = "<em>Sistema</em>" if m['id'] == '-' else f"<button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Eliminar</button>"
            rows += f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td>{btn}</td></tr>"
        
        content = f"""<div class='card'><h2>📦 Gestión de Módulos</h2><button class='btn-emerald' onclick="openM('mM')">+ Nuevo Módulo</button>
            <table><thead><tr><th>Nombre</th><th>Ruta</th><th>Agrupar en Menú</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            
            <div id="mM" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mM')">&times;</span>
            <h3>Nuevo Módulo</h3>
            <label class="label-req">Nombre del Módulo</label><input id="mn" placeholder="Ej: Inventarios">
            <label class="label-req">Ruta</label><input id="mr" placeholder="/inventario">
            <label>Agrupar en Menú</label>
            <div style="display:flex; gap:10px; margin-bottom:20px;">
                <select id="mp" style="flex:1; margin-bottom:0;"><option value="">-- Sin asignar --</option><option>Seguridad</option><option>Principal 1</option><option>Principal 2</option></select>
                <button class="btn-emerald" style="height:42px" onclick="const n=prompt('Nueva Categoría:'); if(n){{const s=document.getElementById('mp'); const o=document.createElement('option'); o.text=n; s.add(o); s.value=n;}}">Crear Nuevo</button>
            </div>
            <div style="display:flex; gap:10px;">
                <button class="btn-blue" style="flex:1" onclick="runCrud('save_modulo','modulos',0,{{n:document.getElementById('mn').value, r:document.getElementById('mr').value, p:document.getElementById('mp').value}})">Guardar</button>
                <button class="btn-emerald" style="background:#f1f5f9; color:#475569; flex:1" onclick="closeM('mM')">Cancelar</button>
            </div></div></div>"""

    elif path == "/permisos":
        pid = int(urllib.parse.parse_qs(environ.get('QUERY_STRING','')).get('p',['0'])[0])
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        # Consolidar todos los módulos para permisos
        cur.execute("SELECT id, strNombreModulo as n FROM modulos")
        all_mods = [{'id':1, 'n':'Perfiles'},{'id':2,'n':'Módulos'},{'id':3,'n':'Usuarios'},{'id':4,'n':'Permisos'},{'id':5,'n':'Principal 1'},{'id':6,'n':'Principal 2'}] + cur.fetchall()
        
        opts = "".join([f"<option value='{p['id']}' {'selected' if p['id']==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = "".join([f"<tr><td>{m['n']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in all_mods])
        
        content = f"""<div class='card'><h2>🔐 Matriz de Permisos</h2>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <select style="width:300px; margin-bottom:0;" onchange="location.href='?p='+this.value"><option value='0'>-- Seleccionar Perfil --</option>{opts}</select>
                <button class="btn-blue" onclick="toggleAll()">Seleccionar Todo</button>
            </div>
            <table><thead><tr><th>Módulo</th><th>Ver</th><th>Crear</th><th>Editar</th><th>Eliminar</th></tr></thead><tbody>{m_rows}</tbody></table>
            <button class="btn-emerald" style="margin-top:20px; width:100%">Guardar Cambios</button></div>"""

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else:
        content = f"<div class='card'><h2>Bienvenido, {u_data['u']}</h2><p>Usa el menú superior para navegar por el sistema.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]