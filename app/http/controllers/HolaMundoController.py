"""Hola Mundo Controller."""
from masonite.controllers import Controller
from masonite.views import View
from masonite.request import Request
import datetime


class HolaMundoController(Controller):
    """Controller for Hola Mundo."""
    
    def show(self, view: View, request: Request):
        """Show the hola mundo page."""
        nombre = request.param("nombre", request.input("nombre", "Visitante"))
        
        return view.render("hola", {
            "titulo": "¡Hola Mundo desde Masonite!",
            "nombre": nombre,
            "fecha": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "tecnologias": ["Python", "Masonite", "Render.com", "HTML5", "CSS3"]
        })
