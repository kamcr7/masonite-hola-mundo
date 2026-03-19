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
        .btn-edit{{background:#0ea5e9; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer; margin-right:5px;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; padding:15px; border-bottom:2px solid #334155; text-transform:uppercase;}}
        td{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:8px; width:100%;}}
        .modal{{display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#ffffff; color:#334155; margin:5% auto; padding:25px; width:600px; border-radius:12px;}}
        .modal-content input, .modal-content select {{background:#f8fafc; color:#334155; border:1px solid #cbd5e1; margin-bottom:15px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # 1. LOGIN
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:350px; margin:100px auto; text-align:center;">
            <h2 style="color:#38bdf8;">Clínica Santa Mónica</h2>
            <form id="fL"><input type="text" name="u" placeholder="Usuario" required><input type="password" name="p" placeholder="Pass" required>
            <center><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div></center>
            <button type="button" onclick="doLogin()" class="btn-blue" style="width:100%; margin-top:20px;">Entrar</button></form></div>
            <script>async function doLogin(){ 
                const res = await fetch('/api/login', {method:'POST', body:new FormData(document.getElementById('fL'))});
                const data = await res.json(); if(data.ok) location.href='/dashboard'; else alert("Error");
            }</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p)); user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")]); return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API GENERAL (POST) ---
    if method == "POST":
        conn = conectar_bd(); cur = conn.cursor(); fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        
        if path == "/api/save_per":
            id_per = fs.getvalue("id")
            if id_per: cur.execute("UPDATE perfiles SET strNombrePerfil=%s, bitAdministrador=%s WHERE id=%s", (fs.getvalue("n"), fs.getvalue("a"), id_per))
            else: cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s, %s)", (fs.getvalue("n"), fs.getvalue("a", "0")))
        
        elif path == "/api/del_per": cur.execute("DELETE FROM perfiles WHERE id=%s", (fs.getvalue("id"),))
        
        elif path == "/api/save_mod":
            id_mod = fs.getvalue("id")
            if id_mod: cur.execute("UPDATE modulos SET strNombreModulo=%s, strMenuPadre=%s WHERE id=%s", (fs.getvalue("n"), fs.getvalue("p"), id_mod))
            else: cur.execute("INSERT INTO modulos (strNombreModulo, strMenuPadre) VALUES (%s, %s)", (fs.getvalue("n"), fs.getvalue("p")))
            
        elif path == "/api/del_mod": cur.execute("DELETE FROM modulos WHERE id=%s", (fs.getvalue("id"),))

        elif path == "/api/save_user":
            img = base64.b64encode(fs["img"].file.read()).decode("utf-8") if "img" in fs and fs["img"].filename else ""
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strCorreo, strPwd, strCelular, idPerfil, strEstado, strImagen) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (fs.getvalue("u"), fs.getvalue("e"), hash_password(fs.getvalue("p")), fs.getvalue("c"), fs.getvalue("pid"), fs.getvalue("est"), img))

        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/perfiles":
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall()
        rows_h = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'SÍ' if r['bitAdministrador'] else 'NO'}</td><td><button class='btn-edit' onclick='editPer({r['id']}, \"{r['strNombrePerfil']}\", {r['bitAdministrador']})'>Editar</button><button class='btn-red' onclick='delPer({r['id']})'>Eliminar</button></td></tr>" for r in rows])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Perfiles</h2><button class='btn-blue' onclick='showM("mPer")'>+ Nuevo Perfil</button></div><table><tr><th>ID</th><th>NOMBRE</th><th>ADMIN</th><th>ACCIONES</th></tr>{rows_h}</table></div>
        <div id="mPer" class="modal"><div class="modal-content"><h3>Datos Perfil</h3><form id="fPer"><input type="hidden" name="id" id="eid"><input name="n" id="en" placeholder="Nombre" required><select name="a" id="ea"><option value="0">Usuario</option><option value="1">Admin</option></select><button type="submit" class="btn-blue">Guardar</button></form></div></div>
        <script>
            const showM = id => document.getElementById(id).style.display='block';
            const editPer = (id, n, a) => {{ document.getElementById('eid').value=id; document.getElementById('en').value=n; document.getElementById('ea').value=a; showM('mPer'); }};
            document.getElementById('fPer').onsubmit=async(e)=>{{ e.preventDefault(); await fetch('/api/save_per',{{method:'POST', body:new FormData(e.target)}}); location.reload(); }};
            async function delPer(id){{ if(confirm('¿Eliminar?')){{ const fd=new FormData(); fd.append('id',id); await fetch('/api/del_per',{{method:'POST', body:fd}}); location.reload(); }} }}
        </script>"""

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall()
        rows_h = "".join([f"<tr><td>{r['strNombreModulo']}</td><td>{r.get('strMenuPadre','')}</td><td><button class='btn-edit' onclick='editMod({r['id']}, \"{r['strNombreModulo']}\", \"{r['strMenuPadre']}\")'>Editar</button><button class='btn-red' onclick='delMod({r['id']})'>Eliminar</button></td></tr>" for r in rows])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Módulos</h2><button class='btn-blue' onclick='showM("mMod")'>+ Nuevo</button></div><table><tr><th>Nombre</th><th>Padre</th><th>Acciones</th></tr>{rows_h}</table></div>
        <div id="mMod" class="modal"><div class="modal-content"><h3>Datos Módulo</h3><form id="fMod"><input type="hidden" name="id" id="mid"><input name="n" id="mn" required><select name="p" id="mp"><option>Seguridad</option><option>Principal 1</option><option>Principal 2</option></select><button type="submit" class="btn-blue">Guardar</button></form></div></div>
        <script>
            const showM = id => document.getElementById(id).style.display='block';
            const editMod = (id, n, p) => {{ document.getElementById('mid').value=id; document.getElementById('mn').value=n; document.getElementById('mp').value=p; showM('mMod'); }};
            document.getElementById('fMod').onsubmit=async(e)=>{{ e.preventDefault(); await fetch('/api/save_mod',{{method:'POST', body:new FormData(e.target)}}); location.reload(); }};
            async function delMod(id){{ if(confirm('¿Eliminar?')){{ const fd=new FormData(); fd.append('id',id); await fetch('/api/del_mod',{{method:'POST', body:fd}}); location.reload(); }} }}
        </script>"""

    elif path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id"); usrs = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        rows = "".join([f"<tr><td><img src='data:image/png;base64,{u['strImagen']}' style='width:35px;height:35px;border-radius:50%;' onerror='this.src=\"https://via.placeholder.com/35\"'></td><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strNombrePerfil']}</td><td>{u['strEstado']}</td><td><button class='btn-red' onclick='delItem({u['id']}, \"user\")'>Eliminar</button></td></tr>" for u in usrs])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Usuarios</h2><button class='btn-blue' onclick='showM("mU")'>+ Nuevo Usuario</button></div><table><tr><th>IMG</th><th>USUARIO</th><th>CORREO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr>{rows}</table></div>
        <div id="mU" class="modal"><div class="modal-content" style="width:650px;"><h3>Nuevo Usuario</h3><form id="fU">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
                <input name="u" placeholder="Usuario" required><input name="e" placeholder="Email" required>
                <input name="p" type="password" placeholder="Pass" required><input name="c" placeholder="Celular">
                <select name="pid">{p_opts}</select><select name="est"><option>Activo</option><option>Inactivo</option></select>
            </div><input type="file" name="img" style="margin-top:10px;"><button type="submit" class="btn-blue" style="width:100%; margin-top:15px;">Guardar</button></form></div></div>
        <script>
            document.getElementById('fU').onsubmit=async(e)=>{{ e.preventDefault(); await fetch('/api/save_user',{{method:'POST', body:new FormData(e.target)}}); location.reload(); }};
        </script>"""

    elif path == "/permisos":
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"<div class='card'><h2>Matriz de Permisos</h2><select style='width:300px; margin-bottom:20px;'><option>Seleccione un Perfil...</option></select><table><tr><th>Módulo</th><th>C</th><th>A</th><th>E</th><th>D</th></tr>{rows}</table><button class='btn-blue' style='margin-top:20px;'>Guardar Permisos</button></div>"

    else: content = "<div class='card'><h1>Bienvenido</h1><p>Panel de administración Clínica Santa Mónica.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]