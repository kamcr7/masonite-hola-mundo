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
        .modal-content{{background:#ffffff; color:#334155; margin:5% auto; padding:25px; width:650px; border-radius:12px;}}
        .modal-content label{{display:block; margin-bottom:5px; font-weight:bold; font-size:0.8rem;}}
        .modal-content input, .modal-content select {{background:#f8fafc; color:#334155; border:1px solid #cbd5e1; margin-bottom:15px;}}
        .badge{{padding:4px 8px; border-radius:6px; font-size:0.75rem; font-weight:bold;}}
        .bg-green{{background:#065f46; color:#a7f3d0;}}
        .bg-red{{background:#991b1b; color:#fecaca;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    if path in ["/", "/login"] and method == "GET":
        content = """<div class='card' style='max-width:350px; margin:100px auto; text-align:center;'>
            <h2 style="color:#38bdf8;">Clínica Santa Mónica</h2>
            <form id='fL'>
            <input name='u' placeholder='Usuario' style='margin-bottom:10px;' required>
            <input name='p' type='password' placeholder='Contraseña' required>
            <div style="margin:20px 0; display:flex; justify-content:center;">
                <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div>
            </div>
            <button type='button' onclick='doLogin()' class='btn-blue' style='width:100%;'>Entrar</button></form></div>
            <script>async function doLogin(){
                const captcha = grecaptcha.getResponse();
                if(!captcha){ alert("Por favor, verifica el captcha"); return; }
                const res=await fetch('/api/login',{method:'POST', body:new FormData(document.getElementById('fL'))});
                const data=await res.json(); if(data.ok) location.href='/dashboard'; else alert('Credenciales incorrectas');
            }</script>"""
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

    # --- API POST ---
    if method == "POST":
        conn = conectar_bd(); cur = conn.cursor(); fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        if path == "/api/save_user":
            img = base64.b64encode(fs["img"].file.read()).decode("utf-8") if "img" in fs and fs["img"].filename else ""
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strCorreo, strPwd, idPerfil, strEstado, strImagen) VALUES (%s,%s,%s,%s,%s,%s)",
                        (fs.getvalue("u"), fs.getvalue("e"), hash_password(fs.getvalue("p")), fs.getvalue("pid"), fs.getvalue("est"), img))
        elif path == "/api/del_user":
            cur.execute("DELETE FROM usuarios WHERE id=%s", (fs.getvalue("id"),))
        elif path == "/api/save_per":
            id_p = fs.getvalue("id"); n, a = fs.getvalue("n"), fs.getvalue("a", "0")
            if id_p: cur.execute("UPDATE perfiles SET strNombrePerfil=%s, bitAdministrador=%s WHERE id=%s", (n, a, id_p))
            else: cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s,%s)", (n, a))
        elif path == "/api/del_per": cur.execute("DELETE FROM perfiles WHERE id=%s", (fs.getvalue("id"),))
        elif path == "/api/save_mod":
            id_m = fs.getvalue("id"); n, p = fs.getvalue("n"), fs.getvalue("p")
            if id_m: cur.execute("UPDATE modulos SET strNombreModulo=%s, strMenuPadre=%s WHERE id=%s", (n, p, id_m))
            else: cur.execute("INSERT INTO modulos (strNombreModulo, strMenuPadre) VALUES (%s,%s)", (n, p))
        elif path == "/api/del_mod": cur.execute("DELETE FROM modulos WHERE id=%s", (fs.getvalue("id"),))
       
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/usuarios":
        try:
            # Query con JOIN para traer el nombre del perfil
            cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
            usrs = cur.fetchall()
            cur.execute("SELECT id, strNombrePerfil FROM perfiles")
            perfs = cur.fetchall()
            p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
           
            rows = ""
            for u in usrs:
                img_data = u.get('strImagen')
                img_src = f"data:image/png;base64,{img_data}" if img_data else "https://ui-avatars.com/api/?name=" + u.get('strNombreUsuario', 'U')
                estado_cls = "bg-green" if u.get('strEstado') == "Activo" else "bg-red"
               
                rows += f"""<tr>
                    <td><img src='{img_src}' style='width:35px;height:35px;border-radius:50%;object-fit:cover;' onerror="this.src='https://via.placeholder.com/35'"></td>
                    <td><b>{u.get('strNombreUsuario','-')}</b></td>
                    <td>{u.get('strCorreo','-')}</td>
                    <td>{u.get('strNombrePerfil','SIN PERFIL')}</td>
                    <td><span class='badge {estado_cls}'>{u.get('strEstado','Inactivo').upper()}</span></td>
                    <td><button class='btn-red' onclick='delUsr({u['id']})'>Eliminar</button></td>
                </tr>"""
           
            content = f"""<div class='card'><div style='display:flex; justify-content:space-between; align-items:center;'><h2>Gestión de Usuarios</h2><button class='btn-blue' onclick='document.getElementById("mU").style.display="block"'>+ Nuevo Usuario</button></div>
                <table><tr><th>IMG</th><th>USUARIO</th><th>CORREO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr>{rows}</table></div>
                <div id="mU" class="modal"><div class="modal-content"><h3>Nuevo Usuario</h3><form id="fU">
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
                    <div><label>Nombre Usuario *</label><input name="u" required></div><div><label>Correo *</label><input name="e" type="email" required></div>
                    <div><label>Contraseña *</label><input name="p" type="password" required></div><div><label>Perfil *</label><select name="pid">{p_opts}</select></div>
                    <div><label>Estado</label><select name="est"><option value="Activo">Activo</option><option value="Inactivo">Inactivo</option></select></div>
                </div><label style="margin-top:10px;">Foto</label><input type="file" name="img"><button type="submit" class="btn-blue" style="width:100%; margin-top:20px;">Guardar Usuario</button>
                <button type="button" onclick="document.getElementById('mU').style.display='none'" style="width:100%; background:transparent; border:none; color:#64748b; cursor:pointer; margin-top:10px;">Cancelar</button></form></div></div>
                <script>document.getElementById('fU').onsubmit=async(e)=>{{e.preventDefault();await fetch('/api/save_user',{{method:'POST',body:new FormData(e.target)}});location.reload();}};
                async function delUsr(id){{if(confirm('¿Eliminar usuario?')){{const fd=new FormData();fd.append('id',id);await fetch('/api/del_user',{{method:'POST',body:fd}});location.reload();}}}}</script>"""
        except Exception as e:
            content = f"<div class='card'><h2>Error Usuarios</h2><p style='color:#ef4444;'>{str(e)}</p></div>"

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall()
        rows_h = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'SÍ' if r['bitAdministrador'] else 'NO'}</td><td><button class='btn-edit' onclick='editPer({r['id']}, \"{r['strNombrePerfil']}\", {r['bitAdministrador']})'>Editar</button><button class='btn-red' onclick='delPer({r['id']})'>Eliminar</button></td></tr>" for r in rows])
        content = f"<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Perfiles</h2><button class='btn-blue' onclick='document.getElementById(\"mPer\").style.display=\"block\"'>+ Nuevo Perfil</button></div><table><tr><th>ID</th><th>NOMBRE</th><th>ADMIN</th><th>ACCIONES</th></tr>{rows_h}</table></div><div id='mPer' class='modal'><div class='modal-content'><h3>Datos Perfil</h3><form id='fPer'><input type='hidden' name='id' id='eid'><input name='n' id='en' placeholder='Nombre' required><select name='a' id='ea'><option value='0'>Usuario</option><option value='1'>Admin</option></select><button type='submit' class='btn-blue'>Guardar</button></form></div></div><script>const editPer=(id,n,a)=>{{document.getElementById('eid').value=id;document.getElementById('en').value=n;document.getElementById('ea').value=a;document.getElementById('mPer').style.display='block';}};document.getElementById('fPer').onsubmit=async(e)=>{{e.preventDefault();await fetch('/api/save_per',{{method:'POST',body:new FormData(e.target)}});location.reload();}};async function delPer(id){{if(confirm('¿Eliminar?')){{const fd=new FormData();fd.append('id',id);await fetch('/api/del_per',{{method:'POST',body:fd}});location.reload();}}}}</script>"

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall()
        rows_h = "".join([f"<tr><td>{r['strNombreModulo']}</td><td>{r.get('strMenuPadre','')}</td><td><button class='btn-edit' onclick='editMod({r['id']}, \"{r['strNombreModulo']}\", \"{r['strMenuPadre']}\")'>Editar</button><button class='btn-red' onclick='delMod({r['id']})'>Eliminar</button></td></tr>" for r in rows])
        content = f"<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Módulos</h2><button class='btn-blue' onclick='document.getElementById(\"mMod\").style.display=\"block\"'>+ Nuevo</button></div><table><tr><th>Nombre</th><th>Padre</th><th>Acciones</th></tr>{rows_h}</table></div><div id='mMod' class='modal'><div class='modal-content'><h3>Datos Módulo</h3><form id='fMod'><input type='hidden' name='id' id='mid'><input name='n' id='mn' required><select name='p' id='mp'><option>Seguridad</option><option>Principal 1</option><option>Principal 2</option></select><button type='submit' class='btn-blue'>Guardar</button></form></div></div><script>const editMod=(id,n,p)=>{{document.getElementById('mid').value=id;document.getElementById('mn').value=n;document.getElementById('mp').value=p;document.getElementById('mMod').style.display='block';}};document.getElementById('fMod').onsubmit=async(e)=>{{e.preventDefault();await fetch('/api/save_mod',{{method:'POST',body:new FormData(e.target)}});location.reload();}};async function delMod(id){{if(confirm('¿Eliminar?')){{const fd=new FormData();fd.append('id',id);await fetch('/api/del_mod',{{method:'POST',body:fd}});location.reload();}}}}</script>"

    elif path == "/permisos":
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        m_rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"""<div class='card'><h2>Matriz de Permisos</h2><label>Seleccione Perfil:</label><select id="selPer" style="width:300px; margin-bottom:20px;" onchange="document.getElementById('tP').style.display=this.value?'block':'none'"><option value="">-- Seleccionar --</option>{p_opts}</select><div id="tP" style="display:none;"><table><tr><th>Módulo</th><th>C</th><th>A</th><th>E</th><th>D</th></tr>{m_rows}</table><button class='btn-blue' style='margin-top:20px;'>Guardar Permisos</button></div></div>"""

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]
    else:
        content = "<div class='card'><h1>Dashboard</h1><p>Bienvenido al panel administrativo de Clínica Santa Mónica.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]