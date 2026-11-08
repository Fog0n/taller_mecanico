"""
Conexión a la base de datos MySQL (XAMPP).

Provee una función para obtener la conexión y otra para
probar que el servidor MySQL esté disponible.
"""

import mysql.connector

from config import settings


def obtener_conexion():
    """
    Devuelve una conexión activa a la base de datos taller_mecanico.

    Lanza un error claro si no es posible conectar (por ejemplo,
    si el servicio MySQL de XAMPP no está iniciado).
    """
    try:
        return mysql.connector.connect(
            host=settings.DB_HOST,
            port=int(settings.DB_PORT),
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,  # Cadena vacía es válida en XAMPP
            database=settings.DB_NAME,
        )
    except mysql.connector.Error as error:
        # Error claro para facilitar el diagnóstico en clase
        raise RuntimeError(
            "No se pudo conectar a MySQL.\n"
            "Verifica que el servicio MySQL esté iniciado en el Panel "
            f"de Control de XAMPP (host={settings.DB_HOST}:{settings.DB_PORT}).\n"
            f"Detalle técnico: {error}"
        ) from error


def probar_conexion() -> bool:
    """
    Prueba la conexión ejecutando un SELECT 1.

    Devuelve True si la conexión funciona, False en caso contrario.
    No lanza excepciones: está pensada para una verificación previa.
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conexion.close()
        return True
    except Exception:
        # Cualquier fallo (conexión rechazada, BD inexistente, etc.)
        # se traduce en un simple False.
        return False
