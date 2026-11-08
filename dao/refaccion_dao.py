"""
DAO de refacciones: acceso a datos de la tabla refacciones (catálogo con stock).
"""

from modelos.refaccion import Refaccion
from db.conexion import obtener_conexion

_COLUMNAS = "refaccion_id, nombre, precio, stock"


def crear(nombre: str, precio: float, stock: int):
    """Inserta una refacción nueva y devuelve su id (refaccion_id)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO refacciones (nombre, precio, stock) VALUES (%s, %s, %s)",
            (nombre, precio, stock),
        )
        conexion.commit()
        id_generado = cursor.lastrowid
        cursor.close()
        conexion.close()
        return id_generado
    except Exception as error:
        raise RuntimeError(f"No se pudo guardar la refacción en la BD: {error}") from error


def obtener_todos() -> list[Refaccion]:
    """Devuelve todo el catálogo de refacciones ordenado por nombre."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(f"SELECT {_COLUMNAS} FROM refacciones ORDER BY nombre")
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo leer el catálogo de refacciones: {error}") from error

    return [Refaccion(*fila) for fila in filas]


def actualizar(refaccion_id: int, nombre: str, precio: float, stock: int) -> None:
    """Actualiza los datos de una refacción (incluido ajuste manual de stock)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE refacciones SET nombre = %s, precio = %s, stock = %s "
            "WHERE refaccion_id = %s",
            (nombre, precio, stock, refaccion_id),
        )
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo actualizar la refacción: {error}") from error


def descontar_stock(refaccion_id: int, cantidad: int) -> None:
    """
    Descuenta stock al usar una refacción en una orden.

    Rechaza el descuento si el stock no alcanza (no deja inventario
    negativo). Será invocado desde la transacción de órdenes.
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        # UPDATE atómico con condición: solo decrementa si alcanza el stock
        cursor.execute(
            "UPDATE refacciones SET stock = stock - %s "
            "WHERE refaccion_id = %s AND stock >= %s",
            (cantidad, refaccion_id, cantidad),
        )
        if cursor.rowcount == 0:  # No actualizó: stock insuficiente
            cursor.close()
            conexion.rollback()
            conexion.close()
            raise RuntimeError("Stock insuficiente de la refacción seleccionada.")
        conexion.commit()
        cursor.close()
        conexion.close()
    except RuntimeError:
        raise  # Mensaje ya claro (stock insuficiente)
    except Exception as error:
        raise RuntimeError(f"No se pudo descontar el stock: {error}") from error


def eliminar(refaccion_id: int) -> None:
    """
    Elimina una refacción del catálogo.

    Nota: detalle_orden.item_id no tiene FK hacia refacciones, por lo
    que el borrado no rompe órdenes históricas.
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM refacciones WHERE refaccion_id = %s", (refaccion_id,))
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo eliminar la refacción: {error}") from error
