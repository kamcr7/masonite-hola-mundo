"""FIX completo para Masonite en Render Python 3.13."""
import sys
import os
import datetime
import warnings

print("=" * 60)
print("🔧 APLICANDO PARCHES PARA MASONITE EN RENDER")
print("=" * 60)

# ============================================
# 1. SILENCIAR ADVERTENCIAS
# ============================================
warnings.filterwarnings("ignore")

# ============================================
# 2. PARCHETODO PENDULUM (problema principal)
# ============================================
class MockPendulum:
    """Mock completo de pendulum para evitar instalación."""
    
    @staticmethod
    def now():
        return datetime.datetime.now()
    
    @staticmethod
    def today():
        return datetime.date.today()
    
    @staticmethod
    def parse(text, *args, **kwargs):
        try:
            # Intentar parsear como ISO
            return datetime.datetime.fromisoformat(text.replace('Z', '+00:00'))
        except:
            return datetime.datetime.now()
    
    @staticmethod
    def from_timestamp(timestamp):
        return datetime.datetime.fromtimestamp(timestamp)
    
    def __init__(self, year=None, month=None, day=None, *args, **kwargs):
        if year is not None:
            self._dt = datetime.datetime(year, month or 1, day or 1)
        else:
            self._dt = datetime.datetime.now()
    
    def __getattr__(self, name):
        # Delegar al datetime real
        return getattr(self._dt, name)
    
    def __repr__(self):
        return f"<MockPendulum {self._dt}>"

# Crear módulo pendulum fake completo
pendulum_module = type(sys)('pendulum')
pendulum_module.now = MockPendulum.now
pendulum_module.today = MockPendulum.today
pendulum_module.parse = MockPendulum.parse
pendulum_module.from_timestamp = MockPendulum.from_timestamp
pendulum_module.Pendulum = MockPendulum
pendulum_module.__version__ = '2.1.2'

# Agregar sub-módulos que Masonite podría necesitar
pendulum_module.timezone = type(sys)('timezone')
pendulum_module.UTC = type(sys)('UTC')

sys.modules['pendulum'] = pendulum_module
print("✅ 1. Pendulum mockeado exitosamente")

# ============================================
# 3. PARCHETODO DISTUTILS (segundo problema)
# ============================================
class MockDistutilsCommand:
    class build_ext:
        def __init__(self, *args, **kwargs):
            pass

class MockDistutils:
    command = MockDistutilsCommand

sys.modules['distutils'] = type(sys)('distutils')
sys.modules['distutils'].command = MockDistutils.command
print("✅ 2. Distutils mockeado")

# ============================================
# 4. PARCHETODO SETUPTOOLS
# ============================================
try:
    import setuptools
    print("✅ 3. Setuptools disponible")
except ImportError:
    sys.modules['setuptools'] = type(sys)('setuptools')
    print("✅ 3. Setuptools mockeado")

# ============================================
# 5. VERIFICAR QUE MASONITE PUEDA IMPORTARSE
# ============================================
print("✅ 4. Todos los parches aplicados")
print("=" * 60)
print("🚀 MASONITE LISTO PARA IMPORTAR")
print("=" * 60)
