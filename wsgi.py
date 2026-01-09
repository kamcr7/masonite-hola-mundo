import os
import psycopg2
from urllib.parse import urlparse

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # [El resto del código sin reCAPTCHA...]
