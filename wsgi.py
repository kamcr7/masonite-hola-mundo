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
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; position:sticky; top:0; z-index:100;}}
        .nav-left{{display:flex; gap:15px; align-items:center;}}
        .logo{{font-weight:bold; color:#38bdf8; font-size:1.1rem;}}
        .nav-link{{color:#94a3b8; text-decoration:none; font-size:0.9rem;}}
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
        input, select{{background:#0f172a; border:1px solid #334155; color:white; padding:10px; border-radius:8px; width:100%; box-sizing:border-box;}}
        .modal{{display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8); overflow:auto;}}
        .modal-content{{background:#ffffff; color:#334155; margin:5% auto; padding:25px; width:650px; border-radius:12px;}}
        .modal-content label{{display:block; margin-bottom:5px; font-weight:600; font-size:0.85rem; color:#1e293b;}}
        .modal-content input, .modal-content select{{background:#f1f5f9; color:#1e293b; border:1px solid #cbd5e1; margin-bottom:15px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # 1. RUTAS PÚBLICAS (LOGIN)
    if path in ["/", "/login"]:
        content = """<div class="card" style="max-width:350px; margin:100px auto; text-align:center;">
            <h2 style="color:#38bdf8;">Clínica Santa Mónica</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" style="width:100%; margin-bottom:15px; background:#0f172a; color:white; border:1px solid #334155; padding:10px; border-radius:8px;">
                <input type="password" name="p" placeholder="Contraseña" style="width:100%; margin-bottom:20px; background:#0f172a; color:white; border:1px solid #334155; padding:10px; border-radius:8px;">
                <center><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div></center>
                <button type="button" onclick="doLogin()" class="btn-blue" style="width:100%; margin-top:20px;">Iniciar Sesión</button>
            </form></div>
            <script>async function doLogin(){ 
                if(!grecaptcha.getResponse()){alert("Completa el Captcha"); return;}
                const res = await fetch('/api/login', {method:'POST', body:new FormData(document.getElementById('fL'))});
                const data = await res.json();
                if(data.ok) location.href='/dashboard'; else alert("Credenciales incorrectas");
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

    # SEGURIDAD: REDIRECCIÓN SI NO HAY SESIÓN
    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # 2. API CRUD USUARIOS (NUEVO)
    if path == "/api/save_user" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, e, p_raw, c, pid, est = fs.getvalue("u"), fs.getvalue("e"), fs.getvalue("p"), fs.getvalue("c"), fs.getvalue("pid"), fs.getvalue("est")
        p_hash = hash_password(p_raw)
        img_b64 = ""
        if "img" in fs and fs["img"].filename:
            img_b64 = base64.b64encode(fs["img"].file.read()).decode("utf-8")
        
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (strNombreUsuario, strCorreo, strPwd, strCelular, idPerfil, strEstado, strImagen) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (u, e, p_hash, c, pid, est, img_b64))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    if path == "/api/del_user" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        uid = fs.getvalue("id")
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # 2. CRUD DE MÓDULOS (API)
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

    # 3. PANTALLA DE PERFILES
    if path == "/perfiles":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM perfiles"); rows = cur.fetchall(); cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['id']}</td><td>{r['strNombrePerfil']}</td><td>{'SÍ' if r['bitAdministrador'] else 'NO'}</td><td style='color:#38bdf8;'>Editar</td></tr>" for r in rows])
        content = f"<div class='card'><h2>Gestión de Perfiles</h2><table><thead><tr><th>ID</th><th>Nombre</th><th>Admin</th><th>Acciones</th></tr></thead><tbody>{rows_h}</tbody></table></div>"
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Perfiles", content, u_data).encode("utf-8")]

    # 4. PANTALLA DE MÓDULOS (VISTA)
    if path == "/modulos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); rows = cur.fetchall(); cur.close(); conn.close()
        rows_h = "".join([f"<tr><td>{r['strNombreModulo']}</td><td>{r.get('strMenuPadre','Seguridad')}</td><td><span style='color:#ef4444; cursor:pointer;' onclick='delMod({r['id']})'>Eliminar</span></td></tr>" for r in rows])
        content = f"""<div class='card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2 style='margin:0;'>Módulos del Sistema</h2>
                <button class='btn-blue' onclick='document.getElementById("mMod").style.display="block"'>+ Nuevo Módulo</button>
            </div>
            <table><thead><tr><th>Nombre</th><th>Menú Padre</th><th>Acciones</th></tr></thead><tbody>{rows_h}</tbody></table>
        </div>
        <div id="mMod" class="modal"><div class="modal-content" style="color:#334155;">
            <h3>Registrar Nuevo Módulo</h3>
            <form id="fMod">
                <input name="n" required placeholder="Nombre (Ej: Reportes)" style="margin-bottom:15px; padding:10px; border-radius:8px; border:1px solid #ccc; color:#000;">
                <select name="p" style="margin-bottom:20px; padding:10px; border-radius:8px; border:1px solid #ccc; color:#000;">
                    <option value="Seguridad">Seguridad</option><option value="Principal 1">Principal 1</option><option value="Principal 2">Principal 2</option>
                </select>
                <div style="text-align:right;">
                    <button type="button" onclick="document.getElementById('mMod').style.display='none'" style="background:none; border:none; color:#64748b; cursor:pointer; margin-right:15px;">Cancelar</button>
                    <button type="submit" class="btn-blue">Guardar Módulo</button>
                </div>
            </form>
        </div></div>
        <script>
            document.getElementById('fMod').onsubmit = async(e) => {{ e.preventDefault();
                await fetch('/api/save_mod', {{method:'POST', body:new FormData(e.target)}});
                location.reload();
            }};
            async function delMod(id) {{ if(confirm('¿Eliminar este módulo?')) {{
                const fd = new FormData(); fd.append('id', id);
                await fetch('/api/del_mod', {{method:'POST', body:fd}});
                location.reload();
            }}}}
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Módulos", content, u_data).encode("utf-8")]

    # 5. PANTALLA DE USUARIOS (NUEVO)
    if path == "/usuarios":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        usrs = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles")
        perfs = cur.fetchall()
        cur.close(); conn.close()
        
        rows_h = "".join([f"""<tr>
            <td><img src='data:image/png;base64,{u['strImagen']}' style='width:35px;height:35px;border-radius:50%;' onerror='this.src="https://via.placeholder.com/35"'></td>
            <td>{u['strNombreUsuario']}</td>
            <td>{u['strCorreo']}</td>
            <td>{u['strNombrePerfil']}</td>
            <td><span style='color:{"#22c55e" if u['strEstado']=="Activo" else "#ef4444"}; font-weight:bold;'>{u['strEstado']}</span></td>
            <td><span style='color:#ef4444; cursor:pointer;' onclick='delUser({u['id']})'>Eliminar</span></td>
        </tr>""" for u in usrs])
        
        perf_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        
        content = f"""<div class='card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2 style='margin:0;'>Gestión de Usuarios</h2>
                <button class='btn-blue' onclick='document.getElementById("mUsr").style.display="block"'>+ Nuevo Usuario</button>
            </div>
            <table><thead><tr><th>Img</th><th>Usuario</th><th>Correo</th><th>Perfil</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows_h}</tbody></table>
        </div>
        <div id="mUsr" class="modal"><div class="modal-content">
            <h3 style="margin-top:0;">Registrar Nuevo Usuario</h3>
            <form id="fUsr" enctype="multipart/form-data">
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px;">
                    <div><label>Nombre de Usuario *</label><input name="u" required></div>
                    <div><label>Correo Electrónico *</label><input type="email" name="e" required></div>
                    <div><label>Contraseña *</label><input type="password" name="p" required></div>
                    <div><label>Número Celular</label><input name="c"></div>
                    <div><label>Perfil *</label><select name="pid" required><option value="">-- Seleccione --</option>{perf_opts}</select></div>
                    <div><label>Estado</label><select name="est"><option value="Activo">Activo</option><option value="Inactivo">Inactivo</option></select></div>
                </div>
                <div style="margin-top:10px;"><label>Fotografía de Perfil</label><input type="file" name="img" accept="image/*" style="border:none; background:transparent; padding:0;"></div>
                <div style="text-align:right; margin-top:20px;">
                    <button type="button" onclick="document.getElementById('mUsr').style.display='none'" style="background:none; border:none; color:#64748b; cursor:pointer; margin-right:15px;">Cancelar</button>
                    <button type="submit" class="btn-blue">Guardar Usuario</button>
                </div>
            </form>
        </div></div>
        <script>
            document.getElementById('fUsr').onsubmit = async(e) => {{ e.preventDefault();
                await fetch('/api/save_user', {{method:'POST', body:new FormData(e.target)}});
                location.reload();
            }};
            async function delUser(id) {{ if(confirm('¿Eliminar este usuario?')) {{
                const fd = new FormData(); fd.append('id', id);
                await fetch('/api/del_user', {{method:'POST', body:fd}});
                location.reload();
            }}}}
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Usuarios", content, u_data).encode("utf-8")]

    # 6. MATRIZ DE PERMISOS
    if path == "/permisos":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        pid = urllib.parse.parse_qs(environ.get('QUERY_STRING', '')).get('pid', [None])[0]
        opt = "".join([f"<option value='{p['id']}' {'selected' if str(p['id'])==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        
        inner = "<div style='text-align:center; padding:50px; color:#64748b;'><h3>⚠️ Seleccione un perfil para administrar.</h3></div>"
        if pid:
            cur.execute("SELECT id, strNombreModulo FROM modulos"); mods = cur.fetchall()
            tbody = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
            inner = f"<table><thead><tr><th>Módulo</th><th>CONSULTAR</th><th>AGREGAR</th><th>EDITAR</th><th>ELIMINAR</th></tr></thead><tbody>{tbody}</tbody></table><div style='text-align:right; margin-top:20px;'><button class='btn-blue'>Guardar Cambios</button></div>"
        
        content = f"<div class='card'><h2>Matriz de Permisos</h2><div style='margin-bottom:20px;'>Perfil: <select onchange='location.href=\"/permisos?pid=\"+this.value' style='width:250px;'><option value=''>-- Seleccionar --</option>{opt}</select></div>{inner}</div>"
        cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Permisos", content, u_data).encode("utf-8")]

    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]

    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Dashboard", "<div class='card'><h1>Bienvenido al Panel de Control</h1><p>Seleccione una opción del menú superior.</p></div>", u_data).encode("utf-8")]