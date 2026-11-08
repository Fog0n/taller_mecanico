"""
Modelo de dominio: vehículo registrado en el taller.
"""

from dataclasses import dataclass


@dataclass
class Vehiculo:
    """
    Representa un vehículo de un cliente (tabla vehiculos).

    La matricula es la clave primaria natural: NO se modifica
    después de registrar el vehículo.
    """

    matricula: str
    modelo: str
    marca: str
    color: str | None  # Opcional: NULO si no se registra
    cliente_id: int    # Dueño del vehículo (FK a clientes)
