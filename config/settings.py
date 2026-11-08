"""
Configuración de conexión a la base de datos.

Carga las variables del archivo .env con python-dotenv y las expone
como constantes para todo el proyecto.
"""

import os

from dotenv import load_dotenv

# Ruta raíz del proyecto (carpeta padre de config/)
_RUTA_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Carga el archivo .env ubicado en la raíz del proyecto
_env_cargado = load_dotenv(os.path.join(_RUTA_RAIZ, ".env"))

# Aviso claro si falta el archivo .env (no interrumpe la ejecución)
if not _env_cargado and not os.path.exists(os.path.join(_RUTA_RAIZ, ".env")):
    print(
        "[ADVERTENCIA] No se encontró el archivo .env en la raíz del proyecto.\n"
        "              Copia .env.example como .env con los valores de tu instalación."
    )

# Constantes de conexión. DB_PASSWORD puede estar vacío: en XAMPP
# el usuario root no tiene contraseña por defecto, y eso es válido.
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "3306")
DB_USER: str = os.getenv("DB_USER", "root")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")  # Se permite cadena vacía
DB_NAME: str = os.getenv("DB_NAME", "taller_mecanico")
