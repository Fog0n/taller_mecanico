"""
Vista de cobros: registro de pagos por orden de trabajo.

Ventana de módulo (CTkToplevel) maestro-detalle: a la izquierda la lista
de órdenes con total/pagado/saldo; a la derecha el panel de la orden
seleccionada con sus pagos y el formulario para registrar uno nuevo.

Reglas de negocio:
- Se permiten pagos parciales (anticipos), nunca por más del saldo.
- Al cubrir el saldo con un pago, la orden pasa a 'pagada' automáticamente.
- Los pagos se pueden eliminar (corrección de errores) con confirmación;
  el estado 'pagada' NO se revierte automáticamente al borrar un pago.
"""

import tkinter.messagebox
from tkinter.messagebox import askyesno, showwarning

import customtkinter as ctk

from config import tema
from dao import cliente_dao
from dao import orden_dao
from dao import pago_dao
from vistas.ordenes import ETIQUETAS_ESTADO
from utils.recarga import vincular_recarga_foco

# Métodos de pago de la BD (ENUM)
METODOS_PAGO = ["Efectivo", "Tarjeta", "Transferencia"]
METODO_VALOR = {
    "Efectivo": "efectivo",
    "Tarjeta": "tarjeta",
    "Transferencia": "transferencia",
}


class CobrosVista(ctk.CTkToplevel):
    """Ventana de registro de pagos por orden de trabajo."""

    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario

        # Orden activa en el panel derecho (None = sin selección)
        self.orden_seleccionada = None

        # Configuración de la ventana
        self.title("Taller Mecánico - Cobros")
        self.geometry(tema.MODULO_SIZE)
        self.resizable(True, True)
        self.minsize(1000, 680)  # Nunca más pequeño: no se pierde información

        # Maestro-detalle: lista (izq) + panel de cobro (der)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._construir_lista()
        self._construir_panel()

        self.refrescar_lista()
        # Recarga datos al recuperar el foco: la lista y el panel pueden
        # haber cambiado si el usuario registró/editó órdenes en Órdenes
        vincular_recarga_foco(self, [self._recargar_cobros])

    def _recargar_cobros(self) -> None:
        """Recarga la lista y el panel de cobro al recuperar el foco."""
        self.refrescar_lista()
        if self.orden_seleccionada is None:
            return
        orden = self.orden_seleccionada
        try:
            total = orden_dao.calcular_total(orden.orden_id)
            saldo = round(total - pago_dao.total_pagado(orden.orden_id), 2)
        except RuntimeError:
            return  # Sin BD: el error se verá al recargar la lista
        self.refrescar_panel(total, saldo)

    # ------------------------------------------------------------------ #
    # Construcción de paneles
    # ------------------------------------------------------------------ #
    def _construir_lista(self) -> None:
        """Panel izquierdo: órdenes con su saldo pendiente."""
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Órdenes (clic en 'Cobrar')")
        self.frame_lista.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)

    def _construir_panel(self) -> None:
        """Panel derecho: resumen, pagos registrados y formulario de pago."""
        self.frame_panel = ctk.CTkFrame(self)
        self.frame_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)

        self.label_titulo = ctk.CTkLabel(
            self.frame_panel, text="Selecciona una orden",
            font=tema.FUENTE_TITULO, text_color=tema.COLOR_TEXTO,
        )
        self.label_titulo.pack(pady=(10, 15))

        # Resumen económico (Total / Pagado / Saldo)
        self.frame_resumen = ctk.CTkFrame(self.frame_panel, fg_color="transparent")
        self.frame_resumen.pack(fill="x", padx=15)
        for col in range(3):
            self.frame_resumen.grid_columnconfigure(col, weight=1)

        self.label_total = self._celda_resumen("TOTAL", tema.COLOR_TEXTO, 0)
        self.label_pagado = self._celda_resumen("PAGADO", "#10b981", 1)
        self.label_saldo = self._celda_resumen("SALDO", tema.COLOR_TEXTO, 2)

        # Pagos registrados de la orden seleccionada
        self.frame_pagos = ctk.CTkScrollableFrame(
            self.frame_panel, label_text="Pagos registrados", height=220,
        )
        self.frame_pagos.pack(fill="both", expand=True, padx=15, pady=(15, 10))

        # Formulario de pago nuevo
        frame_form = ctk.CTkFrame(self.frame_panel)
        frame_form.pack(fill="x", padx=15, pady=(5, 15))
        frame_form.grid_columnconfigure(0, weight=1)
        frame_form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_form, text="Monto ($) *", font=tema.FUENTE_TEXTO).grid(row=0, column=0, padx=10, sticky="w")
        self.entry_monto = ctk.CTkEntry(frame_form, width=140, font=tema.FUENTE_TEXTO, justify="center")
        self.entry_monto.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")

        ctk.CTkLabel(frame_form, text="Método *", font=tema.FUENTE_TEXTO).grid(row=0, column=1, padx=10, sticky="w")
        self.combo_metodo = ctk.CTkComboBox(
            frame_form, values=METODOS_PAGO, width=160, font=tema.FUENTE_TEXTO, state="readonly",
        )
        self.combo_metodo.set("Efectivo")
        self.combo_metodo.grid(row=1, column=1, padx=10, pady=(2, 10), sticky="ew")

        self.boton_registrar = ctk.CTkButton(
            frame_form, text="Registrar pago", command=self.registrar_pago,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON,
        )
        self.boton_registrar.grid(row=2, column=0, columnspan=2, pady=(0, 5))

    def _celda_resumen(self, titulo: str, color: str, columna: int) -> ctk.CTkLabel:
        """Crea una celda del resumen (etiqueta fija + valor) y devuelve el valor."""
        ctk.CTkLabel(
            self.frame_resumen, text=titulo, font=tema.FUENTE_TEXTO, text_color="#9ca3af",
        ).grid(row=0, column=columna)
        valor = ctk.CTkLabel(
            self.frame_resumen, text="$0.00", font=tema.FUENTE_BOTON, text_color=color,
        )
        valor.grid(row=1, column=columna, pady=(0, 5))
        return valor

    # ------------------------------------------------------------------ #
    # Utilidades
    # ------------------------------------------------------------------ #
    def _mensaje_panel(self, texto: str) -> None:
        """Muestra información sobre la orden activa (título del panel)."""
        self.label_titulo.configure(text=texto)

    def _monto_valido(self, texto: str, saldo: float) -> float | None:
        """Lee y valida el monto: número > 0 y no mayor al saldo pendiente."""
        try:
            monto = round(float(texto.strip()), 2)
        except ValueError:
            showwarning("Monto inválido", "El monto debe ser un número (ej. 250 o 250.50).")
            return None
        if monto <= 0:
            showwarning("Monto inválido", "El monto debe ser mayor a cero.")
            return None
        if round(saldo - monto, 2) < 0:
            showwarning(
                "Monto excedido",
                f"El monto no puede exceder el saldo pendiente: ${saldo:.2f}.",
            )
            return None
        return monto

    # ------------------------------------------------------------------ #
    # Lista de órdenes (maestro)
    # ------------------------------------------------------------------ #
    def refrescar_lista(self) -> None:
        """Pinta la lista de órdenes con total, pagado y saldo desde la BD."""
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        # Cabecera
        anchos = [6, 14, 22, 12, 12, 12, 12]
        textos = ["#", "Matrícula", "Cliente", "Estado", "Total", "Pagado", "Saldo"]
        for col, (texto, peso) in enumerate(zip(textos, anchos)):
            ctk.CTkLabel(
                self.frame_lista, text=texto.ljust(peso),
                font=tema.FUENTE_BOTON, text_color="#9ca3af", anchor="w",
            ).grid(row=0, column=col, padx=5, sticky="w")
        for col, peso in enumerate([0, 1, 2, 0, 1, 1, 1, 0]):
            self.frame_lista.grid_columnconfigure(col, weight=peso)

        try:
            ordenes = orden_dao.obtener_todas()
            clientes = {c.cliente_id: c.nombre for c in cliente_dao.obtener_todos()}
        except RuntimeError as error:
            self._mensaje_panel(f"Error: {error}")
            return

        for i, orden in enumerate(ordenes):
            fila = i + 1
            color = "#252525" if i % 2 == 1 else "transparent"

            total = orden_dao.calcular_total(orden.orden_id)
            pagado = pago_dao.total_pagado(orden.orden_id)
            saldo = round(total - pagado, 2)

            datos = [
                f"#{i + 1}",
                orden.matricula,
                clientes.get(orden.cliente_id, "—"),
                ETIQUETAS_ESTADO.get(orden.estado, orden.estado),
                f"${total:.2f}",
                f"${pagado:.2f}",
                f"${saldo:.2f}",
            ]
            for col, texto in enumerate(datos):
                ctk.CTkLabel(
                    self.frame_lista, text=texto, font=tema.FUENTE_TEXTO,
                    text_color=(
                        "#10b981" if (col == 6 and saldo == 0) else
                        tema.COLOR_ERROR if (col == 6 and saldo > 0) else tema.COLOR_TEXTO
                    ),
                    anchor="w", fg_color=color,
                ).grid(row=fila, column=col, padx=5, sticky="w")

            ctk.CTkButton(
                self.frame_lista, text="Cobrar", width=70, height=24,
                fg_color=tema.COLOR_BOTON, font=("Arial", 11),
                command=lambda o=orden, t=total, s=saldo: self.seleccionar_orden(o, t, s),
            ).grid(row=fila, column=7, padx=5, pady=3)

    # ------------------------------------------------------------------ #
    # Panel de cobro (detalle)
    # ------------------------------------------------------------------ #
    def seleccionar_orden(self, orden, total: float, saldo: float) -> None:
        """Activa una orden en el panel derecho y muestra sus pagos."""
        self.orden_seleccionada = orden
        self.refrescar_panel(total, saldo)

    def refrescar_panel(self, total: float, saldo: float) -> None:
        """Actualiza título, resumen, lista de pagos y formulario del panel."""
        orden = self.orden_seleccionada
        if orden is None:
            self._mensaje_panel("Selecciona una orden")
            return

        estado_etiqueta = ETIQUETAS_ESTADO.get(orden.estado, orden.estado)
        self._mensaje_panel(
            f"Orden #{orden.orden_id} — {orden.matricula} ({estado_etiqueta})"
        )

        pagado = round(total - saldo, 2)
        self.label_total.configure(text=f"${total:.2f}")
        self.label_pagado.configure(text=f"${pagado:.2f}")
        self.label_saldo.configure(
            text=f"${saldo:.2f}",
            text_color="#10b981" if saldo == 0 else tema.COLOR_ERROR,
        )

        # Monto pre-llenado con el saldo pendiente (comodidad de captura)
        self.entry_monto.delete(0, "end")
        if saldo > 0:
            self.entry_monto.insert(0, f"{saldo:.2f}")

        self._refrescar_pagos()

    def _refrescar_pagos(self) -> None:
        """Pinta la tabla de pagos de la orden activa."""
        for widget in self.frame_pagos.winfo_children():
            widget.destroy()

        if self.orden_seleccionada is None:
            return
        orden = self.orden_seleccionada

        try:
            pagos = pago_dao.obtener_por_orden(orden.orden_id)
        except RuntimeError as error:
            self._mensaje_panel(f"Error: {error}")
            return

        # Cabecera
        for col, texto in enumerate(["Fecha", "Método", "Monto", ""]):
            ctk.CTkLabel(
                self.frame_pagos, text=texto, font=tema.FUENTE_BOTON, text_color="#9ca3af",
                anchor="w",
            ).grid(row=0, column=col, padx=6, sticky="w")
        for col, peso in enumerate([1, 2, 1, 0]):
            self.frame_pagos.grid_columnconfigure(col, weight=peso)

        if not pagos:
            ctk.CTkLabel(
                self.frame_pagos, text="(sin pagos registrados)",
                font=tema.FUENTE_TEXTO, text_color="#9ca3af",
            ).grid(row=1, column=0, columnspan=3, padx=6, pady=8, sticky="w")
            return

        for i, pago in enumerate(pagos):
            fila = i + 1
            datos = [str(pago.fecha_pago), pago.metodo_pago, f"${pago.monto:.2f}"]
            for col, texto in enumerate(datos):
                ctk.CTkLabel(
                    self.frame_pagos, text=texto, font=tema.FUENTE_TEXTO,
                    text_color=tema.COLOR_TEXTO, anchor="w",
                ).grid(row=fila, column=col, padx=6, sticky="w")

            ctk.CTkButton(
                self.frame_pagos, text="Eliminar", width=70, height=22,
                fg_color=tema.COLOR_ERROR, font=("Arial", 11),
                command=lambda p=pago: self.eliminar_pago(p),
            ).grid(row=fila, column=3, padx=6, pady=2)

    # ------------------------------------------------------------------ #
    # Acciones
    # ------------------------------------------------------------------ #
    def registrar_pago(self) -> None:
        """INSERT del pago; si cubre el saldo, marca la orden como pagada."""
        orden = self.orden_seleccionada
        if orden is None:
            return

        try:
            total = orden_dao.calcular_total(orden.orden_id)
            pagado = pago_dao.total_pagado(orden.orden_id)
        except RuntimeError as error:
            self._mensaje_panel(f"Error: {error}")
            return
        saldo = round(total - pagado, 2)

        monto = self._monto_valido(self.entry_monto.get(), saldo)
        if monto is None:
            return
        metodo = METODO_VALOR[self.combo_metodo.get()]

        try:
            pago_dao.registrar(orden.orden_id, monto, metodo,
                               self.usuario.usuario_id if self.usuario else 0)
        except RuntimeError as error:
            self._mensaje_panel(f"Error: {error}")
            return

        nuevo_saldo = round(saldo - monto, 2)
        # Regla de negocio: al cubrir el saldo, la orden queda 'pagada'
        aviso_estado = ""
        if nuevo_saldo <= 0 and orden.estado != "pagada":
            try:
                orden_dao.cambiar_estado(orden.orden_id, "pagada")
                aviso_estado = " Orden marcada como PAGADA."
            except RuntimeError as error:
                aviso_estado = f" (Aviso: no se pudo marcar pagada: {error})"

        self.refrescar_lista()
        orden_actualizada = [o for o in orden_dao.obtener_todas() if o.orden_id == orden.orden_id]
        if orden_actualizada:
            self.orden_seleccionada = orden_actualizada[0]
        total_nuevo = orden_dao.calcular_total(orden.orden_id)
        saldo_nuevo = round(total_nuevo - pago_dao.total_pagado(orden.orden_id), 2)
        self.refrescar_panel(total_nuevo, saldo_nuevo)
        self._mensaje_panel(
            f"Orden #{orden.orden_id} — pago de ${monto:.2f} registrado.{aviso_estado}"
        )

    def eliminar_pago(self, pago) -> None:
        """DELETE del pago tras confirmación (corrección de captura)."""
        respuesta = self._confirmar_eliminacion(pago)
        if not respuesta:
            return
        try:
            pago_dao.eliminar(pago.pago_id)
        except RuntimeError as error:
            self._mensaje_panel(f"Error: {error}")
            return

        self.refrescar_lista()
        if self.orden_seleccionada is not None:
            orden = self.orden_seleccionada
            total = orden_dao.calcular_total(orden.orden_id)
            saldo = round(total - pago_dao.total_pagado(orden.orden_id), 2)
            self.refrescar_panel(total, saldo)
        self._mensaje_panel(
            f"Orden #{pago.orden_id} — pago de ${pago.monto:.2f} eliminado."
            " El estado 'pagada' no se revierte automáticamente."
        )

    def _confirmar_eliminacion(self, pago) -> bool:
        """Aviso de eliminación con la advertencia de estado."""
        return askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el pago de ${pago.monto:.2f} ({pago.metodo_pago})?\n\n"
            "Si la orden estaba cubierta, el estado 'pagada' NO se revierte "
            "automáticamente; ajústalo desde el módulo Órdenes si es necesario.",
        )