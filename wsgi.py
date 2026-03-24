# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# CONFIGURACIÓN
DB_URL = "mysql://root:xHpkRjCgnCeqzkrMpNVYcgCobhMVNRCi@mysql.railway.internal:3306/railway"
JWT_SECRET = "CLAVE_2026"

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

def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""<div style="background:#0b1120; padding:15px 40px; display:flex; justify-content:space-between; border-bottom:1px solid #1e293b;">
            <div style="color:#38bdf8; font-weight:bold;">🛡️ Clínica Santa Mónica</div>
            <div style="color:white;"><b>{user['u']}</b> | <a href="/logout" style="color:#ef4444; text-decoration:none;">Salir</a></div>
        </div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{background:#0f172a; color:white; font-family:sans-serif; margin:0;}}
        .card{{background:#1e293b; padding:30px; border-radius:12px; max-width:800px; margin:50px auto; border:1px solid #334155;}}
        input{{width:100%; padding:10px; margin:10px 0; background:#0f172a; border:1px solid #334155; color:white; border-radius:6px;}}
        .btn{{background:#2563eb; color:white; border:none; padding:12px; width:100%; border-radius:6px; cursor:pointer; font-weight:bold;}}
        table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th, td{{padding:12px; border-bottom:1px solid #334155; text-align:left;}}
    </style>
    <script>
        function toggleAll() {{
            const chks = document.querySelectorAll('input[type="checkbox"]');
            const state = Array.from(chks).every(c => c.checked);
            chks.forEach(c => c.checked = !state);
        }}
    </script>
    </head><body>{nav}<div class="container">{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    u_data = verify_jwt(environ)

    # LOGIN
    if path in ["/", "/login"]:
        content = """<div class='card' style='max-width:350px;'>
            <h2 style='text-align:center; color:#38bdf8;'>Clínica Santa Mónica</h2>
            <form id='fL'>
                <input name='u' placeholder='Usuario' required>
                <input name='p' type='password' placeholder='Contraseña' required>
                <div style='display:flex; justify-content:center; margin:15px 0;'>
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI" data-theme="dark"></div>
                </div>
                <button type='button' onclick='doLogin()' class='btn'>Entrar</button>
            </form>
        </div>
        <script>
            async function doLogin() {
                const c = grecaptcha.getResponse();
                if(!c) { alert("Captcha obligatorio"); return; }
                const res = await fetch('/api/login', { method:'POST', body:new FormData(document.getElementById('fL')) });
                const data = await res.json();
                if(data.ok) location.href='/dashboard'; else alert('Credenciales incorrectas');
            }
        </script>"""
        start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Login", content).encode("utf-8")]

    if path == "/api/login":
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

    # DASHBOARD / USUARIOS
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    if path == "/usuarios" or path == "/dashboard":
        cur.execute("SELECT * FROM usuarios"); usrs = cur.fetchall()
        rows = "".join([f"<tr><td>{u['strNombreUsuario']}</td><td>{u['strCorreo']}</td><td>{u['strEstado']}</td></tr>" for u in usrs])
        content = f"<div class='card'><h2>Gestión de Usuarios</h2><table><thead><tr><th>Usuario</th><th>Correo</th><th>Estado</th></tr></thead><tbody>{rows}</tbody></table></div>"
    
    elif path == "/permisos":
        cur.execute("SELECT * FROM modulos"); mods = cur.fetchall()
        m_rows = "".join([f"<tr><td>{m['strNombreModulo']}</td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td><td><input type='checkbox'></td></tr>" for m in mods])
        content = f"<div class='card'><div style='display:flex; justify-content:space-between;'><h2>Matriz de Permisos</h2><button onclick='toggleAll()' style='background:#1e293b; color:#38bdf8; border:1px solid #38bdf8; cursor:pointer; padding:5px 10px; border-radius:5px;'>Marcar Todo</button></div><table><tr><th>Módulo</th><th>C</th><th>A</th><th>E</th><th>D</th></tr>{m_rows}</table></div>"

    elif path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Path=/; Max-Age=0")]); return [b""]

    cur.close(); conn.close()
    start_response("200 OK", [("Content-Type", "text/html")]); return [render_layout("Sistema", content, u_data).encode("utf-8")]