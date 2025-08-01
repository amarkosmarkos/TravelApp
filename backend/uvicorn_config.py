"""
Configuración para uvicorn.
"""

import sys
import os

# Agregar el directorio backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Configuración de la aplicación
app = "app.main:app"
host = "0.0.0.0"
port = 8000
reload = True
log_level = "info" 