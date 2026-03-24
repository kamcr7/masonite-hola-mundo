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
    try:
        conn = conectar_bd(); cur = conn.cursor()
        # Ejecutamos las creaciones una por una para evitar Unread Result
        cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(100))")
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(100), strPwd VARCHAR(255), strCorreo VARCHAR(100), strEstado VARCHAR(20), idPerfil INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(100), strRuta VARCHAR(100), strMenuPadre VARCHAR(50))")
        cur.execute("CREATE TABLE IF NOT EXISTS permisos (idPerfil INT, idModulo INT, blnCrear TINYINT, blnEditar TINYINT, blnEliminar TINYINT, blnVer TINYINT, PRIMARY KEY(idPerfil, idModulo))")
        
        # Reparar columnas faltantes
        for col, tip in [("strRuta", "VARCHAR(100)"), ("strMenuPadre", "VARCHAR(50)")]:
            try: cur.execute(f"ALTER TABLE modulos ADD COLUMN {col} {tip}")
            except: pass
            
        conn.commit(); cur.close(); conn.close()
    except Exception as e: print(f"Error init: {e}")

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
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_db if m.get('strMenuPadre') == padre])

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
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
        body {{ font-family:sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
        .logo {{ color:var(--emerald); font-weight:bold; margin-right:20px; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; padding:10px; font-size:14px; }}
        .dropdown {{ position:relative; display:inline-block; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:15px; cursor:pointer; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:160px; border:1px solid var(--border); border-radius:8px; z-index:100; }}
        .dropdown-content a {{ color:white; padding:12px; text-decoration:none; display:block; font-size:13px; }}
        .dropdown-content a:hover {{ background:#334155; }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .container {{ padding:40px; max-width:1100px; margin:0 auto; }}
        .card {{ background:var(--card); padding:25px; border-radius:12px; border:1px solid var(--border); }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
        th, td {{ padding:12px; border-bottom:1px solid var(--border); text-align:left; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:10px; width:100%; margin-bottom:10px; border-radius:6px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:6px; cursor:pointer; font-weight:bold; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:8px; border-radius:4px; cursor:pointer; }}
        .btn-gray {{ background:#475569; color:white; border:none; padding:10px 20px; border-radius:6px; cursor:pointer; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; }}
        .modal-content {{ background:var(--card); width:400px; margin:10% auto; padding:30px; border-radius:15px; position:relative; }}
        .close-x {{ position:absolute; top:15px; right:20px; color:#94a3b8; cursor:pointer; font-size:24px; }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
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
            elif p['action'] == 'save_modulo':
                cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)", (p['data']['n'], p['data']['r'], p['data']['p']))
            elif p['action'] == 'save_usuario':
                d = p['data']
                cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, strCorreo, strEstado, idPerfil) VALUES (%s,%s,%s,'Activo',%s)", (d['u'], hash_password(d['pwd']), d['c'], d['p']))
            elif p['action'] == 'save_perfil':
                cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['nombre'],))
            elif p['action'] == 'save_permisos':
                cur.execute("DELETE FROM permisos WHERE idPerfil=%s", (p['data']['idPerfil'],))
                cur.executemany("INSERT INTO permisos (idPerfil, idModulo, blnCrear, blnEditar, blnEliminar, blnVer) VALUES (%s,%s,%s,%s,%s,%s)", p['data']['perms'])
            conn.commit(); r = b'{"ok":true}'
        except Exception as e: r = json.dumps({"ok":False, "msg":str(e)}).encode()
        cur.close(); conn.close(); start_response("200 OK", [("Content-Type", "application/json")]); return [r]

    if not u_data and path != "/":
        start_response("303 See Other", [("Location", "/")]); return [b""]

    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Eliminar</button></td></tr>" for m in cur.fetchall()])
        content = f"""<div class='card'><h2>📦 Gestión de Módulos</h2><button class='btn-emerald' onclick="openM('mM')">+ Nuevo Módulo</button>
            <table><thead><tr><th>Nombre</th><th>Ruta</th><th>Menú</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mM" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mM')">&times;</span><h3>Nuevo Módulo</h3>
            <input id="mn" placeholder="Nombre"><input id="mr" placeholder="Ruta"><select id="mp"><option>Principal 1</option><option>Principal 2</option><option>Seguridad</option></select>
            <div style="display:flex; gap:10px;"><button class="btn-emerald" style="flex:1" onclick="runCrud('save_modulo','modulos',0,{{n:document.getElementById('mn').value, r:document.getElementById('mr').value, p:document.getElementById('mp').value}})">Guardar</button>
            <button class="btn-gray" onclick="closeM('mM')">Cancelar</button></div></div></div>"""

    elif path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        u_list = cur.fetchall()
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strNombrePerfil'] or 'S/P'}</td><td><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</button></td></tr>" for u in u_list])
        cur.execute("SELECT * FROM perfiles"); perfs = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        content = f"""<div class='card'><h2>👥 Usuarios</h2><button class='btn-emerald' onclick="openM('mU')">+ Nuevo Usuario</button>
            <table><thead><tr><th>Usuario</th><th>Email</th><th>Perfil</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mU" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mU')">&times;</span><h3>Nuevo Usuario</h3>
            <input id="uu" placeholder="Usuario"><input id="ue" placeholder="Email"><input id="up" type="password" placeholder="Password"><select id="uperf">{perfs}</select>
            <div style="display:flex; gap:10px;"><button class="btn-emerald" style="flex:1" onclick="runCrud('save_usuario','usuarios',0,{{u:document.getElementById('uu').value, c:document.getElementById('ue').value, pwd:document.getElementById('up').value, p:document.getElementById('uperf').value}})">Crear</button>
            <button class="btn-gray" onclick="closeM('mU')">Cancelar</button></div></div></div>"""

    elif path == "/permisos":
        pid = int(urllib.parse.parse_qs(environ.get('QUERY_STRING','')).get('p',['0'])[0])
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        mods_manuales = [{'id': 100, 'n': 'Perfiles'}, {'id': 101, 'n': 'Módulos'}, {'id': 102, 'n': 'Usuarios'}, {'id': 103, 'n': 'Permisos'}]
        cur.execute("SELECT id, strNombreModulo as n FROM modulos"); mods_db = cur.fetchall()
        all_mods = mods_manuales + mods_db
        opts = "".join([f"<option value='{p['id']}' {'selected' if p['id']==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = "".join([f"<tr data-mid='{m['id']}'><td>{m['n']}</td><td><input type='checkbox' checked></td><td><input type='checkbox' checked></td><td><input type='checkbox' checked></td></tr>" for m in all_mods])
        content = f"<div class='card'><h2>🔐 Matriz de Permisos</h2><select onchange=\"location.href='?p='+this.value\"><option value='0'>-- Seleccionar Perfil --</option>{opts}</select><table><thead><tr><th>Módulo</th><th>Ver</th><th>Crear</th><th>Editar</th></tr></thead><tbody>{m_rows}</tbody></table></div>"

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"""<div class='card'><h2>👤 Perfiles</h2><button class='btn-emerald' onclick="openM('mP')">+ Nuevo Perfil</button>
            <table><thead><tr><th>ID</th><th>Perfil</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mP" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mP')">&times;</span><h3>Nuevo Perfil</h3><input id="pn" placeholder="Nombre"><div style="display:flex; gap:10px;"><button class="btn-emerald" style="flex:1" onclick="runCrud('save_perfil','perfiles',0,{{nombre:document.getElementById('pn').value}})">Guardar</button><button class="btn-gray" onclick="closeM('mP')">Cancelar</button></div></div></div>"""

    elif path == "/":
        content = '<div class="card" style="width:350px; margin:100px auto;"><h2>Login</h2><form id="fL"><input name="u" placeholder="Admin"><input name="p" type="password" placeholder="***"><button type="button" class="btn-emerald" style="width:100%" onclick="doLogin()">Entrar</button></form></div><script>async function doLogin(){{ const r=await fetch("/api/login",{{method:"POST",body:new FormData(document.getElementById("fL"))}}); const d=await r.json(); if(d.ok)location.href="/dashboard"; else alert("Error");}}</script>'
    else:
        content = f"<h2>Bienvenido</h2><p>Selecciona una opción del menú de Seguridad.</p>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]