# -*- coding: utf-8 -*-
import psycopg2
import base64
import imghdr
import urllib.request
import urllib.parse
import json
import cgi
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date, timedelta

# URL de tu base de datos
DATABASE_URL = "postgresql://neondb_owner:npg_V1CwlGHBK4Og@ep-crimson-recipe-ai9g12ym-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def conectar_bd():
    try:
        result = urlparse(DATABASE_URL)
        return psycopg2.connect(
            host=result.hostname,
            database=result.path[1:],
            user=result.username,
            password=result.password,
            port=result.port,
            connect_timeout=8,
            sslmode="require"
        )
    except:
        return None

# Lógica de búsqueda por inicial
def buscar_por_inicial(inicial):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            query = "SELECT id, nombre, email, fecha_nacimiento FROM crud_personas WHERE LOWER(nombre) LIKE %s ORDER BY nombre ASC"
            cur.execute(query, (inicial.lower() + '%',))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            return None
    return None

# Función de navegación
def navegacion():
    return """
<nav style="background:#343a40;padding:15px;margin:20px auto 30px;border-radius:10px;max-width:1100px;">
  <a href="/" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Inicio</a>
  <a href="/calculadora" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Calculadora</a>
  <a href="/formulario" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Formulario</a>
  <a href="/carrusel" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Carrusel</a>
  <a href="/nombre_recaptcha" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Registro</a>
  <a href="/crud_personas" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">CRUD Personas</a>
  <a href="/simular_404" style="color:white;margin:0 12px;text-decoration:none;font-weight:bold;">Simular 404</a>
</nav>
"""

# Función para crear la página HTML
def page(title, body_html):
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>__TITLE__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
__NAV__
<div class="container">
__BODY__
</div>
</body>
</html>""".replace("__TITLE__", title).replace("__NAV__", navegacion()).replace("__BODY__", body_html)

# Función para mostrar el CRUD de personas
def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    headers = [('Content-Type', 'text/html; charset=utf-8')]

    # GET: filtros
    qs = parse_qs(environ.get("QUERY_STRING", ""))
    letra_inicial = (qs.get("letra_inicial", [""])[0] or "").strip().lower()

    # Buscar usuarios por inicial
    rows = []
    if letra_inicial:
        rows = buscar_por_inicial(letra_inicial)

    # Crear tabla html
    tbody = ""
    if rows:
        for (pid, nombre, email, fn) in rows:
            tbody += f"""
<tr>
  <td><b>{nombre}</b></td>
  <td>{email}</td>
  <td>{fn}</td>
</tr>
"""
    else:
        tbody = "<tr><td colspan='3' style='color:#64748b;'>No hay registros.</td></tr>"

    # UI filtros
    qesc = letra_inicial

    body = """
<h1>Usuarios</h1>

<div style="margin-top:18px;display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;">
  <form method="GET" style="flex:1;min-width:280px;">
    <div class="pill" style="width:100%;justify-content:space-between;">
      <div style="display:flex;gap:10px;align-items:center;flex:1;">
        <span style="font-size:18px;">🔎</span>
        <input name="letra_inicial" value="__Q__" placeholder="Buscar por inicial..." style="border:none;background:transparent;margin:0;padding:0;box-shadow:none;outline:none;flex:1;">
      </div>
      <button class="iconbtn" type="submit" title="Buscar por inicial">
        ✓
      </button>
    </div>
  </form>
</div>

<div style="margin-top:18px;" class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>NOMBRE</th>
        <th>EMAIL</th>
        <th>FECHA DE NACIMIENTO</th>
      </tr>
    </thead>
    <tbody>
      __TBODY__
    </tbody>
  </table>
</div>
""".replace("__TBODY__", tbody)\
   .replace("__Q__", qesc)

    html = page("CRUD Personas", body)
    start_response("200 OK", headers)
    return [html.encode("utf-8")]