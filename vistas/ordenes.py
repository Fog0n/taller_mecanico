"""
Vista de gestión de órdenes de trabajo.

Abierta desde el menú principal. Permite armar el ticket de una orden
(líneas de servicios y refacciones con subtotal) y administrar órdenes
existentes: cambiar estado, ver detalle y eliminar.
"""

import tkinter.messagebox
from tkinter.messagebox import askyesno, showwarning

import customtkinter as ctk

from config import tema
from dao import cliente_dao
from dao import orden_dao
from dao import refaccion_dao
from dao import servicio_dao
from dao import vehiculo_dao
from dao.orden_dao import EstadoValido
from utils.recarga import vincular_recarga_foco

# Estado -> color del chip (semáforo de avance de trabajo)
COLORES_ESTADO = {
    "abierta": "#9ca3af",
    "en_proceso": tema.COLOR_BOTON,
    "terminada": "#f59e0b",
    "entregada": "#10b981",
    "pagada": "#8b5cf6",
}
ETIQUETAS_ESTADO = {
    "abierta": "Abierta",
    "en_proceso": "En proceso",
    "terminada": "Terminada",
    "entregada": "Entregada",
    "pagada": "Pagada",
}


class OrdenesVista(ctk.CTkToplevel):
    """Ventana de administración de órdenes de trabajo."""

    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario

        # Datos vigentes de los catálogos (ids de servicios/refacciones/vehiculos)
        self.cat_servicios: dict[str, int] = {}      # nombre -> servicio_id
        self.cat_refacciones: dict[str, int] = {}    # nombre -> refaccion_id
        self.vehiculos_disponibles: dict[str, str] = {}  # "matricula (dueño)" -> matricula
        self.lineas = []  # Tentativemente: (tipo, item_id, cantidad, precio, subtotal, nombre)

        # Configuración de la ventana
        self.title("Taller Mecánico - Órdenes")
        self.geometry(tema.MODULO_SIZE)
        self.resizable(True, True)
        self.minsize(960, 680)  # Nunca más pequeño: no se pierde información

        self._cargar_catalogos()

        # ---------------------------------------------------------------- #
        # Formulario superior: cabecera + armado del ticket
        # ---------------------------------------------------------------- #
        self.frame_formulario = ctk.CTkFrame(self)
        self.frame_formulario.pack(fill="x", padx=15, pady=(15, 8))

        # Columnas elásticas: vehículo y artículo se estiran al redimensionar
        for col, peso in enumerate([1, 0, 2, 0, 0, 0]):
            self.frame_formulario.grid_columnconfigure(col, weight=peso)

        ctk.CTkLabel(self.frame_formulario, text="Vehículo *", font=tema.FUENTE_TEXTO).grid(row=0, column=0, padx=10, sticky="w")
        self.combo_vid14 = ctk.CTkComboBox(self.frame_formulario, width=260, font=tema.FUENTE_TEXTO, state="readonly")
        self.combo_vid14.configure(
            values=list(self.vehiculos_disponibles.keys()) or ["(sin vehículos)"]
        )
        self.combo_vid14.set(list(self.vehiculos_disponibles.keys())[0] if self.vehiculos_disponibles else "(sin vehículos)")
        self.combo_vid14.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")

        # Tipo de línea
        ctk.CTkLabel(self.frame_formulario, text="Línea de", font=tema.FUENTE_TEXTO).grid(row=0, column=1, padx=10, sticky="w")
        self.seg_tipo = ctk.CTkSegmentedButton(
            self.frame_formulario, values=["servicio", "refaccion"],
            command=self._cambiar_tipo, font=tema.FUENTE_TEXTO,
        )
        self.seg_tipo.set("servicio")
        self.seg_tipo.grid(row=1, column=1, padx=10, pady=(2, 10))

        # Artículo (combo cambia según el tipo)
        ctk.CTkLabel(self.frame_formulario, text="Artículo *", font=tema.FUENTE_TEXTO).grid(row=0, column=2, padx=10, sticky="w")
        self.combo_item = ctk.CTkComboBox(
            self.frame_formulario, width=200, font=tema.FUENTE_TEXTO, state="readonly",
            command=lambda _valor: self._actualizar_stock(),  # Stock al elegir artículo
        )
        self.label_stock = ctk.CTkLabel(
            self.frame_formulario, text="", font=("Arial", 11), text_color="#9ca3af",
        )
        self._llenar_combo_items()
        self.combo_item.grid(row=1, column=2, padx=10, pady=(2, 10), sticky="ew")
        self.label_stock.grid(row=2, column=2, padx=10, sticky="w")

        # Cantidad
        ctk.CTkLabel(self.frame_formulario, text="Cant. *", font=tema.FUENTE_TEXTO).grid(row=0, column=3, padx=10, sticky="w")
        self.entry_cantidad = ctk.CTkEntry(self.frame_formulario, width=60, font=tema.FUENTE_TEXTO)
        self.entry_cantidad.insert(0, "1")
        self.entry_cantidad.grid(row=1, column=3, padx=10, pady=(2, 10))

        # Botones de acción
        ctk.CTkButton(
            self.frame_formulario, text="+ Agregar línea", command=self.agregar_linea,
            fg_color="#4b5563", font=tema.FUENTE_TEXTO,
        ).grid(row=1, column=4, padx=10, pady=(2, 10))

        self.boton_registrar = ctk.CTkButton(
            self.frame_formulario, text="Registrar orden", command=self.registrar_orden,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON,
        )
        self.boton_registrar.grid(row=1, column=5, padx=10, pady=(2, 10))

        # Ticket en construcción (líneas temporales)
        self.frame_ticket = ctk.CTkScrollableFrame(self, height=140, label_text="Ticket en construcción")
        self.frame_ticket.pack(fill="x", padx=15, pady=8)

        # Total al pie del ticket
        self.label_total = ctk.CTkLabel(
            self, text="Total de la nueva orden: $0.00",
            font=tema.FUENTE_BOTON, text_color=tema.COLOR_BOTON,
        )
        self.label_total.pack(pady=(0, 8))

        # ---------------------------------------------------------------- #
        # Lista de órdenes existentes
        # ---------------------------------------------------------------- #
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Órdenes registradas")
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.label_estado = ctk.CTkLabel(self, text="", text_color=tema.COLOR_TEXTO)
        self.label_estado.pack(pady=(0, 5))

        self.refrescar_lista()
        # Recarga datos al recuperar el foco: otros módulos (p. ej. Cobros
        # marcando una orden 'pagada') pueden cambiar la BD entre tanto
        vincular_recarga_foco(self, [self.refrescar_lista])

    # ------------------------------------------------------------------ #
    # Catálogos
    # ------------------------------------------------------------------ #
    def _cargar_catalogos(self) -> None:
        """Carga ids de catálogos y vehículos para los combos."""
        try:
            servicios = servicio_dao.obtener_todos()
            refacciones = refaccion_dao.obtener_todos()
            vehiculos = vehiculo_dao.obtener_todos()
            clientes = {c.cliente_id: c.nombre for c in cliente_dao.obtener_todos()}
        except RuntimeError as error:
            showwarning("Sin conexión", f"{error}\nVerifica MySQL en el Panel de Control de XAMPP.")
            return

        self.cat_servicios = {s.nombre: s.servicio_id for s in servicios}
        self.cat_refacciones = {r.nombre: r.refaccion_id for r in refacciones}
        self.vehiculos_disponibles = {
            f"{v.matricula} — {v.modelo} ({clientes.get(v.cliente_id, '—')})": v.matricula
            for v in vehiculos
        }

    def _llenar_combo_items(self) -> None:
        """Rellena el combo de artículos según la línea elegida (tipo).
        Solo actualiza los nombres disponibles; no cambia la selección actual
        para no alterar el stock mostrado tras registrar una orden."""
        catalogo = self.cat_servicios if self.seg_tipo.get() == "servicio" else self.cat_refacciones
        self.combo_item.configure(values=list(catalogo.keys()) or ["(sin artículos)"])
        # NO hago self.combo_item.set(...) aquí para no alterar la selección
        # y mantener el stock mostrado consistente con la elección del usuario.

    def _actualizar_stock(self) -> None:
        """Muestra el stock vigente de la refacción seleccionada (vacío en servicios)."""
        if self.seg_tipo.get() != "refaccion":
            self.label_stock.configure(text="")
            return
        nombre = self.combo_item.get()
        try:
            coincidencias = [r for r in refaccion_dao.obtener_todos() if r.nombre == nombre]
        except RuntimeError:
            self.label_stock.configure(text="")  # Sin BD: el error se muestra al registrar
            return
        if coincidencias:
            refaccion = coincidencias[0]
            self.label_stock.configure(
                text=f"Stock disponible: {refaccion.stock} unid.",
                text_color=tema.COLOR_ERROR if refaccion.stock == 0 else "#9ca3af",
            )
        else:
            self.label_stock.configure(text="")

    def _cambiar_tipo(self, _valor=None) -> None:
        """Al alternar servicio/refacción recarga el combo y el stock."""
        self._llenar_combo_items()
        self._actualizar_stock()

    # ------------------------------------------------------------------ #
    # Armado del ticket (líneas temporales)
    # ------------------------------------------------------------------ #
    def _mensaje(self, texto: str, es_error: bool = False) -> None:
        """Muestra el resultado de la última operación."""
        self.label_estado.configure(
            text=texto, text_color=tema.COLOR_ERROR if es_error else tema.COLOR_TEXTO,
        )

    def _cantidad_valida(self) -> int | None:
        """Lee y valida la cantidad del campo."""
        texto = self.entry_cantidad.get().strip()
        try:
            cantidad = int(texto)
        except ValueError:
            showwarning("Cantidad inválida", "La cantidad debe ser un número entero.")
            return None
        if cantidad <= 0:
            showwarning("Cantidad inválida", "La cantidad debe ser mayor a cero.")
            return None
        return cantidad

    def _refrescar_ticket(self) -> None:
        """Vuelve a pintar las líneas temporales y el total."""
        for widget in self.frame_ticket.winfo_children():
            widget.destroy()

        # Cabecera
        ctk.CTkLabel(
            self.frame_ticket, text="#", font=tema.FUENTE_BOTON, text_color="#9ca3af",
        ).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkLabel(
            self.frame_ticket, text="Tipo".ljust(12), font=tema.FUENTE_BOTON, text_color="#9ca3af",
        ).grid(row=0, column=1, padx=5, sticky="w")
        ctk.CTkLabel(
            self.frame_ticket, text="Artículo".ljust(24), font=tema.FUENTE_BOTON, text_color="#9ca3af",
        ).grid(row=0, column=2, padx=5, sticky="w")
        ctk.CTkLabel(
            self.frame_ticket, text="Cant.".ljust(8), font=tema.FUENTE_BOTON, text_color="#9ca3af",
        ).grid(row=0, column=3, padx=5, sticky="w")
        ctk.CTkLabel(
            self.frame_ticket, text="Subtotal", font=tema.FUENTE_BOTON, text_color="#9ca3af",
        ).grid(row=0, column=4, padx=5, sticky="w")

        total = 0.0
        for i, linea in enumerate(self.lineas):
            tipo, _item_id, cantidad, precio, subtotal, nombre = linea
            total += subtotal
            fila = i + 1
            ctk.CTkLabel(self.frame_ticket, text=f"#{i + 1}", font=tema.FUENTE_TEXTO).grid(row=fila, column=0, padx=5, sticky="w")
            ctk.CTkLabel(self.frame_ticket, text=tipo.ljust(12), font=tema.FUENTE_TEXTO).grid(row=fila, column=1, padx=5, sticky="w")
            ctk.CTkLabel(self.frame_ticket, text=nombre, font=tema.FUENTE_TEXTO, width=240, anchor="w").grid(row=fila, column=2, padx=5, sticky="w")
            ctk.CTkLabel(self.frame_ticket, text=str(cantidad), font=tema.FUENTE_TEXTO).grid(row=fila, column=3, padx=5, sticky="w")
            ctk.CTkLabel(self.frame_ticket, text=f"${subtotal:.2f}", font=tema.FUENTE_TEXTO).grid(row=fila, column=4, padx=5, sticky="w")
            ctk.CTkButton(
                self.frame_ticket, text="×", width=28, height=22,
                fg_color=tema.COLOR_ERROR, font=("Arial", 11, "bold"),
                command=lambda idx=i: self.quitar_linea(idx),
            ).grid(row=fila, column=5, padx=5)

        if self.label_total is not None:
            self.label_total.configure(text=f"Total de la nueva orden: ${total:.2f}")

    def agregar_linea(self) -> None:
        """Añade una línea temporal al ticket (con precio vigente)."""
        etiqueta_item = self.combo_item.get()
        tipo = self.seg_tipo.get()
        catalogo = self.cat_servicios if tipo == "servicio" else self.cat_refacciones
        if etiqueta_item not in catalogo:
            showwarning("Sin artículo", "Selecciona un artículo del catálogo (o cárgalo en etapas previas).")
            return
        cantidad = self._cantidad_valida()
        if cantidad is None:
            return

        item_id = catalogo[etiqueta_item]
        # Precio vigente desde el DAO de catálogos
        try:
            if tipo == "servicio":
                precio = float([s.precio for s in servicio_dao.obtener_todos() if s.servicio_id == item_id][0])
            else:
                precio = float([r.precio for r in refaccion_dao.obtener_todos() if r.refaccion_id == item_id][0])
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return

        subtotal = precio * cantidad
        self.lineas.append((tipo, item_id, cantidad, precio, subtotal, etiqueta_item))
        self._refrescar_ticket()

    def quitar_linea(self, indice: int) -> None:
        """Retira una línea temporal del ticket."""
        if 0 <= indice < len(self.lineas):
            self.lineas.pop(indice)
            self._refrescar_ticket()

    def limpiar_ticket(self) -> None:
        """Deja el ticket vacío para una orden nueva."""
        self.lineas = []
        self._refrescar_ticket()

    # ------------------------------------------------------------------ #
    # Órdenes en la base de datos
    # ------------------------------------------------------------------ #
    def registrar_orden(self) -> None:
        """Manda la transacción de creación completa con las líneas del ticket."""
        matricula = self.vehiculos_disponibles.get(self.combo_vid14.get())
        if matricula is None:
            showwarning("Sin vehículo", "Registra primero un vehículo en el módulo Vehículos.")
            return
        if not self.lineas:
            showwarning("Ticket vacío", "Agrega al menos una línea de servicio o refacción.")
            return

        detalles = [(tipo, item_id, cantidad) for (tipo, item_id, cantidad, _p, _s, _n) in self.lineas]
        try:
            orden_id = orden_dao.crear_orden(matricula, self._cliente_id_de_vehiculo(matricula),
                                             self.usuario.usuario_id if self.usuario else 0, detalles)
        except RuntimeError as error:
            self._mensaje(f"Orden NO registrada: {error}", es_error=True)
            return
        self.limpiar_ticket()
        self.refrescar_lista()
        self._llenar_combo_items()  # recarga nombres, mantiene selección
        self._actualizar_stock()  # actualiza el stock descontado tras registrar
        self._mensaje(f"Orden #{orden_id} registrada correctamente.")

    def _cliente_id_de_vehiculo(self, matricula: str) -> int:
        """Devuelve el cliente_id actual de un vehículo (por DAO)."""
        for v in vehiculo_dao.obtener_todos():
            if v.matricula == matricula:
                return v.cliente_id
        raise RuntimeError("El vehículo seleccionado no existe (fue eliminado en otra ventana).")

    def refrescar_lista(self) -> None:
        """Vuelve a pintar la lista de órdenes desde la base de datos."""
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        self._fila_encabezado()

        try:
            ordenes = orden_dao.obtener_todas()
            clientes = {c.cliente_id: c.nombre for c in cliente_dao.obtener_todos()}
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return

        for i, orden in enumerate(ordenes):
            self._fila_orden(i, orden, clientes.get(orden.cliente_id, "—"), fondo=i % 2 == 1)

        self._mensaje(f"{len(ordenes)} orden(s) registradas.")

    def _fila_encabezado(self) -> None:
        """Pinta la cabecera de la tabla de órdenes."""
        anchos = [6, 10, 12, 20, 10]
        textos = ["#", "Entrada", "Matrícula", "Cliente", "Estado"]
        for col, (texto, peso) in enumerate(zip(textos, anchos)):
            ctk.CTkLabel(
                self.frame_lista, text=texto.ljust(peso),
                font=tema.FUENTE_BOTON, text_color="#9ca3af", anchor="w",
            ).grid(row=0, column=col, padx=5, sticky="w")
        ctk.CTkLabel(
            self.frame_lista, text="", font=tema.FUENTE_BOTON,
        ).grid(row=0, column=5, padx=5)  # columna de acciones (sin texto)
        # Ancho extra distribuido entre columnas de datos (0 = fija)
        for col, peso in enumerate([0, 1, 2, 3, 0, 0, 0, 0]):
            self.frame_lista.grid_columnconfigure(col, weight=peso)

    def _fila_orden(self, indice: int, orden, dueno: str, fondo: bool) -> None:
        """Pinta una fila de orden con sus acciones."""
        fila = indice + 1
        color = "#252525" if fondo else "transparent"
        entradas = str(orden.fecha_entrada)

        datos = [f"#{indice + 1}", entradas[5:], orden.matricula, dueno]
        for col, texto in enumerate(datos):
            ctk.CTkLabel(
                self.frame_lista, text=texto, font=tema.FUENTE_TEXTO,
                text_color=tema.COLOR_TEXTO, anchor="w", fg_color=color,
            ).grid(row=fila, column=col, padx=5, sticky="w")

        # Chip de estado (color semáforo)
        ctk.CTkLabel(
            self.frame_lista, text=ETIQUETAS_ESTADO.get(orden.estado, orden.estado),
            font=("Arial", 11, "bold"), text_color="#ffffff",
            fg_color=COLORES_ESTADO.get(orden.estado, tema.COLOR_FONDO),
            corner_radius=8, width=100, height=22,
        ).grid(row=fila, column=4, padx=5, pady=3)

        # Acciones: avanzar estado, ver detalle, eliminar
        ctk.CTkButton(
            self.frame_lista, text="Avanzar →", width=80, height=24,
            fg_color=tema.COLOR_BOTON, font=("Arial", 11),
            command=lambda o=orden: self.avanzar_estado(o),
        ).grid(row=fila, column=5, padx=4, pady=3)

        ctk.CTkButton(
            self.frame_lista, text="Detalle", width=60, height=24,
            fg_color="#4b5563", font=("Arial", 11),
            command=lambda o=orden: self.ver_detalle(o),
        ).grid(row=fila, column=6, padx=4, pady=3)

        ctk.CTkButton(
            self.frame_lista, text="Eliminar", width=70, height=24,
            fg_color=tema.COLOR_ERROR, font=("Arial", 11),
            command=lambda o=orden: self.eliminar_orden(o),
        ).grid(row=fila, column=7, padx=4, pady=3)

    def avanzar_estado(self, orden) -> None:
        """Pasa la orden al siguiente estado válido del flujo."""
        flujo = list(EstadoValido)  # abierta → en_proceso → terminada → entregada → pagada
        if orden.estado not in flujo:
            self._mensaje(f"Estado desconocido en la orden #{orden.orden_id}: {orden.estado}", es_error=True)
            return
        indice_actual = flujo.index(orden.estado)
        if indice_actual + 1 >= len(flujo):
            self._mensaje(f"La orden #{orden.orden_id} ya está en el último estado "
                          f"({ETIQUETAS_ESTADO[orden.estado]}).")
            return
        siguiente = flujo[indice_actual + 1]
        try:
            orden_dao.cambiar_estado(orden.orden_id, siguiente)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.refrescar_lista()

    def ver_detalle(self, orden) -> None:
        """Muestra las líneas, subtotales y total de una orden."""
        try:
            detalles = orden_dao.obtener_detalles(orden.orden_id)
            total = orden_dao.calcular_total(orden.orden_id)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return

        lineas_texto = [
            f"  #{i + 1} [{d.tipo}] {d.nombre_item or 'artículo eliminado'} "
            f"× {d.cantidad} = ${d.subtotal:.2f} (unit. ${d.precio_unitario:.2f})"
            for i, d in enumerate(detalles)
        ]
        mensaje = (
            f"Orden #{orden.orden_id} — {orden.matricula}\n"
            f"Entrada: {orden.fecha_entrada} {orden.hora_entrada}\n"
            + (f"Salida: {orden.fecha_salida} {orden.hora_salida}\n" if orden.fecha_salida else "Sin salida\n")
            + f"Estado: {ETIQUETAS_ESTADO[orden.estado]}\n\n"
            + "\n".join(lineas_texto or ["  (sin líneas)"])
            + f"\n\nTOTAL: ${total:.2f}"
        )
        tkinter.messagebox.showinfo(f"Detalle de la orden #{orden.orden_id}", mensaje)

    def eliminar_orden(self, orden) -> None:
        """DELETE tras confirmación; avisa del borrado en cascada."""
        respuesta = askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la orden #{orden.orden_id} de {orden.matricula}?\n\n"
            "También se borrarán sus líneas de detalle y pagos asociados.",
        )
        if not respuesta:
            return
        try:
            orden_dao.eliminar(orden.orden_id)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.refrescar_lista()
