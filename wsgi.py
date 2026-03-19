# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN Y UTILIDADES
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
        # Evitamos duplicados en el menú lateral
        bloqueados = ["perfil", "módulo", "modulo", "usuario", "permisos-perfil"]
        
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a>'
                links += '<a href="/modulos">📦 Módulos</a>'
                links += '<a href="/permisos">🔐 Permisos-Perfil</a>'
                links += '<a href="/usuarios">👥 Usuarios</a>'
            
            subs = [m for m in all_mods if m.get('strMenuPadre') == m_padre and m['strNombreModulo'].lower().strip() not in bloqueados]
            for s in subs:
                links += f'<a href="/m/{s["id"]}">📄 {s["strNombreModulo"]}</a>'
            
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'

        nav = f"""<div class="top-nav">
            <div class="nav-left"><span class="logo">🛡️ Clínica Santa Mónica</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div>
            <div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none; margin-left:10px;">Salir</a></div>
        </div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        body{{font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; position:sticky; top:0; z-index:100;}}
        .nav-left{{display:flex; gap:15px; align-items:center;}}
        .logo{{font-weight:bold; color:#38bdf8; font-size:1.1rem;}}
        .nav-link{{color:#94a3b8; text-decoration:none; font-size:0.9rem; margin-right:15px;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 10px;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:200px; box-shadow:0 8px 16px rgba(0,0,0,0.5); border-radius:8px; border:1px solid #334155; z-index:1000;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem;}}
        .dropdown-content a:hover{{background:#334155; color:#38bdf8;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; padding:15px; border-bottom:2px solid #334155;}}
        td{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:8px;}}
        .modal{{display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#ffffff; color:#334155; margin:10% auto; padding:25px; width:450px; border-radius:12px; position:relative;}}
        .modal-content input, .modal-content select {{background:#f8fafc; border:1px solid #e2e8f0; color:#334155; width:100%; margin-bottom:15px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # --- ENDPOINTS API PARA CRUD DE MÓDULOS ---
    if path == "/api/save_mod" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        n, p = fs.getvalue("n"), fs.getvalue("p")
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("INSERT INTO modulos (strNombreModulo, strMenuPadre) VALUES (%s, %s)", (n, p))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    if path == "/api/del_mod" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        mid = fs.getvalue("id")
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("DELETE FROM modulos WHERE id = %s", (mid,))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    if not u_data and path not in ["/", "/login", "/api/login"]:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- RUTA PERFILES ---
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall(); cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'SÍ' if r['bitAdministrador'] else 'NO'}</td><td style='color:#38bdf8;'>Editar</td></tr>" for r in rows])
        content = f"<div class='card'><h2>Gestión de Perfiles</h2><table><thead><tr><th>ID</th><th>Perfil</th><th>Admin</th><th>Acciones</th></tr></thead><tbody>{rows_h}</tbody></table></div>"
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Perfiles", content, u_data).encode("utf-8")]

    # --- RUTA PERMISOS (MOSTRAR SOLO SI HAY SELECCIÓN) ---
    if path == "/permisos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        qs = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
        pid = qs.get('pid', [None])[0]
        
        opt = "".join([f"<option value='{p['id']}' {'selected' if str(p['id'])==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        
        inner = ""
        if pid:
            cur.execute("SELECT id, strNombreModulo FROM modulos"); mods = cur.fetchall()
            tbody = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
            inner = f"<table><thead><tr><th>Módulo</th><th>CONSULTAR</th><th>AGREGAR</th><th>EDITAR</th><th>ELIMINAR</th></tr></thead><tbody>{tbody}</tbody></table><div style='text-align:right; margin-top:20px;'><button class='btn-blue'>Guardar Cambios</button></div>"
        else:
            inner = "<div style='text-align:center; padding:50px; color:#64748b;'><h3> Seleccione un perfil para ver sus permisos.</h3></div>"
        
        content = f"<div class='card'><h2>Matriz de Permisos</h2> Perfil: <select onchange='location.href=\"/permisos?pid=\"+this.value' style='width:250px;'><option value=''>-- Seleccionar --</option>{opt}</select>{inner}</div>"
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Permisos", content, u_data).encode("utf-8")]

    # --- RUTA MÓDULOS (CRUD RESTAURADO) ---
    if path == "/modulos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall(); cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['strNombreModulo']}</td><td>{r.get('strMenuPadre','Seguridad')}</td><td><span style='color:#ef4444; cursor:pointer;' onclick='delMod({r['id']})'>Eliminar</span></td></tr>" for r in rows])
        content = f"""<div class='card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2 style='margin:0;'>Módulos</h2>
                <button class='btn-blue' onclick='document.getElementById("mMod").style.display="block"'>+ Nuevo Módulo</button>
            </div>
            <table><thead><tr><th>Nombre</th><th>Menú</th><th>Acciones</th></tr></thead><tbody>{rows_h}</tbody></table>
        </div>
        <div id="mMod" class="modal"><div class="modal-content">
            <span onclick='this.parentElement.parentElement.style.display="none"' style='float:right; cursor:pointer;'>&times;</span>
            <h3>Nuevo Módulo</h3>
            <form id="fMod">
                <label>Nombre del Módulo *</label><input name="n" required>
                <label>Agrupar en Menú</label>
                <select name="p"><option value="Seguridad">Seguridad</option><option value="Principal 1">Principal 1</option><option value="Principal 2">Principal 2</option></select>
                <div style='text-align:right;'><button type="submit" class="btn-blue">Guardar</button></div>
            </form>
        </div></div>
        <script>
            document.getElementById('fMod').onsubmit=async(e)=>{{ e.preventDefault(); 
                await fetch('/api/save_mod',{{method:'POST', body:new FormData(e.target)}}); location.reload(); 
            }};
            async function delMod(id){{ if(confirm('¿Eliminar módulo?')){{
                const f=new FormData(); f.append('id', id);
                await fetch('/api/del_mod',{{method:'POST', body:f}}); location.reload();
            }}}}
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Módulos", content, u_data).encode("utf-8")]

    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Dashboard", "<div class='card'><h1>Bienvenido</h1></div>", u_data).encode("utf-8")]