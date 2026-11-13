"""
Vista de reportes del taller (rediseño completo).

Ventana de módulo (CTkToplevel) con panel lateral para elegir entre 8
reportes, selector desplegable de rango (Hoy, Esta semana, Este mes,
Mes pasado, Este año, Historial o Personalizado con fechas manuales),
parámetro "Top N" para los reportes de ranking, y tabla de resultados
con fila TOTAL destacada.

Solo consulta en pantalla; la exportación a CSV queda preparada como
método para una fase posterior.
"""

from tkinter.messagebox import showwarning
from datetime import date, datetime, timedelta

import customtkinter as ctk

from config import tema
from dao import reportes_dao
from dao.orden_dao import EstadoValido
from vistas.ordenes import ETIQUETAS_ESTADO

# Catálogo de reportes: (clave, nombre, descripcion, usa_top_n)
REPORTES = [
    ("resumen", "Resumen general",
     "Cobrado, órdenes, ticket promedio y clientes del periodo", False),
    ("por_dia", "Ingresos por día",
     "Cuánto se cobró cada día del rango", False),
    ("por_metodo", "Ingresos por método",
     "Efectivo, tarjeta y transferencia con su % del total", False),
    ("por_estado", "Órdenes por estado",
     "Órdenes creadas y su valor según su estado", False),
    ("top_servicios", "Top servicios",
     "Servicios más vendidos en las órdenes del rango", True),
    ("top_refacciones", "Top refacciones",
     "Refacciones más vendidas en las órdenes del rango", True),
    ("por_cliente", "Ingresos por cliente",
     "A cuánto asciende el cobro por cliente (top N)", True),
    ("por_usuario", "Actividad por usuario",
     "Órdenes y cobros registrados por cada usuario", False),
]

ETIQUETAS_METODO = {
    "efectivo": "Efectivo",
    "tarjeta": "Tarjeta",
    "transferencia": "Transferencia",
}

# Atajos de rango: etiqueta -> función que devuelve (desde, hasta)
def _rango_hoy():
    hoy = date.today().isoformat()
    return hoy, hoy

def _rango_semana():
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    return lunes.isoformat(), hoy.isoformat()

def _rango_mes():
    hoy = date.today()
    return hoy.replace(day=1).isoformat(), hoy.isoformat()

def _rango_mes_pasado():
    hoy = date.today()
    ultimo_mes = hoy.replace(day=1) - timedelta(days=1)
    return ultimo_mes.replace(day=1).isoformat(), ultimo_mes.isoformat()

def _rango_anio():
    hoy = date.today()
    return hoy.replace(month=1, day=1).isoformat(), hoy.isoformat()

def _rango_historial():
    return "2000-01-01", date.today().isoformat()

ATAJOS_RANGO = [
    ("Hoy", _rango_hoy),
    ("Esta semana", _rango_semana),
    ("Este mes", _rango_mes),
    ("Mes pasado", _rango_mes_pasado),
    ("Este año", _rango_anio),
    ("Historial", _rango_historial),
]


class ReportesVista(ctk.CTkToplevel):
    """Ventana de generación de reportes por rango de fechas."""

    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario

        # Reporte activo (clave del catálogo REPORTES)
        self.reporte_actual = REPORTES[0][0]

        # Configuración de la ventana
        self.title("Taller Mecánico - Reportes")
        self.geometry(tema.MODULO_SIZE)
        self.resizable(True, True)
        self.minsize(1000, 680)  # Nunca más pequeño: no se pierde información

        # Lateral fijo (catálogo de reportes) + área elástica (resultados)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_menu()
        self._construir_area()
        self.seleccionar_reporte(self.reporte_actual)

    # ------------------------------------------------------------------ #
    # Panel lateral: catálogo de reportes
    # ------------------------------------------------------------------ #
    def _construir_menu(self) -> None:
        """Panel izquierdo: lista de reportes seleccionables."""
        self.frame_menu = ctk.CTkFrame(self, width=310)
        self.frame_menu.grid(row=0, column=0, sticky="nsw", padx=(15, 5), pady=15)
        self.frame_menu.grid_propagate(False)  # Respeta el ancho fijado

        ctk.CTkLabel(
            self.frame_menu, text="Reportes disponibles",
            font=tema.FUENTE_TITULO, text_color=tema.COLOR_TEXTO,
        ).pack(pady=(12, 5))

        self.boton_reporte = {}
        for clave, nombre, _descripcion, _top in REPORTES:
            boton = ctk.CTkButton(
                self.frame_menu, text=nombre, anchor="w", height=36,
                fg_color="transparent", hover_color="#333333",
                font=tema.FUENTE_TEXTO, text_color=tema.COLOR_TEXTO,
                command=lambda c=clave: self.seleccionar_reporte(c),
            )
            boton.pack(fill="x", padx=12, pady=3)
            self.boton_reporte[clave] = boton

        # Descripción del reporte activo (al pie del panel)
        self.label_descripcion = ctk.CTkLabel(
            self.frame_menu, text="", wraplength=260, justify="left",
            font=(tema.FUENTE_TEXTO[0], 13), text_color="#9ca3af",
        )
        self.label_descripcion.pack(side="bottom", padx=14, pady=(5, 14))

    # ------------------------------------------------------------------ #
    # Área derecha: formulario + resultados
    # ------------------------------------------------------------------ #
    def _construir_area(self) -> None:
        """Área principal: rango de fechas, atajos, generar y resultados."""
        self.frame_area = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_area.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)

        # Selector de rango (combo) + Top N + generar
        frame_form = ctk.CTkFrame(self.frame_area)
        frame_form.pack(fill="x", pady=(0, 8))
        for col in range(5):
            frame_form.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(frame_form, text="Rango *", font=tema.FUENTE_TEXTO).grid(row=0, column=0, padx=10, sticky="w")
        self.combo_rango = ctk.CTkComboBox(
            frame_form,
            values=[etiqueta for (etiqueta, _f) in ATAJOS_RANGO] + ["Personalizado"],
            width=190, font=tema.FUENTE_TEXTO, state="readonly",
            command=lambda _valor: self._al_cambiar_rango(),  # Genera al elegir
        )
        self.combo_rango.set("Este mes")  # Predeterminado de la ventana
        self.combo_rango.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="ew")

        # Top N: solo visible en los reportes de ranking
        ctk.CTkLabel(frame_form, text="Top N *", font=tema.FUENTE_TEXTO).grid(row=0, column=2, padx=10, sticky="w")
        self.entry_top = ctk.CTkEntry(frame_form, width=80, font=tema.FUENTE_TEXTO, justify="center")
        self.entry_top.insert(0, "5")
        self.entry_top.grid(row=1, column=2, padx=10, pady=(2, 10), sticky="ew")

        self.boton_generar = ctk.CTkButton(
            frame_form, text="Generar reporte", command=self.generar_reporte,
            fg_color=tema.COLOR_BOTON, font=tema.FUENTE_BOTON, width=170,
        )
        self.boton_generar.grid(row=1, column=3, columnspan=2, padx=10, pady=(2, 10))

        # Fechas manuales: solo visibles con el rango 'Personalizado'
        self.frame_fechas = ctk.CTkFrame(self.frame_area, fg_color="transparent")
        self.frame_fechas.pack(fill="x", pady=(0, 5))
        for col in range(2):
            self.frame_fechas.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(self.frame_fechas, text="Desde (AAAA-MM-DD) *", font=tema.FUENTE_TEXTO).grid(row=0, column=0, padx=10, sticky="w")
        self.entry_desde = ctk.CTkEntry(self.frame_fechas, width=150, font=tema.FUENTE_TEXTO, justify="center")
        self.entry_desde.grid(row=1, column=0, padx=10, sticky="ew")

        ctk.CTkLabel(self.frame_fechas, text="Hasta (AAAA-MM-DD) *", font=tema.FUENTE_TEXTO).grid(row=0, column=1, padx=10, sticky="w")
        self.entry_hasta = ctk.CTkEntry(self.frame_fechas, width=150, font=tema.FUENTE_TEXTO, justify="center")
        self.entry_hasta.grid(row=1, column=1, padx=10, sticky="ew")
        self.frame_fechas.pack_forget()  # Ocultas hasta elegir 'Personalizado'

        # Resumen textual + tabla de resultados
        self.label_resumen = ctk.CTkLabel(
            self.frame_area, text="Elige un reporte, ajusta el rango y presiona 'Generar reporte'.",
            font=tema.FUENTE_TEXTO, text_color=tema.COLOR_TEXTO, anchor="w",
        )
        self.label_resumen.pack(fill="x", pady=(2, 5))

        self.frame_resultados = ctk.CTkScrollableFrame(self.frame_area, label_text="Resultados")
        self.frame_resultados.pack(fill="both", expand=True, pady=(0, 5))

    # ------------------------------------------------------------------ #
    # Selección de reporte y atajos
    # ------------------------------------------------------------------ #
    def seleccionar_reporte(self, clave: str) -> None:
        """Marca el reporte elegido en el panel lateral y ajusta la vista."""
        self.reporte_actual = clave

        for clave_boton, boton in self.boton_reporte.items():
            activo = clave_boton == clave
            boton.configure(
                fg_color=tema.COLOR_BOTON if activo else "transparent",
                text_color="#ffffff" if activo else tema.COLOR_TEXTO,
            )

        descripcion = next(d for (c, _n, d, _t) in REPORTES if c == clave)
        self.label_descripcion.configure(text=descripcion)

        # El campo Top N solo aplica a los reportes de ranking
        usa_top = next(t for (c, _n, _d, t) in REPORTES if c == clave)
        if usa_top:
            self.entry_top.grid()
        else:
            self.entry_top.grid_remove()

    def _al_cambiar_rango(self) -> None:
        """Muestra fechas manuales solo en 'Personalizado' y genera al elegir."""
        if self.combo_rango.get() == "Personalizado":
            self.frame_fechas.pack(fill="x", pady=(0, 5), before=self.label_resumen)
            self.label_resumen.configure(
                text="Escribe las fechas y presiona 'Generar reporte'.",
                text_color=tema.COLOR_TEXTO, anchor="w",
            )
            return
        self.frame_fechas.pack_forget()
        self.generar_reporte()  # Atajo: aplicar fechas y generar al instante

    def _fechas_del_rango(self):
        """Fechas según el combo: atajo predefinido o entradas manuales."""
        seleccion = self.combo_rango.get()
        if seleccion == "Personalizado":
            return self._rango_valido()
        return dict(ATAJOS_RANGO)[seleccion]()

    # ------------------------------------------------------------------ #
    # Validaciones
    # ------------------------------------------------------------------ #
    def _rango_valido(self):
        """Valida las fechas; devuelve (desde, hasta) o None con aviso."""
        try:
            desde = datetime.strptime(self.entry_desde.get().strip(), "%Y-%m-%d").date()
            hasta = datetime.strptime(self.entry_hasta.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            showwarning("Fecha inválida", "Las fechas deben tener el formato AAAA-MM-DD (ej. 2026-11-01).")
            return None
        if desde > hasta:
            showwarning("Rango inválido", "La fecha 'Desde' no puede ser posterior a 'Hasta'.")
            return None
        return desde.isoformat(), hasta.isoformat()

    def _top_valido(self) -> int | None:
        """Valida el campo Top N (solo en reportes de ranking)."""
        texto = self.entry_top.get().strip()
        try:
            top = int(texto)
        except ValueError:
            showwarning("Top N inválido", "El valor de Top N debe ser un número entero (ej. 5).")
            return None
        if top < 1:
            showwarning("Top N inválido", "El valor de Top N debe ser al menos 1.")
            return None
        return top

    # ------------------------------------------------------------------ #
    # Generación de reportes
    # ------------------------------------------------------------------ #
    def generar_reporte(self) -> None:
        """Ejecuta la consulta del reporte activo y pinta la tabla."""
        fechas = self._fechas_del_rango()
        if fechas is None:
            return
        desde, hasta = fechas

        # Los reportes de ranking exigen Top N válido antes de consultar
        if self.reporte_actual in ("top_servicios", "top_refacciones", "por_cliente"):
            if self._top_valido() is None:
                return

        try:
            # Despacho por clave del catálogo; devuelve (encabezados, filas,
            # total_fila | None, resumen_texto)
            encabezados, filas, total_fila, resumen = self._consultar(
                desde, hasta,
            )
        except RuntimeError as error:
            self.label_resumen.configure(text=f"Error: {error}", text_color=tema.COLOR_ERROR)
            return

        self.label_resumen.configure(
            text=resumen, text_color=tema.COLOR_TEXTO, anchor="w",
        )
        self._pintar_tabla(encabezados, filas, total_fila)

    def _consultar(self, desde: str, hasta: str):
        """Ejecuta el reporte activo; normaliza su salida para la tabla."""
        clave = self.reporte_actual
        periodo = f"periodo {desde} a {hasta}"

        if clave == "resumen":
            datos = reportes_dao.resumen_general(desde, hasta)
            filas = [
                ("Total cobrado", f"${datos['cobrado']:.2f}"),
                ("Órdenes del periodo", str(datos["ordenes"])),
                ("Ticket promedio (por pago)", f"${datos['ticket_promedio']:.2f}"),
                ("Clientes atendidos", str(datos["clientes"])),
            ]
            nombre = "Resumen general"
            return (["Indicador", "Valor"], filas, None,
                    f"{nombre} — {periodo}")

        if clave == "por_dia":
            datos = reportes_dao.ingresos_por_dia(desde, hasta)
            filas = [(str(fecha), str(numero), f"${monto:.2f}")
                     for (fecha, numero, monto) in datos]
            total = sum(m for (_f, _n, m) in datos)
            return (["Fecha", "Pagos", "Monto"], filas,
                    ("TOTAL", str(sum(n for (_f, n, _m) in datos)), f"${total:.2f}"),
                    f"Ingresos por día — {periodo} — TOTAL: ${total:.2f}")

        if clave == "por_metodo":
            datos = reportes_dao.ingresos_por_metodo(desde, hasta)
            filas = [
                (ETIQUETAS_METODO.get(m, m), str(n), f"${monto:.2f}", f"{pct}%")
                for (m, n, monto, pct) in datos
            ]
            total = sum(m for (_x, _n, m, _p) in datos)
            return (["Método", "Pagos", "Monto", "%"], filas,
                    ("TOTAL", str(sum(n for (_x, n, _m, _p) in datos)),
                     f"${total:.2f}", "100%"),
                    f"Ingresos por método — {periodo} — TOTAL: ${total:.2f}")

        if clave == "por_estado":
            datos = reportes_dao.ordenes_por_estado(desde, hasta)
            # Ordena por el flujo de trabajo (abierta → pagada)
            flujo = {estado: i for i, estado in enumerate(EstadoValido)}
            datos.sort(key=lambda fila: flujo.get(fila[0], 99))
            filas = [(ETIQUETAS_ESTADO.get(e, e), str(n), f"${v:.2f}")
                     for (e, n, v) in datos]
            total = sum(v for (_e, _n, v) in datos)
            return (["Estado", "Órdenes", "Valor"], filas,
                    ("TOTAL", str(sum(n for (_e, n, _v) in datos)), f"${total:.2f}"),
                    f"Órdenes por estado — {periodo} — TOTAL: ${total:.2f}")

        if clave == "top_servicios":
            top = self._top_valido()
            if top is None:
                raise RuntimeError("(cancelado)")
            datos = reportes_dao.top_servicios(desde, hasta, top)
            filas = [(nombre, str(cantidad), f"${dinero:.2f}")
                     for (nombre, cantidad, dinero) in datos]
            total = sum(d for (_n, _c, d) in datos)
            return (["Servicio", "Cantidad", "Vendido"], filas,
                    ("TOTAL", str(sum(c for (_n, c, _d) in datos)), f"${total:.2f}"),
                    f"Top {top} servicios — {periodo} — TOTAL: ${total:.2f}")

        if clave == "top_refacciones":
            top = self._top_valido()
            if top is None:
                raise RuntimeError("(cancelado)")
            datos = reportes_dao.top_refacciones(desde, hasta, top)
            filas = [(nombre, str(cantidad), f"${dinero:.2f}")
                     for (nombre, cantidad, dinero) in datos]
            total = sum(d for (_n, _c, d) in datos)
            return (["Refacción", "Cantidad", "Vendido"], filas,
                    ("TOTAL", str(sum(c for (_n, c, _d) in datos)), f"${total:.2f}"),
                    f"Top {top} refacciones — {periodo} — TOTAL: ${total:.2f}")

        if clave == "por_cliente":
            top = self._top_valido()
            if top is None:
                raise RuntimeError("(cancelado)")
            datos = reportes_dao.ingresos_por_cliente(desde, hasta, top)
            filas = [(cliente, str(numero), f"${monto:.2f}")
                     for (cliente, numero, monto) in datos]
            total = sum(m for (_c, _n, m) in datos)
            return (["Cliente", "Pagos", "Monto"], filas,
                    ("TOTAL", str(sum(n for (_c, n, _m) in datos)), f"${total:.2f}"),
                    f"Top {top} clientes por ingresos — {periodo} — TOTAL: ${total:.2f}")

        # por_usuario
        datos = reportes_dao.actividad_por_usuario(desde, hasta)
        filas = [
            (usuario, str(ordenes), str(pagos), f"${cobrado:.2f}")
            for (usuario, ordenes, pagos, cobrado) in datos
        ]
        total = sum(c for (_u, _o, _p, c) in datos)
        return (["Usuario", "Órdenes creadas", "Pagos registrados", "Cobrado"], filas,
                ("TOTAL", str(sum(o for (_u, o, _p, _c) in datos)),
                 str(sum(p for (_u, _o, p, _c) in datos)), f"${total:.2f}"),
                f"Actividad por usuario — {periodo} — TOTAL cobrado: ${total:.2f}")

    # ------------------------------------------------------------------ #
    # Pintado de resultados
    # ------------------------------------------------------------------ #
    def _pintar_tabla(self, encabezados: list[str], filas: list[tuple],
                      total_fila: tuple | None) -> None:
        """Pinta la tabla (cabecera, filas cebreadas y fila TOTAL)."""
        for widget in self.frame_resultados.winfo_children():
            widget.destroy()

        if not filas:
            ctk.CTkLabel(
                self.frame_resultados, text="(sin datos en el rango seleccionado)",
                font=tema.FUENTE_TEXTO, text_color="#9ca3af",
            ).pack(padx=10, pady=12, anchor="w")
            return

        # Cabecera
        for col, texto in enumerate(encabezados):
            ctk.CTkLabel(
                self.frame_resultados, text=texto, font=tema.FUENTE_BOTON,
                text_color="#9ca3af", anchor="w",
            ).grid(row=0, column=col, padx=8, sticky="w")
        for col in range(len(encabezados)):
            self.frame_resultados.grid_columnconfigure(col, weight=1)

        # Filas de datos (cebreadas)
        for i, fila in enumerate(filas):
            color = "#252525" if i % 2 == 1 else "transparent"
            for col, texto in enumerate(fila):
                ctk.CTkLabel(
                    self.frame_resultados, text=texto, font=tema.FUENTE_TEXTO,
                    text_color=tema.COLOR_TEXTO, anchor="w", fg_color=color,
                ).grid(row=i + 1, column=col, padx=8, pady=2, sticky="w")

        # Fila TOTAL destacada al final
        if total_fila is not None:
            fila_total = i + 2
            for col, texto in enumerate(total_fila):
                ctk.CTkLabel(
                    self.frame_resultados, text=texto, font=tema.FUENTE_BOTON,
                    text_color="#10b981", anchor="w", fg_color="#252525",
                ).grid(row=fila_total, column=col, padx=8, pady=(4, 2), sticky="w")

    # ------------------------------------------------------------------ #
    # Exportación (pendiente para una fase posterior)
    # ------------------------------------------------------------------ #
    def _exportar_csv(self) -> None:
        """Guarda la tabla visible como CSV (por implementar)."""
        raise NotImplementedError("La exportación a CSV se agregará en una fase posterior.")
