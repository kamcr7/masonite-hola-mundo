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
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4', consume_results=True)

# =========================================================
# MAQUETACIÓN
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); mods_db = cur.fetchall()
        cur.close(); conn.close()
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_db if m['strMenuPadre'] == padre])
        
        seg_links = f'<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Modulos</a><a href="/usuarios">👥 Usuarios</a><a href="/permisos">🔐 Permisos</a>{get_links("Seguridad")}'
        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        <div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{seg_links}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1") or '<a>(Vacio)</a>'}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2") or '<a>(Vacio)</a>'}</div></div>
        </div><div class="nav-right"><span class="user-pill" style="color:var(--emerald); margin-right:15px; font-size:13px; border:1px solid var(--border); padding:4px 10px; border-radius:20px;">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
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
        input[type="checkbox"] {{ width: 18px; height: 18px; cursor: pointer; accent-color: var(--emerald); }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        
        // Lógica de Seleccionar/Deseleccionar todo mejorada
        function toggleAll() {{
            const checks = document.querySelectorAll('tbody input[type="checkbox"]');
            const anyChecked = Array.from(checks).some(c => c.checked);
            checks.forEach(i => i.checked = !anyChecked);
            
            // Cambiar texto del botón opcionalmente
            const btn = document.getElementById('btnToggleAll');
            if(btn) btn.innerText = anyChecked ? "SELECCIONAR TODO" : "DESELECCIONAR TODO";
        }}
        
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            if(res.ok) location.reload(); else alert("Error en el servidor");
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

    # (Lógica de API LOGIN y API CRUD se mantiene igual al código anterior...)

    if not u_data and path != "/login":
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/permisos":
        pid = int(urllib.parse.parse_qs(environ.get('QUERY_STRING','')).get('p',['0'])[0])
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        table_html = "<p style='text-align:center; color:#94a3b8; padding:20px;'>⚠️ Seleccione un perfil para gestionar permisos.</p>"
        
        if pid > 0:
            cur.execute("SELECT strNombreModulo as n FROM modulos")
            all_m = [{'n':'Perfiles'},{'n':'Usuarios'},{'n':'Permisos'}] + cur.fetchall()
            m_rows = "".join([f"<tr><td>{m['n']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in all_m])
            table_html = f"""
            <div style="text-align:right; margin:10px 0;">
                <button id="btnToggleAll" class="btn-emerald" style="background:#334155" onclick="toggleAll()">SELECCIONAR TODO</button>
            </div>
            <table><thead><tr><th>Modulo</th><th>Ver</th><th>Crear</th><th>Editar</th><th>Eliminar</th></tr></thead><tbody>{m_rows}</tbody></table>
            <button class="btn-emerald" style="width:100%; margin-top:30px">GUARDAR PERMISOS</button>"""
            
        opts = "".join([f"<option value='{p['id']}' {'selected' if p['id']==pid else ''}>{p['strNombrePerfil']}</option>" for p in perfs])
        content = f"<div class='card'><h2>🔐 Permisos</h2><label>Perfil a configurar:</label><select onchange=\"location.href='?p='+this.value\"><option value='0'>-- Elegir Perfil --</option>{opts}</select>{table_html}</div>"

    elif path == "/modulos":
        # (Aquí va la lógica de módulos enviada antes con las tablas limpias)
        cur.execute("SELECT id, strNombreModulo as n, strRuta as r, strMenuPadre as p FROM modulos")
        mods_db = cur.fetchall()
        rows = "".join([f"<tr><td>{m['n']}</td><td>{m['r']}</td><td>{m['p']}</td><td><button class='btn-blue' onclick='editM(\"mEditM\", {json.dumps(m)})'>Editar</button><button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button></td></tr>" for m in mods_db])
        content = f"<div class='card'><h2>📦 Gestión de Módulos</h2><button class='btn-emerald' onclick=\"openM('mM')\">+ NUEVO MODULO</button><table><thead><tr><th>Nombre</th><th>Ruta</th><th>Padre</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table></div>"

    # (Resto de rutas /usuarios, /perfiles, etc...)
    
    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Clinica", content, u_data).encode("utf-8")]