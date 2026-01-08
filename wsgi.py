"""WSGI entry point for Masonite application."""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from masonite import Application

# Create application
application = Application()

# Set configuration location
application.bind('config.location', 'config/')

# Import routes
try:
    from routes import web
    print("✅ Routes loaded successfully")
except ImportError as e:
    print(f"❌ Error loading routes: {e}")

# This is needed for Render.com and Gunicorn
app = application

if __name__ == "__main__":
    from masonite.servers import Server
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    
    print(f"""
    🚀 Masonite Application Starting...
    ========================================
    📁 Directory: {os.getcwd()}
    🌐 Host: {host}
    🚪 Port: {port}
    🔗 Local URL: http://localhost:{port}
    📊 Debug Mode: {os.getenv('APP_DEBUG', 'True')}
    ☁️  Ready for Render.com
    ========================================
    """)
    
    # Start server
    Server().start(application, host=host, port=port)
