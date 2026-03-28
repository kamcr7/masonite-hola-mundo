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
 
 # --- Línea 36 aproximadamente ---
def generar_navbar(id_perfil):
    conn = conectar_bd(); cur = conn.cursor(dictionary=True)
    # Buscamos módulos donde el perfil tenga permisoVer = 1
    cur.execute("""
        SELECT m.* FROM modulos m 
        JOIN permisos p ON m.strNombreModulo = p.nombreModulo 
        WHERE p.idPerfil = %s AND p.permisoVer = 1
    """, (id_perfil,))
    permitidos = cur.fetchall()
    
    menus = {"Seguridad": "", "Principal 1": "", "Principal 2": ""}
    for m in permitidos:
        padre = m['strMenuPadre']
        if padre in menus:
            menus[padre] += f"<li><a class='dropdown-item' href='{m['strRuta']}'>📦 {m['strNombreModulo']}</a></li>"
    
    cur.close(); conn.close()
    return menus
# =========================================================
# LAYOUT PRINCIPAL (LIGHT MODE CORREGIDO)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        id_p = user.get('pid')
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        
        # 1. Obtenemos los módulos que tienen permiso de VER (permisoVer = 1)
        cur.execute("SELECT nombreModulo FROM permisos WHERE idPerfil=%s AND permisoVer=1", (id_p,))
        permitidos = [r['nombreModulo'].lower() for r in cur.fetchall()]
        
        # 2. Obtenemos todos los módulos para los submenús de Principal 1 y 2
        cur.execute("SELECT * FROM modulos"); all_mods = cur.fetchall()
        cur.close(); conn.close()

        # Función auxiliar para filtrar submenús (Principal 1, Principal 2, etc.)
        def get_links(padre):
            links = []
            for m in all_mods:
                # Solo agregamos el link si el padre coincide Y el usuario tiene permiso de ver ese módulo
                if m['strMenuPadre'] == padre and m['strNombreModulo'].lower() in permitidos:
                    ruta = m["strRuta"] or f"/{m['strNombreModulo'].lower().replace(' ', '-')}"
                    links.append(f'<a href="{ruta}">📦 {m["strNombreModulo"]}</a>')
            return "".join(links)
        
        # 3. Construimos el menú de Seguridad dinámicamente
        seg_items = [
            ("Perfiles", "/perfiles", "👤"),
            ("Módulos",  "/modulos",  "📦"),
            ("Usuarios", "/usuarios", "👥"),
            ("Permisos", "/permisos", "🔐")
        ]
        
        seg_html = ""
        for nom, rut, ico in seg_items:
            if nom.lower() in permitidos:
                seg_html += f'<a href="{rut}">{ico} {nom}</a>'

        # Solo mostramos el botón "Seguridad" si tiene al menos un módulo permitido dentro
        dropdown_seguridad = f"""
        <div class="dropdown">
            <button class="dropbtn">Seguridad ▾</button>
            <div class="dropdown-content">
                {seg_html}
            </div>
        </div>""" if seg_html else ""

        # Construimos Principal 1 y 2
        p1_links = get_links("Principal 1")
        dropdown_p1 = f"""<div class="dropdown"><button class="dropbtn">Principal 1 ▾</button>
                          <div class="dropdown-content">{p1_links}</div></div>""" if p1_links else ""
        
        p2_links = get_links("Principal 2")
        dropdown_p2 = f"""<div class="dropdown"><button class="dropbtn">Principal 2 ▾</button>
                          <div class="dropdown-content">{p2_links}</div></div>""" if p2_links else ""

        nav = f"""
        <div class="top-nav">
          <div class="nav-container">
            <div class="nav-left">
              <span class="logo">🏥 Clinica</span>
              <a href="/dashboard" class="nav-link">Inicio</a>
              {dropdown_seguridad}
              {dropdown_p1}
              {dropdown_p2}
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
      --bg: #f8fafc; 
      --card: #ffffff; 
      --emerald: #10b981;
      --border: #e2e8f0; 
      --text: #1e293b;
      --text-muted: #64748b;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; }}
    
    /* NAV CLARO */
    .top-nav {{ background: #ffffff; height: 60px; border-bottom: 1px solid var(--border); display: flex; align-items: center; position: sticky; top: 0; z-index: 200; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
    .nav-container {{ width: 100%; max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; padding: 0 20px; align-items: center; }}
    .logo {{ color: var(--emerald); font-weight: bold; font-size: 1.2rem; margin-right: 20px; }}
    .nav-link {{ color: var(--text-muted); text-decoration: none; padding: 10px; font-size: 14px; font-weight: 500; }}
    .nav-link:hover {{ color: var(--emerald); }}
    
    .dropdown {{ position: relative; display: inline-block; }}
    .dropdown-content {{ display: none; position: absolute; background: #ffffff; min-width: 180px; border: 1px solid var(--border); border-radius: 12px; z-index: 300; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); top: 100%; left: 0; overflow: hidden; }}
    .dropdown-content a {{ color: var(--text); padding: 12px; text-decoration: none; display: block; border-bottom: 1px solid var(--border); font-size: 14px; }}
    .dropdown-content a:last-child {{ border-bottom: none; }}
    .dropdown-content a:hover {{ background: #f1f5f9; color: var(--emerald); }}
    .dropdown:hover .dropdown-content {{ display: block; }}
    .dropbtn {{ background: transparent; color: var(--text-muted); border: none; padding: 15px; cursor: pointer; font-size: 14px; font-weight: 500; }}
    .dropbtn:hover {{ color: var(--emerald); }}
    
    .user-pill {{ color: var(--emerald); background: #ecfdf5; border: 1px solid #d1fae5; padding: 6px 16px; border-radius: 25px; margin-right: 15px; font-size: 13px; font-weight: bold; }}
    .btn-salir {{ background: #ef4444; color: white; text-decoration: none; padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: bold; transition: 0.2s; }}
    .btn-salir:hover {{ background: #dc2626; }}
    .nav-right {{ display: flex; align-items: center; }}
    
    /* LAYOUT */
    .container {{ padding: 40px; max-width: 1200px; margin: 0 auto; }}
    .card {{ background: var(--card); padding: 30px; border-radius: 16px; border: 1px solid var(--border); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    
    /* TABLE CLARA */
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }}
    th {{ background: #f8fafc; color: var(--text-muted); font-size: 12px; text-transform: uppercase; padding: 15px; text-align: left; border-bottom: 1px solid var(--border); }}
    td {{ padding: 15px; border-bottom: 1px solid var(--border); font-size: 14px; color: var(--text); }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover {{ background: #fcfcfd; }}
    .avatar-table {{ width: 45px; height: 45px; border-radius: 50%; object-fit: cover; background: #f1f5f9; border: 1px solid var(--border); }}
    
    /* PILLS */
    .status-pill {{ padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; }}
    .active {{ background: #dcfce7; color: #166534; }}
    .inactive {{ background: #fee2e2; color: #991b1b; }}
    
    /* FORMS CLAROS */
    input, select {{
      background: #ffffff; border: 1px solid var(--border); color: var(--text);
      padding: 12px; width: 100%; margin-bottom: 15px; border-radius: 8px;
      font-size: 14px; outline: none; transition: all 0.2s;
    }}
    input:focus, select:focus {{ border-color: var(--emerald); box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1); }}
    label {{ display: block; color: var(--text-muted); font-size: 12px; text-transform: uppercase; margin-bottom: 5px; font-weight: 600; }}
    
    .btn-emerald {{ background: var(--emerald); color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; transition: 0.3s; font-size: 14px; }}
    .btn-emerald:hover {{ background: #059669; transform: translateY(-1px); }}
    
    .btn-blue {{ color: #2563eb; background: none; border: none; cursor: pointer; font-weight: bold; font-size: 13px; padding: 4px 8px; }}
    .btn-blue:hover {{ color: #1d4ed8; text-decoration: underline; }}
    .btn-red {{ color: #dc2626; background: none; border: none; cursor: pointer; font-weight: bold; font-size: 13px; padding: 4px 8px; }}
    .btn-red:hover {{ color: #991b1b; text-decoration: underline; }}
    
    /* MODAL CLARO */
    .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(4px); z-index: 1000; overflow-y: auto; }}
    .modal-content {{ background: var(--card); width: 500px; margin: 5% auto; padding: 35px; border-radius: 20px; border: 1px solid var(--border); position: relative; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }}
    .close-x {{ position: absolute; top: 20px; right: 25px; color: var(--text-muted); cursor: pointer; font-size: 24px; line-height: 1; }}
    .close-x:hover {{ color: var(--text); }}
    
    /* DASHBOARD CLARO */
    .dash-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; margin-top: 30px; }}
    .dash-card {{ background: #ffffff; border: 1px solid var(--border); border-radius: 12px; padding: 25px; text-decoration: none; text-align: center; transition: 0.2s; display: block; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
    .dash-card:hover {{ border-color: var(--emerald); transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
    .dash-card .icon {{ font-size: 36px; margin-bottom: 10px; display: block; }}
    .dash-card h3 {{ color: var(--emerald); margin: 0; font-size: 16px; }}
    
    /* SEARCH / TOOLBAR */
    .toolbar {{ display: flex; justify-content: space-between; margin-bottom: 15px; align-items: center; gap: 10px; }}
    .search-input {{ width: 220px; margin-bottom: 0; background: #f1f5f9; }}
    
    .paginador-ui {{ display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border); }}
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
    # 2. API: CRUD PRINCIPAL (REPARADO PARA PERFILES Y MÓDULOS)
    # ----------------------------------------------------------
    if path == "/api/crud" and method == "POST":
        raw = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0)))
        p   = json.loads(raw)
        conn = conectar_bd(); cur = conn.cursor(dictionary=True) 
        
        try:
            # --- VALIDACIÓN DE PERMISOS ---
            if p['action'] != 'save_permisos_matrix':
                id_p = u_data.get('pid')
                mapa = {'save': 'permisoCrear', 'update': 'permisoEditar', 'delete': 'permisoEliminar'}
                col = mapa.get(p['action'])
                if col:
                    nom_mod = p['table'].capitalize()
                    cur.execute(f"SELECT {col} FROM permisos WHERE idPerfil=%s AND nombreModulo=%s", (id_p, nom_mod))
                    p_row = cur.fetchone()
                    if not p_row or not p_row[col]: raise Exception(f"Sin permiso para {p['action']}")

            # --- ACCIONES ---
            if p['action'] == 'delete':
                cur.execute(f"DELETE FROM {p['table']} WHERE id=%s", (p['id'],))

            elif p['action'] == 'save':
                if p['table'] == 'usuarios':
                    u_nom = p['data']['u'].strip()
                    cur.execute("SELECT id FROM usuarios WHERE LOWER(strNombreUsuario)=LOWER(%s)", (u_nom,))
                    if cur.fetchone(): raise Exception("El usuario ya existe")
                    cur.execute("""INSERT INTO usuarios 
                        (strNombreUsuario, strPwd, strCorreo, strTelefono, idPerfil, strEstado, strFoto) 
                        VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (u_nom, hash_password(p['data']['p']), p['data'].get('c',''), 
                         p['data'].get('t',''), p['data']['idp'], p['data']['st'], p['data'].get('img','')))

                elif p['table'] == 'perfiles':
                    # Usamos .get('n') porque Perfiles envía 'n' como nombre
                    cur.execute("INSERT INTO perfiles (strNombrePerfil) VALUES (%s)", (p['data'].get('n', '').strip(),))

                elif p['table'] == 'modulos':
                    # Modulos envía 'n', 'r', 'p'
                    cur.execute("INSERT INTO modulos (strNombreModulo, strRuta, strMenuPadre) VALUES (%s,%s,%s)",
                                (p['data'].get('n','').strip(), p['data'].get('r',''), p['data'].get('p','')))

            elif p['action'] == 'update':
                if p['table'] == 'usuarios':
                    cur.execute("UPDATE usuarios SET strNombreUsuario=%s, idPerfil=%s, strEstado=%s WHERE id=%s",
                                (p['data']['u'].strip(), p['data']['idp'], p['data']['st'], p['id']))

                elif p['table'] == 'perfiles':
                    # Reparado: ahora busca 'n' que es lo que envía el JS de perfiles
                    cur.execute("UPDATE perfiles SET strNombrePerfil=%s WHERE id=%s", 
                                (p['data'].get('n', '').strip(), p['id']))

                elif p['table'] == 'modulos':
                    # Reparado: ahora busca 'n', 'r' y 'p'
                    cur.execute("UPDATE modulos SET strNombreModulo=%s, strRuta=%s, strMenuPadre=%s WHERE id=%s",
                                (p['data'].get('n','').strip(), p['data'].get('r',''), p['data'].get('p',''), p['id']))

            elif p['action'] == 'save_permisos_matrix':
                id_p = p['data']['idp']
                cur.execute("DELETE FROM permisos WHERE idPerfil=%s", (id_p,))
                for per in p['data']['perms']:
                    if per['v'] or per['c'] or per['e'] or per['d']:
                        cur.execute("""INSERT INTO permisos 
                            (idPerfil, nombreModulo, permisoVer, permisoCrear, permisoEditar, permisoEliminar) 
                            VALUES (%s,%s,%s,%s,%s,%s)""",
                            (id_p, per['nom'], per['v'], per['c'], per['e'], per['d']))

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
    # 3. LOGIN (CON DISEÑO DE RECAPTCHA ESTILO GOOGLE)
    # ----------------------------------------------------------
    if path == "/login":
        error_msg = ""
        if method == "POST":
            form = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ)
            usuario = form.getvalue("u", "").strip()
            pwd     = form.getvalue("p", "")
            # Validamos que el captcha haya sido marcado en el cliente
            captcha_val = form.getvalue("captcha_status", "0")

            if captcha_val != "1":
                error_msg = "<p style='color:#ef4444; text-align:center; margin-bottom:10px;'>⚠️ Por favor, verifica que no eres un robot.</p>"
            else:
                conn2 = conectar_bd(); cur2 = conn2.cursor(dictionary=True)
                cur2.execute("SELECT * FROM usuarios WHERE strNombreUsuario=%s AND strPwd=%s AND strEstado='Activo'",
                            (usuario, hash_password(pwd)))
                user_row = cur2.fetchone()
                cur2.close(); conn2.close()
                
                if user_row:
                    token_data = {"u": user_row["strNombreUsuario"], "id": user_row["id"], "pid": user_row["idPerfil"], "exp": time.time() + 86400}
                    token = jwt_encode(token_data)
                    start_response("303 See Other", [("Location", "/dashboard"), ("Set-Cookie", f"token={token}; Path=/; HttpOnly")])
                    return [b""]
                else:
                    error_msg = "<p style='color:#ef4444; text-align:center; margin-bottom:10px;'>⚠️ Usuario o contraseña incorrectos</p>"

        # El contenido HTML manteniendo tu estructura de 'card'
        login_html = f"""
        <style>
            /* Estilos específicos para el widget reCAPTCHA */
            .captcha-container {{
                background: #f9f9f9; border: 1px solid #d3d3d3; border-radius: 3px;
                width: 300px; height: 74px; display: flex; align-items: center;
                padding: 0 12px; margin: 20px auto; font-family: 'Segoe UI', Roboto, sans-serif;
            }}
            .rc-check-box {{
                width: 24px; height: 24px; border: 2px solid #c1c1c1; background: #fff;
                border-radius: 2px; cursor: pointer; transition: all 0.2s;
                display: flex; align-items: center; justify-content: center;
            }}
            .rc-check-box.loading {{
                border-radius: 50%; border: 3px solid #f3f3f3; border-top: 3px solid #4d90fe;
                animation: rc-spin 1s linear infinite; width: 22px; height: 22px;
            }}
            .rc-check-box.checked {{ border: none; background: transparent; }}
            .rc-check-box.checked::after {{
                content: '✔'; color: #00ad45; font-size: 32px; font-weight: bold;
            }}
            .rc-text {{ color: #000; font-size: 14px; margin-left: 12px; flex-grow: 1; user-select: none; }}
            .rc-logo-side {{ text-align: center; line-height: 1; }}
            .rc-logo-side img {{ width: 30px; display: block; margin: 0 auto 2px; }}
            .rc-logo-side span {{ font-size: 8px; color: #555; display: block; }}
            
            @keyframes rc-spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        </style>

        <div style="display:flex; align-items:center; justify-content:center; padding: 40px 0;">
          <div class="card" style="width:100%; max-width:400px;">
            <h2 style="text-align:center; margin-bottom:20px;">Iniciar Sesión</h2>
            {error_msg}
            <form method="POST">
              <label>Usuario</label>
              <input name="u" placeholder="nombre@ejemplo.com" required style="width:100%; margin-bottom:15px;">
              
              <label>Contraseña</label>
              <input name="p" type="password" placeholder="••••••••" required style="width:100%; margin-bottom:10px;">
              
              <div class="captcha-container">
                <div id="check-box" class="rc-check-box" onclick="simularVerificacion()"></div>
                <div class="rc-text">No soy un robot</div>
                <div class="rc-logo-side">
                    <img src="https://www.gstatic.com/recaptcha/api2/logo_48.png" alt="re">
                    <span>reCAPTCHA</span>
                    <span style="color:#777;">Privacidad - Condiciones</span>
                </div>
                <input type="hidden" name="captcha_status" id="captcha_status" value="0">
              </div>

              <button type="submit" class="btn-emerald" style="width:100%; padding:12px;">Entrar</button>
            </form>
          </div>
        </div>

        <script>
            function simularVerificacion() {{
                const box = document.getElementById('check-box');
                const status = document.getElementById('captcha_status');
                
                if(status.value === "1") return; // Evitar repetir

                box.classList.add('loading');
                
                // Simulamos una carga de 1.2 segundos como el real
                setTimeout(() => {{
                    box.classList.remove('loading');
                    box.classList.add('checked');
                    status.value = "1"; // Marcamos como verificado para el backend
                }}, 1200);
            }}
        </script>
        """
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
 
## ----------------------------------------------------------
    # 6. DASHBOARD (ESTILO CORPORATIVO - VERDE ESMERALDA)
    # ----------------------------------------------------------
    if path in ("/", "/dashboard"):
        # Extraemos el nombre del usuario para personalizar la bienvenida
        nombre_usuario = u_data.get('u', 'Usuario')

        content = f"""
        <style>
            .welcome-wrapper {{
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 60vh;
                padding: 20px;
            }}
            /* RECUADRO GIGANTE EN VERDE ESMERALDA */
            .welcome-card-hero {{
                /* Degradado de Verde Esmeralda (oscuro a claro) */
                background: linear-gradient(135deg, #047857 0%, #10b981 100%);
                color: white;
                border-radius: 24px;
                padding: 80px 40px;
                text-align: center;
                width: 100%;
                max-width: 900px;
                box-shadow: 0 25px 50px -12px rgba(4, 120, 87, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .welcome-badge {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.2);
                padding: 8px 20px;
                border-radius: 50px;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 30px;
                backdrop-filter: blur(5px);
                color: white;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .welcome-card-hero h1 {{
                font-size: 3.2rem;
                font-weight: 800;
                margin: 0 0 20px 0;
                text-transform: uppercase;
                letter-spacing: -1px;
                line-height: 1.1;
                color: white;
            }}
            .welcome-card-hero p {{
                font-size: 1.25rem;
                opacity: 0.95;
                max-width: 650px;
                margin: 0 auto;
                line-height: 1.6;
                font-weight: 300;
                color: #ecfdf5; /* Verde muy clarito para el texto secundario */
            }}
            .status-line {{
                margin-top: 50px; 
                opacity: 0.8; 
                font-size: 11px; 
                letter-spacing: 2px; 
                color: #d1fae5;
                text-transform: uppercase;
            }}
        </style>

        <div class="welcome-wrapper">
            <div class="welcome-card-hero">
                <div class="welcome-badge">SISTEMA DE GESTIÓN CLÍNICA v2.0</div>
                
                <h1>BIENVENIDO AL SISTEMA DE ADMINISTRACIÓN</h1>
                
                <p>
                    Hola <strong>{nombre_usuario}</strong>, has ingresado al panel de control central. 
                    Desde aquí podrás gestionar usuarios, configurar la seguridad y supervisar 
                    la estructura modular de la institución con total eficiencia.
                </p>
                
                <div class="status-line">
                    ESTADO DEL SISTEMA: OPERATIVO
                </div>
            </div>
        </div>
        """
 
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
        
        # ----------------------------------------------------------
    # Cierre de BD y respuesta
    # ----------------------------------------------------------
    
    if cur:  cur.close()
    if conn: conn.close()
 
    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
    return [render_layout("Clínica", content, u_data).encode("utf-8")]