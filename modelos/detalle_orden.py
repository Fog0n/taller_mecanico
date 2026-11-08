"""
Modelo de dominio: línea de detalle de una orden.

Cada línea representa un servicio o una refacción aplicada a la
orden; el precio quedó guardado en la línea para que eliminar
el artículo del catálogo no altere órdenes históricas.
"""

from dataclasses import dataclass


@dataclass
class DetalleOrden:
    """Representa una línea del ticket de una orden (tabla detalle_orden)."""

    detalle_id: int
    orden_id: int
    tipo: str                 # 'servicio' o 'refaccion'
    item_id: int              # servicio_id o refaccion_id según tipo
    cantidad: int
    precio_unitario: float
    subtotal: float
    nombre_item: str | None = None  # Solo para mostrar (LEFT JOIN en dao)
