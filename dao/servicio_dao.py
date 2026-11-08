"""
DAO de servicios: acceso a datos de la tabla servicios (catálogo).
"""

from modelos.servicio import Servicio
from db.conexion import obtener_conexion

_COLUMNAS = "servicio_id, nombre, precio"


def crear(nombre: str, precio: float):
    """Inserta un servicio nuevo y devuelve su id (servicio_id)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO servicios (nombre, precio) VALUES (%s, %s)",
            (nombre, precio),
        )
        conexion.commit()
        id_generado = cursor.lastrowid
        cursor.close()
        conexion.close()
        return id_generado
    except Exception as error:
        raise RuntimeError(f"No se pudo guardar el servicio en la BD: {error}") from error


def obtener_todos() -> list[Servicio]:
    """Devuelve todo el catálogo de servicios ordenado por nombre."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(f"SELECT {_COLUMNAS} FROM servicios ORDER BY nombre")
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo leer el catálogo de servicios: {error}") from error

    return [Servicio(*fila) for fila in filas]


def actualizar(servicio_id: int, nombre: str, precio: float) -> None:
    """Actualiza el nombre y precio de un servicio del catálogo."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE servicios SET nombre = %s, precio = %s WHERE servicio_id = %s",
            (nombre, precio, servicio_id),
        )
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo actualizar el servicio: {error}") from error


def eliminar(servicio_id: int) -> None:
    """
    Elimina un servicio del catálogo.

    Nota: detalle_orden.item_id no tiene FK hacia servicios, por lo que
    el borrado no rompe órdenes históricas (el precio quedó guardado
    en la línea de detalle).
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM servicios WHERE servicio_id = %s", (servicio_id,))
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo eliminar el servicio: {error}") from error
