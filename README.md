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
8. Ejecutar la aplicación: ```python main.py```

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
│   └── script_mysql.sql   # Creación de BD y tablas
├── modelos/               # Clases de dominio (pendiente)
│   └── __init__.py
├── dao/                   # Acceso a datos (pendiente)
│   └── __init__.py
├── vistas/
│   ├── __init__.py
│   ├── login.py           # Ventana de inicio de sesión
│   └── menu_principal.py  # Menú principal
└── utils/                 # Utilidades (pendiente)
    └── __init__.py
```

## Estado actual

Login con **autenticación real** contra la tabla `usuarios` (usuarios de prueba: `admin/admin123`, `recepcion/recepc123`), flujo de sesión completo (login → menú → salir → login) y **CRUD funcional de Clientes y Vehículos** desde el menú. Órdenes de trabajo en desarrollo.

## Notas

- 🔐 **Contraseñas:** los usuarios de prueba (`admin/admin123`, `recepcion/recepc123`) se insertan con la contraseña en **texto plano solo para las primeras pruebas**. En una etapa posterior deberán hashearse (por ejemplo, con `bcrypt`).
- ⚠️ **MySQL/XAMPP:** si el servicio MySQL no está activo en XAMPP, la app se abre igualmente pero mostrará una advertencia en consola indicando que debe iniciarse desde el Panel de Control de XAMPP.
