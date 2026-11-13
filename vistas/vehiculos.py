"""
Vista de gestión de vehículos (módulo completo: registro, edición y baja).

Ventana de módulo (CTkToplevel) abierta desde el menú principal.
El cliente dueño se selecciona en un combo; la matricula no se edita
después de registrar el vehículo.
"""

import tkinter.messagebox
from tkinter.messagebox import askyesno, showwarning

import customtkinter as ctk

from config import tema
from dao import cliente_dao
from dao import vehiculo_dao
from modelos.vehiculo import Vehiculo
from utils.recarga import vincular_recarga_foco


class VehiculosVista(ctk.CTkToplevel):
    """Ventana de administración de vehículos."""

    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario

        # Configuración de la ventana
        self.title("Taller Mecánico - Vehículos")
        self.geometry(tema.MODULO_SIZE)
        self.resizable(True, True)
        self.minsize(860, 620)  # Nunca más pequeño: no se pierde información

        # Matricula del vehículo en edición (None = formulario en modo alta)
        self.matricula_seleccionada: str | None = None
        # Catálogo de clientes para el combo (se recarga al abrir la ventana)
        self.clientes_disponibles: dict[str, int] = {}  # "id. nombre" -> cliente_id

        # Formulario (zona superior)
        self.frame_formulario = ctk.CTkFrame(self)
        self.frame_formulario.pack(fill="x", padx=15, pady=15)

        # Columnas elásticas del formulario (aprovechan el ancho extra)
        for col in range(4):
            self.frame_formulario.grid_columnconfigure(col, weight=1)

        self.entry_matricula = self._campo(self.frame_formulario, "Matrícula *", 0, 0)
        self.entry_modelo = self._campo(self.frame_formulario, "Modelo *", 0, 1)
        self.entry_marca = self._campo(self.frame_formulario, "Marca *", 0, 2)
        self.entry_color = self._campo(self.frame_formulario, "Color", 0, 3)
        self.combo_cliente = self._combo_cliente(self.frame_formulario, 1, 0)

        # Botones de acción del formulario (misma línea que el combo)
        self.boton_agregar = ctk.CTkButton(
            self.frame_formulario, text="Registrar vehículo", command=self.registrar_vehiculo,
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

        # Lista de vehículos (zona inferior, desplazable)
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Vehículos registrados")
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Mensaje de estado de la operación en BD
        self.label_estado = ctk.CTkLabel(self, text="", text_color=tema.COLOR_TEXTO)
        self.label_estado.pack(pady=(0, 5))

        self.refrescar_lista()
        # Recarga datos al recuperar el foco: otros módulos pueden haber
        # cambiado la BD mientras esta ventana seguía abierta
        vincular_recarga_foco(self, [self.refrescar_lista])

    # ------------------------------------------------------------------ #
    # Construcción de campos reutilizables
    # ------------------------------------------------------------------ #
    def _campo(self, padre, etiqueta, fila, columna) -> ctk.CTkEntry:
        """Crea un campo del formulario con su etiqueta y lo devuelve."""
        ctk.CTkLabel(padre, text=etiqueta, font=tema.FUENTE_TEXTO).grid(row=fila * 2, column=columna, padx=10, sticky="w")
        entrada = ctk.CTkEntry(padre, width=180, font=tema.FUENTE_TEXTO)
        entrada.grid(row=fila * 2 + 1, column=columna, padx=10, pady=(2, 10), sticky="ew")
        return entrada

    def _combo_cliente(self, padre, fila, columna) -> ctk.CTkComboBox:
        """Crea el selector del cliente dueño (catálogo de clientes)."""
        del fila, columna  # Posición fija: renglones 2/3, columna 0
        ctk.CTkLabel(padre, text="Cliente dueño *", font=tema.FUENTE_TEXTO).grid(row=2, column=0, padx=10, sticky="w")
        # Carga el catálogo actual (de forma tolerante si MySQL está apagado)
        try:
            clientes = cliente_dao.obtener_todos()
        except RuntimeError:
            clientes = []
            showwarning(
                "Sin conexión",
                "No hay conexión a MySQL: no se pudo cargar la lista de clientes.\n"
                "Verifica el Panel de Control de XAMPP.",
            )
        self.clientes_disponibles = {}  # Nombre (o nombre desambiguado) -> cliente_id
        for c in clientes:
            etiqueta = c.nombre
            if etiqueta in self.clientes_disponibles:
                # Dos clientes con el mismo nombre: se desambigua con el id
                etiqueta = f"{c.nombre} (id {c.cliente_id})"
            self.clientes_disponibles[etiqueta] = c.cliente_id

        combo = ctk.CTkComboBox(
            padre,
            values=list(self.clientes_disponibles.keys()) or ["(sin clientes)"],
            width=180,
            font=tema.FUENTE_TEXTO,
            state="readonly",
        )
        combo.set(list(self.clientes_disponibles.keys())[0] if self.clientes_disponibles else "(sin clientes)")
        combo.grid(row=3, column=0, padx=10, pady=(2, 10))
        return combo

    # ------------------------------------------------------------------ #
    # Utilidades del formulario y de la lista
    # ------------------------------------------------------------------ #
    def _cliente_id_seleccionado(self) -> int | None:
        """Devuelve el cliente_id del combo, o None si no hay clientes."""
        etiqueta = self.combo_cliente.get()
        return self.clientes_disponibles.get(etiqueta)

    def _valores_formulario(self):
        """Lee el formulario; devuelve tupla o None si falta un campo obligatorio."""
        matricula = self.entry_matricula.get().strip().upper()
        modelo = self.entry_modelo.get().strip()
        marca = self.entry_marca.get().strip()
        color = self.entry_color.get().strip() or None
        cliente_id = self._cliente_id_seleccionado()

        if not matricula or not modelo or not marca or cliente_id is None:
            showwarning("Datos incompletos", "Matrícula, modelo, marca y cliente son obligatorios.")
            return None
        return matricula, modelo, marca, color, cliente_id

    def _mensaje(self, texto: str, es_error: bool = False) -> None:
        """Muestra el resultado de la última operación."""
        self.label_estado.configure(
            text=texto, text_color=tema.COLOR_ERROR if es_error else tema.COLOR_TEXTO,
        )

    def refrescar_lista(self) -> None:
        """Vuelve a pintar la lista desde la base de datos."""
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        # Encabezado
        self._fila_encabezado()

        try:
            vehiculos = vehiculo_dao.obtener_todos()
            clientes = {c.cliente_id: c.nombre for c in cliente_dao.obtener_todos()}
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return

        for i, vehiculo in enumerate(vehiculos):
            self._fila_vehiculo(i, vehiculo, clientes.get(vehiculo.cliente_id, "—"), fondo=i % 2 == 1)

        self._mensaje(f"{len(vehiculos)} vehículo(s) registrados.")

    def _fila_encabezado(self) -> None:
        """Pinta la cabecera de la tabla."""
        anchos = [7, 14, 18, 14, 12, 24]
        textos = ["#", "Matrícula", "Modelo", "Marca", "Color", "Cliente dueño"]
        for col, (texto, peso) in enumerate(zip(textos, anchos)):
            ctk.CTkLabel(
                self.frame_lista, text=texto.ljust(peso),
                font=tema.FUENTE_BOTON, text_color="#9ca3af",
                anchor="w",
            ).grid(row=0, column=col, padx=5, sticky="w")
        # Ancho extra distribuido entre columnas de datos (0 = fija)
        for col, peso in enumerate([0, 2, 2, 2, 1, 3, 0, 0]):
            self.frame_lista.grid_columnconfigure(col, weight=peso)

    def _fila_vehiculo(self, indice: int, vehiculo: Vehiculo, dueno: str, fondo: bool) -> None:
        """Pinta una fila de vehículo con sus botones Editar / Eliminar.

        La primera columna es enumeración visual consecutiva (#1, #2, ...);
        la matricula (PK real) queda en la identificación de las acciones.
        """
        fila = indice + 1
        color = "#252525" if fondo else "transparent"
        textos = [
            f"#{indice + 1}",  # Enumeración de posición (estética de lista)
            vehiculo.matricula,
            vehiculo.modelo,
            vehiculo.marca,
            vehiculo.color or "—",
            dueno,
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
            command=lambda v=vehiculo: self.cargar_vehiculo(v),
        ).grid(row=fila, column=6, padx=5, pady=3)

        ctk.CTkButton(
            self.frame_lista, text="Eliminar", width=70, height=24,
            fg_color=tema.COLOR_ERROR, font=("Arial", 11),
            command=lambda v=vehiculo: self.eliminar_vehiculo(v),
        ).grid(row=fila, column=7, padx=5, pady=3)

    # ------------------------------------------------------------------ #
    # Acciones CRUD
    # ------------------------------------------------------------------ #
    def registrar_vehiculo(self) -> None:
        """INSERT de vehículo nuevo desde el formulario."""
        datos = self._valores_formulario()
        if datos is None:
            return
        try:
            vehiculo_dao.crear(*datos)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.limpiar_formulario()
        self.refrescar_lista()

    def guardar_cambios(self) -> None:
        """UPDATE del vehículo seleccionado; la matricula no cambia."""
        if self.matricula_seleccionada is None:
            showwarning("Sin selección", "Pulsa 'Editar' en un vehículo de la lista para modificarlo.")
            return
        datos = self._valores_formulario()
        if datos is None:
            return
        try:
            # El primer elemento es la matricula leída del formulario:
            # en edición está deshabilitada, así que se reemplaza por la original.
            _, modelo, marca, color, cliente_id = datos
            vehiculo_dao.actualizar(self.matricula_seleccionada, modelo, marca, color, cliente_id)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.limpiar_formulario()
        self.refrescar_lista()

    def eliminar_vehiculo(self, vehiculo: Vehiculo) -> None:
        """DELETE tras confirmación; advierte del borrado en cascada."""
        respuesta = askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el vehículo {vehiculo.matricula}?\n\n"
            "También se borrarán sus órdenes de trabajo asociadas.",
        )
        if not respuesta:
            return
        try:
            vehiculo_dao.eliminar(vehiculo.matricula)
        except RuntimeError as error:
            self._mensaje(str(error), es_error=True)
            return
        self.refrescar_lista()

    def cargar_vehiculo(self, vehiculo: Vehiculo) -> None:
        """Carga un vehículo en el formulario y activa el modo edición."""
        self.matricula_seleccionada = vehiculo.matricula
        self._asignar(self.entry_matricula, vehiculo.matricula)
        self._asignar(self.entry_modelo, vehiculo.modelo)
        self._asignar(self.entry_marca, vehiculo.marca)
        self._asignar(self.entry_color, vehiculo.color or "")
        # Combo de cliente: selecciona la etiqueta del dueño actual
        for etiqueta, cliente_id in self.clientes_disponibles.items():
            if cliente_id == vehiculo.cliente_id:
                self.combo_cliente.set(etiqueta)
                break
        # La matricula es la identidad del vehículo: no se puede cambiar aquí
        self.entry_matricula.configure(state="disabled")
        self.boton_agregar.configure(state="disabled")
        self.boton_guardar.configure(state="normal")
        self._mensaje(f"Editando: {vehiculo.matricula}")

    @staticmethod
    def _asignar(entrada: ctk.CTkEntry, valor: str) -> None:
        """Reemplaza el contenido de un campo (útil en modo edición)."""
        entrada.configure(state="normal")
        entrada.delete(0, "end")
        entrada.insert(0, valor)

    def limpiar_formulario(self) -> None:
        """Deja el formulario vacío y en modo alta."""
        self.matricula_seleccionada = None
        for entrada in (self.entry_matricula, self.entry_modelo,
                        self.entry_marca, self.entry_color):
            self._asignar(entrada, "")
        if self.clientes_disponibles:
            self.combo_cliente.set(list(self.clientes_disponibles.keys())[0])
        self.entry_matricula.configure(state="normal")  # Reactivar para nuevos registros
        self.boton_agregar.configure(state="normal")
        self.boton_guardar.configure(state="disabled")
