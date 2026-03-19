# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN Y SEGURIDAD
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
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))")
    cur.execute("CREATE TABLE IF NOT EXISTS permisos_perfil (id INT AUTO_INCREMENT PRIMARY KEY, idPerfil INT, idModulo INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), imgUsuario LONGTEXT)")
    try: cur.execute("ALTER TABLE usuarios ADD COLUMN idPerfil INT AFTER strNombreUsuario")
    except: pass
    conn.commit(); cur.close(); conn.close()

# =========================================================
# DISEÑO VISUAL (MODO OSCURO PROFESIONAL)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""
        <div class="top-nav">
            <div class="nav-left">
                <span class="logo">🛡️ Sistema de Gestión</span>
                <a href="/dashboard" class="nav-link">Inicio</a>
                <div class="dropdown">
                    <button class="dropbtn">Seguridad ▼</button>
                    <div class="dropdown-content">
                        <a href="/perfiles">👤 Perfiles</a>
                        <a href="/modulos">📦 Módulos</a>
                        <a href="/permisos">🔐 Permisos-Perfil</a>
                        <a href="/usuarios">👥 Usuarios</a>
                    </div>
                </div>
            </div>
            <div class="nav-right">
                <span class="user-badge">{user['u'][0].upper()}</span>
                <b>{user['u']}</b> | <a href="/logout" style="color:#f87171; text-decoration:none; margin-left:10px;">Salir</a>
            </div>
        </div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:'Inter', sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; position:sticky; top:0; z-index:100;}}
        .nav-left{{display:flex; gap:25px; align-items:center;}}
        .logo{{font-weight:bold; color:#38bdf8; font-size:1.1rem; margin-right:10px;}}
        .nav-link{{color:#94a3b8; text-decoration:none; font-size:0.9rem; transition:0.3s;}}
        .nav-link:hover{{color:white;}}
        
        /* DROPDOWN ESTILO IMAGEN REFERENCIA */
        .dropdown {{position: relative; display: inline-block;}}
        .dropbtn {{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 0; font-family:inherit;}}
        .dropdown:hover .dropbtn {{color:white;}}
        .dropdown-content {{display: none; position: absolute; background:#1e293b; min-width:180px; box-shadow:0 8px 16px rgba(0,0,0,0.5); border-radius:8px; border:1px solid #334155; margin-top:0; overflow:hidden;}}
        .dropdown-content a {{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem; transition:0.2s;}}
        .dropdown-content a:hover {{background:#334155; color:#38bdf8;}}
        .dropdown:hover .dropdown-content {{display: block;}}
        
        .nav-right{{display:flex; align-items:center; gap:12px;}}
        .user-badge{{background:#be185d; width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:50%; font-size:0.8rem;}}
        
        .container{{padding:40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:12px; border-bottom:1px solid #334155;}}
        td{{padding:14px 12px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        .badge{{padding:4px 10px; border-radius:12px; font-size:0.7rem; font-weight:bold;}}
        .badge-si{{background:rgba(16,185,129,0.2); color:#10b981;}}
        .badge-no{{background:rgba(245,158,11,0.2); color:#f59e0b;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:6px; margin:5px 0; width:100%;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# LÓGICA DE APLICACIÓN
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()

    # --- LOGIN ---
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:320px; margin:100px auto; text-align:center;">
            <h2 style="color:#38bdf8;">Clínica Santa Mónica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" required>
                <input type="password" name="p" placeholder="Contraseña" required>
                <div style="margin:20px 0; display:flex; justify-content:center;">
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                </div>
                <button type="button" id="btnIn" class="btn-blue" style="width:100%;">Entrar</button>
            </form><div id="msg" style="color:#f87171; margin-top:10px;"></div></div>
            <script>
                document.getElementById('btnIn').onclick = async () => {
                    if(!grecaptcha.getResponse()) { alert("Valida el captcha"); return; }
                    const res = await fetch('/api/login', {method:'POST', body:new FormData(document.getElementById('fL'))});
                    const d = await res.json();
                    if(d.ok) window.location.href='/dashboard';
                    else document.getElementById('msg').innerText = "Error de acceso";
                };
            </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

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

    # --- PROTECCIÓN ---
    u_data = verify_jwt(environ)
    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- PANTALLA PRINCIPAL ---
    if path == "/dashboard":
        content = f"""
        <div class="card" style="text-align:center; padding:50px;">
            <h1 style="color:#38bdf8;">Bienvenido, {u_data['u']}</h1>
            <p style="color:#94a3b8;">Sistema Corporativo - Clínica Santa Mónica</p>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:20px; margin-top:40px;">
                <div style="background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334155;">
                    <h3 style="margin:0;">Perfiles</h3>
                    <a href="/perfiles" style="color:#38bdf8; text-decoration:none; font-size:0.8rem;">Gestionar →</a>
                </div>
                <div style="background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334155;">
                    <h3 style="margin:0;">Usuarios</h3>
                    <a href="/usuarios" style="color:#38bdf8; text-decoration:none; font-size:0.8rem;">Gestionar →</a>
                </div>
            </div>
        </div>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Inicio", content, u_data).encode("utf-8")]

    # --- CRUD PERFILES (COMO TU IMAGEN) ---
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall()
        cur.close(); conn.close()
        
        rows_html = "".join([f"<tr><td>{r['id']}</td><td><b>{r['strNombrePerfil']}</b></td><td>Sin descripción</td><td><span class='badge {'badge-si' if r['bitAdministrador'] else 'badge-no'}'>{'Sí' if r['bitAdministrador'] else 'No'}</span></td><td>19 mar 2026</td><td>👁️ ✏️ 🗑️</td></tr>" for r in rows])
        
        content = f"""<div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h2>Gestión de Perfiles</h2>
                <button class="btn-blue" onclick="document.getElementById('fAdd').style.display='block'">+ Nuevo</button>
            </div>
            <div id="fAdd" style="display:none; background:#0f172a; padding:20px; border-radius:10px; margin-bottom:20px; border:1px dashed #334155;">
                <form id="formP" style="display:flex; gap:15px; align-items:center;">
                    <input name="n" placeholder="Nombre del Perfil" required style="width:250px;">
                    <label>Admin: <input type="checkbox" name="a" style="width:auto;"></label>
                    <button class="btn-blue">Guardar</button>
                </form>
            </div>
            <input type="text" placeholder="Buscar perfiles..." style="background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:8px; width:100%;">
            <table>
                <thead><tr><th>#</th><th>Nombre Perfil</th><th>Descripción</th><th>Administrador</th><th>Creado</th><th>Acciones</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        <script>
            document.getElementById('formP').onsubmit = async (e) => {{
                e.preventDefault();
                await fetch('/api/save_perfiles', {{method:'POST', body:new FormData(e.target)}});
                location.reload();
            }};
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Perfiles", content, u_data).encode("utf-8")]

    # --- API GENÉRICA PARA GUARDAR ---
    if path.startswith("/api/save_") and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        conn = conectar_bd(); cur = conn.cursor()
        if path == "/api/save_perfiles":
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s,%s)", (fs.getvalue("n"), 1 if fs.getvalue("a") else 0))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0")]); return [b""]

    start_response("404 Not Found", []); return [b"Pagina no encontrada"]