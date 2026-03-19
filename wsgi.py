# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN Y SEGURIDAD
# =========================================================
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@mysql.railway.internal:3306/railway')
JWT_SECRET = "CLAVE_MAESTRA_2026"

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
        bloqueados = ["perfil", "módulo", "modulo", "usuario", "permisos-perfil"] #
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = f'<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos</a>' if m_padre == "Seguridad" else ""
            subs = [m for m in all_mods if m.get('strMenuPadre') == m_padre and m['strNombreModulo'].lower().strip() not in bloqueados]
            for s in subs: links += f'<a href="/m/{s["id"]}">📄 {s["strNombreModulo"]}</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'

        nav = f"""<div class="top-nav">
            <div class="nav-left"><span class="logo">🛡️ Clínica Santa Mónica</span>{menu_html}</div>
            <div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none;">Salir</a></div>
        </div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        body{{font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; padding:20px 10px;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:180px; border:1px solid #334155; border-radius:8px; z-index:1000;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;}}
        .btn-red{{background:#ef4444; color:white; border:none; padding:5px 10px; border-radius:4px; cursor:pointer;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; padding:12px; border-bottom:2px solid #334155;}}
        td{{padding:12px; border-bottom:1px solid #334155;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:8px; border-radius:6px; width:100%;}}
        .modal{{display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#ffffff; color:#1e293b; margin:10% auto; padding:25px; width:400px; border-radius:12px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # RUTA LOGIN
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:350px; margin:100px auto;">
            <h2 style="text-align:center; color:#38bdf8;">Login Clínica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" required style="margin-bottom:15px;">
                <input type="password" name="p" placeholder="Contraseña" required style="margin-bottom:15px;">
                <button type="submit" class="btn-blue" style="width:100%;">Ingresar</button>
            </form></div>
            <script>document.getElementById('fL').onsubmit=async(e)=>{{ e.preventDefault(); 
                const res=await fetch('/api/login',{{method:'POST', body:new FormData(e.target)}});
                const d=await res.json(); if(d.ok) location.href='/dashboard'; else alert('Error');
            }}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login":
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

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- CRUD PERFILES (NUEVO / ELIMINAR) ---
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall(); cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{r['bitAdministrador']}</td><td><button class='btn-red' onclick='delPerf({r['id']})'>Eliminar</button></td></tr>" for r in rows])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Perfiles</h2><button class='btn-blue' onclick='document.getElementById("mP").style.display="block"'>+ Nuevo Perfil</button></div>
            <table><tr><th>ID</th><th>Nombre</th><th>Admin</th><th>Acciones</th></tr>{rows_h}</table></div>
            <div id="mP" class="modal"><div class="modal-content"><h3>Nuevo Perfil</h3><form id="fP"><input name="n" placeholder="Nombre" required><br><br>Admin: <select name="a"><option value="0">No</option><option value="1">Sí</option></select><br><br><button type="submit" class="btn-blue">Guardar</button></form></div></div>
            <script>document.getElementById('fP').onsubmit=async(e)=>{{ e.preventDefault(); await fetch('/api/p_save',{{method:'POST', body:new FormData(e.target)}}); location.reload(); }}
            async function delPerf(id){{ if(confirm('¿Eliminar?')){{ const f=new FormData(); f.append('id',id); await fetch('/api/p_del',{{method:'POST', body:f}}); location.reload(); }} }}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Perfiles", content, u_data).encode("utf-8")]

    # --- CRUD MÓDULOS (EDITAR / ELIMINAR) ---
    if path == "/modulos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall(); cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['strNombreModulo']}</td><td>{r.get('strMenuPadre','')}</td><td><button class='btn-blue' onclick='editMod({r['id']},\"{r['strNombreModulo']}\")'>Editar</button> <button class='btn-red' onclick='delMod({r['id']})'>Eliminar</button></td></tr>" for r in rows])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Módulos</h2><button class='btn-blue' onclick='location.reload()'>+ Nuevo</button></div>
            <table><tr><th>Módulo</th><th>Menú</th><th>Acciones</th></tr>{rows_h}</table></div>
            <script>async function delMod(id){{ if(confirm('¿Eliminar?')){{ const f=new FormData(); f.append('id',id); await fetch('/api/del_mod',{{method:'POST', body:f}}); location.reload(); }} }}
            function editMod(id, nom){{ const n=prompt("Nuevo nombre:", nom); if(n){{ /* API de edición aquí */ }} }}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Módulos", content, u_data).encode("utf-8")]

    # --- LOGOUT ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]

    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Dashboard", "<div class='card'><h1>Bienvenido</h1></div>", u_data).encode("utf-8")]