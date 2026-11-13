"""
Modelo de dominio: pago registrado contra una orden de trabajo.
"""

from dataclasses import dataclass


@dataclass
class Pago:
    """Representa un pago de una orden (tabla pagos)."""

    pago_id: int
    orden_id: int
    monto: float       # DECIMAL(10,2) en MySQL; Decimal en Python (se muestra igual)
    fecha_pago: str    # DATE de la BD (se muestra tal cual)
    metodo_pago: str   # 'efectivo', 'tarjeta' o 'transferencia'
    usuario_id: int    # Usuario que registró el pago