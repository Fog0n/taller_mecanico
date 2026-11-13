"""
Vista de catálogos del taller: servicios y refacciones con inventario.

Ventana de módulo (CTkToplevel) con pestañas. Permite dar de alta,
editar y eliminar servicios (mano de obra) y refacciones (repuestos),
con ajuste manual de stock mediante entradas/salidas de inventario.

Las órdenes históricas conservan precio y nombre congelados en
detalle_orden, así que eliminar un ítem del catálogo no rompe nada.
"""

import tkinter.messagebox
from tkinter.messagebox import askyesno, showwarning

import customtkinter as ctk

from config import tema
from dao import servicio_dao
from dao import refaccion_dao


class CatalogosVista(ctk.CTkToplevel):
    """Ventana de administración de catálogos (servicios y refacciones)."""

    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario

        # Selección en modo edición (None = alta) por pestaña
        self.servicio_seleccionado: int | None = None
        self.refaccion_seleccionada: int | None = None

        # Configuración de la ventana
        self.title("Taller Mecánico - Catálogos")
        self.geometry(tema.MODULO_SIZE)
        self.resizable(True, True)
        self.minsize(1000, 680)  # Nunca más pequeño: no se pierde información

        # Pestañas del módulo
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(15, 5))
        self.tab_servicios = self.tabview.add("Servicios")
        self.tab_refacciones = self.tabview.add("Refacciones")

        self._construir_servicios()
        self._construir_refacciones()

        # Mensaje de estado de la operación en BD
        self.label_estado = ctk.CTkLabel(self, text="", text_color=tema.COLOR_TEXTO)
        self.label_estado.pack(pady=(0, 8))

        self.refrescar_servicios()
        self.refrescar_refacciones()

    # ------------------------------------------------------------------ #
    # Construcción de pestañas
    # ------------------------------------------------------------------ #
    def _construir_servicios(self) -> None:
        """Pestaña Servicios: formulario + lista del catálogo."""
        frame = ctk.CTkFrame(self.tab_servicios)
        frame.pack(fill="x", padx=10, pady=(10, 5))
        for col in (0, 1):
            frame.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(frame, text="Nombre *", font=tema.FUENTE_TEXTO).grid(row=0, column=0, padx=10, sticky="w")
        self.entry_serv_nombre = ctk.CTkEntry(frame, width=240, font=tema.FUENTE_TEXTO)
        self.entry_serv_nombre.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")

        ctk.CTkLabel(frame, text="Precio ($) *", font=tema.FUENTE_TEXTO).grid(row=0, column=1, padx=10, sticky="w")
        self.entry_serv_precio = ctk.CTkEntry(frame, width=140, font=tema.FUENTE_TEXTO)
        self.entry_serv_precio.grid(row=1, column=1, padx=10, pady=(2, 10), sticky="ew")

        self.boton_serv_agregar = ctk.CTkButton(
            frame, text="Agregar servicio", command=self.agregar_servicio,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON,
        )
        self.boton_serv_agregar.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="w")

        self.boton_serv_guardar = ctk.CTkButton(
            frame, text="Guardar cambios", command=self.guardar_servicio,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON, state="disabled",
        )
        self.boton_serv_guardar.grid(row=2, column=1, padx=10, pady=(5, 10))

        ctk.CTkButton(
            frame, text="Limpiar", command=self.limpiar_servicio,
            fg_color="#4b5563", font=tema.FUENTE_TEXTO,
        ).grid(row=2, column=2, padx=10, pady=(5, 10))

        self.frame_lista_serv = ctk.CTkScrollableFrame(
            self.tab_servicios, label_text="Servicios del catálogo",
        )
        self.frame_lista_serv.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _construir_refacciones(self) -> None:
        """Pestaña Refacciones: formulario con stock + lista del inventario."""
        frame = ctk.CTkFrame(self.tab_refacciones)
        frame.pack(fill="x", padx=10, pady=(10, 5))
        for col in (0, 1, 2):
            frame.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(frame, text="Nombre *", font=tema.FUENTE_TEXTO).grid(row=0, column=0, padx=10, sticky="w")
        self.entry_ref_nombre = ctk.CTkEntry(frame, width=240, font=tema.FUENTE_TEXTO)
        self.entry_ref_nombre.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")

        ctk.CTkLabel(frame, text="Precio ($) *", font=tema.FUENTE_TEXTO).grid(row=0, column=1, padx=10, sticky="w")
        self.entry_ref_precio = ctk.CTkEntry(frame, width=140, font=tema.FUENTE_TEXTO)
        self.entry_ref_precio.grid(row=1, column=1, padx=10, pady=(2, 10), sticky="ew")

        ctk.CTkLabel(frame, text="Stock (unid.) *", font=tema.FUENTE_TEXTO).grid(row=0, column=2, padx=10, sticky="w")
        self.entry_ref_stock = ctk.CTkEntry(frame, width=110, font=tema.FUENTE_TEXTO)
        self.entry_ref_stock.insert(0, "0")
        self.entry_ref_stock.grid(row=1, column=2, padx=10, pady=(2, 10), sticky="ew")

        self.boton_ref_agregar = ctk.CTkButton(
            frame, text="Agregar refacción", command=self.agregar_refaccion,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON,
        )
        self.boton_ref_agregar.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="w")

        self.boton_ref_guardar = ctk.CTkButton(
            frame, text="Guardar cambios", command=self.guardar_refaccion,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON, state="disabled",
        )
        self.boton_ref_guardar.grid(row=2, column=1, padx=10, pady=(5, 10))

        ctk.CTkButton(
            frame, text="Limpiar", command=self.limpiar_refaccion,
            fg_color="#4b5563", font=tema.FUENTE_TEXTO,
        ).grid(row=2, column=2, padx=10, pady=(5, 10), sticky="e")

        self.frame_lista_ref = ctk.CTkScrollableFrame(
            self.tab_refacciones, label_text="Refacciones e inventario",
        )
        self.frame_lista_ref.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ------------------------------------------------------------------ #
    # Utilidades comunes
    # ------------------------------------------------------------------ #
    def _asignar(self, entrada: ctk.CTkEntry, valor: str) -> None:
        """Reemplaza el contenido de un campo (útil en modo edición)."""
        entrada.configure(state="normal")
        entrada.delete(0, "end")
        entrada.insert(0, valor)

    def _precio_valido(self, texto: str) -> float | None:
        """Lee y valida un precio: número mayor a cero."""
        try:
            precio = float(texto.strip())
        except ValueError:
            showwarning("Precio inválido", "El precio debe ser un número (ej. 350 o 350.50).")
            return None
        if precio <= 0:
            showwarning("Precio inválido", "El precio debe ser mayor a cero.")
            return None
        return round(precio, 2)

    def _stock_valido(self, texto: str) -> int | None:
        """Lee y valida un stock: entero mayor o igual a cero."""
        try:
            stock = int(texto.strip())
        except ValueError:
            showwarning("Stock inválido", "El stock debe ser un número entero de unidades.")
            return None
        if stock < 0:
            showwarning("Stock inválido", "El stock no puede ser negativo.")
            return None
        return stock

    def _mensaje(self, texto: str, es_error: bool = False) -> None:
        """Muestra el resultado de la última operación."""
        self.label_estado.configure(
            text=texto, text_color=tema.COLOR_ERROR if es_error else tema.COLOR_TEXTO,
        )

    # ------------------------------------------------------------------ #
    # Servicios: lista y acciones CRUD
    # ------------------------------------------------------------------ #
    def refrescar_servicios(self) -> None:
        """Vuelve a pintar la lista de servicios desde la base de datos."""
        for widget in self.frame_lista_serv.winfo_children():
            widget.destroy()

        # Cabecera
        anchos = [8, 40, 16]
        for col, (texto, peso) in enumerate(zip(["#", "Nombre", "Precio"], anchos)):
            ctk.CTkLabel(
                self.frame_lista_serv, text=texto.ljust(peso),
                font=tema.FUENTE_BOTON, text_color="#9ca3af", anchor="w",
            ).grid(row=0, column=col, padx=5, sticky="w")
        for col, peso in enumerate([0, 3, 2, 0, 0]):
            self.frame_lista_serv.grid_columnconfigure(col, weight=peso)

        try:
            servicios = servicio_dao.obtener_todos()
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return

        for i, servicio in enumerate(servicios):
            fila = i + 1
            color = "#252525" if i % 2 == 1 else "transparent"
            datos = [f"#{i + 1}", servicio.nombre, f"${servicio.precio:.2f}"]
            for col, texto in enumerate(datos):
                ctk.CTkLabel(
                    self.frame_lista_serv, text=texto, font=tema.FUENTE_TEXTO,
                    text_color=tema.COLOR_TEXTO, anchor="w", fg_color=color,
                ).grid(row=fila, column=col, padx=5, sticky="w")

            ctk.CTkButton(
                self.frame_lista_serv, text="Editar", width=70, height=24,
                fg_color="#4b5563", font=("Arial", 11),
                command=lambda s=servicio: self.cargar_servicio(s),
            ).grid(row=fila, column=3, padx=5, pady=3)

            ctk.CTkButton(
                self.frame_lista_serv, text="Eliminar", width=70, height=24,
                fg_color=tema.COLOR_ERROR, font=("Arial", 11),
                command=lambda s=servicio: self.eliminar_servicio(s),
            ).grid(row=fila, column=4, padx=5, pady=3)

    def _valores_servicio(self):
        """Lee nombre y precio; devuelve tupla o None si algo falta."""
        nombre = self.entry_serv_nombre.get().strip()
        precio = self._precio_valido(self.entry_serv_precio.get())
        if not nombre:
            showwarning("Datos incompletos", "El nombre del servicio es obligatorio.")
            return None
        if precio is None:
            return None
        return nombre, precio

    def agregar_servicio(self) -> None:
        """INSERT de servicio nuevo desde el formulario."""
        datos = self._valores_servicio()
        if datos is None:
            return
        try:
            servicio_dao.crear(*datos)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.limpiar_servicio()
        self.refrescar_servicios()
        self._mensaje(f"Servicio '{datos[0]}' agregado al catálogo.")

    def guardar_servicio(self) -> None:
        """UPDATE del servicio seleccionado con los datos del formulario."""
        if self.servicio_seleccionado is None:
            showwarning("Sin selección", "Pulsa 'Editar' en un servicio de la lista para modificarlo.")
            return
        datos = self._valores_servicio()
        if datos is None:
            return
        try:
            servicio_dao.actualizar(self.servicio_seleccionado, *datos)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.limpiar_servicio()
        self.refrescar_servicios()
        self._mensaje(f"Servicio '{datos[0]}' actualizado.")

    def cargar_servicio(self, servicio) -> None:
        """Carga un servicio en el formulario y activa el modo edición."""
        self.servicio_seleccionado = servicio.servicio_id
        self._asignar(self.entry_serv_nombre, servicio.nombre)
        self._asignar(self.entry_serv_precio, str(servicio.precio))
        self.boton_serv_agregar.configure(state="disabled")
        self.boton_serv_guardar.configure(state="normal")
        self._mensaje(f"Editando servicio: {servicio.nombre}")

    def limpiar_servicio(self) -> None:
        """Deja el formulario de servicios vacío y en modo alta."""
        self.servicio_seleccionado = None
        self._asignar(self.entry_serv_nombre, "")
        self._asignar(self.entry_serv_precio, "")
        self.boton_serv_agregar.configure(state="normal")
        self.boton_serv_guardar.configure(state="disabled")

    def eliminar_servicio(self, servicio) -> None:
        """DELETE del catálogo tras confirmación (la historia no se rompe)."""
        respuesta = askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el servicio '{servicio.nombre}' del catálogo?\n\n"
            "Las órdenes históricas conservan su precio y nombre grabados.",
        )
        if not respuesta:
            return
        try:
            servicio_dao.eliminar(servicio.servicio_id)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.refrescar_servicios()
        self._mensaje(f"Servicio '{servicio.nombre}' eliminado del catálogo.")

    # ------------------------------------------------------------------ #
    # Refacciones: lista, inventario y acciones CRUD
    # ------------------------------------------------------------------ #
    def refrescar_refacciones(self) -> None:
        """Vuelve a pintar la lista de refacciones desde la base de datos."""
        for widget in self.frame_lista_ref.winfo_children():
            widget.destroy()

        # Cabecera
        anchos = [8, 40, 16, 14]
        for col, (texto, peso) in enumerate(zip(["#", "Nombre", "Precio", "Stock"], anchos)):
            ctk.CTkLabel(
                self.frame_lista_ref, text=texto.ljust(peso),
                font=tema.FUENTE_BOTON, text_color="#9ca3af", anchor="w",
            ).grid(row=0, column=col, padx=5, sticky="w")
        for col, peso in enumerate([0, 3, 2, 1, 0, 0, 0]):
            self.frame_lista_ref.grid_columnconfigure(col, weight=peso)

        try:
            refacciones = refaccion_dao.obtener_todos()
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return

        for i, refaccion in enumerate(refacciones):
            fila = i + 1
            color = "#252525" if i % 2 == 1 else "transparent"
            sin_stock = refaccion.stock == 0
            datos = [
                f"#{i + 1}",
                refaccion.nombre,
                f"${refaccion.precio:.2f}",
                str(refaccion.stock),
            ]
            for col, texto in enumerate(datos):
                ctk.CTkLabel(
                    self.frame_lista_ref, text=texto, font=tema.FUENTE_TEXTO,
                    text_color=tema.COLOR_ERROR if (sin_stock and col == 3) else tema.COLOR_TEXTO,
                    anchor="w", fg_color=color,
                ).grid(row=fila, column=col, padx=5, sticky="w")

            ctk.CTkButton(
                self.frame_lista_ref, text="Editar", width=70, height=24,
                fg_color="#4b5563", font=("Arial", 11),
                command=lambda r=refaccion: self.cargar_refaccion(r),
            ).grid(row=fila, column=4, padx=5, pady=3)

            ctk.CTkButton(
                self.frame_lista_ref, text="± Stock", width=70, height=24,
                fg_color="#8b5cf6", font=("Arial", 11),
                command=lambda r=refaccion: self._dialogo_ajuste_stock(r),
            ).grid(row=fila, column=5, padx=5, pady=3)

            ctk.CTkButton(
                self.frame_lista_ref, text="Eliminar", width=70, height=24,
                fg_color=tema.COLOR_ERROR, font=("Arial", 11),
                command=lambda r=refaccion: self.eliminar_refaccion(r),
            ).grid(row=fila, column=6, padx=5, pady=3)

    def _valores_refaccion(self):
        """Lee nombre, precio y stock; devuelve tupla o None si algo falta."""
        nombre = self.entry_ref_nombre.get().strip()
        precio = self._precio_valido(self.entry_ref_precio.get())
        stock = self._stock_valido(self.entry_ref_stock.get())
        if not nombre:
            showwarning("Datos incompletos", "El nombre de la refacción es obligatorio.")
            return None
        if precio is None or stock is None:
            return None
        return nombre, precio, stock

    def agregar_refaccion(self) -> None:
        """INSERT de refacción nueva (con stock inicial) desde el formulario."""
        datos = self._valores_refaccion()
        if datos is None:
            return
        try:
            refaccion_dao.crear(*datos)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.limpiar_refaccion()
        self.refrescar_refacciones()
        self._mensaje(f"Refacción '{datos[0]}' agregada (stock inicial: {datos[2]} unid.).")

    def guardar_refaccion(self) -> None:
        """UPDATE de la refacción seleccionada (ajuste manual de stock incluido)."""
        if self.refaccion_seleccionada is None:
            showwarning("Sin selección", "Pulsa 'Editar' en una refacción de la lista para modificarla.")
            return
        datos = self._valores_refaccion()
        if datos is None:
            return
        try:
            refaccion_dao.actualizar(self.refaccion_seleccionada, *datos)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.limpiar_refaccion()
        self.refrescar_refacciones()
        self._mensaje(f"Refacción '{datos[0]}' actualizada (stock: {datos[2]} unid.).")

    def cargar_refaccion(self, refaccion) -> None:
        """Carga una refacción en el formulario y activa el modo edición."""
        self.refaccion_seleccionada = refaccion.refaccion_id
        self._asignar(self.entry_ref_nombre, refaccion.nombre)
        self._asignar(self.entry_ref_precio, str(refaccion.precio))
        self._asignar(self.entry_ref_stock, str(refaccion.stock))
        self.boton_ref_agregar.configure(state="disabled")
        self.boton_ref_guardar.configure(state="normal")
        self._mensaje(f"Editando refacción: {refaccion.nombre}")

    def limpiar_refaccion(self) -> None:
        """Deja el formulario de refacciones vacío y en modo alta."""
        self.refaccion_seleccionada = None
        self._asignar(self.entry_ref_nombre, "")
        self._asignar(self.entry_ref_precio, "")
        self._asignar(self.entry_ref_stock, "0")
        self.boton_ref_agregar.configure(state="normal")
        self.boton_ref_guardar.configure(state="disabled")

    def eliminar_refaccion(self, refaccion) -> None:
        """DELETE del catálogo tras confirmación (la historia no se rompe)."""
        respuesta = askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la refacción '{refaccion.nombre}'?\n\n"
            "Sale del catálogo y del inventario; las órdenes históricas "
            "conservan su precio y nombre grabados.",
        )
        if not respuesta:
            return
        try:
            refaccion_dao.eliminar(refaccion.refaccion_id)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.refrescar_refacciones()
        self._mensaje(f"Refacción '{refaccion.nombre}' eliminada del catálogo.")

    # ------------------------------------------------------------------ #
    # Ajuste rápido de inventario (± stock por fila)
    # ------------------------------------------------------------------ #
    def _dialogo_ajuste_stock(self, refaccion) -> None:
        """Mini-diálogo modal para entrada/salida de inventario de una refacción."""
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Ajuste de inventario")
        dialogo.geometry("380x270")
        dialogo.resizable(False, False)
        dialogo.transient(self)
        dialogo.grab_set()

        ctk.CTkLabel(
            dialogo, text=f"{refaccion.nombre} — stock actual: {refaccion.stock} unid.",
            font=tema.FUENTE_TEXTO,
        ).pack(pady=(15, 10))

        ctk.CTkLabel(dialogo, text="Cantidad *", font=tema.FUENTE_TEXTO).pack()
        entry_cantidad = ctk.CTkEntry(dialogo, width=120, font=tema.FUENTE_TEXTO, justify="center")
        entry_cantidad.pack(pady=(2, 10))

        seg_movimiento = ctk.CTkSegmentedButton(
            dialogo, values=["Entrada (+)", "Salida (−)"],
            font=tema.FUENTE_TEXTO,
        )
        seg_movimiento.set("Entrada (+)")
        seg_movimiento.pack(pady=(0, 15))

        frame_botones = ctk.CTkFrame(dialogo, fg_color="transparent")
        frame_botones.pack()

        def aceptar() -> None:
            """Aplica el movimiento de inventario (entrada o salida)."""
            try:
                cantidad = int(entry_cantidad.get().strip())
            except ValueError:
                showwarning("Cantidad inválida", "La cantidad debe ser un número entero.")
                return
            if cantidad <= 0:
                showwarning("Cantidad inválida", "La cantidad debe ser mayor a cero.")
                return
            es_entrada = seg_movimiento.get() == "Entrada (+)"
            nuevo_stock = refaccion.stock + cantidad if es_entrada else refaccion.stock - cantidad
            if nuevo_stock < 0:
                showwarning(
                    "Stock insuficiente",
                    f"No puedes dar salida de {cantidad} unid.: solo hay {refaccion.stock} en inventario.",
                )
                return
            try:
                # Se reenvían nombre y precio vigentes: solo cambia el stock
                refaccion_dao.actualizar(
                    refaccion.refaccion_id, refaccion.nombre, refaccion.precio, nuevo_stock,
                )
            except RuntimeError as error:
                self._mensaje(str(error), es_error=True)
                return
            dialogo.destroy()
            self.refrescar_refacciones()
            self._mensaje(
                f"{refaccion.nombre}: {'entrada' if es_entrada else 'salida'} de "
                f"{cantidad} unid. → stock {nuevo_stock}."
            )

        ctk.CTkButton(
            frame_botones, text="Aplicar", command=aceptar,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON, width=120,
        ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            frame_botones, text="Cancelar", command=dialogo.destroy,
            fg_color="#4b5563", font=tema.FUENTE_TEXTO, width=100,
        ).grid(row=0, column=1, padx=8)