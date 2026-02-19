# -*- coding: utf-8 -*-
import psycopg2
import base64
import imghdr
import urllib.request
import urllib.parse
import json
import cgi
import re
from urllib.parse import parse_qs
from datetime import datetime, date, timedelta

DATABASE_URL = "postgresql://neondb_owner:npg_V1CwlGHBK4Og@ep-crimson-recipe-ai9g12ym-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    headers = [('Content-Type', 'text/html; charset=utf-8')]

    # -------------------- helpers --------------------
    def navegacion():
        return """
<nav style="background:#343a40;padding:15px;margin:20px auto 30px;border-radius:5px;max-width:1100px;">
  <a href="/" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Inicio</a>
  <a href="/calculadora" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Calculadora</a>
  <a href="/formulario" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Formulario</a>
  <a href="/carrusel" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Carrusel</a>
  <a href="/nombre_recaptcha" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Registro</a>
  <a href="/crud_personas" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">CRUD Personas</a>
  <a href="/simular_404" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Simular 404</a>
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

    def limpiar_espacios(nombre):
        return " ".join((nombre or "").strip().split())

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
  <style>
    body{font-family:Arial;margin:0;background:#f8f9fa;}
    .container{max-width:1000px;margin:0 auto 40px;background:white;padding:40px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.1);}
    h1{text-align:center;margin-top:0;}
    .ok{background:#d4edda;color:#155724;padding:12px;border-radius:6px;margin:15px 0;}
    .bad{background:#f8d7da;color:#721c24;padding:12px;border-radius:6px;margin:15px 0;}
    .info{background:#e7f3ff;color:#0b4f9c;padding:12px;border-radius:6px;margin:15px 0;border-left:4px solid #007bff;}
    input,textarea{width:95%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;font-size:16px;}
    button{padding:12px;border:none;border-radius:6px;font-weight:bold;cursor:pointer;}
    .btn-primary{background:#28a745;color:white;width:100%;}
    .btn-blue{background:#007bff;color:white;width:100%;}
    .btn-danger{background:#dc3545;color:white;}
    .btn-danger:hover{background:#c82333;}
    .btn-small{padding:8px 10px;border-radius:6px;font-size:14px;}
    hr{margin:30px 0;border:none;border-top:2px solid #eee;}
    table{width:100%;border-collapse:collapse;}
    th,td{padding:10px;border-bottom:1px solid #eee;text-align:left;}
    th{background:#f8f9fa;}
    .row-actions{display:flex;gap:8px;flex-wrap:wrap;}
    @media(max-width:768px){
      .row-actions{flex-direction:column;align-items:stretch;}
      a.btn-small, button.btn-small{width:100%;}
      input,textarea{width:100%;}
    }
  </style>
</head>
<body>
__NAV__
<div class="container">
__BODY__
</div>
</body>
</html>""".replace("__TITLE__", title).replace("__NAV__", navegacion()).replace("__BODY__", body_html)

    # =========================================================
    # INICIO
    # =========================================================
    if path == "/" and method == "GET":
        body = """
<h1>Aplicación</h1>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:25px;">
  <div style="background:#e9ecef;padding:18px;border-radius:10px;text-align:center;">
    <h3>CRUD Personas</h3>
    <a href="/crud_personas">Ir →</a>
  </div>
</div>
"""
        html = page("Inicio", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # ✅ CRUD PERSONAS (nombre, email, fecha_nacimiento)
    # - nombre: solo letras
    # - fecha: no permite hoy ni futuras (max=ayer)
    # - editar / eliminar
    # - PRG
    # =========================================================
    if path == "/crud_personas":
        mensaje = ""
        hoy = date.today()
        max_fecha = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")  # ayer

        edit_id = None
        edit_nombre = ""
        edit_email = ""
        edit_fecha = ""

        # modo edición por query ?edit=ID
        try:
            qs = environ.get("QUERY_STRING", "") or ""
            q = parse_qs(qs)
            if "edit" in q and q["edit"]:
                edit_id = (q["edit"][0] or "").strip()
        except:
            edit_id = None

        # POST (guardar/actualizar/eliminar/borrar todo)
        if method == "POST":
            try:
                content_length = int(environ.get("CONTENT_LENGTH", "0") or "0")
                post_data = environ["wsgi.input"].read(content_length).decode("utf-8") if content_length > 0 else ""
                params = parse_qs(post_data)

                # borrar todo
                if (params.get("borrar_todo", [""])[0] or "").strip() == "1":
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
                        cur.execute("DELETE FROM personas_crud")
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/crud_personas')] + headers)
                    return [b""]

                # eliminar
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

                    start_response("303 See Other", [('Location', '/crud_personas')] + headers)
                    return [b""]

                # guardar / actualizar
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
                    # validación básica (html ya valida, pero server también)
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

                    start_response("303 See Other", [('Location', '/crud_personas')] + headers)
                    return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        # si está editando, cargar datos
        if edit_id:
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

        # listado
        listado_html = ""
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
                cur.execute("SELECT id, nombre, email, fecha_nacimiento, fecha FROM personas_crud ORDER BY fecha DESC LIMIT 200")
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    trs = ""
                    for (pid, nom, em, fn, fec) in rows:
                        trs += """
<tr>
  <td>{id}</td>
  <td>{nom}</td>
  <td>{em}</td>
  <td>{fn}</td>
  <td><small>{fec}</small></td>
  <td>
    <div class="row-actions">
      <a class="btn-small" style="background:#007bff;color:white;text-decoration:none;" href="/crud_personas?edit={id}">Editar</a>
      <form method="POST" style="margin:0;" onsubmit="return confirm('¿Eliminar este registro?');">
        <input type="hidden" name="eliminar_id" value="{id}">
        <button class="btn-small btn-danger" type="submit">Eliminar</button>
      </form>
    </div>
  </td>
</tr>
""".format(
                            id=str(pid),
                            nom=str(nom),
                            em=str(em),
                            fn=(fn.strftime("%Y-%m-%d") if fn else ""),
                            fec=str(fec)[:16]
                        )

                    listado_html = """
<table>
  <thead>
    <tr>
      <th>ID</th>
      <th>Nombre</th>
      <th>Email</th>
      <th>Fecha nacimiento</th>
      <th>Creado</th>
      <th>Acciones</th>
    </tr>
  </thead>
  <tbody>
    {trs}
  </tbody>
</table>
""".format(trs=trs)
                else:
                    listado_html = "<p>No hay registros aún.</p>"
            except Exception as e:
                listado_html = "<div class='bad'>Error cargando: %s</div>" % str(e)
        else:
            listado_html = "<div class='bad'>No hay conexión a BD</div>"

        titulo_form = "Editar persona" if edit_id else "Agregar persona"
        boton_texto = "Actualizar" if edit_id else "Guardar"
        cancel_edit = ""
        if edit_id:
            cancel_edit = '<div style="text-align:right;margin-top:6px;"><a href="/crud_personas">Cancelar edición</a></div>'

        body = """
<h1>CRUD Personas</h1>
__MENSAJE__

<div class="info">
  <b>Reglas:</b> Nombre solo letras. Fecha no permite hoy ni futuras.
</div>

<div style="background:#f8f9fa;padding:22px;border-radius:10px;">
  <h3>{titulo}</h3>
  <form method="POST">
    <input type="hidden" name="id" value="{eid}">

    <label><b>Nombre</b></label>
    <input name="nombre" placeholder="Ej: Juan Pérez" required value="{enombre}"
           oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">

    <label><b>Email</b></label>
    <input type="email" name="email" placeholder="Ej: correo@dominio.com" required value="{eemail}">

    <label><b>Fecha de nacimiento</b></label>
    <input type="date" name="fecha_nacimiento" max="{maxf}" required value="{efecha}">
    <small>Debe ser anterior a hoy.</small>

    <button class="btn-primary" type="submit">{boton}</button>
  </form>
  {cancel}
</div>

<hr>

<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
  <h3 style="margin:0;">Listado</h3>
  <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros?');" style="margin:0;">
    <input type="hidden" name="borrar_todo" value="1">
    <button class="btn-danger" type="submit">Borrar todo</button>
  </form>
</div>

<div style="background:#fff;padding:15px;border-radius:10px;margin-top:10px;overflow:auto;">
__LISTADO__
</div>
""".replace("__MENSAJE__", mensaje).replace("__LISTADO__", listado_html).format(
            titulo=titulo_form,
            boton=boton_texto,
            eid=str(edit_id or ""),
            enombre=(edit_nombre or "").replace('"', "&quot;"),
            eemail=(edit_email or "").replace('"', "&quot;"),
            efecha=(edit_fecha or "").replace('"', "&quot;"),
            maxf=max_fecha,
            cancel=cancel_edit
        )

        html = page("CRUD Personas", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # SIMULAR 404
    # =========================================================
    if path == "/simular_404":
        body = """
<h1 style="color:#dc3545;font-size:54px;margin-bottom:10px;">404</h1>
<h2>Página no encontrada</h2>
<p>Esta ruta existe, pero responde como <b>404</b> para probar tu pantalla.</p>
<a href="/" style="display:inline-block;margin-top:20px;padding:12px 22px;background:#007bff;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">Volver al Inicio</a>
"""
        html = page("Simular 404", body)
        start_response("404 Not Found", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # 404 REAL
    # =========================================================
    body = """
<h1 style="color:#dc3545;font-size:54px;margin-bottom:10px;">404</h1>
<h2>Página no encontrada</h2>
<p>La ruta solicitada <code>%s</code> no existe.</p>
<a href="/" style="display:inline-block;margin-top:20px;padding:12px 22px;background:#007bff;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">Volver al Inicio</a>
""" % path

    html = page("404", body)
    start_response("404 Not Found", headers)
    return [html.encode("utf-8")
]
