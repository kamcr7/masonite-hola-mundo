# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# --- CONFIG ---
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
        p = json.loads(base64.urlsafe_b64decode(t.split('.')[1] + "==").decode("utf-8"))
        return p if p['exp'] > time.time() else None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

# --- LAYOUT ---
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
                links += '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos</a><a href="/usuarios">👥 Usuarios</a>'
            subs = [m for m in all_mods if m.get('strMenuPadre') == m_padre and m['strNombreModulo'].lower() not in ["perfil","módulo","usuario","permisos-perfil"]]
            for s in subs: links += f'<a href="/m/{s["id"]}">📄 {s["strNombreModulo"]}</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        nav = f"""<div class="top-nav"><div class="nav-left"><span class="logo">🛡️ Clínica</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div><div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444;text-decoration:none;">Salir</a></div></div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title><style>
        body{{font-family:sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 20px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b;}}
        .nav-left{{display:flex; gap:15px; align-items:center;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:160px; border:1px solid #334155; border-radius:8px;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .dropdown-content a{{color:white; padding:10px; display:block; text-decoration:none; font-size:13px;}}
        .container{{padding:20px;}} .card{{background:#1e293b; padding:20px; border-radius:10px; border:1px solid #334155;}}
        table{{width:100%; border-collapse:collapse; margin-top:15px;}} th{{text-align:left; padding:10px; color:#94a3b8; border-bottom:1px solid #334155;}}
        td{{padding:10px; border-bottom:1px solid #1e293b;}} .btn-blue{{background:#2563eb; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer;}}
        input, select{{background:#0f172a; color:white; border:1px solid #334155; padding:8px; border-radius:5px; width:100%; margin-bottom:10px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    u_data = verify_jwt(environ)

    # --- LOGIN LOGIC ---
    if path in ["/", "/login"] and not u_data:
        if environ.get("REQUEST_METHOD") == "POST":
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
        
        content = """<div class="card" style="max-width:300px; margin:100px auto;"><h3>Login</h3><form id="fL"><input name="u" placeholder="User"><input name="p" type="password" placeholder="Pass"><button type="button" class="btn-blue" onclick="doL()">Entrar</button></form></div>
        <script>async function doL(){ const fd=new FormData(document.getElementById('fL')); const r=await fetch('/login',{method:'POST',body:fd}); const d=await r.json(); if(d.ok) location.href='/dashboard'; else alert('Error'); }</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    
    if path == "/usuarios":
        try:
            cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
            usrs = cur.fetchall()
            cur.execute("SELECT id, strNombrePerfil FROM perfiles")
            perfs = cur.fetchall()
            p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
            rows = "".join([f"<tr><td>{u.get('strNombreUsuario','-')}</td><td>{u.get('strNombrePerfil','-')}</td><td>{u.get('strEstado','Activo')}</td></tr>" for u in usrs])
            content = f"<div class='card'><h2>Usuarios</h2><table><tr><th>Usuario</th><th>Perfil</th><th>Estado</th></tr>{rows}</table></div>"
        except Exception as e:
            content = f"<div class='card'><h3>Error en Usuarios</h3><p>{str(e)}</p></div>"

    elif path == "/permisos":
        cur.execute("SELECT id, strNombrePerfil FROM perfiles")
        perfs = cur.fetchall()
        cur.execute("SELECT * FROM modulos")
        mods = cur.fetchall()
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"""<div class='card'><h2>Gestión de Permisos</h2><p>Seleccione un perfil para ver la tabla:</p>
            <select id="selP" onchange="document.getElementById('tP').style.display=this.value?'block':'none'"><option value="">-- Seleccionar Perfil --</option>{p_opts}</select>
            <div id="tP" style="display:none;"><table><tr><th>Módulo</th><th>C</th><th>R</th><th>U</th><th>D</th></tr>{m_rows}</table><button class="btn-blue" style="margin-top:10px;">Guardar Permisos</button></div></div>"""

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else:
        content = f"<div class='card'><h2>Bienvenido al Sistema</h2><p>Hola {u_data['u']}, selecciona una opción del menú.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]