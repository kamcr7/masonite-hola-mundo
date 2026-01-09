import os
import psycopg2
import requests
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    print("=== DEBUG START ===")
    print(f"Path: {path}, Method: {method}")
    
    # Configuración
    SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    print(f"Has DATABASE_URL: {bool(DATABASE_URL)}")
    
    # Resto del código igual...
    # [El mismo código de antes aquí]
    
