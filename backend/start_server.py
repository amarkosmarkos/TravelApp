#!/usr/bin/env python3
"""
Script de inicio para el servidor de la aplicación de viajes.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Configurar el path para que Python pueda encontrar los módulos
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

# Configurar variables de entorno si no están definidas
os.environ.setdefault("PYTHONPATH", str(backend_dir))

def main():
    """Función principal para iniciar el servidor."""
    print("🚀 Iniciando servidor de Travel Assistant...")
    print(f"📁 Directorio de trabajo: {backend_dir}")
    print(f"🐍 Python path: {sys.path[0]}")
    
    # Asegurar que PYTHONPATH se propaga a sub-procesos (Windows + reload)
    os.environ["PYTHONPATH"] = str(backend_dir)

    reload_flag = os.getenv("FRESH_RELOAD", "false").lower() == "true"

    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=reload_flag,  # Desactivado por defecto para evitar bucles
            reload_dirs=[str(backend_dir)] if reload_flag else None,
            app_dir=str(backend_dir),
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Error iniciando el servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 