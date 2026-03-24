# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# =========================================================
# CONFIGURACIÓN
# =========================================================
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_FINAL_V_PRO"

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
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4', consume_results=True)

# =========================================================
# MAQUETACIÓN Y SEGURIDAD DE MENÚ
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        # Obtenemos solo los módulos que el perfil del usuario puede VER
        cur.execute("""
            SELECT m.* FROM modulos m 
            JOIN permisos p ON m.id = p.idModulo 
            WHERE p.idPerfil = %s AND p.blnVer = 1
        """, (user['idp'],))
        mods_db = cur.fetchall()
        cur.close(); conn.close()
        
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_db if m['strMenuPadre'] == padre])
        
        # El menú de Seguridad solo se muestra si el usuario tiene permisos en esos módulos específicos
        seg_links = get_links("Seguridad")
        p1_links = get_links("Principal 1")
        p2_links = get_links("Principal 2")

        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        {f'<div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{seg_links}</div></div>' if seg_links else ''}
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
            const permisos = [];
            rows.forEach(tr => {{
                const checks = tr.querySelectorAll("input[type='checkbox']");
                permisos.append({{
                    idm: tr.dataset.idm,
                    v: checks[0].checked ? 1 : 0,
                    c: checks[1].checked ? 1 : 0,
                    e: checks[2].checked ? 1 : 0,
                    d: checks[3].checked ? 1 : 0
                }});
            }});
            const res = await fetch('/api/permisos', {{ method:'POST', body:JSON.stringify({{idp: idPerfil, lista: permisos}}) }});
            if(res.ok) alert("Permisos actualizados!");
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
        cur.execute("SELECT id, strNombreUsuario, idPerfil FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "idp": user['idPerfil'], "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")])
        return [b'{"ok":false, "msg":"Credenciales Incorrectas"}']

    if path == "/login":
        content = """<div class="card" style="width:350px; margin:100px auto;">
            <h2 style="text-align:center">🏥 CLINICA LOGIN</h2>
            <form id="fL">
                <input name="u" placeholder="Usuario">
                <input name="p" type="password" placeholder="Contraseña">
                <button type="button" class="btn-emerald" style="width:100%" onclick="doLogin()">ENTRAR</button>
            </form></div>
            <script>async function doLogin(){{
                const f = new FormData(document.getElementById("fL"));
                const r = await fetch("/api/login",{{method:"POST",body:f}});
                const d = await r.json(); if(d.ok) location.href="/dashboard"; else alert(d.msg);
            }}</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API PERMISOS ---
    if path == "/api/permisos" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        for item in p['lista']:
            cur.execute("""
                INSERT INTO permisos (idPerfil, idModulo, blnVer, blnCrear, blnEditar, blnEliminar) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                ON DUPLICATE KEY UPDATE blnVer=%s, blnCrear=%s, blnEditar=%s, blnEliminar=%s
            """, (p['idp'], item['idm'], item['v'], item['c'], item['e'], item['d'], item['v'], item['c'], item['e'], item['d']))
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
        table_html = "<div style='text-align:center; padding:40px; color:#94a3b8;'>⚠️ Seleccione un perfil para gestionar accesos.</div>"
        if pid > 0:
            cur.execute("SELECT id, strNombreModulo as n FROM modulos")
            mods = cur.fetchall()
            # Obtener permisos actuales para marcarlos como checked
            cur.execute("SELECT * FROM permisos WHERE idPerfil = %s", (pid,))
            perm_dict = {x['idModulo']: x for x in cur.fetchall()}
            
            m_rows = ""
            for m in mods:
                p = perm_dict.get(m['id'], {'blnVer':0, 'blnCrear':0, 'blnEditar':0, 'blnEliminar':0})
                chk = lambda v: "checked" if v else ""
                m_rows += f"""<tr data-idm="{m['id']}"><td>{m['n']}</td>
                    <td><input type='checkbox' {chk(p['blnVer'])}></td>
                    <td><input type='checkbox' {chk(p['blnCrear'])}></td>
                    <td><input type='checkbox' {chk(p['blnEditar'])}></td>
                    <td><input type='checkbox' {chk(p['blnEliminar'])}></td></tr>"""
            
            table_html = f"""<div style="text-align:right; margin:15px;"><button class="btn-emerald" style="background:#334155" onclick="toggleAll()">TODOS</button></div>
            <table><thead><tr><th>Modulo</th><th>Ver</th><th>Crear</th><th>Editar</th><th>Borrar</th></tr></thead><tbody>{m_rows}</tbody></table>
            <button class="btn-emerald" style="width:100%; margin-top:20px" onclick="savePermisos({pid})">GUARDAR CAMBIOS</button>"""
        
        opts = "".join([f"<option value='{p['id']}' {'selected' if p['id']==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        content = f"<div class='card'><h2>🔐 Matriz de Permisos</h2><select onchange=\"location.href='?p='+this.value\"><option value='0'>-- Elegir Perfil --</option>{opts}</select>{table_html}</div>"

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0; Path=/")]); return [b""]
    else:
        content = f"<div class='card'><h2>Bienvenido</h2><p>Acceso concedido para {u_data['u']}. Usa el menu superior.</p></div>"

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode("utf-8")]