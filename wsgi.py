# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# CONFIGURACIÓN
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_CORPORATIVA_2026"

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
# DISEÑO CORPORATIVO (ESTILO EMPRESA)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        menu_html = ""
        for m_padre in ["Seguridad", "Principal 1", "Principal 2", "prueba"]:
            links = ""
            if m_padre == "Seguridad":
                links += '<a href="/perfiles">Perfil</a><a href="/usuarios">Usuarios</a><a href="/permisos">Permisos</a>'
            menu_html += f'<div class="dropdown"><button class="dropbtn">{m_padre} ▾</button><div class="dropdown-content">{links}</div></div>'
        
        nav = f"""<div class="header">
            <div class="nav-container">
                <div class="brand">🏢 EMPRESA</div>
                <div class="menu-items">{menu_html}<a href="/logout" class="btn-salir">Salir</a></div>
            </div>
        </div>"""
   
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{{{font-family:'Segoe UI', Arial, sans-serif; background:#f0f2f5; color:#334155; margin:0;}}}}
        
        /* HEADER PROFESIONAL */
        .header{{{{background:#2b4592; color:white; height:65px; box-shadow:0 2px 4px rgba(0,0,0,0.1);}}}}
        .nav-container{{{{max-width:1400px; margin:0 auto; display:flex; justify-content:space-between; align-items:center; height:100%; padding:0 20px;}}}}
        .brand{{{{font-weight:bold; font-size:1.4rem; letter-spacing:1px;}}}}
        
        /* MENU DESPLEGABLE */
        .menu-items{{{{display:flex; align-items:center; gap:5px;}}}}
        .dropbtn{{{{background:transparent; color:rgba(255,255,255,0.9); border:none; padding:22px 15px; cursor:pointer; font-size:0.95rem; font-family:inherit;}}}}
        .dropdown{{{{position:relative;}}}}
        .dropdown-content{{{{display:none; position:absolute; background:white; min-width:180px; box-shadow:0 8px 16px rgba(0,0,0,0.1); z-index:1000; border-radius:0 0 8px 8px;}}}}
        .dropdown-content a{{{{color:#334155; padding:12px 16px; text-decoration:none; display:block; font-size:0.9rem;}}}}
        .dropdown-content a:hover{{{{background:#f8fafc; color:#2b4592;}}}}
        .dropdown:hover .dropdown-content{{{{display:block;}}}}
        .dropdown:hover .dropbtn{{{{background:rgba(255,255,255,0.1);}}}}
        .btn-salir{{{{background:#e11d48; color:white; padding:8px 18px; border-radius:6px; text-decoration:none; font-weight:bold; margin-left:15px; font-size:0.85rem;}}}}

        /* CONTENIDO PRINCIPAL */
        .main-content{{{{padding:40px 20px; max-width:1200px; margin:0 auto;}}}}
        .card-white{{{{background:white; border-radius:12px; padding:40px; box-shadow:0 1px 3px rgba(0,0,0,0.1); border:1px solid #e2e8f0; text-align:center;}}}}
        
        /* TABLAS ESTILO GESTIÓN */
        .table-card{{{{background:white; border-radius:8px; border:1px solid #e2e8f0; overflow:hidden;}}}}
        .table-header{{{{padding:20px; border-bottom:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;}}}}
        table{{{{width:100%; border-collapse:collapse;}}}}
        th{{{{background:#f8fafc; text-align:left; color:#64748b; font-size:0.8rem; text-transform:uppercase; padding:15px; border-bottom:1px solid #e2e8f0;}}}}
        td{{{{padding:15px; border-bottom:1px solid #f1f5f9; font-size:0.95rem;}}}}
        .btn-action{{{{color:#2563eb; text-decoration:none; margin-right:10px; font-size:0.85rem; font-weight:600;}}}}
        .btn-delete{{{{color:#ef4444; text-decoration:none; font-size:0.85rem; font-weight:600;}}}}
        
        /* INPUTS */
        input{{{{background:#fff; border:1px solid #cbd5e1; padding:12px; border-radius:8px; width:100%; margin-bottom:15px;}}}}
    </style>
    </head><body>{nav}<div class='main-content'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    u_data = verify_jwt(environ)

    # LOGIN ESTILO CORPORATIVO
    if path in ["/", "/login"]:
        content = """<div style='margin-top:50px; display:flex; justify-content:center;'>
            <div class='card-white' style='width:400px;'>
                <h2 style='color:#1e293b; margin-top:0;'>Bienvenido</h2>
                <p style='color:#64748b; margin-bottom:30px;'>Inicia sesión en tu cuenta de Empresa</p>
                <form id='fL'>
                    <input name='u' placeholder='Usuario' required>
                    <input name='p' type='password' placeholder='Contraseña' required>
                    <div style='display:flex; justify-content:center; margin:20px 0;'>
                        <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                    </div>
                    <button type='button' onclick='doLogin()' style='background:#2b4592; color:white; border:none; padding:15px; width:100%; border-radius:8px; cursor:pointer; font-weight:bold;'>Ingresar</button>
                </form>
            </div>
        </div>
        <script>
            async function doLogin() {
                const res = await fetch('/api/login', { method:'POST', body:new FormData(document.getElementById('fL')) });
                const data = await res.json();
                if(data.ok) location.href='/dashboard'; else alert('Acceso denegado');
            }
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login":
        # ... (Lógica de login igual a la anterior)
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

    # VISTAS INTERNAS ESTILO "EMPRESA"
    if path == "/dashboard":
        content = f"""<div class='card-white' style='max-width:700px; margin:0 auto;'>
            <div style='background:#f1f5f9; width:60px; height:60px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px;'>👤</div>
            <h1 style='margin:0;'>Bienvenido al Sistema</h1>
            <h2 style='color:#2b4592;'>{u_data['u']} - <span style='color:#64748b; font-size:1rem;'>ADMINISTRADOR</span></h2>
            <p style='color:#64748b;'>Selecciona un módulo en el menú superior para comenzar.</p>
        </div>"""
    
    elif path == "/perfiles":
        content = """<div class='table-card'>
            <div class='table-header'>
                <h3 style='margin:0;'>Gestión de Perfiles</h3>
                <button style='background:#2b4592; color:white; border:none; padding:10px 20px; border-radius:6px; cursor:pointer;'>+ Nuevo Perfil</button>
            </div>
            <table><thead><tr><th>Nombre del Perfil</th><th style='text-align:right;'>Acciones</th></tr></thead>
            <tbody>
                <tr><td>Edelion</td><td style='text-align:right;'><a href='#' class='btn-action'>Editar</a><a href='#' class='btn-delete'>Eliminar</a></td></tr>
                <tr><td>VENTAS</td><td style='text-align:right;'><a href='#' class='btn-action'>Editar</a><a href='#' class='btn-delete'>Eliminar</a></td></tr>
                <tr><td>ADMINISTRADOR</td><td style='text-align:right;'><a href='#' class='btn-action'>Editar</a><a href='#' class='btn-delete'>Eliminar</a></td></tr>
            </tbody></table>
        </div>"""
    
    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]

    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]