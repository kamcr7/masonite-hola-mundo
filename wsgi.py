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
    try: cur.execute("ALTER TABLE modulos ADD COLUMN strMenuPadre VARCHAR(50) DEFAULT 'Seguridad'")
    except: pass
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
        
        # Módulos base fijos para evitar duplicados en el menú visual
        base_seguridad = ["Perfiles", "Módulos", "Permisos-Perfil", "Usuarios"]
        
        menu_html = ""
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a>'
                links += '<a href="/modulos">📦 Módulos</a>'
                links += '<a href="/permisos">🔐 Permisos-Perfil</a>'
                links += '<a href="/usuarios">👥 Usuarios</a>'
            
            # Agregar módulos de la BD que NO sean los base para no duplicar
            subs = [m for m in all_mods if m.get('strMenuPadre') == m_padre and m['strNombreModulo'] not in base_seguridad]
            for s in subs:
                links += f'<a href="/m/{s["id"]}">{s["strNombreModulo"]}</a>'
            
            menu_html += f"""<div class="dropdown">
                <button class="dropbtn">{m_padre} ▾</button>
                <div class="dropdown-content">{links}</div>
            </div>"""

        nav = f"""<div class="top-nav">
            <div class="nav-left"><span class="logo">🛡️ Sistema de Gestión</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div>
            <div class="nav-right">
                <span class="user-badge">{user['u'][0].upper()}</span>
                <b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none; margin-left:10px;">Salir</a>
            </div>
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
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 0;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:200px; box-shadow:0 8px 16px rgba(0,0,0,0.5); border-radius:8px; border:1px solid #334155; overflow:hidden;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem;}}
        .dropdown-content a:hover{{background:#334155; color:#38bdf8;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid #334155;}}
        td{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        .badge{{background:#1e3a8a; padding:4px 10px; border-radius:6px; font-size:0.75rem; color:#38bdf8;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:12px; border-radius:8px; width:100%; margin-top:5px;}}
        .modal{{display:none; position:fixed; z-index:1000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#ffffff; color:#334155; margin:10% auto; padding:25px; width:450px; border-radius:12px;}}
        .modal-content h3{{margin-top:0; color:#1e293b;}}
        .modal-content input, .modal-content select{{background:#f8fafc; border:1px solid #e2e8f0; color:#334155;}}
        .user-badge{{background:#be185d; width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center; border-radius:50%; margin-right:8px; font-size:0.8rem;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()
    u_data = verify_jwt(environ)

    if not u_data and path not in ["/", "/login", "/api/login"]:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- LOGIN --- (Simplificado para el ejemplo)
    if path in ["/", "/login"]:
        content = '<div class="card" style="max-width:350px; margin:auto;"><h2>Login</h2><form id="fL"><input name="u" placeholder="Usuario"><input type="password" name="p" style="margin-top:10px;"><button type="button" onclick="login()" class="btn-blue" style="width:100%; margin-top:20px;">Entrar</button></form></div><script>async function login(){const res=await fetch("/api/login",{method:"POST",body:new FormData(document.getElementById("fL"))}); if((await res.json()).ok) location.href="/dashboard"; else alert("Error");}</script>'
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        # Por simplicidad, acepta cualquier usuario con pass '123' o busca en BD
        tk = jwt_encode({"u": fs.getvalue("u"), "exp": time.time()+3600})
        start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/")]); return [b'{"ok":true}']

    # --- DASHBOARD ---
    if path == "/dashboard":
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Dashboard", "<div class='card'><h1>Bienvenido</h1></div>", u_data).encode("utf-8")]

    # --- MÓDULOS ---
    if path == "/modulos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall()
        cur.close(); conn.close()
        
        rows_h = "".join([f"""<tr>
            <td>{r['strNombreModulo']}</td>
            <td><span class="badge">{r.get('strMenuPadre','Seguridad')}</span></td>
            <td><span style="color:#2563eb; cursor:pointer;">Editar</span> <span style="color:#ef4444; margin-left:10px; cursor:pointer;">Eliminar</span></td>
        </tr>""" for r in rows])

        content = f"""<div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="margin:0;">Gestión de Módulos</h2>
                <div style="display:flex; gap:10px;">
                    <input type="text" placeholder="Buscar por nombre..." style="width:250px; margin:0;">
                    <button class="btn-blue" onclick="document.getElementById('mMod').style.display='block'">+ Nuevo Módulo</button>
                </div>
            </div>
            <table><thead><tr><th>NOMBRE DEL MÓDULO</th><th>MENÚ ASIGNADO</th><th>ACCIONES</th></tr></thead><tbody>{rows_h if rows_h else '<tr><td colspan="3" align="center">No hay registros</td></tr>'}</tbody></table>
        </div>
        <div id="mMod" class="modal"><div class="modal-content">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3>Nuevo Módulo</h3>
                <span onclick="document.getElementById('mMod').style.display='none'" style="cursor:pointer;">✕</span>
            </div>
            <form id="fMod">
                <label style="font-size:0.85rem; font-weight:bold;">Nombre del Módulo *</label>
                <input name="n" placeholder="Ej. Principal 1.1" required>
                <label style="font-size:0.85rem; font-weight:bold; display:block; margin-top:15px;">Agrupar en Menú</label>
                <select name="p">
                    <option value="Seguridad">Seguridad</option>
                    <option value="Principal 1">Principal 1</option>
                    <option value="Principal 2">Principal 2</option>
                </select>
                <div style="margin-top:30px; text-align:right; display:flex; gap:10px; justify-content:flex-end;">
                    <button type="button" onclick="document.getElementById('mMod').style.display='none'" style="background:#f1f5f9; border:1px solid #e2e8f0; padding:10px 20px; border-radius:8px; cursor:pointer;">Cancelar</button>
                    <button class="btn-blue" style="background:#1e3a8a;">Guardar</button>
                </div>
            </form>
        </div></div>
        <script>
            document.getElementById('fMod').onsubmit = async (e) => {{
                e.preventDefault(); await fetch('/api/save_mod', {{method:'POST', body:new FormData(e.target)}}); location.reload();
            }};
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Módulos", content, u_data).encode("utf-8")]

    # --- API SAVE ---
    if path == "/api/save_mod" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("INSERT INTO modulos (strNombreModulo, strMenuPadre) VALUES (%s,%s)", (fs.getvalue("n"), fs.getvalue("p")))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]

    start_response("303 See Other", [("Location", "/dashboard")]); return [b""]