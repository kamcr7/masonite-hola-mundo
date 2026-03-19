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

# --- LAYOUT MEJORADO ---
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        
        # Filtro estricto para evitar duplicados en el menú
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

# --- CONTROLADOR ---
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # CORRECCIÓN: Pantalla de Login forzada
    if path in ["/", "/login"] and not u_data:
        content = """<div class="card" style="max-width:350px; margin:100px auto; text-align:center;">
            <h2 style="color:#38bdf8;">Acceso al Sistema</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" style="margin-bottom:15px;">
                <input type="password" name="p" placeholder="Contraseña" style="margin-bottom:20px;">
                <center><div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div></center>
                <button type="button" onclick="doLogin()" class="btn-blue" style="width:100%; margin-top:20px;">Entrar</button>
            </form></div>
            <script>async function doLogin(){ 
                const res = await fetch('/api/login', {method:'POST', body:new FormData(document.getElementById('fL'))});
                const data = await res.json(); if(data.ok) location.href='/dashboard'; else alert("Error de acceso");
            }</script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly")])
            return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API CRUD (POST) ---
    if method == "POST":
        conn = conectar_bd(); cur = conn.cursor()
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        
        if path == "/api/del_user": cur.execute("DELETE FROM usuarios WHERE id=%s", (fs.getvalue("id"),))
        elif path == "/api/del_mod": cur.execute("DELETE FROM modulos WHERE id=%s", (fs.getvalue("id"),))
        elif path == "/api/del_per": cur.execute("DELETE FROM perfiles WHERE id=%s", (fs.getvalue("id"),))
        elif path == "/api/save_user":
            img = base64.b64encode(fs["img"].file.read()).decode("utf-8") if "img" in fs and fs["img"].filename else ""
            cur.execute("INSERT INTO usuarios (strNombreUsuario, strCorreo, strPwd, strCelular, idPerfil, strEstado, strImagen) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (fs.getvalue("u"), fs.getvalue("e"), hash_password(fs.getvalue("p")), fs.getvalue("c"), fs.getvalue("pid"), fs.getvalue("est"), img))
        elif path == "/api/save_mod":
            cur.execute("INSERT INTO modulos (strNombreModulo, strMenuPadre) VALUES (%s, %s)", (fs.getvalue("n"), fs.getvalue("p")))
        elif path == "/api/save_per":
            cur.execute("INSERT INTO perfiles (strNombrePerfil, bitAdministrador) VALUES (%s, %s)", (fs.getvalue("n"), fs.getvalue("a")))

        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        rows = "".join([f"<tr><td><img src='data:image/png;base64,{u['strImagen']}' style='width:35px;height:35px;border-radius:50%;'></td><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strNombrePerfil']}</td><td>{u['strEstado']}</td><td><button onclick='delItem({u['id']}, \"user\")' style='color:#ef4444; border:none; background:none; cursor:pointer;'>Eliminar</button></td></tr>" for u in cur.fetchall()])
        content = f"<div class='card'><h2>Gestión de Usuarios</h2><table><tr><th>IMG</th><th>USUARIO</th><th>CORREO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr>{rows}</table><button class='btn-blue' onclick='showM(\"mUsr\")' style='margin-top:15px;'>+ Nuevo Usuario</button></div>"
        content += '<div id="mUsr" class="modal"><div class="modal-content"><h3>Nuevo Usuario</h3><form id="fUsr"><input name="u" placeholder="Usuario"><input name="e" placeholder="Email"><input name="p" type="password" placeholder="Pass"><input name="c" placeholder="Celular"><select name="pid"><option value="1">Admin</option></select><select name="est"><option>Activo</option></select><input type="file" name="img"><button type="submit" class="btn-blue">Guardar</button></form></div></div>'

    elif path == "/permisos":
        # Matriz de permisos visual
        cur.execute("SELECT * FROM modulos")
        mods = cur.fetchall()
        rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"<div class='card'><h2>Matriz de Permisos</h2><table><tr><th>Módulo</th><th>Consultar</th><th>Agregar</th><th>Editar</th><th>Eliminar</th></tr>{rows}</table><button class='btn-blue' style='margin-top:20px;'>Guardar Matriz</button></div>"
    
    else: content = "<div class='card'><h1>Bienvenido al Panel</h1></div>"

    scripts = """<script>
        const showM = id => document.getElementById(id).style.display='block';
        const setupF = (fid, url) => { 
            let f = document.getElementById(fid);
            if(f) f.onsubmit = async (e) => { e.preventDefault(); await fetch(url, {method:'POST', body:new FormData(e.target)}); location.reload(); };
        };
        setupF('fUsr', '/api/save_user');
        async function delItem(id, tipo) { 
            if(confirm('¿Eliminar?')) { 
                let fd = new FormData(); fd.append('id', id); 
                await fetch('/api/del_'+tipo, {method:'POST', body:fd}); location.reload(); 
            } 
        }
    </script>"""
    
    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content + scripts, u_data).encode("utf-8")]