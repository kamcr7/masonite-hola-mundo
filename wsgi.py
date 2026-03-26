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
    return mysql.connector.connect(
        host=res.hostname, port=res.port, user=res.username,
        password=res.password, database=res.path[1:], charset='utf8mb4'
    )
 
# =========================================================
# LAYOUT PRINCIPAL
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()
        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>'
                            for m in all_mods if m['strMenuPadre'] == padre])
        nav = f"""
        <div class="top-nav">
          <div class="nav-container">
            <div class="nav-left">
              <span class="logo">🏥 Clinica</span>
              <a href="/dashboard" class="nav-link">Inicio</a>
              <div class="dropdown">
                <button class="dropbtn">Seguridad ▾</button>
                <div class="dropdown-content">
                  <a href="/perfiles">👤 Perfiles</a>
                  <a href="/modulos">📦 Módulos</a>
                  <a href="/usuarios">👥 Usuarios</a>
                  <a href="/permisos">🔐 Permisos</a>
                </div>
              </div>
              <div class="dropdown">
                <button class="dropbtn">Principal 1 ▾</button>
                <div class="dropdown-content">{get_links("Principal 1")}</div>
              </div>
              <div class="dropdown">
                <button class="dropbtn">Principal 2 ▾</button>
                <div class="dropdown-content">{get_links("Principal 2")}</div>
              </div>
            </div>
            <div class="nav-right">
              <span class="user-pill">{user['u']}</span>
              <a href="/logout" class="btn-salir">Salir</a>
            </div>
          </div>
        </div>"""
 
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0b1120; --card: #1e293b; --emerald: #10b981;
      --border: #334155; --text: #f8fafc;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: sans-serif; background: var(--bg); color: var(--text); margin: 0; }}
    /* NAV */
    .top-nav {{ background: #070b14; height: 60px; border-bottom: 1px solid var(--border); display: flex; align-items: center; position: sticky; top: 0; z-index: 200; }}
    .nav-container {{ width: 100%; max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; padding: 0 20px; align-items: center; }}
    .logo {{ color: #10b981; font-weight: bold; font-size: 1.2rem; margin-right: 20px; }}
    .nav-link {{ color: #94a3b8; text-decoration: none; padding: 10px; font-size: 14px; }}
    .nav-link:hover {{ color: white; }}
    .dropdown {{ position: relative; display: inline-block; }}
    .dropdown-content {{ display: none; position: absolute; background: var(--card); min-width: 180px; border: 1px solid var(--border); border-radius: 12px; z-index: 300; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); top: 100%; left: 0; }}
    .dropdown-content a {{ color: white; padding: 12px; text-decoration: none; display: block; border-bottom: 1px solid #334155; font-size: 14px; }}
    .dropdown-content a:last-child {{ border-bottom: none; }}
    .dropdown-content a:hover {{ background: #2d3748; border-radius: 0 0 12px 12px; }}
    .dropdown:hover .dropdown-content {{ display: block; }}
    .dropbtn {{ background: transparent; color: #94a3b8; border: none; padding: 15px; cursor: pointer; font-size: 14px; }}
    .dropbtn:hover {{ color: white; }}
    .user-pill {{ color: var(--emerald); border: 1px solid var(--border); padding: 6px 16px; border-radius: 25px; margin-right: 15px; font-size: 13px; font-weight: bold; }}
    .btn-salir {{ background: #ef4444; color: white; text-decoration: none; padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: bold; }}
    .nav-right {{ display: flex; align-items: center; }}
    /* LAYOUT */
    .container {{ padding: 40px; max-width: 1200px; margin: 0 auto; }}
    .card {{ background: var(--card); padding: 30px; border-radius: 16px; border: 1px solid var(--border); }}
    /* TABLE */
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #0f172a; border-radius: 12px; overflow: hidden; }}
    th {{ background: #1e293b; color: #94a3b8; font-size: 12px; text-transform: uppercase; padding: 15px; text-align: left; }}
    td {{ padding: 15px; border-bottom: 1px solid var(--border); font-size: 14px; }}
    tr:last-child td {{ border-bottom: none; }}
    .avatar-table {{ width: 45px; height: 45px; border-radius: 50%; object-fit: cover; background: #334155; border: 1px solid var(--border); }}
    .status-pill {{ padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; }}
    .active {{ background: #065f46; color: #34d399; }}
    .inactive {{ background: #7f1d1d; color: #f87171; }}
    /* FORMS */
    input, select {{
      background: #0f172a; border: 1px solid var(--border); color: white;
      padding: 12px; width: 100%; margin-bottom: 15px; border-radius: 8px;
      font-size: 14px; outline: none; transition: border 0.2s;
    }}
    input:focus, select:focus {{ border-color: var(--emerald); }}
    label {{ display: block; color: #94a3b8; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }}
    .btn-emerald {{ background: var(--emerald); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; transition: 0.3s; font-size: 14px; }}
    .btn-emerald:hover {{ background: #059669; }}
    .btn-blue {{ color: #3b82f6; background: none; border: none; cursor: pointer; font-weight: bold; font-size: 13px; padding: 4px 8px; }}
    .btn-blue:hover {{ color: #60a5fa; }}
    .btn-red {{ color: #ef4444; background: none; border: none; cursor: pointer; font-weight: bold; font-size: 13px; padding: 4px 8px; }}
    .btn-red:hover {{ color: #f87171; }}
    /* MODAL */
    .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 1000; overflow-y: auto; }}
    .modal-content {{ background: var(--card); width: 500px; margin: 5% auto; padding: 35px; border-radius: 20px; border: 1px solid var(--border); position: relative; }}
    .close-x {{ position: absolute; top: 20px; right: 25px; color: #94a3b8; cursor: pointer; font-size: 24px; line-height: 1; }}
    .close-x:hover {{ color: white; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
    /* PAGINADOR */
    .paginador-ui {{ display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border); }}
    .paginador-ui button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
    /* PERMISOS */
    .check-item {{ background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid var(--border); display: flex; align-items: center; gap: 10px; cursor: pointer; }}
    /* DASHBOARD CARDS */
    .dash-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; margin-top: 30px; }}
    .dash-card {{ background: #0f172a; border: 1px solid var(--border); border-radius: 12px; padding: 25px; text-decoration: none; text-align: center; transition: 0.2s; display: block; }}
    .dash-card:hover {{ border-color: var(--emerald); transform: translateY(-2px); }}
    .dash-card .icon {{ font-size: 36px; margin-bottom: 10px; }}
    .dash-card h3 {{ color: #10b981; margin: 0; font-size: 16px; }}
    /* SEARCH BAR */
    .toolbar {{ display: flex; justify-content: space-between; margin-bottom: 15px; align-items: center; gap: 10px; }}
    .search-input {{ width: 220px; margin-bottom: 0; }}
  </style>
  <script>
    function openM(id) {{ document.getElementById(id).style.display = 'block'; }}
    function closeM(id) {{ document.getElementById(id).style.display = 'none'; }}
 
    async function runCrud(action, table, id, data={{}}) {{
      const res = await fetch('/api/crud', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ action, table, id, data }})
      }});
      const j = await res.json();
      if (j.ok) location.reload();
      else alert("Error: " + (j.error || "Desconocido"));
    }}
 
    function preEdit(id, fields, mId='mEdit') {{
      for (let k in fields) {{
        let el = document.getElementById('ed_' + k);
        if (el) el.value = fields[k];
      }}
      document.getElementById('ed_id').value = id;
      openM(mId);
    }}
 
    /* ---- PAGINADOR ---- */
    let paginaActual = 1;
    const filasPorPagina = 5;
 
    function filtrar(rowClass, nameClass) {{
      const val = (document.getElementById('txtBusca') || {{}}).value || "";
      document.querySelectorAll(rowClass).forEach(row => {{
        const b = row.querySelector(nameClass);
        const text = b ? b.innerText.toUpperCase() : "";
        row.dataset.visible = text.includes(val.toUpperCase()) ? "true" : "false";
      }});
      renderTable(rowClass);
    }}
 
    function renderTable(rowClass) {{
      const filas = Array.from(document.querySelectorAll(rowClass));
      const visibles = filas.filter(r => r.dataset.visible !== "false");
      const total = Math.ceil(visibles.length / filasPorPagina) || 1;
      if (paginaActual > total) paginaActual = total;
      filas.forEach(r => r.style.display = 'none');
      visibles.slice((paginaActual - 1) * filasPorPagina, paginaActual * filasPorPagina)
              .forEach(r => r.style.display = '');
      const info = document.getElementById('infoPagina');
      if (info) info.innerText = `Página ${{paginaActual}} de ${{total}}`;
    }}
 
    function cambiarPagina(delta, rowClass) {{
      paginaActual += delta;
      renderTable(rowClass);
    }}
 
    window.onload = () => {{
      const b = document.getElementById('txtBusca');
      if (b) b.value = "";
      if (document.querySelector('.u-row')) filtrar('.u-row', '.u-name');
      if (document.querySelector('.p-row')) filtrar('.p-row', '.p-name');
      if (document.querySelector('.m-row')) filtrar('.m-row', '.m-name');
    }};
  </script>
</head>
<body>
  {nav}
  <div class="container">{content}</div>
</body>
</html>"""
 
 
# =========================================================
# APLICACIÓN WSGI PRINCIPAL
# =========================================================
def application(environ, start_response):
    path   = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    u_data = verify_jwt(environ)
    conn   = None
    cur    = None
 
    # ----------------------------------------------------------
    # 1. API: GET PERMISOS (matriz)
    # ----------------------------------------------------------
    if path == "/api/get_permisos":
        from urllib.parse import parse_qs
        params  = parse_qs(environ.get('QUERY_STRING', ''))
        idp_raw = params.get('idp', [None])[0]
        res = b'{"ok":false,"perms":[]}'
        if idp_raw:
            conn = conectar_bd(); cur = conn.cursor(dictionary=True)
            try:
                cur.execute("""SELECT idModulo as idm, can_view as v, can_add as a,
                               can_edit as e, can_delete as d
                               FROM perfil_modulo WHERE idPerfil = %s""", (idp_raw,))
                perms = cur.fetchall()
                res = json.dumps({"ok": True, "perms": perms}).encode('utf-8')
            except Exception as e:
                res = json.dumps({"ok": False, "error": str(e)}).encode('utf-8')
            finally:
                cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")])
        return [res]
 
    # ----------------------------------------------------------
    # 2. API: CRUD PRINCIPAL
    # ----------------------------------------------------------
    if path == "/api/crud" and method == "POST":
        raw = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0)))
        p   = json.loads(raw)
        conn = conectar_bd(); cur = conn.cursor()
        try:
            if p['action'] == 'delete':
                cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))
 
            elif p['action'] == 'save':
                if p['table'] == 'usuarios':
                    u_nom = p['data']['u'].strip()
                    cur.execute("SELECT id FROM usuarios WHERE LOWER(strNombreUsuario)=LOWER(%s)", (u_nom,))
                    if cur.fetchone(): raise Exception("El nombre de usuario ya existe")
                    cur.execute("INSERT INTO usuarios (strNombreUsuario, strPwd, idPerfil, strEstado) VALUES (%s,%s,%s,%s)",
                                (u_nom, hash_password(p['data']['p']), p['data']['idp'], p['data']['st']))
 
                elif p['table'] == 'perfiles':
                    nombre = p['data']['n'].strip()
                    cur.execute("SELECT id FROM perfiles WHERE LOWER(strNombrePerfil)=LOWER(%s)", (nombre,))
                    if cur.fetchone(): raise Exception("Ese perfil ya existe")
                    cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (nombre,))
 
                elif p['table'] == 'modulos':
                    m_nom = p['data']['n'].strip()
                    cur.execute("SELECT id FROM modulos WHERE LOWER(strNombreModulo)=LOWER(%s)", (m_nom,))
                    if cur.fetchone(): raise Exception("El módulo ya existe")
                    cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)",
                                (m_nom, p['data']['r'], p['data']['p']))
 
                elif p['table'] == 'permisos':
                    id_p = p['data']['idp']
                    cur.execute("DELETE FROM perfil_modulo WHERE idPerfil=%s", (id_p,))
                    for per in p['data']['perms']:
                        if per['v'] or per['a'] or per['e'] or per['d']:
                            cur.execute("""INSERT INTO perfil_modulo
                                (idPerfil, idModulo, can_view, can_add, can_edit, can_delete)
                                VALUES (%s,%s,%s,%s,%s,%s)""",
                                (id_p, per['idm'], per['v'], per['a'], per['e'], per['d']))
 
            elif p['action'] == 'update':
                if p['table'] == 'usuarios':
                    u_nom = p['data']['u'].strip()
                    cur.execute("SELECT id FROM usuarios WHERE LOWER(strNombreUsuario)=LOWER(%s) AND id!=%s", (u_nom, p['id']))
                    if cur.fetchone(): raise Exception("Ya existe otro usuario con ese nombre")
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s WHERE id=%s",
                                (u_nom, p['data']['idp'], p['data']['st'], p['id']))
 
                elif p['table'] == 'perfiles':
                    nombre = p['data']['n'].strip()
                    cur.execute("SELECT id FROM perfiles WHERE LOWER(strNombrePerfil)=LOWER(%s) AND id!=%s", (nombre, p['id']))
                    if cur.fetchone(): raise Exception("Ya existe otro perfil con ese nombre")
                    cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", (nombre, p['id']))
 
                elif p['table'] == 'modulos':
                    m_nom = p['data']['n'].strip()
                    cur.execute("SELECT id FROM modulos WHERE LOWER(strNombreModulo)=LOWER(%s) AND id!=%s", (m_nom, p['id']))
                    if cur.fetchone(): raise Exception("Ya existe otro módulo con ese nombre")
                    cur.execute("UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s",
                                (m_nom, p['data']['r'], p['data']['p'], p['id']))
 
            conn.commit()
            res = b'{"ok":true}'
        except Exception as e:
            if conn: conn.rollback()
            res = json.dumps({"ok": False, "error": str(e)}).encode()
        finally:
            if cur: cur.close()
            if conn: conn.close()
        start_response("200 OK", [("Content-Type", "application/json")])
        return [res]
 
    # ----------------------------------------------------------
    # 3. LOGIN
    # ----------------------------------------------------------
    if path == "/login":
        error_msg = ""
        if method == "POST":
            form    = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
            usuario = form.getvalue("u", "").strip()
            pwd     = form.getvalue("p", "")
            conn2   = conectar_bd(); cur2 = conn2.cursor(dictionary=True)
            cur2.execute(
                "SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s AND strEstado='Activo'",
                (usuario, hash_password(pwd))
            )
            user = cur2.fetchone()
            cur2.close(); conn2.close()
            if user:
                token = jwt_encode({"u": user["strNombreUsuario"], "id": user["id"], "exp": time.time() + 86400})
                start_response("303 See Other", [
                    ("Location", "/dashboard"),
                    ("Set-Cookie", f"token={token}; Path=/; HttpOnly")
                ])
                return [b""]
            else:
                error_msg = "<p style='color:#ef4444; text-align:center; margin-bottom:15px;'>⚠️ Usuario o contraseña incorrectos</p>"
 
        login_html = f"""
        <div style="min-height:80vh; display:flex; align-items:center; justify-content:center;">
          <div class="card" style="width:400px;">
            <div style="text-align:center; margin-bottom:30px;">
              <div style="font-size:56px; margin-bottom:10px;">🏥</div>
              <h2 style="color:#10b981; margin:0 0 5px;">Clínica</h2>
              <p style="color:#94a3b8; font-size:14px; margin:0;">Sistema de Gestión Médica</p>
            </div>
            {error_msg}
            <form method="POST" action="/login">
              <label>Usuario</label>
              <input name="u" placeholder="Nombre de usuario" autocomplete="username">
              <label>Contraseña</label>
              <input name="p" type="password" placeholder="Contraseña" autocomplete="current-password">
              <button type="submit" class="btn-emerald" style="margin-top:5px;">INICIAR SESIÓN</button>
            </form>
          </div>
        </div>"""
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [render_layout("Login - Clínica", login_html).encode("utf-8")]
 
    # ----------------------------------------------------------
    # 4. LOGOUT
    # ----------------------------------------------------------
    if path == "/logout":
        start_response("303 See Other", [
            ("Location", "/login"),
            ("Set-Cookie", "token=; Path=/; Max-Age=0")
        ])
        return [b""]
 
    # ----------------------------------------------------------
    # 5. PROTECCIÓN DE SESIÓN — redirige si no hay JWT válido
    # ----------------------------------------------------------
    if not u_data:
        start_response("303 See Other", [("Location", "/login")])
        return [b""]
 
    # ----------------------------------------------------------
    # Conexión para pantallas protegidas
    # ----------------------------------------------------------
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    content = ""
 
    # ----------------------------------------------------------
    # 6. DASHBOARD
    # ----------------------------------------------------------
    if path in ("/", "/dashboard"):
        content = f"""
        <div class="card">
          <h2 style="margin-top:0;">🏠 Bienvenido, {u_data['u']}</h2>
          <p style="color:#94a3b8;">Selecciona una sección del menú para comenzar.</p>
          <div class="dash-grid">
            <a href="/usuarios" class="dash-card">
              <div class="icon">👥</div><h3>Usuarios</h3>
            </a>
            <a href="/perfiles" class="dash-card">
              <div class="icon">👤</div><h3>Perfiles</h3>
            </a>
            <a href="/modulos" class="dash-card">
              <div class="icon">📦</div><h3>Módulos</h3>
            </a>
            <a href="/permisos" class="dash-card">
              <div class="icon">🔐</div><h3>Permisos</h3>
            </a>
          </div>
        </div>"""
 
    # ----------------------------------------------------------
    # 7. USUARIOS
    # ----------------------------------------------------------
    elif path == "/usuarios":
        cur.execute("SELECT u.*, p.strNombrePerfil FROM usuarios u LEFT JOIN perfiles p ON u.idPerfil=p.id")
        usuarios = cur.fetchall()
        rows = "".join([f"""
        <tr class='u-row'>
          <td><img src='https://ui-avatars.com/api/?name={u['strNombreUsuario']}&background=random' class='avatar-table'></td>
          <td><b class='u-name'>{u['strNombreUsuario']}</b></td>
          <td>{u.get('strNombrePerfil','—')}</td>
          <td><span class='status-pill {"active" if u["strEstado"]=="Activo" else "inactive"}'>{u['strEstado']}</span></td>
          <td>
            <button class='btn-blue' onclick='preEdit({u["id"]}, {{u:"{u["strNombreUsuario"]}", idp:{u["idPerfil"]}, st:"{u["strEstado"]}"}}, "mEdit")'>Editar</button>
            <button class='btn-red' onclick="runCrud('delete','usuarios',{u['id']})">Borrar</button>
          </td>
        </tr>""" for u in usuarios])

        cur.execute("SELECT * FROM perfiles")
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in cur.fetchall()])

        content = f"""
        <div class='card'>
          <h2 style="margin-top:0;">👥 Gestión de Usuarios</h2>
          <div class='toolbar'>
            <button class='btn-emerald' style='width:auto' onclick="openM('mNew')">+ NUEVO USUARIO</button>
            <input type='text' id='txtBusca' class='search-input'
              onkeyup="paginaActual=1; filtrar('.u-row','.u-name');" placeholder='🔍 Buscar...'>
          </div>
          <table>
            <thead><tr><th>IMG</th><th>USUARIO</th><th>PERFIL</th><th>ESTADO</th><th>ACCIONES</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
          <div class='paginador-ui'>
            <button class='btn-blue' onclick="cambiarPagina(-1,'.u-row')">❮ Anterior</button>
            <span id='infoPagina' style='color:var(--emerald); font-weight:bold;'></span>
            <button class='btn-blue' onclick="cambiarPagina(1,'.u-row')">Siguiente ❯</button>
          </div>
        </div>

        <div id='mNew' class='modal'><div class='modal-content'>
          <span class='close-x' onclick="closeM('mNew')">&times;</span>
          <h3>Nuevo Usuario</h3>
          <div class='grid-2'>
            <div><label>Nombre (Solo letras)</label>
                 <input id='un' maxlength='15' onkeypress="return /^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]+$/.test(event.key)"></div>
            <div><label>Pass (5-8 carac.)</label>
                 <input id='up' type='password' maxlength='8'></div>
            <div><label>Correo (@gmail.com)</label>
                 <input id='uc' type='email' placeholder='ejemplo@gmail.com'></div>
            <div><label>Teléfono (10 dígitos)</label>
                 <input id='ut' maxlength='10' onkeypress="return /^[0-9]+$/.test(event.key)"></div>
            <div><label>Perfil</label><select id='un_idp'>{p_opts}</select></div>
            <div><label>Estado</label><select id='un_st'><option>Activo</option><option>Inactivo</option></select></div>
          </div>
          <button class='btn-emerald' onclick='validateAndSave()'>GUARDAR USUARIO</button>
        </div></div>

        <div id='mEdit' class='modal'><div class='modal-content'>
          <span class='close-x' onclick="closeM('mEdit')">&times;</span>
          <h3>Editar Usuario</h3>
          <input type='hidden' id='ed_id'>
          <div class='grid-2'>
            <div><label>Usuario</label>
                 <input id='ed_u' onkeypress="return /^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]+$/.test(event.key)"></div>
            <div><label>Perfil</label><select id='ed_idp'>{p_opts}</select></div>
            <div><label>Estado</label><select id='ed_st'><option>Activo</option><option>Inactivo</option></select></div>
          </div>
          <button class='btn-emerald' onclick='updateUser()'>ACTUALIZAR</button>
        </div></div>

        <script>
          function validateAndSave() {{
            const u = document.getElementById('un').value.trim();
            const p = document.getElementById('up').value;
            const c = document.getElementById('uc').value.trim();
            const t = document.getElementById('ut').value.trim();
            
            if (!u||!p||!c||!t) return alert("⚠️ Todos los campos son obligatorios");
            if (!/^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]+$/.test(u)) return alert("⚠️ El nombre solo puede contener letras");
            if (p.length < 5 || p.length > 8) return alert("⚠️ La contraseña debe tener entre 5 y 8 caracteres");
            if (!c.toLowerCase().endsWith("@gmail.com")) return alert("⚠️ El correo debe ser @gmail.com");
            if (!/^\d{{10}}$/.test(t)) return alert("⚠️ El teléfono debe tener exactamente 10 dígitos numéricos");
            
            runCrud('save','usuarios',0,{{ u, p, idp:document.getElementById('un_idp').value, st:document.getElementById('un_st').value }});
          }}
          
          function updateUser() {{
            const u = document.getElementById('ed_u').value.trim();
            if (!u) return alert("⚠️ El nombre es obligatorio");
            if (!/^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]+$/.test(u)) return alert("⚠️ El nombre solo puede contener letras");

            runCrud('update','usuarios', document.getElementById('ed_id').value, {{
              u: u,
              idp: document.getElementById('ed_idp').value,
              st: document.getElementById('ed_st').value
            }});
          }}
        </script>"""
 
    # ----------------------------------------------------------
    # 8. PERFILES
    # ----------------------------------------------------------
    elif path == "/perfiles":
        cur.execute("SELECT * FROM perfiles ORDER BY id ASC")
        perfiles = cur.fetchall()
        rows = "".join([f"""
        <tr class='p-row'>
          <td>{i}</td>
          <td><b class='p-name'>{p['strNombrePerfil']}</b></td>
          <td>
            <button class='btn-blue' onclick='preEdit({p["id"]}, {{n:"{p["strNombrePerfil"]}"}}, "mEditP")'>Editar</button>
            <button class='btn-red' onclick="runCrud('delete','perfiles',{p['id']})">Borrar</button>
          </td>
        </tr>""" for i, p in enumerate(perfiles, 1)])

        content = f"""
        <div class='card'>
          <h2 style="margin-top:0;">👤 Gestión de Perfiles</h2>
          <div class='toolbar'>
            <button class='btn-emerald' style='width:auto' onclick="openM('mNewP')">+ NUEVO PERFIL</button>
            <input type='text' id='txtBusca' class='search-input'
              onkeyup="paginaActual=1; filtrar('.p-row','.p-name');" placeholder='🔍 Buscar...'>
          </div>
          <table>
            <thead><tr><th>#</th><th>NOMBRE</th><th>ACCIONES</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
          <div class='paginador-ui'>
            <button class='btn-blue' onclick="cambiarPagina(-1,'.p-row')">❮ Anterior</button>
            <span id='infoPagina' style='color:var(--emerald); font-weight:bold;'></span>
            <button class='btn-blue' onclick="cambiarPagina(1,'.p-row')">Siguiente ❯</button>
          </div>
        </div>

        <div id='mNewP' class='modal'><div class='modal-content'>
          <span class='close-x' onclick="closeM('mNewP')">&times;</span>
          <h3>Nuevo Perfil</h3>
          <label>Nombre del Perfil (Solo letras, máx 15)</label>
          <input id='pn' maxlength='15' placeholder='Ej: Administrador' onkeypress="return /^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]+$/.test(event.key)">
          <button class='btn-emerald' onclick='savePerfil()'>GUARDAR</button>
        </div></div>

        <div id='mEditP' class='modal'><div class='modal-content'>
          <span class='close-x' onclick="closeM('mEditP')">&times;</span>
          <h3>Editar Perfil</h3>
          <input type='hidden' id='ed_id'>
          <label>Nombre</label>
          <input id='ed_n' maxlength='15' onkeypress="return /^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]+$/.test(event.key)">
          <button class='btn-emerald' onclick='updatePerfil()'>ACTUALIZAR</button>
        </div></div>

        <script>
          function savePerfil() {{
            const n = document.getElementById('pn').value.trim();
            if (!n) return alert("⚠️ Nombre obligatorio");
            if (n.length > 15) return alert("⚠️ Máximo 15 caracteres");
            runCrud('save','perfiles',0,{{n}});
          }}
          function updatePerfil() {{
            const n = document.getElementById('ed_n').value.trim();
            if (!n) return alert("⚠️ Nombre obligatorio");
            runCrud('update','perfiles', document.getElementById('ed_id').value, {{n}});
          }}
        </script>"""
        
    # ----------------------------------------------------------
    # 9. MÓDULOS
    # ----------------------------------------------------------
    elif path == "/modulos":
        cur.execute("SELECT * FROM modulos ORDER BY id ASC")
        modulos = cur.fetchall()
        rows = "".join([f"""
        <tr class='m-row'>
          <td><b class='m-name'>{m['strNombreModulo']}</b></td>
          <td><code style='color:#94a3b8; font-size:12px;'>{m['strRuta']}</code></td>
          <td>{m['strMenuPadre']}</td>
          <td>
            <button class='btn-blue' onclick='preEdit({m["id"]}, {{n:"{m["strNombreModulo"]}", p:"{m["strMenuPadre"]}"}}, "mEditM")'>Editar</button>
            <button class='btn-red' onclick="runCrud('delete','modulos',{m['id']})">Borrar</button>
          </td>
        </tr>""" for m in modulos])

        content = f"""
        <div class='card'>
          <h2 style="margin-top:0;">📦 Gestión de Módulos</h2>
          <div class='toolbar'>
            <button class='btn-emerald' style='width:auto' onclick="openM('mNewM')">+ NUEVO MÓDULO</button>
            <input type='text' id='txtBusca' class='search-input'
              onkeyup="paginaActual=1; filtrar('.m-row','.m-name');" placeholder='🔍 Buscar...'>
          </div>
          <table>
            <thead><tr><th>NOMBRE</th><th>RUTA</th><th>PADRE</th><th>ACCIONES</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
          <div class='paginador-ui'>
            <button class='btn-blue' onclick="cambiarPagina(-1,'.m-row')">❮ Anterior</button>
            <span id='infoPagina' style='color:var(--emerald); font-weight:bold;'></span>
            <button class='btn-blue' onclick="cambiarPagina(1,'.m-row')">Siguiente ❯</button>
          </div>
        </div>

        <div id='mNewM' class='modal'><div class='modal-content'>
          <span class='close-x' onclick="closeM('mNewM')">&times;</span>
          <h3>Nuevo Módulo</h3>
          <label>Nombre del Módulo (Letras, Números y Puntos, máx 20)</label>
          <input id='mn' maxlength='20' onkeypress="return /^[a-zA-Z0-9.ñÑáéíóúÁÉÍÓÚ ]+$/.test(event.key)">
          <label>Menú Padre</label>
          <select id='mp'><option>Principal 1</option><option>Principal 2</option></select>
          <button class='btn-emerald' onclick='saveMod()'>GUARDAR</button>
        </div></div>

        <div id='mEditM' class='modal'><div class='modal-content'>
          <span class='close-x' onclick="closeM('mEditM')">&times;</span>
          <h3>Editar Módulo</h3>
          <input type='hidden' id='ed_id'>
          <label>Nombre</label>
          <input id='ed_n_mod' maxlength='20' onkeypress="return /^[a-zA-Z0-9.ñÑáéíóúÁÉÍÓÚ ]+$/.test(event.key)">
          <label>Menú Padre</label>
          <select id='ed_p_mod'><option>Principal 1</option><option>Principal 2</option></select>
          <button class='btn-emerald' onclick='updateMod()'>ACTUALIZAR</button>
        </div></div>

        <script>
          function saveMod() {{
            const n = document.getElementById('mn').value.trim();
            if (!n) return alert("⚠️ Nombre obligatorio");
            // Generar ruta automática (limpiando puntos para la URL)
            const r = "/" + n.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '');
            runCrud('save','modulos',0,{{ n, r, p: document.getElementById('mp').value }});
          }}
          function updateMod() {{
            const id = document.getElementById('ed_id').value;
            const n  = document.getElementById('ed_n_mod').value.trim();
            const p  = document.getElementById('ed_p_mod').value;
            if (!n) return alert("⚠️ Nombre obligatorio");
            const r = "/" + n.toLowerCase().replace(/\s+/g, '-').replace(/\./g, '');
            runCrud('update','modulos', id, {{ n, r, p }});
          }}
        </script>"""
 
    # ----------------------------------------------------------
    # 10. PERMISOS
    # ----------------------------------------------------------
    elif path == "/permisos":
        cur.execute("SELECT id, strNombrePerfil FROM perfiles")
        perfiles = cur.fetchall()
        mods_fijos = [
            {'id': -1, 'nm': 'Perfiles',  'p': 'Seguridad'},
            {'id': -2, 'nm': 'Módulos',   'p': 'Seguridad'},
            {'id': -3, 'nm': 'Usuarios',  'p': 'Seguridad'},
            {'id': -4, 'nm': 'Permisos',  'p': 'Seguridad'},
        ]
        cur.execute("SELECT id, strNombreModulo as nm, strMenuPadre as p FROM modulos")
        todos_mods = mods_fijos + cur.fetchall()
 
        p_opts = "".join([f"<option value='{p['id']}'>{p['strNombrePerfil']}</option>" for p in perfiles])
        rows   = "".join([f"""
        <tr class='perm-row' data-visible='true'>
          <td><b class='perm-name'>{m['nm']}</b><br><small style='color:#94a3b8;'>{m['p']}</small></td>
          <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m["id"]}' id='v_{m["id"]}' style='width:auto; margin:0;'></td>
          <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m["id"]}' id='a_{m["id"]}' style='width:auto; margin:0;'></td>
          <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m["id"]}' id='e_{m["id"]}' style='width:auto; margin:0;'></td>
          <td style='text-align:center'><input type='checkbox' class='perm-check' data-mod='{m["id"]}' id='d_{m["id"]}' style='width:auto; margin:0;'></td>
        </tr>""" for m in todos_mods])
 
        content = f"""
        <div class='card'>
          <h2 style="margin-top:0;">🛡️ Matriz de Permisos</h2>
          <label>Selecciona un Perfil</label>
          <select id='sel_perfil' onchange='cargarPermisos(this.value)'
            style='border:2px solid var(--emerald); max-width:350px;'>
            <option value=''>-- Seleccione un perfil --</option>{p_opts}
          </select>
 
          <div id='area_permisos' style='display:none; margin-top:25px;'>
            <div class='toolbar'>
              <div style='display:flex; gap:10px;'>
                <button class='btn-blue' onclick='bulk(true)' style='width:auto'>☑ Todo</button>
                <button class='btn-red'  onclick='bulk(false)' style='width:auto'>☐ Nada</button>
              </div>
              <input type='text' id='txtBusca' class='search-input'
                onkeyup="paginaActual=1; filtrar('.perm-row','.perm-name');" placeholder='🔍 Buscar módulo...'>
            </div>
            <table>
              <thead><tr><th>MÓDULO</th><th>VER</th><th>AGREGAR</th><th>EDITAR</th><th>ELIMINAR</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
            <div class='paginador-ui'>
              <button class='btn-blue' onclick="cambiarPagina(-1,'.perm-row')">❮ Anterior</button>
              <span id='infoPagina' style='color:var(--emerald); font-weight:bold;'></span>
              <button class='btn-blue' onclick="cambiarPagina(1,'.perm-row')">Siguiente ❯</button>
            </div>
            <button class='btn-emerald' style='margin-top:20px; font-size:16px;' onclick='guardarPermisos()'>
              💾 GUARDAR CONFIGURACIÓN
            </button>
          </div>
        </div>
 
        <script>
          async function cargarPermisos(idp) {{
            if (!idp) {{ document.getElementById('area_permisos').style.display='none'; return; }}
            document.querySelectorAll('.perm-check').forEach(c => c.checked = false);
            const res  = await fetch('/api/get_permisos?idp=' + idp);
            const data = await res.json();
            if (data.ok) {{
              data.perms.forEach(p => {{
                const vEl = document.getElementById('v_' + p.idm);
                const aEl = document.getElementById('a_' + p.idm);
                const eEl = document.getElementById('e_' + p.idm);
                const dEl = document.getElementById('d_' + p.idm);
                if (vEl && p.v) vEl.checked = true;
                if (aEl && p.a) aEl.checked = true;
                if (eEl && p.e) eEl.checked = true;
                if (dEl && p.d) dEl.checked = true;
              }});
              document.getElementById('area_permisos').style.display = 'block';
              paginaActual = 1;
              filtrar('.perm-row', '.perm-name');
            }}
          }}
          function bulk(v) {{
            document.querySelectorAll('.perm-row').forEach(row => {{
              if (row.style.display !== 'none')
                row.querySelectorAll('.perm-check').forEach(c => c.checked = v);
            }});
          }}
          function guardarPermisos() {{
            const idp = document.getElementById('sel_perfil').value;
            if (!idp) return alert("Selecciona un perfil primero");
            const ids = [...new Set(Array.from(document.querySelectorAll('.perm-check')).map(c => c.dataset.mod))];
            const matrix = ids.map(id => ({{
              idm: parseInt(id),
              v: document.getElementById('v_' + id).checked ? 1 : 0,
              a: document.getElementById('a_' + id).checked ? 1 : 0,
              e: document.getElementById('e_' + id).checked ? 1 : 0,
              d: document.getElementById('d_' + id).checked ? 1 : 0
            }}));
            runCrud('save', 'permisos', 0, {{ idp, perms: matrix }});
          }}
        </script>"""
 
    # ----------------------------------------------------------
    # Cierre de BD y respuesta
    # ----------------------------------------------------------
    if cur:  cur.close()
    if conn: conn.close()
 
    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
    return [render_layout("Clínica", content, u_data).encode("utf-8")]