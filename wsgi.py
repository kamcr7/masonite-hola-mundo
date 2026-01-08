# Versión simple con función lambda
from masonite.foundation import Application
from masonite.response import Response
from masonite.routes import Get

app = Application()

# Ruta con función lambda (sin controlador)
router = app.make('router')
router.add(Get('/', lambda request: Response('''
<h1 style="text-align:center;color:green;margin-top:100px">
    ✅ Masonite 4 en Railway - ¡Funcionando!
</h1>
<p style="text-align:center">Despliegue exitoso</p>
''')))

application = app
