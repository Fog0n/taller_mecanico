"""
Punto de entrada de la aplicación "Taller Mecánico".

Aplica el tema visual, verifica la conexión a MySQL (sin abortar
si falla) y abre la ventana de inicio de sesión.
"""

from config import tema  # Aplica modo oscuro y tema azul al importar
from db.conexion import probar_conexion
from vistas.login import LoginVista


def main() -> None:
    """Secuencia de arranque: verificación de BD y ventana de login."""
    # Prueba de conexión (solo informativa, no bloquea la app)
    if probar_conexion():
        print("Conexión a MySQL verificada correctamente.")
    else:
        print(
            "No se pudo conectar a MySQL. Verifica que el servicio MySQL "
            "esté iniciado en el Panel de Control de XAMPP."
        )

    # Interfaz: ventana de login como principal
    app = LoginVista()
    app.mainloop()


if __name__ == "__main__":
    main()
