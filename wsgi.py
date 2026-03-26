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
        
        
# ==========================================
    # --- PANTALLA USUARIOS (VALIDACIÓN MEJORADA) ---
    # ==========================================
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

        content = f"""
        <div class='card'>
            <h2>👥 Gestión de Usuarios</h2>
            <div style='display:flex; justify-content:space-between; margin-bottom:15px; align-items:center;'>
                <button class='btn-emerald' style='width:auto' onclick="openM('mNew')">+ NUEVO USUARIO</button>
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
                <div><label>Nombre</label>
                    <input id='un' maxlength="15" onkeypress="return /^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$/i.test(event.key)">
                </div>
                <div><label>Pass (5-8 carac.)</label><input id='up' type='password' maxlength="8"></div>
                <div><label>Correo (@gmail.com)</label><input id='uc' type='email' maxlength="30"></div>
                <div><label>Teléfono (10 dig)</label>
                    <input id='ut' maxlength="10" onkeypress="return /^[0-9]+$/.test(event.key)">
                </div>
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
                <div><label>Usuario</label>
                    <input id='ed_u' maxlength="15" onkeypress="return /^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$/i.test(event.key)">
                </div>
                <div><label>Perfil</label><select id='ed_idp'>{p_opts}</select></div>
                <div><label>Estado</label><select id='ed_st'><option>Activo</option><option>Inactivo</option></select></div>
            </div>
            <button class='btn-emerald' onclick="updateUser()">ACTUALIZAR</button>
        </div></div>
        """
    # ==========================================
    # --- PANTALLA PERFILES CORREGIDA ---
    # ==========================================
    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles ORDER BY id ASC")
        perfiles = cur.fetchall()
        rows = ""
        for i, p in enumerate(perfiles, 1):
            # Usamos comillas simples para los strings en preEdit para evitar errores de escape
            nombre_p = p['strNombrePerfil'].replace('"', '&quot;')
            rows += f"""<tr class='p-row'>
                <td>{i}</td>
                <td><b class='p-name'>{nombre_p}</b></td>
                <td>
                    <button class='btn-blue' onclick='preEdit({p["id"]}, {{n:"{nombre_p}"}}, "mEditP")'>Editar</button>
                    <button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button>
                </td>
            </tr>"""
            
        content = f"""
        <div class='card'>
            <h2>👤 Gestión de Perfiles</h2>
            <div style='display:flex; justify-content:space-between; margin-bottom:15px;'>
                <button class='btn-emerald' style='width:auto' onclick="openM('mNewP')">+ NUEVO PERFIL</button>
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
            <span class='close-x' onclick="closeM('mNewP')">&times;</span>
            <h3>Nuevo Perfil</h3>
            <input id='pn' maxlength="20" onkeypress="return /^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$/i.test(event.key)" placeholder="Nombre perfil...">
            <button class='btn-emerald' onclick=\"savePerfil()\">GUARDAR</button>
        </div></div>

        <div id='mEditP' class='modal'><div class='modal-content'>
            <span class='close-x' onclick="closeM('mEditP')">&times;</span>
            <h3>Editar Perfil</h3>
            <input type='hidden' id='ed_id'>
            <input id='ed_n' maxlength="20" onkeypress="return /^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$/i.test(event.key)">
            <button class='btn-emerald' onclick=\"updatePerfil()\">ACTUALIZAR</button>
        </div></div>
        """
    # ==========================================
    # --- PANTALLA MODULOS (CORREGIDO UPDATE) ---
    # ==========================================
    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos ORDER BY id ASC")
        rows = "".join([f"""<tr class='m-row'>
            <td><b class='m-name'>{m['strNombreModulo']}</b></td>
            <td>{m['strMenuPadre']}</td>
            <td>
                <button class='btn-blue' onclick='preEdit({m['id']}, {{n:\"{m['strNombreModulo']}\", p:\"{m['strMenuPadre']}\"}}, \"mEditM\")'>Editar</button>
                <button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button>
            </td>
        </tr>""" for m in cur.fetchall()])
        
        content = f"""
        <div class='card'>
            <h2>📦 Gestión de Módulos</h2>
            <div style='display:flex; justify-content:space-between; margin-bottom:15px;'>
                <button class='btn-emerald' style='width:auto' onclick="openM('mNewM')">+ NUEVO MÓDULO</button>
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
    # --- PANTALLA PERMISOS (TABLA QUE CARGA AL SELECCIONAR) ---
    # ==========================================
    elif path == "/permisos":
        cur.execute("SELECT id, strNombrePerfil FROM perfiles")
        perfiles = cur.fetchall()
        # Módulos fijos + variables
        mods_fijos = [{'id': -1, 'nm': 'Perfiles', 'p': 'Seguridad'}, {'id': -2, 'nm': 'Modulos', 'p': 'Seguridad'}, {'id': -3, 'nm': 'Usuarios', 'p': 'Seguridad'}, {'id': -4, 'nm': 'Permisos', 'p': 'Seguridad'}]
        cur.execute("SELECT id, strNombreModulo as nm, strMenuPadre as p FROM modulos")
        todos_mods = mods_fijos + cur.fetchall()
        
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfiles])
        
        # Agregamos data-visible='true' para que el paginador las reconozca al cargar
        rows = "".join([f"""<tr class='perm-row' data-visible='true'>
                <td><b class='perm-name'>{m['nm']}</b><br><small>{m['p']}</small></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' id='v_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' id='a_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' id='e_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' id='d_{m['id']}'></td>
            </tr>""" for m in todos_mods])

        content = f"""
        <div class='card'>
            <h2>🛡️ Matriz de Permisos</h2>
            <select id='sel_perfil' onchange='cargarPermisos(this.value)' style='border: 2px solid var(--emerald); padding:10px;'>
                <option value=''>-- Seleccione un Perfil para ver la tabla --</option>{p_opts}
            </select>
            
            <div id='area_permisos' style='display:none; margin-top:20px;'>
                <div style='display:flex; gap:10px; margin-bottom:15px; align-items:center;'>
                    <button class='btn-blue' onclick='bulk(true)' style="width:auto">☑ Todo</button>
                    <button class='btn-red' onclick='bulk(false)' style="width:auto">☐ Nada</button>
                    <input type="text" id="txtBusca" onkeyup="paginaActual=1; filtrar('.perm-row', '.perm-name');" placeholder="🔍 Buscar módulo..." style="margin-left:auto; width:200px; margin-bottom:0;">
                </div>
                <table>
                    <thead><tr><th>MÓDULO</th><th>VER</th><th>ADD</th><th>EDT</th><th>DEL</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                <div class="paginador-ui">
                    <button class="btn-blue" onclick="cambiarPagina(-1, '.perm-row')">❮</button>
                    <span id="infoPagina" style="font-weight:bold; color:var(--emerald);"></span>
                    <button class="btn-blue" onclick="cambiarPagina(1, '.perm-row')">❯</button>
                </div>
                <button class='btn-emerald' style='margin-top:20px; width:100%; font-size:16px;' onclick='guardarPermisos()'>GUARDAR CONFIGURACIÓN ACTUAL</button>
            </div>
        </div>
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
            document.getElementById('infoPagina').innerText = `Página ${paginaActual} de ${total}`;
        }

        function cambiarPagina(delta, rowClass) {
            paginaActual += delta;
            renderTable(rowClass);
        }

        // --- VALIDACIÓN USUARIOS ---
        function validateAndSave() {
            const u = document.getElementById('un').value.trim();
            const p = document.getElementById('up').value;
            const c = document.getElementById('uc').value.trim();
            const t = document.getElementById('ut').value.trim();
            
            // Expresión para solo letras (incluye espacios y acentos)
            const regexLetras = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$/;
            // Expresión para solo números
            const regexNumeros = /^[0-9]+$/;

            if(!u || !p || !c || !t) return alert("Todos los campos son obligatorios");
            
            if(!regexLetras.test(u)) return alert("El nombre solo debe contener letras");
            if(p.length < 5) return alert("La contraseña debe tener entre 5 y 8 caracteres");
            if(!c.endsWith("@gmail.com")) return alert("El correo debe ser @gmail.com");
            if(t.length !== 10 || !regexNumeros.test(t)) return alert("El teléfono debe tener exactamente 10 números");

            runCrud('save', 'usuarios', 0, { u, p, c, t, idp: document.getElementById('un_idp').value, st: document.getElementById('un_st').value });
            closeM('mNew');
        }

        function updateUser() {
            const u = document.getElementById('ed_u').value.trim();
            const regexLetras = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$/;

            if(!u) return alert("El nombre es obligatorio");
            if(!regexLetras.test(u)) return alert("El nombre solo debe contener letras");

            runCrud('update', 'usuarios', document.getElementById('ed_id').value, { 
                u, idp: document.getElementById('ed_idp').value, st: document.getElementById('ed_st').value 
            });
            closeM('mEdit');
        }

        // MODULOS
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

        // --- PERFILES (VALIDACIÓN DE SOLO LETRAS) ---
        function validarNombrePerfil(nombre) {
            // Esta expresión permite letras (incluyendo ñ y acentos) y espacios
            const regex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$/;
            
            if (!nombre) {
                alert("El nombre es obligatorio");
                return false;
            }
            if (nombre.length < 3) {
                alert("El nombre debe tener al menos 3 caracteres");
                return false;
            }
            if (!regex.test(nombre)) {
                alert("El nombre solo puede contener letras (sin números ni símbolos)");
                return false;
            }
            return true;
        }

        function savePerfil() {
            const n = document.getElementById('pn').value.trim();
            
            if(validarNombrePerfil(n)) {
                runCrud('save', 'perfiles', 0, {n});
                document.getElementById('pn').value = ""; // Limpiar tras guardar
            }
        }

        function updatePerfil() {
            const id = document.getElementById('ed_id').value;
            const n = document.getElementById('ed_n').value.trim();
            
            if(validarNombrePerfil(n)) {
                runCrud('update', 'perfiles', id, {n});
                // Cerrar modal si usas uno
                if(typeof closeModals === 'function') closeModals(); 
            }
        }

        // PERMISOS
        async function cargarPermisos(idp) {
            if(!idp) { document.getElementById('area_permisos').style.display='none'; return; }
            document.querySelectorAll('.perm-check').forEach(c => c.checked = false);
            const res = await fetch('/api/get_permisos?idp=' + idp);
            const data = await res.json();
            if(data.ok) {
                data.perms.forEach(p => {
                    if(p.v) document.getElementById('v_'+p.idm).checked = true;
                    if(p.a) document.getElementById('a_'+p.idm).checked = true;
                    if(p.e) document.getElementById('e_'+p.idm).checked = true;
                    if(p.d) document.getElementById('d_'+p.idm).checked = true;
                });
                document.getElementById('area_permisos').style.display = 'block';
                paginaActual = 1;
                filtrar('.perm-row', '.perm-name');
            }
        }

        function bulk(v) {
            document.querySelectorAll('.perm-row').forEach(row => {
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

            runCrud('save', 'permisos', 0, { 
                idp: parseInt(idp), // Aseguramos que sea número
                perms: matrix 
            });
        }

        // Al entrar, limpiar buscador y renderizar
        window.onload = () => {
            const b = document.getElementById('txtBusca');
            if(b) b.value = "";
            if(document.querySelector('.u-row')) filtrar('.u-row', '.u-name');
            if(document.querySelector('.p-row')) filtrar('.p-row', '.p-name');
            if(document.querySelector('.m-row')) filtrar('.m-row', '.m-name');
        };
    </script>
    """

    # --- CIERRE Y RENDERIZADO FINAL ---
    try:
        # Intentamos cerrar si existen, pero dentro de un try por seguridad
        if 'cur' in locals() and cur: cur.close()
        if 'conn' in locals() and conn: conn.close()
    except:
        pass

    # Generamos la respuesta HTML
    try:
        # Asegúrate de que 'content' no sea None
        final_body = render_layout("Clínica 2026", content or "Sin contenido", u_data)
        res_html = final_body.encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html")])
        return [res_html]
    except Exception as e:
        # Si el render_layout falla, mostramos el error técnico
        start_response("500 Internal Server Error", [("Content-Type", "text/html")])
        return [f"<h1>Error de Renderizado</h1><p>{str(e)}</p>".encode()]

# --- FIN DE LA FUNCIÓN APPLICATION ---