# -*- coding: utf-8 -*-
import psycopg2
import urllib.parse
import re
from urllib.parse import parse_qs
from datetime import datetime, date, timedelta

DATABASE_URL = "postgresql://neondb_owner:npg_V1CwlGHBK4Og@ep-crimson-recipe-ai9g12ym-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    headers = [('Content-Type', 'text/html; charset=utf-8')]

    # -------------------- helpers --------------------
    def navegacion():
        return """
<nav style="background:#343a40;padding:15px;margin:20px auto 20px;border-radius:8px;max-width:1200px;">
  <a href="/" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Inicio</a>
  <a href="/crud_personas" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">CRUD Personas</a>
</nav>
"""

    def conectar_bd():
        try:
            return psycopg2.connect(DATABASE_URL, connect_timeout=5)
        except:
            return None

    def validar_nombre_solo_letras(nombre):
        patron = r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$"
        return bool(re.fullmatch(patron, (nombre or "").strip()))

    def limpiar_espacios(txt):
        return " ".join((txt or "").strip().split())

    def parsear_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except:
            return None

    def page(title, body_html):
        return """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>__TITLE__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body{font-family:Arial;margin:0;background:#f5f7fb;color:#111827;}
    .wrap{max-width:1200px;margin:0 auto 50px;padding:0 14px;}
    .card{background:#fff;border:1px solid #e5e7eb;border-radius:14px;box-shadow:0 8px 30px rgba(16,24,40,.06);}
    .container{padding:22px;}
    h1{font-size:32px;margin:0;}
    .ok{background:#d4edda;color:#155724;padding:12px;border-radius:10px;margin:15px 0;border:1px solid #c3e6cb;}
    .bad{background:#fee2e2;color:#991b1b;padding:12px;border-radius:10px;margin:15px 0;border:1px solid #fecaca;}
    .info{background:#eff6ff;color:#1e40af;padding:12px;border-radius:10px;margin:15px 0;border:1px solid #bfdbfe;}
    input,select{width:100%;padding:12px 14px;margin:8px 0;border:1px solid #e5e7eb;border-radius:12px;font-size:15px;outline:none;}
    input:focus{border-color:#93c5fd;box-shadow:0 0 0 4px rgba(59,130,246,.12);}
    button{padding:12px 14px;border:none;border-radius:12px;font-weight:700;cursor:pointer;}
    .btn-primary{background:#4f46e5;color:white;}
    .btn-primary:hover{filter:brightness(.95);}
    .btn-danger{background:#ef4444;color:white;}
    .btn-danger:hover{filter:brightness(.95);}
    .btn-ghost{background:#eef2ff;color:#4f46e5;}
    .btn-ghost:hover{filter:brightness(.97);}
    .btn-pill{border-radius:999px;padding:10px 14px;}
    .btn-sm{padding:9px 12px;border-radius:10px;font-size:14px;}

    /* CRUD UI */
    .header-row{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:18px 22px;border-bottom:1px solid #eef2f7;}
    .searchbar{flex:1;display:flex;justify-content:center;position:relative;}
    .searchbox{
      width:min(680px, 100%);
      background:#fff;
      border:1px solid #e5e7eb;
      border-radius:999px;
      display:flex;
      align-items:center;
      padding:10px 12px;
      gap:10px;
      box-shadow:0 8px 25px rgba(16,24,40,.06);
    }
    .searchbox input{
      border:none;outline:none;margin:0;padding:8px 6px;
      border-radius:999px;background:transparent;
      width:100%;
    }
    .iconbtn{
      width:36px;height:36px;border-radius:999px;
      display:inline-flex;align-items:center;justify-content:center;
      border:1px solid #e5e7eb;background:#fff;cursor:pointer;
    }
    .iconbtn:hover{background:#f9fafb;}

    /* Dropdown filtros */
    .filters{
      position:absolute;
      top:56px;
      left:50%;
      transform:translateX(-50%);
      width:min(680px, 100%);
      background:#fff;
      border:1px solid #e5e7eb;
      border-radius:14px;
      box-shadow:0 20px 45px rgba(16,24,40,.14);
      padding:14px;
      display:none;
      z-index:50;
    }
    .filters.show{display:block;}
    .filters .row{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
    .filters label{font-size:12px;color:#6b7280;font-weight:800;text-transform:uppercase;letter-spacing:.06em;}
    .filters .actions{display:flex;gap:10px;justify-content:flex-end;margin-top:10px;flex-wrap:wrap;}

    table{width:100%;border-collapse:separate;border-spacing:0;}
    thead th{
      text-transform:uppercase;
      font-size:12px;
      letter-spacing:.06em;
      color:#6b7280;
      background:#f9fafb;
      padding:14px 16px;
      border-bottom:1px solid #eef2f7;
    }
    tbody td{
      padding:18px 16px;
      border-bottom:1px solid #eef2f7;
      vertical-align:middle;
    }
    tbody tr:hover{background:#fbfdff;}
    .actions{display:flex;gap:10px;justify-content:flex-start;flex-wrap:wrap;}
    .btn-edit{background:#eef2ff;color:#4f46e5;}
    .btn-edit:hover{filter:brightness(.97);}
    .btn-del{background:#fee2e2;color:#ef4444;}
    .btn-del:hover{filter:brightness(.97);}

    .footerbar{
      display:flex;align-items:center;justify-content:flex-end;gap:10px;
      padding:16px 22px;
    }
    .pagepill{
      background:#eef2f7;border:1px solid #e5e7eb;border-radius:999px;
      padding:10px 14px;font-weight:700;color:#374151;
    }

    /* Modal */
    .modal-backdrop{
      position:fixed;inset:0;background:rgba(17,24,39,.45);
      display:flex;align-items:center;justify-content:center;
      padding:16px;
      z-index:100;
    }
    .modal{
      width:min(760px, 100%);
      background:#fff;border-radius:16px;border:1px solid #e5e7eb;
      box-shadow:0 25px 70px rgba(0,0,0,.2);
      overflow:hidden;
    }
    .modal-head{
      padding:16px 18px;border-bottom:1px solid #eef2f7;
      display:flex;align-items:center;justify-content:space-between;
      gap:10px;
    }
    .modal-title{font-size:20px;font-weight:900;margin:0;}
    .modal-body{padding:18px;}
    .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:10px;}
    .field{display:flex;flex-direction:column;}
    .field label{font-weight:800;margin-top:6px;}
    .hint{color:#6b7280;margin-top:4px;font-size:13px;}
    .modal-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:16px;flex-wrap:wrap;}

    @media(max-width:820px){
      .header-row{flex-direction:column;align-items:stretch;}
      .searchbar{justify-content:stretch;}
      .filters{left:0;transform:none;width:100%;}
      .filters .row{grid-template-columns:1fr;}
      .grid2{grid-template-columns:1fr;}
    }
  </style>
</head>
<body>
__NAV__
<div class="wrap">
__BODY__
</div>

<script>
function toggleFilters(){
  var el = document.getElementById('filtersBox');
  if(!el) return;
  el.classList.toggle('show');
}
document.addEventListener('click', function(e){
  var f = document.getElementById('filtersBox');
  var btn = document.getElementById('filterBtn');
  if(!f) return;
  if(f.classList.contains('show')){
    if(!f.contains(e.target) && btn && !btn.contains(e.target)){
      f.classList.remove('show');
    }
  }
});
</script>
</body>
</html>""".replace("__TITLE__", title).replace("__NAV__", navegacion()).replace("__BODY__", body_html)

    # =========================================================
    # INICIO
    # =========================================================
    if path == "/" and method == "GET":
        body = """
<div class="card">
  <div class="container">
    <h1>Aplicación</h1>
    <div style="margin-top:18px;">
      <a class="btn-pill btn-primary" style="text-decoration:none;display:inline-block;" href="/crud_personas">Ir a CRUD Personas</a>
    </div>
  </div>
</div>
"""
        html = page("Inicio", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CRUD PERSONAS + FILTRO FECHAS
    # =========================================================
    if path == "/crud_personas":
        hoy = date.today()
        max_fecha = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")

        qs = environ.get("QUERY_STRING", "") or ""
        q = parse_qs(qs)

        edit_id = (q.get("edit", [""])[0] or "").strip()
        open_modal = (q.get("new", [""])[0] or "").strip() == "1" or bool(edit_id)

        # paginación + filtros
        per_page = 5
        try:
            page_num = int((q.get("p", ["1"])[0] or "1"))
            if page_num < 1: page_num = 1
        except:
            page_num = 1

        search = limpiar_espacios(q.get("q", [""])[0] if q.get("q") else "")

        desde_str = (q.get("from", [""])[0] or "").strip()
        hasta_str = (q.get("to", [""])[0] or "").strip()
        desde = parsear_fecha(desde_str) if desde_str else None
        hasta = parsear_fecha(hasta_str) if hasta_str else None

        # si vienen invertidas, intercambia
        if desde and hasta and desde > hasta:
            tmp = desde
            desde = hasta
            hasta = tmp
            desde_str = desde.strftime("%Y-%m-%d")
            hasta_str = hasta.strftime("%Y-%m-%d")

        mensaje = ""
        edit_nombre = ""
        edit_email = ""
        edit_fecha = ""

        # POST: guardar/editar/eliminar (NO BORRA BD salvo delete 1)
        if method == "POST":
            try:
                content_length = int(environ.get("CONTENT_LENGTH", "0") or "0")
                post_data = environ["wsgi.input"].read(content_length).decode("utf-8") if content_length > 0 else ""
                params = parse_qs(post_data)

                # eliminar 1
                eliminar_id = (params.get("eliminar_id", [""])[0] or "").strip()
                if eliminar_id:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS personas_crud (
                              id SERIAL PRIMARY KEY,
                              nombre VARCHAR(120) NOT NULL,
                              email VARCHAR(160) NOT NULL,
                              fecha_nacimiento DATE NOT NULL,
                              fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        cur.execute("DELETE FROM personas_crud WHERE id=%s", (eliminar_id,))
                        conn.commit()
                        cur.close()
                        conn.close()

                    loc = "/crud_personas?p=%s&q=%s&from=%s&to=%s" % (
                        str(page_num),
                        urllib.parse.quote(search),
                        urllib.parse.quote(desde_str),
                        urllib.parse.quote(hasta_str)
                    )
                    start_response("303 See Other", [('Location', loc)] + headers)
                    return [b""]

                # guardar/editar
                pid = (params.get("id", [""])[0] or "").strip()
                nombre_raw = (params.get("nombre", [""])[0] or "")
                nombre = limpiar_espacios(nombre_raw)
                email = (params.get("email", [""])[0] or "").strip()
                fecha_str = (params.get("fecha_nacimiento", [""])[0] or "").strip()

                errores = []
                if not nombre:
                    errores.append("Nombre es requerido")
                elif not validar_nombre_solo_letras(nombre):
                    errores.append("Nombre solo debe tener letras y espacios")

                if not email:
                    errores.append("Email es requerido")
                else:
                    if "@" not in email or "." not in email.split("@")[-1]:
                        errores.append("Email inválido")

                fecha_nac = None
                if not fecha_str:
                    errores.append("Fecha de nacimiento es requerida")
                else:
                    fecha_nac = parsear_fecha(fecha_str)
                    if not fecha_nac:
                        errores.append("Fecha inválida")
                    else:
                        if fecha_nac >= hoy:
                            errores.append("La fecha no puede ser hoy ni una futura")

                if errores:
                    mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                    open_modal = True
                    edit_id = pid or edit_id
                    edit_nombre = nombre
                    edit_email = email
                    edit_fecha = fecha_str
                else:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS personas_crud (
                              id SERIAL PRIMARY KEY,
                              nombre VARCHAR(120) NOT NULL,
                              email VARCHAR(160) NOT NULL,
                              fecha_nacimiento DATE NOT NULL,
                              fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        if pid:
                            cur.execute(
                                "UPDATE personas_crud SET nombre=%s, email=%s, fecha_nacimiento=%s WHERE id=%s",
                                (nombre, email, fecha_nac, pid)
                            )
                        else:
                            cur.execute(
                                "INSERT INTO personas_crud (nombre, email, fecha_nacimiento) VALUES (%s,%s,%s)",
                                (nombre, email, fecha_nac)
                            )
                        conn.commit()
                        cur.close()
                        conn.close()

                    loc = "/crud_personas?p=%s&q=%s&from=%s&to=%s" % (
                        str(page_num),
                        urllib.parse.quote(search),
                        urllib.parse.quote(desde_str),
                        urllib.parse.quote(hasta_str)
                    )
                    start_response("303 See Other", [('Location', loc)] + headers)
                    return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)
                open_modal = True

        # cargar datos al editar
        if edit_id and not edit_nombre:
            conn = conectar_bd()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS personas_crud (
                          id SERIAL PRIMARY KEY,
                          nombre VARCHAR(120) NOT NULL,
                          email VARCHAR(160) NOT NULL,
                          fecha_nacimiento DATE NOT NULL,
                          fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cur.execute("SELECT nombre, email, fecha_nacimiento FROM personas_crud WHERE id=%s", (edit_id,))
                    row = cur.fetchone()
                    cur.close()
                    conn.close()
                    if row:
                        edit_nombre = row[0] or ""
                        edit_email = row[1] or ""
                        edit_fecha = (row[2].strftime("%Y-%m-%d") if row[2] else "")
                except:
                    pass

        # construir WHERE dinámico (nombre + rango fechas)
        where = []
        args = []
        if search:
            where.append("nombre ILIKE %s")
            args.append("%" + search + "%")
        if desde:
            where.append("fecha_nacimiento >= %s")
            args.append(desde)
        if hasta:
            where.append("fecha_nacimiento <= %s")
            args.append(hasta)

        where_sql = (" WHERE " + " AND ".join(where)) if where else ""

        total = 0
        rows = []
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS personas_crud (
                      id SERIAL PRIMARY KEY,
                      nombre VARCHAR(120) NOT NULL,
                      email VARCHAR(160) NOT NULL,
                      fecha_nacimiento DATE NOT NULL,
                      fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("SELECT COUNT(*) FROM personas_crud" + where_sql, tuple(args))
                total = int(cur.fetchone()[0] or 0)

                total_pages = max(1, (total + per_page - 1) // per_page)
                if page_num > total_pages:
                    page_num = total_pages

                offset = (page_num - 1) * per_page
                cur.execute("""
                    SELECT id, nombre, email, fecha_nacimiento
                    FROM personas_crud
                    {where}
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                """.format(where=where_sql), tuple(args + [per_page, offset]))

                rows = cur.fetchall()
                cur.close()
                conn.close()
            except:
                rows = []
                total_pages = 1
        else:
            mensaje = "<div class='bad'>No hay conexión a BD</div>"
            total_pages = 1

        # tabla
        trs = ""
        for (pid, nom, em, fn) in rows:
            trs += """
<tr>
  <td><b>{nom}</b></td>
  <td>{em}</td>
  <td>{fn}</td>
  <td>
    <div class="actions">
      <a class="btn-sm btn-edit" style="text-decoration:none;" href="/crud_personas?edit={id}&p={p}&q={q}&from={fr}&to={to}">Editar</a>
      <form method="POST" style="margin:0" onsubmit="return confirm('¿Eliminar este usuario?');">
        <input type="hidden" name="eliminar_id" value="{id}">
        <button class="btn-sm btn-del" type="submit">Eliminar</button>
      </form>
    </div>
  </td>
</tr>
""".format(
                id=str(pid),
                nom=str(nom),
                em=str(em),
                fn=(fn.strftime("%Y-%m-%d") if fn else ""),
                p=str(page_num),
                q=urllib.parse.quote(search),
                fr=urllib.parse.quote(desde_str),
                to=urllib.parse.quote(hasta_str)
            )
        if not trs:
            trs = "<tr><td colspan='4' style='padding:18px;color:#6b7280;'>No hay usuarios con ese filtro.</td></tr>"

        # paginación links conservando filtros
        base_q = "q=%s&from=%s&to=%s" % (urllib.parse.quote(search), urllib.parse.quote(desde_str), urllib.parse.quote(hasta_str))
        if page_num > 1:
            prev_link = '<a class="iconbtn" title="Anterior" style="text-decoration:none;" href="/crud_personas?p=%s&%s">‹</a>' % (str(page_num-1), base_q)
        else:
            prev_link = '<span class="iconbtn" style="opacity:.35;cursor:not-allowed;">‹</span>'

        if page_num < total_pages:
            next_link = '<a class="iconbtn" title="Siguiente" style="text-decoration:none;" href="/crud_personas?p=%s&%s">›</a>' % (str(page_num+1), base_q)
        else:
            next_link = '<span class="iconbtn" style="opacity:.35;cursor:not-allowed;">›</span>'

        # modal
        modal_html = ""
        if open_modal:
            titulo = "Editar usuario" if edit_id else "Nuevo usuario"
            btn = "Actualizar" if edit_id else "Guardar"
            cancel_url = "/crud_personas?p=%s&%s" % (str(page_num), base_q)
            modal_html = """
<div class="modal-backdrop" onclick="if(event.target===this) window.location.href='{cancel}';">
  <div class="modal">
    <div class="modal-head">
      <div class="modal-title">{titulo}</div>
      <a href="{cancel}" class="iconbtn" style="text-decoration:none;">✕</a>
    </div>
    <div class="modal-body">
      {msg}
      <form method="POST" autocomplete="off">
        <input type="hidden" name="id" value="{eid}">

        <div class="grid2">
          <div class="field">
            <label>Nombre</label>
            <input name="nombre" placeholder="Ej: Alan" required value="{enombre}"
              oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">
          </div>
          <div class="field">
            <label>Email</label>
            <input type="email" name="email" placeholder="correo@dominio.com" required value="{eemail}">
          </div>
        </div>

        <div class="field" style="margin-top:6px;">
          <label>Fecha de nacimiento</label>
          <input type="date" name="fecha_nacimiento" max="{maxf}" required value="{efecha}">
          <div class="hint">Debe ser anterior a hoy.</div>
        </div>

        <div class="modal-actions">
          <a class="btn-pill btn-ghost" style="text-decoration:none;" href="{cancel}">Cancelar</a>
          <button class="btn-pill btn-primary" type="submit">{btn}</button>
        </div>
      </form>
    </div>
  </div>
</div>
""".format(
                titulo=titulo,
                btn=btn,
                eid=(edit_id or ""),
                enombre=(edit_nombre or "").replace('"', "&quot;"),
                eemail=(edit_email or "").replace('"', "&quot;"),
                efecha=(edit_fecha or "").replace('"', "&quot;"),
                maxf=max_fecha,
                cancel=cancel_url,
                msg=(mensaje or "")
            )

        # UI principal
        body = """
<div class="card">
  <div class="header-row">
    <h1>Usuarios</h1>

    <div class="searchbar">
      <form class="searchbox" method="GET" action="/crud_personas">
        <span style="font-size:18px;">🔎</span>
        <input name="q" value="{q}" placeholder="Buscar por nombre o apellidos..." />
        <input type="hidden" name="p" value="1">
        <button id="filterBtn" class="iconbtn" title="Filtros" type="button" onclick="toggleFilters()">⏷</button>
        <a class="iconbtn" title="Limpiar" style="text-decoration:none;" href="/crud_personas">🧹</a>

        <div id="filtersBox" class="filters">
          <div class="row">
            <div class="field">
              <label>Fecha desde</label>
              <input type="date" name="from" value="{fr}">
            </div>
            <div class="field">
              <label>Fecha hasta</label>
              <input type="date" name="to" value="{to}">
            </div>
          </div>
          <div class="actions">
            <a class="btn-pill btn-ghost" style="text-decoration:none;" href="/crud_personas">Limpiar filtros</a>
            <button class="btn-pill btn-primary" type="submit">Aplicar</button>
          </div>
        </div>
      </form>
    </div>

    <a class="btn-pill btn-primary" style="text-decoration:none;display:inline-flex;align-items:center;gap:8px;"
       href="/crud_personas?new=1&p={p}&q={qenc}&from={frenc}&to={toenc}">
       <span style="font-size:18px;">＋</span> Nuevo
    </a>
  </div>

  <div class="container">
    {alert}

    <div style="overflow:auto;border-radius:14px;border:1px solid #eef2f7;">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Email</th>
            <th>Fecha de nacimiento</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {trs}
        </tbody>
      </table>
    </div>
  </div>

  <div class="footerbar">
    {prev}
    <div class="pagepill">Página {p} de {tp}</div>
    {next}
  </div>
</div>

{modal}
""".format(
            trs=trs,
            p=str(page_num),
            tp=str(total_pages),
            prev=prev_link,
            next=next_link,
            q=(search or "").replace('"', "&quot;"),
            qenc=urllib.parse.quote(search),
            fr=(desde_str or ""),
            to=(hasta_str or ""),
            frenc=urllib.parse.quote(desde_str),
            toenc=urllib.parse.quote(hasta_str),
            modal=modal_html,
            alert=(mensaje if (mensaje and not open_modal) else "")
        )

        html = page("CRUD Personas", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # 404
    # =========================================================
    body = """
<div class="card">
  <div class="container" style="text-align:center;">
    <h1 style="color:#ef4444;font-size:54px;margin-bottom:10px;">404</h1>
    <h2>Página no encontrada</h2>
    <p>La ruta solicitada <code>%s</code> no existe.</p>
    <a href="/" style="display:inline-block;margin-top:20px;padding:12px 22px;background:#4f46e5;color:white;text-decoration:none;border-radius:12px;font-weight:bold;">Volver al Inicio</a>
  </div>
</div>
""" % path

    html = page("404", body)
    start_response("404 Not Found", headers)
    return [html.encode("utf-8")]
