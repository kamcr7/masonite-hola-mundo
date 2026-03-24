# -*- coding: utf-8 -*-
import hashlib, json, hmac, time, urllib.parse, cgi, mysql.connector, os, base64
from http import cookies

# ... (Configuración y funciones JWT iguales) ...

# =========================================================
# MAQUETACIÓN (CON FILTRO DE PERMISOS)
# =========================================================
def render_layout(title, content, user=None):
    nav = ""
    if user:
        conn = conectar_bd(); cur = conn.cursor(dictionary=True)
        # 1. Obtener ID del perfil del usuario logueado
        cur.execute("SELECT idPerfil FROM usuarios WHERE strNombreUsuario=%s", (user['u'],))
        u_info = cur.fetchone()
        pid = u_info['idPerfil'] if u_info else 0

        # 2. Obtener solo los módulos donde tiene permiso de 'Ver'
        cur.execute("""
            SELECT m.* FROM modulos m 
            INNER JOIN permisos p ON m.strNombreModulo = p.nombreModulo 
            WHERE p.idPerfil = %s AND p.permisoVer = 1
        """, (pid,))
        mods_permitidos = cur.fetchall()
        
        # 3. Lista de nombres para los módulos del sistema (Seguridad)
        cur.execute("SELECT nombreModulo FROM permisos WHERE idPerfil=%s AND permisoVer=1", (pid,))
        nombres_ok = [row['nombreModulo'] for row in cur.fetchall()]

        def get_links(padre):
            return "".join([f'<a href="{m["strRuta"]}">📦 {m["strNombreModulo"]}</a>' for m in mods_permitidos if m['strMenuPadre'] == padre])
        
        # Filtro para el menú de Seguridad
        seg_links = ""
        if "Perfiles" in nombres_ok: seg_links += '<a href="/perfiles">👤 Perfiles</a>'
        if "Modulos" in nombres_ok: seg_links += '<a href="/modulos">📦 Modulos</a>'
        if "Usuarios" in nombres_ok: seg_links += '<a href="/usuarios">👥 Usuarios</a>'
        if "Permisos" in nombres_ok: seg_links += '<a href="/permisos">🔐 Permisos</a>'
        
        cur.close(); conn.close()

        nav = f"""<div class="top-nav"><div class="nav-container"><div class="nav-left"><span class="logo">🏥 Clinica</span>
        <a href="/dashboard" class="nav-link">Inicio</a>
        {f'<div class="dropdown"><button class="dropbtn">Seguridad ▾</button><div class="dropdown-content">{seg_links}</div></div>' if seg_links else ''}
        <div class="dropdown"><button class="dropbtn">Principal 1 ▾</button><div class="dropdown-content">{get_links("Principal 1") or '<a>(Vacio)</a>'}</div></div>
        <div class="dropdown"><button class="dropbtn">Principal 2 ▾</button><div class="dropdown-content">{get_links("Principal 2") or '<a>(Vacio)</a>'}</div></div>
        </div><div class="nav-right"><span class="user-pill">{user['u']}</span><a href="/logout" class="btn-salir">Salir</a></div></div></div>"""
   
    return f"""<html><head>... (CSS igual) ...
    <script>
        // NUEVA FUNCIÓN PARA GUARDAR PERMISOS
        async function guardarPermisos(perfilId) {{
            const rows = document.querySelectorAll("tbody tr");
            const data = [];
            rows.forEach(row => {{
                const checks = row.querySelectorAll('input[type="checkbox"]');
                data.append({{
                    mod: row.cells[0].innerText,
                    v: checks[0].checked ? 1 : 0,
                    c: checks[1].checked ? 1 : 0,
                    e: checks[2].checked ? 1 : 0,
                    d: checks[3].checked ? 1 : 0
                }});
            }});
            const res = await fetch('/api/permisos', {{
                method: 'POST',
                body: JSON.stringify({{ pid: perfilId, permisos: data }})
            }});
            if(res.ok) alert("Permisos actualizados con éxito");
        }}
    </script>
    ..."""

# =========================================================
# LOGICA DEL SERVIDOR (ENDPOINT PERMISOS)
# =========================================================
def application(environ, start_response):
    # ... (Login y CRUD igual) ...

    # API PARA GUARDAR PERMISOS
    if path == "/api/permisos" and method == "POST":
        p = json.loads(environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0))))
        conn = conectar_bd(); cur = conn.cursor()
        # Limpiar permisos anteriores del perfil
        cur.execute("DELETE FROM permisos WHERE idPerfil = %s", (p['pid'],))
        # Insertar los nuevos
        for perm in p['permisos']:
            cur.execute("""INSERT INTO permisos (idPerfil, nombreModulo, permisoVer, permisoCrear, permisoEditar, permisoEliminar) 
                           VALUES (%s, %s, %s, %s, %s, %s)""", 
                        (p['pid'], perm['mod'], perm['v'], perm['c'], perm['e'], perm['d']))
        conn.commit(); cur.close(); conn.close()
        start_response("200 OK", [("Content-Type", "application/json")]); return [b'{"ok":true}']

    # VISTA DE PERMISOS (MOSTRAR ESTADOS ACTUALES)
    elif path == "/permisos":
        pid = int(urllib.parse.parse_qs(environ.get('QUERY_STRING','')).get('p',['0'])[0])
        cur.execute("SELECT * FROM perfiles"); perfs = cur.fetchall()
        
        table_html = "<p style='text-align:center; color:#94a3b8;'>Seleccione un perfil.</p>"
        if pid > 0:
            # Traer permisos actuales para marcarlos en la tabla
            cur.execute("SELECT * FROM permisos WHERE idPerfil = %s", (pid,))
            current = {{r['nombreModulo']: r for r in cur.fetchall()}}
            
            cur.execute("SELECT strNombreModulo as n FROM modulos")
            all_m = [{'n':'Perfiles'},{'n':'Usuarios'},{'n':'Modulos'},{'n':'Permisos'}] + cur.fetchall()
            
            m_rows = ""
            for m in all_m:
                c = current.get(m['n'], {{'permisoVer':0,'permisoCrear':0,'permisoEditar':0,'permisoEliminar':0}})
                def ck(val): return "checked" if val else ""
                m_rows += f"""<tr>
                    <td>{m['n']}</td>
                    <td><input type='checkbox' {ck(c['permisoVer'])}></td>
                    <td><input type='checkbox' {ck(c['permisoCrear'])}></td>
                    <td><input type='checkbox' {ck(c['permisoEditar'])}></td>
                    <td><input type='checkbox' {ck(c['permisoEliminar'])}></td>
                </tr>"""

            table_html = f"""
            <div style="text-align:right; margin-bottom:10px;">
                <button id="btnToggleAll" class="btn-emerald" style="background:#334155" onclick="toggleAll()">SELECCIONAR TODO</button>
            </div>
            <table><thead><tr><th>Modulo</th><th>Ver</th><th>Crear</th><th>Editar</th><th>Eliminar</th></tr></thead>
            <tbody>{m_rows}</tbody></table>
            <button class="btn-emerald" style="width:100%; margin-top:20px" onclick="guardarPermisos({pid})">GUARDAR PERMISOS</button>"""