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
# MAQUETACIÓN
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        menu_html = ""
        bloqueados = ["perfil", "módulo", "modulo", "usuario", "permisos-perfil"]
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos</a><a href="/usuarios">👥 Usuarios</a>'
            subs = [m for m in all_mods if m.get('strMenuPadre') == m_padre and m['strNombreModulo'].lower().strip() not in bloqueados]
            for s in subs: links += f'<a href="/m/{s["id"]}">📄 {s["strNombreModulo"]}</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        nav = f"""<div class="top-nav"><div class="nav-left"><span class="logo">🛡️ Clínica Santa Mónica</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div><div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none; margin-left:10px;">Salir</a></div></div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; position:sticky; top:0; z-index:100;}}
        .nav-left{{display:flex; gap:15px; align-items:center;}}
        .logo{{font-weight:bold; color:#38bdf8; font-size:1.1rem;}}
        .nav-link{{color:#94a3b8; text-decoration:none; font-size:0.9rem;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 10px;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:200px; border-radius:8px; border:1px solid #334155; z-index:1000;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600;}}
        .btn-red{{background:#ef4444; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer;}}
        .btn-gray{{background:#475569; color:white; border:none; padding:5px 15px; border-radius:6px; cursor:pointer; font-size:0.8rem;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; padding:15px; border-bottom:2px solid #334155; text-transform:uppercase;}}
        td{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:8px; width:100%;}}
        .modal{{display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#ffffff; color:#334155; margin:5% auto; padding:25px; width:650px; border-radius:12px;}}
        .badge{{padding:4px 8px; border-radius:6px; font-size:0.75rem; font-weight:bold;}}
        .bg-green{{background:#065f46; color:#a7f3d0;}}
        .bg-red{{background:#991b1b; color:#fecaca;}}
        /* Estilos Paginación */
        .pagination{{margin-top:20px; display:flex; gap:5px; justify-content:center;}}
        .page-btn{{padding:8px 12px; background:#1e293b; border:1px solid #334155; color:white; cursor:pointer; border-radius:4px;}}
        .page-btn.active{{background:#2563eb; border-color:#2563eb;}}
    </style>
    <script>
        function paginate(tableId, rowsPerPage) {{
            const table = document.getElementById(tableId);
            const rows = Array.from(table.tBodies[0].rows);
            const pageCount = Math.ceil(rows.length / rowsPerPage);
            const paginationContainer = document.getElementById('pagination');
            let currentPage = 1;

            function showPage(page) {{
                currentPage = page;
                const start = (page - 1) * rowsPerPage;
                const end = start + rowsPerPage;
                rows.forEach((row, index) => row.style.display = (index >= start && index < end) ? '' : 'none');
                renderButtons();
            }}

            function renderButtons() {{
                paginationContainer.innerHTML = '';
                for (let i = 1; i <= pageCount; i++) {{
                    const btn = document.createElement('button');
                    btn.innerText = i; btn.className = 'page-btn ' + (i === currentPage ? 'active' : '');
                    btn.onclick = () => showPage(i);
                    paginationContainer.appendChild(btn);
                }}
            }}
            if(rows.length > rowsPerPage) showPage(1);
        }}

        function checkAll() {{
            document.querySelectorAll('#tP input[type="checkbox"]').forEach(cb => cb.checked = true);
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

    # LOGIN (Mantenido igual)
    if path in ["/", "/login"] and method == "GET":
        content = """<div class='card' style='max-width:350px; margin:100px auto; text-align:center;'>
            <h2 style="color:#38bdf8;">Clínica Santa Mónica</h2>
            <form id='fL'>
            <input name='u' placeholder='Usuario' style='margin-bottom:10px;' required>
            <input name='p' type='password' placeholder='Contraseña' required>
            <div style="margin:20px 0; display:flex; justify-content:center;"><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div></div>
            <button type='button' onclick='doLogin()' class='btn-blue' style='width:100%;'>Entrar</button></form></div>
            <script>async function doLogin(){{const captcha = grecaptcha.getResponse(); if(!captcha){{ alert("Verifica el captcha"); return; }}
            const res=await fetch('/api/login',{{method:'POST', body:new FormData(document.getElementById('fL'))}});
            const data=await res.json(); if(data.ok) location.href='/dashboard'; else alert('Credenciales incorrectas');}}</script>"""
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

    # --- API POST (Mantenido) ---
    if method == "POST":
        conn = conectar_bd(); cur = conn.cursor(); fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        if path == "/api/save_user":
            img = base64.b64encode(fs["img"].file.read()).decode("utf-8") if "img" in fs and fs["img"].filename else ""
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strCorreo, strPwd, idPerfil, strEstado, strImagen) VALUES (%s,%s,%s,%s,%s,%s)",
                        (fs.getvalue("u"), fs.getvalue("e"), hash_password(fs.getvalue("p")), fs.getvalue("pid"), fs.getvalue("est"), img))
        elif path == "/api/del_user":
            cur.execute("DELETE FROM usuarios WHERE id=%s", (fs.getvalue("id"),))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTAS CON PAGINACIÓN ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        usrs = cur.fetchall()
        rows = "".join([f"<tr><td><img src='https://ui-avatars.com/api/?name={u['strNombreUsuario']}' style='width:30px; border-radius:50%'></td><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u.get('strNombrePerfil','-')}</td><td>{u['strEstado']}</td><td><button class='btn-red'>X</button></td></tr>" for u in usrs])
        content = f"<div class='card'><h2>Usuarios</h2><table id='t'><thead><tr><th>IMG</th><th>USUARIO</th><th>CORREO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table><div id='pagination' class='pagination'></div></div><script>paginate('t', 5);</script>"

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles"); rows_db = cur.fetchall()
        rows = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{r['bitAdministrador']}</td><td><button class='btn-red'>X</button></td></tr>" for r in rows_db])
        content = f"<div class='card'><h2>Perfiles</h2><table id='t'><thead><tr><th>ID</th><th>NOMBRE</th><th>ADMIN</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table><div id='pagination' class='pagination'></div></div><script>paginate('t', 5);</script>"

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos"); rows_db = cur.fetchall()
        rows = "".join([f"<tr><td>{r['strNombreModulo']}</td><td>{r['strMenuPadre']}</td><td><button class='btn-red'>X</button></td></tr>" for r in rows_db])
        content = f"<div class='card'><h2>Módulos</h2><table id='t'><thead><tr><th>Nombre</th><th>Padre</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table><div id='pagination' class='pagination'></div></div><script>paginate('t', 5);</script>"

    elif path == "/permisos":
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        m_rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"""<div class='card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2>Matriz de Permisos</h2>
                <button class='btn-gray' onclick='checkAll()'>✔️ Seleccionar Todos</button>
            </div>
            <div id="tP"><table><tr><th>Módulo</th><th>C</th><th>A</th><th>E</th><th>D</th></tr>{m_rows}</table><button class='btn-blue' style='margin-top:20px;'>Guardar Permisos</button></div>
        </div>"""
    else:
        content = "<div class='card'><h1>Dashboard</h1><p>Bienvenido.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]