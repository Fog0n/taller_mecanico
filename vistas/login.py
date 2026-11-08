"""
Vista de inicio de sesión.

Ventana con autenticación real contra la tabla usuarios de MySQL.
Compara la contraseña en texto plano por ahora; el hashing
se implementará en una etapa posterior.
"""

import customtkinter as ctk

from config import tema
from dao.usuario_dao import obtener_por_username


class LoginVista(ctk.CTk):
    """Ventana principal de la aplicación: inicio de sesión."""

    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("Taller Mecánico - Login")
        self.geometry(tema.LOGIN_SIZE)
        self.resizable(False, False)
        self.center_window()

        # Título
        self.label_titulo = ctk.CTkLabel(
            self,
            text="Taller Mecánico",
            font=tema.FUENTE_TITULO,
            text_color=tema.COLOR_TEXTO,
        )
        self.label_titulo.pack(pady=(50, 25))

        # Campo: usuario
        self.entry_usuario = ctk.CTkEntry(
            self,
            placeholder_text="Usuario",
            width=250,
            font=tema.FUENTE_TEXTO,
        )
        self.entry_usuario.pack(pady=10)

        # Campo: contraseña (oculta)
        self.entry_password = ctk.CTkEntry(
            self,
            placeholder_text="Contraseña",
            width=250,
            font=tema.FUENTE_TEXTO,
            show="*",
        )
        self.entry_password.pack(pady=10)

        # Botón de inicio de sesión
        self.boton_login = ctk.CTkButton(
            self,
            text="Iniciar sesión",
            command=self.iniciar_sesion,
            fg_color=tema.COLOR_BOTON,
            font=tema.FUENTE_BOTON,
            width=250,
        )
        self.boton_login.pack(pady=(20, 10))

        # Label de error (inicialmente vacío)
        self.label_error = ctk.CTkLabel(self, text="", fg_color="transparent")
        self.label_error.pack(pady=5)

    def center_window(self) -> None:
        """Centra la ventana en la pantalla."""
        self.eval("tk::PlaceWindow . center")

    def iniciar_sesion(self) -> None:
        """Valida credenciales contra la BD y abre el menú principal."""
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        # Validación simple de campos vacíos
        if not usuario or not password:
            self.label_error.configure(
                text="Usuario y contraseña son obligatorios.",
                text_color=tema.COLOR_ERROR,
            )
            return

        # Consulta del usuario en la base de datos
        try:
            encontrado = obtener_por_username(usuario)
        except RuntimeError:
            self.label_error.configure(
                text="Sin conexión a MySQL. Verifícalo en el Panel de Control de XAMPP.",
                text_color=tema.COLOR_ERROR,
            )
            return

        # Autenticación: usuario existe y contraseña coincide
        if encontrado is None or encontrado.password != password:
            self.label_error.configure(
                text="Usuario o contraseña incorrectos.",
                text_color=tema.COLOR_ERROR,
            )
            return

        # Login correcto: cerrar login y abrir el menú principal
        from vistas.menu_principal import MenuPrincipalVista  # Import tardío (evita ciclo)

        self.destroy()
        MenuPrincipalVista(encontrado).mainloop()
