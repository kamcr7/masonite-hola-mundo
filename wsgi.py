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

# =========================================================
# MAQUETACIÓN (SCRIPTS DE PAGINACIÓN Y TOGGLE)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        menu_html = ""
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos</a><a href="/usuarios">👥 Usuarios</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        nav = f"""<div class="top-nav"><div class="nav-left"><span class="logo">🛡️ Clínica Santa Mónica</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div><div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none; margin-left:10px;">Salir</a></div></div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; position:sticky; top:0; z-index:100;}}
        .nav-left{{display:flex; gap:15px; align-items:center;}}
        .logo{{font-weight:bold; color:#38bdf8; font-size:1.1rem;}}
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 10px;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:200px; border-radius:8px; border:1px solid #334155; z-index:1000;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600;}}
        .btn-red{{background:#ef4444; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; padding:15px; border-bottom:2px solid #334155;}}
        td{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        .modal{{display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#ffffff; color:#334155; margin:5% auto; padding:25px; width:450px; border-radius:12px;}}
        .modal-content input, .modal-content select {{width:100%; padding:10px; margin:10px 0; border:1px solid #ccc; border-radius:5px;}}
        .pagination{{margin-top:20px; display:flex; gap:5px; justify-content:center;}}
        .page-btn{{padding:8px 12px; background:#1e293b; border:1px solid #334155; color:white; cursor:pointer; border-radius:4px;}}
    </style>
    <script>
        function paginate(tableId) {{
            const table = document.getElementById(tableId);
            if(!table) return;
            const rows = Array.from(table.tBodies[0].rows);
            const perPage = 5;
            const totalPages = Math.ceil(rows.length / perPage);
            const container = document.getElementById('pagButtons');
            if(totalPages <= 1) return;
            function showPage(p) {{
                rows.forEach((r, i) => r.style.display = (i >= (p-1)*perPage && i < p*perPage) ? '' : 'none');
                Array.from(container.children).forEach((b, i) => b.style.background = (i+1 === p) ? '#2563eb' : '#1e293b');
            }}
            for(let i=1; i<=totalPages; i++) {{
                let btn = document.createElement('button'); btn.innerText = i; btn.className = 'page-btn';
                btn.onclick = () => showPage(i); container.appendChild(btn);
            }}
            showPage(1);
        }}
        function togglePermisos() {{
            const checks = document.querySelectorAll('#tP input[type="checkbox"]');
            const allChecked = Array.from(checks).every(c => c.checked);
            checks.forEach(c => c.checked = !allChecked);
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

    # LOGIN (ESTRICTAMENTE EL QUE TE FUNCIONA)
    if path in ["/", "/login"] and method == "GET":
        content = """<div class='card' style='max-width:350px; margin:100px auto; text-align:center;'>
            <h2 style="color:#38bdf8;">Clínica Santa Mónica</h2>
            <form id='fL'><input name='u' placeholder='Usuario' style='width:100%; padding:10px; margin-bottom:10px;' required>
            <input name='p' type='password' placeholder='Contraseña' style='width:100%; padding:10px;' required>
            <div style="margin:20px 0; display:flex; justify-content:center;"><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div></div>
            <button type='button' onclick='doLogin()' class='btn-blue' style='width:100%;'>Entrar</button></form></div>
            <script>async function doLogin(){{
                const c = grecaptcha.getResponse(); if(!c){{ alert("Captcha requerido"); return; }}
                const res=await fetch('/api/login',{{method:'POST', body:new FormData(document.getElementById('fL'))}});
                const data=await res.json(); if(data.ok) location.href='/dashboard'; else alert('Error de login');
            }}</script>"""
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

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API POST (RECUPERADA) ---
    if method == "POST":
        conn = conectar_bd(); cur = conn.cursor(); fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        if path == "/api/save_user":
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strCorreo, strPwd, strEstado, idPerfil) VALUES (%s,%s,%s,%s,%s)",
                        (fs.getvalue("u"), fs.getvalue("e"), hash_password(fs.getvalue("p")), "Activo", 1))
        elif path == "/api/del_user":
            cur.execute("DELETE FROM usuarios WHERE id=%s", (fs.getvalue("id"),))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/usuarios":
        cur.execute("SELECT * FROM usuarios"); usrs = cur.fetchall()
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td><button class='btn-red' onclick='del({u['id']})'>Eliminar</button></td></tr>" for u in usrs])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Usuarios</h2><button class='btn-blue' onclick='document.getElementById("mU").style.display="block"'>+ Nuevo</button></div>
        <table id='tMain'><thead><tr><th>Usuario</th><th>Correo</th><th>Acción</th></tr></thead><tbody>{rows}</tbody></table><div id='pagButtons' class='pagination'></div></div>
        <div id='mU' class='modal'><div class='modal-content'><h3>Nuevo Usuario</h3><form id='fU'><input name='u' placeholder='Usuario'><input name='e' placeholder='Email'><input name='p' type='password' placeholder='Pass'><button class='btn-blue'>Guardar</button></form></div></div>
        <script>paginate('tMain'); document.getElementById('fU').onsubmit=async(e)=>{{e.preventDefault(); await fetch('/api/save_user',{{method:'POST',body:new FormData(e.target)}}); location.reload();}};</script>"""

    elif path == "/permisos":
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        m_rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Permisos</h2><button class='btn-blue' onclick='togglePermisos()'>Marcar / Desmarcar Todos</button></div>
        <div id='tP'><table><tr><th>Módulo</th><th>C</th><th>A</th><th>E</th><th>D</th></tr>{m_rows}</table></div></div>"""
    
    else:
        content = "<h1>Dashboard</h1><p>Bienvenido al sistema.</p>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]