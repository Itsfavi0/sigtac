# SIGTAC — Changelog

> Registro cronológico de cambios, decisiones y avances relevantes del proyecto.
> No registrar cada modificación mínima de código; registrar cambios que afecten arquitectura, funcionalidad, reglas de negocio, estructura o dirección del desarrollo.

---

## [2026-10-11] — Alineación del modelo con la BD: fecha_nac y nivel_min (revisión de seguridad, paso 5)

### Cambio
- `empleado`: nueva columna `fecha_nac DATE NOT NULL`, para que la tabla coincida con la clase `Empleado` (que hereda `fecha_nac` de `Persona`).
- `seed.sql`: los 6 empleados incluyen fecha de nacimiento (ficticia).
- `tipo_cama.nivel_min`: el `COMMENT` indica ahora que es **solo informativo** y que la compatibilidad la decide `Cama.es_compatible()` en Python.

### Archivos afectados
- `db_scripts/schema.sql`
- `db_scripts/seed.sql`

### Motivo
- Un futuro `EmpleadoDAO` no podía construir un `Empleado` porque la tabla no guardaba la fecha de nacimiento.
- `nivel_min` contradecía a `es_compatible` (p. ej. Observación: `nivel_min = 4` en la BD, pero la clase acepta niveles 2, 3 y 4). La decisión documentada en `PROJECT_CONTEXT.md` es no comparar contra `nivel_min` en SQL; la columna quedaba como dato engañoso.

### Impacto
- Es necesario volver a ejecutar `schema.sql` y `seed.sql` en cada entorno de desarrollo (borra los datos).
- Los DAOs de empleado deben leer `fecha_nac`.
- Verificado cargando ambos scripts en una base temporal (ya eliminada) y autenticando con un usuario real del seed.

### Decisiones
- Se mantiene la compatibilidad de camas en Python (decisión previa del proyecto); se descartó crear `nivel_max` porque duplicaría la regla en la BD.
- `fecha_nac` es `NOT NULL` por coherencia con `Persona`. Es un dato personal: en un sistema real habría que justificar su recolección.

### Pendientes
- Actualizar `db_scripts/diagrama.png` (aún muestra `empleado` sin `fecha_nac`).
- Permisos duplicados (tabla `rol` frente a `tiene_permiso` en las clases): se resolverá en la Fase 4 (controladores), según el plan de desarrollo.
- Unificar los estados de cama y episodio entre Python y la BD (usar `Enum`; la BD tiene `REFERIDO` y `FUGADO / ABANDONO` que el código no conoce).

---

## [2026-10-11] — Higiene del repositorio: .gitignore, .env.example y README (revisión de seguridad, paso 4)

### Cambio
- `.gitignore` reescrito y ordenado por secciones:
  - Corregido `.mwb` (solo ignoraba un archivo con ese nombre exacto) por `*.mwb`.
  - Añadidos `__pycache__/`, `*.py[cod]`, `.pytest_cache/` y `.env.*` (con la excepción `!.env.example`).
  - Eliminados `node_modules/` y `vendor/`, que no aplican a un proyecto Python.
- Nuevo `.env.example`: plantilla con las variables de conexión, sin valores secretos.
- Nuevo `README.md` en la raíz: descripción, aviso de proyecto académico, requisitos, instalación, configuración, scripts de BD (con advertencia de que destruyen datos) y estructura.

### Archivos afectados
- `.gitignore`
- `.env.example` (nuevo)
- `README.md` (nuevo)

### Motivo
- Sin `__pycache__/` ignorado, los archivos compilados terminarían en el repositorio.
- Sin plantilla, quien clone el proyecto no sabe qué variables definir y la aplicación (que ahora exige las variables) no arrancaría.
- El README documenta los requisitos (Python 3.12+, MySQL 8) y avisa de que `schema.sql` y `seed.sql` borran datos.

### Impacto
- Todo el equipo: cada integrante crea su `.env` a partir de `.env.example`.

### Decisiones
- El README recomienda un usuario de BD con permisos `SELECT, INSERT, UPDATE` sobre `sigtac_db` y no `root`. Si un DAO necesita otro permiso (por ejemplo `DELETE`), se ampliará aquí.
- Se declara en el README que MariaDB no es compatible (collation `utf8mb4_0900_ai_ci`).

### Pendientes
- Añadir instrucciones de ejecución cuando exista `main.py`.
- Fijar versiones en `requirements.txt` (punto de la revisión sobre dependencias).

---

## [2026-10-11] — Estrategias de triaje sin valores por defecto (revisión de seguridad, paso 3)

### Cambio
- `ReglaManchester` y `ReglaMINSA` ya no sustituyen un signo vital ausente por un valor "normal" (`sato2=100`, `pa_sis=120`, `temp=37.0`, `fc=80`). Si falta alguno, o es `None`, lanzan `SignosVitalesIncompletosError` indicando cuáles faltan.
- Nueva validación compartida `EstrategiaTriaje._exigir_signos()` en la clase base.
- Nueva excepción `SignosVitalesIncompletosError` en `models/excepciones.py`.
- Cada estrategia exige únicamente los signos que usa: Manchester `sato2` y `pa_sis`; MINSA `temp` y `fc`.

### Archivos afectados
- `models/estrategias.py`
- `models/excepciones.py`

### Motivo
En triaje, "no medido" no equivale a "normal". Con los valores por defecto, un paciente sin saturación registrada se evaluaba como si tuviera 100 %, lo que podía clasificarlo en un nivel menos urgente del que le corresponde (infraclasificación).

### Impacto
- Módulo de Triaje: quien llame a `clasificar()` debe capturar `SignosVitalesIncompletosError` y pedir al enfermero que complete la medición.

### Decisiones
- No se modificaron los umbrales ni los pesos: los criterios clínicos requieren validación con la norma y se dejan fuera de este cambio.
- Se usa una excepción de dominio (`SigtacError`) en lugar de `ValueError` para poder distinguirla de otros errores de validación.

### Pendientes
- Las dos estrategias dan resultados distintos para el mismo paciente: con los datos del seed del episodio 1 (`sato2=89`, `pa_sis=165`, dolor torácico), Manchester sugiere nivel 1 y MINSA nivel 2, porque MINSA no evalúa saturación ni presión. Revisar con la norma si es intencional.
- Documentar en el README que los algoritmos son una simulación didáctica y no deben usarse con pacientes reales.
- Pruebas automatizadas (`pytest`) de ambas estrategias.

---

## [2026-10-11] — Endurecimiento de autenticación (revisión de seguridad, paso 2)

### Cambio
- `UsuarioDAO.autenticar` valida que el DNI tenga exactamente 8 dígitos (`[0-9]{8}`) antes de consultar la BD.
- Nueva función `utils.security.simular_verificacion()`: ejecuta bcrypt contra un hash señuelo (calculado una vez al importar el módulo). Se invoca cuando el login falla sin comparar contra un hash real (usuario inexistente, cuenta desactivada o sin hash).
- `db_scripts/seed.sql`: los 5 usuarios de prueba tienen ahora hashes bcrypt reales y válidos (60 caracteres) en lugar del placeholder `$2b$12$EjemploHash...`.
- `utils/security.py` (`__main__`): el generador de hashes pide la clave con `getpass` en vez de usar claves fijas escritas en el código.

### Archivos afectados
- `dao/usuario_dao.py`
- `utils/security.py`
- `db_scripts/seed.sql`

### Motivo
- El placeholder del seed tenía 61 caracteres (bcrypt exige 60): `checkpw` lanzaba `ValueError` y ningún usuario de prueba podía iniciar sesión.
- Sin el señuelo, un DNI inexistente respondía al instante y uno existente tardaba ~180 ms (bcrypt), lo que permitía descubrir DNIs válidos midiendo tiempos. Medido tras el cambio: inexistente 185 ms, clave incorrecta 182 ms, desactivado 181 ms.
- Rechazar DNIs mal formados evita consultas innecesarias y cadenas arbitrarias en los logs.

### Impacto
- Módulo de Seguridad y Acceso (autenticación).
- Para cargar los nuevos hashes hay que volver a ejecutar `db_scripts/seed.sql` (hace `TRUNCATE`, solo en BD de desarrollo).

### Decisiones
- Clave de desarrollo de todos los usuarios del seed: `Sigtac#Dev2026`. Es **solo para desarrollo**; nunca debe usarse en un entorno real.
- El formato de DNI se fijó en 8 dígitos aunque la columna `dni` admite 15 caracteres. Si se necesitan carnés de extranjería u otros documentos, habrá que ampliar `PATRON_DNI`.
- Se usa `[0-9]` en vez de `\d` porque en Python `\d` acepta también dígitos de otros alfabetos.
- Los cambios históricos se registran aquí y no como texto dentro de docstrings o comentarios del código.

### Pendientes
- Límite de intentos fallidos / bloqueo temporal de cuenta (requiere columnas nuevas en `usuario`).

---

## [2026-10-11] — Conexión a BD y logging (revisión de seguridad, paso 1)

### Cambio
- `ConexionBD`: ya no usa valores por defecto inseguros (`root` / contraseña vacía); si falta `DB_HOST`, `DB_USER`, `DB_PASS` o `DB_NAME` lanza `ConexionBDError` con un mensaje claro. Se lee `DB_PORT` (3306 por defecto).
- La conexión usa `autocommit=True` y se abre de forma perezosa en `obtener_conexion()`. Singleton y reconexión protegidos con `threading.Lock`.
- Nueva excepción `ConexionBDError` en `models/excepciones.py`; `obtener_conexion()` la lanza en vez de devolver `None`.
- Se eliminó el bloque `__main__` de demostración de `db_connection.py` y los `print` pasaron a `logging`.
- `UsuarioDAO`: captura `ConexionBDError`; los logs dejaron de incluir DNI y nombres (usan `id_empleado` y rol) y usan formato diferido (`%s`) en vez de f-strings.
- Nuevo `utils/logging_config.py` con `configurar_logging()`, a llamar una vez desde el punto de entrada.

### Archivos afectados
- `dao/db_connection.py`
- `dao/usuario_dao.py`
- `models/excepciones.py`
- `utils/logging_config.py` (nuevo)

### Motivo
- Con `autocommit=False` y una única conexión compartida, una consulta quedaba atada a una "foto" antigua de la transacción (`REPEATABLE READ`): un usuario desactivado por un administrador podía seguir viéndose como activo.
- Los valores por defecto ocultaban errores de configuración e intentaban entrar como `root` sin clave.
- DNI y nombres son datos personales; no deben quedar en los logs. Con f-strings, un DNI con saltos de línea podía falsear entradas del log.

### Impacto
- Capa DAO y arranque de la aplicación (falta de configuración ahora es un error explícito).
- Cualquier DAO nuevo debe capturar `ConexionBDError`.

### Decisiones
- `autocommit=True` es una solución provisional válida mientras solo haya lecturas. Cuando se implementen DAOs de escritura que necesiten transacciones (asignar cama, dar de alta), migrar a un pool de conexiones (`mysql.connector.pooling`) con `commit`/`rollback` explícitos.

### Pendientes
- Llamar a `configurar_logging()` desde `main.py` cuando exista.

---

## [2026-10-05] — Robustecimiento y corrección de excepciones en UsuarioDAO

### Cambio
Refactorización del método `autenticar` en `UsuarioDAO`:
- Validación y saneamiento de entradas (`dni`, `password_plano`).
- Uso de cursor en modo `buffered=True` dentro del bloque `try` para proteger el Singleton de MySQL (`ConexionBD`).
- Reemplazo de captura genérica de excepciones (`Exception`) por `mysql.connector.Error as DBError`, eliminando la advertencia de inspección de PyCharm (`Too broad exception clause`).
- Cierre seguro del cursor dentro del bloque `finally` protegido contra desconexiones inesperadas.
- Migración de mensajes por consola (`print`) a la biblioteca estándar `logging`.

### Archivos afectados
- `dao/usuario_dao.py`

### Motivo
Evitar desincronizaciones de socket (`InternalError: Unread result found`) en la conexión compartida por la aplicación, prevenir excepciones no controladas ante entradas vacías o nulas y cumplir las directrices de inspección estática y manejo de excepciones específicas de Python y PyCharm.

### Impacto
- Módulo de Seguridad y Acceso (autenticación).
- Robustez y resiliencia en la capa DAO y en el ciclo de vida de los cursores MySQL.

### Decisiones
- Se captura específicamente `DBError` (`mysql.connector.Error`) tanto en la consulta como en el cierre del cursor en `finally` para apegarse a las recomendaciones de PEP 8 y PyCharm.
- Se mantiene el retorno del diccionario de sesión limpio (removiendo `hash_clave`) a la espera de la integración con `auth_controller.py`.

### Pendientes
- Actualizar `db_scripts/seed.sql` con un hash bcrypt válido para el administrador de pruebas.
- Continuar con la implementación de `paciente_dao.py`.

---

## [2026-10-05] — Estado inicial registrado

### Avance informado

El desarrollo actual se encuentra trabajando en:

```text
dao/usuario_dao.py
```

La documentación de planificación mantiene la Fase 2 (`models/`) como **En curso**, mientras que el trabajo actual ya ha comenzado a entrar en la Fase 3 (`dao/`).

Por este motivo, el estado no se marca como “Fase 3 completada”.

### Nota

El contenido concreto y el grado de finalización de `usuario_dao.py` deben verificarse contra el código real antes de marcar sus funcionalidades como completadas.

---

## [2026-10-05] — Decisiones técnicas documentadas

Se conservaron como decisiones importantes del proyecto:

### Arquitectura

Arquitectura por capas:

```text
Views
  ↓
Controllers
  ↓
Models / Domain
  ↓
DAO
  ↓
MySQL
```

### Patrones

- DAO para separar SQL del dominio.
- Strategy para algoritmos de clasificación de triaje.
- Singleton para la conexión a MySQL.

### Camas

La compatibilidad no debe resolverse comparando directamente `tipo_cama.nivel_min` en SQL.

La consulta DAO obtiene camas disponibles y el objeto correspondiente decide la compatibilidad mediante:

```text
cama.es_compatible(nivel)
```

### Seguridad

- `bcrypt` para contraseñas.
- `.env` para credenciales.
- Consultas parametrizadas.
- Validación de `usuario.activo`.

### Auditoría

La auditoría de operaciones sensibles se realizará mediante llamadas explícitas desde los controladores a `auditoria_dao`.

---

## Plantilla para futuras entradas

Copiar esta estructura:

```markdown
## [YYYY-MM-DD] — Título del cambio

### Cambio
Descripción breve.

### Archivos afectados
- `ruta/archivo.py`
- `ruta/otro_archivo.py`

### Motivo
Por qué se hizo.

### Impacto
Qué módulos/reglas afecta.

### Decisiones
Si hubo una decisión técnica importante.

### Pendientes
Qué queda por hacer.
```

---

## Reglas del changelog

Registrar especialmente:

- cambios de arquitectura;
- cambios de base de datos;
- cambios de reglas de negocio;
- nuevos patrones;
- cambios de flujo;
- correcciones importantes;
- decisiones que deban explicarse en la sustentación;
- cambios de orden en el plan;
- problemas relevantes y su solución.

No usar el changelog como sustituto del código ni como documentación de cada línea modificada.
