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
# DISEÑO MODIFICADO: INCLUYE PERMISOS Y MEJORAS VISUALES
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in all_mods if m['strMenuPadre'] == padre])
        
        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left">
        <span class="logo" style="color:#10b981; font-weight:bold; font-size:1.2rem; margin-right:20px;">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        <div class="dropdown">
            <button class="dropbtn">Seguridad ▾</button>
            <div class="dropdown-content">
                <a href="/perfiles">👤 Perfiles</a>
                <a href="/modulos">📦 Modulos</a>
                <a href="/usuarios">👥 Usuarios</a>
                <a href="/permisos">🔐 Permisos</a>  </div>
        </div>
        <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1")}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2")}</div></div>
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
        
        /* Estilos específicos para Permisos */
        .grid-permisos {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:15px; margin-top:15px; }}
        .check-item {{ background:#0f172a; padding:12px; border-radius:8px; border:1px solid var(--border); display:flex; align-items:center; gap:10px; cursor:pointer; }}
        .check-item input {{ width:auto; margin:0; cursor:pointer; }}
        
        .close-x {{ position:absolute; top:20px; right:25px; color:#94a3b8; cursor:pointer; font-size:24px; }}
        .user-pill {{ color:var(--emerald); border:1px solid var(--border); padding:6px 16px; border-radius:25px; margin-right:15px; font-size:13px; font-weight:bold; }}
        .btn-salir {{ background:#ef4444; color:white; text-decoration:none; padding:8px 18px; border-radius:8px; font-size:13px; font-weight:bold; }}
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
        function handleImg(e, prevId) {{
            const reader = new FileReader();
            reader.onload = () => {{ 
                const prev = document.getElementById(prevId);
                prev.src = reader.result;
                prev.style.display = 'block';
            }};
            reader.readAsDataURL(e.target.files[0]);
        }}
    </script>
    </head><body>{nav}<div class='container'>{content}</div></body></html>"""

def application(environ, start_response):
    path = environ.get("PATH_INFO", "/"); method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ); content = ""

    # 1. Inicializamos en None para evitar errores de "local variable referenced before assignment"
    conn = None
    cur = None

 # --- API GET PERMISOS (MATRIZ COMPLETA) ---
    if path == "/api/get_permisos" and method == "GET":
        import cgi
        params = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
        idp = params.getvalue('idp')
        res = b'{"ok":false}'
        conn = conectar_bd(); cur = conn.cursor(dictionary=True) # Usamos dictionary para leer nombres de columna
        try:
            # Consultamos los 4 tipos de permisos por módulo
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

    # --- API CRUD PRINCIPAL (ACTUALIZADO PARA MATRIZ) ---
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
        
 # --- PANTALLA USUARIOS ---
    if path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil = p.id")
        usuarios = cur.fetchall()
        
        rows = "".join([f"""<tr>
            <td><img src='https://ui-avatars.com/api/?name={u['strNombreUsuario']}&background=random' class='avatar-table'></td>
            <td><b>{u['strNombreUsuario']}</b></td>
            <td>{u['strNombrePerfil']}</td>
            <td><span class='status-pill {'active' if u['strEstado']=='Activo' else 'inactive'}'>{u['strEstado']}</span></td>
            <td>
                <button class='btn-blue' onclick='preEdit({u['id']}, {{u:\"{u['strNombreUsuario']}\", idp:{u['idPerfil']}, st:\"{u['strEstado']}\"}})'>Editar</button>
                <button class='btn-red' onclick=\"runCrud('delete','usuarios',{u['id']})\">Borrar</button>
            </td>
        </tr>""" for u in usuarios])

        cur.execute("SELECT * FROM perfiles")
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])

        content = f"""
        <div class='card'>
            <h2>👥 Gestión de Usuarios</h2>
            <button class='btn-emerald' style='width:auto' onclick="openM('mNew')">+ NUEVO USUARIO</button>
            <table>
                <thead><tr><th>IMG</th><th>USUARIO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>

        <div id='mNew' class='modal'><div class='modal-content'>
            <span class='close-x' onclick="closeM('mNew')">&times;</span>
            <h3>Nuevo Usuario</h3>
            <div class='grid-2'>
                <div>
                    <label>Nombre (Letras, máx 15)</label>
                    <input id='un' maxlength="15" oninput="this.value=this.value.replace(/[^a-zA-Z\\s]/g,'')">
                </div>
                <div>
                    <label>Pass (5-8 carac.)</label>
                    <input id='up' type='password' minlength="5" maxlength="8">
                </div>
                <div>
                    <label>Correo (@gmail.com)</label>
                    <input id='uc' type='email' maxlength="30" placeholder="ejemplo@gmail.com">
                </div>
                <div>
                    <label>Teléfono (10 dígitos)</label>
                    <input id='ut' maxlength="10" oninput="this.value=this.value.replace(/[^0-9]/g,'')">
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
                <div><label>Usuario</label><input id='ed_u' maxlength="15" oninput="this.value=this.value.replace(/[^a-zA-Z\\s]/g,'')"></div>
                <div><label>Perfil</label><select id='ed_idp'>{p_opts}</select></div>
                <div><label>Estado</label><select id='ed_st'><option>Activo</option><option>Inactivo</option></select></div>
            </div>
            <button class='btn-emerald' onclick="updateUser()">ACTUALIZAR</button>
        </div></div>

        <script>
            function validateAndSave() {{
                const u = document.getElementById('un').value.trim();
                const p = document.getElementById('up').value;
                const c = document.getElementById('uc').value.trim();
                const t = document.getElementById('ut').value.trim();
                const idp = document.getElementById('un_idp').value;
                const st = document.getElementById('un_st').value;

                // Validaciones de JS
                if(u.length < 3) return alert("Nombre demasiado corto");
                if(p.length < 5 || p.length > 8) return alert("La contraseña debe tener entre 5 y 8 caracteres");
                if(!c.endsWith("@gmail.com")) return alert("El correo debe ser @gmail.com");
                if(t.length !== 10) return alert("El teléfono debe tener exactamente 10 dígitos");

                const data = {{ u, p, idp, st }}; // Tu API solo procesa estos 4 según el código que enviaste
                runCrud('save', 'usuarios', 0, data);
            }}

            function updateUser() {{
                const id = document.getElementById('ed_id').value;
                const u = document.getElementById('ed_u').value.trim();
                const idp = document.getElementById('ed_idp').value;
                const st = document.getElementById('ed_st').value;

                if(!u) return alert("El nombre es obligatorio");
                runCrud('update', 'usuarios', id, {{ u, idp, st }});
            }}
        </script>
        """
            
    # --- PANTALLA PERFILES ---
    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles ORDER BY id ASC")
        perfiles = cur.fetchall()
        rows = ""
        for index, p in enumerate(perfiles, start=1):
            rows += f"""<tr>
                <td>{index}</td>
                <td><b>{p['strNombrePerfil']}</b></td>
                <td>
                    <button class='btn-blue' onclick='preEdit({p['id']}, {{n:\"{p['strNombrePerfil']}\"}}, \"mEditP\")'>Editar</button>
                    <button class='btn-red' onclick=\"runCrud('delete','perfiles',{p['id']})\">Borrar</button>
                </td>
            </tr>"""
            
        content = f"""<div class='card'><h2>👤 Gestión de Perfiles</h2><button class='btn-emerald' style='width:auto' onclick="openM('mNewP')">+ NUEVO PERFIL</button>
            <table><thead><tr><th>#</th><th>NOMBRE DEL PERFIL</th><th>ACCIONES</th></tr></thead><tbody>{rows}</tbody></table></div>
        <div id='mNewP' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mNewP')">&times;</span><h3>Nuevo Perfil</h3>
            <label>Nombre del Perfil (Máx. 15 letras)</label>
            <input id='pn' placeholder='Ej: Ventas' maxlength="15" oninput="this.value = this.value.replace(/[^A-Za-z\\s]/g, '')">
            <button class='btn-emerald' onclick=\"savePerfil()\">CREAR PERFIL</button></div></div>
        <div id='mEditP' class='modal'><div class='modal-content'><span class='close-x' onclick="closeM('mEditP')">&times;</span><h3>Editar Perfil</h3><input type='hidden' id='ed_id'>
            <label>Nombre del Perfil</label>
            <input id='ed_n' maxlength="15" oninput="this.value = this.value.replace(/[^A-Za-z\\s]/g, '')">
            <button class='btn-emerald' onclick=\"updatePerfil()\">ACTUALIZAR</button></div></div>
        <script>
            async function savePerfil() {{
                const nom = document.getElementById('pn').value.trim();
                if(!nom) return alert("Escribe un nombre válido");
                runCrud('save', 'perfiles', 0, {{n: nom}});
            }}
            async function updatePerfil() {{
                const id = document.getElementById('ed_id').value;
                const nom = document.getElementById('ed_n').value.trim();
                if(!nom) return alert("El nombre no puede estar vacío");
                runCrud('update', 'perfiles', id, {{n: nom}});
            }}
        </script>"""

# --- PANTALLA MODULOS
    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos ORDER BY id ASC")
        modulos = cur.fetchall()
    
        rows = "".join([f"""<tr>
            <td><b>{m['strNombreModulo']}</b></td>
            <td>{m['strMenuPadre']}</td>
            <td>
                <button class='btn-blue' onclick='preEdit({m['id']}, {{n:\"{m['strNombreModulo']}\", p:\"{m['strMenuPadre']}\"}}, \"mEditM\")'>Editar</button>
                <button class='btn-red' onclick=\"runCrud('delete','modulos',{m['id']})\">Borrar</button>
            </td>
        </tr>""" for m in modulos])
        
        content = f"""
        <div class='card'>
            <h2>📦 Gestión de Módulos</h2>
            <button class='btn-emerald' style='width:auto' onclick="openM('mNewM')">+ NUEVO MÓDULO</button>
            <table>
                <thead><tr><th>NOMBRE</th><th>MENÚ PADRE</th><th>ACCIONES</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>

        <div id='mNewM' class='modal'>
            <div class='modal-content'>
                <span class='close-x' onclick="closeM('mNewM')">&times;</span>
                <h3>Nuevo Módulo</h3>
                <label>Nombre del Módulo (Máx. 20)</label>
                <input id='mn' placeholder='Ej: Facturación' maxlength="20" 
                       oninput="this.value = this.value.replace(/[^A-Za-z0-9\\s]/g, '')">
                <label>Menú Padre</label>
                <select id='mp'><option>Principal 1</option><option>Principal 2</option></select>
                <button class='btn-emerald' onclick="saveMod()">GUARDAR MÓDULO</button>
            </div>
        </div>

        <div id='mEditM' class='modal'>
            <div class='modal-content'>
                <span class='close-x' onclick="closeM('mEditM')">&times;</span>
                <h3>Editar Módulo</h3>
                <input type='hidden' id='ed_id'>
                <label>Nombre del Módulo</label>
                <input id='ed_n' maxlength="20" 
                       oninput="this.value = this.value.replace(/[^A-Za-z0-9\\s]/g, '')">
                <label>Menú Padre</label>
                <select id='ed_p'><option>Principal 1</option><option>Principal 2</option></select>
                <button class='btn-emerald' onclick="updateMod()">ACTUALIZAR CAMBIOS</button>
            </div>
        </div>

        <script>
            // Las funciones JS siguen generando la ruta automática para enviarla al API
            async function saveMod() {{
                const n = document.getElementById('mn').value.trim();
                const p = document.getElementById('mp').value;
                if(!n) return alert("El nombre es obligatorio");
                
                // Generamos una ruta automática basada en el nombre (ej: "Mi Modulo" -> "/mi-modulo")
                const autoRuta = "/" + n.toLowerCase().replace(/\\s+/g, '-');
                
                runCrud('save', 'modulos', 0, {{n, r: autoRuta, p}});
            }}

            async function updateMod() {{
                const id = document.getElementById('ed_id').value;
                const n = document.getElementById('ed_n').value.trim();
                const p = document.getElementById('ed_p').value;
                if(!n) return alert("El nombre no puede estar vacío");

                const autoRuta = "/" + n.toLowerCase().replace(/\\s+/g, '-');

                runCrud('update', 'modulos', id, {{n, r: autoRuta, p}});
            }}
        </script>
        """
       # --- PANTALLA PERMISOS (ALINEADO Y FUNCIONAL) ---
   # --- PANTALLA PERMISOS (CORREGIDA) ---
    elif path == "/permisos":
        cur.execute("SELECT id, strNombrePerfil FROM perfiles")
        perfiles = cur.fetchall()
        
        # Lista extendida de módulos (Fijos + DB)
        mods_fijos = [
            {'id': -1, 'nm': 'Perfiles', 'p': 'Seguridad'}, {'id': -2, 'nm': 'Modulos', 'p': 'Seguridad'},
            {'id': -3, 'nm': 'Usuarios', 'p': 'Seguridad'}, {'id': -4, 'nm': 'Permisos', 'p': 'Seguridad'}
        ]
        cur.execute("SELECT id, strNombreModulo as nm, strMenuPadre as p FROM modulos")
        todos_mods = mods_fijos + cur.fetchall()

        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfiles])
        
        # Generar filas con la matriz de checkboxes
        rows = ""
        for m in todos_mods:
            rows += f"""
            <tr class='mod-row'>
                <td><b class='mod-name'>{m['nm']}</b> <br><small style='color:#94a3b8'>{m['p']}</small></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' data-type='v' id='v_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' data-type='a' id='a_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' data-type='e' id='e_{m['id']}'></td>
                <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m['id']}' data-type='d' id='d_{m['id']}'></td>
            </tr>"""

        content = f"""
        <div class='card'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;'>
                <h2>🛡️ Matriz de Permisos</h2>
                <select id='sel_perfil' onchange='cargarPermisos(this.value)' style='width:250px; margin:0;'>
                    <option value=''>-- Seleccionar Perfil --</option>
                    {p_opts}
                </select>
            </div>

            <div id='area_permisos' style='display:none'>
                <div style='display:flex; gap:10px; margin-bottom:15px;'>
                    <button class='btn-blue' onclick='bulk(true)' style='width:auto; padding:8px 15px;'>☑ Marcar Todo</button>
                    <button class='btn-red' onclick='bulk(false)' style='width:auto; padding:8px 15px;'>☐ Desmarcar Todo</button>
                    <input type="text" id="txtBusca" onkeyup="filtrar()" placeholder="🔍 Buscar módulo..." style="margin:0; width:200px; margin-left:auto;">
                </div>

                <div style="max-height:500px; overflow-y:auto; border-radius:12px; border:1px solid var(--border);">
                    <table style='margin-top:0;'>
                        <thead style='position:sticky; top:0; z-index:10;'>
                            <tr>
                                <th>MÓDULO</th>
                                <th style='text-align:center'>CONSULTAR</th>
                                <th style='text-align:center'>AGREGAR</th>
                                <th style='text-align:center'>EDITAR</th>
                                <th style='text-align:center'>ELIMINAR</th>
                            </tr>
                        </thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                <button class='btn-emerald' style='margin-top:20px;' onclick='guardarPermisos()'>GUARDAR CONFIGURACIÓN</button>
            </div>
        </div>

        <script>
            function filtrar() {{
                let val = document.getElementById('txtBusca').value.toUpperCase();
                document.querySelectorAll('.mod-row').forEach(row => {{
                    let text = row.querySelector('.mod-name').innerText.toUpperCase();
                    row.style.display = text.includes(val) ? "" : "none";
                }});
            }}

            function bulk(v) {{
                document.querySelectorAll('.mod-row').forEach(row => {{
                    if(row.style.display !== 'none') {{
                        row.querySelectorAll('.perm-check').forEach(c => c.checked = v);
                    }}
                }});
            }}

            async function cargarPermisos(idp) {{
                if(!idp) return document.getElementById('area_permisos').style.display='none';
                document.querySelectorAll('.perm-check').forEach(c => c.checked = false);
                
                const res = await fetch('/api/get_permisos?idp=' + idp);
                const data = await res.json();
                if(data.ok) {{
                    data.perms.forEach(p => {{
                        if(p.v) document.getElementById('v_'+p.idm).checked = true;
                        if(p.a) document.getElementById('a_'+p.idm).checked = true;
                        if(p.e) document.getElementById('e_'+p.idm).checked = true;
                        if(p.d) document.getElementById('d_'+p.idm).checked = true;
                    }});
                    document.getElementById('area_permisos').style.display = 'block';
                }}
            }}

            function guardarPermisos() {{
                const idp = document.getElementById('sel_perfil').value;
                const matrix = {{}};
                
                document.querySelectorAll('.perm-check').forEach(c => {{
                    const idm = c.dataset.mod;
                    if(!matrix[idm]) matrix[idm] = {{idm, v:0, a:0, e:0, d:0}};
                    if(c.checked) matrix[idm][c.dataset.type] = 1;
                }});

                runCrud('save', 'permisos', 0, {{ idp, perms: Object.values(matrix) }});
            }}
        </script>
        """
        
    # --- CIERRE FINAL SEGURO ---
    if cur: cur.close()
    if conn: conn.close()
    
    start_response("200 OK", [("Content-Type", "text/html")])
    return [render_layout("Clinica", content, u_data).encode()]