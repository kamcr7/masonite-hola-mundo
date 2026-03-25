# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_FINAL_V_FIXED"

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
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in all_mods if m['strMenuPadre'] == padre])
        
        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">
            <a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Modulos</a><a href="/usuarios">👥 Usuarios</a>
        </div></div>
        <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1")}</div></div>
        </div><div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
        body {{ font-family: sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
        .logo {{ color:var(--emerald); font-weight:bold; font-size:1.2rem; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; padding:10px; font-size:14px; }}
        .dropdown {{ position:relative; display:inline-block; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border:1px solid var(--border); border-radius:12px; z-index:100; }}
        .dropdown-content a {{ color:white; padding:12px; text-decoration:none; display:block; border-bottom: 1px solid #334155; }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:15px; cursor:pointer; }}
        .container {{ padding:40px; max-width:1200px; margin:0 auto; }}
        .card {{ background:var(--card); padding:30px; border-radius:16px; border:1px solid var(--border); margin-bottom:20px; }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; background:#0f172a; border-radius:12px; overflow:hidden; }}
        th {{ background:#1e293b; color:#94a3b8; font-size:12px; text-transform:uppercase; padding:15px; text-align:left; }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:14px; }}
        .avatar-table {{ width:40px; height:40px; border-radius:50%; object-fit: cover; background:#334155; border: 1px solid var(--border); }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%; }}
        .btn-blue {{ color:#3b82f6; background:none; border:none; cursor:pointer; font-weight:bold; margin-right:10px; }}
        .btn-red {{ color:#ef4444; background:none; border:none; cursor:pointer; font-weight:bold; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; }}
        .modal-content {{ background:var(--card); width:550px; margin:5% auto; padding:35px; border-radius:20px; border: 1px solid var(--border); position:relative; }}
        .grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:15px; }}
        .close-x {{ position:absolute; top:20px; right:25px; color:#94a3b8; cursor:pointer; font-size:24px; }}
        .user-pill {{ color:var(--emerald); border:1px solid var(--border); padding:6px 16px; border-radius:25px; margin-right:15px; font-size:13px; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 18px; border-radius:8px; font-size:13px; }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            const j = await res.json();
            if(j.ok) location.reload(); else alert("Error: " + j.error);
        }}

        function preEditU(id, u, idp, st) {{
            document.getElementById('ed_u_id').value = id;
            document.getElementById('ed_u_n').value = u;
            document.getElementById('ed_u_idp').value = idp;
            document.getElementById('ed_u_st').value = st;
            openM('mEditU');
        }}

        function preEditP(id, n) {{
            document.getElementById('ed_p_id').value = id;
            document.getElementById('ed_p_n').value = n;
            openM('mEditP');
        }}

        function preEditM(id, n, r, p) {{
            document.getElementById('ed_m_id').value = id;
            document.getElementById('ed_m_n').value = n;
            document.getElementById('ed_m_r').value = r;
            document.getElementById('ed_m_p').value = p;
            openM('mEditM');
        }}

        function handleImg(e, prevId) {{
            const reader = new FileReader();
            reader.onload = () => {{ document.getElementById(prevId).src = reader.result; }};
            reader.readAsDataURL(e.target.files[0]);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/"); method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)
    content = ""

    # --- API LOGIN & CRUD ---
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
        u, p = fs.getvalue("u"), fs.getvalue("p")
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, hash_password(p)))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            token = jwt_encode({"u": u, "exp": time.time() + 86400})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={token}; Path=/; HttpOnly")])
            return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save':
                if p['table'] == 'perfiles': cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['n'],))
                if p['table'] == 'modulos': cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)", (p['data']['n'], p['data']['r'], p['data']['p']))
                if p['table'] == 'usuarios': cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,%s)", (p['data']['u'], hash_password(p['data']['p']), p['data']['idp'], p['data']['st']))
            elif p['action'] == 'update':
                if p['table'] == 'perfiles': cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (p['data']['n'], p['id']))
                if p['table'] == 'modulos': cur.execute("UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s", (p['data']['n'], p['data']['r'], p['data']['p'], p['id']))
                if p['table'] == 'usuarios': cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s WHERE id=%s", (p['data']['u'], p['data']['idp'], p['data']['st'], p['id']))
            conn.commit(); res = b'{"ok":true}'
        except Exception as e: conn.rollback(); res = json.dumps({"ok":False, "error":str(e)}).encode()
        finally: cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [res]

    if not u_data and path != "/login":
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    # --- RUTA PERFILES ---
    if path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-blue' onclick='preEditP({p['id']}, \"{p['strNombrePerfil']}\")'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Eliminar</button></td></tr>" for p in cur.fetchall()])
        content = f"""<div class='card'><h2>👤 Gestión de Perfiles</h2><button class='btn-emerald' style='width:auto' onclick="openM('mNewP')">+ NUEVO PERFIL</button><table><thead><tr><th>ID</th><th>NOMBRE</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div id='mNewP' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNewP')">&times;</span><h3>Nuevo Perfil</h3><input id='pn' placeholder='Nombre'><button class='btn-emerald' onclick=\"runCrud('save','perfiles',0,{{n:document.getElementById('pn').value}})\">GUARDAR</button></div></div>
        <div id='mEditP' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mEditP')">&times;</span><h3>Editar Perfil</h3><input type='hidden' id='ed_p_id'><input id='ed_p_n'><button class='btn-emerald' onclick=\"runCrud('update','perfiles',document.getElementById('ed_p_id').value,{{n:document.getElementById('ed_p_n').value}})\">ACTUALIZAR</button></div></div>"""

    # --- RUTA MODULOS ---
    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-blue' onclick='preEditM({m['id']}, \"{m['strNombreModulo']}\", \"{m['strRuta']}\", \"{m['strMenuPadre']}\")'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Eliminar</button></td></tr>" for m in cur.fetchall()])
        content = f"""<div class='card'><h2>📦 Gestión de Módulos</h2><button class='btn-emerald' style='width:auto' onclick="openM('mNewM')">+ NUEVO MÓDULO</button><table><thead><tr><th>NOMBRE</th><th>RUTA</th><th>PADRE</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div id='mNewM' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNewM')">&times;</span><h3>Nuevo Módulo</h3><input id='mn' placeholder='Nombre'><input id='mr' placeholder='/ruta'><input id='mp' placeholder='Padre'><button class='btn-emerald' onclick=\"runCrud('save','modulos',0,{{n:document.getElementById('mn').value, r:document.getElementById('mr').value, p:document.getElementById('mp').value}})\">GUARDAR</button></div></div>
        <div id='mEditM' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mEditM')">&times;</span><h3>Editar Módulo</h3><input type='hidden' id='ed_m_id'><input id='ed_m_n'><input id='ed_m_r'><input id='ed_m_p'><button class='btn-emerald' onclick=\"runCrud('update','modulos',document.getElementById('ed_m_id').value,{{n:document.getElementById('ed_m_n').value, r:document.getElementById('ed_m_r').value, p:document.getElementById('ed_m_p').value}})\">ACTUALIZAR</button></div></div>"""

    # --- RUTA USUARIOS ---
    elif path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        rows = ""
        for u in cur.fetchall():
            img = f"https://ui-avatars.com/api/?name={u['strNombreUsuario']}&background=random"
            rows += f"<tr><td><img src='{img}' class='avatar-table'></td><td>{u['strNombreUsuario']}</td><td>{u['strNombrePerfil']}</td><td>{u['strEstado']}</td><td><button class='btn-blue' onclick='preEditU({u['id']}, \"{u['strNombreUsuario']}\", {u['idPerfil']}, \"{u['strEstado']}\")'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</button></td></tr>"
        cur.execute("SELECT * FROM perfiles"); p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        content = f"""<div class='card'><h2>👥 Usuarios</h2><button class='btn-emerald' style='width:auto' onclick="openM('mNewU')">+ NUEVO</button><table><thead><tr><th>IMG</th><th>USUARIO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div id='mNewU' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNewU')">&times;</span><h3>Nuevo Usuario</h3><div class='grid-2'><div><label>User</label><input id='un'></div><div><label>Pass</label><input id='up' type='password'></div><div><label>Perfil</label><select id='uip'>{p_opts}</select></div><div><label>Estado</label><select id='ust'><option>Activo</option><option>Inactivo</option></select></div></div><button class='btn-emerald' onclick=\"runCrud('save','usuarios',0,{{u:document.getElementById('un').value, p:document.getElementById('up').value, idp:document.getElementById('uip').value, st:document.getElementById('ust').value}})\">GUARDAR</button></div></div>
        <div id='mEditU' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mEditU')">&times;</span><h3>Editar Usuario</h3><input type='hidden' id='ed_u_id'><label>Usuario</label><input id='ed_u_n'><label>Perfil</label><select id='ed_u_idp'>{p_opts}</select><label>Estado</label><select id='ed_u_st'><option>Activo</option><option>Inactivo</option></select><button class='btn-emerald' onclick=\"runCrud('update','usuarios',document.getElementById('ed_u_id').value,{{u:document.getElementById('ed_u_n').value, idp:document.getElementById('ed_u_idp').value, st:document.getElementById('ed_u_st').value}})\">ACTUALIZAR</button></div></div>"""

    elif path == "/login":
        content = """<div class='card' style='width:350px;margin:100px auto'><h2>Login</h2><form id='f'><input name='u' placeholder='Usuario'><input name='p' type='password' placeholder='Pass'><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div><button type='button' class='btn-emerald' onclick='doL()'>ENTRAR</button></form></div>
        <script>async function doL(){{if(!grecaptcha.getResponse())return alert("Captcha!");const r=await fetch('/api/login',{{method:'POST',body:new FormData(document.getElementById('f'))}});if((await r.json()).ok)location.href='/usuarios';else alert("Error")}}</script>"""
    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else: content = f"<div class='card'><h2>Dashboard</h2><p>Bienvenido {u_data['u'] if u_data else ''}</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode()]