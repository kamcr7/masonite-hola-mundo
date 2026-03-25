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
# MAQUETACIÓN PROFESIONAL
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
        .card {{ background:var(--card); padding:30px; border-radius:16px; border:1px solid var(--border); }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; background:#0f172a; border-radius:12px; overflow:hidden; }}
        th {{ background:#1e293b; color:#94a3b8; font-size:12px; text-transform:uppercase; padding:15px; text-align:left; }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:14px; }}
        .avatar-table {{ width:45px; height:45px; border-radius:50%; object-fit: cover; background:#334155; border: 1px solid var(--border); }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; }}
        .modal-content {{ background:var(--card); width:600px; margin:5% auto; padding:35px; border-radius:20px; border: 1px solid var(--border); position:relative; }}
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

    # --- API LOGIN ---
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

    # --- API CRUD ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save' and p['table'] == 'usuarios':
                cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,%s)", 
                           (p['data']['u'], hash_password(p['data']['p']), p['data']['idp'], p['data']['st']))
            conn.commit(); res = b'{"ok":true}'
        except Exception as e: conn.rollback(); res = json.dumps({"ok":False, "error":str(e)}).encode()
        finally: cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [res]

    if not u_data and path != "/login":
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    if path == "/login":
        content = f"""<div class='card' style='width:350px;margin:100px auto'>
            <h2 style='text-align:center'>Clínica Login</h2>
            <form id='f'>
                <input name='u' placeholder='Usuario'>
                <input name='p' type='password' placeholder='Contraseña'>
                <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" style="margin-bottom:15px"></div>
                <button type='button' class='btn-emerald' onclick='doL()'>ENTRAR</button>
            </form>
        </div>
        <script>
            async function doL(){{
                if(!grecaptcha.getResponse()) return alert("Completa el captcha");
                const f = new FormData(document.getElementById('f'));
                const r = await fetch('/api/login', {{method:'POST', body:f}});
                if((await r.json()).ok) location.href='/usuarios'; else alert("Datos incorrectos");
            }}
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode()]

    elif path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        rows = "".join([f"<tr><td><img src='https://ui-avatars.com/api/?name={u['strNombreUsuario']}&background=random' class='avatar-table'></td><td>{u['strNombreUsuario']}</td><td>{u['strNombrePerfil']}</td><td>{u['strEstado']}</td><td><button class='btn-salir' style='background:#ef4444' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</button></td></tr>" for u in cur.fetchall()])
        cur.execute("SELECT * FROM perfiles"); p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        content = f"""<div class='card'>
            <div style='display:flex;justify-content:space-between'><h2>👥 Gestión Usuarios</h2><button class='btn-emerald' style='width:auto' onclick="openM('mNew')">+ NUEVO</button></div>
            <table><thead><tr><th>IMG</th><th>USUARIO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table>
        </div>
        <div id='mNew' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNew')">&times;</span>
            <h3>Nuevo Usuario</h3>
            <div class='grid-2'>
                <div><label>Usuario</label><input id='un'></div>
                <div><label>Correo</label><input id='uc'></div>
                <div><label>Clave</label><input id='up' type='password'></div>
                <div><label>Celular</label><input id='ut'></div>
                <div><label>Perfil</label><select id='uip'>{p_opts}</select></div>
                <div><label>Estado</label><select id='ust'><option>Activo</option><option>Inactivo</option></select></div>
            </div>
            <label>Foto</label><input type='file' onchange="handleImg(event,'pv')"><img id='pv' style='width:50px;display:block;margin:10px 0'>
            <button class='btn-emerald' onclick=\"runCrud('save','usuarios',0,{{u:document.getElementById('un').value, p:document.getElementById('up').value, idp:document.getElementById('uip').value, st:document.getElementById('ust').value}})\">GUARDAR</button>
        </div></div>"""

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    
    else: content = f"<div class='card'><h2>Dashboard</h2><p>Bienvenido {u_data['u']}</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode()]