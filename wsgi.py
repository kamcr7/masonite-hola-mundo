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
# DISEÑO ORIGINAL RESTAURADO
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in all_mods if m['strMenuPadre'] == padre])
        
        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo" style="color:#10b981; font-weight:bold; font-size:1.2rem; margin-right:20px;">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">
            <a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Modulos</a><a href="/usuarios">👥 Usuarios</a>
        </div></div>
        <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1")}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2")}</div></div>
        </div><div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
        body {{ font-family: sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
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
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%; }}
        .btn-blue {{ color:#3b82f6; background:none; border:none; cursor:pointer; }}
        .btn-red {{ color:#ef4444; background:none; border:none; cursor:pointer; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; }}
        .modal-content {{ background:var(--card); width:500px; margin:5% auto; padding:35px; border-radius:20px; border: 1px solid var(--border); position:relative; }}
        .grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:15px; }}
        .close-x {{ position:absolute; top:20px; right:25px; color:#94a3b8; cursor:pointer; font-size:24px; }}
        .user-pill {{ color:var(--emerald); border:1px solid var(--border); padding:6px 16px; border-radius:25px; margin-right:15px; font-size:13px; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 18px; border-radius:8px; font-size:13px; font-weight:bold; }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            const j = await res.json();
            if(j.ok) location.reload(); 
            else alert("Error: " + (j.error || "Desconocido"));
        }}
        function preEdit(id, fields, mId='mEdit') {{
            for(let k in fields) {{ let el = document.getElementById('ed_'+k); if(el) el.value = fields[k]; }}
            document.getElementById('ed_id').value = id;
            openM(mId);
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
    u_data = verify_jwt(environ); content = ""

# --- API CRUD ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': 
                cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            elif p['action'] == 'save':
                if p['table'] == 'usuarios':
                    cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,%s)",
                               (p['data']['u'], hash_password(p['data']['p']), p['data']['idp'], p['data']['st']))
                elif p['table'] == 'perfiles':
                    # VALIDACIÓN DE DUPLICADOS (Ignora mayúsculas/minúsculas)
                    nombre = p['data']['n'].strip()
                    cur.execute("SELECT id FROM perfiles WHERE LOWER(strNombrePerfil) = LOWER(%s)", (nombre,))
                    if cur.fetchone():
                        raise Exception("Ese nombre de perfil ya existe")
                    cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (nombre,))
                elif p['table'] == 'modulos':
                    cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)",
                               (p['data']['n'], p['data']['r'], p['data']['p']))
            elif p['action'] == 'update':
                if p['table'] == 'usuarios':
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s WHERE id=%s",
                               (p['data']['u'], p['data']['idp'], p['data']['st'], p['id']))
                elif p['table'] == 'perfiles':
                    # VALIDACIÓN DE DUPLICADOS AL EDITAR (Que no sea el mismo ID)
                    nombre = p['data']['n'].strip()
                    cur.execute("SELECT id FROM perfiles WHERE LOWER(strNombrePerfil) = LOWER(%s) AND id != %s", (nombre, p['id']))
                    if cur.fetchone():
                        raise Exception("Ya existe otro perfil con ese nombre")
                    cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (nombre, p['id']))
                elif p['table'] == 'modulos':
                    cur.execute("UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s",
                               (p['data']['n'], p['data']['r'], p['data']['p'], p['id']))
            
            conn.commit(); res = b'{"ok":true}'
        except Exception as e: 
            conn.rollback(); res = json.dumps({"ok":False, "error":str(e)}).encode()
        finally: 
            cur.close(); conn.close()
        
        start_response("200 OK", [("Content-Type", "application/json")]); return [res]
        
    # --- PANTALLA USUARIOS ---
    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        rows = "".join([f"<tr><td><img src='https://ui-avatars.com/api/?name={u['strNombreUsuario']}&background=random' class='avatar-table'></td><td><b>{u['strNombreUsuario']}</b></td><td>{u['strNombrePerfil']}</td><td><span class='status-pill {'active' if u['strEstado']=='Activo' else 'inactive'}'>{u['strEstado']}</span></td><td><button class='btn-blue' onclick='preEdit({u['id']},{{u:\"{u['strNombreUsuario']}\", idp:{u['idPerfil']}, st:\"{u['strEstado']}\"}})'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Eliminar</button></td></tr>" for u in cur.fetchall()])
        cur.execute("SELECT * FROM perfiles"); p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        
        content = f"""<div class='card'><div style='display:flex;justify-content:space-between'><h2>👥 Gestión de Usuarios</h2><button class='btn-emerald' style='width:auto' onclick="openM('mNew')">+ NUEVO USUARIO</button></div>
        <table><thead><tr><th>IMG</th><th>USUARIO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div id='mNew' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNew')">&times;</span><h3>Nuevo Usuario</h3>
            <div class='grid-2'>
                <div><label>Usuario</label><input id='un'></div>
                <div><label>Pass</label><input id='up' type='password'></div>
                <div><label>Perfil</label><select id='un_idp'>{p_opts}</select></div>
                <div><label>Estado</label><select id='un_st'><option>Activo</option><option>Inactivo</option></select></div>
            </div>
            <label>Foto</label><input type='file' onchange="handleImg(event,'pv1')"><img id='pv1' style='width:50px;display:block;margin:10px 0'>
            <button class='btn-emerald' onclick=\"runCrud('save','usuarios',0,{{u:document.getElementById('un').value, p:document.getElementById('up').value, idp:document.getElementById('un_idp').value, st:document.getElementById('un_st').value}})\">GUARDAR</button></div></div>
        <div id='mEdit' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mEdit')">&times;</span><h3>Editar Usuario</h3><input type='hidden' id='ed_id'>
            <label>Usuario</label><input id='ed_u'><label>Perfil</label><select id='ed_idp'>{p_opts}</select><label>Estado</label><select id='ed_st'><option>Activo</option><option>Inactivo</option></select>
            <button class='btn-emerald' onclick=\"runCrud('update','usuarios',document.getElementById('ed_id').value,{{u:document.getElementById('ed_u').value, idp:document.getElementById('ed_idp').value, st:document.getElementById('ed_st').value}})\">ACTUALIZAR</button></div></div>"""

# --- PANTALLA PERFILES CORREGIDA ---
    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles ORDER BY id ASC")
        perfiles = cur.fetchall()
        rows = ""
        # Usamos enumerate para que la numeración visual sea siempre correlativa
        for index, p in enumerate(perfiles, start=1):
            rows += f"""<tr>
                <td>{index}</td>
                <td><b>{p['strNombrePerfil']}</b></td>
                <td>
                    <button class='btn-blue' onclick='preEdit({p['id']}, {{n:\"{p['strNombrePerfil']}\"}}, \"mEditP\")'>Editar</button>
                    <button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button>
                </td>
            </tr>"""
            
        content = f"""
        <div class='card'>
            <h2>👤 Gestión de Perfiles</h2>
            <button class='btn-emerald' style='width:auto' onclick="openM('mNewP')">+ NUEVO PERFIL</button>
            <table>
                <thead><tr><th>#</th><th>NOMBRE DEL PERFIL</th><th>ACCIONES</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>

        <div id='mNewP' class='modal'>
            <div class='modal-content'>
                <span class='close-x' onclick="closeM('mNewP')">&times;</span>
                <h3>Nuevo Perfil</h3>
                <label>Nombre del Perfil (Máx. 15 letras)</label>
                <input id='pn' placeholder='Ej: Ventas' maxlength="15"
                       oninput="this.value = this.value.replace(/[^A-Za-z\\s]/g, '')">
                <button class='btn-emerald' onclick=\"savePerfil()\">CREAR PERFIL</button>
            </div>
        </div>

        <div id='mEditP' class='modal'>
            <div class='modal-content'>
                <span class='close-x' onclick="closeM('mEditP')">&times;</span>
                <h3>Editar Perfil</h3>
                <input type='hidden' id='ed_id'>
                <label>Nombre del Perfil</label>
                <input id='ed_n' maxlength="15"
                       oninput="this.value = this.value.replace(/[^A-Za-z\\s]/g, '')">
                <button class='btn-emerald' onclick=\"updatePerfil()\">ACTUALIZAR</button>
            </div>
        </div>

        <script>
            // Funciones para limpiar espacios y enviar datos
            async function savePerfil() {{
                const nom = document.getElementById('pn').value.trim();
                if(!nom) return alert("Escribe un nombre válido");
                runCrud('save', 'perfiles', 0, {{n: nom}});
            }}

            async function updatePerfil() {{
                const id = document.getElementById('ed_id').value;
                const nom = document.getElementById('ed_n').value.trim();
                if(!nom) return alert("El nombre no puede estar vacío");
                runCrud('update', 'perfiles', id, {{n: nom}});
            }}
        </script>
        """

    # --- PANTALLA MODULOS ---
    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td><b>{m['strNombreModulo']}</b></td><td>{m['strRuta']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-blue' onclick='preEdit({m['id']}, {{n:\"{m['strNombreModulo']}\", r:\"{m['strRuta']}\", p:\"{m['strMenuPadre']}\"}}, \"mEditM\")'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button></td></tr>" for m in cur.fetchall()])
        content = f"""<div class='card'><h2>📦 Módulos</h2><button class='btn-emerald' style='width:auto' onclick="openM('mNewM')">+ NUEVO MÓDULO</button><table><thead><tr><th>NOMBRE</th><th>RUTA</th><th>PADRE</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div id='mNewM' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNewM')">&times;</span><h3>Nuevo Módulo</h3><input id='mn' placeholder='Nombre'><input id='mr' placeholder='Ruta'><select id='mp'><option>Principal 1</option><option>Principal 2</option></select><button class='btn-emerald' onclick=\"runCrud('save','modulos',0,{{n:document.getElementById('mn').value, r:document.getElementById('mr').value, p:document.getElementById('mp').value}})\">GUARDAR</button></div></div>
        <div id='mEditM' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mEditM')">&times;</span><h3>Editar Módulo</h3><input type='hidden' id='ed_id'><input id='ed_n'><input id='ed_r'><select id='ed_p'><option>Principal 1</option><option>Principal 2</option></select><button class='btn-emerald' onclick=\"runCrud('update','modulos',document.getElementById('ed_id').value,{{n:document.getElementById('ed_n').value, r:document.getElementById('ed_r').value, p:document.getElementById('ed_p').value}})\">ACTUALIZAR</button></div></div>"""

    elif path == "/login":
        content = "<div class='card' style='width:350px;margin:100px auto'><h2>Login</h2><form id='f'><input name='u' placeholder='Usuario'><input name='p' type='password' placeholder='Pass'><button type='button' class='btn-emerald' onclick='doL()'>ENTRAR</button></form></div><script>async function doL(){{const r=await fetch('/api/login',{{method:'POST',body:new FormData(document.getElementById('f'))}});if((await r.json()).ok)location.href='/dashboard';else alert('Error')}}</script>"
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode()]
    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else: content = f"<div class='card'><h2>Dashboard</h2><p>Bienvenido <b>{u_data['u'] if u_data else ''}</b></p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode()]