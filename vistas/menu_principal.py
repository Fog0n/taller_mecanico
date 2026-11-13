"""
Vista del menú principal.

Ventana con frame lateral de navegación y área central de contenido.
Las pantallas internas (CRUDs, reportes) se implementarán después.
"""

import customtkinter as ctk

from config import tema


class MenuPrincipalVista(ctk.CTk):
    """Ventana principal de la aplicación tras iniciar sesión."""

    def __init__(self, usuario=None):
        super().__init__()

        # Usuario autenticado que abrió la sesión
        self.usuario = usuario

        # Configuración de la ventana
        self.title("Taller Mecánico - Menú Principal")
        self.geometry(tema.MENU_SIZE)
        self.resizable(True, True)
        self.minsize(1000, 650)  # Nunca más pequeño: no se pierde información

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
        comandos = {
            "Clientes": self.abrir_clientes,    # Módulo funcional desde esta fase
            "Vehículos": self.abrir_vehiculos,  # Módulo funcional desde esta fase
            "Órdenes": self.abrir_ordenes,      # Módulo funcional desde esta fase
            "Salir": self.cerrar_sesion,
            # Cobros y Reportes se implementan en fases posteriores
        }
        for texto in textos:
            boton = ctk.CTkButton(
                self.frame_lateral,
                text=texto,
                font=tema.FUENTE_BOTON,
                fg_color=tema.COLOR_BOTON,
                width=180,
                command=comandos.get(texto),
            )
            boton.pack(pady=8, padx=10)

        # Área central de contenido (vacía por ahora)
        self.area_central = ctk.CTkFrame(self, corner_radius=0, fg_color=tema.COLOR_FONDO)
        self.area_central.pack(side="right", fill="both", expand=True)

        # Mensaje de bienvenida (personalizado con el nombre del usuario)
        self.label_bienvenida = ctk.CTkLabel(
            self.area_central,
            text=f"Bienvenido, {self.usuario.nombre}" if self.usuario else "Bienvenido",
            font=tema.FUENTE_TITULO,
            text_color=tema.COLOR_TEXTO,
        )
        self.label_bienvenida.place(relx=0.5, rely=0.5, anchor="center")

    def abrir_clientes(self) -> None:
        """Abre la ventana de administración de clientes."""
        from vistas.clientes import ClientesVista  # Import tardío (evita ciclo)

        ClientesVista(self.usuario).transient(self)  # Encima del menú

    def abrir_vehiculos(self) -> None:
        """Abre la ventana de administración de vehículos."""
        from vistas.vehiculos import VehiculosVista  # Import tardío (evita ciclo)

        VehiculosVista(self.usuario).transient(self)  # Encima del menú

    def abrir_ordenes(self) -> None:
        """Abre la ventana de gestión de órdenes de trabajo."""
        from vistas.ordenes import OrdenesVista  # Import tardío (evita ciclo)

        OrdenesVista(self.usuario).transient(self)  # Encima del menú

    def cerrar_sesion(self) -> None:
        """Cierra la sesión: destruye el menú y vuelve al login."""
        self.destroy()

        from vistas.login import LoginVista  # Import tardío (evita ciclo)

        LoginVista().mainloop()
