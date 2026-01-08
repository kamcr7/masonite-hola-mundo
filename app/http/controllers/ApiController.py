"""API Controller."""
from masonite.controllers import Controller
from masonite.response import Response
import datetime


class ApiController(Controller):
    """Controller for API endpoints."""
    
    def saludo(self, response: Response):
        """Return a simple greeting."""
        return response.json({
            "mensaje": "¡Hola desde la API de Masonite!",
            "estado": "success",
            "timestamp": datetime.datetime.now().isoformat(),
            "framework": "Masonite",
            "hosting": "Render.com"
        })
    
    def saludo_personalizado(self, response: Response, nombre="Visitante"):
        """Return a personalized greeting."""
        return response.json({
            "mensaje": f"¡Hola {nombre}!",
            "saludo": f"Bienvenido a la API de Masonite en Render.com, {nombre}",
            "estado": "success",
            "timestamp": datetime.datetime.now().isoformat(),
            "parametros": {
                "nombre": nombre
            }
        })
