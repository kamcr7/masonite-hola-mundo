# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_SECURITY_V5"

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
        # Asegurar columnas por si acaso
        try: cur.execute("ALTER TABLE modulos ADD COLUMN strRuta VARCHAR(100)")
        except: pass
        try: cur.execute("ALTER TABLE modulos ADD COLUMN strMenuPadre VARCHAR(50)")
        except: pass
        conn.commit(); cur.close(); conn.close()
    except: pass

# =========================================================
# MAQUETACIÓN
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        try:
            conn = conectar_bd(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM modulos"); mods_db = cur.fetchall()
            cur.close(); conn.close()
        except: mods_db = []
        
        def get_links(padre):
            links = "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_db if m.get('strMenuPadre') == padre])
            return links

        seg_base = '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/usuarios">👥 Usuarios</a><a href="/permisos">🔐 Permisos</a>'
        
        nav = f"""<div class="top-nav">
            <div class="nav-container">
                <div class="nav-left">
                    <span class="logo">🛡️ Clínica</span>
                    <a href="/dashboard" class="nav-link">Inicio</a>
                    <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{seg_base}{get_links("Seguridad")}</div></div>
                    <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1") or '<a>(Vacío)</a>'}</div></div>
                    <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2") or '<a>(Vacío)</a>'}</div></div>
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
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:22px 12px; cursor:pointer; font-size:0.9rem; font-family:inherit; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border-radius:8px; border:1px solid var(--border); box-shadow:0 10px 15px rgba(0,0,0,0.4); z-index:1000;}}
        .dropdown-content a {{ color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem; }}
        .dropdown-content a:hover {{ background:#334155; color:var(--emerald); }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .container {{ padding:40px 20px; max-width:1100px; margin:0 auto; }}
        .card {{ background:var(--card); border-radius:16px; padding:30px; border:1px solid var(--border); margin-bottom:20px; }}
        table {{ width:100%; border-collapse:collapse; margin-top:15px; }}
        th {{ text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid var(--border); }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:0.95rem; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; }}
        .btn-salir {{ background:#ef4444; color:white; padding:7px 15px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:0.8rem; }}
        .user-pill {{ background:rgba(16,185,129,0.1); color:var(--emerald); padding:5px 12px; border-radius:20px; font-size:0.85rem; margin-right:10px; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; border-radius:8px; width:100%; margin-bottom:12px; box-sizing:border-box; }}
        .modal {{ display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8); }}
        .modal-content {{ background:var(--card); margin:8% auto; padding:30px; border:1px solid var(--border); width:400px; border-radius:16px; position:relative; }}
        .close-btn {{ position:absolute; right:20px; top:15px; cursor:pointer; font-size:1.5rem; color:#94a3b8; }}
    </style>
    <script>
        function openM(id, tid=0) {{ document.getElementById(id).style.display = 'block'; if(tid) document.querySelector('#'+id+' [name=id]').value = tid; }}
        function closeM(id) {{ document.getElementById(id).style.display = 'none'; }}
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            const result = await res.json();
            if(result.ok) location.reload(); else alert('Error: '+result.msg);
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

    # API LOGIN Y CRUD IGUAL... (omitido por brevedad en la explicación, pero incluido en el bloque de abajo)
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

    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save_perfil':
                cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['nombre'],))
            elif p['action'] == 'save_modulo':
                cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s, %s, %s)", (p['data']['n'], p['data']['r'], p['data']['p']))
            elif p['action'] == 'save_permisos':
                cur.execute("DELETE FROM permisos WHERE idPerfil=%s", (p['data']['idPerfil'],))
                cur.executemany("INSERT INTO permisos (idPerfil, idModulo, blnCrear, blnEditar, blnEliminar, blnVer) VALUES (%s,%s,%s,%s,%s,%s)", p['data']['perms'])
            conn.commit(); r = b'{"ok":true}'
        except Exception as e: r = json.dumps({"ok":false, "msg":str(e)}).encode()
        cur.close(); conn.close(); start_response("200 OK", [("Content-Type", "application/json")]); return [r]

    if not u_data and path not in ["/", "/login", "/api/login"]:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- VISTAS ACTUALIZADAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button></td></tr>" for m in cur.fetchall()])
        content = f"""<div class='card'><h2>📦 Módulos</h2><button class='btn-emerald' onclick="openM('mM')">+ Nuevo Módulo</button>
            <table><thead><tr><th>Nombre</th><th>Ruta</th><th>Menú</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mM" class="modal"><div class="modal-content"><span class="close-btn" onclick="closeM('mM')">&times;</span><h3>Nuevo Módulo</h3>
            <input id="mn" placeholder="Nombre (Ej: Inventario)"><input id="mr" placeholder="Ruta (Ej: /inventario)"><select id="mp"><option>Principal 1</option><option>Principal 2</option><option>Seguridad</option></select>
            <button class="btn-emerald" style="width:100%" onclick="runCrud('save_modulo','modulos',0,{{n:document.getElementById('mn').value, r:document.getElementById('mr').value, p:document.getElementById('mp').value}})">Guardar Módulo</button></div></div>"""

    elif path == "/permisos":
        pid = int(urllib.parse.parse_qs(environ.get('QUERY_STRING','')).get('p',['0'])[0])
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        # Aquí unimos los fijos con los dinámicos
        modulos_fijos = [{'id': -1, 'n': 'Perfiles'}, {'id': -2, 'n': 'Módulos'}, {'id': -3, 'n': 'Usuarios'}, {'id': -4, 'n': 'Permisos'}]
        cur.execute("SELECT id, strNombreModulo as n FROM modulos"); modulos_db = cur.fetchall()
        all_mods = modulos_fijos + modulos_db
        
        cur.execute("SELECT * FROM permisos WHERE idPerfil=%s", (pid,))
        p_dict = {{p['idModulo']: p for p in cur.fetchall()}}
        
        opts = "".join([f"<option value='{p['id']}' {'selected' if p['id']==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = "".join([f"<tr data-mid='{m['id']}'><td>{m['n']}</td><td><input type='checkbox' class='c'></td><td><input type='checkbox' class='e'></td><td><input type='checkbox' class='v' checked></td></tr>" for m in all_mods])
        
        content = f"""<div class='card'><h2>🔐 Matriz de Permisos</h2><select onchange="location.href='?p='+this.value"><option value="0">-- Selecciona Perfil --</option>{opts}</select>
            <button class="btn-emerald" onclick="saveP()" style="margin-left:10px;">Guardar Cambios</button>
            <table><thead><tr><th>Módulo</th><th>Crear</th><th>Editar</th><th>Ver</th></tr></thead><tbody>{m_rows}</tbody></table></div>
            <script>async function saveP(){{
                const pid = new URLSearchParams(location.search).get('p');
                const ps = [];
                document.querySelectorAll('tbody tr').forEach(r => {{
                    ps.push([pid, r.dataset.mid, r.querySelector('.c').checked?1:0, r.querySelector('.e').checked?1:0, 0, r.querySelector('.v').checked?1:0]);
                }});
                await runCrud('save_permisos','permisos',0,{{idPerfil:pid, perms:ps}});
            }}</script>"""

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"""<div class='card'><h2>👤 Perfiles</h2><button class='btn-emerald' onclick="openM('mP')">+ Nuevo Perfil</button>
            <table><thead><tr><th>ID</th><th>Nombre</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mP" class="modal"><div class="modal-content"><span class="close-btn" onclick="closeM('mP')">&times;</span><h3>Nuevo Perfil</h3>
            <input id="pn" placeholder="Nombre del Perfil"><button class="btn-emerald" style="width:100%" onclick="runCrud('save_perfil','perfiles',0,{{nombre:document.getElementById('pn').value}})">Guardar</button></div></div>"""

    elif path in ["/", "/login"]:
        content = '<div class="card" style="width:350px; margin:100px auto; text-align:center;"><h2>Login</h2><form id="fL"><input name="u" placeholder="Admin"><input name="p" type="password" placeholder="***"><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div><button type="button" class="btn-emerald" onclick="doLogin()">Entrar</button></form></div><script>async function doLogin(){{ const res=await fetch("/api/login",{{method:"POST",body:new FormData(document.getElementById("fL"))}}); const d=await res.json(); if(d.ok)location.href="/dashboard"; else alert("Error");}}</script>'
    else:
        content = f"<h2>Bienvenido al Sistema</h2><p>Selecciona un módulo para empezar.</p>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]