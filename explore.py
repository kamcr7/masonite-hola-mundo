# Script para explorar masonite.routes
import masonite.routes
print("=== CONTENIDO DE masonite.routes ===")
for attr in dir(masonite.routes):
    if not attr.startswith('_'):
        print(f"- {attr}")

print("\n=== masonite.routes.__all__ ===")
if hasattr(masonite.routes, '__all__'):
    print(masonite.routes.__all__)
