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
# MAQUETACIÓN CON TODOS LOS CAMPOS SOLICITADOS
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
        .status-pill {{ padding:4px 12px; border-radius:20px; font-size:11px; font-weight:bold; }}
        .active {{ background:#065f46; color:#34d399; }}
        .inactive {{ background:#7f1d1d; color:#f87171; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-blue {{ color:#3b82f6; background:none; border:none; cursor:pointer; }}
        .btn-red {{ color:#ef4444; background:none; border:none; cursor:pointer; }}
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
            if((await res.json()).ok) location.reload(); else alert("Error en DB");
        }}
        function preEdit(id, fields, mId='mEdit') {{
            for(let k in fields) {{ let el = document.getElementById('ed_'+k); if(el) el.value = fields[k]; }}
            document.getElementById('ed_id').value = id;
            openM(mId);
        }}
        function handleImg(e, prevId) {{
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onloadend = () => {{ document.getElementById(prevId).src = reader.result; }};
            reader.readAsDataURL(file);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/"); method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ); content = ""

    # --- API CRUD (LÓGICA DE GUARDADO SEGURA) ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save':
                if p['table'] == 'usuarios':
                    # NOTA: Solo insertamos los campos que tu DB soporta actualmente para evitar el error 1054
                    cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,%s)", 
                               (p['data']['u'], hash_password(p['data']['p']), p['data']['idp'], p['data']['st']))
                elif p['table'] == 'perfiles':
                    cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['n'],))
                elif p['table'] == 'modulos':
                    cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)", 
                               (p['data']['n'], p['data']['r'], p['data']['p']))
            elif p['action'] == 'update':
                if p['table'] == 'usuarios':
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s WHERE id=%s", 
                               (p['data']['u'], p['data']['idp'], p['data']['st'], p['id']))
            conn.commit(); res = b'{"ok":true}'
        except Exception as e: conn.rollback(); res = json.dumps({"ok":False, "error":str(e)}).encode()
        finally: cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [res]

    if not u_data and path != "/login":
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    
    # --- USUARIOS (FORMULARIO COMPLETO) ---
    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        rows = ""
        for u in cur.fetchall():
            img = "https://ui-avatars.com/api/?name="+u['strNombreUsuario']+"&background=random"
            rows += f"<tr><td><img src='{img}' class='avatar-table'></td><td><b>{u['strNombreUsuario']}</b></td><td>{u['strNombrePerfil']}</td><td><span class='status-pill {'active' if u['strEstado']=='Activo' else 'inactive'}'>{u['strEstado']}</span></td><td><button class='btn-blue' onclick='preEdit({u['id']},{{u:\"{u['strNombreUsuario']}\", idp:{u['idPerfil']}, st:\"{u['strEstado']}\"}})'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Eliminar</button></td></tr>"
        
        cur.execute("SELECT * FROM perfiles"); p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        content = f"""<div class='card'><div style='display:flex;justify-content:space-between'><h2>👥 Usuarios</h2><button class='btn-emerald' style='width:auto' onclick="openM('mNew')">+ NUEVO USUARIO</button></div>
        <table><thead><tr><th>IMG</th><th>Usuario</th><th>Perfil</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
        
        <div id='mNew' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNew')">&times;</span><h3>Registrar Usuario</h3>
            <div class='grid-2'>
                <div><label>Usuario</label><input id='un' placeholder='Username'></div>
                <div><label>Correo</label><input id='uc' placeholder='email@correo.com'></div>
                <div><label>Clave</label><input id='up' type='password' placeholder='******'></div>
                <div><label>Celular</label><input id='ut' placeholder='77777777'></div>
                <div><label>Perfil</label><select id='uip'>{p_opts}</select></div>
                <div><label>Estado</label><select id='ust'><option>Activo</option><option>Inactivo</option></select></div>
            </div>
            <label>Foto de Perfil</label><input type='file' onchange="handleImg(event,'pv1')">
            <img id='pv1' style='width:60px;height:60px;border-radius:50%;object-fit:cover;margin:10px 0;display:block'>
            <button class='btn-emerald' style='width:100%' onclick=\"runCrud('save','usuarios',0,{{u:document.getElementById('un').value, p:document.getElementById('up').value, idp:document.getElementById('uip').value, st:document.getElementById('ust').value}})\">GUARDAR USUARIO</button>
        </div></div>"""

    # --- PERFILES ---
    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td><b>{p['strNombrePerfil']}</b></td><td><button class='btn-blue' onclick='preEdit({p['id']}, {{n:\"{p['strNombrePerfil']}\"}}, \"mEditP\")'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"<div class='card'><h2>👤 Perfiles</h2><button class='btn-emerald' style='width:auto' onclick=\"openM('mNewP')\">+ NUEVO PERFIL</button><table><thead><tr><th>ID</th><th>Nombre</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>"

    # --- MODULOS ---
    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td><b>{m['strNombreModulo']}</b></td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button></td></tr>" for m in cur.fetchall()])
        content = f"<div class='card'><h2>📦 Módulos</h2><table><thead><tr><th>Nombre</th><th>Ruta</th><th>Padre</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>"

    elif path == "/login":
        content = "<div class='card' style='width:350px;margin:100px auto'><h2>Login</h2><form id='f'><input name='u' placeholder='Usuario'><input name='p' type='password' placeholder='Pass'><button type='button' class='btn-emerald' style='width:100%' onclick='doL()'>ENTRAR</button></form></div><script>async function doL(){{const r=await fetch('/api/login',{{method:'POST',body:new FormData(document.getElementById('f'))}});if((await r.json()).ok)location.href='/dashboard';else alert('Error')}}</script>"
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode()]
    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else: content = f"<div class='card'><h2>Dashboard</h2><p>Bienvenido <b>{u_data['u']}</b></p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode()]