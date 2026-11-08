"""
DAO de usuarios: acceso a datos de la tabla usuarios.

Nota: la comparación de contraseñas aún es en texto plano;
será reemplazada por hashing (bcrypt) en una etapa posterior.
"""

from db.conexion import obtener_conexion
from modelos.usuario import Usuario


def obtener_por_username(username: str):
    """
    Busca un usuario por su username.

    Devuelve un objeto Usuario si existe, o None si no se encuentra.
    Lanza RuntimeError si la base de datos no está disponible.
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT usuario_id, nombre, email, username, password, perfil "
            "FROM usuarios WHERE username = %s",
            (username,),
        )
        fila = cursor.fetchone()
        cursor.close()
        conexion.close()
    except Exception as error:
        # Error claro para la vista (por ejemplo, MySQL apagado en XAMPP)
        raise RuntimeError(f"No se pudo consultar el usuario en la BD: {error}") from error

    if fila is None:
        return None

    return Usuario(*fila)
