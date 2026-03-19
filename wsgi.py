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
    cur.execute("CREATE TABLE IF NOT EXISTS permisos_perfil (id INT AUTO_INCREMENT PRIMARY KEY, idPerfil INT, idModulo INT, can_view TINYINT(1), can_add TINYINT(1), can_edit TINYINT(1), can_del TINYINT(1))")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), imgUsuario LONGTEXT)")
    conn.commit(); cur.close(); conn.close()

# =========================================================
# MAQUETACIÓN (NAVBAR Y CSS)
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
                <b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none;">Salir</a>
            </div>
        </div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        body{{font-family:'Segoe UI', sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; position:sticky; top:0; z-index:100;}}
        .nav-left{{display:flex; gap:25px; align-items:center;}}
        .logo{{font-weight:bold; color:#38bdf8; font-size:1.1rem;}}
        .nav-link{{color:#94a3b8; text-decoration:none; font-size:0.9rem;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 0;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:180px; border-radius:8px; border:1px solid #334155; overflow:hidden;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px; text-decoration:none; display:block; font-size:0.85rem;}}
        .dropdown-content a:hover{{background:#334155; color:#38bdf8;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600;}}
        .btn-save{{background:#1e3a8a; color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; float:right; margin-top:15px;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px; background:#1e293b;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid #334155;}}
        td{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        .badge-si{{background:rgba(16,185,129,0.1); color:#10b981; padding:4px 10px; border-radius:20px; font-size:0.7rem; border:1px solid #064e3b;}}
        .badge-no{{background:rgba(245,158,11,0.1); color:#f59e0b; padding:4px 10px; border-radius:20px; font-size:0.7rem; border:1px solid #451a03;}}
        input[type="text"], select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:8px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# APP PRINCIPAL
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()
    u_data = verify_jwt(environ)

    # --- API: ELIMINAR ---
    if path.startswith("/api/delete_") and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        table = path.replace("/api/delete_", "")
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute(f"DELETE FROM {table} WHERE id=%s", (fs.getvalue("id"),))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- API: GUARDAR PERMISOS ---
    if path == "/api/save_matriz" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        pid = fs.getvalue("pid")
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("DELETE FROM permisos_perfil WHERE idPerfil=%s", (pid,))
        # Recorrer módulos enviados
        mods = fs.getlist("mid")
        for mid in mods:
            v = 1 if fs.getvalue(f"v_{mid}") else 0
            a = 1 if fs.getvalue(f"a_{mid}") else 0
            e = 1 if fs.getvalue(f"e_{mid}") else 0
            d = 1 if fs.getvalue(f"d_{mid}") else 0
            cur.execute("INSERT INTO permisos_perfil (idPerfil, idModulo, can_view, can_add, can_edit, can_del) VALUES (%s,%s,%s,%s,%s,%s)", (pid, mid, v, a, e, d))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTA: PERMISOS (MATRIZ) ---
    if path == "/permisos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        cur.execute("SELECT id, strNombreModulo FROM modulos"); mods = cur.fetchall()
        
        selected_pid = cgi.parse_qs(environ.get('QUERY_STRING', '')).get('pid', [None])[0]
        permisos_actuales = {}
        if selected_pid:
            cur.execute("SELECT * FROM permisos_perfil WHERE idPerfil=%s", (selected_pid,))
            for p in cur.fetchall(): permisos_actuales[p['idModulo']] = p
        
        opt_perfil = "".join([f"<option value='{p['id']}' {'selected' if str(p['id'])==selected_pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        
        tbody = ""
        for m in mods:
            p = permisos_actuales.get(m['id'], {'can_view':0, 'can_add':0, 'can_edit':0, 'can_del':0})
            tbody += f"""<tr>
                <td>{m['strNombreModulo']}<input type="hidden" name="mid" value="{m['id']}"></td>
                <td align="center"><input type="checkbox" name="v_{m['id']}" {'checked' if p['can_view'] else ''}></td>
                <td align="center"><input type="checkbox" name="a_{m['id']}" {'checked' if p['can_add'] else ''}></td>
                <td align="center"><input type="checkbox" name="e_{m['id']}" {'checked' if p['can_edit'] else ''}></td>
                <td align="center"><input type="checkbox" name="d_{m['id']}" {'checked' if p['can_del'] else ''}></td>
            </tr>"""

        content = f"""<div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h2>Matriz de Permisos</h2>
                <div>Perfil: <select onchange="window.location.href='/permisos?pid='+this.value">{f"<option value=''>-- Seleccione Perfil --</option>" + opt_perfil}</select></div>
            </div>
            {f'''<form id="fMatriz">
                <input type="hidden" name="pid" value="{selected_pid}">
                <table>
                    <thead><tr><th>Módulo</th><th>Consultar</th><th>Agregar</th><th>Editar</th><th>Eliminar</th></tr></thead>
                    <tbody>{tbody}</tbody>
                </table>
                <button type="submit" class="btn-save">Guardar Matriz de Permisos</button>
            </form>''' if selected_pid else '<p style="text-align:center; padding:40px; color:#94a3b8;">Selecciona un perfil para ver y editar sus permisos.</p>'}
        </div>
        <script>
            if(document.getElementById('fMatriz')){{
                document.getElementById('fMatriz').onsubmit = async (e) => {{
                    e.preventDefault();
                    const res = await fetch('/api/save_matriz', {{method:'POST', body:new FormData(e.target)}});
                    if((await res.json()).ok) alert("Permisos actualizados");
                }};
            }}
        </script>"""
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Permisos", content, u_data).encode("utf-8")]

    # --- LOGIN Y OTRAS RUTAS (RESUMIDAS PARA EL EJEMPLO) ---
    if not u_data and path not in ["/", "/login", "/api/login"]:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # Redirección por defecto a Perfiles si no hay ruta
    start_response("303 See Other", [("Location", "/permisos")]); return [b""]