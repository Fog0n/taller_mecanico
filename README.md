# Taller Mecánico

## Descripción breve

Aplicación de escritorio en Python con CustomTkinter para la gestión de un taller mecánico: clientes, vehículos, órdenes de trabajo, cobros y reportes. La persistencia se realiza en MySQL, gestionado localmente con XAMPP.

## Integrantes

> ⚠️ Pendiente: completar con los miembros del equipo.
- Integrante 1 — _: (nombre, correo)
- Integrante 2 — (nombre, correo)
- Integrante 3 — (nombre, correo)

## Requisitos

- **Python 3.11+**
- **XAMPP** con el módulo **MySQL activo** (Panel de Control de XAMPP)
- Git (opcional, para control de versiones)

## Instalación y ejecución

1. Abrir el **Panel de Control de XAMPP** e iniciar el módulo **MySQL** (botón *Start*).
2. Crear el entorno virtual:
   ```bash
   python -m venv venv
   ```
3. Activar el entorno virtual:
   - **Windows:**
     ```bat
     venv\Scripts\activate
     ```
   - **Linux / Mac:**
     ```bash
     source venv/bin/activate
     ```
4. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
5. Copiar `.env.example` como `.env` (los valores por defecto funcionan con XAMPP):
   - **Windows:** `copy .env.example .env`
   - **Linux / Mac:** `cp .env.example .env`
6. Abrir [http://localhost/phpmyadmin](http://localhost/phpmyadmin), ir a la pestaña **Importar** y cargar el archivo `db/script_mysql.sql` (o abrir la pestaña **SQL** y copiar y pegar su contenido).
7. Verificar que la base de datos `taller_mecanico` y sus tablas existan en phpMyAdmin.
8. (Si la BD ya existía y se agregan los objetos nuevos) Ejecutar `db/triggers_procedures.sql` para crear los triggers y el procedimiento almacenado.
9. Ejecutar la aplicación: ```python main.py```

## Estructura del proyecto

```
taller_mecanico/
├── main.py                # Punto de entrada de la aplicación
├── requirements.txt       # Dependencias
├── .env.example           # Plantilla de variables de entorno
├── .gitignore
├── README.md
├── config/
│   ├── __init__.py
│   ├── settings.py        # Carga de variables de .env
│   └── tema.py            # Tema visual (CustomTkinter)
├── db/
│   ├── __init__.py
│   ├── conexion.py        # Conexión y prueba de MySQL
│   ├── script_mysql.sql   # Creación de BD, tablas, triggers y procedimientos
│   └── triggers_procedures.sql  # Triggers y procedimientos almacenados (objetos nuevos de BD)
├── dao/
│   ├── __init__.py
│   ├── cliente_dao.py      # CRUD de clientes (incluye campo frecuente)
│   ├── orden_dao.py        # Órdenes transaccionales (crear, estados, detalle, eliminar) + SP sp_crear_orden
│   ├── refaccion_dao.py    # CRUD de refacciones + descontar_stock (inventario)
│   ├── servicio_dao.py     # CRUD de servicios (catálogo)
│   └── vehiculo_dao.py
├── modelos/                # Clases de dominio (dataclasses)
│   ├── __init__.py
│   ├── cliente.py
│   ├── detalle_orden.py
│   ├── orden.py
│   ├── refaccion.py
│   ├── servicio.py
│   ├── usuario.py
│   └── vehiculo.py
├── vistas/
│   ├── __init__.py
│   ├── login.py            # Ventana de inicio de sesión (fija 400x500)
│   ├── menu_principal.py   # Menú principal (Clientes, Vehículos, Órdenes, Catálogos)
│   ├── clientes.py         # CRUD de clientes + marca manual de "cliente frecuente" (★)
│   ├── vehiculos.py        # CRUD de vehículos (matrícula = PK, no editable en edición)
│   ├── ordenes.py          # Órdenes: ticket, estados, detalle, eliminar, stock visible
│   └── catalogos.py        # Catálogos con pestañas: servicios + refacciones e inventario (± stock)
└── utils/                  # Utilidades (pendiente)
    └── __init__.py
```

## Estado actual

Login con **autenticación real** contra la tabla `usuarios` (usuarios de prueba: `admin/admin123`, `recepcion/recepc123`), flujo de sesión completo (login → menú → salir → login) y los siguientes **módulos funcionales desde el menú**:

**Clientes** — CRUD completo (nombre, teléfono, email, RFC, tipo persona/empresa), con marca manual de **cliente frecuente** (checkbox en el formulario; ★ dorada en la lista).

**Vehículos** — CRUD completo (matrícula como identidad no editable en edición, modelo, marca, color, cliente dueño).

**Órdenes de trabajo** — módulo completo:
- **Crear orden** con líneas de servicios y refacciones (ticket en construcción con total dinámico)
- **Stock visible**: label "Stock disponible" junto al combo de artículos, se actualiza al cambiar tipo y tras registrar
- **Transacción con rollback**: si hay stock insuficiente, no queda ni orden ni líneas huérfanas
- **Flujo de estados**: Abierta → En proceso → Terminada → Entregada → Pagada (semáforo de colores)
- **Detalle de orden**: líneas, subtotales, fecha de entrada/salida, total
- **Eliminar orden** con confirmación y restauración de stock vía trigger

**Catálogos** — ventana con pestañas:
- **Servicios**: alta, edición y eliminación del catálogo de mano de obra (nombre, precio)
- **Refacciones**: alta, edición y eliminación con **inventario** (stock) y ajuste rápido **± Stock** por fila (entradas/salidas con validación de stock suficiente)
- Todo lo dado de alta aquí aparece en los combos de Órdenes al reabrir la ventana

**Aspecto general** — ventanas de módulo **redimensionables** (1120x720 por defecto, con mínimo que garantiza que no se pierda información) y layouts con columnas elásticas. Login compacto fijo.

**Objetos de BD** — triggers de stock automático y procedimiento `sp_crear_orden` (ver sección abajo).


## Notas

- 🔐 **Contraseñas:** los usuarios de prueba (`admin/admin123`, `recepcion/recepc123`) se insertan con la contraseña en **texto plano solo para las primeras pruebas**. En una etapa posterior deberán hashearse (por ejemplo, con `bcrypt`).
- ⚠️ **MySQL/XAMPP:** si el servicio MySQL no está activo en XAMPP, la app se abre igualmente pero mostrará una advertencia en consola indicando que debe iniciarse desde el Panel de Control de XAMPP.

## Objetos de base de datos (triggers y procedimientos)

La BD incluye los siguientes objetos almacenados (definidos en `db/script_mysql.sql` y `db/triggers_procedures.sql`):

| Objeto | Nombre | Propósito |
|--------|--------|-----------|
| Trigger | `trg_detalle_orden_descontar_stock` | Descuenta stock de refacciones al insertar un detalle de orden (valida stock suficiente). |
| Trigger | `trg_detalle_orden_restaurar_stock` | Restaura stock al eliminar una línea de detalle de orden. |
| Procedimiento | `sp_crear_orden` | Crea la cabecera de una orden y devuelve el `orden_id` generado. |

**Nota (MariaDB):** los triggers no se disparan con `ON DELETE CASCADE`. Por eso el DAO borra los detalles explícitamente antes de eliminar la cabecera, para que el trigger de restauración se ejecute.
