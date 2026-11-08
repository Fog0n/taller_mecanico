"""
Vista de gestión de clientes (módulo completo: alta, edición y baja).

Ventana de módulo (CTkToplevel) abierta desde el menú principal.
La lista soporta muchos clientes vía CTkScrollableFrame y cada fila
tiene botones de Editar y Eliminar.
"""

import tkinter.messagebox
from tkinter.messagebox import askyesno, showwarning

import customtkinter as ctk

from config import tema
from dao import cliente_dao

# Mapeo etiqueta mostrada -> valor enum de la BD
TIPOS_CLIENTE = {
    "Persona física": "persona_fisica",
    "Empresa": "empresa",
}


class ClientesVista(ctk.CTkToplevel):
    """Ventana de administración de clientes."""

    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario

        # Configuración de la ventana
        self.title("Taller Mecánico - Clientes")
        self.geometry("860x620")
        self.resizable(False, False)

        # Formulario (zona superior)
        self.frame_formulario = ctk.CTkFrame(self)
        self.frame_formulario.pack(fill="x", padx=15, pady=15)

        # id del cliente en edición (None = formulario en modo alta)
        self.cliente_seleccionado: int | None = None

        # Campos del formulario
        self.entry_nombre = self._campo(self.frame_formulario, "Nombre *", 0, 0)
        self.entry_telefono = self._campo(self.frame_formulario, "Teléfono *", 0, 1)
        self.entry_email = self._campo(self.frame_formulario, "Email", 0, 2)
        self.entry_rfc = self._campo(self.frame_formulario, "RFC", 0, 3)
        self.combo_tipo = self._combo(self.frame_formulario)

        # Botones de acción del formulario (misma línea que el combo de tipo)
        self.boton_agregar = ctk.CTkButton(
            self.frame_formulario, text="Agregar cliente", command=self.agregar_cliente,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON,
        )
        self.boton_agregar.grid(row=3, column=1, padx=10, pady=(15, 5), sticky="w")

        self.boton_guardar = ctk.CTkButton(
            self.frame_formulario, text="Guardar cambios", command=self.guardar_cambios,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON, state="disabled",
        )
        self.boton_guardar.grid(row=3, column=2, padx=10, pady=(15, 5))

        self.boton_limpiar = ctk.CTkButton(
            self.frame_formulario, text="Limpiar", command=self.limpiar_formulario,
            fg_color="#4b5563", font=tema.FUENTE_TEXTO,
        )
        self.boton_limpiar.grid(row=3, column=3, padx=10, pady=(15, 5))

        # Lista de clientes (zona inferior, desplazable)
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Clientes registrados")
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Mensaje de estado de la operación en BD
        self.label_estado = ctk.CTkLabel(self, text="", text_color=tema.COLOR_TEXTO)
        self.label_estado.pack(pady=(0, 5))

        self.refrescar_lista()

    # ------------------------------------------------------------------ #
    # Construcción de campos reutilizables
    # ------------------------------------------------------------------ #
    def _campo(self, padre, etiqueta, fila, columna) -> ctk.CTkEntry:
        """Crea un campo del formulario con su etiqueta y lo devuelve."""
        ctk.CTkLabel(padre, text=etiqueta, font=tema.FUENTE_TEXTO).grid(row=fila * 2, column=columna, padx=10, sticky="w")
        entrada = ctk.CTkEntry(padre, width=180, font=tema.FUENTE_TEXTO)
        entrada.grid(row=fila * 2 + 1, column=columna, padx=10, pady=(2, 10))
        return entrada

    def _combo(self, padre) -> ctk.CTkComboBox:
        """Crea el selector de tipo de cliente."""
        ctk.CTkLabel(padre, text="Tipo de cliente", font=tema.FUENTE_TEXTO).grid(row=2, column=0, padx=10, sticky="w")
        combo = ctk.CTkComboBox(
            padre,
            values=list(TIPOS_CLIENTE.keys()),
            width=180,
            font=tema.FUENTE_TEXTO,
            state="readonly",
        )
        combo.set("Persona física")
        combo.grid(row=3, column=0, padx=10, pady=(2, 10))
        return combo

    # ------------------------------------------------------------------ #
    # Utilidades del formulario y de la lista
    # ------------------------------------------------------------------ #
    def _valores_formulario(self):
        """Lee el formulario; devuelve tupla o None si falta un campo obligatorio."""
        nombre = self.entry_nombre.get().strip()
        telefono = self.entry_telefono.get().strip()
        email = self.entry_email.get().strip() or None
        rfc = self.entry_rfc.get().strip() or None
        tipo = TIPOS_CLIENTE[self.combo_tipo.get()]

        if not nombre or not telefono:
            showwarning("Datos incompletos", "Nombre y teléfono son obligatorios.")
            return None
        return nombre, telefono, email, rfc, tipo

    def _mensaje(self, texto: str, es_error: bool = False) -> None:
        """Muestra el resultado de la última operación."""
        self.label_estado.configure(
            text=texto, text_color=tema.COLOR_ERROR if es_error else tema.COLOR_TEXTO,
        )

    def refrescar_lista(self) -> None:
        """Vuelve a pintar la lista desde la base de datos."""
        # Limpia filas actuales
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        # Encabezado
        self._fila_encabezado()

        try:
            clientes = cliente_dao.obtener_todos()
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return

        # Una fila por cliente
        for i, cliente in enumerate(clientes):
            self._fila_cliente(i, cliente, fondo=i % 2 == 1)

        self._mensaje(f"{len(clientes)} cliente(s) registrados.")

    def _fila_encabezado(self) -> None:
        """Pinta la cabecera de la tabla."""
        anchos = [8, 25, 15, 22, 16, 14]
        textos = ["#", "Nombre", "Teléfono", "Email", "RFC", "Tipo"]
        for col, (texto, peso) in enumerate(zip(textos, anchos)):
            ctk.CTkLabel(
                self.frame_lista, text=texto.ljust(peso),
                font=tema.FUENTE_BOTON, text_color="#9ca3af",
                anchor="w",
            ).grid(row=0, column=col, padx=(5, 5), sticky="w")
        self.frame_lista.grid_columnconfigure(len(anchos) + 1, weight=2)  # columna de botones

    def _fila_cliente(self, indice: int, cliente, fondo: bool) -> None:
        """Pinta una fila de cliente con sus botones Editar / Eliminar.

        La primera columna es enumeración visual consecutiva (#1, #2, ...);
        el cliente_id real de la BD queda interno y se usa en las acciones.
        """
        fila = indice + 1
        color = "#252525" if fondo else "transparent"
        textos = [
            f"#{indice + 1}",  # Numeración de posición (estética de lista)
            cliente.nombre,
            cliente.telefono,
            cliente.email or "",
            cliente.rfc or "",
            cliente.tipo_cliente.replace("_", " "),
        ]
        # Etiquetas de datos (columnas 0 a 5)
        for col, texto in enumerate(textos):
            ctk.CTkLabel(
                self.frame_lista, text=texto, font=tema.FUENTE_TEXTO,
                text_color=tema.COLOR_TEXTO, anchor="w", fg_color=color,
            ).grid(row=fila, column=col, padx=5, sticky="w")

        # Botones de acción de la fila (columnas 6 y 7)
        ctk.CTkButton(
            self.frame_lista, text="Editar", width=70, height=24,
            fg_color="#4b5563", font=("Arial", 11),
            command=lambda c=cliente: self.cargar_cliente(c),
        ).grid(row=fila, column=6, padx=5, pady=3)

        ctk.CTkButton(
            self.frame_lista, text="Eliminar", width=70, height=24,
            fg_color=tema.COLOR_ERROR, font=("Arial", 11),
            command=lambda c=cliente: self.eliminar_cliente(c),
        ).grid(row=fila, column=7, padx=5, pady=3)

    # ------------------------------------------------------------------ #
    # Acciones CRUD
    # ------------------------------------------------------------------ #
    def agregar_cliente(self) -> None:
        """INSERT de cliente nuevo desde el formulario."""
        datos = self._valores_formulario()
        if datos is None:
            return
        try:
            cliente_dao.crear(*datos)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.limpiar_formulario()
        self.refrescar_lista()

    def guardar_cambios(self) -> None:
        """UPDATE del cliente seleccionado con los datos del formulario."""
        if self.cliente_seleccionado is None:
            showwarning("Sin selección", "Pulsa 'Editar' en un cliente de la lista para modificarlo.")
            return
        datos = self._valores_formulario()
        if datos is None:
            return
        try:
            cliente_dao.actualizar(self.cliente_seleccionado, *datos)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.limpiar_formulario()
        self.refrescar_lista()

    def eliminar_cliente(self, cliente) -> None:
        """DELETE tras confirmación; advierte del borrado en cascada."""
        respuesta = askyesno(
            "Confirmar eliminación",
            f"¿Eliminar a {cliente.nombre}?\n\n"
            "También se borrarán sus vehículos y órdenes asociadas.",
        )
        if not respuesta:
            return
        try:
            cliente_dao.eliminar(cliente.cliente_id)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.refrescar_lista()

    def cargar_cliente(self, cliente) -> None:
        """Carga un cliente en el formulario y activa el modo edición."""
        self.cliente_seleccionado = cliente.cliente_id
        self.entry_nombre.delete(0, "end"); self.entry_nombre.insert(0, cliente.nombre)
        self.entry_telefono.delete(0, "end"); self.entry_telefono.insert(0, cliente.telefono)
        self.entry_email.delete(0, "end"); self.entry_email.insert(0, cliente.email or "")
        self.entry_rfc.delete(0, "end"); self.entry_rfc.insert(0, cliente.rfc or "")
        self.combo_tipo.set(
            "Empresa" if cliente.tipo_cliente == "empresa" else "Persona física"
        )
        self.boton_agregar.configure(state="disabled")
        self.boton_guardar.configure(state="normal")
        self._mensaje(f"Editando: {cliente.nombre}")

    def limpiar_formulario(self) -> None:
        """Deja el formulario vacío y en modo alta."""
        self.cliente_seleccionado = None
        self.entry_nombre.delete(0, "end")
        self.entry_telefono.delete(0, "end")
        self.entry_email.delete(0, "end")
        self.entry_rfc.delete(0, "end")
        self.combo_tipo.set("Persona física")
        self.boton_agregar.configure(state="normal")
        self.boton_guardar.configure(state="disabled")
