# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_V3_SECURITY"

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
        # Verificamos que traiga el ID de perfil (idp) para evitar el KeyError
        return p if p['exp'] > time.time() and 'idp' in p else None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4', consume_results=True)

# =========================================================
# MAQUETACIÓN Y AUTORIZACIÓN
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        # Cargamos solo los módulos que el usuario puede VER
        # Nota: Los módulos de sistema (Perfiles, Usuarios, Permisos) deben estar en la tabla 'modulos' con estos nombres exactos
        cur.execute("""
            SELECT m.* FROM modulos m 
            JOIN permisos p ON m.id = p.idModulo 
            WHERE p.idPerfil = %s AND p.blnVer = 1
        """, (user['idp'],))
        mods_db = cur.fetchall()
        cur.close(); conn.close()
        
        def get_links(padre):
            links = "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_db if m['strMenuPadre'] == padre])
            return links

        s_links = get_links("Seguridad")
        p1_links = get_links("Principal 1")
        p2_links = get_links("Principal 2")

        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        {f'<div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{s_links}</div></div>' if s_links else ''}
        {f'<div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{p1_links}</div></div>' if p1_links else ''}
        {f'<div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{p2_links}</div></div>' if p2_links else ''}
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
        .container {{ padding:40px; max-width:1100px; margin:0 auto; }}
        .card {{ background:var(--card); padding:25px; border-radius:12px; border:1px solid var(--border); }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; background:#0f172a; border-radius:8px; }}
        th, td {{ padding:15px; border-bottom:1px solid var(--border); text-align:left; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold; }}
        .btn-red {{ background:#ef4444; color:white; border:none; padding:8px 12px; border-radius:6px; cursor:pointer; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; }}
        .modal-content {{ background:var(--card); width:450px; margin:10% auto; padding:30px; border-radius:15px; position:relative; border: 1px solid var(--border); }}
        .close-x {{ position:absolute; top:15px; right:20px; color:#94a3b8; cursor:pointer; font-size:24px; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 15px; border-radius:8px; font-size:13px; }}
        .user-pill {{ color:var(--emerald); background: rgba(16, 185, 129, 0.1); padding: 5px 12px; border-radius: 20px; font-size: 13px; margin-right: 15px; }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        function toggleAll() {{ document.querySelectorAll('tbody input[type="checkbox"]').forEach(i => i.checked = !i.checked); }}
        
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            if(res.ok) location.reload(); else alert("Error en el servidor");
        }}

        async function savePermisos(idPerfil) {{
            const rows = document.querySelectorAll("tbody tr");
            const lista = [];
            rows.forEach(tr => {{
                const idm = tr.getAttribute("data-idm");
                const checks = tr.querySelectorAll("input[type='checkbox']");
                lista.push({{ idm, v: checks[0].checked?1:0, c: checks[1].checked?1:0, e: checks[2].checked?1:0, d: checks[3].checked?1:0 }});
            }});
            const res = await fetch('/api/permisos', {{ method:'POST', body:JSON.stringify({{idp: idPerfil, lista}}) }});
            if(res.ok) alert("Permisos guardados con éxito.");
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # --- RUTA LOGIN ---
    if path == "/login":
        if method == "POST":
            fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
            u, p = fs.getvalue("u"), hash_password(fs.getvalue("p"))
            conn = conectar_bd(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, strNombreUsuario, idPerfil FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
            user = cur.fetchone(); cur.close(); conn.close()
            if user:
                tk = jwt_encode({"u": user['strNombreUsuario'], "idp": user['idPerfil'], "exp": time.time()+3600})
                start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
                return [b'{"ok":true}']
            start_response("200 OK", [("Content-Type", "application/json")])
            return [b'{"ok":false, "msg":"Usuario o Clave incorrectos"}']
        
        content = """<div class="card" style="width:350px; margin:100px auto;">
            <h2 style="text-align:center">🏥 ACCESO</h2>
            <input id="un" placeholder="Usuario"><input id="up" type="password" placeholder="Clave">
            <button class="btn-emerald" style="width:100%" onclick="login()">ENTRAR</button></div>
            <script>async function login(){{
                const f = new FormData(); f.append("u", document.getElementById("un").value); f.append("p", document.getElementById("up").value);
                const r = await fetch("/login", {{method:"POST", body:f}});
                const d = await r.json(); if(d.ok) location.href="/dashboard"; else alert(d.msg);
            }}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- VERIFICACIÓN DE PERMISO DE RUTA ---
    # Si no es el dashboard, verificamos si tiene permiso de 'blnVer' para esta ruta
    if path not in ["/dashboard", "/logout", "/api/crud", "/api/permisos"]:
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("""
            SELECT p.blnVer FROM permisos p 
            JOIN modulos m ON p.idModulo = m.id 
            WHERE p.idPerfil = %s AND m.strRuta = %s
        """, (u_data['idp'], path))
        row = cur.fetchone(); cur.close(); conn.close()
        if not row or row[0] == 0:
            start_response("303 See Other", [("Location", "/dashboard")]); return [b""]

    # --- API PERMISOS ---
    if path == "/api/permisos" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        for i in p['lista']:
            cur.execute("""
                INSERT INTO permisos (idPerfil, idModulo, blnVer, blnCrear, blnEditar, blnEliminar) 
                VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE 
                blnVer=VALUES(blnVer), blnCrear=VALUES(blnCrear), blnEditar=VALUES(blnEditar), blnEliminar=VALUES(blnEliminar)
            """, (p['idp'], i['idm'], i['v'], i['c'], i['e'], i['d']))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- API CRUD ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        if p['action'] == 'delete': cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
        elif p['action'] == 'save_modulo': cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)", (p['data']['n'], p['data']['r'], p['data']['p']))
        elif p['action'] == 'save_perfil': cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data']['n'],))
        elif p['action'] == 'save_usuario': cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,'Activo')", (p['data']['u'], hash_password(p['data']['p']), p['data']['idp']))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/permisos":
        pid = int(urllib.parse.parse_qs(environ.get('QUERY_STRING','')).get('p',['0'])[0])
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        table_html = "<p style='text-align:center; padding:20px;'>Seleccione un perfil arriba.</p>"
        if pid > 0:
            cur.execute("SELECT id, strNombreModulo as n FROM modulos")
            mods = cur.fetchall()
            cur.execute("SELECT * FROM permisos WHERE idPerfil = %s", (pid,))
            p_map = {x['idModulo']: x for x in cur.fetchall()}
            m_rows = ""
            for m in mods:
                p = p_map.get(m['id'], {'blnVer':0, 'blnCrear':0, 'blnEditar':0, 'blnEliminar':0})
                c = lambda v: "checked" if v else ""
                m_rows += f"<tr data-idm='{m['id']}'><td>{m['n']}</td><td><input type='checkbox' {c(p['blnVer'])}></td><td><input type='checkbox' {c(p['blnCrear'])}></td><td><input type='checkbox' {c(p['blnEditar'])}></td><td><input type='checkbox' {c(p['blnEliminar'])}></td></tr>"
            table_html = f"<table><thead><tr><th>Modulo</th><th>Ver</th><th>Crear</th><th>Editar</th><th>Borrar</th></tr></thead><tbody>{m_rows}</tbody></table><button class='btn-emerald' style='width:100%;margin-top:15px' onclick='savePermisos({pid})'>GUARDAR</button>"
        
        opts = "".join([f"<option value='{p['id']}' {'selected' if p['id']==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        content = f"<div class='card'><h2>🔐 Permisos</h2><select onchange=\"location.href='?p='+this.value\"><option value='0'>-- Perfil --</option>{opts}</select>{table_html}</div>"

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos")
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m['strMenuPadre']}</td><td><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">X</button></td></tr>" for m in cur.fetchall()])
        content = f"<div class='card'><h2>📦 Módulos</h2><button class='btn-emerald' onclick=\"openM('mM')\">+ NUEVO</button><table>{rows}</table></div><div id='mM' class='modal'><div class='modal-content'><input id='mn' placeholder='Nombre'><input id='mr' placeholder='/ruta'><select id='mp'><option>Principal 1</option><option>Principal 2</option><option>Seguridad</option></select><button class='btn-emerald' onclick=\"runCrud('save_modulo','modulos',0,{{n:document.getElementById('mn').value,r:document.getElementById('mr').value,p:document.getElementById('mp').value}})\">GUARDAR</button></div></div>"

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles")
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td><button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">X</button></td></tr>" for p in cur.fetchall()])
        content = f"<div class='card'><h2>👤 Perfiles</h2><button class='btn-emerald' onclick=\"openM('mP')\">+ NUEVO</button><table>{rows}</table></div><div id='mP' class='modal'><div class='modal-content'><input id='pn' placeholder='Nombre'><button class='btn-emerald' onclick=\"runCrud('save_perfil','perfiles',0,{{n:document.getElementById('pn').value}})\">GUARDAR</button></div></div>"

    elif path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u JOIN perfiles p ON u.idPerfil = p.id")
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strNombrePerfil']}</td><td><button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">X</button></td></tr>" for u in cur.fetchall()])
        cur.execute("SELECT * FROM perfiles"); opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
        content = f"<div class='card'><h2>👥 Usuarios</h2><button class='btn-emerald' onclick=\"openM('mU')\">+ NUEVO</button><table>{rows}</table></div><div id='mU' class='modal'><div class='modal-content'><input id='un' placeholder='User'><input id='up' type='password'><select id='uip'>{opts}</select><button class='btn-emerald' onclick=\"runCrud('save_usuario','usuarios',0,{{u:document.getElementById('un').value,p:document.getElementById('up').value,idp:document.getElementById('uip').value}})\">CREAR</button></div></div>"

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else:
        content = f"<div class='card'><h2>Panel de Control</h2><p>Bienvenido, <b>{u_data['u']}</b>. Tu perfil tiene acceso limitado según tu rol.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode("utf-8")]