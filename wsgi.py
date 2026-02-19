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

# ✅ TU BD (Neon)
DATABASE_URL = "postgresql://neondb_owner:npg_V1CwlGHBK4Og@ep-crimson-recipe-ai9g12ym-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# ✅ keys de prueba (no production)
RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    headers = [('Content-Type', 'text/html; charset=utf-8')]

    # -------------------- helpers --------------------
    def navegacion():
        return """
<nav style="background:#343a40;padding:15px;margin:20px auto 20px;border-radius:8px;max-width:1200px;">
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
            # Neon acepta directo el DSN
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

    def calcular_edad(fecha_nac):
        if not fecha_nac:
            return None
        hoy = date.today()
        return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))

    def validar_recaptcha(recaptcha_response):
        try:
            url = "https://www.google.com/recaptcha/api/siteverify"
            data = urllib.parse.urlencode({
                "secret": RECAPTCHA_SECRET_KEY,
                "response": recaptcha_response
            }).encode("utf-8")
            req = urllib.request.Request(url, data=data)
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode("utf-8"))
            return bool(result.get("success", False))
        except:
            return False

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
    h1{font-size:32px;margin:0;text-align:left;}
    h2,h3{margin:0 0 10px;}
    .ok{background:#d4edda;color:#155724;padding:12px;border-radius:10px;margin:15px 0;border:1px solid #c3e6cb;}
    .bad{background:#fee2e2;color:#991b1b;padding:12px;border-radius:10px;margin:15px 0;border:1px solid #fecaca;}
    .info{background:#eff6ff;color:#1e40af;padding:12px;border-radius:10px;margin:15px 0;border:1px solid #bfdbfe;}
    input,textarea,select{width:100%;padding:12px 14px;margin:8px 0;border:1px solid #e5e7eb;border-radius:12px;font-size:15px;outline:none;box-sizing:border-box;}
    input:focus,textarea:focus,select:focus{border-color:#93c5fd;box-shadow:0 0 0 4px rgba(59,130,246,.12);}
    button{padding:12px 14px;border:none;border-radius:12px;font-weight:700;cursor:pointer;}
    .btn-primary{background:#4f46e5;color:white;}
    .btn-primary:hover{filter:brightness(.95);}
    .btn-blue{background:#2563eb;color:white;}
    .btn-blue:hover{filter:brightness(.95);}
    .btn-danger{background:#ef4444;color:white;}
    .btn-danger:hover{filter:brightness(.95);}
    .btn-ghost{background:#eef2ff;color:#4f46e5;}
    .btn-ghost:hover{filter:brightness(.97);}
    .btn-pill{border-radius:999px;padding:10px 14px;}
    .btn-sm{padding:9px 12px;border-radius:10px;font-size:14px;}
    hr{margin:26px 0;border:none;border-top:1px solid #eef2f7;}

    /* ========= CRUD UI (similar al ejemplo) ========= */
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

    /* old container look for other pages */
    .simple-box{background:#fff;border:1px solid #e5e7eb;border-radius:14px;box-shadow:0 8px 30px rgba(16,24,40,.06);padding:22px;}
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
<div style="
  background:linear-gradient(135deg, rgba(79,70,229,.10), rgba(37,99,235,.06));
  border:1px solid #e5e7eb;
  border-radius:18px;
  padding:22px;
  margin-top:6px;
">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
    <div>
      <h1 style="margin:0;font-size:34px;">Aplicación</h1>
      <p style="margin:6px 0 0;color:#6b7280;">Elige una sección para continuar.</p>
    </div>

    <div style="
      display:flex;gap:10px;align-items:center;flex-wrap:wrap;
      background:#ffffffcc;border:1px solid #e5e7eb;border-radius:999px;
      padding:10px 12px;
    ">
      <span style="font-size:18px;">🚀</span>
      <span style="font-weight:800;color:#374151;">Acceso rápido</span>
      <a href="/crud_personas" style="
        text-decoration:none;
        background:#4f46e5;color:#fff;
        padding:10px 14px;border-radius:999px;
        font-weight:800;
        display:inline-flex;gap:8px;align-items:center;
      ">Ir a CRUD Personas →</a>
    </div>
  </div>

  <div style="
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
    gap:16px;
    margin-top:18px;
  ">

    <!-- Card -->
    <a href="/calculadora" style="text-decoration:none;color:inherit;">
      <div style="
        background:#fff;
        border:1px solid #eef2f7;
        border-radius:16px;
        padding:16px;
        box-shadow:0 12px 35px rgba(16,24,40,.06);
        transition:transform .12s ease, box-shadow .12s ease, border-color .12s ease;
      " class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="
              width:44px;height:44px;border-radius:14px;
              background:#eef2ff;border:1px solid #e0e7ff;
              display:flex;align-items:center;justify-content:center;
              font-size:20px;
            ">🧮</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Calculadora</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Suma y división con validación</div>
            </div>
          </div>
          <div style="color:#4f46e5;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/formulario" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#ecfeff;border:1px solid #cffafe;display:flex;align-items:center;justify-content:center;font-size:20px;">📝</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Formulario</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Imagen + fecha válida + correo</div>
            </div>
          </div>
          <div style="color:#2563eb;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/carrusel" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#fff7ed;border:1px solid #ffedd5;display:flex;align-items:center;justify-content:center;font-size:20px;">🖼️</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Carrusel</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Sube y administra imágenes</div>
            </div>
          </div>
          <div style="color:#f97316;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/nombre_recaptcha" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#f0fdf4;border:1px solid #dcfce7;display:flex;align-items:center;justify-content:center;font-size:20px;">✅</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Registro</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">reCAPTCHA + máximo 30 letras</div>
            </div>
          </div>
          <div style="color:#16a34a;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/crud_personas" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #eef2f7;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#eef2ff;border:1px solid #e0e7ff;display:flex;align-items:center;justify-content:center;font-size:20px;">👤</div>
            <div>
              <div style="font-weight:900;font-size:18px;">CRUD Personas</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Alta, edición, borrado + filtros</div>
            </div>
          </div>
          <div style="color:#4f46e5;font-weight:900;">→</div>
        </div>
      </div>
    </a>

    <a href="/simular_404" style="text-decoration:none;color:inherit;">
      <div style="background:#fff;border:1px solid #fee2e2;border-radius:16px;padding:16px;box-shadow:0 12px 35px rgba(16,24,40,.06);" class="homecard">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
          <div style="display:flex;gap:12px;align-items:center;">
            <div style="width:44px;height:44px;border-radius:14px;background:#fee2e2;border:1px solid #fecaca;display:flex;align-items:center;justify-content:center;font-size:20px;">⚠️</div>
            <div>
              <div style="font-weight:900;font-size:18px;">Simular 404</div>
              <div style="color:#6b7280;font-size:13px;margin-top:2px;">Prueba tu pantalla de error</div>
            </div>
          </div>
          <div style="color:#ef4444;font-weight:900;">→</div>
        </div>
      </div>
    </a>

  </div>
</div>

<style>
.homecard:hover{
  transform:translateY(-2px);
  box-shadow:0 18px 48px rgba(16,24,40,.10);
  border-color:#dbeafe;
}
</style>
"""
    html = page("Inicio", body)
    start_response("200 OK", headers)
    return [html.encode("utf-8")]

    # =========================================================
    # CALCULADORA (solo números)
    # =========================================================
    if path == "/calculadora":
        resultado_suma = ""
        resultado_div = ""

        if method == "POST":
            try:
                content_length = int(environ.get("CONTENT_LENGTH", "0") or "0")
                post_data = environ["wsgi.input"].read(content_length).decode("utf-8") if content_length > 0 else ""
                params = parse_qs(post_data)

                try:
                    num1 = float(params.get("suma1", [""])[0])
                    num2 = float(params.get("suma2", [""])[0])
                    resultado_suma = "<div class='ok'>Resultado: %s + %s = %s</div>" % (num1, num2, (num1 + num2))
                except:
                    resultado_suma = "<div class='bad'>Ingresa SOLO números válidos para la suma</div>"

                try:
                    num3 = float(params.get("div1", [""])[0])
                    num4 = float(params.get("div2", [""])[0])
                    if num4 == 0:
                        resultado_div = "<div class='bad'>No se puede dividir entre cero</div>"
                    else:
                        resultado_div = "<div class='ok'>Resultado: %s ÷ %s = %.2f</div>" % (num3, num4, (num3 / num4))
                except:
                    resultado_div = "<div class='bad'>Ingresa SOLO números válidos para la división</div>"
            except Exception as e:
                resultado_suma = "<div class='bad'>Error: %s</div>" % str(e)

        body = """
<div class="simple-box">
  <h1>Calculadora</h1>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:14px;">
    <div style="background:#f9fafb;padding:16px;border-radius:14px;border:1px solid #eef2f7;">
      <h3>Suma</h3>
      <form method="POST">
        <input type="number" step="any" name="suma1" placeholder="10" required>
        <input type="number" step="any" name="suma2" placeholder="5" required>
        <button class="btn-blue" type="submit" style="width:100%;">Calcular</button>
      </form>
      __SUMA__
    </div>

    <div style="background:#f9fafb;padding:16px;border-radius:14px;border:1px solid #eef2f7;">
      <h3>División</h3>
      <form method="POST">
        <input type="number" step="any" name="div1" placeholder="10" required>
        <input type="number" step="any" name="div2" placeholder="2" required>
        <button class="btn-blue" type="submit" style="width:100%;">Calcular</button>
      </form>
      __DIV__
    </div>
  </div>
</div>
<style>
@media(max-width:768px){
  .simple-box > div[style*="grid-template-columns:1fr 1fr"]{grid-template-columns:1fr !important;}
}
</style>
""".replace("__SUMA__", resultado_suma).replace("__DIV__", resultado_div)

        html = page("Calculadora", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # FORMULARIO + PRG
    # =========================================================
    if path == "/formulario":
        mensaje = ""
        hoy = date.today()
        max_fecha = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

                # borrar todo
                if (fs.getvalue("borrar_todo") or "").strip() == "1":
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS formulario_simple (id SERIAL PRIMARY KEY, nombre VARCHAR(100), fecha_nacimiento DATE, correo VARCHAR(120), imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("DELETE FROM formulario_simple")
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/formulario')] + headers)
                    return [b""]

                nombre = (fs.getvalue("nombre") or "").strip()
                fecha_str = (fs.getvalue("fecha_nacimiento") or "").strip()
                correo = (fs.getvalue("correo") or "").strip()
                correo2 = (fs.getvalue("correo_confirmar") or "").strip()

                errores = []
                if not nombre:
                    errores.append("Nombre es requerido")
                elif not validar_nombre_solo_letras(nombre):
                    errores.append("Nombre solo debe tener letras y espacios")

                fecha_nac = None
                if not fecha_str:
                    errores.append("Fecha de nacimiento es requerida")
                else:
                    fecha_nac = parsear_fecha(fecha_str)
                    if not fecha_nac:
                        errores.append("Fecha de nacimiento inválida")
                    else:
                        if fecha_nac >= hoy:
                            errores.append("La fecha de nacimiento no puede ser la de hoy ni una futura")

                if not correo:
                    errores.append("Correo es requerido")
                elif correo != correo2:
                    errores.append("Los correos no coinciden")

                imagen_data = None
                imagen_nombre = ""
                imagen_tipo = ""

                if "imagen" not in fs:
                    errores.append("Debe subir una imagen")
                else:
                    imagen_file = fs["imagen"]
                    if not getattr(imagen_file, "filename", ""):
                        errores.append("Debe subir una imagen")
                    else:
                        imagen_nombre = imagen_file.filename
                        imagen_data = imagen_file.file.read()
                        imagen_tipo = imghdr.what(None, h=imagen_data) or "desconocido"
                        if len(imagen_data) > 5 * 1024 * 1024:
                            errores.append("La imagen es demasiado grande (máximo 5MB)")
                        if imagen_tipo not in ["jpeg", "jpg", "png", "gif"]:
                            errores.append("Solo JPG, PNG o GIF")

                if errores:
                    mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                else:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS formulario_simple (id SERIAL PRIMARY KEY, nombre VARCHAR(100), fecha_nacimiento DATE, correo VARCHAR(120), imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute(
                            "INSERT INTO formulario_simple (nombre, fecha_nacimiento, correo, imagen_nombre, imagen_tipo, imagen_data) VALUES (%s,%s,%s,%s,%s,%s)",
                            (nombre, fecha_nac, correo, imagen_nombre, imagen_tipo, psycopg2.Binary(imagen_data))
                        )
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/formulario')] + headers)
                    return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        registros_html = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS formulario_simple (id SERIAL PRIMARY KEY, nombre VARCHAR(100), fecha_nacimiento DATE, correo VARCHAR(120), imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                cur.execute("SELECT nombre, fecha_nacimiento, correo, fecha FROM formulario_simple ORDER BY fecha DESC LIMIT 10")
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    items = ""
                    for (n, fn, c, f) in rows:
                        edad = calcular_edad(fn)
                        items += "<div style='background:#fff;padding:12px;border-radius:12px;margin:10px 0;border:1px solid #eef2f7;'><b>%s</b> — Edad: %s — %s<br><small style='color:#6b7280'>%s</small></div>" % (n, edad, c, str(f)[:16])
                    registros_html = """
<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
  <h3 style="margin:0;">Registros guardados</h3>
  <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros del formulario?');" style="margin:0;">
    <input type="hidden" name="borrar_todo" value="1">
    <button class="btn-danger btn-sm" type="submit">Borrar registros</button>
  </form>
</div>
<div style="background:#f9fafb;padding:15px;border-radius:14px;margin-top:10px;border:1px solid #eef2f7;">
__ITEMS__
</div>
""".replace("__ITEMS__", items)
                else:
                    registros_html = "<p>No hay registros aún.</p>"
            except Exception as e:
                registros_html = "<div class='bad'>Error cargando registros: %s</div>" % str(e)
        else:
            registros_html = "<div class='bad'>No hay conexión a BD</div>"

        body = """
<div class="simple-box">
  <h1>Formulario</h1>
  __MENSAJE__

  <form method="POST" enctype="multipart/form-data">
    <label><b>Nombre</b></label>
    <input name="nombre" placeholder="Nombre" required oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">

    <label><b>Fecha de nacimiento</b></label>
    <input type="date" name="fecha_nacimiento" max="__MAX__" required>
    <small style="color:#6b7280;">Debe ser anterior a hoy.</small>

    <label><b>Correo</b></label>
    <input type="email" name="correo" placeholder="Correo" required>

    <label><b>Confirmar correo</b></label>
    <input type="email" name="correo_confirmar" placeholder="Confirmar correo" required>

    <label><b>Imagen</b></label>
    <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>

    <button class="btn-primary" style="width:100%;" type="submit">Guardar</button>
  </form>

  <hr>
  __REGS__
</div>
""".replace("__MENSAJE__", mensaje).replace("__REGS__", registros_html).replace("__MAX__", max_fecha)

        html = page("Formulario", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # REGISTRO + PRG + MAX 30 LETRAS
    # =========================================================
    if path == "/nombre_recaptcha":
        mensaje = ""

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

                if (fs.getvalue("borrar_todo") or "").strip() == "1":
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS nombres_recaptcha (id SERIAL PRIMARY KEY, nombre VARCHAR(30), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("DELETE FROM nombres_recaptcha")
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/nombre_recaptcha')] + headers)
                    return [b""]

                nombre_raw = (fs.getvalue("nombre") or "")
                nombre = limpiar_espacios(nombre_raw)
                rec = (fs.getvalue("g-recaptcha-response") or "").strip()

                errores = []
                if not nombre:
                    errores.append("Debes escribir un nombre para poder agregar.")
                else:
                    if not validar_nombre_solo_letras(nombre):
                        errores.append("Nombre solo debe tener letras y espacios")
                    if len(nombre) > 30:
                        errores.append("Solo se permiten 30 letras máximo.")

                if not rec:
                    errores.append("Completa el reCAPTCHA")
                elif not validar_recaptcha(rec):
                    errores.append("reCAPTCHA inválido")

                if errores:
                    mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                else:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS nombres_recaptcha (id SERIAL PRIMARY KEY, nombre VARCHAR(30), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("INSERT INTO nombres_recaptcha (nombre) VALUES (%s)", (nombre[:30],))
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/nombre_recaptcha')] + headers)
                    return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        lista = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS nombres_recaptcha (id SERIAL PRIMARY KEY, nombre VARCHAR(30), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                cur.execute("SELECT nombre, fecha FROM nombres_recaptcha ORDER BY fecha DESC LIMIT 15")
                rows = cur.fetchall()
                cur.close()
                conn.close()
                if rows:
                    lista = "<ul>" + "".join("<li><b>%s</b> <small style='color:#6b7280'>(%s)</small></li>" % (n, str(f)[:16]) for (n, f) in rows) + "</ul>"
                else:
                    lista = "<p>No hay nombres aún.</p>"
            except Exception as e:
                lista = "<div class='bad'>Error cargando: %s</div>" % str(e)
        else:
            lista = "<div class='bad'>No hay conexión a BD</div>"

        body = """
<div class="simple-box">
  <h1>Registro</h1>
  <div class="info">Máximo 30 letras.</div>
  __MENSAJE__

  <script src="https://www.google.com/recaptcha/api.js" async defer></script>

  <form method="POST">
    <label><b>Nombre</b></label>
    <input name="nombre" placeholder="Nombre" required maxlength="30"
           oninput="this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\\s]/g,'')">

    <div style="background:#f9fafb;padding:15px;border-radius:14px;margin:15px 0;text-align:center;border:1px solid #eef2f7;">
      <div class="g-recaptcha" data-sitekey="__SITEKEY__"></div>
    </div>

    <button class="btn-primary" style="width:100%;" type="submit">Guardar</button>
  </form>

  <hr>

  <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
    <h3 style="margin:0;">Nombres ingresados (últimos 15)</h3>
    <form method="POST" onsubmit="return confirm('¿Borrar TODOS los registros de Registro?');" style="margin:0;">
      <input type="hidden" name="borrar_todo" value="1">
      <button class="btn-danger btn-sm" type="submit">Borrar registros</button>
    </form>
  </div>

  <div style="background:#f9fafb;padding:15px;border-radius:14px;margin-top:10px;border:1px solid #eef2f7;">
    __LISTA__
  </div>
</div>
""".replace("__MENSAJE__", mensaje).replace("__LISTA__", lista).replace("__SITEKEY__", RECAPTCHA_SITE_KEY)

        html = page("Registro", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # SIMULAR 404
    # =========================================================
    if path == "/simular_404":
        body = """
<div class="simple-box" style="text-align:center;">
  <h1 style="color:#ef4444;font-size:54px;margin-bottom:10px;">404</h1>
  <h2>Página no encontrada</h2>
  <p style="color:#6b7280;">Esta ruta existe, pero responde como <b>404</b> para probar tu pantalla.</p>
  <a href="/" class="btn-pill btn-blue" style="display:inline-block;text-decoration:none;">Volver al Inicio</a>
</div>
"""
        html = page("Simular 404", body)
        start_response("404 Not Found", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CARRUSEL + PRG
    # =========================================================
    if path == "/carrusel":
        mensaje = ""

        if method == "POST":
            try:
                fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

                eliminar_id = (fs.getvalue("eliminar_id") or "").strip()
                if eliminar_id:
                    conn = conectar_bd()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("CREATE TABLE IF NOT EXISTS carrusel_imagenes (id SERIAL PRIMARY KEY, imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        cur.execute("DELETE FROM carrusel_imagenes WHERE id=%s", (eliminar_id,))
                        conn.commit()
                        cur.close()
                        conn.close()

                    start_response("303 See Other", [('Location', '/carrusel')] + headers)
                    return [b""]

                if "imagen" not in fs:
                    mensaje = "<div class='bad'>Debes seleccionar una imagen</div>"
                else:
                    img_file = fs["imagen"]
                    if not getattr(img_file, "filename", ""):
                        mensaje = "<div class='bad'>Debes seleccionar una imagen</div>"
                    else:
                        img_nombre = img_file.filename
                        img_data = img_file.file.read()
                        img_tipo = imghdr.what(None, h=img_data) or "desconocido"

                        errores = []
                        if len(img_data) > 5 * 1024 * 1024:
                            errores.append("Máximo 5MB")
                        if img_tipo not in ["jpeg", "jpg", "png", "gif"]:
                            errores.append("Solo JPG, PNG o GIF")

                        if errores:
                            mensaje = "<div class='bad'><ul>%s</ul></div>" % "".join("<li>%s</li>" % e for e in errores)
                        else:
                            conn = conectar_bd()
                            if conn:
                                cur = conn.cursor()
                                cur.execute("CREATE TABLE IF NOT EXISTS carrusel_imagenes (id SERIAL PRIMARY KEY, imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                                cur.execute(
                                    "INSERT INTO carrusel_imagenes (imagen_nombre, imagen_tipo, imagen_data) VALUES (%s,%s,%s)",
                                    (img_nombre, img_tipo, psycopg2.Binary(img_data))
                                )
                                conn.commit()
                                cur.close()
                                conn.close()

                            start_response("303 See Other", [('Location', '/carrusel')] + headers)
                            return [b""]

            except Exception as e:
                mensaje = "<div class='bad'>Error: %s</div>" % str(e)

        slides = ""
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS carrusel_imagenes (id SERIAL PRIMARY KEY, imagen_nombre VARCHAR(255), imagen_tipo VARCHAR(20), imagen_data BYTEA, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                cur.execute("SELECT id, imagen_tipo, imagen_data FROM carrusel_imagenes ORDER BY fecha DESC")
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    i = 0
                    for (img_id, img_tipo, img_data) in rows:
                        b64 = base64.b64encode(img_data).decode("utf-8")
                        active = "active" if i == 0 else ""
                        slides += """
<div class="slide __ACTIVE__">
  <img src="data:image/__TYPE__;base64,__B64__" style="max-width:100%;max-height:520px;border-radius:14px;box-shadow:0 2px 12px rgba(0,0,0,.12);">
  <form method="POST" onsubmit="return confirm('¿Eliminar esta imagen?');" style="margin-top:12px;">
    <input type="hidden" name="eliminar_id" value="__ID__">
    <button class="btn-danger btn-sm" type="submit">Eliminar</button>
  </form>
</div>
""".replace("__ACTIVE__", active).replace("__TYPE__", img_tipo).replace("__B64__", b64).replace("__ID__", str(img_id))
                        i += 1
                else:
                    slides = "<p>No hay imágenes aún.</p>"
            except Exception as e:
                slides = "<div class='bad'>Error cargando carrusel: %s</div>" % str(e)

        body = """
<div class="simple-box">
  <h1>Carrusel</h1>
  __MENSAJE__

  <div id="wrap">__SLIDES__</div>

  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:15px;">
    <button class="btn-blue" style="width:60px;border-radius:50%;height:50px;font-size:20px;" onclick="prev()">◀</button>
    <button class="btn-blue" style="width:60px;border-radius:50%;height:50px;font-size:20px;" onclick="next()">▶</button>
  </div>

  <hr>

  <h3>Agregar imagen</h3>
  <form method="POST" enctype="multipart/form-data">
    <input type="file" name="imagen" accept="image/jpeg,image/png,image/gif" required>
    <button class="btn-primary" type="submit" style="width:100%;">Agregar</button>
  </form>
</div>

<style>
.slide{display:none;text-align:center;}
.slide.active{display:block;}
</style>

<script>
var idx = 0;
function show(i){
  var slides = document.querySelectorAll('.slide');
  if(!slides || slides.length===0) return;
  for(var k=0;k<slides.length;k++){ slides[k].classList.remove('active'); }
  idx = (i + slides.length) % slides.length;
  slides[idx].classList.add('active');
}
function next(){ show(idx+1); }
function prev(){ show(idx-1); }
document.addEventListener('DOMContentLoaded', function(){ show(0); });
</script>
""".replace("__MENSAJE__", mensaje).replace("__SLIDES__", slides)

        html = page("Carrusel", body)
        start_response("200 OK", headers)
        return [html.encode("utf-8")]

    # =========================================================
    # CRUD PERSONAS (NOMBRE, EMAIL, FECHA NAC) + MODAL + FILTRO FECHAS
    #   - nombre solo letras
    #   - fecha no permite hoy o futuras (max ayer)
    #   - buscar por nombre
    #   - filtro por rango (from/to) en fecha_nacimiento
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
        total_pages = 1

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
            except Exception as e:
                mensaje = "<div class='bad'>Error BD: %s</div>" % str(e)
        else:
            mensaje = "<div class='bad'>No hay conexión a BD</div>"

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

        base_q = "q=%s&from=%s&to=%s" % (urllib.parse.quote(search), urllib.parse.quote(desde_str), urllib.parse.quote(hasta_str))

        if page_num > 1:
            prev_link = '<a class="iconbtn" title="Anterior" style="text-decoration:none;" href="/crud_personas?p=%s&%s">‹</a>' % (str(page_num-1), base_q)
        else:
            prev_link = '<span class="iconbtn" style="opacity:.35;cursor:not-allowed;">‹</span>'

        if page_num < total_pages:
            next_link = '<a class="iconbtn" title="Siguiente" style="text-decoration:none;" href="/crud_personas?p=%s&%s">›</a>' % (str(page_num+1), base_q)
        else:
            next_link = '<span class="iconbtn" style="opacity:.35;cursor:not-allowed;">›</span>'

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
    # 404 REAL
    # =========================================================
    body = """
<div class="simple-box" style="text-align:center;">
  <h1 style="color:#ef4444;font-size:54px;margin-bottom:10px;">404</h1>
  <h2>Página no encontrada</h2>
  <p style="color:#6b7280;">La ruta solicitada <code>%s</code> no existe.</p>
  <a href="/" class="btn-pill btn-primary" style="display:inline-block;text-decoration:none;">Volver al Inicio</a>
</div>
""" % path

    html = page("404", body)
    start_response("404 Not Found", headers)
    return [html.encode("utf-8")]
