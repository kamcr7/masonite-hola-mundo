# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@mysql.railway.internal:3306/railway')
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

def init_db():
    conn = conectar_bd(); cur = conn.cursor(buffered=True)
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50), strMenuPadre VARCHAR(50))")
    cur.execute("CREATE TABLE IF NOT EXISTS permisos_perfil (id INT AUTO_INCREMENT PRIMARY KEY, idPerfil INT, idModulo INT, can_view TINYINT(1), can_add TINYINT(1), can_edit TINYINT(1), can_del TINYINT(1))")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), imgUsuario LONGTEXT)")
    conn.commit(); cur.close(); conn.close()

# =========================================================
# MAQUETACIÓN (LAYOUT)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        
        menu_html = ""
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos-Perfil</a>'
            
            subs = [m for m in all_mods if m['strMenuPadre'] == m_padre]
            for s in subs:
                links += f'<a href="/m/{s["id"]}">{s["strNombreModulo"]}</a>'
            
            menu_html += f"""<div class="dropdown">
                <button class="dropbtn">{m_padre} {'▴' if m_padre=='Seguridad' else '▾'}</button>
                <div class="dropdown-content">{links}</div>
            </div>"""

        nav = f"""<div class="top-nav">
            <div class="nav-left"><span class="logo">🛡️ Sistema de Gestión</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div>
            <div class="nav-right"><span class="user-badge">{user['u'][0].upper()}</span><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none; margin-left:10px;">Salir</a></div>
        </div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; position:sticky; top:0; z-index:100;}}
        .nav-left{{display:flex; gap:20px; align-items:center;}}
        .logo{{font-weight:bold; color:#38bdf8; font-size:1.1rem;}}
        .nav-link{{color:#94a3b8; text-decoration:none; font-size:0.9rem;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 0; font-family:inherit;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:180px; box-shadow:0 8px 16px rgba(0,0,0,0.5); border-radius:8px; border:1px solid #334155; overflow:hidden;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem;}}
        .dropdown-content a:hover{{background:#334155; color:#38bdf8;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600;}}
        .btn-save{{background:#1e3a8a; color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; float:right; margin-top:20px;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid #334155;}}
        td{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:8px; width:100%; box-sizing:border-box;}}
        .user-badge{{background:#be185d; width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center; border-radius:50%; margin-right:8px;}}
        .modal{{display:none; position:fixed; z-index:1000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#1e293b; margin:10% auto; padding:25px; width:450px; border-radius:12px; border:1px solid #334155; position:relative;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()
    u_data = verify_jwt(environ)

    # --- LOGIN ---
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:350px; margin:100px auto; text-align:center;">
            <h2 style="color:#38bdf8;">Clínica Santa Mónica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" required style="margin-bottom:15px;">
                <input type="password" name="p" placeholder="Contraseña" required style="margin-bottom:20px;">
                <div style="margin-bottom:20px; display:flex; justify-content:center;">
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                </div>
                <button type="button" id="btnIn" class="btn-blue" style="width:100%;">Entrar</button>
            </form></div>
            <script>
                document.getElementById('btnIn').onclick = async () => {
                    if(!grecaptcha.getResponse()) { alert("Captcha requerido"); return; }
                    const res = await fetch('/api/login', {method:'POST', body:new FormData(document.getElementById('fL'))});
                    if((await res.json()).ok) window.location.href='/dashboard'; else alert("Error");
                };
            </script>"""
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

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- DASHBOARD ---
    if path == "/dashboard":
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Inicio", "<div class='card'><h1>Bienvenido</h1></div>", u_data).encode("utf-8")]

    # --- PERFILES ---
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall()
        cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'Sí' if r['bitAdministrador'] else 'No'}</td><td><button class='btn-blue' style='padding:5px 10px;'>✎</button></td></tr>" for r in rows])
        content = f"<div class='card'><h2>Gestión de Perfiles</h2><table><thead><tr><th>ID</th><th>Nombre</th><th>Admin</th><th>Acción</th></tr></thead><tbody>{rows_h}</tbody></table></div>"
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Perfiles", content, u_data).encode("utf-8")]

    # --- MÓDULOS (DISEÑO SOLICITADO) ---
    if path == "/modulos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall()
        cur.close(); conn.close()
        
        rows_h = "".join([f"<tr><td>{r['strNombreModulo']}</td><td><span style='background:#1e3a8a; padding:4px 8px; border-radius:5px;'>{r['strMenuPadre']}</span></td><td style='color:#38bdf8;'>Editar <span style='color:#ef4444; margin-left:10px;'>Eliminar</span></td></tr>" for r in rows])
        
        content = f"""<div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2>Gestión de Módulos</h2>
                <button class="btn-blue" onclick="document.getElementById('mMod').style.display='block'">+ Nuevo Módulo</button>
            </div>
            <table><thead><tr><th>NOMBRE DEL MÓDULO</th><th>MENÚ ASIGNADO</th><th>ACCIONES</th></tr></thead><tbody>{rows_h}</tbody></table>
        </div>
        <div id="mMod" class="modal"><div class="modal-content">
            <h3>Nuevo Módulo</h3>
            <form id="fMod">
                <p>Nombre del Módulo *</p><input name="n" required>
                <p>Agrupar en Menú</p>
                <select name="p">
                    <option value="Seguridad">Seguridad</option>
                    <option value="Principal 1">Principal 1</option>
                    <option value="Principal 2">Principal 2</option>
                </select>
                <div style="margin-top:20px; text-align:right;">
                    <button type="button" onclick="document.getElementById('mMod').style.display='none'" class="btn-ghost">Cancelar</button>
                    <button class="btn-blue">Guardar</button>
                </div>
            </form>
        </div></div>
        <script>
            document.getElementById('fMod').onsubmit = async (e) => {{
                e.preventDefault(); await fetch('/api/save_mod', {{method:'POST', body:new FormData(e.target)}}); location.reload();
            }};
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Módulos", content, u_data).encode("utf-8")]

    # --- MATRIZ DE PERMISOS ---
    if path == "/permisos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        cur.execute("SELECT id, strNombreModulo FROM modulos"); mods = cur.fetchall()
        qs = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
        pid = qs.get('pid', [None])[0]
        
        permisos = {}
        if pid:
            cur.execute("SELECT * FROM permisos_perfil WHERE idPerfil=%s", (pid,))
            for p in cur.fetchall(): permisos[p['idModulo']] = p
        
        opt = "".join([f"<option value='{x['id']}' {'selected' if str(x['id'])==pid else ''}>{x['strNombrePerfil']}</option>" for x in perfs])
        
        tbody = ""
        for m in mods:
            p = permisos.get(m['id'], {'can_view':0, 'can_add':0, 'can_edit':0, 'can_del':0})
            tbody += f"<tr><td>{m['strNombreModulo']}<input type='hidden' name='mid' value='{m['id']}'></td>"
            for k in ['v','a','e','d']:
                key = {'v':'can_view','a':'can_add','e':'can_edit','d':'can_del'}[k]
                tbody += f"<td align='center'><input type='checkbox' name='{k}_{m['id']}' {'checked' if p[key] else ''}></td>"
            tbody += "</tr>"

        content = f"""<div class="card">
            <h2>Matriz de Permisos</h2>
            Perfil: <select onchange="location.href='/permisos?pid='+this.value" style="width:300px;"><option value=''>-- Seleccionar --</option>{opt}</select>
            {f'<form id="fM"><input type="hidden" name="pid" value="{pid}"><table><thead><tr><th>Módulo</th><th>CONSULTAR</th><th>AGREGAR</th><th>EDITAR</th><th>ELIMINAR</th></tr></thead><tbody>{tbody}</tbody></table><button class="btn-save">Guardar Matriz de Permisos</button></form>' if pid else ''}
        </div>
        <script>
            if(document.getElementById('fM')) document.getElementById('fM').onsubmit = async (e) => {{
                e.preventDefault(); await fetch('/api/save_permisos', {{method:'POST', body:new FormData(e.target)}}); alert("Permisos Guardados");
            }};
        </script>"""
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Permisos", content, u_data).encode("utf-8")]

    # --- API AUXILIARES ---
    if path == "/api/save_mod" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("INSERT INTO modulos (strNombreModulo, strMenuPadre) VALUES (%s,%s)", (fs.getvalue("n"), fs.getvalue("p")))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    if path == "/api/save_permisos" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        pid = fs.getvalue("pid")
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("DELETE FROM permisos_perfil WHERE idPerfil=%s", (pid,))
        for mid in fs.getlist("mid"):
            cur.execute("INSERT INTO permisos_perfil (idPerfil, idModulo, can_view, can_add, can_edit, can_del) VALUES (%s,%s,%s,%s,%s,%s)", 
                       (pid, mid, 1 if fs.getvalue(f"v_{mid}") else 0, 1 if fs.getvalue(f"a_{mid}") else 0, 1 if fs.getvalue(f"e_{mid}") else 0, 1 if fs.getvalue(f"d_{mid}") else 0))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]

    start_response("303 See Other", [("Location", "/dashboard")]); return [b""]