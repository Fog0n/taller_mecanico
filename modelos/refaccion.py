"""
Modelo de dominio: refacción del inventario del taller.
"""

from dataclasses import dataclass


@dataclass
class Refaccion:
    """Representa una refacción con su inventario (tabla refacciones)."""

    refaccion_id: int
    nombre: str
    precio: float  # DECIMAL(10,2) en MySQL; Decimal en Python (se muestra igual)
    stock: int
