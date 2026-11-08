"""
Modelo de dominio: usuario del sistema.
"""

from dataclasses import dataclass


@dataclass
class Usuario:
    """Representa un usuario con acceso al sistema (tabla usuarios)."""

    usuario_id: int
    nombre: str
    email: str
    username: str
    password: str  # Texto plano por ahora; se hasheará en etapa posterior
    perfil: str    # 'admin' o 'recepcion'
