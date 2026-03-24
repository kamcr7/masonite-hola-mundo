# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# CONFIGURACIÓN
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
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
        if not t: return None
        p = json.loads(base64.urlsafe_b64decode(t.split('.')[1] + "==").decode("utf-8"))
        return p if p['exp'] > time.time() else None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

# =========================================================
# MAQUETACIÓN CON DISEÑO ORIGINAL
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        menu_html = ""
        # Menús desplegables con el diseño original de tus capturas
        for m_padre in ["Seguridad", "Principal 1", "Principal 2"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">👤 Perfiles</a><a href="/modulos">📦 Módulos</a><a href="/permisos">🔐 Permisos</a><a href="/usuarios">👥 Usuarios</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        
        nav = f"""<div class="top-nav">
            <div class="nav-left"><span class="logo">🛡️ Clínica Santa Mónica</span><a href="/dashboard" class="nav-link">Inicio</a>{menu_html}</div>
            <div class="nav-right"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none; margin-left:10px;">Salir</a></div>
        </div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{{{font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#0f172a; color:#f8fafc; margin:0; overflow-x:hidden;}}}}
        
        /* NAVBAR */
        .top-nav{{{{background:#0b1120; padding:0 40px; height:60px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; position:sticky; top:0; z-index:100;}}}}
        .nav-left{{{{display:flex; gap:15px; align-items:center;}}}}
        .logo{{{{font-weight:bold; color:#38bdf8; font-size:1.1rem; margin-right:20px;}}}}
        .nav-link{{{{color:#94a3b8; text-decoration:none; font-size:0.9rem; padding:20px 10px; transition:0.3s;}}}}
        .nav-link:hover{{{{color:#38bdf8;}}}}
        
        /* DROPDOWNS */
        .dropbtn{{{{background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.9rem; padding:20px 10px; font-family:inherit;}}}}
        .dropdown{{{{position:relative; display:inline-block;}}}}
        .dropdown-content{{{{display:none; position:absolute; background:#1e293b; min-width:200px; border-radius:8px; border:1px solid #334155; box-shadow:0 10px 15px -3px rgba(0,0,0,0.5); z-index:1000; overflow:hidden;}}}}
        .dropdown-content a{{{{color:#e2e8f0; padding:12px 16px; text-decoration:none; display:block; font-size:0.85rem; transition:0.2s;}}}}
        .dropdown-content a:hover{{{{background:#334155; color:#38bdf8;}}}}
        .dropdown:hover .dropdown-content{{{{display:block;}}}}
        .dropdown:hover .dropbtn{{{{color:#38bdf8;}}}}

        /* CONTENEDORES */
        .container{{{{padding:30px 40px; max-width:1200px; margin:0 auto;}}}}
        .card{{{{background:#1e293b; border-radius:12px; padding:25px; border:1px solid #334155; margin-bottom:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.2);}}}}
        
        /* TABLAS */
        table{{{{width:100%; border-collapse:collapse; margin-top:20px; background:#1e293b;}}}}
        th{{{{text-align:left; color:#94a3b8; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:15px; border-bottom:2px solid #334155;}}}}
        td{{{{padding:14px 15px; border-bottom:1px solid #334155; font-size:0.9rem; color:#e2e8f0;}}}}
        tr:hover td{{{{background:#1a2234;}}}}

        /* BOTONES */
        .btn-blue{{{{background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600; transition:0.2s;}}}}
        .btn-blue:hover{{{{background:#1d4ed8; transform:translateY(-1px);}}}}
        .btn-red{{{{background:#ef4444; color:white; border:none; padding:6px 10px; border-radius:6px; cursor:pointer; font-size:0.8rem;}}}}
        
        /* INPUTS */
        input, select{{{{background:#0f172a; border:1px solid #334155; color:white; padding:12px; border-radius:8px; width:100%; margin-bottom:15px; font-size:0.9rem;}}}}
        input:focus{{{{border-color:#38bdf8; outline:none;}}}}
    </style>
    <script>
        function toggleAll() {{
            const checks = document.querySelectorAll('input[type="checkbox"]');
            const state = Array.from(checks).every(c => c.checked);
            checks.forEach(c => c.checked = !state);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

# =========================================================
# CONTROLADOR WSGI
# =========================================================
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)

    # VISTA DE LOGIN
    if path in ["/", "/login"] and method == "GET":
        content = """<div style='display:flex; justify-content:center; align-items:center; min-height:80vh;'>
            <div class='card' style='width:380px; text-align:center;'>
                <h2 style="color:#38bdf8; margin-bottom:10px;">Clínica Santa Mónica</h2>
                <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:25px;">Ingresa tus credenciales para continuar</p>
                <form id='fL'>
                    <input name='u' placeholder='Usuario' required>
                    <input name='p' type='password' placeholder='Contraseña' required>
                    <div style="margin:20px 0; display:flex; justify-content:center;">
                        <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div>
                    </div>
                    <button type='button' onclick='doLogin()' class='btn-blue' style='width:100%; padding:14px;'>Entrar al Sistema</button>
                </form>
            </div>
        </div>
        <script>
            async function doLogin() {
                const c = grecaptcha.getResponse(); 
                if(!c) { alert("Por favor, completa el captcha"); return; }
                const res = await fetch('/api/login', { method:'POST', body:new FormData(document.getElementById('fL')) });
                const data = await res.json(); 
                if(data.ok) location.href='/dashboard'; 
                else alert('Usuario o contraseña incorrectos');
            }
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Acceso", content).encode("utf-8")]

    # API DE LOGIN
    if path == "/api/login" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        u, p = fs.getvalue("u"), hash_password(fs.getvalue("p", ""))
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s", (u, p))
        user = cur.fetchone(); cur.close(); conn.close()
        if user:
            tk = jwt_encode({"u": u, "exp": time.time()+3600})
            start_response("200 OK", [("Content-Type", "application/json"), ("Set-Cookie", f"token={tk}; Path=/; HttpOnly; SameSite=Lax")])
            return [b'{"ok":true}']
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":false}']

    # SEGURIDAD
    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # VISTAS INTERNAS
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)

    if path == "/usuarios":
        cur.execute("SELECT * FROM usuarios"); usrs = cur.fetchall()
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td><span style='color:#4ade80;'>●</span> {u['strEstado']}</td><td><button class='btn-red'>Eliminar</button></td></tr>" for u in usrs])
        content = f"""<div class='card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2 style='margin:0;'>Gestión de Usuarios</h2>
                <button class='btn-blue'>+ Nuevo Usuario</button>
            </div>
            <table><thead><tr><th>Usuario</th><th>Correo</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows}</tbody></table>
        </div>"""

    elif path == "/permisos":
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        m_rows = "".join([f"<tr><td><b>{m['strNombreModulo']}</b></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"""<div class='card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2 style='margin:0;'>Matriz de Permisos</h2>
                <button onclick='toggleAll()' class='btn-blue' style='background:#334155;'>Invertir Selección</button>
            </div>
            <table><thead><tr><th>Módulo</th><th>Crear (C)</th><th>Actualizar (A)</th><th>Eliminar (E)</th><th>Detalle (D)</th></tr></thead><tbody>{m_rows}</tbody></table>
            <div style='margin-top:20px; text-align:right;'><button class='btn-blue'>Guardar Cambios</button></div>
        </div>"""

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]
    
    else: # DASHBOARD
        content = f"""<div class='card' style='text-align:center; padding:50px;'>
            <h1 style='color:#38bdf8;'>Panel de Control</h1>
            <p style='color:#94a3b8; font-size:1.1rem;'>Bienvenido de nuevo, <b>{u_data['u']}</b>. Selecciona una opción en el menú superior.</p>
        </div>"""

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]