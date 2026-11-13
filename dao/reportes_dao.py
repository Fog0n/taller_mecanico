"""
DAO de reportes: consultas de lectura para el módulo de Reportes.

Solo ejecuta SELECTs agregados; no modifica datos. Todas las funciones
reciben un rango de fechas (desde/hasta inclusive) como 'AAAA-MM-DD'.

Criterios de medición (coherentes con Cobros y Órdenes):
- INGRESOS: se miden por pagos COBRADOS (pagos.fecha_pago).
- ORDENES/SERVICIOS/REFACCIONES: se miden por órdenes CREADAS
  (ordenes.fecha_entrada).
"""

from decimal import Decimal

from db.conexion import obtener_conexion


def _ejecutar_lectura(sql: str, parametros: tuple = ()) -> list[tuple]:
    """Ejecuta un SELECT de lectura y convierte montos DECIMAL a float."""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)
        filas = [
            tuple(float(valor) if isinstance(valor, Decimal) else valor for valor in fila)
            for fila in cursor.fetchall()
        ]
        cursor.close()
        conexion.close()
        return filas
    except Exception as error:
        raise RuntimeError(f"No se pudo generar el reporte: {error}") from error


# --------------------------------------------------------------------- #
# Resumen general
# --------------------------------------------------------------------- #
def resumen_general(desde: str, hasta: str) -> dict:
    """Indicadores del periodo: cobrado, órdenes, ticket promedio y clientes."""
    (cobrado, num_pagos), = _ejecutar_lectura(
        "SELECT COALESCE(SUM(monto), 0), COUNT(*) FROM pagos "
        "WHERE fecha_pago BETWEEN %s AND %s",
        (desde, hasta),
    )
    (num_ordenes, num_clientes), = _ejecutar_lectura(
        "SELECT COUNT(*), COUNT(DISTINCT cliente_id) FROM ordenes "
        "WHERE fecha_entrada BETWEEN %s AND %s",
        (desde, hasta),
    )
    return {
        "cobrado": cobrado,
        "ordenes": num_ordenes,
        "ticket_promedio": round(cobrado / num_pagos, 2) if num_pagos else 0.0,
        "clientes": num_clientes,
    }


# --------------------------------------------------------------------- #
# Ingresos (tabla pagos)
# --------------------------------------------------------------------- #
def ingresos_por_dia(desde: str, hasta: str) -> list[tuple]:
    """Devuelve (fecha, numero_de_pagos, monto_total) por día con cobros."""
    return _ejecutar_lectura(
        "SELECT fecha_pago, COUNT(*), SUM(monto) FROM pagos "
        "WHERE fecha_pago BETWEEN %s AND %s "
        "GROUP BY fecha_pago ORDER BY fecha_pago",
        (desde, hasta),
    )


def ingresos_por_metodo(desde: str, hasta: str) -> list[tuple]:
    """Devuelve (metodo, numero_de_pagos, monto, porcentaje) por método."""
    filas = _ejecutar_lectura(
        "SELECT metodo_pago, COUNT(*), SUM(monto) FROM pagos "
        "WHERE fecha_pago BETWEEN %s AND %s "
        "GROUP BY metodo_pago ORDER BY metodo_pago",
        (desde, hasta),
    )
    total = sum(monto for (_m, _n, monto) in filas)
    return [
        (metodo, numero, monto, round(monto / total * 100, 1) if total else 0.0)
        for (metodo, numero, monto) in filas
    ]


def ingresos_por_cliente(desde: str, hasta: str, limite: int) -> list[tuple]:
    """Devuelve (cliente, numero_de_pagos, monto) por cliente, top 'limite'."""
    return _ejecutar_lectura(
        "SELECT c.nombre, COUNT(p.pago_id), SUM(p.monto) "
        "FROM pagos p "
        "JOIN ordenes o ON o.orden_id = p.orden_id "
        "JOIN clientes c ON c.cliente_id = o.cliente_id "
        "WHERE p.fecha_pago BETWEEN %s AND %s "
        "GROUP BY c.cliente_id, c.nombre "
        "ORDER BY SUM(p.monto) DESC LIMIT %s",
        (desde, hasta, limite),
    )


def actividad_por_usuario(desde: str, hasta: str) -> list[tuple]:
    """Devuelve (usuario, ordenes_creadas, pagos_registrados, cobrado)."""
    return _ejecutar_lectura(
        "SELECT u.nombre, COALESCE(o.n, 0), COALESCE(p.n, 0), COALESCE(p.cobrado, 0) "
        "FROM usuarios u "
        "LEFT JOIN (SELECT usuario_id, COUNT(*) AS n FROM ordenes "
        "           WHERE fecha_entrada BETWEEN %s AND %s GROUP BY usuario_id) o "
        "       ON o.usuario_id = u.usuario_id "
        "LEFT JOIN (SELECT usuario_id, COUNT(*) AS n, SUM(monto) AS cobrado FROM pagos "
        "           WHERE fecha_pago BETWEEN %s AND %s GROUP BY usuario_id) p "
        "       ON p.usuario_id = u.usuario_id "
        "ORDER BY COALESCE(p.cobrado, 0) DESC",
        (desde, hasta, desde, hasta),
    )


# --------------------------------------------------------------------- #
# Órdenes y ventas (tabla ordenes / detalle_orden)
# --------------------------------------------------------------------- #
def ordenes_por_estado(desde: str, hasta: str) -> list[tuple]:
    """Devuelve (estado, numero_de_ordenes, valor_total) por estado."""
    return _ejecutar_lectura(
        "SELECT o.estado, COUNT(DISTINCT o.orden_id), COALESCE(SUM(d.subtotal), 0) "
        "FROM ordenes o LEFT JOIN detalle_orden d ON d.orden_id = o.orden_id "
        "WHERE o.fecha_entrada BETWEEN %s AND %s "
        "GROUP BY o.estado",
        (desde, hasta),
    )


def top_servicios(desde: str, hasta: str, limite: int) -> list[tuple]:
    """Devuelve (servicio, cantidad_vendida, dinero) top 'limite' del rango."""
    return _ejecutar_lectura(
        "SELECT s.nombre, SUM(d.cantidad), SUM(d.subtotal) "
        "FROM detalle_orden d "
        "JOIN ordenes o ON o.orden_id = d.orden_id "
        "JOIN servicios s ON s.servicio_id = d.item_id "
        "WHERE d.tipo = 'servicio' AND o.fecha_entrada BETWEEN %s AND %s "
        "GROUP BY s.servicio_id, s.nombre "
        "ORDER BY SUM(d.subtotal) DESC LIMIT %s",
        (desde, hasta, limite),
    )


def top_refacciones(desde: str, hasta: str, limite: int) -> list[tuple]:
    """Devuelve (refaccion, cantidad_vendida, dinero) top 'limite' del rango."""
    return _ejecutar_lectura(
        "SELECT r.nombre, SUM(d.cantidad), SUM(d.subtotal) "
        "FROM detalle_orden d "
        "JOIN ordenes o ON o.orden_id = d.orden_id "
        "JOIN refacciones r ON r.refaccion_id = d.item_id "
        "WHERE d.tipo = 'refaccion' AND o.fecha_entrada BETWEEN %s AND %s "
        "GROUP BY r.refaccion_id, r.nombre "
        "ORDER BY SUM(d.subtotal) DESC LIMIT %s",
        (desde, hasta, limite),
    )
