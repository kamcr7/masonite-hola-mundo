# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# --- CONFIGURACIÓN ---
DB_URL = os.getenv('DB_URL', 'mysql://root:mxvHDOGWiQGekUUTxIFAXnIpmRlHnFZu@mysql.railway.internal:3306/railway')
JWT_SECRET = "CLAVE_MAESTRA_CLINICA_2026_SECURITY"

def hash_password(p): return hashlib.sha256((p or "").encode("utf-8")).hexdigest()
def b64url_encode(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode("utf-8")

def jwt_encode(p):
    h = b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode("utf-8"))
    py = b64url_encode(json.dumps(p).encode("utf-8"))
    s = hmac.new(JWT_SECRET.encode("utf-8"), f"{h}.{py}".encode("utf-8"), hashlib.sha256).digest()
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

# --- LAYOUT ---
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        
        # Filtramos para no mostrar los nombres técnicos como "Usuario" o "Perfil" en el menú
        bloqueados = ["perfil", "módulo", "modulo", "usuario", "permisos-perfil"]
        menu_html = ""
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos</a><a href="/usuarios">👥 Usuarios</a>'
            
            subs = [m for m in all_mods if m.get('strMenuPadre') == m_padre and m['strNombreModulo'].lower() not in bloqueados]
            for s in subs: links += f'<a href="/m/{s["id"]}">📄 {s["strNombreModulo"]}</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        
        nav = f"""<div class="top-nav"><div class="nav-left"><span class="logo">🛡️ Clínica Santa Mónica</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div><div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none;">Salir</a></div></div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; margin:0;}}
        .top-nav{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b;}}
        .nav-left{{display:flex; gap:15px; align-items:center;}}
        .logo{{font-weight:bold; color:#38bdf8; font-size:1.1rem;}}
        .nav-link{{color:#94a3b8; text-decoration:none; font-size:0.9rem;}}
        .dropdown{{position:relative; display:inline-block;}}
        .dropbtn{{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 10px;}}
        .dropdown-content{{display:none; position:absolute; background:#1e293b; min-width:180px; border-radius:8px; border:1px solid #334155; z-index:1000;}}
        .dropdown-content a{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem;}}
        .dropdown:hover .dropdown-content{{display:block;}}
        .container{{padding:30px 40px;}}
        .card{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155;}}
        .btn-blue{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th{{text-align:left; color:#94a3b8; font-size:0.75rem; padding:15px; border-bottom:2px solid #334155; text-transform:uppercase;}}
        td{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem;}}
        .modal{{display:none; position:fixed; z-index:2000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8);}}
        .modal-content{{background:#ffffff; color:#334155; margin:5% auto; padding:25px; width:650px; border-radius:12px;}}
        .modal-content input, .modal-content select{{background:#f1f5f9; color:#1e293b; border:1px solid #cbd5e1; padding:10px; width:100%; border-radius:8px; margin-bottom:15px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

# --- WSGI ---
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    if path in ["/", "/login"]:
        # (Lógica de login igual a la anterior...)
        start_response("200 OK", [("Content-Type", "text/html")])
        return [render_layout("Login", "<h2>Login</h2>").encode("utf-8")]

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API UNIFICADA ---
    if method == "POST":
        conn = conectar_bd(); cur = conn.cursor()
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        
        # Eliminar genérico
        if path.startswith("/api/del_"):
            tabla = path.split("_")[2] + "s"
            cur.execute(f"DELETE FROM {tabla} WHERE id=%s", (fs.getvalue("id"),))
        
        # Guardar Usuario
        elif path == "/api/save_user":
            img = base64.b64encode(fs["img"].file.read()).decode("utf-8") if "img" in fs and fs["img"].filename else ""
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strCorreo, strPwd, strCelular, idPerfil, strEstado, strImagen) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (fs.getvalue("u"), fs.getvalue("e"), hash_password(fs.getvalue("p")), fs.getvalue("c"), fs.getvalue("pid"), fs.getvalue("est"), img))
        
        # Guardar Módulo
        elif path == "/api/save_mod":
            cur.execute("INSERT INTO modulos (strNombreModulo, strMenuPadre) VALUES (%s, %s)", (fs.getvalue("n"), fs.getvalue("p")))

        # Guardar Perfil
        elif path == "/api/save_per":
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s, %s)", (fs.getvalue("n"), fs.getvalue("a")))

        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    
    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        usrs = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles"); perfs = cur.fetchall()
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfs])
        rows = "".join([f"<tr><td><img src='data:image/png;base64,{u['strImagen']}' style='width:35px;height:35px;border-radius:50%;'></td><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strNombrePerfil']}</td><td>{u['strEstado']}</td><td><button onclick='delItem({u['id']}, \"user\")' style='color:red;'>Eliminar</button></td></tr>" for u in usrs])
        content = f"""<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Usuarios</h2><button class='btn-blue' onclick='showM("mUsr")'>+ Nuevo Usuario</button></div><table><tr><th>IMG</th><th>USUARIO</th><th>CORREO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr>{rows}</table></div>
        <div id="mUsr" class="modal"><div class="modal-content"><h3>Nuevo Usuario</h3><form id="fUsr">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
                <input name="u" placeholder="Nombre Usuario" required><input name="e" placeholder="Correo" type="email" required>
                <input name="p" placeholder="Contraseña" type="password" required><input name="c" placeholder="Celular">
                <select name="pid">{p_opts}</select><select name="est"><option>Activo</option><option>Inactivo</option></select>
            </div><input type="file" name="img"><button type="submit" class="btn-blue">Guardar</button></form></div></div>"""

    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td>{m.get('strMenuPadre','Seguridad')}</td><td><button onclick='delItem({m['id']}, \"mod\")' style='color:red;'>Eliminar</button></td></tr>" for m in mods])
        content = f"<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Módulos</h2><button class='btn-blue' onclick='showM(\"mMod\")'>+ Nuevo</button></div><table><tr><th>NOMBRE</th><th>MENÚ</th><th>ACCIONES</th></tr>{rows}</table></div>"
        content += f'<div id="mMod" class="modal"><div class="modal-content"><h3>Nuevo Módulo</h3><form id="fMod"><input name="n" placeholder="Nombre" required><select name="p"><option>Seguridad</option><option>Principal 1</option><option>Principal 2</option></select><button type="submit" class="btn-blue">Guardar</button></form></div></div>'

    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles"); pers = cur.fetchall()
        rows = "".join([f"<tr><td>{p['id']}</td><td>{p['strNombrePerfil']}</td><td>{'SÍ' if p['bitAdministrador'] else 'NO'}</td><td><button onclick='delItem({p['id']}, \"per\")' style='color:red;'>Eliminar</button></td></tr>" for p in pers])
        content = f"<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Perfiles</h2><button class='btn-blue' onclick='showM(\"mPer\")'>+ Nuevo</button></div><table><tr><th>ID</th><th>PERFIL</th><th>ADMIN</th><th>ACCIONES</th></tr>{rows}</table></div>"
        content += f'<div id="mPer" class="modal"><div class="modal-content"><h3>Nuevo Perfil</h3><form id="fPer"><input name="n" placeholder="Nombre" required><select name="a"><option value="1">SÍ</option><option value="0">NO</option></select><button type="submit" class="btn-blue">Guardar</button></form></div></div>'

    elif path == "/permisos":
        content = "<div class='card'><h2>Gestión de Permisos</h2><p>Seleccione un perfil para ver la matriz...</p></div>"

    else: content = "<div class='card'><h1>Bienvenido</h1></div>"

    scripts = """<script>
        const showM = id => document.getElementById(id).style.display='block';
        const setupF = (fid, url) => { 
            let f = document.getElementById(fid);
            if(f) f.onsubmit = async (e) => { e.preventDefault(); await fetch(url, {method:'POST', body:new FormData(e.target)}); location.reload(); };
        };
        setupF('fUsr', '/api/save_user'); setupF('fMod', '/api/save_mod'); setupF('fPer', '/api/save_per');
        async function delItem(id, tipo) { 
            if(confirm('¿Eliminar?')) { 
                let fd = new FormData(); fd.append('id', id); 
                await fetch('/api/del_'+tipo, {method:'POST', body:fd}); location.reload(); 
            } 
        }
    </script>"""
    
    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content + scripts, u_data).encode("utf-8")]