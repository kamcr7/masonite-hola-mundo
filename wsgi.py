# -*- coding: utf-8 -*-
import os
import re
import cgi
import json
import hmac
import time
import base64
import hashlib
import urllib.request
import urllib.parse
from urllib.parse import parse_qs, urlparse
from datetime import datetime, date

import psycopg2

# =========================================================
# CONFIG
# =========================================================
DATABASE_URL = "postgresql://neondb_owner:npg_V1CwlGHBK4Og@ep-crimson-recipe-ai9g12ym-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
JWT_SECRET = "CAMBIA_ESTA_LLAVE_SUPER_SECRETA_2026"
JWT_EXPIRE_SECONDS = 60 * 60 * 8  # 8 horas
PAGE_SIZE = 5

# =========================================================
# HELPERS GENERALES
# =========================================================
def html_escape(s):
    s = s or ""
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&#39;")
    )

def limpiar_espacios(texto):
    return " ".join((texto or "").strip().split())

def validar_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", (email or "").strip()))

def validar_celular(cel):
    return bool(re.fullmatch(r"^\d{10,15}$", (cel or "").strip()))

def validar_usuario(usuario):
    return bool(re.fullmatch(r"^[A-Za-z0-9_.-]{3,30}$", (usuario or "").strip()))

def hash_password(password):
    password = password or ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def b64url_decode(data):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))

def jwt_encode(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def jwt_decode(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_signature = hmac.new(
            JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
        ).digest()

        if not hmac.compare_digest(expected_signature, b64url_decode(signature_b64)):
            return None

        payload = json.loads(b64url_decode(payload_b64).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except:
        return None

def parse_cookies(environ):
    cookie_header = environ.get("HTTP_COOKIE", "")
    cookies = {}
    for item in cookie_header.split(";"):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            cookies[k] = v
    return cookies

def make_cookie(name, value, max_age=None, path="/", http_only=True):
    cookie = f"{name}={value}; Path={path}; SameSite=Lax"
    if max_age is not None:
        cookie += f"; Max-Age={max_age}"
    if http_only:
        cookie += "; HttpOnly"
    return ("Set-Cookie", cookie)

def redirect(start_response, location, extra_headers=None):
    headers = [("Location", location)]
    if extra_headers:
        headers.extend(extra_headers)
    start_response("303 See Other", headers)
    return [b""]

def json_response(start_response, data, status="200 OK"):
    body = json.dumps(data).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8")])
    return [body]

def get_form_data(environ):
    fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)
    data = {}
    if hasattr(fs, "list") and fs.list:
        for item in fs.list:
            if item.filename:
                data[item.name] = item
            else:
                data[item.name] = item.value
    return fs, data

def verificar_recaptcha(token):
    try:
        data = urllib.parse.urlencode({
            "secret": RECAPTCHA_SECRET_KEY,
            "response": token or ""
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return bool(result.get("success"))
    except:
        return False

def conectar_bd():
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


# =========================================================
# BD
# =========================================================
def init_db():
    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS perfiles (
        id SERIAL PRIMARY KEY,
        strNombrePerfil VARCHAR(120) NOT NULL UNIQUE,
        bitAdministrador BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS modulos (
        id SERIAL PRIMARY KEY,
        strNombreModulo VARCHAR(120) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        strNombreUsuario VARCHAR(50) NOT NULL UNIQUE,
        idPerfil INTEGER NOT NULL REFERENCES perfiles(id),
        strPwd VARCHAR(255) NOT NULL,
        idEstadoUsuario INTEGER NOT NULL DEFAULT 1, -- 1 activo, 0 inactivo
        strCorreo VARCHAR(150) NOT NULL,
        strNumeroCelular VARCHAR(20) NOT NULL,
        strImagenBase64 TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS permisos_perfil (
        id SERIAL PRIMARY KEY,
        idModulo INTEGER NOT NULL REFERENCES modulos(id) ON DELETE CASCADE,
        idPerfil INTEGER NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
        bitAgregar BOOLEAN NOT NULL DEFAULT FALSE,
        bitEditar BOOLEAN NOT NULL DEFAULT FALSE,
        bitConsulta BOOLEAN NOT NULL DEFAULT FALSE,
        bitEliminar BOOLEAN NOT NULL DEFAULT FALSE,
        bitDetalle BOOLEAN NOT NULL DEFAULT FALSE,
        UNIQUE (idModulo, idPerfil)
    )
    """)

    # seed mínimo
    cur.execute("SELECT COUNT(*) FROM perfiles")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO perfiles (strNombrePerfil, bitAdministrador)
        VALUES
        ('ADMINISTRADOR', TRUE),
        ('RECEPCION', FALSE)
        """)

    cur.execute("SELECT COUNT(*) FROM modulos")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO modulos (strNombreModulo)
        VALUES
        ('CONFIGURACIÓN'),
        ('PERFIL'),
        ('PERMISOS PERFIL'),
        ('USUARIO')
        """)

    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id FROM perfiles WHERE strNombrePerfil='ADMINISTRADOR'")
        perfil_admin = cur.fetchone()[0]

        cur.execute("""
        INSERT INTO usuarios (
            strNombreUsuario, idPerfil, strPwd, idEstadoUsuario, strCorreo, strNumeroCelular
        )
        VALUES (%s, %s, %s, 1, %s, %s)
        """, ("admin", perfil_admin, hash_password("admin123"), "admin@clinica.com", "7710000000"))

    # dar permisos completos al admin
    cur.execute("SELECT id FROM perfiles WHERE strNombrePerfil='ADMINISTRADOR'")
    perfil_admin = cur.fetchone()[0]
    cur.execute("SELECT id FROM modulos")
    mods = cur.fetchall()

    for (mid,) in mods:
        cur.execute("""
        INSERT INTO permisos_perfil (
            idModulo, idPerfil, bitAgregar, bitEditar, bitConsulta, bitEliminar, bitDetalle
        )
        VALUES (%s, %s, TRUE, TRUE, TRUE, TRUE, TRUE)
        ON CONFLICT (idModulo, idPerfil) DO NOTHING
        """, (mid, perfil_admin))

    conn.commit()
    cur.close()
    conn.close()