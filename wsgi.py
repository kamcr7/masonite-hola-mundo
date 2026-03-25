# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
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
    return mysql.connector.connect(host=res.hostname, port=res.port, user=res.username, password=res.password, database=res.path[1:], charset='utf8mb4')

# =========================================================
# DISEÑO MODIFICADO: CON MENÚ DINÁMICO SEGÚN PERMISOS
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        # Conectamos para obtener permisos del perfil actual
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        idp = user.get('idPerfil') # El idPerfil debe venir en el JWT

        # 1. Obtener módulos de la BD que el perfil tiene permitido VER
        cur.execute("""
            SELECT m.* FROM modulos m 
            INNER JOIN perfil_modulo pm ON m.id = pm.idModulo 
            WHERE pm.idPerfil = %s AND pm.can_view = 1
        """, (idp,))
        all_mods = cur.fetchall()

        # 2. Obtener permisos para módulos fijos (IDs negativos)
        cur.execute("SELECT idModulo FROM perfil_modulo WHERE idPerfil = %s AND can_view = 1 AND idModulo < 0", (idp,))
        fijos = [r['idModulo'] for r in cur.fetchall()]
        
        cur.close(); conn.close()

        # Función auxiliar para links de módulos dinámicos
        def get_links(padre):
            links = [f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in all_mods if m['strMenuPadre'] == padre]
            return "".join(links)

        # Construcción dinámica del menú de Seguridad
        seg_links = ""
        if -1 in fijos: seg_links += '<a href="/perfiles">👤 Perfiles</a>'
        if -2 in fijos: seg_links += '<a href="/modulos">📦 Modulos</a>'
        if -3 in fijos: seg_links += '<a href="/usuarios">👥 Usuarios</a>'
        if -4 in fijos: seg_links += '<a href="/permisos">🔐 Permisos</a>'
        
        # Solo mostrar el dropdown de Seguridad si tiene al menos un acceso
        menu_seguridad = f"""<div class="dropdown">
            <button class="dropbtn">Seguridad ▾</button>
            <div class="dropdown-content">{seg_links}</div>
        </div>""" if seg_links else ""

        # Solo mostrar Principal 1 y 2 si tienen links hijos
        links_p1 = get_links("Principal 1")
        links_p2 = get_links("Principal 2")
        
        menu_p1 = f'<div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{links_p1}</div></div>' if links_p1 else ""
        menu_p2 = f'<div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{links_p2}</div></div>' if links_p2 else ""

        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left">
        <span class="logo" style="color:#10b981; font-weight:bold; font-size:1.2rem; margin-right:20px;">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        {menu_seguridad}
        {menu_p1}
        {menu_p2}
        </div><div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
    
    return f"""<html><head><meta charset='utf-8'><title>{title}</title>
    <style>
        :root {{ --bg: #0b1120; --card: #1e293b; --emerald: #10b981; --border: #334155; --text: #f8fafc; }}
        body {{ font-family: sans-serif; background:var(--bg); color:var(--text); margin:0; }}
        .top-nav {{ background:#070b14; height:60px; border-bottom:1px solid var(--border); display:flex; align-items:center; }}
        .nav-container {{ width:100%; max-width:1200px; margin:0 auto; display:flex; justify-content:space-between; padding:0 20px; }}
        .nav-link {{ color:#94a3b8; text-decoration:none; padding:10px; font-size:14px; }}
        .dropdown {{ position:relative; display:inline-block; }}
        .dropdown-content {{ display:none; position:absolute; background:var(--card); min-width:180px; border:1px solid var(--border); border-radius:12px; z-index:100; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }}
        .dropdown-content a {{ color:white; padding:12px; text-decoration:none; display:block; border-bottom: 1px solid #334155; font-size:14px; }}
        .dropdown-content a:hover {{ background: #2d3748; }}
        .dropdown:hover .dropdown-content {{ display:block; }}
        .dropbtn {{ background:transparent; color:#94a3b8; border:none; padding:15px; cursor:pointer; font-size:14px; }}
        .container {{ padding:40px; max-width:1200px; margin:0 auto; }}
        .card {{ background:var(--card); padding:30px; border-radius:16px; border:1px solid var(--border); }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; background:#0f172a; border-radius:12px; overflow:hidden; }}
        th {{ background:#1e293b; color:#94a3b8; font-size:12px; text-transform:uppercase; padding:15px; text-align:left; }}
        td {{ padding:15px; border-bottom:1px solid var(--border); font-size:14px; }}
        .avatar-table {{ width:45px; height:45px; border-radius:50%; object-fit: cover; background:#334155; border: 1px solid var(--border); }}
        .status-pill {{ padding:4px 12px; border-radius:20px; font-size:11px; font-weight:bold; }}
        .active {{ background:#065f46; color:#34d399; }}
        .inactive {{ background:#7f1d1d; color:#f87171; }}
        input, select {{ background:#0f172a; border:1px solid var(--border); color:white; padding:12px; width:100%; margin-bottom:15px; border-radius:8px; }}
        .btn-emerald {{ background:var(--emerald); color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%; transition: 0.3s; }}
        .btn-emerald:hover {{ background: #059669; }}
        .btn-blue {{ color:#3b82f6; background:none; border:none; cursor:pointer; font-weight:bold; }}
        .btn-red {{ color:#ef4444; background:none; border:none; cursor:pointer; font-weight:bold; }}
        .modal {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:1000; }}
        .modal-content {{ background:var(--card); width:500px; margin:5% auto; padding:35px; border-radius:20px; border: 1px solid var(--border); position:relative; }}
        .grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:15px; }}
        .close-x {{ position:absolute; top:20px; right:25px; color:#94a3b8; cursor:pointer; font-size:24px; }}
        .user-pill {{ color:var(--emerald); border:1px solid var(--border); padding:6px 16px; border-radius:25px; margin-right:15px; font-size:13px; font-weight:bold; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 18px; border-radius:8px; font-size:13px; font-weight:bold; }}
        
        /* Paginador */
        .paginador-ui {{ display:flex; justify-content:center; align-items:center; gap:15px; margin-top:15px; padding-top:15px; border-top:1px solid var(--border); }}
    </style>
    <script>
        function openM(id) {{ document.getElementById(id).style.display='block'; }}
        function closeM(id) {{ document.getElementById(id).style.display='none'; }}
        async function runCrud(action, table, id, data={{}}) {{
            const res = await fetch('/api/crud', {{ method:'POST', body:JSON.stringify({{action, table, id, data}}) }});
            const j = await res.json();
            if(j.ok) location.reload(); 
            else alert("Error: " + (j.error || "Desconocido"));
        }}
        function preEdit(id, fields, mId='mEdit') {{
            for(let k in fields) {{ let el = document.getElementById('ed_'+k); if(el) el.value = fields[k]; }}
            document.getElementById('ed_id').value = id;
            openM(mId);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/"); method = environ.get("REQUEST_METHOD", "GET")
    
    # 1. Intentar conectar a la base de datos
    try:
        conn = conectar_bd()
        cur = conn.cursor(dictionary=True)

        # =========================================================
        # --- BLOQUE DE AUTO-REPARACIÓN DE PERMISOS ---
        # =========================================================
        try:
            # Creamos la tabla si Railway la borró o no existe
            cur.execute("""
                CREATE TABLE IF NOT EXISTS perfil_modulo (
                    idPerfil INT, idModulo INT,
                    can_view TINYINT(1) DEFAULT 0, can_add TINYINT(1) DEFAULT 0,
                    can_edit TINYINT(1) DEFAULT 0, can_delete TINYINT(1) DEFAULT 0,
                    PRIMARY KEY (idPerfil, idModulo)
                )
            """)
            
            # Verificamos si el Admin (Perfil 1) ya tiene permisos
            cur.execute("SELECT COUNT(*) as total FROM perfil_modulo WHERE idPerfil = 1")
            if cur.fetchone()['total'] == 0:
                # Insertar permisos de seguridad base (-1 al -4)
                for m_id in [-1, -2, -3, -4]:
                    cur.execute("INSERT IGNORE INTO perfil_modulo VALUES (1, %s, 1, 1, 1, 1)", (m_id,))
                
                # Darle permiso al admin en todos los módulos dinámicos existentes
                cur.execute("""
                    INSERT IGNORE INTO perfil_modulo (idPerfil, idModulo, can_view, can_add, can_edit, can_delete) 
                    SELECT 1, id, 1, 1, 1, 1 FROM modulos
                """)
                conn.commit()
        except Exception as e_repair:
            print(f"Aviso: Fallo en auto-reparación: {e_repair}")
        # =========================================================

    except Exception as e_conn:
        start_response("500 Error", [("Content-Type", "text/plain")])
        return [f"Error crítico de conexión: {e_conn}".encode()]

    # 2. Verificar usuario (JWT)
    u_data = verify_jwt(environ)
    content = ""
    # 1. Inicializamos en None para evitar errores de "local variable referenced before assignment"
    conn = None
    cur = None

# --- API GET PERMISOS ---
    if path == "/api/get_permisos":
        import cgi
        qs = environ.get('QUERY_STRING', '')
        params = cgi.parse_qs(qs)
        idp = params.get('idp', [''])[0]
        
        res = b'{"ok":false}'
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""SELECT idModulo as idm, can_view as v, can_add as a, 
                           can_edit as e, can_delete as d FROM perfil_modulo 
                           WHERE idPerfil = %s""", (idp,))
            perms = cur.fetchall()
            res = json.dumps({"ok": True, "perms": perms}).encode()
        except Exception as e:
            res = json.dumps({"ok": False, "error": str(e)}).encode()
        finally:
            cur.close(); conn.close()
        
        start_response("200 OK", [("Content-Type", "application/json")]); return [res]

    # --- API CRUD PRINCIPAL  ---
    if path == "/api/crud" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete': 
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
                    cur.execute("SELECT id FROM modulos WHERE LOWER(strNombreModulo) = LOWER(%s)", (m_nom,))
                    if cur.fetchone(): raise Exception("El módulo ya existe")
                    cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)",
                               (m_nom, p['data']['r'], p['data']['p']))
                
                # --- NUEVA LÓGICA PARA GUARDAR MATRIZ DE PERMISOS ---
                elif p['table'] == 'permisos':
                    id_p = p['data']['idp']
                    # Limpiamos permisos anteriores
                    cur.execute("DELETE FROM perfil_modulo WHERE idPerfil = %s", (id_p,))
                    # Insertamos la nueva matriz enviada desde el JS
                    for per in p['data']['perms']:
                        # Solo insertamos si el módulo tiene al menos un permiso marcado
                        if per['v'] or per['a'] or per['e'] or per['d']:
                            cur.execute("""INSERT INTO perfil_modulo 
                                (idPerfil, idModulo, can_view, can_add, can_edit, can_delete) 
                                VALUES (%s, %s, %s, %s, %s, %s)""", 
                                (id_p, per['idm'], per['v'], per['a'], per['e'], per['d']))

            elif p['action'] == 'update':
                if p['table'] == 'usuarios':
                    u_nom = p['data']['u'].strip()
                    cur.execute("SELECT id FROM usuarios WHERE LOWER(strNombreUsuario) = LOWER(%s) AND id != %s", (u_nom, p['id']))
                    if cur.fetchone(): raise Exception("Ya existe otro usuario con ese nombre")
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s WHERE id=%s",
                               (u_nom, p['data']['idp'], p['data']['st'], p['id']))
                
                elif p['table'] == 'perfiles':
                    nombre = p['data']['n'].strip()
                    cur.execute("SELECT id FROM perfiles WHERE LOWER(strNombrePerfil) = LOWER(%s) AND id != %s", (nombre, p['id']))
                    if cur.fetchone(): raise Exception("Ya existe otro perfil con ese nombre")
                    cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (nombre, p['id']))
                
                elif p['table'] == 'modulos':
                    m_nom = p['data']['n'].strip()
                    cur.execute("SELECT id FROM modulos WHERE LOWER(strNombreModulo) = LOWER(%s) AND id != %s", (m_nom, p['id']))
                    if cur.fetchone(): raise Exception("Ya existe otro módulo con ese nombre")
                    cur.execute("UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s",
                               (m_nom, p['data']['r'], p['data']['p'], p['id']))
            
            conn.commit(); res = b'{"ok":true}'
        except Exception as e: 
            if conn: conn.rollback()
            res = json.dumps({"ok":False, "error":str(e)}).encode()
        finally:
            if cur: cur.close()
            if conn: conn.close()
        
        start_response("200 OK", [("Content-Type", "application/json")]); return [res]
        
    # --- PROTECCIÓN DE SESIÓN ---
    if not u_data and path != "/login":
        start_response("303 See Other", [("Location", "/login")]); return [b""]

    # --- CONEXIÓN PARA RENDERIZADO DE PANTALLAS ---
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        
 # ==========================================
    # --- PANTALLA USUARIOS ---
    # ==========================================
    if path == "/usuarios":
        # VALIDACIÓN
        cur.execute("SELECT can_view, can_add, can_edit, can_delete FROM perfil_modulo WHERE idPerfil = %s AND idModulo = -3", (u_data['idPerfil'],))
        p_act = cur.fetchone()
        if not p_act or not p_act['can_view']:
            start_response("303 See Other", [("Location", "/dashboard")]); return [b""]

        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        usuarios = cur.fetchall()
        
        rows = ""
        for u in usuarios:
            # Botones condicionales según p_act
            btn_e = f"<button class='btn-blue' onclick='preEdit({u['id']}, {{u:\"{u['strNombreUsuario']}\", idp:{u['idPerfil']}, st:\"{u['strEstado']}\"}}, \"mEdit\")'>Editar</button>" if p_act['can_edit'] else ""
            btn_d = f"<button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</button>" if p_act['can_delete'] else ""
            
            rows += f"""<tr class='u-row'>
                <td><img src='https://ui-avatars.com/api/?name={u['strNombreUsuario']}&background=random' class='avatar-table'></td>
                <td><b class='u-name'>{u['strNombreUsuario']}</b></td>
                <td>{u['strNombrePerfil']}</td>
                <td><span class='status-pill {'active' if u['strEstado']=='Activo' else 'inactive'}'>{u['strEstado']}</span></td>
                <td>{btn_e} {btn_d}</td>
            </tr>"""

        cur.execute("SELECT * FROM perfiles")
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])

        btn_nuevo = f"<button class='btn-emerald' style='width:auto' onclick=\"openM('mNew')\">+ NUEVO USUARIO</button>" if p_act['can_add'] else "<span></span>"

        content = f"""
        <div class='card'>
            <h2>👥 Gestión de Usuarios</h2>
            <div style='display:flex; justify-content:space-between; margin-bottom:15px; align-items:center;'>
                {btn_nuevo}
                <input type="text" id="txtBusca" onkeyup="paginaActual=1; filtrar('.u-row', '.u-name');" placeholder="🔍 Buscar..." style="width:200px; margin:0;">
            </div>
            <table>
                <thead><tr><th>IMG</th><th>USUARIO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <div class="paginador-ui">
                <button class="btn-blue" onclick="cambiarPagina(-1, '.u-row')">❮</button>
                <span id="infoPagina"></span>
                <button class="btn-blue" onclick="cambiarPagina(1, '.u-row')">❯</button>
            </div>
        </div>
        <div id='mNew' class='modal'><div class='modal-content'>
            <span class='close-x' onclick="closeM('mNew')">&times;</span>
            <h3>Nuevo Usuario</h3>
            <div class='grid-2'>
                <div><label>Nombre</label><input id='un' maxlength="15"></div>
                <div><label>Pass (5-8 carac.)</label><input id='up' type='password' maxlength="8"></div>
                <div><label>Correo (@gmail.com)</label><input id='uc' type='email'></div>
                <div><label>Teléfono (10 dig)</label><input id='ut' maxlength="10"></div>
                <div><label>Perfil</label><select id='un_idp'>{p_opts}</select></div>
                <div><label>Estado</label><select id='un_st'><option>Activo</option><option>Inactivo</option></select></div>
            </div>
            <button class='btn-emerald' onclick="validateAndSave()">GUARDAR USUARIO</button>
        </div></div>
        <div id='mEdit' class='modal'><div class='modal-content'>
            <span class='close-x' onclick="closeM('mEdit')">&times;</span>
            <h3>Editar Usuario</h3>
            <input type='hidden' id='ed_id'>
            <div class='grid-2'>
                <div><label>Usuario</label><input id='ed_u'></div>
                <div><label>Perfil</label><select id='ed_idp'>{p_opts}</select></div>
                <div><label>Estado</label><select id='ed_st'><option>Activo</option><option>Inactivo</option></select></div>
            </div>
            <button class='btn-emerald' onclick="updateUser()">ACTUALIZAR</button>
        </div></div>
        """

    # ==========================================
    # --- PANTALLA PERFILES ---
    # ==========================================
    elif path == "/perfiles":
        cur.execute("SELECT can_view, can_add, can_edit, can_delete FROM perfil_modulo WHERE idPerfil = %s AND idModulo = -1", (u_data['idPerfil'],))
        p_act = cur.fetchone()
        if not p_act or not p_act['can_view']:
            start_response("303 See Other", [("Location", "/dashboard")]); return [b""]

        cur.execute("SELECT * FROM perfiles ORDER BY id ASC")
        perfiles = cur.fetchall()
        rows = ""
        for i, p in enumerate(perfiles, 1):
            btn_e = f"<button class='btn-blue' onclick='preEdit({p['id']}, {{n:\"{p['strNombrePerfil']}\"}}, \"mEditP\")'>Editar</button>" if p_act['can_edit'] else ""
            btn_d = f"<button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button>" if p_act['can_delete'] else ""
            
            rows += f"""<tr class='p-row'>
                <td>{i}</td>
                <td><b class='p-name'>{p['strNombrePerfil']}</b></td>
                <td>{btn_e} {btn_d}</td>
            </tr>"""
            
        btn_nuevo = f"<button class='btn-emerald' style='width:auto' onclick=\"openM('mNewP')\">+ NUEVO PERFIL</button>" if p_act['can_add'] else ""

        content = f"""
        <div class='card'>
            <h2>👤 Gestión de Perfiles</h2>
            <div style='display:flex; justify-content:space-between; margin-bottom:15px;'>
                {btn_nuevo}
                <input type="text" id="txtBusca" onkeyup="paginaActual=1; filtrar('.p-row', '.p-name');" placeholder="🔍 Buscar...">
            </div>
            <table><thead><tr><th>#</th><th>NOMBRE</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table>
            <div class="paginador-ui">
                <button class="btn-blue" onclick="cambiarPagina(-1, '.p-row')">❮</button>
                <span id="infoPagina"></span>
                <button class="btn-blue" onclick="cambiarPagina(1, '.p-row')">❯</button>
            </div>
        </div>
        <div id='mNewP' class='modal'><div class='modal-content'>
            <span class='close-x' onclick="closeM('mNewP')">&times;</span><h3>Nuevo Perfil</h3>
            <input id='pn' placeholder="Nombre perfil..."><button class='btn-emerald' onclick=\"savePerfil()\">GUARDAR</button>
        </div></div>
        <div id='mEditP' class='modal'><div class='modal-content'>
            <span class='close-x' onclick="closeM('mEditP')">&times;</span><h3>Editar Perfil</h3>
            <input type='hidden' id='ed_id'><input id='ed_n'><button class='btn-emerald' onclick=\"updatePerfil()\">ACTUALIZAR</button>
        </div></div>
        """

    # ==========================================
    # --- PANTALLA MODULOS ---
    # ==========================================
    elif path == "/modulos":
        cur.execute("SELECT can_view, can_add, can_edit, can_delete FROM perfil_modulo WHERE idPerfil = %s AND idModulo = -2", (u_data['idPerfil'],))
        p_act = cur.fetchone()
        if not p_act or not p_act['can_view']:
            start_response("303 See Other", [("Location", "/dashboard")]); return [b""]

        cur.execute("SELECT * FROM modulos ORDER BY id ASC")
        rows = ""
        for m in cur.fetchall():
            btn_e = f"<button class='btn-blue' onclick='preEdit({m['id']}, {{n:\"{m['strNombreModulo']}\", p:\"{m['strMenuPadre']}\"}}, \"mEditM\")'>Editar</button>" if p_act['can_edit'] else ""
            btn_d = f"<button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button>" if p_act['can_delete'] else ""
            rows += f"""<tr class='m-row'>
                <td><b class='m-name'>{m['strNombreModulo']}</b></td>
                <td>{m['strMenuPadre']}</td>
                <td>{btn_e} {btn_d}</td>
            </tr>"""
        
        btn_nuevo = f"<button class='btn-emerald' style='width:auto' onclick=\"openM('mNewM')\">+ NUEVO MÓDULO</button>" if p_act['can_add'] else ""

        content = f"""
        <div class='card'>
            <h2>📦 Gestión de Módulos</h2>
            <div style='display:flex; justify-content:space-between; margin-bottom:15px;'>
                {btn_nuevo}
                <input type="text" id="txtBusca" onkeyup="paginaActual=1; filtrar('.m-row', '.m-name');" placeholder="🔍 Buscar...">
            </div>
            <table><thead><tr><th>NOMBRE</th><th>PADRE</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table>
            <div class="paginador-ui">
                <button class="btn-blue" onclick="cambiarPagina(-1, '.m-row')">❮</button>
                <span id="infoPagina"></span>
                <button class="btn-blue" onclick="cambiarPagina(1, '.m-row')">❯</button>
            </div>
        </div>
        <div id='mNewM' class='modal'><div class='modal-content'>
            <span class='close-x' onclick="closeM('mNewM')">&times;</span>
            <h3>Nuevo Módulo</h3>
            <label>Nombre</label><input id='mn'>
            <label>Padre</label><select id='mp'><option>Principal 1</option><option>Principal 2</option></select>
            <button class='btn-emerald' onclick="saveMod()">GUARDAR</button>
        </div></div>
        <div id='mEditM' class='modal'><div class='modal-content'>
            <span class='close-x' onclick="closeM('mEditM')">&times;</span>
            <h3>Editar Módulo</h3>
            <input type='hidden' id='ed_id'>
            <label>Nombre</label><input id='ed_n_mod'>
            <label>Padre</label><select id='ed_p_mod'><option>Principal 1</option><option>Principal 2</option></select>
            <button class='btn-emerald' onclick="updateMod()">ACTUALIZAR</button>
        </div></div>
        """

    # ==========================================
    # --- PANTALLA PERMISOS ---
    # ==========================================
    elif path == "/permisos":
        cur.execute("SELECT can_view, can_edit FROM perfil_modulo WHERE idPerfil = %s AND idModulo = -4", (u_data['idPerfil'],))
        p_act = cur.fetchone()
        if not p_act or not p_act['can_view']:
            start_response("303 See Other", [("Location", "/dashboard")]); return [b""]

        cur.execute("SELECT id, strNombrePerfil FROM perfiles")
        perfiles = cur.fetchall()
        mods_fijos = [
            {'id': -1, 'nm': 'Perfiles', 'p': 'Seguridad'}, {'id': -2, 'nm': 'Modulos', 'p': 'Seguridad'},
            {'id': -3, 'nm': 'Usuarios', 'p': 'Seguridad'}, {'id': -4, 'nm': 'Permisos', 'p': 'Seguridad'}
        ]
        cur.execute("SELECT id, strNombreModulo as nm, strMenuPadre as p FROM modulos")
        todos_mods = mods_fijos + cur.fetchall()
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfiles])
        
        rows = ""
        for m in todos_mods:
            rows += f"""
            <tr class='mod-row'>
                <td><b class='mod-name'>{m['nm']}</b><br><small style='color:#94a3b8'>{m['p']}</small></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' data-type='v' id='v_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' data-type='a' id='a_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' data-type='e' id='e_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' data-type='d' id='d_{m['id']}'></td>
            </tr>"""

        # Botón de guardar solo si tiene permiso de editar
        btn_guardar = f"<button class='btn-emerald' style='margin-top:20px; width:100%;' onclick='guardarPermisos()'>GUARDAR CONFIGURACIÓN</button>" if p_act['can_edit'] else ""

        content = f"""
        <div class='card'>
            <h2>🛡️ Matriz de Permisos</h2>
            <div style='margin-bottom:20px;'><label>Seleccione Perfil:</label>
                <select id='sel_perfil' onchange='cargarPermisos(this.value)'><option value=''>-- Elegir --</option>{p_opts}</select>
            </div>
            <div id='area_permisos' style='display:none;'>
                <div style='display:flex; gap:10px; margin-bottom:15px; align-items:center;'>
                    <button class='btn-blue' onclick='bulk(true)' style='width:auto; padding:8px 12px;'>☑ Todo</button>
                    <button class='btn-red' onclick='bulk(false)' style='width:auto; padding:8px 12px;'>☐ Nada</button>
                    <input type="text" id="txtBusca" onkeyup="resetPaginacion(); filtrar();" placeholder="🔍 Buscar módulo..." style="margin:0; width:200px; margin-left:auto;">
                </div>
                <div style="border:1px solid var(--border); border-radius:12px; overflow:hidden;">
                    <table id="tablaPermisos" style='margin:0;'>
                        <thead><tr><th>MÓDULO</th><th>VER</th><th>ADD</th><th>EDIT</th><th>DEL</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                <div style="display:flex; justify-content:center; align-items:center; gap:15px; margin-top:15px;">
                    <button class="btn-blue" onclick="cambiarPagina(-1)" id="btnAnt" style="width:auto; padding:5px 15px;">❮</button>
                    <span id="infoPagina"></span>
                    <button class="btn-blue" onclick="cambiarPagina(1)" id="btnSig" style="width:auto; padding:5px 15px;">❯</button>
                </div>
                {btn_guardar}
            </div>
        </div>
        <script>
            // ... (Tu JS de permisos se mantiene igual) ...
        </script>
        """
    # ==========================================
    # --- JAVASCRIPT GLOBAL CORREGIDO ---
    # ==========================================
    content += """
    <style>
        .paginador-ui { display:flex; justify-content:center; align-items:center; gap:15px; margin-top:15px; padding-top:15px; border-top:1px solid var(--border); }
        .paginador-ui button:disabled { opacity: 0.4; cursor: not-allowed; }
    </style>
    <script>
        let paginaActual = 1;
        const filasPorPagina = 5;

        function filtrar(rowClass, nameClass) {
            const val = document.getElementById('txtBusca').value.toUpperCase();
            document.querySelectorAll(rowClass).forEach(row => {
                const b = row.querySelector(nameClass);
                const text = b ? b.innerText.toUpperCase() : "";
                row.dataset.visible = text.includes(val) ? "true" : "false";
            });
            renderTable(rowClass);
        }

        function renderTable(rowClass) {
            const filas = Array.from(document.querySelectorAll(rowClass));
            const visibles = filas.filter(r => r.dataset.visible !== "false");
            const total = Math.ceil(visibles.length / filasPorPagina) || 1;
            if (paginaActual > total) paginaActual = total;
            
            filas.forEach(r => r.style.display = 'none');
            visibles.slice((paginaActual-1)*5, paginaActual*5).forEach(r => r.style.display = '');
            const info = document.getElementById('infoPagina');
            if(info) info.innerText = `Página ${paginaActual} de ${total}`;
        }

        function cambiarPagina(delta, rowClass) {
            paginaActual += delta;
            if(paginaActual < 1) paginaActual = 1;
            renderTable(rowClass);
        }

        function validateAndSave() {
            const u = document.getElementById('un').value.trim();
            const p = document.getElementById('up').value;
            const c = document.getElementById('uc').value.trim();
            const t = document.getElementById('ut').value.trim();
            
            if(!u || !p || !c || !t) return alert("Todos los campos son obligatorios");
            if(p.length < 5) return alert("La contraseña debe ser mayor a 5 caracteres");
            if(!c.endsWith("@gmail.com")) return alert("El correo debe ser @gmail.com");
            if(t.length !== 10) return alert("El teléfono debe tener 10 dígitos");

            runCrud('save', 'usuarios', 0, { u, p, idp: document.getElementById('un_idp').value, st: document.getElementById('un_st').value });
        }

        function updateUser() {
            runCrud('update', 'usuarios', document.getElementById('ed_id').value, { 
                u: document.getElementById('ed_u').value, idp: document.getElementById('ed_idp').value, st: document.getElementById('ed_st').value 
            });
        }

        function saveMod() {
            const n = document.getElementById('mn').value.trim();
            if(!n) return alert("Nombre obligatorio");
            const r = "/" + n.toLowerCase().replace(/\s+/g, '-');
            runCrud('save', 'modulos', 0, { n, r, p: document.getElementById('mp').value });
        }

        function updateMod() {
            const id = document.getElementById('ed_id').value;
            const n = document.getElementById('ed_n_mod').value.trim();
            const p = document.getElementById('ed_p_mod').value;
            if(!n) return alert("Nombre obligatorio");
            const r = "/" + n.toLowerCase().replace(/\s+/g, '-');
            runCrud('update', 'modulos', id, { n, r, p });
        }

        function savePerfil() {
            const n = document.getElementById('pn').value.trim();
            if(!n) return alert("Nombre obligatorio");
            runCrud('save', 'perfiles', 0, {n});
        }
        function updatePerfil() {
            runCrud('update', 'perfiles', document.getElementById('ed_id').value, {n: document.getElementById('ed_n').value});
        }

        async function cargarPermisos(idp) {
            if(!idp) { document.getElementById('area_permisos').style.display='none'; return; }
            document.querySelectorAll('.perm-check').forEach(c => c.checked = false);
            const res = await fetch('/api/get_permisos?idp=' + idp);
            const data = await res.json();
            if(data.ok) {
                data.perms.forEach(p => {
                    const v = document.getElementById('v_'+p.idm), a = document.getElementById('a_'+p.idm),
                          e = document.getElementById('e_'+p.idm), d = document.getElementById('d_'+p.idm);
                    if(v && p.v) v.checked = true;
                    if(a && p.a) a.checked = true;
                    if(e && p.e) e.checked = true;
                    if(d && p.d) d.checked = true;
                });
                document.getElementById('area_permisos').style.display = 'block';
                paginaActual = 1;
                filtrar('.mod-row', '.mod-name');
            }
        }

        function bulk(v) {
            document.querySelectorAll('.mod-row').forEach(row => {
                if(row.style.display !== 'none') row.querySelectorAll('.perm-check').forEach(c => c.checked = v);
            });
        }

        function guardarPermisos() {
            const idp = document.getElementById('sel_perfil').value;
            const matrix = [];
            const ids = [...new Set(Array.from(document.querySelectorAll('.perm-check')).map(c => c.dataset.mod))];
            ids.forEach(id => {
                matrix.push({
                    idm: parseInt(id),
                    v: document.getElementById('v_'+id).checked ? 1 : 0,
                    a: document.getElementById('a_'+id).checked ? 1 : 0,
                    e: document.getElementById('e_'+id).checked ? 1 : 0,
                    d: document.getElementById('d_'+id).checked ? 1 : 0
                });
            });
            runCrud('save', 'permisos', 0, { idp, perms: matrix });
        }

        window.onload = () => {
            const b = document.getElementById('txtBusca');
            if(b) b.value = "";
            if(document.querySelector('.u-row')) filtrar('.u-row', '.u-name');
            if(document.querySelector('.p-row')) filtrar('.p-row', '.p-name');
            if(document.querySelector('.m-row')) filtrar('.m-row', '.m-name');
        };
    </script>
    """

    # --- RENDERIZADO FINAL ---
    try:
        # Si la ruta no coincide con nada de lo anterior, mostramos Inicio
        if not content:
            content = """
            <div class='card'>
                <h2>Bienvenido al Sistema</h2>
                <p>Usa el menú superior para navegar por los módulos disponibles.</p>
            </div>"""
            
        res_html = render_layout("Clinica 2026", content, u_data).encode("utf-8")
        start_response("200 OK", [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Cache-Control", "no-cache")
        ])
        return [res_html]

    except Exception as e:
        # Si algo falla aquí, imprimimos el error real en la pantalla
        start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
        return [f"Error de Ejecución: {str(e)}".encode()]
    
    finally:
        # Cerramos con seguridad: solo si existen y no son None
        if 'cur' in locals() and cur: 
            try: cur.close()
            except: pass
        if 'conn' in locals() and conn: 
            try: conn.close()
            except: pass
  