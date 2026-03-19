# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies 

# =========================================================
# CONFIGURACIÓN
# =========================================================
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
        if not t: return None
        parts = t.split('.')
        p = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode("utf-8"))
        return p if p['exp'] > time.time() else None
    except: return None

def conectar_bd():
    res = urllib.parse.urlparse(DB_URL)
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

def init_db():
    conn = conectar_bd(); cur = conn.cursor(buffered=True)
    cur.execute("CREATE TABLE IF NOT EXISTS perfiles (id INT AUTO_INCREMENT PRIMARY KEY, strNombrePerfil VARCHAR(50), bitAdministrador TINYINT(1))")
    cur.execute("CREATE TABLE IF NOT EXISTS modulos (id INT AUTO_INCREMENT PRIMARY KEY, strNombreModulo VARCHAR(50))")
    cur.execute("CREATE TABLE IF NOT EXISTS permisos_perfil (id INT AUTO_INCREMENT PRIMARY KEY, idPerfil INT, idModulo INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id INT AUTO_INCREMENT PRIMARY KEY, strNombreUsuario VARCHAR(50), idPerfil INT, strPwd VARCHAR(255), idEstadoUsuario INT, strCorreo VARCHAR(150), imgUsuario LONGTEXT)")
    conn.commit(); cur.close(); conn.close()

def render_layout(title, content, user=None):
    nav = ""
    if user:
        nav = f"""<div style="background:#0f4573; color:white; padding:15px; display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; gap:20px;">
                <a href="/dashboard" style="color:white; text-decoration:none; font-weight:bold;">🏠 Inicio</a>
                <a href="/perfiles" style="color:white; text-decoration:none;">Perfiles</a>
                <a href="/modulos" style="color:white; text-decoration:none;">Módulos</a>
                <a href="/permisos" style="color:white; text-decoration:none;">Permisos</a>
                <a href="/usuarios" style="color:white; text-decoration:none;">Usuarios</a>
            </div>
            <div><b>{user['u']}</b> | <a href="/logout" style="color:#ff7675; text-decoration:none;">Salir</a></div>
        </div>"""
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        body{{font-family:sans-serif; background:#f0f2f5; margin:0;}} 
        .card{{background:white; padding:25px; margin:20px auto; max-width:1000px; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,0.1);}}
        table{{width:100%; border-collapse:collapse; margin-top:15px; background:white;}} 
        th,td{{padding:12px; border:1px solid #ddd; text-align:left;}}
        th{{background:#0f4573; color:white;}}
        .btn{{background:#0f4573; color:white; border:none; padding:10px 20px; cursor:pointer; border-radius:4px; font-weight:bold;}}
        input, select{{padding:10px; border:1px solid #ccc; border-radius:4px; margin:5px 0; width:100%; box-sizing:border-box;}}
        .form-grid{{display:grid; grid-template-columns: 1fr 1fr; gap:15px; background:#f9f9f9; padding:20px; border-radius:8px; margin-bottom:20px;}}
    </style></head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    init_db()

    # --- LOGIN Y API LOGIN (SE MANTIENEN IGUAL) ---
    if path in ["/", "/login"]:
        # ... (Código de login anterior igual) ...
        content = """<div class="card" style="max-width:320px; text-align:center; margin-top:80px;">
            <h2 style="color:#0f4573;">Acceso Sistema</h2>
            <form id="fL">
                <input type="text" name="u" placeholder="Usuario" required>
                <input type="password" name="p" placeholder="Contraseña" required>
                <div style="margin:15px 0; display:flex; justify-content:center;">
                    <div class="g-recaptcha" data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>
                </div>
                <button type="button" id="btnIn" class="btn" style="width:100%;">Entrar</button>
            </form><div id="msg" style="color:red; margin-top:10px;"></div></div>
            <script>
                document.getElementById('btnIn').onclick = async () => {
                    const captcha = grecaptcha.getResponse();
                    if(!captcha) { document.getElementById('msg').innerText = "Resuelve el captcha"; return; }
                    const fd = new FormData(document.getElementById('fL'));
                    const res = await fetch('/api/login', {method:'POST', body:fd});
                    const d = await res.json();
                    if(d.ok) window.location.replace('/dashboard');
                    else { document.getElementById('msg').innerText = d.msg; grecaptcha.reset(); }
                };
            </script>"""
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
            return [json.dumps({"ok":True}).encode("utf-8")]
        start_response("200 OK", [("Content-Type", "application/json")]); return [json.dumps({"ok":False, "msg":"Error"}).encode("utf-8")]

    # --- SEGURIDAD ---
    u_data = verify_jwt(environ)
    if not u_data:
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- API GUARDAR USUARIO ---
    if path == "/api/save_usuarios" and method == "POST":
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
        conn = conectar_bd(); cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strCorreo, idEstadoUsuario, imgUsuario) VALUES (%s,%s,%s,%s,1,%s)", 
            (fs.getvalue("u"), hash_password(fs.getvalue("p")), fs.getvalue("pid"), fs.getvalue("e"), fs.getvalue("img")))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # --- VISTA USUARIOS ---
    if path == "/usuarios":
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil=p.id")
        rows = cur.fetchall()
        cur.execute("SELECT id, strNombrePerfil FROM perfiles")
        perfs = cur.fetchall()
        cur.close(); conn.close()

        opt_p = "".join([f"<option value='{x['id']}'>{x['strNombrePerfil']}</option>" for x in perfs])
        
        form = f"""
        <form id='fU' class='form-grid'>
            <div>
                <label>Usuario:</label><input name='u' required>
                <label>Contraseña:</label><input name='p' type='password' required>
            </div>
            <div>
                <label>Email:</label><input name='e' type='email' required>
                <label>Perfil:</label><select name='pid'>{opt_p}</select>
            </div>
            <div style="grid-column: span 2;">
                <label>Foto de Perfil:</label><input type='file' id='fimg' accept='image/*'>
                <button type='submit' class='btn' style="margin-top:10px; width:200px;">Registrar Usuario</button>
            </div>
        </form>"""
        
        tbl = "<table><tr><th>Foto</th><th>Usuario</th><th>Email</th><th>Perfil</th></tr>"
        for r in rows:
            img = r.get('imgUsuario') or 'https://via.placeholder.com/40'
            tbl += f"<tr><td><img src='{img}' width='40' height='40' style='border-radius:50%; object-fit:cover;'></td><td>{r['strNombreUsuario']}</td><td>{r['strCorreo']}</td><td>{r['strNombrePerfil']}</td></tr>"
        tbl += "</table>"
        
        content = f"<div class='card'><h2>Gestión de Usuarios</h2>{form}{tbl}</div>"
        
        script = """<script>
            document.getElementById('fU').onsubmit = async (e) => {
                e.preventDefault();
                const fd = new FormData(e.target);
                const file = document.getElementById('fimg').files[0];
                
                const sendData = async (base64Img) => {
                    if(base64Img) fd.append('img', base64Img);
                    const res = await fetch('/api/save_usuarios', {method:'POST', body:fd});
                    if(res.ok) location.reload();
                };

                if(file) {
                    const reader = new FileReader();
                    reader.onloadend = () => sendData(reader.result);
                    reader.readAsDataURL(file);
                } else {
                    sendData('');
                }
            };
        </script>"""
        
        start_response("200 OK", [("Content-Type", "text/html")]); return [(render_layout("Usuarios", content, u_data) + script).encode("utf-8")]

    # --- REDIRECCIONES / OTROS ---
    if path == "/logout":
        start_response("303 See Other", [("Location", "/login"), ("Set-Cookie", "token=; Max-Age=0")]); return [b""]
    
    # Redirección por defecto si no es usuario (para no romper el flujo)
    start_response("200 OK", [("Content-Type", "text/html")]); 
    return [render_layout("Clínica", "<div class='card'><h3>Cargando...</h3><script>location.href='/usuarios'</script></div>", u_data).encode("utf-8")]