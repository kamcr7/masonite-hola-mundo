"""Welcome Controller."""
from masonite.controllers import Controller
from masonite.views import View
import datetime


class WelcomeController(Controller):
    """Controller for welcome page."""
    
    def show(self, view: View):
        """Show the welcome page."""
        return view.render("welcome", {
            "title": "¡Bienvenido a Masonite!",
            "year": datetime.datetime.now().year,
            "message": "Tu aplicación está funcionando correctamente en Render.com",
            "features": [
                "Framework Python moderno",
                "Fácil de aprender y usar",
                "Listo para producción",
                "Soporte para APIs REST",
                "Sistema de plantillas Jinja2",
                "ORM integrado",
                "Autenticación incluida",
                "Despliegue fácil en Render"
            ]
        })
