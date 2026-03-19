# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN
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
        if not t: return None
        p = json.loads(base64.urlsafe_b64decode(t.split('.')[1] + "==").decode("utf-8"))
        return p if p['exp'] > time.time() else None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

# =========================================================
# MAQUETACIÓN (LAYOUT) CON SOPORTE CAPTCHA
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        menu_html = ""
        # Filtrado para evitar duplicados en el menú
        bloqueados = ["perfil", "módulo", "modulo", "usuario", "permisos-perfil"]
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = f'<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos</a>' if m_padre == "Seguridad" else ""
            subs = [m for m in all_mods if m.get('strMenuPadre') == m_padre and m['strNombreModulo'].lower().strip() not in bloqueados]
            for s in subs: links += f'<a href="/m/{s["id"]}">📄 {s["strNombreModulo"]}</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'

        nav = f"""<div class="top-nav">
            <div class="nav-left"><span class="logo">🛡️ Clínica Santa Mónica</span>{menu_html}</div>
            <div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none; margin-left:15px;">Salir</a></div>
        </div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; padding:20px 10px; font-size:0.9rem;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:180px; border:1px solid #334155; border-radius:8px; z-index:1000;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem;}}
        .dropdown-content a:hover{{background:#334155; color:#38bdf8;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:bold;}}
        .btn-red{{background:#ef4444; color:white; border:none; padding:5px 10px; border-radius:4px; cursor:pointer;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; padding:12px; border-bottom:2px solid #334155; font-size:0.8rem; text-transform:uppercase;}}
        td{{padding:12px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:6px; width:100%;}}
        .modal{{display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#ffffff; color:#1e293b; margin:10% auto; padding:25px; width:400px; border-radius:12px;}}
        .modal-content input, .modal-content select {{background:#f1f5f9; color:#1e293b; border:1px solid #cbd5e1;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # --- RUTA LOGIN (CON CAPTCHA RESTAURADO) ---
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:350px; margin:80px auto; text-align:center;">
            <h2 style="color:#38bdf8; margin-bottom:25px;">Clínica Santa Mónica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" required style="margin-bottom:15px;">
                <input type="password" name="p" placeholder="Contraseña" required style="margin-bottom:20px;">
                <center><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div></center>
                <button type="submit" class="btn-blue" style="width:100%; margin-top:20px; padding:12px;">Entrar al Sistema</button>
            </form></div>
            <script>document.getElementById('fL').onsubmit=async(e)=>{{ e.preventDefault();
                if(!grecaptcha.getResponse()){{ alert("Por favor, completa el Captcha"); return; }}
                const res=await fetch('/api/login',{{method:'POST', body:new FormData(e.target)}});
                const d=await res.json(); if(d.ok) location.href='/dashboard'; else alert('Usuario o clave incorrectos');
            }}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
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

    # --- API ENDPOINTS (MODIFICACIÓN/ELIMINACIÓN) ---
    if path in ["/api/save_mod", "/api/p_save"] and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        n, p = fs.getvalue("n"), fs.getvalue("p", "Seguridad")
        query = "INSERT INTO modulos (strNombreModulo, strMenuPadre) VALUES (%s,%s)" if path == "/api/save_mod" else "INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s,%s)"
        conn = conectar_bd(); cur = conn.cursor(); cur.execute(query, (n, p)); conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    if path in ["/api/del_mod", "/api/p_del"] and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        table = "modulos" if path == "/api/del_mod" else "perfiles"
        conn = conectar_bd(); cur = conn.cursor(); cur.execute(f"DELETE FROM {table} WHERE id=%s", (fs.getvalue("id"),)); conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- PANTALLAS CRUD COMPLETAS ---
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall(); cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'SÍ' if r['bitAdministrador'] else 'NO'}</td><td><button class='btn-red' onclick='delItem({r['id']},\"/api/p_del\")'>Eliminar</button></td></tr>" for r in rows])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Gestión de Perfiles</h2><button class='btn-blue' onclick='document.getElementById("mP").style.display="block"'>+ Nuevo Perfil</button></div><table><tr><th>ID</th><th>Nombre</th><th>Admin</th><th>Acciones</th></tr>{rows_h}</table></div>
        <div id="mP" class="modal"><div class="modal-content"><h3>Nuevo Perfil</h3><form onsubmit='event.preventDefault(); saveItem(this,"/api/p_save")'><label>Nombre</label><input name="n" required><br><br><label>Admin</label><select name="p"><option value="0">No</option><option value="1">Sí</option></select><br><br><button type="submit" class="btn-blue">Guardar</button></form></div></div>"""
        
    elif path == "/modulos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM modulos"); rows = cur.fetchall(); cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['strNombreModulo']}</td><td>{r.get('strMenuPadre','')}</td><td><button class='btn-blue' onclick='alert(\"Editar ID: {r['id']}\")'>Editar</button> <button class='btn-red' onclick='delItem({r['id']},\"/api/del_mod\")'>Eliminar</button></td></tr>" for r in rows])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Gestión de Módulos</h2><button class='btn-blue' onclick='document.getElementById("mM").style.display="block"'>+ Nuevo Módulo</button></div><table><tr><th>Módulo</th><th>Menú Asignado</th><th>Acciones</th></tr>{rows_h}</table></div>
        <div id="mM" class="modal"><div class="modal-content"><h3>Nuevo Módulo</h3><form onsubmit='event.preventDefault(); saveItem(this,"/api/save_mod")'><label>Nombre</label><input name="n" required><br><br><label>Menú Padre</label><select name="p"><option value="Seguridad">Seguridad</option><option value="Principal 1">Principal 1</option><option value="Principal 2">Principal 2</option></select><br><br><button type="submit" class="btn-blue">Guardar</button></form></div></div>"""

    else:
        content = "<div class='card'><h1>Panel de Control</h1><p>Bienvenido al sistema.</p></div>"

    # SCRIPTS GLOBALES DE CRUD
    full_content = content + """<script>
        async function saveItem(form, url){ await fetch(url, {method:'POST', body:new FormData(form)}); location.reload(); }
        async function delItem(id, url){ if(confirm('¿Seguro?')){ const f=new FormData(); f.append('id',id); await fetch(url, {method:'POST', body:f}); location.reload(); } }
        window.onclick = (e) => { if(e.target.className=='modal') e.target.style.display='none'; }
    </script>"""
    
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]

    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", full_content, u_data).encode("utf-8")]