# MÍNIMO pero FUNCIONAL
from masonite.foundation import Application
from masonite.response import Response
from masonite.routes import Get

app = Application()
router = app.make('router')

# Ruta mínima
router.add(Get('/', lambda req: Response("✅ Masonite 4 en Railway")))

application = app
