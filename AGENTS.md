# AGENTS.md

Instrucciones para agentes (OpenCode) en este repositorio.

## Contexto

Proyecto escolar de escritorio: **Python 3.11+ + CustomTkinter (GUI) + MySQL vía XAMPP**. Organización por capas: `vistas/` (GUI) → `dao/` (acceso a datos) → `db/` (conexión) → `config/` (settings y tema). `modelos/` con dataclasses; `main.py` es el punto de entrada.

## Requisitos de entorno (OBLIGATORIOS antes de ejecutar/pruebas)

- `venv\Scripts\python.exe` es el intérprete del proyecto (creado, con dependencias instaladas). No usar el Python global del sistema: no tiene customtkinter ni mysql-connector.
- MySQL de XAMPP debe estar **iniciado** (Panel de Control de XAMPP). Verificar con `Test-NetConnection localhost -Port 3306`.
- Existe `.env` en la raíz copiado de `.env.example` (usuario `root` con contraseña **vacía** — eso es válido, no es error).
- La BD `taller_mecanico` ya está importada. El usuario de MySQL de XAMPP está en `C:\xampp\mysql\bin\mysql.exe`.

## Comandos

- Ejecutar app: `venv\Scripts\python.exe main.py` (desde `taller_mecanico/`). No mata la ventana; el proceso vive en segundo plano y termina limpio al cerrar la ventana.
- Recrear BD desde cero: `cmd /c "C:\xampp\mysql\bin\mysql.exe -u root --default-character-set=utf8mb4 < db\script_mysql.sql"`.
- Aplicar triggers y procedimientos (solo si no existen): `cmd /c "C:\xampp\mysql\bin\mysql.exe -u root --default-character-set=utf8mb4 < db\triggers_procedures.sql"`.
- Verificar referencias después de cambios: `venv\Scripts\python.exe -m py_compile <archivos>`. No hay tests ni lint configurados.
- PowerShell aquí falla con strings C# `python -c "..."` multilínea (codificación); para pruebas rápidas escribir un script temporal `*.py` y borrarlo.

## Objetos de base de datos (triggers y procedimientos)

La BD `taller_mecanico` incluye objetos almacenados definidos en `db\script_mysql.sql` y `db\triggers_procedures.sql`:

| Objeto | Nombre | Descripción |
|--------|--------|-------------|
| Trigger | `trg_detalle_orden_descontar_stock` | BEFORE INSERT en `detalle_orden`. Valida y descuenta stock de refacciones automáticamente. Lanza error si stock insuficiente. |
| Trigger | `trg_detalle_orden_restaurar_stock` | AFTER DELETE en `detalle_orden`. Restaura stock al borrar una línea de detalle. |
| Procedimiento | `sp_crear_orden` | Crea la cabecera de una orden y devuelve `orden_id` (OUT param). El DAO controla la transacción completa (cabecera + detalles). |

**Nota importante (MariaDB):** los triggers no se disparan con `ON DELETE CASCADE`. Por eso, `orden_dao.eliminar()` borra los detalles explícitamente uno por uno antes de borrar la cabecera, para que el trigger de restauración se ejecute.

**No re-importar `db\script_mysql.sql`** si la BD ya existe y se agregaron triggers/procedimientos después: los `INSERT` de usuarios no usan `INSERT IGNORE` y se duplicarían. Usar `db\triggers_procedures.sql` para agregar solo los objetos nuevos.

## Trampas conocidas

- La app debe abrir el login **aunque MySQL esté apagado** (solo advertencia en consola). `probar_conexion()` devuelve `True/False` sin lanzar excepciones; el DAO de usuarios sí lanza `RuntimeError`.
- `vistas/login.py` y `vistas/menu_principal.py` chocan con imports circulares: importarlos **dentro de los métodos** (patrón de import tardío ya usado).
- El flujo de sesión encadena ventanas: `LoginVista.destroy()` → `MenuPrincipalVista(usuario).mainloop()`; salir hace lo inverso. Cada `CTk` es un root Tk nuevo (los mensajes `invalid command name "..._animation"` al cerrar son ruido inofensivo de CustomTkinter).
- La salida de consola en PowerShell remoto muestra acentos mal (encoding); es cosmético.

## Convenciones obligatorias (decisión del equipo)

- Nombres de variables/funciones en **español**; comentarios breves y profesionales.
- **Solo 3 librerías** en requirements.txt: customtkinter, mysql-connector-python, python-dotenv. No añadir otras sin acordar (el hasheo bcrypt está pendiente para el ajuste final).
- Contraseñas en texto plano por ahora (decisión de alcance); fase posterior las hashea.
- Estética: colores/fuentes/tamaños definidos solo en `config/tema.py` (`COLOR_*`, `FUENTE_*`, `LOGIN_SIZE`, `MENU_SIZE`, `MODULO_SIZE`); las vistas no hardcodean estilos.
- Pantallas de módulo: **redimensionables** con `minsize` protector y layouts con pesos de grid (columnas elásticas). Login queda fijo 400x500 por diseño.

## Módulos funcionales (estado)

- Menú principal: botones conectados → **Clientes**, **Vehículos**, **Órdenes**, **Catálogos**, **Cobros**, **Reportes**, **Salir** (todas las fases completas).
- `vistas/catalogos.py`: pestañas Servicios/Refacciones con CTkTabview; alta/edición/eliminación y ajuste de inventario (± stock) con validación. Usa `servicio_dao`/`refaccion_dao` sin lógica automática.
- Los combos de Órdenes cargan los catálogos al abrir la ventana; además las ventanas recargan al recuperar el foco (ver `utils/recarga.py`).
- `vistas/cobros.py`: maestro-detalle de pagos (`pago_dao`). La regla "al cubrir el saldo la orden pasa a 'pagada'" vive en la VISTA (no en el DAO); pagos parciales permitidos, monto nunca excede el saldo.
- `vistas/reportes.py` + `dao/reportes_dao.py`: 8 reportes de solo lectura. **Criterios de medición**: ingresos por pagos COBRADOS (`pagos.fecha_pago`); órdenes/ventas por órdenes CREADAS (`ordenes.fecha_entrada`). El combo de rango predefinido genera al instante; "Personalizado" valida fechas `AAAA-MM-DD`. La exportación a CSV queda como método `_exportar_csv()` sin botón (pendiente).
- `clientes` tiene campo `frecuente` (TINYINT(1)) **solo manual**: se edita con el checkbox de la vista de clientes (★ dorada en la lista); nada en órdenes/cobros lo modifica.
- Ventanas de módulo: redimensionables con `minsize` y recarga automática de datos al recuperar el foco (`utils/recarga.py`, debounce 0.5 s). Al agregar una vista nueva, conectar `vincular_recarga_foco(self, [...])` al final del `__init__`.

## Grafo de conocimiento (graphify)

- `graphify-out/` contiene el grafo generado y está en `.gitignore`: **artefacto regenerable, nunca commitear**. Si existe `graphify-out/graph.json`, preguntas sobre el código se responden con el grafo (fast path) en vez de re-escanear.
- El paquete es `graphifyy` y está instalado en el **Python global (Python313)**, NO en el venv del proyecto → usar `python -m graphify ...` (el venv no lo tiene; el CLI directo por `dispatch_command` no acepta strings).
- Mejor referencia del CLI: `python -m graphify <comando>` (p. ej. `python -m graphify export html`). El módulo `graphify.cli` expone `dispatch_command` pero desvía por `sys.argv`.
- Para que el SQL participe en el AST: `pip install "graphifyy[sql]"` (instalado en el global).
- Salida de consola con acentos: exportar `PYTHONIOENCODING="utf-8"` antes de correr graphify.
- La extracción semántica (README, AGENTS, requirements) se hace **inline por el agente** con el schema de `references/extraction-spec.md` del skill (no hay GEMINI_API_KEY; no pedir claves).
- Tras cambios de código: `/graphify . --update` (incremental, se apoya en `manifest.json`). Cuidado: la extracción semántica inline de los 3 docs no usa caché — se re-hace en cada `--update` (coste trivial).

## Git

- Trunk-based: commits directos en `main` (rama única, draft school team); mensajes `<type>: <descripción>` en español (`feat`, `fix`, `docs`, `chore`).
- Commits atómicos: un módulo lógico por commit (modelo+DAO / vista / docs por separado).
- Hacer `push` después de probar la fase manualmente. `.gitignore` ya excluye `venv/`, `.env`, `__pycache__/` — nunca commitearlos.
