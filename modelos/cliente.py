"""
Modelo de dominio: cliente del taller.
"""

from dataclasses import dataclass


@dataclass
class Cliente:
    """Representa un cliente atendido por el taller (tabla clientes)."""

    cliente_id: int
    nombre: str
    telefono: str
    email: str | None  # Opcional: NULO si no se registra
    rfc: str | None    # Opcional: NULO si no se registra
    tipo_cliente: str  # 'persona_fisica' o 'empresa'
