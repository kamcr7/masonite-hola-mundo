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
# DISEÑO Y NAVEGACIÓN
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT idPerfil FROM usuarios WHERE strNombreUsuario=%s", (user['u'],))
        u_p = cur.fetchone(); u_pid = u_p['idPerfil'] if u_p else 0
        
        # Permisos
        if u_pid == 1:
            p_ok = ["Perfiles", "Usuarios", "Modulos", "Permisos"]
            cur.execute("SELECT strNombreModulo as n FROM modulos"); p_ok += [r['n'] for r in cur.fetchall()]
        else:
            cur.execute("SELECT nombreModulo FROM permisos WHERE idPerfil=%s AND permisoVer=1", (u_pid,))
            p_ok = [r['nombreModulo'] for r in cur.fetchall()]
        
        cur.execute("SELECT * FROM modulos"); mods_db = cur.fetchall()
        cur.close(); conn.close()
        
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' 
                           for m in mods_db if m['strMenuPadre'] == padre and m['strNombreModulo'] in p_ok])
        
        seg_links = "".join([
            f'<a href="/perfiles">👤 Perfiles</a>' if "Perfiles" in p_ok else "",
            f'<a href="/modulos">📦 Modulos</a>' if "Modulos" in p_ok else "",
            f'<a href="/usuarios">👥 Usuarios</a>' if "Usuarios" in p_ok else "",
            f'<a href="/permisos">🔐 Permisos</a>' if "Permisos" in p_ok else ""
        ])
        
        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{seg_links or '<a>(Sin Acceso)</a>'}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1") or '<a>(Vacio)</a>'}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2") or '<a>(Vacio)</a>'}</div></div>
        </div><div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
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
        th {{ background:#1e293b; color:#94a3b8; font-size:12px; padding:15px; text-align:left; }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:14px; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-blue {{ background:transparent; color:#3b82f6; border:none; cursor:pointer; margin-right:10px; }}
        .btn-red {{ background:transparent; color:#ef4444; border:none; cursor:pointer; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; }}
        .modal-content {{ background:var(--card); width:550px; margin:5% auto; padding:30px; border-radius:15px; border: 1px solid var(--border); position:relative; }}
        .grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:15px; }}
        .user-pill {{ color:var(--emerald); border:1px solid var(--border); padding:4px 12px; border-radius:20px; margin-right:10px; font-size:13px; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 15px; border-radius:8px; font-size:13px; }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            const d = await res.json();
            if(d.ok) location.reload(); else alert("Error: " + d.error);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)
    content = ""

    # --- LOGIN API ---
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

    # --- CRUD API ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save_usuario':
                cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,%s)", 
                           (p['data']['u'], hash_password(p['data']['p']), p['data']['idp'], p['data']['st']))
            elif p['action'] == 'save_perfil':
                cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['n'],))
            elif p['action'] == 'save_modulo':
                cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)", 
                           (p['data']['n'], p['data']['r'], p['data']['p']))
            conn.commit(); res_body = b'{"ok":true}'
        except Exception as e:
            conn.rollback(); res_body = json.dumps({"ok":False, "error": str(e)}).encode("utf-8")
        finally: cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [res_body]

    # --- VISTAS ---
    if path == "/login":
        content = f"<div class='card' style='width:350px; margin:100px auto'><h2>Login</h2><form id='f'><input name='u' placeholder='Usuario'><input name='p' type='password' placeholder='Pass'><button type='button' class='btn-emerald' style='width:100%' onclick='doL()'>ENTRAR</button></form></div><script>async function doL(){{const r=await fetch('/api/login',{{method:'POST',body:new FormData(document.getElementById('f'))}});if((await r.json()).ok)location.href='/dashboard';else alert('Error')}}</script>"
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strNombrePerfil']}</td><td>{u['strEstado']}</td><td><button class='btn-blue'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Eliminar</button></td></tr>" for u in cur.fetchall()])
        cur.execute("SELECT * FROM perfiles"); p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        content = f"<div class='card'><h2>👥 Usuarios</h2><button class='btn-emerald' onclick=\"openM('mU')\">+ NUEVO</button><table><thead><tr><th>Usuario</th><th>Perfil</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div><div id='mU' class='modal'><div class='modal-content'><h3>Nuevo Usuario</h3><div class='grid-2'><div><label>Usuario</label><input id='un'></div><div><label>Correo</label><input id='uc'></div><div><label>Clave</label><input id='up' type='password'></div><div><label>Celular</label><input id='ut'></div><div><label>Perfil</label><select id='uip'>{p_opts}</select></div><div><label>Estado</label><select id='ust'><option>Activo</option><option>Inactivo</option></select></div></div><button class='btn-emerald' style='width:100%' onclick=\"runCrud('save_usuario','usuarios',0,{{u:document.getElementById('un').value, p:document.getElementById('up').value, idp:document.getElementById('uip').value, st:document.getElementById('ust').value}})\">GUARDAR</button><br><br><button onclick=\"closeM('mU')\">Cerrar</button></div></div>"

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-blue'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button></td></tr>" for p in cur.fetchall()])
        content = f"<div class='card'><h2>👤 Perfiles</h2><button class='btn-emerald' onclick=\"openM('mP')\">+ NUEVO</button><table><thead><tr><th>ID</th><th>Perfil</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div><div id='mP' class='modal'><div class='modal-content'><h3>Nuevo Perfil</h3><input id='pn' placeholder='Nombre'><button class='btn-emerald' style='width:100%' onclick=\"runCrud('save_perfil','perfiles',0,{{n:document.getElementById('pn').value}})\">GUARDAR</button></div></div>"

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-blue'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button></td></tr>" for m in cur.fetchall()])
        content = f"<div class='card'><h2>📦 Módulos</h2><button class='btn-emerald' onclick=\"openM('mM')\">+ NUEVO</button><table><thead><tr><th>Nombre</th><th>Ruta</th><th>Padre</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div><div id='mM' class='modal'><div class='modal-content'><h3>Nuevo Módulo</h3><input id='mn' placeholder='Nombre'><input id='mr' placeholder='Ruta'><select id='mp'><option>Principal 1</option><option>Principal 2</option></select><button class='btn-emerald' style='width:100%' onclick=\"runCrud('save_modulo','modulos',0,{{n:document.getElementById('mn').value, r:document.getElementById('mr').value, p:document.getElementById('mp').value}})\">GUARDAR</button></div></div>"

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else:
        content = f"<div class='card'><h2>Dashboard</h2><p>Bienvenido, <b>{u_data['u']}</b>.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode("utf-8")]