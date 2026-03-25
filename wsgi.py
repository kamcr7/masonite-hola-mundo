# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_FINAL_V_FIXED"
RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"

def hash_password(p): return hashlib.sha256((p or "").encode("utf-8")).hexdigest()
def b64url_encode(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode("utf-8")

def jwt_encode(p):
    h = b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode("utf-8"))
    py = b64url_encode(json.dumps(p).encode("utf-8"))
    msg = f"{h}.{py}".encode("utf-8")
    s = hmac.new(JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
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
# MAQUETACIÓN CORREGIDA (LLAVES ESCAPADAS)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT idPerfil FROM usuarios WHERE strNombreUsuario=%s", (user['u'],))
        u_p = cur.fetchone()
        u_pid = u_p['idPerfil'] if u_p else 0
        
        if u_pid == 1:
            cur.execute("SELECT strNombreModulo as n FROM modulos")
            p_ok = ["Perfiles", "Usuarios", "Modulos", "Permisos"] + [r['n'] for r in cur.fetchall()]
        else:
            cur.execute("SELECT nombreModulo FROM permisos WHERE idPerfil=%s AND permisoVer=1", (u_pid,))
            p_ok = [r['nombreModulo'] for r in cur.fetchall()]
        
        cur.execute("SELECT * FROM modulos"); mods_db = cur.fetchall()
        cur.close(); conn.close()
        
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' 
                           for m in mods_db if m['strMenuPadre'] == padre and m['strNombreModulo'] in p_ok])
        
        seg_links = ""
        if "Perfiles" in p_ok: seg_links += '<a href="/perfiles">👤 Perfiles</a>'
        if "Modulos" in p_ok: seg_links += '<a href="/modulos">📦 Modulos</a>'
        if "Usuarios" in p_ok: seg_links += '<a href="/usuarios">👥 Usuarios</a>'
        if "Permisos" in p_ok: seg_links += '<a href="/permisos">🔐 Permisos</a>'
        
        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{seg_links or '<a>(Sin Acceso)</a>'}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1") or '<a>(Vacio)</a>'}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2") or '<a>(Vacio)</a>'}</div></div>
        </div><div class="nav-right"><span class="user-pill" style="color:var(--emerald); margin-right:15px; font-size:13px; border:1px solid var(--border); padding:4px 10px; border-radius:20px;">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
   
    # Nota las llaves dobles {{ }} en el CSS, esto evita el SyntaxError
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; --pill-active: #065f46; --pill-inactive: #7f1d1d; }}
        body {{ font-family:sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
        .logo {{ color:var(--emerald); font-weight:bold; font-size:1.2rem; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; padding:10px; font-size:14px; }}
        .dropdown {{ position:relative; display:inline-block; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:15px; cursor:pointer; font-size:14px; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border:1px solid var(--border); border-radius:8px; z-index:100; }}
        .dropdown-content a {{ color:white; padding:12px; text-decoration:none; display:block; font-size:13px; border-bottom: 1px solid #334155; }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .container {{ padding:40px; max-width:1200px; margin:0 auto; }}
        .card {{ background:var(--card); padding:25px; border-radius:12px; border:1px solid var(--border); }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; background:#0f172a; border-radius:8px; overflow:hidden; }}
        th {{ background:#1e293b; color:#94a3b8; font-size:12px; text-transform:uppercase; padding:15px; text-align:left; }}
        td {{ padding:15px; border-bottom:1px solid var(--border); text-align:left; font-size:14px; }}
        .avatar {{ width:40px; height:40px; border-radius:50%; object-fit: cover; background:#334155; display:inline-block; vertical-align:middle; margin-right:10px; }}
        .status-pill {{ padding:4px 12px; border-radius:20px; font-size:11px; font-weight:bold; text-transform:uppercase; }}
        .active {{ background:var(--pill-active); color:#34d399; }}
        .inactive {{ background:var(--pill-inactive); color:#f87171; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-blue {{ background:transparent; color:#3b82f6; border:none; cursor:pointer; font-weight:500; margin-right:10px; }}
        .btn-red {{ background:transparent; color:#ef4444; border:none; cursor:pointer; font-weight:500; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; }}
        .modal-content {{ background:var(--card); width:600px; margin:5% auto; padding:30px; border-radius:15px; position:relative; border: 1px solid var(--border); }}
        .grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:15px; }}
        .close-x {{ position:absolute; top:15px; right:20px; color:#94a3b8; cursor:pointer; font-size:24px; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 15px; border-radius:8px; font-size:13px; }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            const d = await res.json();
            if(d.ok) location.reload(); else alert("Error: " + (d.error || "Desconocido"));
        }}

        function editM(modalId, data) {{
            for (let key in data) {{
                let el = document.getElementById('edit_' + key);
                if(el) el.value = data[key];
            }}
            document.getElementById('edit_id').value = data.id;
            if(data.img && document.getElementById('preview_edit')) document.getElementById('preview_edit').src = data.img;
            openM(modalId);
        }}

        function handleImg(e, previewId, hiddenId) {{
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onloadend = () => {{
                document.getElementById(previewId).src = reader.result;
                document.getElementById(hiddenId).value = reader.result;
            }};
            reader.readAsDataURL(file);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # --- API LOGIN ---
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
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false, "msg":"Credenciales incorrectas"}']

    if path == "/":
        target = "/dashboard" if u_data else "/login"
        start_response("303 See Other", [("Location", target)]); return [b""]

    if path == "/login":
        if u_data: start_response("303 See Other", [("Location", "/dashboard")]); return [b""]
        content = f"""<div class="card" style="width:350px; margin:100px auto; border-top: 4px solid var(--emerald);">
            <h2 style="text-align:center">Inicia Sesión</h2>
            <form id="fL">
                <input name="u" placeholder="Usuario">
                <input name="p" type="password" placeholder="Contraseña">
                <div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}" style="margin-bottom:20px;"></div>
                <button type="button" class="btn-emerald" style="width:100%" onclick="doLogin()">ACCEDER</button>
            </form></div>
            <script>async function doLogin(){{
                const f = new FormData(document.getElementById("fL"));
                const r = await fetch("/api/login", {{method:"POST", body:f}});
                const d = await r.json();
                if(d.ok) location.href="/dashboard"; else alert(d.msg);
            }}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]

    # --- API CRUD CORREGIDO ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd()
        cur = conn.cursor(buffered=True) # IMPORTANTE: buffered=True soluciona el error out of sync
        
        try:
            if p['action'] == 'delete': 
                cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            
            elif p['action'] == 'save_modulo': 
                cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)", (p['data']['n'], p['data']['r'], p['data']['p']))
            
            elif p['action'] == 'update_modulo':
                cur.execute("UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s", (p['data']['n'], p['data']['r'], p['data']['p'], p['id']))
            
            elif p['action'] == 'save_perfil': 
                cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['n'],))
            
            elif p['action'] == 'update_perfil':
                cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (p['data']['n'], p['id']))
            
            elif p['action'] == 'save_usuario':
                cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado, strCorreo, strCelular, strImagen) VALUES (%s,%s,%s,%s,%s,%s,%s)", 
                           (p['data']['u'], hash_password(p['data']['p']), p['data']['idp'], p['data']['st'], p['data']['em'], p['data']['ph'], p['data']['img']))
            
            elif p['action'] == 'update_usuario':
                if p['data'].get('p'):
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, strPwd=%s, idPerfil=%s, strEstado=%s, strCorreo=%s, strCelular=%s, strImagen=%s WHERE id=%s", 
                               (p['data']['u'], hash_password(p['data']['p']), p['data']['idp'], p['data']['st'], p['data']['em'], p['data']['ph'], p['data']['img'], p['id']))
                else:
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s, strCorreo=%s, strCelular=%s, strImagen=%s WHERE id=%s", 
                               (p['data']['u'], p['data']['idp'], p['data']['st'], p['data']['em'], p['data']['ph'], p['data']['img'], p['id']))

            # Reajuste de IDs para perfiles (opcional)
            if p['table'] == 'perfiles' and p['action'] in ['delete', 'save_perfil']:
                cur.execute("SET @count = 0;")
                cur.execute("UPDATE perfiles SET id = (@count := @count + 1);")

            conn.commit()
            res_body = b'{"ok":true}'
        except Exception as e:
            conn.rollback()
            res_body = json.dumps({"ok":false, "error": str(e)}).encode("utf-8")
        finally:
            cur.close()
            conn.close()

        start_response("200 OK", [("Content-Type", "application/json")])
        return [res_body]

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        users = cur.fetchall()
        rows = ""
        for u in users:
            img = u.get('strImagen') or "https://ui-avatars.com/api/?name="+u['strNombreUsuario']
            st_cls = "active" if u['strEstado'] == "Activo" else "inactive"
            rows += f"<tr><td><img src='{img}' class='avatar'></td><td><b>{u['strNombreUsuario']}</b></td><td>{u.get('strCorreo','-')}</td><td>{u['strNombrePerfil']}</td><td><span class='status-pill {st_cls}'>{u['strEstado']}</span></td><td><button class='btn-blue' onclick='editM(\"mEditU\", {{id:{u['id']}, u:\"{u['strNombreUsuario']}\", em:\"{u.get('strCorreo','')}\", ph:\"{u.get('strCelular','')}\", idp:{u['idPerfil']}, st:\"{u['strEstado']}\", img:\"{img}\"}})'>Editar</button> <button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Eliminar</button></td></tr>"
        
        cur.execute("SELECT * FROM perfiles"); p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between'><h2>👥 Usuarios</h2><button class='btn-emerald' onclick="openM('mU')">+ NUEVO USUARIO</button></div>
            <table><thead><tr><th>IMG</th><th>Usuario</th><th>Correo</th><th>Perfil</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
            
            <div id="mU" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mU')">&times;</span><h3>Nuevo Usuario</h3>
                <div class="grid-2">
                    <div><label>Usuario</label><input id="un"></div>
                    <div><label>Correo</label><input id="uem"></div>
                    <div><label>Contraseña</label><input id="up" type="password"></div>
                    <div><label>Celular</label><input id="uph"></div>
                    <div><label>Perfil</label><select id="uip">{p_opts}</select></div>
                    <div><label>Estado</label><select id="ust"><option>Activo</option><option>Inactivo</option></select></div>
                </div>
                <label>Foto</label><input type="file" onchange="handleImg(event, 'preview_new', 'uimg_b64')">
                <img id="preview_new" style="width:50px; height:50px; border-radius:50%; margin-bottom:15px; display:block;">
                <input type="hidden" id="uimg_b64">
                <button class="btn-emerald" style="width:100%" onclick="runCrud('save_usuario','usuarios',0,{{u:document.getElementById('un').value, em:document.getElementById('uem').value, p:document.getElementById('up').value, ph:document.getElementById('uph').value, idp:document.getElementById('uip').value, st:document.getElementById('ust').value, img:document.getElementById('uimg_b64').value}})">GUARDAR</button>
            </div></div>

            <div id="mEditU" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mEditU')">&times;</span><h3>Editar Usuario</h3>
                <input type="hidden" id="edit_id">
                <div class="grid-2">
                    <div><label>Usuario</label><input id="edit_u"></div>
                    <div><label>Correo</label><input id="edit_em"></div>
                    <div><label>Contraseña</label><input id="edit_p" type="password"></div>
                    <div><label>Celular</label><input id="edit_ph"></div>
                    <div><label>Perfil</label><select id="edit_idp">{p_opts}</select></div>
                    <div><label>Estado</label><select id="edit_st"><option>Activo</option><option>Inactivo</option></select></div>
                </div>
                <label>Foto</label><input type="file" onchange="handleImg(event, 'preview_edit', 'edit_img')">
                <img id="preview_edit" style="width:50px; height:50px; border-radius:50%; margin-bottom:15px; display:block;">
                <input type="hidden" id="edit_img">
                <button class="btn-emerald" style="width:100%" onclick="runCrud('update_usuario','usuarios',document.getElementById('edit_id').value,{{u:document.getElementById('edit_u').value, em:document.getElementById('edit_em').value, p:document.getElementById('edit_p').value, ph:document.getElementById('edit_ph').value, idp:document.getElementById('edit_idp').value, st:document.getElementById('edit_st').value, img:document.getElementById('edit_img').value}})">ACTUALIZAR</button>
            </div></div>"""

    elif path == "/perfiles":
        cur.execute("SELECT id, strNombrePerfil as n FROM perfiles"); perfs = cur.fetchall()
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['n']}</td><td><button class='btn-blue' onclick='editM(\"mEditP\", {json.dumps(p)})'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in perfs])
        content = f"""<div class='card'><h2>👤 Perfiles</h2><button class='btn-emerald' onclick="openM('mP')">+ NUEVO PERFIL</button><table><thead><tr><th>ID</th><th>Nombre</th><th>Accion</th></tr></thead><tbody>{rows}</tbody></table></div>
            <div id="mP" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mP')">&times;</span><h3>Nuevo Perfil</h3><input id="pn" placeholder="Nombre"><button class="btn-emerald" style="width:100%" onclick="runCrud('save_perfil','perfiles',0,{{n:document.getElementById('pn').value}})">GUARDAR</button></div></div>
            <div id="mEditP" class="modal"><div class="modal-content"><span class="close-x" onclick="closeM('mEditP')">&times;</span><h3>Editar Perfil</h3><input type="hidden" id="edit_id"><input id="edit_n" placeholder="Nombre"><button class="btn-emerald" style="width:100%" onclick="runCrud('update_perfil','perfiles',document.getElementById('edit_id').value,{{n:document.getElementById('edit_n').value}})">ACTUALIZAR</button></div></div>"""

    else:
        content = f"<div class='card'><h2>Bienvenido</h2><p>Hola <b>{u_data['u']}</b>, usa el menú superior para navegar.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode("utf-8")]