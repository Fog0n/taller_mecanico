"""
DAO de clientes: acceso a datos de la tabla clientes (CRUD).
"""

from modelos.cliente import Cliente
from db.conexion import obtener_conexion

# Columnas que se leen/escriben en todos los métodos
_COLUMNAS = "cliente_id, nombre, telefono, email, rfc, tipo_cliente"


def crear(nombre: str, telefono: str, email: str | None, rfc: str | None, tipo_cliente: str):
    """Inserta un cliente nuevo y devuelve su id (cliente_id)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, email, rfc, tipo_cliente) "
            "VALUES (%s, %s, %s, %s, %s)",
            (nombre, telefono, email, rfc, tipo_cliente),
        )
        conexion.commit()
        id_generado = cursor.lastrowid
        cursor.close()
        conexion.close()
        return id_generado
    except Exception as error:
        raise RuntimeError(f"No se pudo guardar el cliente en la BD: {error}") from error


def obtener_todos() -> list[Cliente]:
    """Devuelve todos los clientes ordenados por nombre."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(f"SELECT {_COLUMNAS} FROM clientes ORDER BY nombre")
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo leer la lista de clientes: {error}") from error

    return [Cliente(*fila) for fila in filas]


def actualizar(cliente_id: int, nombre: str, telefono: str, email: str | None,
               rfc: str | None, tipo_cliente: str) -> None:
    """Actualiza los datos de un cliente existente."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE clientes SET nombre = %s, telefono = %s, email = %s, "
            "rfc = %s, tipo_cliente = %s WHERE cliente_id = %s",
            (nombre, telefono, email, rfc, tipo_cliente, cliente_id),
        )
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo actualizar el cliente: {error}") from error


def eliminar(cliente_id: int) -> None:
    """
    Elimina un cliente por su id.

    ATENCIÓN: la BD usa ON DELETE CASCADE, por lo que también elimina
    sus vehículos y órdenes asociadas (la vista debe advertirlo).
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM clientes WHERE cliente_id = %s", (cliente_id,))
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo eliminar el cliente: {error}") from error
