"""
DAO de pagos: acceso a datos de la tabla pagos.

Los pagos se registran contra una orden; al sumar el total de pagos
igual o superior al total de la orden, la vista marca la orden como
'pagada' (la regla de negocio vive en la vista, no aquí).
"""

from modelos.pago import Pago
from db.conexion import obtener_conexion

_COLUMNAS = "pago_id, orden_id, monto, fecha_pago, metodo_pago, usuario_id"


def registrar(orden_id: int, monto: float, metodo_pago: str, usuario_id: int) -> int:
    """Inserta un pago del día para la orden y devuelve su id (pago_id)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO pagos (orden_id, monto, fecha_pago, metodo_pago, usuario_id) "
            "VALUES (%s, %s, CURDATE(), %s, %s)",
            (orden_id, monto, metodo_pago, usuario_id),
        )
        conexion.commit()
        id_generado = cursor.lastrowid
        cursor.close()
        conexion.close()
        return id_generado
    except Exception as error:
        raise RuntimeError(f"No se pudo registrar el pago: {error}") from error


def obtener_por_orden(orden_id: int) -> list[Pago]:
    """Devuelve los pagos de una orden, el más reciente primero."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(f"SELECT {_COLUMNAS} FROM pagos WHERE orden_id = %s ORDER BY pago_id DESC", (orden_id,))
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo leer los pagos de la orden: {error}") from error

    return [Pago(*fila) for fila in filas]


def total_pagado(orden_id: int) -> float:
    """Suma de los pagos registrados de una orden (0 si no tiene)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE orden_id = %s",
            (orden_id,),
        )
        (total,) = cursor.fetchone()
        cursor.close()
        conexion.close()
        return float(total)
    except Exception as error:
        raise RuntimeError(f"No se pudo calcular lo pagado de la orden: {error}") from error


def eliminar(pago_id: int) -> None:
    """Elimina un pago registrado (corrección de errores de captura)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM pagos WHERE pago_id = %s", (pago_id,))
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo eliminar el pago: {error}") from error