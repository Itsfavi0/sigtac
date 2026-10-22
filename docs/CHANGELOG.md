# SIGTAC — Changelog

> Registro cronológico de cambios, decisiones y avances relevantes del proyecto.
> No registrar cada modificación mínima de código; registrar cambios que afecten arquitectura, funcionalidad, reglas de negocio, estructura o dirección del desarrollo.

---

## [2026-10-21] — `AuditoriaDAO` y `sigtac_db` recreada

### Cambio
- Nuevo `dao/auditoria_dao.py` (`AuditoriaDAO`, hereda de `BaseDAO`): `registrar(id_usuario, tabla, accion, id_registro, detalles=None)` y `listar_por_registro(tabla, id_registro)`.
- Nuevo `models/auditoria.py`: `AccionAuditoria` (`INSERT`, `UPDATE`, `ANULAR`, `IDENTIFICAR`).
- Nuevo `tests/test_auditoria_dao.py` (32 pruebas) y 2 pruebas en `tests/test_estados_vs_bd.py`: la lista de tablas auditables coincide con `schema.sql` y las acciones del seed existen en el Enum.
- El usuario recreó `sigtac_db` con `schema.sql` y `seed.sql` actuales.

### Archivos afectados
- `dao/auditoria_dao.py` (nuevo), `models/auditoria.py` (nuevo), `tests/test_auditoria_dao.py` (nuevo), `tests/test_estados_vs_bd.py`, `CLAUDE.md`, `docs/`

### Motivo
Siguiente DAO del plan. Es de una sola tabla y no necesita transacciones, y los controladores de la Fase 4 lo usarán después de cada operación sensible.

### Impacto
- Pruebas: 531 pasan.
- `listar_por_registro` se comprobó en solo lectura contra `sigtac_db` (usuario `sigtac_app`): devuelve las 2 filas del seed con `AccionAuditoria`, `fecha_hora` como `datetime` y `detalles` en `None`, y una lista vacía para un registro sin auditoría. `registrar` no se probó contra MySQL real para no dejar filas de prueba en `sigtac_db`: la bitácora no admite borrado.

### Decisiones
- **Solo inserción:** el DAO no tiene métodos para modificar ni borrar; un test lo comprueba. Una auditoría editable no sirve como evidencia.
- **`accion` con Enum:** evita que la misma acción quede escrita de varias formas y no se pueda agrupar en reportes. `AccionAuditoria` está en `models/` porque la usarán los controladores.
- **Lista blanca de tablas (`TABLAS_AUDITABLES`):** el nombre de la tabla viaja como parámetro, así que no es un riesgo de inyección; la lista evita registros que apunten a tablas inexistentes. Incluye todas las tablas del esquema salvo la propia bitácora.
- **`detalles` se convierte a JSON en el DAO** (`ensure_ascii=False`, para que las tildes queden legibles). Debe contener solo ids y valores no sensibles, nunca documentos, nombres ni claves. El log solo registra id, tabla y acción, nunca los detalles.
- **La fecha la pone MySQL** (`DEFAULT CURRENT_TIMESTAMP`): todos los registros usan el mismo reloj, el del servidor.
- **Un fallo al auditar lanza `PersistenciaError`**, como el resto de los DAO. Si la operación auditada debe deshacerse en ese caso se decidirá junto con las transacciones.
- `id_usuario` es obligatorio en la tabla, así que los intentos de login de usuarios inexistentes no se auditan (quedan cubiertos por el bloqueo de intentos y los logs).

### Pendientes
- Llamar a `AuditoriaDAO.registrar` desde los controladores (Fase 4).
- Opcional: quitar a `sigtac_app` el permiso `UPDATE` sobre `bitacora_auditoria`.

---

## [2026-10-21] — Pacientes sin identificar (NN)

### Cambio
- `paciente.id_tipo_documento` y `paciente.num_documento` admiten `NULL` (paciente sin identificar). Nuevo `CHECK CH_paciente_documento`: los dos son `NULL` o los dos tienen valor. La FK a `tipo_documento` pasa a `ON UPDATE RESTRICT`. `empleado` no cambia: su documento sigue siendo obligatorio.
- `Persona` admite `documento=None` solo en las subclases que lo permiten (`_ADMITE_SIN_DOCUMENTO`, `True` solo en `Paciente`).
- `Paciente`: propiedad `identificado`, fábrica `Paciente.no_identificado(sexo, edad_estimada, id_seguro)` y método `identificar(documento, nombres, apellidos, fecha_nac)`.
- `PacienteDAO`: `LEFT JOIN tipo_documento`, `crear` acepta pacientes sin documento, nuevos `listar_no_identificados()` e `identificar(paciente)`.
- `seed.sql`: un paciente NN.

### Archivos afectados
- `db_scripts/schema.sql`, `db_scripts/seed.sql`, `models/persona.py`, `dao/paciente_dao.py`
- `tests/test_persona.py`, `tests/test_paciente_dao.py`, `tests/test_estados_vs_bd.py`, `docs/`

### Motivo
A emergencia llegan pacientes inconscientes o sin papeles que hay que atender (y registrar su triaje) antes de saber quiénes son. Hasta ahora el registro exigía documento, nombres y fecha de nacimiento reales.

### Impacto
- Pruebas: 497 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), junto con el cambio de `tipo_documento`. Se cargaron `schema.sql` y `seed.sql` y se usaron los DAO reales. 33 comprobaciones pasaron:
  - Esquema: 22 tablas; los códigos de `tipo_documento` coinciden con `TipoDocumento`; `codigo` distingue mayúsculas (`'dni'` no encuentra `'DNI'`); el seed tiene 5 pacientes, 1 de ellos NN.
  - Restricciones: tipo + número repetido → 1062; el mismo número con otro tipo se acepta; tipo sin número o número sin tipo → 3819 (`CH_paciente_documento`); varios NN a la vez se aceptan; tipo inexistente → 1452; empleado sin documento → 1048.
  - `PacienteDAO`: busca por DNI y por CE; el mismo número con otro tipo no encuentra a nadie; `buscar_por_id` devuelve un NN (confirma el `LEFT JOIN`); `crear` guarda el pasaporte normalizado y un duplicado lanza `RegistroDuplicadoError`; un NN se guarda con tipo y número `NULL` y conserva su edad estimada; `listar_no_identificados` lo incluye; `actualizar` no le pone documento.
  - `identificar`: con el documento de otro paciente → `RegistroDuplicadoError` y el NN queda igual; con un documento nuevo → `True`, se encuentra por documento con el mismo id y sale de la lista de NN; un segundo `identificar` con un objeto desactualizado → `False` y se conserva el primer documento.
  - `UsuarioDAO.autenticar`: con DNI encuentra al empleado (suma un intento fallido con clave incorrecta); con el mismo número y tipo CE no lo encuentra.
- El futuro controlador de pacientes debe ofrecer "registrar NN" y, más adelante, "identificar".

### Decisiones
- **Documento `NULL`, no un tipo "SIN DOCUMENTO":** un tipo falso obligaría a inventar un número único. Un `UNIQUE` de MySQL admite varios `NULL`, así que puede haber varios NN a la vez, y el `CHECK` impide un tipo sin número o al revés.
- **Fecha de nacimiento estimada en lugar de `NULL`:** la edad aproximada es útil en la atención y así `calcular_edad()` sigue funcionando para todos. Se guarda el 1 de enero de (año actual − edad), con lo que la edad calculada coincide con la estimada todo el año. No se añadió una columna "fecha estimada": mientras el paciente no esté identificado, sus datos se consideran provisionales.
- **Nombres "NN":** convención de los hospitales para pacientes sin nombre. La constante vive en `Paciente.NOMBRE_NO_IDENTIFICADO` y un test comprueba que el seed la use.
- **Identificar es una operación aparte y se hace una sola vez:** `actualizar` sigue sin tocar el documento. `Paciente.identificar` lanza `ReglaNegocioError` si ya está identificado y valida todo antes de modificar. En la BD, `WHERE num_documento IS NULL` impide sobrescribir el documento aunque dos usuarios identifiquen al mismo paciente a la vez.
- **Atributo de clase `_ADMITE_SIN_DOCUMENTO` en lugar de repetir la validación en `Empleado`:** por defecto toda persona exige documento; solo `Paciente` lo relaja.
- No se creó una subclase `PacienteNoIdentificado`: al identificarlo, el objeto tendría que cambiar de clase.

### Pendientes
- Si el documento del NN ya pertenece a otro paciente, `identificar` lanza `RegistroDuplicadoError`. Unir los dos registros queda para la Fase 4.
- Recrear `sigtac_db` con los scripts nuevos; actualizar `diagrama.png`.

---

## [2026-10-21] — Documento de identidad para personas extranjeras

### Cambio
- Nueva tabla de catálogo `tipo_documento` (DNI, CE, PAS, CPP). En `paciente` y `empleado`, la columna `dni` se reemplaza por `id_tipo_documento` (FK) + `num_documento`, con `UNIQUE (id_tipo_documento, num_documento)`. El esquema pasa a 22 tablas.
- Nuevo `models/documento.py`: `TipoDocumento` (`StrEnum`) y `DocumentoIdentidad` (objeto valor inmutable: tipo + número, con `__eq__`/`__hash__`).
- `Persona` y sus subclases reciben un `DocumentoIdentidad` en lugar de `dni: str` (propiedad `documento`). Se elimina `es_dni_valido`.
- `PacienteDAO.buscar_por_dni(dni)` pasa a `buscar_por_documento(documento)`; `crear` obtiene `id_tipo_documento` con una subconsulta por código.
- `UsuarioDAO.autenticar(tipo_documento, num_documento, password_plano)`: el login pide tipo y número; la sesión devuelve `tipo_documento` y `num_documento` en lugar de `dni`.
- `seed.sql`: catálogo de tipos y una paciente extranjera con carné de extranjería.

### Archivos afectados
- `db_scripts/schema.sql`, `db_scripts/seed.sql`, `models/documento.py` (nuevo), `models/persona.py`, `dao/paciente_dao.py`, `dao/usuario_dao.py`, comentarios en `dao/base_dao.py`, `models/excepciones.py` y `utils/security.py`
- `tests/test_documento.py` (nuevo, 53 pruebas), `tests/test_persona.py`, `tests/test_paciente_dao.py`, `tests/test_usuario_dao.py`, `tests/test_estados_vs_bd.py`
- `CLAUDE.md`, `docs/`

### Motivo
El sistema solo aceptaba DNI peruano (8 dígitos): un paciente o un empleado extranjero no se podía registrar (problema abierto 2 de `PROJECT_STATUS.md`). Un hospital debe atender a cualquier persona sin importar su nacionalidad.

### Impacto
- Pruebas: 466 pasan.
- Verificado en MySQL 8.0.46 junto con el cambio de pacientes NN (ver la entrada siguiente). `sigtac_db` necesita volver a crearse con `schema.sql` y `seed.sql` (borra los datos de desarrollo).
- Quien llame a `autenticar` o a `buscar_por_documento` (futuros `auth_controller` y vistas) debe enviar el tipo de documento: el formulario de login necesita un selector de tipo.

### Decisiones
- **Tipo + número juntos identifican a la persona:** el mismo número puede ser un DNI de una persona y el pasaporte de otra. Por eso el `UNIQUE` es compuesto.
- **Catálogo en lugar de `CHECK`:** añadir un tipo es un `INSERT`, no un cambio de esquema; sigue el patrón de `seguro` y `estado_cama`. Un test compara `TipoDocumento` con `seed.sql`.
- **El formato vive en un solo lugar (`DocumentoIdentidad`):** el DNI exige exactamente 8 dígitos; los documentos extranjeros aceptan de 6 a 12 letras o dígitos, porque su formato varía según el país y la fecha de emisión. No se verificó el formato oficial exacto de CE, pasaporte ni CPP.
- **Normalización en el objeto valor:** el número se guarda sin espacios en los extremos y en mayúsculas. Antes `Persona` rechazaba un DNI con espacios y `UsuarioDAO` lo limpiaba; ahora lo hace `DocumentoIdentidad` para todos.
- **Objeto en lugar de dos atributos sueltos:** `Persona` recibe un `DocumentoIdentidad` ya validado, así el tipo y el número no pueden quedar desincronizados. `__repr__` oculta el número para que no termine en un log.
- El documento sigue sin poder actualizarse (`PacienteDAO.actualizar`), igual que antes el DNI.

### Pendientes
- Recrear `sigtac_db` con los scripts nuevos.
- Actualizar `db_scripts/diagrama.png`.
- Pacientes sin identificar (NN): requieren otra decisión (sin documento, nombre ni fecha de nacimiento conocidos).

---

## [2026-10-13] — `CamaDAO` (lectura) y reglas nuevas en `CLAUDE.md`

### Cambio
- Nuevo `dao/cama_dao.py` (`CamaDAO`, hereda de `BaseDAO`): `buscar_por_id`, `buscar_por_codigo`, `listar_activas` y `listar_disponibles`. Una fábrica (`CLASES_POR_TIPO`) convierte cada fila en su subclase de `Cama`.
- Nuevo `tests/test_cama_dao.py` (25 pruebas) y una prueba en `tests/test_estados_vs_bd.py` que compara la fábrica con los tipos de `seed.sql`.
- `CLAUDE.md`: no añadir `Co-Authored-By` de Claude; mensajes con cuerpo con `git commit -F` en PowerShell; no reescribir commits ya subidos; método `_a_<entidad>` en cada DAO; `FOUND_ROWS`; no escribir operaciones multi-paso antes de decidir las transacciones; la verificación en base temporal requiere cuenta de administrador.

### Archivos afectados
- `dao/cama_dao.py` (nuevo), `tests/test_cama_dao.py` (nuevo), `tests/test_estados_vs_bd.py`, `CLAUDE.md`, `docs/`

### Motivo
Siguiente DAO del plan. Las reglas de `CLAUDE.md` recogen lo aprendido el 2026-10-12/13: un commit con varios `-m` quedó con el título roto en PowerShell y tuvo que reescribirse, y el usuario pidió que Claude no figure como coautor.

### Impacto
- Pruebas: 419 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada). 11 comprobaciones pasaron:
  - La fábrica crea la subclase correcta con los nombres reales de `tipo_cama`, y todos los estados de la BD existen en `EstadoCama`.
  - `listar_activas` devuelve las 8 camas del seed; `listar_disponibles`, solo las 4 `DISPONIBLE`, ordenadas por área y código.
  - Compatibilidad por polimorfismo sobre datos reales: nivel 1 → Trauma Shock y UCI; nivel 4 → solo Observación.
  - Búsqueda por código e id con JOIN a área y estado; inexistente → `None`.
  - Una cama dada de baja no aparece en búsquedas, en el mapa ni entre las disponibles.

### Decisiones
- **Solo lectura por ahora.** Cambiar el estado de una cama son dos escrituras (`UPDATE cama` + `INSERT historial_estado_cama`); sin transacción, un fallo en la segunda dejaría un cambio sin historial. Se implementará después de decidir las transacciones (problema 4).
- **La fábrica usa el nombre del tipo, no el id:** `nombre_tipo_cama` es `UNIQUE` y los ids dependen del orden de inserción. Un tipo sin clase lanza `ValueError`, y una prueba asegura que la fábrica y `seed.sql` coincidan.
- **La compatibilidad no se filtra en el DAO ni en SQL:** `listar_disponibles` filtra solo por estado; el controlador aplica `cama.es_compatible(nivel)`. Así la regla tiene un solo dueño (el modelo) y el DAO no contiene reglas de negocio.
- **Solo camas activas:** el modelo `Cama` no tiene `activo`, así que una cama dada de baja (`estado_registro = FALSE`) no se devuelve en ninguna consulta.
- El estado se filtra con un parámetro tomado del Enum (`EstadoCama.DISPONIBLE.value`), no escrito en el SQL.
- Las partes fijas del SQL (`_SELECT`, `_ORDEN`) se concatenan entre sí; los valores siempre van como parámetros.
- `listar_activas` (todas las camas en cualquier estado) se añade para el futuro mapa de camas.

### Pendientes
- `cambiar_estado` + `historial_estado_cama`, tras la decisión sobre transacciones.

---

## [2026-10-12] — `PacienteDAO` y `FOUND_ROWS` en la conexión

### Cambio
- Nuevo `dao/paciente_dao.py` (`PacienteDAO`, hereda de `BaseDAO`): `buscar_por_id`, `buscar_por_dni`, `crear`, `actualizar` y `anular`.
- `dao/db_connection.py`: la conexión se abre con `ClientFlag.FOUND_ROWS`.
- Nuevo `tests/test_paciente_dao.py` (28 pruebas) y 1 prueba nueva en `tests/test_db_connection.py`.

### Archivos afectados
- `dao/paciente_dao.py` (nuevo), `dao/db_connection.py`, `tests/test_paciente_dao.py` (nuevo), `tests/test_db_connection.py`, `docs/`

### Motivo
Siguiente paso de la Fase 3. `FOUND_ROWS` es necesario para `actualizar`: sin él, MySQL devuelve en `rowcount` las filas *modificadas*, y guardar un paciente sin cambios daría 0, que el DAO confundiría con "no existe". Con `FOUND_ROWS`, `rowcount` cuenta las filas *encontradas*.

### Impacto
- Pruebas: 393 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), creada con una cuenta de administrador porque `sigtac_app` no puede crear bases. 15 comprobaciones pasaron:
  - Búsqueda por DNI e id, JOIN a `seguro`, `fecha_nac` como `date`, DNI inexistente → `None`.
  - `crear` devuelve el id; DNI duplicado → `RegistroDuplicadoError` (1062); seguro inexistente → `PersistenciaError` (1452), no duplicado.
  - `actualizar` sin cambios devuelve `True` (confirma `FOUND_ROWS`); con cambios los guarda; id inexistente → `False`.
  - `anular`: el paciente sigue existiendo con `activo=False`; anular dos veces devuelve `True`; id inexistente → `False`.
  - Los mensajes de error registrados solo muestran el `errno`, sin el DNI.

### Decisiones
- **El DNI no se actualiza:** `actualizar` solo modifica nombres, apellidos, fecha de nacimiento, sexo y seguro. El DNI identifica a la persona; un DNI mal registrado se corrige anulando el registro y creando uno nuevo.
- **`buscar_por_dni` incluye a los anulados:** el `UNIQUE` del DNI también los cubre, así que el controlador debe saber que el paciente existe (para reactivarlo) en lugar de intentar un `INSERT` que fallaría.
- `actualizar` y `anular` devuelven `False` si el id no existe; `anular` es idempotente (anular dos veces devuelve `True`).
- `crear` rechaza un paciente que ya tiene id o que está anulado (`ValueError`), sin consultar la BD.
- El DAO no repite validaciones: si una fila tiene datos inválidos, el constructor de `Paciente` lanza `ValueError`.
- Los logs solo registran `id_paciente`, nunca DNI ni nombres.

### Pendientes
- Reactivar un paciente anulado (`estado_registro = TRUE`): se añadirá cuando el controlador lo necesite.
- Búsqueda por nombre o listado: se añadirá cuando la vista lo necesite.

---

## [2026-10-12] — `BaseDAO` y política de errores de la capa DAO

### Cambio
- Nuevo `dao/base_dao.py`: clase `BaseDAO` con `_consultar_uno`, `_consultar_varios`, `_insertar` (devuelve el id generado) y `_ejecutar` (devuelve las filas afectadas). Pide la conexión, abre y cierra el cursor y traduce los errores de MySQL.
- `models/excepciones.py`: nuevas `PersistenciaError` y `RegistroDuplicadoError`. `ConexionBDError` pasa a derivar de `PersistenciaError`.
- `dao/usuario_dao.py`: `UsuarioDAO` hereda de `BaseDAO`; ya no maneja cursores. Su comportamiento no cambia (las 33 pruebas pasan sin modificar sus aserciones).
- Nuevo `tests/test_base_dao.py` (23 pruebas).

### Archivos afectados
- `dao/base_dao.py` (nuevo), `dao/usuario_dao.py`, `models/excepciones.py`, `tests/test_base_dao.py` (nuevo), `tests/test_usuario_dao.py`, `CLAUDE.md`, `docs/`

### Motivo
Cada DAO repetía unas 15 líneas (conexión, cursor, `try/except`, cierre en `finally`). Con cinco DAO más, un error en una copia sería difícil de encontrar. Además, devolver `None` ante cualquier fallo, como hace el login, no sirve en el resto de DAO: el controlador no podría distinguir "el paciente no existe" de "MySQL está caído".

### Impacto
- Política de errores de los DAO (salvo `UsuarioDAO.autenticar`): `None` o lista vacía significan "no encontrado"; los fallos lanzan `PersistenciaError` o una subclase (`ConexionBDError`, `RegistroDuplicadoError` para el error 1062).
- Pruebas: 364 pasan. Las pruebas de `usuario_dao` reemplazan `ConexionBD` en `base_dao`, que es donde ahora se usa.

### Decisiones
- **Jerarquía:** `SigtacError → PersistenciaError → {ConexionBDError, RegistroDuplicadoError}`. Un controlador puede capturar todos los fallos de BD con una sola cláusula y, si quiere, tratar el duplicado aparte.
- **Sin `commit()`/`rollback()` en `BaseDAO`:** con `autocommit=True` no tienen efecto, y dentro de la futura transacción de asignar cama un `commit` por sentencia la rompería. Las transacciones se decidirán aparte (problema 4 de `PROJECT_STATUS.md`).
- **Los logs y mensajes no incluyen el texto de MySQL**, solo el código (`errno`): MySQL arma la consulta en el cliente y sus mensajes pueden traer los valores enviados (por ejemplo `Duplicate entry '12345678'`). El error original queda encadenado (`raise ... from e`) para depurar.
- Solo se traducen errores de `mysql.connector`; un error de programación (p. ej. `KeyError`) se propaga tal cual para no ocultarlo.
- `params` debe ser una tupla (`TypeError` si no): evita el error clásico de pasar `(valor)` en lugar de `(valor,)`.
- `BaseDAO` no es abstracta: no tiene métodos que las subclases deban implementar, solo métodos que heredan.

---

## [2026-10-12] — Script para crear el usuario de BD de la aplicación

### Cambio
- Nuevo `db_scripts/crear_usuario_app.sql`: crea `sigtac_app@localhost` con `SELECT, INSERT, UPDATE` sobre `sigtac_db.*` y muestra sus permisos. La clave va como marcador (`<una_clave_segura>`).
- `README.md` remite al script.

### Archivos afectados
- `db_scripts/crear_usuario_app.sql` (nuevo), `README.md`, `docs/`

### Motivo
El `.env` local usaba `root`. Con mínimo privilegio, un error de programación, una inyección SQL o un `.env` filtrado solo pueden leer y escribir datos de `sigtac_db`. No pueden borrar, alterar tablas ni tocar otras bases del servidor.

### Impacto
- Verificado en MySQL 8.0.46 con un usuario temporal (`sigtac_verif_tmp`, ya eliminado):
  - El script se ejecuta sin errores y se puede repetir.
  - `SHOW GRANTS` muestra solo `USAGE` global y `SELECT, INSERT, UPDATE` en `sigtac_db`.
  - El usuario puede leer `cama`; MySQL le deniega `DELETE`, `DROP`, `CREATE` y leer otra base (error 1142).
- `schema.sql`, `seed.sql` y las verificaciones con base temporal siguen necesitando una cuenta de administrador.

### Decisiones
- Sin `DELETE`: la BD hace cumplir la RN-11 (baja lógica) aunque un DAO intente borrar.
- `CREATE USER IF NOT EXISTS` + `ALTER USER`: el script se puede ejecutar de nuevo sin error y deja la clave indicada.
- La clave nunca se escribe en el archivo versionado.

---

## [2026-10-12] — Verificación en MySQL 8.0 real y CHECK de texto sensibles a mayúsculas

### Cambio
- `schema.sql`: las columnas `paciente.sexo` y `empleado.turno` usan ahora `COLLATE utf8mb4_bin`.
- Se cargaron `schema.sql` y `seed.sql` en una base temporal (`sigtac_scratch_tmp`, ya eliminada) en **MySQL 8.0.46** y se ejecutaron 32 comprobaciones; todas pasaron:
  - Carga de ambos scripts sin errores; 21 tablas.
  - Columnas nuevas de `empleado` con los datos del seed (área "Triaje", especialidades, turno `MAÑANA` con su acento intacto).
  - `CHECK` de `turno` y `sexo`: rechazan `MADRUGADA`, `mañana`, `MANANA`, `Mañana`, `noche`, `m`, `f` y `X`; aceptan `NOCHE` y `NULL`. La FK de `id_area` rechaza un área inexistente.
  - RN-10 (`CH_triaje_rn10`): rechaza la reclasificación sin justificación, con 9 caracteres y con solo espacios; acepta 10 caracteres.
  - RN-05 (columnas generadas con `UNIQUE`): rechaza una segunda asignación vigente de la misma cama o del mismo episodio; acepta una cama libre y una asignación ya liberada.
  - Los modelos aceptan los datos reales: los 3 pacientes y los 5 empleados con subclase se construyen sin errores desde las filas de la BD.
  - `UsuarioDAO.autenticar` contra la base real: login correcto, clave incorrecta, usuario desactivado y DNI inválido.

### Archivos afectados
- `db_scripts/schema.sql`, `docs/`

### Motivo
La primera ejecución de la verificación mostró que la BD **aceptaba `'mañana'`** aunque el `CHECK` solo permite `'MAÑANA'`. La *collation* de la base (`utf8mb4_0900_ai_ci`) no distingue acentos (`ai`) ni mayúsculas (`ci`), así que `IN ('MAÑANA', ...)` daba por iguales `'mañana'` y `'MANANA'`. Lo mismo ocurría con `sexo` (`'m'` pasaba como `'M'`). Python rechaza esas variantes, de modo que un dato así entraría en la BD y luego fallaría al reconstruir el objeto. Con `utf8mb4_bin`, la comparación es exacta, igual que en Python.

### Impacto
- Pruebas: 341 pasan. La verificación en BD se hizo con un script temporal (no versionado), según la regla de `CLAUDE.md`.
- `sigtac_db` **no se modificó**. Para aplicar los cambios del 2026-10-12 hay que volver a ejecutar `schema.sql` y `seed.sql` sobre ella (borra los datos de desarrollo).
- Queda cerrado el pendiente "Probar `schema.sql` y `seed.sql` en un MySQL 8.0 real".

### Decisiones
- La *collation* binaria se aplica **solo a las dos columnas** cuyo `CHECK` compara texto. El resto de la base conserva `utf8mb4_0900_ai_ci`: es lo deseable para las búsquedas (por ejemplo, encontrar "Pérez" al buscar "perez").
- **Corrección:** el CHANGELOG del 2026-10-11 dice que el servidor de desarrollo es MariaDB 11.8. En este equipo el servidor es MySQL 8.0.46 (servicio `MySQL80`). Las verificaciones anteriores probablemente se hicieron en otra máquina.

### Pendientes
- El `.env` local usa `root`. Sirvió para crear la base temporal, pero la aplicación debería usar un usuario con solo `SELECT, INSERT, UPDATE`.
- Convertir la verificación en pruebas de integración permanentes (opcionales, que se salten si no hay BD).

---

## [2026-10-12] — Alineación de `persona.py` con la BD y validaciones de entrada

### Cambio
**Modelos (`models/persona.py`)**
- `Paciente`:
  - Nuevo atributo `sexo` (`'M'` o `'F'`, igual que `CH_paciente_sexo`).
  - `seguro` (texto) se reemplaza por `id_seguro` (entero obligatorio, FK a `seguro`) y `nombre_seguro` (opcional, solo para mostrar; el DAO lo obtendrá con un JOIN).
  - `id_paciente` admite `None` para un paciente aún no guardado en la BD.
  - Nueva firma: `Paciente(id_paciente, dni, nombres, apellidos, fecha_nac, sexo, id_seguro, activo=True, nombre_seguro=None)`.
- `Empleado`: nuevo atributo `activo` y método `anular()` (espejo de `empleado.estado_registro`, RN-11), igual que `Paciente`. Las tres subclases reciben `activo=True` como último parámetro.
- Subclases: `Enfermero.area`, `Medico.especialidad` y `PersonalLimpieza.turno` ahora tienen `@property` y aparecen en `obtener_resumen()`.
- Validaciones nuevas (lanzan `ValueError`):
  - DNI de exactamente 8 dígitos (`[0-9]`, sin espacios).
  - `nombres`, `apellidos`, `cargo`, `area` y `especialidad` obligatorios y no vacíos; se guardan sin espacios en los extremos.
  - `fecha_nac` debe ser `date` (no `datetime` ni texto) y no puede ser futura.
  - Los ids son enteros positivos (o `None` si aún no se guardaron); se rechaza `bool`.
  - `activo` debe ser `bool`: el DAO debe convertir el 0/1 de MySQL.
  - `colegiatura` es opcional, pero si se envía no puede estar vacía.
  - `turno` debe ser `MAÑANA`, `TARDE` o `NOCHE`.
  - Los mensajes de error no incluyen el valor recibido, porque podría ser un dato personal y acabar en un log.
- Nueva función `es_dni_valido()` y constante `PATRON_DNI` en `models/persona.py`.

**DAO (`dao/usuario_dao.py`)**
- Usa `es_dni_valido()` de `models/persona.py` en lugar de su propio `PATRON_DNI`. El comportamiento no cambia.

**Base de datos**
- `schema.sql`, tabla `empleado`: nuevas columnas `id_area` (FK a `area`), `especialidad` y `turno`, todas `NULL`, y la restricción `CH_empleado_turno`.
- `seed.sql`: nueva área `(5, 'Triaje')`, sin camas. Los empleados tienen ahora área (enfermería), especialidad (médicos) o turno (limpieza).

**Pruebas**
- `tests/test_persona.py` reescrito: 29 → 185 pruebas. Cubre cada validación con valores límite (DNI de 7 y 9 dígitos, fecha de hoy frente a mañana, etc.), la baja lógica de `Empleado` y los atributos de las subclases.
- `tests/test_estados_vs_bd.py`: nueva prueba que compara `Paciente.SEXOS_VALIDOS` y `PersonalLimpieza.TURNOS_VALIDOS` con los `CHECK` de `schema.sql`.

### Archivos afectados
`models/persona.py`, `dao/usuario_dao.py`, `db_scripts/schema.sql`, `db_scripts/seed.sql`, `tests/test_persona.py`, `tests/test_estados_vs_bd.py`, `docs/`

### Motivo
Resolver los problemas abiertos 1 a 5 de `PROJECT_STATUS.md`. `paciente_dao.py` no podía insertar un `Paciente` (faltaba `sexo`, que es `NOT NULL`). Un futuro `EmpleadoDAO` no podía reconstruir el estado ni los datos propios de cada subclase. Y los objetos aceptaban datos que la BD rechazaría (o peor, que aceptaría siendo incorrectos).

### Eliminado
- `Paciente.seguro` (texto): reemplazado por `id_seguro` + `nombre_seguro`. La tabla guarda un id, y con solo el nombre el DAO tendría que buscar el id por texto en cada inserción.
- `PATRON_DNI` de `dao/usuario_dao.py`: movido a `models/persona.py`. Una regla, un dueño: si el formato del DNI cambia, se cambia en un solo lugar.
- Comentario incorrecto en `Enfermero.registrar_triaje()` ("cerrar el episodio", copiado de `Medico.dar_alta`).

### Impacto
- Pruebas: 341 pasan (antes 183).
- Hay que volver a ejecutar `schema.sql` y `seed.sql` en cada entorno de desarrollo (borra los datos).
- **El SQL no se verificó contra una BD real:** el usuario del `.env` fue rechazado por el servidor (`Access denied`). Solo se comprobó de forma estática que cada fila del `INSERT INTO empleado` tenga 11 valores para 11 columnas.
- Cualquier código que cree `Paciente` con el parámetro `seguro` debe cambiar a `id_seguro` (hoy solo las pruebas lo hacían).

### Decisiones
- **`area`, `especialidad` y `turno` se guardan en la tabla `empleado`** como columnas que admiten `NULL` (una sola tabla para toda la jerarquía), en lugar de crear una tabla por subclase. Es más simple para el alcance del curso. La desventaja: la BD no puede impedir que, por ejemplo, un operario de limpieza tenga especialidad, porque el tipo de empleado está en otra tabla (`cargo.tipo`). Esa coherencia la garantizan las clases Python, que exigen cada atributo a su subclase.
- **`area` es una FK** a la tabla `area` ya existente, no texto libre. Se añadió el área "Triaje" porque el único enfermero del seed tiene rol "Enfermero de Triaje" y no existía un área que la representara.
- **`especialidad` es texto libre** (`VARCHAR(100)`), no un catálogo. Se solapa en parte con `cargo` ("Médico Internista" / "Medicina Interna"), pero son conceptos distintos (el puesto frente al título profesional), con el mismo criterio con el que se separaron `rol` y `cargo`. Si se necesitan reportes por especialidad, conviene convertirla en catálogo.
- **`turno` usa `CHECK`** con tres valores, como `sexo`; Python y la BD se mantienen sincronizados con una prueba.
- **DNI solo de 8 dígitos**, como ya exigía el login. La columna sigue siendo `VARCHAR(15)` y no se cambió.
- `activo` exige `bool` estricto, para que un 0/1 mal convertido en un DAO se detecte de inmediato.

### Pendientes
- Verificar `schema.sql` y `seed.sql` en una base temporal con un usuario administrador.
- Pacientes sin DNI peruano (extranjeros) o sin identificar (inconscientes): hoy no se pueden registrar. Requiere una decisión del equipo.
- Actualizar `db_scripts/diagrama.png` con las columnas nuevas de `empleado`.
- El `.env` local usa `root`. `CLAUDE.md` indica usar un usuario con solo `SELECT, INSERT, UPDATE`.

---

## [2026-10-12] — Cierre de la Fase 2: pruebas de `persona.py` y documentación al día

### Cambio
- Nuevo `tests/test_persona.py` con 29 pruebas de `Persona`, `Paciente`, `Empleado`, `Enfermero`, `Medico` y `PersonalLimpieza`:
  - `Persona` y `Empleado` son abstractas (no se pueden instanciar).
  - Propiedades de solo lectura.
  - `Paciente`: activo por defecto, reconstrucción como inactivo desde la BD y `anular()` como baja lógica (RN-11).
  - `calcular_edad()` con valores límite: el día antes, el día del cumpleaños y el día después; recién nacido; nacido el 29 de febrero en años bisiestos y no bisiestos. La fecha de hoy se fija con `monkeypatch` para que la prueba no dependa del día en que se ejecute.
  - `obtener_resumen()` polimórfico, con y sin colegiatura.
  - `tiene_permiso()` de cada subclase, incluidos módulos no permitidos y vacíos.
- `PROJECT_STATUS.md` reescrito con el estado real: Fase 2 completada, Fase 3 en curso, problemas abiertos y próximo trabajo.
- `DEVELOPMENT_PLAN.md`: casillas alineadas con el código (`Empleado` estaba sin marcar aunque existía; faltaban `estados.py`, 6 excepciones, `logging_config.py` y los archivos de pruebas; `controllers/` y `views/` figuraban como creados y no existen).

### Archivos afectados
- `tests/test_persona.py` (nuevo)
- `docs/PROJECT_STATUS.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/CHANGELOG.md`

### Motivo
- `Paciente` y `Empleado` eran las únicas clases del dominio sin pruebas (pendiente registrado el 2026-10-11). `paciente_dao.py` construirá objetos `Paciente`, así que su comportamiento debía quedar fijado antes.
- `PROJECT_STATUS.md` llevaba fecha del 2026-10-05 y no recogía los cambios del 2026-10-11. Como el proyecto lo usa como fuente de verdad del estado actual, estaba induciendo a error.

### Impacto
- Pruebas: 183 pasan (antes 154). No se modificó código de producción.
- La Fase 2 se da por cerrada.

### Decisiones
- **No se añadieron validaciones nuevas a `Persona`** (formato de DNI, fecha de nacimiento futura): ninguna regla del proyecto las define todavía. Se registran como problema abierto en `PROJECT_STATUS.md`, en lugar de inventarlas o marcarlas como `xfail`.
- Las pruebas de `tiene_permiso()` fijan el comportamiento actual. Si en la Fase 4 los permisos pasan a depender solo de la tabla `rol`, habrá que actualizarlas.
- **Cambio de orden de los DAO:** `auditoria_dao.py` se adelanta antes que `triaje_dao.py` y `asignacion_dao.py`. Es de una sola tabla, no necesita transacciones y lo usarán todos los controladores. Los dos DAO de varios pasos esperan la decisión sobre transacciones (`ConexionBD` usa `autocommit=True`).

### Pendientes
Diferencias entre el código y la BD encontradas al escribir las pruebas (detalle en `PROJECT_STATUS.md`, "Problemas abiertos"):
- `Paciente` no tiene `sexo`, que es `NOT NULL` en la tabla `paciente`. **Bloquea `paciente_dao.py`.**
- `Paciente.seguro` es texto; la tabla guarda `id_seguro`.
- `Empleado` no refleja `estado_registro`.
- `Enfermero.area`, `Medico.especialidad` y `PersonalLimpieza.turno` no tienen columna en la BD ni `@property`.
- `Persona` no valida el DNI ni la fecha de nacimiento.

---

## [2026-10-11] — Entorno virtual recreado dentro del proyecto

### Cambio
Se eliminó y se recreó `.venv` con `python -m venv` e instalando `requirements-dev.txt`.

### Archivos afectados
- `.venv/` (no versionado), `CLAUDE.md`

### Motivo
El `.venv` original era una copia de otro entorno (`Proyectos Personales/.venv`) y su script `pip` seguía apuntando a esa carpeta: un `pip install` instalaba los paquetes fuera del proyecto. Los entornos virtuales guardan rutas absolutas y no deben copiarse ni moverse.

### Impacto
- `pip` y `python` del `.venv` apuntan ahora a `SIGTAC/.venv`. Verificado con `pip --version` y 154 pruebas en verde.
- El entorno antiguo de la carpeta padre no se tocó.
- PyCharm: el intérprete configurado en `.idea/misc.xml` sigue apuntando al entorno de la carpeta padre; hay que seleccionar `SIGTAC/.venv` en la configuración del proyecto (archivo local no versionado).

### Pendientes
- Cada integrante del equipo debe crear su propio `.venv` (no se comparte).

---

## [2026-10-11] — Cierre de la revisión: reglas en modelos y BD, bloqueo de cuentas y dependencias (paso 7)

### Cambio
**Modelos**
- `EpisodioEmergencia.asignar_cama()` exige estado "en espera de cama" y un triaje activo (RN-01); `dar_alta()` exige estar en atención con cama. Ambos lanzan `ReglaNegocioError`.
- `obtener_triaje_actual()` ignora los triajes anulados, usa `max()` y su tipo de retorno es `Triaje | None`.
- Nuevo `models/estados.py` con `EstadoCama` y `EstadoEpisodio` (`StrEnum`). `Cama` y `EpisodioEmergencia` validan el estado recibido (un estado inexistente lanza `ValueError`). Las constantes `ESTADO_*` se conservan como alias. El Enum de episodio incluye `REFERIDO` y `FUGADO`, que ya existían en la BD.
- `SignosVitales` rechaza valores fisiológicamente imposibles (rangos amplios en `RANGOS`).
- `Sintoma` es ahora un `dataclass(frozen=True)` realmente inmutable y rechaza pesos negativos.
- Añadidos `__init__.py` en `dao/`, `models/` y `utils/`.

**Base de datos** (`schema.sql`, `seed.sql`)
- `usuario`: nuevas columnas `intentos_fallidos` y `bloqueado_hasta`.
- `triaje`: `CHECK` que hace cumplir la RN-10 en la BD (si el nivel final difiere del sugerido, la justificación es obligatoria y de al menos 10 caracteres).
- `asignacion_cama`: columnas generadas `cama_vigente` y `episodio_vigente` con índice `UNIQUE`: la BD impide dos asignaciones vigentes de la misma cama (RN-05) o del mismo episodio.
- Todas las columnas `estado_registro` son `NOT NULL`; `bitacora_auditoria.detalles_json` pasa a tipo `JSON`.
- Aviso visible al inicio de ambos scripts: destruyen datos, solo para desarrollo.

**Autenticación** (`UsuarioDAO`)
- Bloqueo temporal: 5 intentos fallidos consecutivos bloquean la cuenta 15 minutos (`MAX_INTENTOS_FALLIDOS`, `MINUTOS_BLOQUEO`). Un bloqueo se rechaza aunque la clave sea correcta, usa el señuelo y no suma intentos. Un login correcto reinicia el contador; un bloqueo vencido se reinicia antes de evaluar.
- El contador se incrementa dentro de la propia BD (operación atómica).

**Dependencias**: versiones fijadas con `==` en `requirements.txt` y `requirements-dev.txt`.

### Archivos afectados
`models/estados.py` (nuevo), `models/cama.py`, `models/triaje.py`, `dao/usuario_dao.py`, `db_scripts/schema.sql`, `db_scripts/seed.sql`, `requirements.txt`, `requirements-dev.txt`, `README.md`, `tests/` y los `__init__.py`.

### Motivo
Cerrar los hallazgos pendientes de la revisión: reglas de negocio que solo existían como comentarios, estados como texto repetido sin validar, ausencia de límite de intentos de login y dependencias sin versión fija.

### Impacto
- Es necesario volver a ejecutar `schema.sql` y `seed.sql` (borra los datos de desarrollo).
- El usuario de BD de la aplicación necesita `UPDATE` sobre `usuario` (ya contemplado en el README).
- Un servicio que llame a `asignar_cama()` o `dar_alta()` debe capturar `ReglaNegocioError`.
- Pruebas: 154 pasan. Se eliminaron los dos `xfail` porque las brechas están corregidas, y un nuevo test compara los Enum con los catálogos de `seed.sql`.
- Las restricciones de la BD y el bloqueo se verificaron contra una base temporal real (ya eliminada): datos inválidos rechazados, válidos aceptados, y simulación de un ataque de 5 claves erróneas.

### Decisiones
- **Servidor de desarrollo:** es MariaDB 11.8.8, no MySQL 8. **Corrección:** el README afirmaba que el proyecto no funciona en MariaDB; era una suposición no verificada y es falsa para esta versión. Las verificaciones de los pasos 5 a 7 se hicieron en MariaDB; el objetivo documentado sigue siendo MySQL 8.0.
- Los `CHECK` de `triaje` obligaron a cambiar las FK de `id_nivel` e `id_nivel_sugerido` a `ON UPDATE RESTRICT` (una columna usada en un `CHECK` no admite `CASCADE`). Es inocuo: los ids de catálogo no cambian.
- Criterio de excepciones: `ValueError` para datos de entrada inválidos (fuera de rango, formato) y excepciones de `SigtacError` para reglas de negocio violadas.
- El bloqueo es temporal (15 min) y no permanente, para que un atacante no pueda dejar fuera a un empleado de forma indefinida. Aun así permite un bloqueo temporal intencional; es el costo conocido de esta medida.
- Los rangos de `SignosVitales` son amplios y solo descartan errores de digitación; no definen qué es clínicamente normal.
- Las versiones se fijaron a las instaladas en desarrollo. `customtkinter`, `reportlab` y `matplotlib` aún no se usan en el código, por lo que no se han probado.

### Pendientes (fuera del alcance de la revisión)
- Permisos duplicados entre la tabla `rol` y `tiene_permiso` en las clases: se decidirá en la Fase 4 (controladores).
- Actualizar `db_scripts/diagrama.png` (faltan `fecha_nac`, `intentos_fallidos`, `bloqueado_hasta` y las columnas generadas).
- Probar `schema.sql` y `seed.sql` en un MySQL 8.0 real (aquí solo había MariaDB).
- Pruebas de integración contra una BD real y pruebas de `Paciente`/`Empleado`.
- Recrear el `.venv` dentro del proyecto (su `pip` apunta aún a otro entorno; usar `python -m pip`).
- Datos reales de integrantes en `seed.sql`: decisión del equipo.

---

## [2026-10-11] — Pruebas automáticas con pytest (revisión de seguridad, paso 6)

### Cambio
- Nueva carpeta `tests/` con 127 pruebas (125 pasan, 2 `xfail`):
  - `test_cama.py`: máquina de estados de `Cama` (RN-05, RN-07, RN-08) y `es_compatible` por tipo.
  - `test_triaje.py`: `Triaje`, `SignosVitales` y `EpisodioEmergencia` (RN-01, RN-09, RN-10, RN-11).
  - `test_estrategias.py`: umbrales y límites de `ReglaManchester` y `ReglaMINSA`, y signos vitales obligatorios.
  - `test_security.py`: bcrypt (formato, sal, hash inválido).
  - `test_db_connection.py`: variables obligatorias, `autocommit`, Singleton y reconexión.
  - `test_usuario_dao.py`: login, cuenta desactivada, señuelo, validación de DNI, consulta parametrizada, cierre del cursor y logs sin datos personales.
- Nuevos `pytest.ini` y `requirements-dev.txt` (dependencias de desarrollo separadas de las de la aplicación).
- Sección "Pruebas" en el README.

### Archivos afectados
- `tests/` (nuevo), `pytest.ini` (nuevo), `requirements-dev.txt` (nuevo), `README.md`

### Motivo
Hasta ahora las comprobaciones de los pasos 1 a 5 eran scripts desechables. Con pruebas permanentes, cualquier cambio que reintroduzca uno de los fallos corregidos se detecta de inmediato.

### Impacto
- Las pruebas no necesitan MySQL ni `.env`: la conexión se simula.
- Verificado reintroduciendo a propósito 4 fallos (`\d` en el DNI, `sato2` por defecto, falta del señuelo y `autocommit` desactivado): las pruebas detectaron los 4.

### Decisiones
- Las dos brechas conocidas están como `xfail(strict=True)`: `asignar_cama` sin triaje (RN-01) y `obtener_triaje_actual` que no ignora triajes anulados. Cuando se corrijan, la prueba fallará y obligará a quitar la marca.
- No se miden tiempos en las pruebas (serían inestables): se comprueba que se invoque el señuelo.
- Pendiente de cobertura: pruebas de integración contra MySQL real (por ahora solo se verificó a mano).

### Pendientes
- Corregir las dos brechas marcadas como `xfail` en `models/triaje.py`.
- Pruebas de `Paciente`, `Empleado` y sus subclases.

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
