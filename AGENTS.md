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
- Verificar referencias después de cambios: `venv\Scripts\python.exe -m py_compile <archivos>`. No hay tests ni lint configurados.
- PowerShell aquí falla con strings C# `python -c "..."` multilínea (codificación); para pruebas rápidas escribir un script temporal `*.py` y borrarlo.

## Trampas conocidas

- **NO re-importar `db\script_mysql.sql`** si la BD ya existe: los `INSERT` de usuarios no están protegidos con `INSERT IGNORE`, se duplicarían los usuarios de prueba.
- La app debe abrir el login **aunque MySQL esté apagado** (solo advertencia en consola). `probar_conexion()` devuelve `True/False` sin lanzar excepciones; el DAO de usuarios sí lanza `RuntimeError`.
- `vistas/login.py` y `vistas/menu_principal.py` chocan con imports circulares: importarlos **dentro de los métodos** (patrón de import tardío ya usado).
- El flujo de sesión encadena ventanas: `LoginVista.destroy()` → `MenuPrincipalVista(usuario).mainloop()`; salir hace lo inverso. Cada `CTk` es un root Tk nuevo (los mensajes `invalid command name "..._animation"` al cerrar son ruido inofensivo de CustomTkinter).
- La salida de consola en PowerShell remoto muestra acentos mal (encoding); es cosmético.

## Convenciones obligatorias (decisión del equipo)

- Nombres de variables/funciones en **español**; comentarios breves y profesionales.
- **Solo 3 librerías** en requirements.txt: customtkinter, mysql-connector-python, python-dotenv. No añadir otras sin acordar (el hasheo bcrypt está pendiente para el ajuste final).
- Contraseñas en texto plano por ahora (decisión de alcance); fase posterior las hashea.
- Estética: colores/fuentes/tamaños definidos solo en `config/tema.py` (`COLOR_*`, `FUENTE_*`, `LOGIN_SIZE`, `MENU_SIZE`); las vistas no hardcodean estilos.

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
