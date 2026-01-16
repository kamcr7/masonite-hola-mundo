import os
import psycopg2
import requests
import re
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # === CONFIGURACIÓN ===
    # PostgreSQL
    DATABASE_URL = "postgresql://postgres:YmbYQizQXChKLoqdVAORJvZiJMDCbLTt@interchange.proxy.rlwy.net:31359/railway"
    
    # reCAPTCHA
    SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    
    # === PÁGINA DE ERROR ===
    def mostrar_error(tipo_error="general", campo=""):
        mensajes = {
            "general": "Ocurrió un error inesperado.",
            "bd_conexion": "No se pudo conectar a la base de datos.",
            "campos_requeridos": "Todos los campos son obligatorios.",
            "recaptcha": "Por favor, verifica que no eres un robot.",
            "telefono_invalido": f"El teléfono en '{campo}' debe tener 10 dígitos numéricos.",
            "telefono_no_coincide": "Los teléfonos no coinciden.",
            "codigo_invalido": f"El código en '{campo}' debe tener 6 dígitos numéricos.",
            "codigo_no_coincide": "Los códigos de confirmación no coinciden.",
            "nombre_invalido": "El nombre no puede contener números.",
            "email_invalido": "El email no tiene un formato válido."
        }
        
        mensaje = mensajes.get(tipo_error, "Ocurrió un error.")
        robot = "📱" if "telefono" in tipo_error else "🔢" if "codigo" in tipo_error else "🤖"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Error en formulario</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            text-align: center; 
            margin-top: 80px; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .error-box {{
            max-width: 500px;
            margin: 0 auto;
            padding: 40px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .icono {{
            font-size: 70px;
            margin: 0 0 20px 0;
        }}
        h1 {{ 
            color: #dc3545;
            margin: 0 0 15px 0;
        }}
        .mensaje {{ 
            color: #6c757d; 
            font-size: 18px;
            line-height: 1.5;
            margin: 0 0 25px 0;
        }}
        .campo-error {{
            background: #fff3cd;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
        }}
        .boton {{
            display: inline-block;
            padding: 12px 30px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 16px;
            border: none;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="error-box">
        <div class="icono">{robot}</div>
        <h1>Error en formulario</h1>
        <div class="mensaje">
            {mensaje}
            <p>Por favor, corrige los datos e inténtalo de nuevo.</p>
        </div>
        <a href="/" class="boton">Volver al formulario</a>
    </div>
</body>
</html>'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # === VALIDACIONES ===
    def validar_telefono(telefono):
        # Debe tener exactamente 10 dígitos
        return re.match(r'^\d{10}$', telefono) is not None
    
    def validar_codigo(codigo):
        # Debe tener exactamente 6 dígitos
        return re.match(r'^\d{6}$', codigo) is not None
    
    def validar_nombre(nombre):
        # No debe contener números
        return re.search(r'\d', nombre) is None
    
    def validar_email(email):
        # Validación básica de email
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
    
    # === CONEXIÓN BD ===
    def conectar_bd():
        try:
            result = urlparse(DATABASE_URL)
            return psycopg2.connect(
                host=result.hostname,
                database=result.path[1:],
                user=result.username,
                password=result.password,
                port=result.port,
                connect_timeout=5
            )
        except:
            return None
    
    # === VERIFICAR RECAPTCHA ===
    def verificar_recaptcha(token):
        if not token:
            return False
        if SECRET_KEY == "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe":
            return True
        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={'secret': SECRET_KEY, 'response': token},
                timeout=5
            )
            return response.json().get('success', False)
        except:
            return False
    
    # === PÁGINA PRINCIPAL ===
    if path == '/' and method == 'GET':
        try:
            conn = conectar_bd()
            if conn:
                cur = conn.cursor()
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS registros (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(100),
                        email VARCHAR(100),
                        telefono VARCHAR(10),
                        codigo_verificacion VARCHAR(6),
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cur.execute("SELECT nombre, telefono, fecha FROM registros ORDER BY fecha DESC LIMIT 10")
                registros = cur.fetchall()
                cur.close()
                conn.close()
                
                registros_html = ''
                if registros:
                    registros_html = '<h3>Últimos registros:</h3><ul>'
                    for nombre, telefono, fecha in registros:
                        fecha_str = str(fecha)[:16]
                        # Mostrar solo últimos 4 dígitos del teléfono
                        telefono_masked = f"*** *** {telefono[-4:]}" if telefono else "No disponible"
                        registros_html += f'<li><strong>{nombre}</strong> - Tel: {telefono_masked} ({fecha_str})</li>'
                    registros_html += '</ul>'
                else:
                    registros_html = '<p>No hay registros aún.</p>'
            else:
                registros_html = '<p style="color: #dc3545;">⚠️ Base de datos no disponible</p>'
            
        except:
            registros_html = '<p style="color: #dc3545;">⚠️ Error cargando registros</p>'
        
        # FORMULARIO COMPLETO
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Formulario de Registro</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 600px; 
            margin: 40px auto; 
            padding: 20px;
            background: #f8f9fa;
        }}
        .form-container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #333; 
            text-align: center;
            margin-bottom: 30px;
        }}
        .campo {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }}
        input[type="text"],
        input[type="email"] {{
            width: 95%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }}
        .requerido {{ color: #dc3545; }}
        .info {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
        }}
        .campo-confirmacion {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .g-recaptcha {{
            margin: 20px 0;
        }}
        button {{
            width: 100%;
            padding: 12px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }}
        button:hover {{
            background: #218838;
        }}
        hr {{
            margin: 30px 0;
            border: none;
            border-top: 1px solid #dee2e6;
        }}
        .ejemplo {{
            background: #fff3cd;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 14px;
        }}
        .error-message {{
            color: #dc3545;
            font-size: 14px;
            margin-top: 5px;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="form-container">
        <h1>📋 Formulario de Registro</h1>
        
        <form method="POST" id="registroForm">
            <!-- Nombre -->
            <div class="campo">
                <label>Nombre completo <span class="requerido">*</span></label>
                <input type="text" name="nombre" placeholder="Ej: Juan Pérez" required>
                <div class="info">No debe contener números</div>
                <div class="error-message" id="nombreError">El nombre no puede contener números</div>
            </div>
            
            <!-- Email -->
            <div class="campo">
                <label>Email <span class="requerido">*</span></label>
                <input type="email" name="email" placeholder="ejemplo@correo.com" required>
                <div class="info">Formato válido de email</div>
                <div class="error-message" id="emailError">Email no válido</div>
            </div>
            
            <!-- Teléfono con confirmación -->
            <div class="campo-confirmacion">
                <h3>📱 Teléfono (10 dígitos)</h3>
                
                <div class="campo">
                    <label>Teléfono <span class="requerido">*</span></label>
                    <input type="text" name="telefono" placeholder="Ej: 5512345678" required maxlength="10">
                    <div class="info">10 dígitos numéricos</div>
                    <div class="error-message" id="telefonoError">Debe tener 10 dígitos</div>
                </div>
                
                <div class="campo">
                    <label>Confirmar teléfono <span class="requerido">*</span></label>
                    <input type="text" name="telefono_confirmar" placeholder="Repite el teléfono" required maxlength="10">
                    <div class="error-message" id="telefonoConfirmError">Los teléfonos no coinciden</div>
                </div>
                
                <div class="ejemplo">
                    <strong>Ejemplo válido:</strong> 5512345678
                </div>
            </div>
            
            <!-- Código de verificación con confirmación -->
            <div class="campo-confirmacion">
                <h3>🔢 Código de verificación (6 dígitos)</h3>
                
                <div class="campo">
                    <label>Código <span class="requerido">*</span></label>
                    <input type="text" name="codigo" placeholder="Ej: 123456" required maxlength="6">
                    <div class="info">6 dígitos numéricos</div>
                    <div class="error-message" id="codigoError">Debe tener 6 dígitos</div>
                </div>
                
                <div class="campo">
                    <label>Confirmar código <span class="requerido">*</span></label>
                    <input type="text" name="codigo_confirmar" placeholder="Repite el código" required maxlength="6">
                    <div class="error-message" id="codigoConfirmError">Los códigos no coinciden</div>
                </div>
                
                <div class="ejemplo">
                    <strong>Ejemplo válido:</strong> 123456
                </div>
            </div>
            
            <!-- reCAPTCHA -->
            <div class="g-recaptcha" data-sitekey="{SITE_KEY}"></div>
            <script src="https://www.google.com/recaptcha/api.js"></script>
            
            <!-- Botón -->
            <button type="submit">✅ Enviar Registro</button>
        </form>
        
        <hr>
        
        {registros_html}
        
        <div class="info" style="text-align: center; margin-top: 20px;">
            <p><strong>Validaciones implementadas:</strong></p>
            <p>✓ Campos obligatorios ✓ Formato email ✓ Teléfono 10 dígitos ✓ Código 6 dígitos<br>
            ✓ Confirmaciones ✓ No números en nombre ✓ reCAPTCHA</p>
        </div>
    </div>
    
    <script>
    // Validación en tiempo real
    document.getElementById('registroForm').addEventListener('submit', function(e) {{
        let valid = true;
        
        // Validar nombre (no números)
        const nombre = document.querySelector('input[name="nombre"]');
        const nombreError = document.getElementById('nombreError');
        if (/\d/.test(nombre.value)) {{
            nombreError.style.display = 'block';
            valid = false;
        }} else {{
            nombreError.style.display = 'none';
        }}
        
        // Validar teléfono (10 dígitos)
        const telefono = document.querySelector('input[name="telefono"]');
        const telefonoError = document.getElementById('telefonoError');
        if (!/^\d{{10}}$/.test(telefono.value)) {{
            telefonoError.style.display = 'block';
            valid = false;
        }} else {{
            telefonoError.style.display = 'none';
        }}
        
        // Validar confirmación teléfono
        const telefonoConfirm = document.querySelector('input[name="telefono_confirmar"]');
        const telefonoConfirmError = document.getElementById('telefonoConfirmError');
        if (telefono.value !== telefonoConfirm.value) {{
            telefonoConfirmError.style.display = 'block';
            valid = false;
        }} else {{
            telefonoConfirmError.style.display = 'none';
        }}
        
        // Validar código (6 dígitos)
        const codigo = document.querySelector('input[name="codigo"]');
        const codigoError = document.getElementById('codigoError');
        if (!/^\d{{6}}$/.test(codigo.value)) {{
            codigoError.style.display = 'block';
            valid = false;
        }} else {{
            codigoError.style.display = 'none';
        }}
        
        // Validar confirmación código
        const codigoConfirm = document.querySelector('input[name="codigo_confirmar"]');
        const codigoConfirmError = document.getElementById('codigoConfirmError');
        if (codigo.value !== codigoConfirm.value) {{
            codigoConfirmError.style.display = 'block';
            valid = false;
        }} else {{
            codigoConfirmError.style.display = 'none';
        }}
        
        if (!valid) {{
            e.preventDefault();
            alert("Por favor, corrige los errores en el formulario.");
        }}
    }});
    </script>
</body>
</html>'''
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
    
    # === PROCESAR FORMULARIO ===
    elif path == '/' and method == 'POST':
        try:
            # Leer datos
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            
            from urllib.parse import parse_qs
            params = parse_qs(post_data)
            
            # Extraer datos
            nombre = params.get('nombre', [''])[0].strip()
            email = params.get('email', [''])[0].strip()
            telefono = params.get('telefono', [''])[0].strip()
            telefono_confirmar = params.get('telefono_confirmar', [''])[0].strip()
            codigo = params.get('codigo', [''])[0].strip()
            codigo_confirmar = params.get('codigo_confirmar', [''])[0].strip()
            recaptcha_token = params.get('g-recaptcha-response', [''])[0]
            
            # === VALIDACIONES DEL SERVIDOR ===
            
            # 1. Campos requeridos
            if not all([nombre, email, telefono, telefono_confirmar, codigo, codigo_confirmar]):
                return mostrar_error("campos_requeridos")
            
            # 2. Validar nombre (no números)
            if not validar_nombre(nombre):
                return mostrar_error("nombre_invalido")
            
            # 3. Validar email
            if not validar_email(email):
                return mostrar_error("email_invalido")
            
            # 4. Validar teléfono (10 dígitos)
            if not validar_telefono(telefono):
                return mostrar_error("telefono_invalido", "Teléfono")
            
            # 5. Confirmar teléfono
            if telefono != telefono_confirmar:
                return mostrar_error("telefono_no_coincide")
            
            # 6. Validar código (6 dígitos)
            if not validar_codigo(codigo):
                return mostrar_error("codigo_invalido", "Código")
            
            # 7. Confirmar código
            if codigo != codigo_confirmar:
                return mostrar_error("codigo_no_coincide")
            
            # 8. reCAPTCHA
            if not verificar_recaptcha(recaptcha_token):
                return mostrar_error("recaptcha")
            
            # 9. Guardar en BD
            conn = conectar_bd()
            if not conn:
                return mostrar_error("bd_conexion")
            
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO registros (nombre, email, telefono, codigo_verificacion) VALUES (%s, %s, %s, %s)",
                (nombre, email, telefono, codigo)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            # Éxito - redirigir
            start_response('302 Found', [('Location', '/')])
            return [b'Redirecting...']
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return mostrar_error("general")
    
    # === 404 ===
    else:
        html = '''<h1>404 - Página no encontrada</h1><a href="/">Inicio</a>'''
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [html.encode('utf-8')]
