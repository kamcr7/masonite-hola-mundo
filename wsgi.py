# Versión SIMPLIFICADA pero COMPLETA
from masonite.foundation import Application
from masonite.response import Response
from masonite.routes import Route

# Crear e inicializar app
app = Application()

# Providers MÍNIMOS necesarios
from masonite.providers import RouteProvider, ResponseProvider

app.register_providers([RouteProvider, ResponseProvider])

for provider in [RouteProvider, ResponseProvider]:
    provider(app).register()
    provider(app).boot()

# Obtener router y añadir ruta
router = app.make('router')
router.add(Route.get('/', lambda req: Response("✅ Masonite 4 en Railway - ¡Funcionando!")))

application = app
