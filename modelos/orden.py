"""
Modelo de dominio: orden de trabajo del taller.
"""

from dataclasses import dataclass


@dataclass
class Orden:
    """Representa una orden de trabajo sobre un vehículo (tabla ordenes)."""

    orden_id: int
    matricula: str
    cliente_id: int
    usuario_id: int          # Usuario que levantó la orden
    fecha_entrada: "datetime.date"
    hora_entrada: "datetime.time"
    fecha_salida: "datetime.date | None"
    hora_salida: "datetime.time | None"
    estado: str              # abierta/en_proceso/terminada/entregada/pagada
