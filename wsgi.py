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
# MAQUETACIÓN ESTILO ORIGINAL (DARK NEON)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT idPerfil FROM usuarios WHERE strNombreUsuario=%s", (user['u'],))
        u_pid = (cur.fetchone() or {}).get('idPerfil', 0)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in all_mods if m['strMenuPadre'] == padre])
        
        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">
            <a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Modulos</a><a href="/usuarios">👥 Usuarios</a><a href="/permisos">🔐 Permisos</a>
        </div></div>
        <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1")}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2")}</div></div>
        </div><div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; --pill-active: #065f46; --pill-inactive: #7f1d1d; }}
        body {{ font-family: 'Inter', sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
        .logo {{ color:var(--emerald); font-weight:bold; font-size:1.2rem; margin-right:20px; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; padding:10px; font-size:14px; transition: 0.3s; }}
        .nav-link:hover {{ color:white; }}
        .dropdown {{ position:relative; display:inline-block; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:15px; cursor:pointer; font-size:14px; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:200px; border:1px solid var(--border); border-radius:12px; z-index:100; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); overflow:hidden; }}
        .dropdown-content a {{ color:white; padding:12px 16px; text-decoration:none; display:block; font-size:13px; border-bottom: 1px solid #334155; }}
        .dropdown-content a:hover {{ background: #2d3e5a; }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .container {{ padding:40px; max-width:1200px; margin:0 auto; }}
        .card {{ background:var(--card); padding:30px; border-radius:16px; border:1px solid var(--border); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }}
        h2 {{ margin-top:0; font-weight: 600; letter-spacing: -0.025em; }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; background:#0f172a; border-radius:12px; overflow:hidden; }}
        th {{ background:#1e293b; color:#94a3b8; font-size:12px; text-transform:uppercase; padding:15px; text-align:left; letter-spacing: 0.05em; }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:14px; }}
        .avatar {{ width:40px; height:40px; border-radius:50%; object-fit: cover; background:#334155; vertical-align:middle; margin-right:12px; border: 2px solid var(--border); }}
        .status-pill {{ padding:4px 12px; border-radius:20px; font-size:11px; font-weight:bold; }}
        .active {{ background:var(--pill-active); color:#34d399; }}
        .inactive {{ background:var(--pill-inactive); color:#f87171; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; font-size:14px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; transition: 0.2s; }}
        .btn-emerald:hover {{ background: #059669; transform: translateY(-1px); }}
        .btn-blue {{ color:#3b82f6; background:none; border:none; cursor:pointer; font-weight:500; padding:5px 10px; }}
        .btn-red {{ color:#ef4444; background:none; border:none; cursor:pointer; font-weight:500; padding:5px 10px; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; backdrop-filter: blur(4px); }}
        .modal-content {{ background:var(--card); width:600px; margin:5% auto; padding:35px; border-radius:20px; border: 1px solid var(--border); position:relative; }}
        .grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:20px; }}
        .close-x {{ position:absolute; top:20px; right:25px; color:#94a3b8; cursor:pointer; font-size:24px; }}
        .user-pill {{ color:var(--emerald); border:1px solid var(--border); padding:6px 16px; border-radius:25px; margin-right:15px; font-size:13px; font-weight: 500; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 18px; border-radius:8px; font-size:13px; font-weight:bold; }}
    </style>
    <script>
        function openM(id, isEdit=false) {{ 
            if(!isEdit) {{
                document.querySelectorAll('#'+id+' input').forEach(i => i.value='');
                document.querySelectorAll('#'+id+' img').forEach(img => img.src='');
            }}
            document.getElementById(id).style.display='block'; 
        }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            if((await res.json()).ok) location.reload(); else alert("Error en el servidor");
        }}
        function preEdit(id, fields, modalId='mEdit') {{
            for(let k in fields) {{ 
                let el = document.getElementById('ed_'+k);
                if(el) el.value = fields[k];
            }}
            document.getElementById('ed_id').value = id;
            openM(modalId, true);
        }}
        function handleImg(e, prevId, hiddenId) {{
            const reader = new FileReader();
            reader.onload = () => {{ document.getElementById(prevId).src = reader.result; document.getElementById(hiddenId).value = reader.result; }};
            reader.readAsDataURL(e.target.files[0]);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/"); method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ); content = ""

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
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    if not u_data and path != "/login":
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- MOTOR CRUD ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save':
                if p['table'] == 'usuarios':
                    cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,%s)", (p['data']['u'], hash_password(p['data']['p']), p['data']['idp'], p['data']['st']))
                elif p['table'] == 'perfiles':
                    cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['n'],))
                elif p['table'] == 'modulos':
                    cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)", (p['data']['n'], p['data']['r'], p['data']['p']))
            elif p['action'] == 'update':
                if p['table'] == 'usuarios':
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s WHERE id=%s", (p['data']['u'], p['data']['idp'], p['data']['st'], p['id']))
                elif p['table'] == 'perfiles':
                    cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (p['data']['n'], p['id']))
                elif p['table'] == 'modulos':
                    cur.execute("UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s", (p['data']['n'], p['data']['r'], p['data']['p'], p['id']))
            conn.commit(); res = b'{"ok":true}'
        except Exception as e: conn.rollback(); res = json.dumps({"ok":False, "error":str(e)}).encode()
        finally: cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [res]

    # --- VISTAS ---
    if path == "/login":
        content = "<div class='card' style='width:350px;margin:100px auto;text-align:center;'><h2>🏥 Clinica Login</h2><form id='f'><input name='u' placeholder='Usuario'><input name='p' type='password' placeholder='Contraseña'><button type='button' class='btn-emerald' style='width:100%' onclick='doL()'>ACCEDER</button></form></div><script>async function doL(){{const r=await fetch('/api/login',{{method:'POST',body:new FormData(document.getElementById('f'))}});if((await r.json()).ok)location.href='/dashboard';else alert('Acceso denegado')}}</script>"
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode()]

    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        rows = "".join([f"<tr><td><img src='' class='avatar'></td><td><b>{u['strNombreUsuario']}</b></td><td>{u['strNombrePerfil']}</td><td><span class='status-pill {'active' if u['strEstado']=='Activo' else 'inactive'}'>{u['strEstado']}</span></td><td><button class='btn-blue' onclick='preEdit({u['id']},{{u:\"{u['strNombreUsuario']}\", idp:{u['idPerfil']}, st:\"{u['strEstado']}\"}})'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Eliminar</button></td></tr>" for u in cur.fetchall()])
        cur.execute("SELECT * FROM perfiles"); p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        
        content = f"""<div class='card'><div style='display:flex;justify-content:space-between'><h2>👥 Gestión de Usuarios</h2><button class='btn-emerald' onclick="openM('mNew')">+ NUEVO USUARIO</button></div>
        <table><thead><tr><th>IMG</th><th>Usuario</th><th>Perfil</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
        
        <div id='mNew' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNew')">&times;</span><h3>Registrar Usuario</h3>
            <div class='grid-2'><div><label>Usuario</label><input id='un'></div><div><label>Correo</label><input id='uc'></div><div><label>Clave</label><input id='up' type='password'></div><div><label>Celular</label><input id='ut'></div><div><label>Perfil</label><select id='uip'>{p_opts}</select></div><div><label>Estado</label><select id='ust'><option>Activo</option><option>Inactivo</option></select></div></div>
            <label>Foto de Perfil</label><input type='file' onchange="handleImg(event,'pv1','hi1')"><img id='pv1' style='width:50px;border-radius:50%'><input type='hidden' id='hi1'>
            <button class='btn-emerald' style='width:100%' onclick=\"runCrud('save','usuarios',0,{{u:document.getElementById('un').value, p:document.getElementById('up').value, idp:document.getElementById('uip').value, st:document.getElementById('ust').value}})\">GUARDAR USUARIO</button>
        </div></div>
        <div id='mEdit' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mEdit')">&times;</span><h3>Editar Usuario</h3><input type='hidden' id='ed_id'>
            <label>Nombre de Usuario</label><input id='ed_u'><label>Perfil</label><select id='ed_idp'>{p_opts}</select><label>Estado</label><select id='ed_st'><option>Activo</option><option>Inactivo</option></select>
            <button class='btn-emerald' style='width:100%' onclick=\"runCrud('update','usuarios',document.getElementById('ed_id').value,{{u:document.getElementById('ed_u').value, idp:document.getElementById('ed_idp').value, st:document.getElementById('ed_st').value}})\">ACTUALIZAR DATOS</button>
        </div></div>"""

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td><b>{p['strNombrePerfil']}</b></td><td><button class='btn-blue' onclick='preEdit({p['id']}, {{n:\"{p['strNombrePerfil']}\"}})'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"""<div class='card'><h2>👤 Perfiles de Acceso</h2><button class='btn-emerald' onclick="openM('mNew')">+ NUEVO PERFIL</button><table><thead><tr><th>ID</th><th>Nombre del Perfil</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div id='mNew' class='modal'><div class='modal-content'><h3>Nuevo Perfil</h3><input id='pn' placeholder='Ej: Administrador'><button class='btn-emerald' style='width:100%' onclick=\"runCrud('save','perfiles',0,{{n:document.getElementById('pn').value}})\">CREAR PERFIL</button></div></div>
        <div id='mEdit' class='modal'><div class='modal-content'><h3>Editar Perfil</h3><input type='hidden' id='ed_id'><input id='ed_n'><button class='btn-emerald' style='width:100%' onclick=\"runCrud('update','perfiles',document.getElementById('ed_id').value,{{n:document.getElementById('ed_n').value}})\">ACTUALIZAR PERFIL</button></div></div>"""

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td><b>{m['strNombreModulo']}</b></td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-blue' onclick='preEdit({m['id']}, {{n:\"{m['strNombreModulo']}\", r:\"{m['strRuta']}\", p:\"{m['strMenuPadre']}\"}})'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button></td></tr>" for m in cur.fetchall()])
        content = f"""<div class='card'><h2>📦 Módulos del Sistema</h2><button class='btn-emerald' onclick="openM('mNew')">+ NUEVO MÓDULO</button><table><thead><tr><th>Nombre</th><th>Ruta</th><th>Padre</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div id='mNew' class='modal'><div class='modal-content'><h3>Registrar Módulo</h3><input id='mn' placeholder='Nombre del Módulo'><input id='mr' placeholder='Ruta (ej: /pacientes)'><select id='mp'><option>Principal 1</option><option>Principal 2</option></select><button class='btn-emerald' style='width:100%' onclick=\"runCrud('save','modulos',0,{{n:document.getElementById('mn').value, r:document.getElementById('mr').value, p:document.getElementById('mp').value}})\">GUARDAR MÓDULO</button></div></div>
        <div id='mEdit' class='modal'><div class='modal-content'><h3>Editar Módulo</h3><input type='hidden' id='ed_id'><input id='ed_n'><input id='ed_r'><select id='ed_p'><option>Principal 1</option><option>Principal 2</option></select><button class='btn-emerald' style='width:100%' onclick=\"runCrud('update','modulos',document.getElementById('ed_id').value,{{n:document.getElementById('ed_n').value, r:document.getElementById('ed_r').value, p:document.getElementById('ed_p').value}})\">ACTUALIZAR MÓDULO</button></div></div>"""

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else: content = f"<div class='card'><h2>Dashboard</h2><p>Bienvenido al sistema clínico, <b>{u_data['u']}</b>. Utiliza el menú superior para navegar.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode()]