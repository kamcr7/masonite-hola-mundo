# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_SECURITY_V3"

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
# REPARACIÓN Y ESTRUCTURA (Silent Fail activo)
# =========================================================
def inicializar_datos():
    try:
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(100))")
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(100), strPwd VARCHAR(255), strCorreo VARCHAR(100), strEstado VARCHAR(20), idPerfil INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(100), strRuta VARCHAR(100), strMenuPadre VARCHAR(50))")
        cur.execute("CREATE TABLE IF NOT EXISTS permisos (idPerfil INT, idModulo INT, blnCrear TINYINT, blnEditar TINYINT, blnEliminar TINYINT, blnVer TINYINT, PRIMARY KEY(idPerfil, idModulo))")
        
        # Módulos base si está vacío
        cur.execute("SELECT COUNT(*) FROM modulos")
        if cur.fetchone()[0] == 0:
            base_mods = [('Perfiles','/perfiles','Seguridad'),('Módulos','/modulos','Seguridad'),('Permisos','/permisos','Seguridad'),('Usuarios','/usuarios','Seguridad')]
            cur.executemany("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s, %s, %s)", base_mods)
        
        conn.commit(); cur.close(); conn.close()
    except Exception as e: print(f"Error de estructura (ignorado): {e}")

# =========================================================
# MAQUETACIÓN GLOBAL (Diseño + JS CRUD)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        
        menu_html = ""
        # Menú dinámico basado en strMenuPadre
        for m_padre in ["Seguridad", "Principal 1", "Principal 2", "Prueba"]:
            links = "".join([f'<a href="{m['strRuta']}">📦 {m['strNombreModulo']}</a>' for m in all_mods if m['strMenuPadre'] == m_padre])
            if links: menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        
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
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:22px 12px; cursor:pointer; font-size:0.9rem; font-family:inherit; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border-radius:8px; border:1px solid var(--border); box-shadow:0 10px 15px rgba(0,0,0,0.4); z-index:1000;}}
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
        .btn-salir {{ background:#ef4444; color:white; padding:7px 15px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:0.8rem; margin-left:10px; }}
        .user-pill {{ background:rgba(16,185,129,0.1); color:var(--emerald); padding:5px 12px; border-radius:20px; font-size:0.85rem; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; border-radius:8px; width:100%; box-sizing:border-box; margin-bottom:15px;}}
        .modal {{ display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.7); }}
        .modal-content {{ background:var(--card); margin:10% auto; padding:30px; width:400px; border-radius:16px; border:1px solid var(--border); }}
        .icon-circle {{ background:rgba(16,185,129,0.1); width:65px; height:65px; border-radius:14px; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; color:var(--emerald); font-size:24px; border:1px solid rgba(16,185,129,0.3); }}
    </style>
    <script>
        function openM(id, tid=0, name='') {{ 
            const m = document.getElementById(id); m.style.display = 'block';
            if(tid) {{ m.querySelector('[name="id"]').value = tid; if(name) m.querySelector('[name="nombre"]').value = name; }}
            else if(m.querySelector('form')) m.querySelector('form').reset();
        }}
        function closeM(id) {{ document.getElementById(id).style.display = 'none'; }}
        
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{ action, table, id, data }}) }});
            const result = await res.json();
            if(result.ok) location.reload(); else alert('Error: ' + result.msg);
        }}

        async function saveForm(formId, action, table) {{
            const fd = new FormData(document.getElementById(formId));
            const data = Object.fromEntries(fd.entries());
            const id = data.id || 0;
            await runCrud(id ? 'update' : 'create', table, id, data);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)
    inicializar_datos()

    # --- PANTALLA 1: LOGIN (RESTAURADA) ---
    if path in ["/", "/login"] and method == "GET":
        content = """<style>input{{padding:12px 12px 12px 40px!important;}}</style>
        <div class="card" style="width:400px; margin:80px auto; text-align:center;">
            <div class="icon-circle">🛡️</div>
            <h2 style="margin:0; font-size:1.8rem; color:white;">Sistema de Gestión</h2>
            <p style="color:#94a3b8; margin:5px 0 25px;">Ingresa tus credenciales</p>
            <div style="background:rgba(16,185,129,0.05); border:1px solid rgba(16,185,129,0.2); border-radius:10px; padding:15px; margin-bottom:20px; text-align:left; font-size:0.85rem;">
                <b style="color:var(--emerald); display:block; margin-bottom:5px;">ℹ️ Credenciales de prueba:</b>
                Usuario: <code style="color:white;">admin</code> | Clave: <code style="color:white;">123</code>
            </div>
            <form id="fL">
                <div style="position:relative;"><span style="position:absolute; left:14px; top:12px;">👤</span><input name="u" placeholder="Usuario" required></div>
                <div style="position:relative;"><span style="position:absolute; left:14px; top:12px;">🔒</span><input name="p" type="password" placeholder="Contraseña" required></div>
                <div style="margin:20px 0; display:flex; justify-content:center;"><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div></div>
                <button type="button" onclick="doLogin()" class="btn-emerald" style="width:100%; padding:14px;">Iniciar Sesión</button>
            </form>
        </div>
        <script>
            async function doLogin() {{
                if(!grecaptcha.getResponse()) {{ alert("Completa el captcha"); return; }}
                const res = await fetch('/api/login', {{ method:'POST', body:new FormData(document.getElementById('fL')) }});
                const data = await res.json(); if(data.ok) location.href='/dashboard'; else alert('Error de acceso');
            }}
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Acceso", content).encode("utf-8")]

    # --- API LOGIN / API CRUD ---
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
        t, d, id = p['table'], p['data'], p['id']
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {t} WHERE id=%s", (id,))
            elif p['action'] == 'save_perms':
                cur.execute("DELETE FROM permisos WHERE idPerfil=%s", (d['idPerfil'],))
                cur.executemany("INSERT INTO permisos VALUES (%s,%s,%s,%s,%s,%s)", d['perms'])
            elif t == 'perfiles':
                if id: cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (d['nombre'], id))
                else: cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (d['nombre'],))
            elif t == 'modulos':
                sql = "UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s" if id else "INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)"
                args = (d['nombre'], d['ruta'], d['padre'], id) if id else (d['nombre'], d['ruta'], d['padre'])
                cur.execute(sql, args)
            elif t == 'usuarios':
                if id: cur.execute("UPDATE usuarios SET strNombreUsuario=%s, strCorreo=%s, idPerfil=%s WHERE id=%s", (d['u'], d['c'], d['p'], id))
                else: cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, strCorreo, strEstado, idPerfil) VALUES (%s,%s,%s,'Activo',%s)", (d['u'], hash_password(d['pwd']), d['c'], d['p']))
            conn.commit(); r = b'{"ok":true}'
        except Exception as e: r = json.dumps({"ok":false, "msg":str(e)}).encode()
        cur.close(); conn.close(); start_response("200 OK", [("Content-Type", "application/json")]); return [r]

    if not u_data: start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- VISTAS PRIVADAS (CRUD + EDITAR RESTAURADO) ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    
    if path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td style='text-align:right;'><a href='#' class='btn-outline' onclick=\"openM('mP',{p['id']},'{p['strNombrePerfil']}')\">Editar</a><a href='#' class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</a></td></tr>" for p in cur.fetchall()])
        content = f"""<div class="card"><div style="display:flex; justify-content:space-between; align-items:center;"><h2>👤 Gestión de Perfiles</h2><button class="btn-emerald" onclick="openM('mP')">+ Nuevo Perfil</button></div>
            <table><thead><tr><th>ID</th><th>Nombre del Perfil</th><th style="text-align:right;">Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mP" class="modal"><div class="modal-content"><h3>Perfil</h3><form id="fP"><input type="hidden" name="id"><input name="nombre" placeholder="Nombre (Ej: Recursos Humanos)" required></form>
            <button class="btn-emerald" style="width:100%" onclick="saveForm('fP','','perfiles')">Guardar</button><button class="btn-outline" style="width:100%; margin-top:10px;" onclick="closeM('mP')">Cancelar</button></div></div>"""

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td style='text-align:right;'><a href='#' class='btn-outline'>Editar</a><a href='#' class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</a></td></tr>" for m in cur.fetchall()])
        content = f"""<div class="card"><div style="display:flex; justify-content:space-between; align-items:center;"><h2>📦 Módulos</h2><button class="btn-emerald" onclick="openM('mM')">+ Nuevo Módulo</button></div>
            <table><thead><tr><th>Nombre</th><th>Ruta</th><th>Menú Padre</th><th style="text-align:right;">Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mM" class="modal"><div class="modal-content"><h3>Módulo</h3><form id="fM"><input type="hidden" name="id"><input name="nombre" placeholder="Nombre (Ej: Inventario)"><input name="ruta" placeholder="Ruta (Ej: /inventario)">
            <select name="padre"><option value="">-- Agrupar en Menú --</option><option>Seguridad</option><option>Principal 1</option><option>Principal 2</option><option>Prueba</option></select></form>
            <button class="btn-emerald" style="width:100%" onclick="saveForm('fM','','modulos')">Guardar</button><button class="btn-outline" style="width:100%; margin-top:10px;" onclick="closeM('mM')">Cancelar</button></div></div>"""

    elif path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strNombrePerfil'] or '--'}</td><td><a href='#' class='btn-outline'>Editar</a><a href='#' class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</a></td></tr>" for u in cur.fetchall()])
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        content = f"""<div class="card"><div style="display:flex; justify-content:space-between; align-items:center;"><h2>👥 Usuarios</h2><button class="btn-emerald" onclick="openM('mU')">+ Nuevo Usuario</button></div>
            <table><thead><tr><th>Usuario</th><th>Correo</th><th>Perfil</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mU" class="modal"><div class="modal-content"><h3>Usuario</h3><form id="fU"><input type="hidden" name="id"><input name="u" placeholder="Usuario"><input name="c" placeholder="Correo"><input name="pwd" type="password" placeholder="Contraseña"><select name="p">{opts}</select></form>
            <button class="btn-emerald" style="width:100%" onclick="saveForm('fU','','usuarios')">Guardar</button><button class="btn-outline" style="width:100%; margin-top:10px;" onclick="closeM('mU')">Cancelar</button></div></div>"""

    elif path == "/permisos":
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        pid = int(urllib.parse.parse_qs(environ.get('QUERY_STRING','')).get('p',['0'])[0])
        cur.execute("SELECT * FROM permisos WHERE idPerfil=%s", (pid,))
        perms = {{p['idModulo']: p for p in cur.fetchall()}}
        opts = "".join([f"<option value='{p['id']}' {'selected' if p['id']==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = ""
        for m in mods:
            p = perms.get(m['id'], {{'blnCrear':0,'blnEditar':0,'blnEliminar':0,'blnVer':0}})
            chk = lambda k: 'checked' if p[k] else ''
            m_rows += f"<tr data-mid='{m['id']}'><td>{m['strNombreModulo']}</td><td><input type='checkbox' class='c' {chk('blnCrear')}></td><td><input type='checkbox' class='e' {chk('blnEditar')}></td><td><input type='checkbox' class='d' {chk('blnEliminar')}></td><td><input type='checkbox' class='v' {chk('blnVer')}></td></tr>"
        content = f"""<div class="card"><h2>🔐 Matriz de Permisos</h2><div style="display:flex; gap:10px; margin-bottom:20px;"><select id="sP" onchange="location.href='?p='+this.value"><option value="0">-- Selecciona Perfil --</option>{opts}</select>
            <button class="btn-emerald" onclick="savePerms()">Guardar Permisos</button></div><table><thead><tr><th>Módulo</th><th>C</th><th>E</th><th>B</th><th>V</th></tr></thead><tbody>{m_rows}</tbody></table></div>
            <script>async function savePerms(){{ const pid=document.getElementById('sP').value; if(pid=='0') return; const perms=[]; document.querySelectorAll('tbody tr').forEach(r=>{{ perms.push([pid, r.dataset.mid, r.querySelector('.c').checked?1:0, r.querySelector('.e').checked?1:0, r.querySelector('.d').checked?1:0, r.querySelector('.v').checked?1:0]); }}); await runCrud('save_perms','permisos',0,{{idPerfil:pid, perms}}); }}</script>"""

    elif path == "/logout": start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]
    else: content = f"<div class='card' style='text-align:center;'><h1>🛡️</h1><h3>Bienvenido al sistema</h3></div>"

    cur.close(); conn.close(); start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]