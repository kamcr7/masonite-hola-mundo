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
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))")
    cur.execute("CREATE TABLE IF NOT EXISTS permisos_perfil (id INT AUTO_INCREMENT PRIMARY KEY, idPerfil INT, idModulo INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), imgUsuario LONGTEXT)")
    # Asegurar columna idPerfil por si hubo errores previos
    try: cur.execute("ALTER TABLE usuarios ADD COLUMN idPerfil INT AFTER strNombreUsuario")
    except: pass
    conn.commit(); cur.close(); conn.close()

def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""<div style="background:#0b1120; color:white; padding:15px 40px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b;">
            <div style="display:flex; gap:25px; align-items:center;">
                <span style="font-weight:bold; color:#38bdf8; font-size:1.1rem;">🛡️ Sistema de Gestión</span>
                <a href="/perfiles" style="color:#94a3b8; text-decoration:none; font-size:0.9rem;">Seguridad</a>
                <a href="/modulos" style="color:#94a3b8; text-decoration:none; font-size:0.9rem;">Módulos</a>
                <a href="/permisos" style="color:#94a3b8; text-decoration:none; font-size:0.9rem;">Permisos</a>
                <a href="/usuarios" style="color:#94a3b8; text-decoration:none; font-size:0.9rem;">Usuarios</a>
            </div>
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="background:#be185d; width:30px; height:30px; display:flex; align-items:center; justify-content:center; border-radius:50%; font-size:0.8rem; font-weight:bold;">{user['u'][0].upper()}</span>
                <span style="font-size:0.9rem;"><b>{user['u']}</b></span>
                <a href="/logout" style="color:#ef4444; text-decoration:none; font-size:0.8rem; margin-left:10px;">Salir</a>
            </div>
        </div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:'Inter', sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:24px; border:1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);}}
        .header-flex{{display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 18px; border-radius:8px; cursor:pointer; font-weight:600; font-size:0.85rem;}}
        .btn-green{{background:#16a34a; color:white; border:none; padding:10px; border-radius:8px; cursor:pointer;}}
        .search-input{{width:100%; background:#0f172a; border:1px solid #334155; padding:12px; border-radius:8px; color:white; margin:15px 0; font-size:0.9rem;}}
        table{{width:100%; border-collapse:collapse;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:12px; border-bottom:1px solid #334155;}}
        td{{padding:16px 12px; border-bottom:1px solid #334155; font-size:0.9rem; color:#e2e8f0;}}
        .badge-yes{{background:rgba(6,78,59,0.5); color:#34d399; padding:4px 12px; border-radius:20px; font-size:0.7rem; font-weight:bold; border:1px solid #064e3b;}}
        .badge-no{{background:rgba(69,26,3,0.5); color:#fbbf24; padding:4px 12px; border-radius:20px; font-size:0.7rem; font-weight:bold; border:1px solid #451a03;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:6px; margin:5px 0;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()

    # --- LOGIN ---
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:350px; margin:80px auto; text-align:center;">
            <h2 style="color:#38bdf8; margin-bottom:25px;">Clínica Santa Mónica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" style="width:100%; margin-bottom:15px;" required>
                <input type="password" name="p" placeholder="Contraseña" style="width:100%; margin-bottom:20px;" required>
                <div style="margin-bottom:20px; display:flex; justify-content:center;">
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                </div>
                <button type="button" id="btnIn" class="btn-blue" style="width:100%; padding:12px;">Entrar al Sistema</button>
            </form><div id="msg" style="color:#ef4444; margin-top:15px; font-size:0.85rem;"></div></div>
            <script>
                document.getElementById('btnIn').onclick = async () => {
                    if(!grecaptcha.getResponse()) { document.getElementById('msg').innerText = "Por favor, valida el captcha"; return; }
                    const fd = new FormData(document.getElementById('fL'));
                    const res = await fetch('/api/login', {method:'POST', body:fd});
                    const d = await res.json();
                    if(d.ok) window.location.replace('/perfiles');
                    else { document.getElementById('msg').innerText = "Credenciales incorrectas"; grecaptcha.reset(); }
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

    # --- SEGURIDAD ---
    u_data = verify_jwt(environ)
    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API GUARDAR ---
    if path.startswith("/api/save_") and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        conn = conectar_bd(); cur = conn.cursor()
        if path == "/api/save_perfiles":
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s,%s)", (fs.getvalue("n"), 1 if fs.getvalue("a") else 0))
        elif path == "/api/save_modulos":
            cur.execute("INSERT INTO modulos (strNombreModulo) VALUES (%s)", (fs.getvalue("n"),))
        elif path == "/api/save_usuarios":
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strCorreo, idEstadoUsuario, imgUsuario) VALUES (%s,%s,%s,%s,1,%s)", 
                (fs.getvalue("u"), hash_password(fs.getvalue("p")), fs.getvalue("pid"), fs.getvalue("e"), fs.getvalue("img")))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTA PERFILES (DISEÑO SOLICITADO) ---
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall()
        cur.close(); conn.close()
        
        rows_html = "".join([f"""<tr>
            <td style='color:#94a3b8;'>{r['id']}</td>
            <td style='font-weight:600;'>{r['strNombrePerfil']}</td>
            <td style='color:#64748b;'>Sin descripción</td>
            <td><span class='{"badge-yes" if r['bitAdministrador'] else "badge-no"}'>{"Sí" if r['bitAdministrador'] else "No"}</span></td>
            <td style='color:#64748b;'>19 mar 2026</td>
            <td><span style='cursor:pointer;'>👁️ ✏️ 🗑️</span></td>
        </tr>""" for r in rows])

        form = """<div id="formAdd" style="display:none; background:#0f172a; padding:20px; border-radius:10px; margin-bottom:20px; border:1px dashed #334155;">
            <form id="f" style="display:flex; gap:15px; align-items:center;">
                <input name="n" placeholder="Nombre Perfil" required style="flex:1;">
                <label style="font-size:0.8rem;">Admin: <input type="checkbox" name="a"></label>
                <button class="btn-blue">Guardar Perfil</button>
            </form></div>"""

        content = f"""<div class="card">
            <div class="header-flex">
                <div>
                    <h2 style="margin:0; font-size:1.5rem;">Gestión de Perfiles</h2>
                    <span style="font-size:0.8rem; color:#94a3b8;">{len(rows)} registros encontrados</span>
                </div>
                <div style="display:flex; gap:10px;">
                    <button class="btn-green">📊</button>
                    <button class="btn-blue" onclick="document.getElementById('formAdd').style.display='block'">+ Nuevo</button>
                </div>
            </div>
            {form}
            <input type="text" class="search-input" placeholder="Buscar por nombre o descripción...">
            <table>
                <thead><tr><th>#</th><th>Nombre Perfil ↑↓</th><th>Descripción ↑↓</th><th>Administrador</th><th>Creado</th><th>Acciones</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>"""
        
        script = """<script>
            if(document.getElementById('f')){
                document.getElementById('f').onsubmit = async (e) => {
                    e.preventDefault();
                    await fetch('/api/save_perfiles', {method:'POST', body:new FormData(e.target)});
                    location.reload();
                };
            }
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [(render_layout("Perfiles", content, u_data)+script).encode("utf-8")]

    # --- LOGOUT ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0")]); return [b""]

    # Redirección por defecto
    start_response("303 See Other", [("Location", "/perfiles")]); return [b""]