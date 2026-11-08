"""
Modelo de dominio: servicio del catálogo (mano de obra).
"""

from dataclasses import dataclass


@dataclass
class Servicio:
    """Representa un servicio del catálogo (tabla servicios)."""

    servicio_id: int
    nombre: str
    precio: float  # DECIMAL(10,2) en MySQL; Decimal en Python (se muestra igual)
