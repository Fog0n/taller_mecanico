"""
Vista del menú principal.

Ventana con frame lateral de navegación y área central de contenido.
Las pantallas internas (CRUDs, reportes) se implementarán después.
"""

import customtkinter as ctk

from config import tema


class MenuPrincipalVista(ctk.CTk):
    """Ventana principal de la aplicación tras iniciar sesión."""

    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("Taller Mecánico - Menú Principal")
        self.geometry(tema.MENU_SIZE)
        self.resizable(False, False)

        # Frame lateral (barra de navegación)
        self.frame_lateral = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.frame_lateral.pack(side="left", fill="y")

        # Título del panel lateral
        ctk.CTkLabel(
            self.frame_lateral,
            text="Taller Mecánico",
            font=tema.FUENTE_TITULO,
            text_color=tema.COLOR_TEXTO,
        ).pack(pady=(25, 20))

        # Botones de navegación
        textos = ["Clientes", "Vehículos", "Órdenes", "Cobros", "Reportes", "Salir"]
        for texto in textos:
            boton = ctk.CTkButton(
                self.frame_lateral,
                text=texto,
                font=tema.FUENTE_BOTON,
                fg_color=tema.COLOR_BOTON,
                width=180,
                # Por ahora "Salir" cierra la sesión; el resto son marcadores
                command=(self.cerrar_sesion if texto == "Salir" else None),
            )
            boton.pack(pady=8, padx=10)

        # Área central de contenido (vacía por ahora)
        self.area_central = ctk.CTkFrame(self, corner_radius=0, fg_color=tema.COLOR_FONDO)
        self.area_central.pack(side="right", fill="both", expand=True)

        # Mensaje de bienvenida
        self.label_bienvenida = ctk.CTkLabel(
            self.area_central,
            text="Bienvenido",
            font=tema.FUENTE_TITULO,
            text_color=tema.COLOR_TEXTO,
        )
        self.label_bienvenida.place(relx=0.5, rely=0.5, anchor="center")

    def cerrar_sesion(self) -> None:
        """Cierra la ventana (se reabrirá el login en una etapa posterior)."""
        self.destroy()
