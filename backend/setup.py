#!/usr/bin/env python3
"""
Script de configuración para el proyecto Travel Assistant.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica la versión de Python."""
    if sys.version_info < (3, 8):
        print("❌ Se requiere Python 3.8 o superior")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")

def install_dependencies():
    """Instala las dependencias del proyecto."""
    print("📦 Instalando dependencias...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        sys.exit(1)

def setup_environment():
    """Configura el entorno de desarrollo."""
    print("🔧 Configurando entorno...")
    
    # Crear archivo .env si no existe
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creando archivo .env...")
        env_content = """# Configuración de la aplicación
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Configuración de la base de datos
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=travel_assistant

# Configuración de Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here

# Configuración de JWT
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Archivo .env creado")
    else:
        print("✅ Archivo .env ya existe")

def main():
    """Función principal de configuración."""
    print("🚀 Configurando Travel Assistant...")
    
    # Verificar versión de Python
    check_python_version()
    
    # Instalar dependencias
    install_dependencies()
    
    # Configurar entorno
    setup_environment()
    
    print("\n✅ Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("1. Configura las variables de entorno en el archivo .env")
    print("2. Asegúrate de que MongoDB esté ejecutándose")
    print("3. Ejecuta: python start_server.py")
    print("\n🎯 Para más información, consulta el README.md")

if __name__ == "__main__":
    main() 