"""
DAO de vehículos: acceso a datos de la tabla vehiculos (CRUD).
"""

from modelos.vehiculo import Vehiculo
from db.conexion import obtener_conexion

_COLUMNAS = "matricula, modelo, marca, color, cliente_id"


def _error_legible(error: Exception) -> RuntimeError:
    """Traduce los errores frecuentes de MySQL a mensajes claros."""
    codigo = getattr(error, "errno", None)
    if codigo == 1062:  # Er_Dup_Entry: PK matricula duplicada
        return RuntimeError("Esa matrícula ya está registrada en la base de datos.")
    if codigo == 1452:  # FK inválida: cliente inexistente
        return RuntimeError("El cliente seleccionado no existe en la base de datos.")
    return RuntimeError(f"Error de base de datos: {error}")


def crear(matricula: str, modelo: str, marca: str, color: str | None, cliente_id: int):
    """Registra un vehículo nuevo (la matricula es su identificador)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO vehiculos (matricula, modelo, marca, color, cliente_id) "
            "VALUES (%s, %s, %s, %s, %s)",
            (matricula, modelo, marca, color, cliente_id),
        )
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise _error_legible(error) from error


def obtener_todos() -> list[Vehiculo]:
    """Devuelve todos los vehículos ordenados por matricula."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(f"SELECT {_COLUMNAS} FROM vehiculos ORDER BY matricula")
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo leer la lista de vehículos: {error}") from error

    return [Vehiculo(*fila) for fila in filas]


def actualizar(matricula: str, modelo: str, marca: str, color: str | None,
               cliente_id: int) -> None:
    """
    Actualiza un vehículo existente identificado por su matricula.

    La matricula NO se modifica: es la identidad del vehículo.
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE vehiculos SET modelo = %s, marca = %s, color = %s, "
            "cliente_id = %s WHERE matricula = %s",
            (modelo, marca, color, cliente_id, matricula),
        )
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise _error_legible(error) from error


def eliminar(matricula: str) -> None:
    """
    Elimina un vehículo por su matricula.

    ATENCIÓN: la BD usa ON DELETE CASCADE, por lo que también elimina
    sus órdenes y detalles asociados (la vista debe advertirlo).
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM vehiculos WHERE matricula = %s", (matricula,))
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise _error_legible(error) from error
