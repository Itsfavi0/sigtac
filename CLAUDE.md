# CLAUDE.md

Guía para trabajar en **SIGTAC** (Sistema Integrado de Gestión de Triaje y Asignación de Camas).
Prototipo académico de escritorio (curso POO II, Universidad Nacional del Callao). Python 3.12+ y
MySQL 8.0 (en desarrollo también funciona MariaDB 11.8). GUI prevista: Tkinter + CustomTkinter.

> Es una simulación didáctica: los algoritmos de triaje no están validados clínicamente.
> El usuario es estudiante: explica el porqué de los cambios, no solo el qué.

## Comandos

```bash
# Instalación (entorno virtual dentro del proyecto)
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt

# Configuración local (el .env NO se versiona)
cp .env.example .env                   # completar DB_USER, DB_PASS, etc.

# Base de datos (solo desarrollo: DESTRUYEN los datos existentes)
mysql -u <admin> -p < db_scripts/schema.sql    # DROP TABLE + CREATE
mysql -u <admin> -p < db_scripts/seed.sql      # TRUNCATE + datos de prueba
# Usuario de la app (una vez; reemplazar <una_clave_segura> antes): SELECT, INSERT, UPDATE sobre sigtac_db
mysql -u <admin> -p < db_scripts/crear_usuario_app.sql

# Pruebas (no necesitan MySQL ni .env: la BD se simula)
python -m pytest                               # todas
python -m pytest tests/test_cama.py -v         # un archivo
python -m pytest -k "bloqueo" -x               # filtrar por nombre, parar al primer fallo
```

- Usa `python -m pip` y `python -m pytest` (con el `.venv` activado): garantiza que se use el intérprete del entorno.
  No copiar ni mover la carpeta `.venv`; los entornos virtuales guardan rutas absolutas. Para recrearlo:
  `rm -rf .venv && python -m venv .venv && python -m pip install -r requirements-dev.txt`.
- Aún no existe `main.py` ni linter configurado. Si se añaden, documentar aquí su comando.

## Estructura

```text
dao/          Acceso a datos: db_connection.py (Singleton ConexionBD), base_dao.py y un *_dao.py por entidad
models/       Dominio: persona, cama, triaje, estrategias, estados (Enum), excepciones
utils/        security.py (bcrypt) y logging_config.py
db_scripts/   schema.sql, seed.sql, crear_usuario_app.sql y diagrama.png
tests/        pytest: un test_*.py por módulo
docs/         PROJECT_CONTEXT, DEVELOPMENT_PLAN, PROJECT_STATUS y CHANGELOG
```

Pendientes por fase (ver `docs/DEVELOPMENT_PLAN.md`): `controllers/` (Fase 4) y `views/` (Fase 6) no existen aún.

## Arquitectura (capas)

```text
views → controllers → models (dominio) → dao → MySQL
```

- **Views**: solo interfaz. Nunca SQL ni reglas de negocio.
- **Controllers**: orquestan vista, modelos y DAO; aquí van los permisos por rol (`UsuarioSinPermisoError`).
- **Models**: reglas de negocio y estados. Nunca SQL ni importar de `dao/`, `views/` o `controllers/`.
- **DAO**: único lugar con SQL. Reciben y devuelven datos o modelos; no contienen reglas de negocio.
- Las dependencias van solo hacia abajo. No duplicar una regla en dos capas: una regla, un dueño.
- Patrones del proyecto: **DAO**, **Strategy** (`EstrategiaTriaje` → `ReglaManchester`/`ReglaMINSA`),
  **Singleton** (`ConexionBD`). Para un algoritmo nuevo de triaje, crear otra estrategia; no tocar las existentes.

## Reglas de código

- Idioma: nombres de clases, métodos y mensajes en **español**, como el resto del proyecto.
- Estados siempre con los Enum de `models/estados.py` (`EstadoCama`, `EstadoEpisodio`); sus valores
  deben coincidir con los catálogos de `seed.sql` (hay un test que lo comprueba).
- Errores: `ValueError` para datos de entrada inválidos; excepciones de `models/excepciones.py`
  (`SigtacError`) para reglas de negocio violadas. Capturar excepciones específicas, nunca `except Exception`.
- Logging con `logging` y formato diferido (`logger.info("... %s", x)`); nada de `print` ni f-strings en logs.
  `configurar_logging()` se llama una sola vez desde el punto de entrada.
- Los comentarios explican qué hace el código. **El historial de cambios no va en docstrings ni comentarios:
  se registra en `docs/CHANGELOG.md`** (entradas nuevas arriba, con Cambio / Archivos / Motivo / Impacto / Decisiones / Pendientes).

## Base de datos

- Todo SQL con parámetros: `cursor.execute(sql, (valor,))`. Prohibido concatenar o usar f-strings en SQL.
  Si un nombre de tabla/columna/`ORDER BY` es dinámico, validarlo contra una lista blanca.
- No hay borrado físico (RN-11): se usa `estado_registro = FALSE`.
- Cada DAO nuevo hereda de `BaseDAO` (`dao/base_dao.py`) y usa `_consultar_uno`, `_consultar_varios`, `_insertar`
  y `_ejecutar`: ahí se cierran los cursores y los errores de MySQL se traducen a `PersistenciaError`
  (o `RegistroDuplicadoError`, o `ConexionBDError`). `None`/lista vacía = no encontrado; un fallo lanza excepción.
  Excepción: `UsuarioDAO.autenticar` devuelve `None` ante todo fallo, para no revelar la causa.
- Cada DAO tiene un método `_a_<entidad>(fila)` que es el único punto que convierte una fila en un objeto; las
  validaciones las hace el constructor del modelo, no el DAO. `estado_registro` llega como 0/1: convertir con `bool()`.
- `ConexionBD` usa `autocommit=True` y `FOUND_ROWS`: el `rowcount` de un `UPDATE` cuenta las filas *encontradas*
  (0 = no existe), aunque los valores no cambien. Las operaciones multi-paso de escritura (asignar cama, dar de alta,
  cambiar estado de cama + historial) necesitan transacciones explícitas: no escribirlas antes de esa decisión.
- Las reglas críticas viven también en la BD (RN-05 y RN-10 con `UNIQUE`/`CHECK`). Cambios de esquema:
  actualizar `schema.sql`, `seed.sql`, los modelos, las pruebas y `diagrama.png`.
- Un `CHECK` que compare texto (`IN ('A', 'B')`) necesita la columna con `COLLATE utf8mb4_bin`: la collation
  por defecto (`utf8mb4_0900_ai_ci`) ignora mayúsculas y acentos y aceptaría `'mañana'` por `'MAÑANA'`.
- La compatibilidad cama–triaje se decide en Python (`Cama.es_compatible`), **no** con `tipo_cama.nivel_min`.

## Reglas de negocio (resumen)

RN-01: sin triaje activo no se asigna cama · RN-05: solo se reserva una cama disponible, y solo hay una
asignación vigente por cama · RN-07/08: al dar de alta la cama pasa a limpieza y solo vuelve a disponible
con confirmación · RN-09: un episodio conserva el historial de triajes (se agrega uno nuevo, no se edita) ·
RN-10: reclasificar exige justificación escrita (≥ 10 caracteres) · RN-11: baja lógica, nunca borrado físico.

## Seguridad

- Nunca versionar ni mostrar `.env`; nunca poner credenciales en el código. Las variables de conexión son
  obligatorias (sin valores por defecto). Usar un usuario de BD con `SELECT, INSERT, UPDATE`, no `root`.
- Contraseñas solo con bcrypt (`utils/security.py`); nunca registrar claves, hashes, números de documento ni nombres en logs.
- `UsuarioDAO.autenticar` devuelve siempre `None` ante cualquier fallo (sin revelar la causa), valida el documento
  con `DocumentoIdentidad`, usa `simular_verificacion` en las salidas tempranas y bloquea 5 intentos fallidos durante 15 min.
- Las claves del seed son solo de desarrollo; nunca usarlas fuera de local.

## Pruebas

- Toda regla de negocio o cambio de comportamiento lleva su test; los valores límite se prueban explícitamente.
- Los tests de DAO y conexión usan `MagicMock`/`monkeypatch`: no deben requerir MySQL ni `.env`.
- Probar comportamiento, no tiempos (los tiempos son inestables); para el señuelo se verifica que se invoque.
- Una brecha conocida se documenta con `@pytest.mark.xfail(strict=True, reason=...)` hasta corregirla.
- Cambios de SQL (`schema.sql`, consultas) se verifican contra una **base temporal** con otro nombre
  (p. ej. `sigtac_scratch_tmp`) que se elimina al terminar. Nunca ejecutar `schema.sql` o `seed.sql`
  contra `sigtac_db` sin que el usuario lo pida.
- El `.env` usa `sigtac_app`, que no puede crear bases: la verificación en base temporal necesita una cuenta de
  administrador. El script pide la clave con `getpass` y lo ejecuta el usuario; Claude nunca escribe ni guarda esa clave.
- Los valores fijos de Python que reflejan catálogos o `CHECK` de la BD (Enum, tipos de cama, sexo, turno) se
  comparan con `seed.sql`/`schema.sql` en `tests/test_estados_vs_bd.py`.

## Git

- Commits al estilo `tipo(ámbito): mensaje` en español (`feat`, `fix`, `docs`, `test`, `refactor`), uno por cambio lógico.
- No hacer commit ni push sin que el usuario lo pida; proponer el mensaje y los archivos.
- No añadir líneas `Co-Authored-By` (ni otra atribución) de Claude en los mensajes de commit.
- En PowerShell, un mensaje con cuerpo se pasa con `git commit -F archivo`: varios `-m` con comillas pueden quedar
  pegados en el título. Un commit ya subido no se reescribe (`--amend`, `rebase`); uno local sí, comprobando antes
  con `git status -sb` que siga `ahead`.
- Antes de dar algo por terminado: `python -m pytest` en verde y `docs/CHANGELOG.md` actualizado.
