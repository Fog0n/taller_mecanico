"""
DAO de órdenes: acceso a datos de las tablas ordenes y detalle_orden.

La creación de una orden es TRANSACCIONAL (all-or-nothing): si alguna
línea falla (p. ej. stock de refacciones insuficiente) se revierte
todo y no quedan ni órdenes huérfanas ni stock desfasado.

El descuento de stock de refacciones se delega al trigger de BD
trg_detalle_orden_descontar_stock (BEFORE INSERT en detalle_orden).
"""

from modelos.orden import Orden
from modelos.detalle_orden import DetalleOrden
from db.conexion import obtener_conexion

# Línea de detalle: (tipo, item_id, cantidad) con tipo 'servicio'|'refaccion'
EstadoValido = ("abierta", "en_proceso", "terminada", "entregada", "pagada")


def _leer_precios(cursor):
    """Contenidos de precios consistentes con la transacción activa."""
    precios_serv = {}
    cursor.execute("SELECT servicio_id, precio FROM servicios")
    precios_serv.update({fil[0]: fil[1] for fil in cursor.fetchall()})
    precios_ref = {}
    cursor.execute("SELECT refaccion_id, precio FROM refacciones")
    precios_ref.update({fil[0]: fil[1] for fil in cursor.fetchall()})
    return precios_serv, precios_ref


def crear_orden(matricula: str, cliente_id: int, usuario_id: int,
                detalles: list[tuple[str, int, int]]) -> int:
    """
    Crea una orden completa con sus líneas de detalle en una sola
    transacción y devuelve el nuevo orden_id.

    detalles: lista de tuplas (tipo, item_id, cantidad).
    Lanza RuntimeError con mensaje claro si algo no puede completarse
    (stock insuficiente, tipo desconocido, etc.); en ese caso nada queda
    escrito en la base de datos.

    El descuento de stock se ejecuta en el trigger de BD
    trg_detalle_orden_descontar_stock al insertar cada detalle de tipo
    'refaccion'.
    """
    if not detalles:
        raise RuntimeError("Una orden necesita al menos una línea de detalle.")

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        conexion.autocommit = False  # controlamos COMMIT/ROLLBACK manualmente

        # 1. Cabecera de la orden vía procedimiento almacenado
        cursor.execute(
            "CALL sp_crear_orden(%s, %s, %s, @orden_id)",
            (matricula, cliente_id, usuario_id),
        )
        cursor.execute("SELECT @orden_id")
        fila = cursor.fetchone()
        if not fila or fila[0] is None:
            raise RuntimeError("No se pudo obtener el orden_id generado.")
        orden_id = int(fila[0])

        # 2. Precios vigentes (dentro de la transacción)
        precios_serv, precios_ref = _leer_precios(cursor)

        # 3. Líneas de detalle (el trigger valida y descuenta stock)
        for tipo, item_id, cantidad in detalles:
            if tipo == "servicio":
                if item_id not in precios_serv:
                    raise RuntimeError("El servicio seleccionado no existe.")
                precio_unitario = precios_serv[item_id]
            elif tipo == "refaccion":
                if item_id not in precios_ref:
                    raise RuntimeError("La refacción seleccionada no existe.")
                precio_unitario = precios_ref[item_id]
            else:
                raise RuntimeError(f"Tipo de línea desconocido: {tipo}")

            subtotal = float(precio_unitario) * cantidad
            cursor.execute(
                "INSERT INTO detalle_orden (orden_id, tipo, item_id, "
                "cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s, %s)",
                (orden_id, tipo, item_id, cantidad, precio_unitario, subtotal),
            )

        # 4. Todo bien: confirmar la transacción
        conexion.commit()
        cursor.close()
        conexion.close()
        return orden_id

    except RuntimeError:
        try:
            conexion.rollback()
            cursor.close()
            conexion.close()
        except Exception:
            pass
        raise
    except Exception as error:
        try:
            conexion.rollback()
            cursor.close()
            conexion.close()
        except Exception:
            pass
        raise RuntimeError(f"No se pudo crear la orden (se canceló todo): {error}") from error


def obtener_todas() -> list[Orden]:
    """Devuelve todas las órdenes, la más reciente primero."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT orden_id, matricula, cliente_id, usuario_id, "
            "fecha_entrada, hora_entrada, fecha_salida, hora_salida, estado "
            "FROM ordenes ORDER BY orden_id DESC"
        )
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo leer la lista de órdenes: {error}") from error

    return [Orden(*fila) for fila in filas]


def obtener_detalles(orden_id: int) -> list[DetalleOrden]:
    """Devuelve las líneas de detalle de una orden (con nombre de artículo)."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        # LEFT JOIN: si el artículo ya no está en el catálogo, la línea
        # histórica se mantiene sin nombre
        cursor.execute(
            "SELECT d.detalle_id, d.orden_id, d.tipo, d.item_id, d.cantidad, "
            "d.precio_unitario, d.subtotal, "
            "COALESCE(s.nombre, r.nombre) AS nombre_item "
            "FROM detalle_orden d "
            "LEFT JOIN servicios s ON d.tipo = 'servicio' AND d.item_id = s.servicio_id "
            "LEFT JOIN refacciones r ON d.tipo = 'refaccion' AND d.item_id = r.refaccion_id "
            "WHERE d.orden_id = %s ORDER BY d.detalle_id",
            (orden_id,),
        )
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
    except Exception as error:
        raise RuntimeError(f"No se pudo leer el detalle de la orden: {error}") from error

    return [DetalleOrden(*fila) for fila in filas]


def calcular_total(orden_id: int) -> float:
    """Devuelve el total acumulado de los subtotales de una orden."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(subtotal), 0) FROM detalle_orden WHERE orden_id = %s",
            (orden_id,),
        )
        (total,) = cursor.fetchone()
        cursor.close()
        conexion.close()
        return float(total)
    except Exception as error:
        raise RuntimeError(f"No se pudo calcular el total de la orden: {error}") from error


def eliminar(orden_id: int) -> None:
    """
    Elimina una orden por su id.

    Primero borra las líneas de detalle una por una (disparando el trigger
    trg_detalle_orden_restaurar_stock que devuelve el stock de refacciones),
    y luego borra la cabecera. La BD usa ON DELETE CASCADE como respaldo,
    pero el borrado explícito de detalles es necesario para que los triggers
    se ejecuten (MariaDB no dispara triggers en cascada).
    """
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        conexion.autocommit = False

        # 1. Leer detalles para saber qué restaurar (opcional: el trigger ya lo hace)
        cursor.execute(
            "SELECT detalle_id, tipo, item_id, cantidad FROM detalle_orden WHERE orden_id = %s",
            (orden_id,),
        )
        detalles = cursor.fetchall()

        # 2. Borrar cada detalle explícitamente (dispara trigger AFTER DELETE)
        for detalle_id, tipo, item_id, cantidad in detalles:
            cursor.execute(
                "DELETE FROM detalle_orden WHERE detalle_id = %s",
                (detalle_id,),
            )

        # 3. Borrar la cabecera (ON DELETE CASCADE borraría restos, si los hubiera)
        cursor.execute("DELETE FROM ordenes WHERE orden_id = %s", (orden_id,))
        if cursor.rowcount == 0:
            raise RuntimeError("La orden no existe.")

        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as error:
        try:
            conexion.rollback()
            cursor.close()
            conexion.close()
        except Exception:
            pass
        raise RuntimeError(f"No se pudo eliminar la orden: {error}") from error


def cambiar_estado(orden_id: int, nuevo_estado: str) -> None:
    """
    Cambia el estado del flujo de trabajo de la orden.

    al pasar a 'terminada' se registra automáticamente la fecha/hora
    de salida; los demás estados no tocan esos campos.
    'pagada' es la meta del módulo de cobros (fase posterior).
    """
    if nuevo_estado not in EstadoValido:
        raise RuntimeError(f"Estado no reconocido: {nuevo_estado}")
    if nuevo_estado == "abierta":
        raise RuntimeError("Una orden no puede regresar a 'abierta'.")

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        if nuevo_estado == "terminada":
            # Al cerrar el trabajo se marca la salida (según la BD, los
            # campos se complementan con CURDATE/CURTIME)
            cursor.execute(
                "UPDATE ordenes SET estado = %s, fecha_salida = CURDATE(), "
                "hora_salida = CURTIME() WHERE orden_id = %s",
                (nuevo_estado, orden_id),
            )
        else:
            cursor.execute(
                "UPDATE ordenes SET estado = %s WHERE orden_id = %s",
                (nuevo_estado, orden_id),
            )
        if cursor.rowcount == 0:
            raise RuntimeError("La orden no existe o ya era la misma.")
        conexion.commit()
        cursor.close()
        conexion.close()
    except RuntimeError:
        raise  # Mensajes ya claros
    except Exception as error:
        raise RuntimeError(f"No se pudo cambiar el estado de la orden: {error}") from error
