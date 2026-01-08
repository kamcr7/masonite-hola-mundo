"""Web Routes."""
from masonite.routes import Route

ROUTES = [
    # Home page
    Route.get("/", "WelcomeController@show").name("welcome"),
    
    # Hola Mundo
    Route.get("/hola", "HolaMundoController@show").name("hola"),
    Route.get("/hola/@nombre", "HolaMundoController@show").name("hola.nombre"),
    
    # API
    Route.get("/api/saludo", "ApiController@saludo").name("api.saludo"),
    Route.get("/api/saludo/@nombre", "ApiController@saludo_personalizado").name("api.saludo.personalizado"),
]
