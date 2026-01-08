"""Application Configuration."""
import os
from masonite import config

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Application configuration
config.set('application', {
    'DEBUG': os.getenv('APP_DEBUG', 'True') == 'True',
    'KEY': os.getenv('APP_KEY', 'secret-key-32-characters-long-change-me'),
})

# Template configuration
config.set('templates', {
    'views': os.path.join(BASE_DIR, 'resources/templates'),
    'cache': os.path.join(BASE_DIR, 'storage/framework/cache/views'),
})

# Storage configuration
config.set('storage', {
    'default': 'local',
    'disks': {
        'local': {
            'driver': 'file',
            'root': os.path.join(BASE_DIR, 'storage/app'),
        },
    },
})
