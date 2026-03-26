# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, mysql.connector, os, base64
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
    # Agregamos un timeout para que no se quede colgado eternamente
    return mysql.connector.connect(
        host=res.hostname, port=res.port, 
        user=res.username, password=res.password, 
        database=res.path[1:], charset='utf8mb4',
        connect_timeout=5
    )

def render_layout(title, content, user=None):
    nav = ""
    if user:
        try:
            conn_nav = conectar_bd()
            cur_nav = conn_nav.cursor(dictionary=True)
            cur_nav.execute("SELECT * FROM modulos")
            all_mods = cur_nav.fetchall()
            cur_nav.close(); conn_nav.close()
            
            def get_links(padre):
                return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in all_mods if m.get('strMenuPadre') == padre])
            
            nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left">
            <span class="logo" style="color:#10b981; font-weight:bold; font-size:1.2rem; margin-right:20px;">🏥 Clinica</span>
            <a href="/usuarios" class="nav-link">Inicio</a>
            <div class="dropdown">
                <button class="dropbtn">Seguridad ▾</button>
                <div class="dropdown-content">
                    <a href="/perfiles">👤 Perfiles</a>
                    <a href="/modulos">📦 Modulos</a>
                    <a href="/usuarios">👥 Usuarios</a>
                    <a href="/permisos">🔐 Permisos</a>
                </div>
            </div>
            <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1")}</div></div>
            <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2")}</div></div>
            </div><div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
        except Exception as e:
            nav = f"<div style='background:red; color:white; padding:10px;'>Error en Menú: {str(e)}</div>"

    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
        body {{ font-family: sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
        /* ... El resto de tu CSS igual ... */
    </style>
    <body>{nav}<div class='container'>{content}</div></body></html>"""
    
def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)
    
    # 1. RUTAS PÚBLICAS
    if path == "/login":
        # Tu lógica de login aquí
        pass

    # 2. PROTECCIÓN DE SESIÓN
    if not u_data:
        start_response("303 See Other", [("Location", "/login")])
        return [b""]

    # Variables de control para la base de datos
    conn = None
    cur = None
    content = ""
    
    try:
        # --- API: GET PERMISOS ---
        if path == "/api/get_permisos":
            from urllib.parse import parse_qs
            params = parse_qs(environ.get('QUERY_STRING', ''))
            idp = params.get('idp', [None])[0]
            conn = conectar_bd(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT idModulo as idm, can_view as v, can_add as a, can_edit as e, can_delete as d FROM perfil_modulo WHERE idPerfil = %s", (idp,))
            res = json.dumps({"ok": True, "perms": cur.fetchall()}).encode('utf-8')
            start_response("200 OK", [("Content-Type", "application/json")])
            return [res]
            
        # --- API: CRUD PRINCIPAL (POST) ---
        if path == "/api/crud" and method == "POST":
            length = int(environ.get("CONTENT_LENGTH", 0))
            p = json.loads(environ["wsgi.input"].read(length).decode("utf-8"))
            conn = conectar_bd(); cur = conn.cursor()
            
            if p['action'] == 'delete': 
                if p['table'] in ['usuarios', 'perfiles', 'modulos', 'perfil_modulo']:
                    cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
            
            elif p['action'] == 'save':
                if p['table'] == 'usuarios':
                    u_nom = p['data']['u'].strip()
                    cur.execute("SELECT id FROM usuarios WHERE LOWER(strNombreUsuario) = LOWER(%s)", (u_nom,))
                    if cur.fetchone(): raise Exception("El nombre de usuario ya existe")
                    cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,%s)",
                               (u_nom, hash_password(p['data']['p']), p['data']['idp'], p['data']['st']))
                elif p['table'] == 'perfiles':
                    nombre = p['data']['n'].strip()
                    cur.execute("SELECT id FROM perfiles WHERE LOWER(strNombrePerfil) = LOWER(%s)", (nombre,))
                    if cur.fetchone(): raise Exception("Ese perfil ya existe")
                    cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (nombre,))
                elif p['table'] == 'modulos':
                    m_nom = p['data']['n'].strip()
                    cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)",
                               (m_nom, p['data'].get('r', '#'), p['data']['p']))
                elif p['table'] == 'permisos':
                    id_p = p['data']['idp']
                    cur.execute("DELETE FROM perfil_modulo WHERE idPerfil = %s", (id_p,))
                    for per in p['data']['perms']:
                        v, a, e, d = int(per['v']), int(per['a']), int(per['e']), int(per['d'])
                        if v or a or e or d:
                            cur.execute("INSERT INTO perfil_modulo (idPerfil, idModulo, can_view, can_add, can_edit, can_delete) VALUES (%s,%s,%s,%s,%s,%s)", 
                                       (id_p, per['idm'], v, a, e, d))

            elif p['action'] == 'update':
                if p['table'] == 'usuarios':
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s WHERE id=%s",
                               (p['data']['u'].strip(), p['data']['idp'], p['data']['st'], p['id']))
                elif p['table'] == 'perfiles':
                    cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (p['data']['n'].strip(), p['id']))
                elif p['table'] == 'modulos':
                    cur.execute("UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s",
                               (p['data']['n'].strip(), p['data']['r'], p['data']['p'], p['id']))

            conn.commit()
            start_response("200 OK", [("Content-Type", "application/json")])
            return [json.dumps({"ok": True}).encode("utf-8")]

        # --- RENDERIZADO DE PANTALLAS (GET) ---
        conn = conectar_bd()
        cur = conn.cursor(dictionary=True)

        if path == "/usuarios":
            cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
            usuarios = cur.fetchall()
            rows = "".join([f"""<tr class='u-row'>
                <td><img src='https://ui-avatars.com/api/?name={u['strNombreUsuario']}&background=random' class='avatar-table'></td>
                <td><b class='u-name'>{u['strNombreUsuario']}</b></td>
                <td>{u['strNombrePerfil']}</td>
                <td><span class='status-pill {'active' if u['strEstado']=='Activo' else 'inactive'}'>{u['strEstado']}</span></td>
                <td>
                    <button class='btn-blue' onclick='preEdit({u['id']}, {{u:\"{u['strNombreUsuario']}\", idp:{u['idPerfil']}, st:\"{u['strEstado']}\"}}, \"mEdit\")'>Editar</button>
                    <button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</button>
                </td>
            </tr>""" for u in usuarios])

            cur.execute("SELECT * FROM perfiles")
            p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])
            content = f" <div class='card'> <h2>👥 Gestión de Usuarios</h2> ... </div> " # (He abreviado el HTML por espacio, pero mantén el tuyo dentro)

        elif path == "/perfiles":
            cur.execute("SELECT * FROM perfiles ORDER BY id ASC")
            perfiles = cur.fetchall()
            rows = ""
            for i, p in enumerate(perfiles, 1):
                nombre_p = p['strNombrePerfil'].replace('"', '&quot;')
                rows += f"""<tr class='p-row'><td>{i}</td><td><b class='p-name'>{nombre_p}</b></td><td>...</td></tr>"""
            content = f" <div class='card'> ... </div> "

        elif path == "/modulos":
            cur.execute("SELECT * FROM modulos ORDER BY id ASC")
            rows = "".join([f"""<tr class='m-row'><td>{m['strNombreModulo']}</td>...</tr>""" for m in cur.fetchall()])
            content = f" <div class='card'> ... </div> "

        elif path == "/permisos":
            cur.execute("SELECT id, strNombrePerfil FROM perfiles")
            perfiles = cur.fetchall()
            p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfiles])
            # ... resto de la lógica de permisos ...
            content = f" <div class='card'> ... </div> "

        # JAVASCRIPT GLOBAL
        content += """ <script> ... </script> """

        # RENDERIZADO FINAL
        final_body = render_layout("Clínica 2026", content, u_data)
        start_response("200 OK", [("Content-Type", "text/html")])
        return [final_body.encode("utf-8")]

    except Exception as e: 
        print(f"Error detectado: {str(e)}") 
        start_response("500 Internal Server Error", [("Content-Type", "text/html")])
        return [f"<h1>Error en el servidor</h1><p>{str(e)}</p>".encode()]

    finally: 
        if 'cur' in locals() and cur: cur.close()
        if 'conn' in locals() and conn: conn.close()