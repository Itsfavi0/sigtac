# SIGTAC — Changelog

> Registro cronológico de cambios, decisiones y avances relevantes del proyecto.
> No registrar cada modificación mínima de código; registrar cambios que afecten arquitectura, funcionalidad, reglas de negocio, estructura o dirección del desarrollo.

---

## [2026-10-26] — Pendientes de la Fase 4: referir, fuga, fuera de servicio, edición de pacientes y administración

### Cambio
- **Cierre de episodios** (`models/triaje.py`): `EpisodioEmergencia.referir()` (solo desde EN ESPERA DE CAMA o EN ATENCIÓN: exige triaje) y `registrar_fuga()` (desde cualquier estado abierto). Ambos, y `dar_alta`, cierran con `_cerrar`, que guarda la fecha de egreso.
  - `EpisodioDAO.cambiar_estado` pone `fecha_alta = NOW()` en cualquier cierre (alta, referido o fuga), no solo en el alta.
  - `ReporteDAO.promedio_estancia_min` ahora filtra por ALTA MÉDICA.
  - `CamaController.referir` y `registrar_fuga` liberan la cama si el paciente tenía una: si solo estaba reservada vuelve a DISPONIBLE y la asignación se anula; si estaba ocupada pasa a EN LIMPIEZA con su solicitud (RN-07).
- **Mantenimiento de camas** (`CamaController`): `poner_fuera_de_servicio(id_cama, motivo)` y `volver_a_servicio(id_cama)`.
  - El motivo es obligatorio (máx. 200 caracteres) y queda en la bitácora.
  - Se rechaza una cama con paciente asignado, con limpieza pendiente o que ya está fuera de servicio.
  - Nuevo `SolicitudLimpiezaDAO.buscar_pendiente_por_cama`.
- **Pacientes** (`models/persona.py`):
  - `Paciente.actualizar_datos(...)` devuelve los campos que cambiaron. Un NN conserva "NN" como nombre hasta que se identifica.
  - `Paciente.reactivar()`: un NN dado de baja no se reactiva.
  - En `PacienteController`:
    - `actualizar_datos`: permiso PACIENTES; bloquea la fila primero. La auditoría guarda solo los nombres de los campos.
    - `dar_de_baja` y `reactivar`: permiso ADMINISTRACION. No se da de baja a un paciente con un episodio abierto.
  - `PacienteDAO.actualizar` solo modifica pacientes activos.
  - Nuevos `PacienteDAO.reactivar` (UPDATE condicional) y la acción de auditoría `REACTIVAR`.
- **Administración** (nuevos `models/usuario.py` y `controllers/admin_controller.py`, permiso ADMINISTRACION):
  - `CuentaUsuario`, con las transiciones `activar`, `desactivar`, `cambiar_rol` y `desbloquear`.
  - `validar_clave_nueva`: mínimo 8 caracteres, letras y números, máximo 72 bytes y sin espacios en los extremos.
  - `AdminController` ofrece: `listar_cuentas`, `listar_empleados_sin_cuenta`, `listar_roles`, `crear_cuenta`, `cambiar_rol`, `desactivar`, `activar`, `restablecer_clave`, `desbloquear`, `bitacora(desde, hasta, tabla, id_usuario, limite)` e `historial_de_registro`.
  - `UsuarioDAO` gana los métodos de administración de cuentas: `listar_cuentas`, `buscar_cuenta`, `crear_cuenta`, `cambiar_rol` y `cambiar_activo` (los dos últimos con UPDATE condicional), `restablecer_clave` y `desbloquear`.
  - `AuditoriaDAO.listar` consulta la bitácora por período, con filtros opcionales y un tope de 1000 filas.
- `BaseDAO._validar_periodo` (antes solo en `ReporteDAO`): ahora también lo usa `AuditoriaDAO`.
- `scripts/verificar_controladores.py` se amplía con todos estos flujos. Incluye un **login real** con una cuenta creada por el administrador: cambio de rol, desactivación, bloqueo por 5 intentos, desbloqueo y clave restablecida.
- Pruebas:
  - nuevas: `tests/test_admin_controller.py` (86) y `tests/test_usuario.py` (27);
  - ampliadas: `test_cama_controller` (92), `test_paciente_controller` (78), `test_usuario_dao`, `test_auditoria_dao`, `test_paciente_dao`, `test_asignacion_dao`, `test_episodio_dao`, `test_reporte_dao`, `test_triaje` y `test_persona`.

### Archivos afectados
- `models/triaje.py`, `models/persona.py`, `models/auditoria.py`, `models/usuario.py` (nuevo)
- `dao/base_dao.py`, `dao/episodio_dao.py`, `dao/reporte_dao.py`, `dao/paciente_dao.py`, `dao/solicitud_limpieza_dao.py`, `dao/usuario_dao.py`, `dao/auditoria_dao.py`
- `controllers/cama_controller.py`, `controllers/paciente_controller.py`, `controllers/admin_controller.py` (nuevo)
- `scripts/verificar_controladores.py`, `tests/`, `docs/`, `CLAUDE.md`

### Motivo
Eran los "pendientes conocidos" de la Fase 4:
- operaciones sin controlador (camas fuera de servicio, editar y reactivar pacientes, cuentas y bitácora);
- estados del catálogo sin transición en el modelo (REFERIDO y FUGADO).

Las vistas de la Fase 6 los necesitan.

### Impacto
- Pruebas: **1349 pasan** (antes 1104).
- `promedio_estancia_min` ya no cuenta los referidos ni las fugas, aunque todos tienen fecha de egreso.
- Sin cambios de esquema (`accion` de la bitácora es `VARCHAR` sin `CHECK`): no hace falta recrear `sigtac_db`.
- Verificación ampliada en MySQL (`scripts/verificar_controladores.py`, ejecutada por el usuario con su cuenta de administrador): **todas las comprobaciones correctas**, incluido el login real con la cuenta creada por el administrador.

### Decisiones
- **`fecha_alta` es la fecha de egreso:** se guarda en todo cierre, porque el episodio terminó igual. Por eso el indicador de estancia filtra por ALTA MÉDICA: si no, una fuga a los pocos minutos acortaría el promedio.
- **Referir exige triaje y la fuga no:** referir es una decisión clínica sobre un paciente evaluado; irse se puede antes de que lo vean.
- **Referir y fuga con permiso GESTION_CAMAS (médico y jefe de guardia):** liberan una cama, igual que el alta. Queda por validar con el equipo si el enfermero también debe registrar una fuga desde la sala de espera.
- **Fuera de servicio con GESTION_CAMAS:**
  - El modelo admite decretarlo desde cualquier estado (no cambió).
  - El controlador lo impide si hay una asignación vigente o una limpieza pendiente; si no, quedarían abiertas sobre una cama fuera de servicio.
  - Para una cama con un paciente dentro falta el **traslado de cama**.
- **Baja y reactivación de pacientes con ADMINISTRACION:** son correcciones de registros (un duplicado, una baja por error), no parte de la atención. Editar los datos sí es de PACIENTES.
- **Un administrador no se desactiva ni cambia su propio rol:** así el sistema no se queda sin administrador por un clic equivocado. Lo hace otro administrador.
- **Política de claves en el modelo, hash en el controlador:** el DAO rechaza cualquier valor que no sea un hash bcrypt, como defensa por si se le pasara la clave en texto plano por error. Ni la clave ni el hash van a la bitácora ni a los logs.
- **72 bytes como máximo:** bcrypt ignora (y bcrypt 5 rechaza) lo que pase de 72 bytes. Se mide en bytes UTF-8: "ñ" ocupa 2.

### Pendientes
- Traslado de cama, para un paciente cuya cama falla.
- Validar con el equipo los permisos nuevos: fuga con GESTION_CAMAS, y baja y reactivación con ADMINISTRACION.
- Una cuenta desactivada que ya tenía la sesión abierta en otra PC la conserva hasta cerrarla: la sesión vive en la aplicación.
- Que cada usuario pueda cambiar su propia clave (hoy solo la restablece el administrador).
- Actualizar `db_scripts/diagrama.png`.

---

## [2026-10-22] — Revisión de la Fase 4 antes de fusionar con `main`

### Cambio
- `models/triaje.py`: `Triaje` (nivel sugerido) y `Triaje.reclasificar` (nivel nuevo) solo aceptan enteros del 1 al 5 (`_es_nivel_valido`). Antes `True` pasaba como nivel 1 y `2.0` como nivel 2, porque `True in range(1, 6)` y `2.0 in range(1, 6)` son verdaderos en Python.
- `scripts/verificar_controladores.py`: se quita un import sin usar y se comenta por qué el `DROP DATABASE` arma el nombre con una constante (un nombre de base no puede ir como parámetro).
- Pruebas: `test_el_nivel_debe_ser_un_entero` en `tests/test_triaje.py` (5 casos).

### Archivos afectados
- `models/triaje.py`, `scripts/verificar_controladores.py`, `tests/test_triaje.py`, `docs/`

### Motivo
Revisión de la rama `feat/fase4-controladores` antes de fusionarla. Con los controladores, el nivel final llega desde la vista (`TriajeController.registrar(..., nivel_final=...)`): un valor mal convertido (un checkbox, un `float`) no debe aceptarse como nivel.

### Impacto
- Pruebas: 1104 pasan. Verificación en MySQL repetida: 56 de 56.
- Sin cambios de comportamiento para niveles enteros válidos.

### Decisiones
- **La regla queda en el modelo:** es la validación del nivel de triaje; el controlador no la repite.

### Pendientes
- Ninguno nuevo.

---

## [2026-10-22] — Verificación de la Fase 4 en MySQL 8.0.46 (`scripts/verificar_controladores.py`)

### Cambio
- Nuevo `scripts/verificar_controladores.py`: crea `sigtac_scratch_tmp`, carga `schema.sql` y `seed.sql`, recorre el flujo completo a través de los cinco controladores (admisión → triaje → cola → asignación → ocupación → alta → limpieza → reportes) y elimina la base al terminar. Es el primer script de verificación que queda en el repositorio (los anteriores eran temporales).
- `CLAUDE.md`: comando del script y reglas de los controladores (patrón de cada operación, `bloquear`, pruebas con `CapaDatosFalsa`).

### Archivos afectados
- `scripts/verificar_controladores.py` (nuevo), `CLAUDE.md`, `docs/`

### Motivo
Las pruebas de los controladores simulan la BD; faltaba comprobar contra MySQL real el SQL nuevo (historial en bloque, `FOR UPDATE`, consultas de reportes) y el flujo de punta a punta.

### Impacto
- **56 de 56 comprobaciones correctas** en MySQL 8.0.46, entre ellas:
  - Dos PCs admiten a la misma paciente a la vez: la segunda espera el bloqueo (1,5 s) y luego rechaza el segundo episodio; queda uno solo.
  - Otra PC da de alta un episodio mientras se registra su triaje: el triaje espera el bloqueo, ve el alta y no guarda nada.
  - El historial cargado en bloque (`listar_por_estado`) es igual al de `buscar_por_id`.
  - Asignar a una cama incompatible o ya reservada se rechaza y no cambia el episodio; dar de alta una cama solo reservada se deshace por completo.
  - Ciclo completo de la cama con historial, asignación, solicitud de limpieza y bitácora; cancelar una reserva no pasa por limpieza.
  - Reportes: ocupación, pacientes en emergencia, ingresos, triajes por nivel, reclasificación y tiempos promedio coinciden con consultas directas (p. ej. estancia 30 min = (45 + 15) / 2).
- No se tocó `sigtac_db`.

### Decisiones
- **El script queda en `scripts/`, no en `tests/`:** necesita MySQL y una cuenta de administrador; `python -m pytest` debe seguir funcionando sin BD.
- **Clave por variable de entorno o `getpass`:** `SIGTAC_ADMIN_PWD` (solo para ese proceso) permite ejecutarlo sin escribir la clave; nunca se guarda en un archivo.
- **Concurrencia con una segunda conexión real en otro hilo:** la única forma de comprobar que `FOR UPDATE` hace esperar y que, después de esperar, se ven los datos confirmados por la otra PC.

### Pendientes
- Convertirlo en pruebas de integración de pytest (marcadas y omitidas si no hay BD) cuando se acuerde cómo dar la cuenta de administrador en el equipo.

---

## [2026-10-22] — Fase 4: `reporte_dao.py` y `reporte_controller.py` (indicadores)

### Cambio
- Nuevo `dao/reporte_dao.py` (`ReporteDAO`, solo lectura): `contar_camas_por_estado`, `contar_episodios_por_estado`, `contar_ingresos`, `contar_triajes_por_nivel`, `contar_reclasificaciones`, `promedio_espera_triaje_min`, `promedio_espera_cama_min` y `promedio_estancia_min`. Los períodos son `[desde, hasta)` con `datetime`.
- Nuevo `controllers/reporte_controller.py` con `ReporteController(sesion)` (permiso `REPORTES`):
  - `estado_actual() -> EstadoGuardia`: camas por estado, porcentaje de ocupación y pacientes en emergencia por estado.
  - `indicadores(desde, hasta) -> IndicadoresPeriodo`: ingresos, triajes por nivel, porcentaje de reclasificación y tiempos promedio (puerta-triaje, espera de cama y estancia), entre dos días incluidos.
- Pruebas: `tests/test_reporte_dao.py` (44) y `tests/test_reporte_controller.py` (17).

### Archivos afectados
- `dao/reporte_dao.py`, `controllers/reporte_controller.py` (nuevos), `tests/test_reporte_dao.py`, `tests/test_reporte_controller.py` (nuevos), `docs/`

### Motivo
Último controlador del plan de la Fase 4 ("consultar datos, preparar AVG/COUNT y KPIs, entregar datos a las vistas").

### Impacto
- Pruebas: 1099 pasan.
- Las vistas reciben objetos inmutables (`dataclass(frozen=True)`) con los números ya calculados.

### Decisiones
- **SQL en el DAO, porcentajes en el controlador:** contar y promediar se hace en MySQL (no se traen miles de filas a Python); el plan pedía que el controlador "preparara AVG/COUNT", pero el SQL solo puede vivir en un DAO.
- **LEFT JOIN desde los catálogos:** un estado o nivel sin filas aparece con 0, así la vista siempre recibe todas las categorías.
- **Período `[desde, hasta)`:** el controlador recibe días (`date`) y consulta desde las 00:00 del primero hasta las 00:00 del día siguiente al último; así el último día entra completo sin depender de `23:59:59`.
- **Ocupación = (reservadas + ocupadas) / (camas activas − fuera de servicio):** una cama reservada ya está comprometida; una en limpieza no está en uso pero sí en servicio.
- **Pacientes en emergencia:** se descartan los estados cerrados con `EpisodioEmergencia.ESTADOS_CERRADOS` del modelo (la regla no se repite en el controlador).
- **Lecturas en una transacción:** todas las cifras de un reporte salen de la misma foto de la BD.
- **Las reservas canceladas no cuentan** en la espera de cama (`asignacion_cama.estado_registro = FALSE`).

### Pendientes
- Exportar los indicadores a PDF (`utils/pdf_generator.py`, Fase 5).
- Indicador de pacientes atendidos dentro del tiempo máximo de su nivel (`nivel_triaje.tiempo_max_min`).

---

## [2026-10-22] — Fase 4: `cama_controller.py` (ciclo de la cama)

### Cambio
- Nuevo `controllers/cama_controller.py` con `CamaController(sesion)`:
  - `VER_CAMAS`: `mapa_camas()`, `cola_de_espera()` (episodios EN ESPERA DE CAMA por prioridad).
  - `GESTION_CAMAS`: `camas_compatibles(id_episodio)`, `asignar(id_episodio, id_cama)`, `ocupar(id_cama)`, `cancelar_asignacion(id_episodio)`, `dar_alta(id_episodio)`.
  - `LIMPIEZA`: `solicitudes_limpieza()`, `confirmar_limpieza(id_solicitud)`.
- Pruebas: `tests/test_cama_controller.py` (57).

### Archivos afectados
- `controllers/cama_controller.py` (nuevo), `tests/test_cama_controller.py` (nuevo), `docs/`

### Motivo
Es el núcleo del sistema (asignación de camas): une los modelos `Cama` y `EpisodioEmergencia` con los DAO de cama, episodio, asignación, limpieza y auditoría en transacciones atómicas.

### Impacto
- Pruebas: 1038 pasan.
- Flujos y lo que guarda cada uno (todo en una transacción, con auditoría):

  | Operación | Episodio | Cama | Además |
  |---|---|---|---|
  | `asignar` | EN ESPERA DE CAMA → EN ATENCIÓN | DISPONIBLE → RESERVADA | `AsignacionDAO.crear` |
  | `ocupar` | — | RESERVADA → OCUPADA | exige asignación vigente |
  | `cancelar_asignacion` | EN ATENCIÓN → EN ESPERA DE CAMA | RESERVADA → DISPONIBLE | `AsignacionDAO.anular` |
  | `dar_alta` | EN ATENCIÓN → ALTA MÉDICA | OCUPADA → EN LIMPIEZA | `AsignacionDAO.liberar` + `SolicitudLimpiezaDAO.crear` |
  | `confirmar_limpieza` | — | EN LIMPIEZA → DISPONIBLE | `SolicitudLimpiezaDAO.atender` |

### Decisiones
- **Compatibilidad en el controlador, con la regla del modelo:** `asignar` rechaza una cama que no sea `es_compatible` con el nivel actual; el controlador solo la aplica, la regla sigue siendo de cada subclase de `Cama`.
- **Primero RN-01, después la compatibilidad:** `episodio.asignar_cama()` va antes del chequeo de compatibilidad para que, sin triaje, el error diga "RN-01" y no "cama incompatible".
- **Concurrencia por `UPDATE` condicional:** si otra PC tomó la cama (o cambió el episodio) entre la lectura y la escritura, `cambiar_estado` lanza la excepción y se deshace todo, también el cambio del episodio que ya se había guardado. No hace falta bloquear filas porque estas operaciones siempre cambian el estado.
- **`ocupar` exige una asignación vigente:** el modelo permite ocupar desde DISPONIBLE, pero sin asignación no se sabría qué paciente está en la cama.
- **No se da de alta una cama solo reservada:** primero se ocupa (el paciente llegó) o se cancela; así una reserva que no se usó no pasa por limpieza.
- **Auditoría por operación:** asignación (`INSERT`/`ANULAR` en `asignacion_cama`), ocupación (`UPDATE` en `cama`), alta (`UPDATE` en `episodio_emergencia`, con la solicitud de limpieza) y limpieza (`UPDATE` en `solicitud_limpieza`). El historial de estados de la cama ya lo guarda `CamaDAO`, pero no dice quién: la bitácora sí.

### Pendientes
- Fuera de servicio / volver a servicio (el modelo lo tiene; falta decidir quién puede y qué pasa con un paciente en una cama que falla).
- Transiciones a REFERIDO y FUGADO (siguen pendientes en el modelo).

---

## [2026-10-22] — Fase 4: `triaje_controller.py` y colas de espera

### Cambio
- Nuevo `controllers/triaje_controller.py` con `TriajeController(sesion, estrategia=None)` (permiso `TRIAJE`; la estrategia por defecto es `ReglaManchester`):
  - `listar_sintomas()`, `cola_de_triaje()` (episodios EN ESPERA DE TRIAJE por orden de llegada).
  - `sugerir(signos, ids_sintomas) -> Sugerencia(nivel, protocolo)`: lo que propone la estrategia, sin guardar.
  - `registrar(id_episodio, signos, ids_sintomas, nivel_final=None, justificacion=None) -> id_triaje`: signos vitales + triaje + síntomas, cambio de estado del primer triaje y auditoría, en una transacción.
- Nuevo `controllers/colas.py`: `EntradaCola(posicion, episodio, paciente)` y `armar_cola(estado)`, que comparten el triaje y la gestión de camas.
- Pruebas: `tests/test_triaje_controller.py` (41) y `tests/test_colas.py` (3).

### Archivos afectados
- `controllers/triaje_controller.py`, `controllers/colas.py` (nuevos), `tests/test_triaje_controller.py`, `tests/test_colas.py` (nuevos), `docs/`

### Motivo
Siguiente paso del flujo: el episodio abierto en admisión necesita su triaje (RN-01) para entrar en la cola de cama.

### Impacto
- Pruebas: 981 pasan.
- La vista recibe la sugerencia y el protocolo para mostrarlos, y luego llama a `registrar` con lo que el profesional decidió.

### Decisiones
- **El nivel sugerido se recalcula al registrar:** no se recibe de la vista. Así el "sugerido" de la BD es siempre lo que dijo el algoritmo y no puede alterarse para esquivar la justificación de RN-10.
- **Reclasificar solo si el nivel cambia:** si `nivel_final` es igual al sugerido (o `None`) se confirma la sugerencia y no se guarda justificación. Resuelve en el controlador el pendiente "reclasificar al mismo nivel": el controlador nunca llama a `reclasificar` con el mismo nivel (el modelo aún lo admite).
- **Bloqueo del episodio:** un segundo triaje no cambia el estado, así que no hay `UPDATE` condicional que detecte a otra PC; `EpisodioDAO.bloquear` impide que lo den de alta a mitad del registro.
- **Errores de formulario antes de la BD:** signo faltante → `SignosVitalesIncompletosError` (el mismo que usan las estrategias); signo desconocido, texto en vez de número o síntoma repetido o inexistente → `ValueError`.
- **La auditoría guarda niveles y protocolo, no la justificación:** es texto clínico (ya queda en `triaje.justificacion`).
- **Colas en un módulo aparte:** la cola de triaje y la de cama son la misma operación con distinto estado; `armar_cola` lee episodios y pacientes en una sola transacción (misma foto de la BD) y ordena con `ordenar_por_prioridad` del modelo. El permiso lo comprueba cada controlador.

### Pendientes
- Mostrar en la cola si se superó el tiempo máximo de espera del nivel (`nivel_triaje.tiempo_max_min`).

---

## [2026-10-22] — Fase 4: `paciente_controller.py` (admisión y pacientes NN)

### Cambio
- Nuevo `controllers/paciente_controller.py` con `PacienteController(sesion)`, todo con el permiso `PACIENTES`:
  - Consultas: `listar_seguros()`, `buscar_por_documento(tipo, numero)`, `listar_no_identificados()`.
  - `registrar(...)`: paciente con documento; rechaza un documento ya registrado (activo o dado de baja).
  - `registrar_no_identificado(sexo, edad_estimada, id_seguro)`: paciente NN.
  - `abrir_episodio(id_paciente, motivo_consulta)`: el episodio empieza EN ESPERA DE TRIAJE; un paciente no puede tener dos episodios abiertos.
  - `identificar(id_paciente, ...)`: si el documento ya es de otro paciente, pide fusionar en lugar de duplicar a la persona.
  - `fusionar(id_nn, id_destino)`: no fusiona si los dos tienen un episodio abierto.
  - Cada escritura va con su auditoría (`INSERT`, `IDENTIFICAR`, `FUSIONAR`) dentro de la misma transacción.
- `tests/conftest.py` (nuevo): `CapaDatosFalsa` (reemplaza los DAO y `transaccion()` de un controlador y anota el orden de las llamadas) y la fábrica `sesion_de(rol)`.
- Pruebas: `tests/test_paciente_controller.py` (54).

### Archivos afectados
- `controllers/paciente_controller.py` (nuevo), `tests/conftest.py` (nuevo), `tests/test_paciente_controller.py` (nuevo), `docs/`

### Motivo
Sin admisión no hay episodio, y sin episodio no hay triaje ni cama. Los pacientes NN ya estaban resueltos en modelos y DAO; faltaba quien orquestara las reglas con permisos, transacción y auditoría.

### Impacto
- Pruebas: 937 pasan.
- Patrón de todos los controladores: `exigir_permiso` → validar datos con el modelo (sin tocar la BD) → `with transaccion():` leer, aplicar la regla del modelo, guardar y auditar.

### Decisiones
- **Leer dentro de la transacción:** los datos se cargan en la misma transacción que los guarda; así ninguna operación trabaja con un objeto que quedó viejo tras un fallo o tras el cambio de otra PC.
- **Validar antes de abrir la transacción:** un dato inválido (`ValueError`) no llega a la BD.
- **Un episodio abierto por paciente:** la persona sigue en emergencia; abrir otro duplicaría su cola y su cama. La fila del paciente se bloquea (`PacienteDAO.bloquear`) para que dos PCs no lo admitan a la vez. No hay restricción en la BD (no es fácil expresarla con `UNIQUE`); queda en el controlador.
- **Documento existente:** se avisa con `ReglaNegocioError` antes de insertar (mensaje claro para la vista); el `UNIQUE` sigue respaldando la regla si dos PCs registran a la vez (`RegistroDuplicadoError`, se deshace todo).
- **Identificar con un documento ajeno:** se rechaza y se indica fusionar; identificar duplicaría a la persona (y el `UNIQUE` lo impediría con un error menos claro).
- **Auditoría sin datos personales:** solo ids (`{"id_destino": 1, "episodios_movidos": 1}`).
- **Pruebas con un registro de llamadas:** `CapaDatosFalsa` permite comprobar el orden exacto (`inicio` → escrituras → auditoría → `commit`) y que ante un error haya `rollback` sin auditoría.

### Pendientes
- Reactivar un paciente dado de baja (hoy solo se informa; no hay método).
- Editar los datos de un paciente identificado (`PacienteDAO.actualizar` existe; falta decidir quién puede y si se audita con `UPDATE`).

---

## [2026-10-22] — Base para los controladores: colas, historial en bloque y bloqueo de filas

### Cambio
- `models/triaje.py`:
  - `EpisodioEmergencia.nivel_actual`: nivel final del triaje vigente (o `None`).
  - `ordenar_por_prioridad(episodios)`: orden de la cola de espera (nivel más urgente primero; a igual nivel, el que llegó antes; sin triaje, al final por llegada).
  - `SignosVitales` rechaza valores que no sean números (`ValueError`), p. ej. el texto `"120"` de un formulario o `True`.
- `dao/filtros_episodio.py` (nuevo): lista blanca de condiciones SQL fijas (`estado`, `paciente`) para cargar varios episodios a la vez.
- `TriajeDAO.listar_historial(filtro, valor)`: triajes con síntomas y signos vitales de muchos episodios en 3 consultas fijas.
- `EpisodioDAO.listar_por_estado(estado)` y `listar_por_paciente(id_paciente)`: episodios con su historial completo (4 consultas, no 3 por episodio); `EpisodioDAO.bloquear(id_episodio)`.
- `PacienteDAO.listar_seguros()`, `listar_por_estado_de_episodio(estado)` (id_episodio → Paciente, para mostrar nombres en una cola) y `bloquear(id_paciente)`.
- `SolicitudLimpiezaDAO.buscar_por_id(id_solicitud)`.
- `BaseDAO._bloquear(sql, params)`: `SELECT ... FOR UPDATE`; lanza `RuntimeError` fuera de `transaccion()`.

### Archivos afectados
- `models/triaje.py`, `dao/filtros_episodio.py` (nuevo), `dao/base_dao.py`, `dao/triaje_dao.py`, `dao/episodio_dao.py`, `dao/paciente_dao.py`, `dao/solicitud_limpieza_dao.py`
- `tests/test_triaje.py`, `tests/test_triaje_dao.py`, `tests/test_episodio_dao.py`, `tests/test_paciente_dao.py`, `tests/test_asignacion_dao.py`

### Motivo
Los controladores de la Fase 4 necesitaban: la cola de espera (RN-01: solo con triaje; prioridad por nivel), saber si un paciente ya tiene un episodio abierto, y evitar que dos PCs pisen la misma operación cuando no hay un cambio de estado que sirva de `UPDATE` condicional (p. ej. un segundo triaje mientras otra PC da de alta).

### Impacto
- Pruebas: 883 pasan tras este cambio. SQL nuevo pendiente de verificar en base temporal (se verifica junto con los controladores, ver la entrada de la verificación).

### Decisiones
- **Historial en bloque, no N+1:** cargar 20 episodios de la cola con `buscar_por_id` serían 60 consultas; con `listar_historial` son 3, filtrando por el mismo criterio que la lista de episodios (JOIN con `episodio_emergencia`).
- **Filtros como lista blanca:** el criterio (`estado` o `paciente`) elige un fragmento SQL fijo; el valor viaja siempre como parámetro. Se evitó generar `IN (%s, %s, ...)` dinámico.
- **La prioridad de la cola es del modelo:** `ordenar_por_prioridad` usa `obtener_triaje_actual`; repetir esa regla en SQL (último triaje activo por episodio) la duplicaría.
- **`SELECT ... FOR UPDATE` en una consulta propia y sin JOIN:** bloquear con el `_SELECT` de paciente también bloquearía las filas de `seguro` y `tipo_documento` y pondría en fila a todas las admisiones con el mismo seguro. `FOR UPDATE OF p` lo evitaría, pero MariaDB (usada en desarrollo) no lo admite.
- **El bloqueo va primero en la transacción:** en REPEATABLE READ la foto de la BD se toma en la primera lectura normal; si el bloqueo va antes, las lecturas siguientes ven lo que otra PC confirmó mientras se esperaba.
- **`_bloquear` exige transacción:** con autocommit el bloqueo se libera al instante y no protegería nada; es un error de programación (`RuntimeError`).
- **`SignosVitales` valida el tipo:** antes un texto llegaba a la comparación de rangos y lanzaba `TypeError` (que no es `ValueError` y la vista no capturaría).

### Pendientes
- Verificar el SQL nuevo y los bloqueos en una base temporal.

---

## [2026-10-21] — Fase 4: `auth_controller.py` (sesión y permisos)

### Cambio
- Nueva carpeta `controllers/` con `auth_controller.py`:
  - `Sesion`: el usuario que inició sesión (`id_usuario`, `id_empleado`, `nombre_rol`, `nombres`, `apellidos`, `cargo`). Datos de solo lectura, `puede(permiso)` para las vistas y `cerrar()` para invalidarla.
  - `exigir_permiso(sesion, permiso)`: punto único donde los controladores comprueban un permiso; lanza `UsuarioSinPermisoError` si no hay sesión, si está cerrada o si el rol no tiene el permiso. Devuelve la sesión (para usar su `id_usuario` en la auditoría).
  - `AuthController`: `iniciar_sesion(tipo_documento, num_documento, password)`, `cerrar_sesion()`, `exigir_sesion()`, `sesion` y `autenticado`.
- `models/excepciones.py`: nueva `AutenticacionError` (login fallido, siempre con el mismo mensaje).
- Pruebas: nuevo `tests/test_auth_controller.py` (73), con `UsuarioDAO.autenticar` simulado.

### Archivos afectados
- `controllers/__init__.py` y `controllers/auth_controller.py` (nuevos), `models/excepciones.py`
- `tests/test_auth_controller.py` (nuevo)
- `CLAUDE.md`, `docs/`

### Motivo
Primer paso de la Fase 4: sin sesión no se pueden aplicar los permisos ni saber quién hizo cada operación (auditoría). Los demás controladores dependen de este.

### Impacto
- Pruebas: 848 pasan. Sin cambios en la BD ni en los DAO (no requiere verificación en base temporal).
- Los próximos controladores se crean con la sesión (`TriajeController(sesion)`) y empiezan cada operación con `exigir_permiso(self._sesion, Permiso.X)`.

### Decisiones
- **Sesión inyectada, no global:** cada controlador recibe la `Sesion` al crearse. Una variable global obligaría a las pruebas a modificar estado compartido; así, una prueba crea una sesión de cualquier rol en una línea.
- **Cerrar sesión invalida el objeto:** como los controladores guardan la sesión que recibieron, `cerrar_sesion()` marca esa misma `Sesion` como cerrada; cualquier controlador que aún la tenga deja de poder operar (`exigir_permiso` falla).
- **Un nuevo login cierra antes la sesión anterior:** si el intento falla, no queda nadie conectado (evita que una persona opere con la sesión de otra).
- **Login fallido = excepción con mensaje genérico:** `AutenticacionError` (subclase de `SigtacError`, como el resto de errores que la vista muestra). El mensaje no dice si falló el documento, la clave o el bloqueo, igual que `UsuarioDAO.autenticar`, que devuelve `None` sin revelar la causa.
- **La sesión guarda lo mínimo:** ni clave, ni hash, ni número de documento; el `repr` muestra solo `id_usuario` y rol (puede terminar en un log).
- **Rol desconocido:** el usuario inicia sesión pero no tiene ningún permiso (denegar por defecto, como `tiene_permiso`).
- **Permiso mal escrito:** `exigir_permiso` lo valida antes que la sesión y lanza `ValueError` (error de programación), haya sesión o no.
- **Login y logout no van a la bitácora:** `bitacora_auditoria` registra cambios sobre tablas (`tabla` + `id_registro`); el inicio y el fallo de sesión ya quedan en el log de `UsuarioDAO.autenticar` (sin documentos ni nombres).

### Pendientes
- `paciente_controller.py`, `triaje_controller.py`, `cama_controller.py` y `reporte_controller.py` (en ese orden).
- Antes de `cama_controller`: un método de `EpisodioDAO` para listar la cola de espera. Antes de `reporte_controller`: `dao/reporte_dao.py` con las consultas AVG/COUNT.

---

## [2026-10-21] — Permisos por rol (`models/permisos.py`)

### Cambio
- Nuevo `models/permisos.py`: `Rol` (`StrEnum` con los 5 roles de la tabla `rol`), `Permiso` (`StrEnum` con los módulos del sistema), la matriz `PERMISOS_POR_ROL` (`frozenset` por rol) y `tiene_permiso(rol, permiso)`.
- `models/persona.py`: se quita `tiene_permiso()` de `Empleado` (era abstracto) y de `Enfermero`, `Medico` y `PersonalLimpieza`. `Empleado` deja de ser abstracta y puede representar al personal sin profesión específica (p. ej. el administrador).
- Pruebas: nuevo `tests/test_permisos.py` (52); en `tests/test_persona.py` se reemplazan las pruebas de `tiene_permiso()` por subclase y la de `Empleado` abstracto; `tests/test_estados_vs_bd.py` compara `Rol` con la tabla `rol` de `seed.sql`.
- `CLAUDE.md`: regla de permisos en los controladores.

### Archivos afectados
- `models/permisos.py` (nuevo), `models/persona.py`
- `tests/test_permisos.py` (nuevo), `tests/test_persona.py`, `tests/test_estados_vs_bd.py`
- `CLAUDE.md`, `docs/`

### Motivo
Era el último problema abierto antes de la Fase 4: los permisos existían en dos lugares (tabla `rol` y `tiene_permiso()` en cada subclase) y no coincidían. Los controladores necesitan una sola fuente para aplicar los permisos.

### Impacto
- Pruebas: 775 pasan. Sin cambios en la BD (no requiere verificación en base temporal); los nombres de `Rol` se comparan con `seed.sql`.
- Matriz aplicada (pendiente de validar con el equipo):

  | Permiso | Admin | Jefe de Guardia | Médico | Enfermero de Triaje | Limpieza |
  |---|:-:|:-:|:-:|:-:|:-:|
  | `PACIENTES` (registrar, identificar, fusionar NN) | | ✅ | ✅ | ✅ | |
  | `TRIAJE` (registrar, reclasificar) | | ✅ | ✅ | ✅ | |
  | `GESTION_CAMAS` (asignar, cancelar reserva, alta) | | ✅ | ✅ | | |
  | `VER_CAMAS` (mapa de camas) | ✅ | ✅ | ✅ | ✅ | ✅ |
  | `LIMPIEZA` (confirmar, RN-08) | | | | | ✅ |
  | `REPORTES` | ✅ | ✅ | | | |
  | `ADMINISTRACION` (usuarios y auditoría) | ✅ | | | | |

- Cambios respecto a `tiene_permiso()` anterior: el enfermero ya no gestiona camas (asignar es decisión médica) y desaparece `historias_clinicas`, que no es un módulo del alcance.

### Decisiones
- **El permiso depende del rol, no de la profesión:** el proyecto separó `rol` de `cargo` porque "el cargo laboral y los permisos del software son conceptos distintos"; `tiene_permiso()` en las subclases volvía a atar el permiso a la profesión. Además, el administrador y el jefe de guardia no tenían subclase, y un mismo médico puede tener roles distintos.
- **Matriz en Python, no tabla `rol_permiso`:** los permisos casi no cambian; en Python es un archivo, sin SQL ni pantalla de edición, y se prueba sin MySQL. Si más adelante se pide editarlos en vivo, se migra a una tabla sin tocar los controladores (siguen llamando a `tiene_permiso`).
- **Denegar por defecto:** un rol desconocido no tiene ningún permiso (distingue mayúsculas y tildes, como el nombre en la BD). Un permiso desconocido sí es un error de programación (`ValueError`).
- **El modelo responde, el controlador lanza:** `tiene_permiso` devuelve `True`/`False`; `UsuarioSinPermisoError` la lanza el controlador, como indica `DEVELOPMENT_PLAN.md`.
- **`Empleado` instanciable:** sin `tiene_permiso` abstracto ya no hay razón para impedirlo, y así el personal administrativo tiene una clase. Las subclases conservan lo propio de la profesión (área, especialidad, turno).
- **Matriz duplicada a propósito en la prueba:** `test_permisos.py` escribe la matriz esperada aparte; un cambio accidental en `PERMISOS_POR_ROL` hace fallar la prueba.

### Pendientes
- Validar la matriz con el equipo (o con el documento Word del proyecto, que manda si define permisos).
- Aplicar los permisos en los controladores de la Fase 4.

---

## [2026-10-21] — Fusión de pacientes NN, cancelación de reservas y episodios cerrados

### Cambio
- **Fusión de un paciente NN con uno ya registrado:**
  - `Paciente.fusionar_en(destino)` valida la regla (NN sin identificar y activo; destino identificado y activo; distintos) y anula el NN en memoria.
  - `PacienteDAO.fusionar(nn, destino)`, en una transacción: comprueba que el destino siga activo e identificado, anula el NN (`UPDATE` condicional) y pasa sus episodios al destino. Devuelve cuántos episodios movió.
  - `AccionAuditoria.FUSIONAR`.
  - `Paciente.identificar` rechaza un NN anulado, y `PacienteDAO.identificar` exige además `estado_registro = TRUE`.
- **Cancelar una reserva:**
  - `Cama.cancelar_reserva()` (RESERVADA → DISPONIBLE, sin limpieza).
  - `EpisodioEmergencia.cancelar_asignacion()` (EN ATENCIÓN → EN ESPERA DE CAMA).
  - `AsignacionDAO.anular(id_asignacion)`: baja lógica (`estado_registro = FALSE`), sin fecha de liberación.
- **Episodios cerrados:**
  - `EpisodioEmergencia.cerrado` (ALTA, REFERIDO, FUGADO o anulado); `agregar_triaje` y `agregar_signos_vitales` lanzan `ReglaNegocioError` en un episodio cerrado.
  - El constructor de `EpisodioEmergencia` recibe `triajes` y `signos_vitales` para reconstruirlo desde la BD; `EpisodioDAO.buscar_por_id` los pasa ahí en lugar de usar `agregar_triaje`.
- Pruebas: 41 nuevas o ajustadas en `test_persona.py`, `test_triaje.py`, `test_cama.py`, `test_paciente_dao.py`, `test_episodio_dao.py` y `test_asignacion_dao.py`.

### Archivos afectados
- `models/persona.py`, `models/triaje.py`, `models/cama.py`, `models/auditoria.py`
- `dao/paciente_dao.py`, `dao/episodio_dao.py`, `dao/asignacion_dao.py`
- `tests/test_persona.py`, `tests/test_triaje.py`, `tests/test_cama.py`, `tests/test_paciente_dao.py`, `tests/test_episodio_dao.py`, `tests/test_asignacion_dao.py`, `docs/`

### Motivo
Tres decisiones pendientes que afectan a los flujos que orquestarán los controladores de la Fase 4. Resolverlas antes evita que el controlador tenga que improvisar reglas que pertenecen al modelo.

### Impacto
- Pruebas: 725 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), con los DAO reales en transacciones como las de los futuros controladores. 22 comprobaciones pasaron:
  - Fusión: un NN con un episodio triado resulta ser Rosa (DNI del seed); el episodio, con su triaje, pasa a ella; el NN queda anulado y sin documento (no se borra), sale de la lista de no identificados y la fusión queda auditada; los datos de Rosa no cambian. Fusionarlo otra vez con datos viejos falla; identificar en la BD al NN ya fusionado devuelve `False`; fusionar con un destino anulado en la BD lanza `ReglaNegocioError` y deshace la anulación del NN.
  - Cancelar una reserva: el episodio vuelve a EN ESPERA DE CAMA y la cama a DISPONIBLE sin solicitud de limpieza; la asignación queda anulada sin fecha de liberación; el historial registra RESERVADA y DISPONIBLE; el episodio puede recibir otra cama; anular otra vez falla; una cama OCUPADA no se puede cancelar.
  - Episodio cerrado: un episodio dado de alta se carga con su historial (con la versión anterior, `buscar_por_id` habría fallado al aplicar la nueva regla) y registrar un triaje en él lanza `ReglaNegocioError` sin guardar nada.

### Decisiones
- **Fusionar en lugar de identificar:** si el documento del NN ya pertenece a otro paciente, identificarlo duplicaría la persona. Los episodios pasan al paciente real y el NN se anula (RN-11): queda como rastro, y la auditoría `FUSIONAR` registra a quién se unió. Los datos provisionales del NN (nombres "NN", edad estimada) se descartan.
- **El destino se comprueba dentro de la transacción** con un `SELECT` antes de anular el NN. No se usó `SELECT ... FOR UPDATE`: el margen para que otro usuario anule al destino justo en ese instante es mínimo y el resultado sería un episodio de un paciente anulado, recuperable.
- **Reserva cancelada = asignación anulada, no liberada:** `fecha_liberacion` significa "se usó y se dio de alta"; `estado_registro = FALSE` significa "no llegó a usarse". Los reportes (p. ej. estancia media) podrán distinguirlas. La cama no pasa por limpieza porque nunca se ocupó; una cama OCUPADA debe salir por el alta (RN-07).
- **Reconstruir ≠ registrar:** el historial de un episodio leído de la BD se pasa al constructor, sin aplicar las reglas de un triaje nuevo. Así un episodio cerrado tiene historial y se conserva el estado guardado.
- **Episodio cerrado incluye REFERIDO y FUGADO / ABANDONO** aunque el modelo aún no tenga esas transiciones: existen en el catálogo y un episodio en esos estados tampoco debe recibir triajes.

### Pendientes
- Transiciones a REFERIDO y FUGADO / ABANDONO (el modelo no las tiene).
- Decidir si `Triaje.reclasificar` al mismo nivel sugerido debe rechazarse.
- Permisos por rol antes de los controladores.

---

## [2026-10-21] — `AsignacionDAO` y `SolicitudLimpiezaDAO` (cierre de la Fase 3)

### Cambio
- Nuevo `models/asignacion.py`: `AsignacionCama` y `SolicitudLimpieza`, registros inmutables (`dataclass(frozen=True)`) con `vigente` / `pendiente`. Validan las mismas fechas que `CH_asignacion_fechas` y `CH_limpieza_fechas`, y que una solicitud atendida indique el empleado.
- Nuevo `dao/asignacion_dao.py` (`AsignacionDAO`): `crear`, `buscar_vigente_por_episodio`, `buscar_vigente_por_cama` y `liberar` (`UPDATE` condicional).
- Nuevo `dao/solicitud_limpieza_dao.py` (`SolicitudLimpiezaDAO`): `crear`, `listar_pendientes` (con el código de la cama) y `atender` (`UPDATE` condicional).
- Pruebas: `tests/test_asignacion.py` (10) y `tests/test_asignacion_dao.py` (26), nuevos.

### Archivos afectados
- `models/asignacion.py` (nuevo), `dao/asignacion_dao.py` (nuevo), `dao/solicitud_limpieza_dao.py` (nuevo)
- `tests/test_asignacion.py` (nuevo), `tests/test_asignacion_dao.py` (nuevo), `docs/`

### Motivo
Último DAO de la Fase 3. Con él se cierra el ciclo de una cama (RN-05, RN-07, RN-08) y `cama_controller` (Fase 4) tiene todo lo que necesita para asignar, dar de alta y confirmar la limpieza.

### Impacto
- Pruebas: 684 pasan. **Fase 3 completada.**
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), con funciones que imitan los futuros controladores (cada operación en una transacción con auditoría) y una segunda conexión como "otra PC". 24 comprobaciones pasaron:
  - Seed: TRA-01 tiene la asignación vigente del episodio 1; una cama libre no tiene; la solicitud pendiente es la de UCI-02.
  - Asignar (episodio 2, nivel 2): las camas compatibles son OBS-01, OBS-02 y UCI-01 (TRA-02 no); el episodio pasa a EN ATENCIÓN, UCI-01 a RESERVADA, la asignación queda vigente para ambos y auditada.
  - Conflictos: otra PC que asigna la misma cama con datos viejos recibe `CamaNoDisponibleError` y el cambio de estado de su episodio se deshace; asignar otra cama al mismo episodio con datos viejos lanza `ReglaNegocioError` y la otra cama sigue DISPONIBLE; una segunda asignación vigente de TRA-01 la rechaza el `UNIQUE` de la BD (`RegistroDuplicadoError`, RN-05).
  - Ocupar y dar de alta (RN-07): UCI-01 OCUPADA → EN LIMPIEZA (no DISPONIBLE), episodio en ALTA MÉDICA, asignación liberada con fecha de MySQL y una solicitud de limpieza pendiente. Repetir el alta con datos viejos falla y no crea otra solicitud.
  - Limpieza (RN-08): UCI-01 vuelve a DISPONIBLE, la solicitud queda atendida por el empleado 4 y sale de pendientes; atenderla otra vez lanza `ReglaNegocioError`. Historial de UCI-01: RESERVADA > OCUPADA > EN LIMPIEZA > DISPONIBLE.
  - Una cama liberada se puede volver a asignar: el `UNIQUE` solo cuenta las asignaciones vigentes.

### Decisiones
- **Dos DAO, uno por entidad:** la solicitud de limpieza es otra tabla con su propio ciclo (pendiente → atendida).
- **Cada método es una sola sentencia y no abre transacción propia:** el controlador los combina con `CamaDAO.cambiar_estado` y `EpisodioDAO.cambiar_estado` en `transaccion()`. Ver la tabla de flujos en `PROJECT_CONTEXT.md`.
- **`liberar` y `atender` son `UPDATE` condicionales** (`fecha_liberacion IS NULL`, `fecha_atencion IS NULL`); 0 filas → `ReglaNegocioError` para que se deshaga la transacción. Las fechas las pone MySQL.
- **El `UNIQUE` de `cama_vigente`/`episodio_vigente` es el respaldo de RN-05:** el conflicto normal lo detecta antes el `UPDATE` condicional de la cama; el `UNIQUE` lo detiene incluso si un controlador olvidara cambiar el estado. `crear` deja pasar el `RegistroDuplicadoError` sin traducirlo, porque no se sabe si el duplicado es de la cama o del episodio.
- **Una sola solicitud pendiente por cama** sin restricción en la BD: el `UPDATE` condicional de la cama deja pasar una sola transición a EN LIMPIEZA por ciclo, y la solicitud se crea en esa misma transacción.
- **Las asignaciones no se borran:** se liberan y quedan como historial; un test comprueba que el DAO no tiene métodos para borrar.
- **La compatibilidad cama–triaje no está en estos DAO:** la comprueba el controlador con `cama.es_compatible(nivel)`.

### Pendientes
- Cola de espera (episodios EN ESPERA DE CAMA por nivel y tiempo de espera): en `cama_controller`, Fase 4.
- Cancelar una reserva (cama RESERVADA cuyo paciente nunca llegó): el modelo no tiene esa transición; `cama.dar_alta()` exige OCUPADA. Decidirlo con el controlador.
- Permisos por rol ("Permisos duplicados" en `PROJECT_STATUS.md`) antes de los controladores.

---

## [2026-10-21] — `TriajeDAO` y `EpisodioDAO`

### Cambio
- Nuevo `dao/triaje_dao.py` (`TriajeDAO`): `listar_sintomas`, `registrar(id_episodio, signos, triaje)` (signos vitales + triaje + `triaje_sintoma` en una transacción), `listar_por_episodio` y `listar_signos_por_episodio`.
- Nuevo `dao/episodio_dao.py` (`EpisodioDAO`): `crear`, `buscar_por_id` (con su historial de signos y triajes) y `cambiar_estado` (`UPDATE` condicional).
- `models/triaje.py`:
  - `Triaje.sintomas` (tupla de solo lectura); `agregar_sintoma` rechaza lo que no es `Sintoma` y un síntoma repetido.
  - `EpisodioEmergencia`: propiedades `triajes` y `signos_vitales` (tuplas de solo lectura) y parámetros opcionales `fecha_ingreso`, `fecha_alta` y `activo` para reconstruirlo desde la BD.
  - `obtener_triaje_actual`: con la misma fecha y hora gana el último triaje agregado.
- `dao/base_dao.py`: nuevo `BaseDAO._validar_id`; `AuditoriaDAO` usaba una copia idéntica y ahora usa este.
- Pruebas: `tests/test_triaje_dao.py` (31, nuevo), `tests/test_episodio_dao.py` (26, nuevo), 10 nuevas en `tests/test_triaje.py` y 1 en `tests/test_estados_vs_bd.py` (los niveles 1–5 del seed coinciden con el modelo).
- `CLAUDE.md`: reglas de cambios de estado (el modelo decide, el DAO guarda), fechas puestas por MySQL y `_validar_id`.

### Archivos afectados
- `dao/triaje_dao.py` (nuevo), `dao/episodio_dao.py` (nuevo), `dao/base_dao.py`, `dao/auditoria_dao.py`, `models/triaje.py`
- `tests/test_triaje_dao.py` (nuevo), `tests/test_episodio_dao.py` (nuevo), `tests/test_triaje.py`, `tests/test_estados_vs_bd.py`
- `CLAUDE.md`, `docs/`

### Motivo
Siguiente paso de la Fase 3: el triaje es el centro del sistema y `triaje_controller` (Fase 4) lo necesita. Con `transaccion()` ya decidida, las varias escrituras de un triaje se pueden guardar de forma atómica.

### Impacto
- Pruebas: 648 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), recorriendo el flujo que hará `triaje_controller` (Manchester sugiere, la enfermera confirma, todo en una transacción con auditoría) y con una segunda conexión como "otra PC". 22 comprobaciones pasaron:
  - Catálogo: 10 síntomas ordenados, con peso como `float`. El episodio 2 del seed se reconstruye con su triaje reclasificado (sugerido 3, final 2, con justificación y síntoma); el episodio 1 conserva su estado EN ATENCIÓN; uno inexistente devuelve `None`.
  - Llegada y primer triaje (paciente extranjera): el episodio nace EN ESPERA DE TRIAJE con fecha de MySQL; se guardan signos, triaje (nivel final, sugerido, justificación, enfermera), 2 síntomas y la auditoría; el episodio pasa a EN ESPERA DE CAMA (RN-01).
  - Reevaluación (RN-09): un triaje nuevo, el anterior intacto; el triaje actual es la reevaluación y el estado no cambia.
  - Dos enfermeros triando el mismo episodio: el segundo recibe `ReglaNegocioError` y su triaje, signos y auditoría se deshacen.
  - Un síntoma inexistente (FK, 1452) deshace todo el triaje y el cambio de estado.
  - Asignar cama y dar de alta guardan los estados; la fecha de alta la pone MySQL (≥ ingreso). Un episodio con datos desactualizados lanza `ReglaNegocioError`.
- **No ejercitado contra MySQL:** guardar un triaje *nuevo* con nivel final distinto del sugerido. En la verificación, Manchester sugirió 1 y la "reclasificación" también fue a 1. Lo cubren las pruebas unitarias (parámetros del `INSERT`), la lectura del triaje reclasificado del seed y la verificación del `CHECK CH_triaje_rn10` del 2026-10-12.

### Decisiones
- **Dos DAO, uno por entidad:** el plan solo nombraba `triaje_dao.py`, pero el episodio es otra entidad (`CLAUDE.md`: un `*_dao.py` por entidad). `EpisodioDAO.buscar_por_id` usa `TriajeDAO` para cargar el historial, así el modelo puede aplicar RN-01 sobre datos reales.
- **`TriajeDAO` solo inserta y lee (RN-09):** una reevaluación es un triaje nuevo; un test comprueba que no hay métodos para modificar ni borrar.
- **`registrar` no cambia el estado del episodio:** la transición la decide el modelo (`agregar_triaje`) y la guarda `EpisodioDAO.cambiar_estado`, en la misma transacción del controlador. Si dos enfermeros trían a la vez, el `UPDATE` condicional del segundo encuentra 0 filas y deshace todo su triaje.
- **`EpisodioDAO.cambiar_estado` no abre transacción propia:** es una sola sentencia; dentro de la del controlador, su excepción deshace los pasos anteriores.
- **0 filas → `ReglaNegocioError`** (no `False`), por la misma razón que en `CamaDAO.cambiar_estado`.
- **Las fechas las pone MySQL** (triaje, signos, ingreso y alta): un solo reloj para todas las PCs, y `CH_episodio_fechas` se cumple aunque el reloj de una PC esté desfasado. La fecha de alta se pone al pasar a ALTA MÉDICA (`IF(%s, NOW(), fecha_alta)`).
- **Niveles por número:** `id_nivel` e `id_nivel_sugerido` se obtienen con subconsultas sobre `nivel_triaje.numero`, no por id. Un `id_nivel_sugerido` `NULL` se lee como "sin sugerencia" (sugerido = final).
- **Reconstrucción con los métodos del modelo:** `_a_triaje` usa `reclasificar()` y `anular()`, así las reglas (RN-10, RN-11) se aplican también a lo que llega de la BD.
- **Desempate de `obtener_triaje_actual`:** la BD guarda segundos; dos triajes en el mismo segundo devolvían el más antiguo. Ahora gana el último agregado, que en un historial leído por `fecha_hora, id_triaje` es el más reciente.
- **Síntoma repetido:** lo rechaza el modelo (`agregar_sintoma`) antes de llegar al `INSERT`, que fallaría por la clave primaria de `triaje_sintoma`.
- **Sin datos clínicos en los logs:** ni la justificación ni el motivo de consulta; solo ids, niveles y estados.

### Pendientes
- Decidir si se puede registrar un triaje en un episodio ya dado de alta, referido o fugado (hoy el modelo no lo impide).
- `Triaje.reclasificar` acepta "reclasificar" al mismo nivel sugerido y guarda la justificación aunque `es_reclasificacion` sea `False`. No viola RN-10, pero conviene decidir si debe rechazarse.
- Cola de espera (episodios EN ESPERA DE CAMA ordenados por nivel y tiempo): con `asignacion_dao.py` / `cama_controller`.

---

## [2026-10-21] — `CamaDAO.cambiar_estado` con historial

### Cambio
- `dao/cama_dao.py`: nuevo `CamaDAO.cambiar_estado(cama, estado_anterior)`. Dentro de `transaccion()` ejecuta un `UPDATE` condicional (solo cambia la cama si en la BD sigue en `estado_anterior`, está activa y existe) y un `INSERT` en `historial_estado_cama`.
- `models/excepciones.py`: el docstring de `CamaNoDisponibleError` cubre cualquier cambio de estado en conflicto, no solo la asignación.
- `tests/test_cama_dao.py`: 22 pruebas nuevas (47 en total). La clase `BD` simulada también reemplaza `ConexionBD` en `dao.transaccion`.

### Archivos afectados
- `dao/cama_dao.py`, `models/excepciones.py`, `tests/test_cama_dao.py`, `docs/`

### Motivo
Primer uso real de `transaccion()`. Cambiar el estado de una cama son dos escrituras: sin transacción, un fallo en el historial dejaría un cambio sin registrar. Lo necesitarán la asignación de camas, el alta (RN-07) y la confirmación de limpieza (RN-08).

### Impacto
- Pruebas: 580 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), con `CamaDAO`, `AuditoriaDAO` y `transaccion()` reales y una segunda conexión que hace de "otra PC". 19 comprobaciones pasaron:
  - Ciclo completo de TRA-02: DISPONIBLE → RESERVADA → OCUPADA → EN LIMPIEZA → DISPONIBLE; cada paso queda guardado y el historial tiene los 4 cambios en orden.
  - Conflicto entre dos PCs: esta PC carga OBS-01 (DISPONIBLE), la otra la ocupa, y esta intenta reservarla con datos desactualizados → `CamaNoDisponibleError`; la cama conserva el estado de la otra PC, no se escribe historial y la transacción queda cerrada.
  - Una cama inexistente y una dada de baja (RN-11) lanzan `CamaNoDisponibleError` y no cambian.
  - Dentro de la transacción de un controlador: si falla un paso posterior se deshacen estado, historial y auditoría; si todo sale bien, la otra PC no ve nada hasta el COMMIT y después ve los tres.

### Decisiones
- **El modelo decide, el DAO guarda:** las transiciones válidas siguen siendo de la máquina de estados de `Cama` (`reservar`, `dar_alta`, `liberar_limpieza`...). El DAO no repite esas reglas; solo recibe la cama ya cambiada y el estado del que partió.
- **`UPDATE` condicional para la concurrencia:** el objeto en memoria puede estar desactualizado (el modelo permitió reservar porque creía que la cama estaba DISPONIBLE). La condición `id_estado_cama = <estado_anterior>` hace que la BD tenga la última palabra.
- **0 filas → excepción, no `False`:** dentro de la transacción de un controlador, la excepción deshace toda la operación; un `False` que nadie revise dejaría confirmar el resto. Por la misma razón, una cama inexistente o dada de baja también lanza `CamaNoDisponibleError` (el `UPDATE` no distingue esos casos de un conflicto).
- **No se registra un "cambio" al mismo estado:** `cambiar_estado` lanza `ValueError` si el estado no cambió (p. ej. `fuera_de_servicio()` sobre una cama que ya lo estaba).
- **Los ids de estado se obtienen del catálogo por nombre** con subconsultas sobre `estado_cama` (el valor del Enum), igual que `CamaDAO.listar_disponibles`.
- **La auditoría la registra el controlador**, dentro de la misma transacción; el DAO no audita por su cuenta.

### Pendientes
- Usar `cambiar_estado` desde `asignacion_dao.py` y desde los controladores de la Fase 4.

---

## [2026-10-21] — Transacciones explícitas (`dao/transaccion.py`)

### Cambio
- Nuevo `dao/transaccion.py`: gestor de contexto `with transaccion():` que agrupa varias escrituras en una unidad (patrón *Unit of Work*). Hace COMMIT si el bloque termina bien y ROLLBACK ante cualquier excepción, que luego se vuelve a lanzar. Un bloque anidado se une a la transacción abierta.
- `dao/db_connection.py`: `ConexionBD` conoce el estado de transacción (`en_transaccion`, `iniciar_transaccion`, `terminar_transaccion`). Durante una transacción, `obtener_conexion` **no se reconecta**: lanza `ConexionBDError`.
- Nuevo `tests/test_transaccion.py` (16 pruebas) y 11 pruebas nuevas en `tests/test_db_connection.py`.
- `CLAUDE.md`: reglas de uso de `transaccion()` y de concurrencia con `UPDATE` condicional.

### Archivos afectados
- `dao/transaccion.py` (nuevo), `dao/db_connection.py`, `tests/test_transaccion.py` (nuevo), `tests/test_db_connection.py`, `CLAUDE.md`, `docs/`

### Motivo
Era el problema abierto que bloqueaba `cama_dao.cambiar_estado`, `triaje_dao.py` y `asignacion_dao.py`. Con `autocommit=True`, si falla un paso intermedio de una operación (p. ej. el tercer paso de asignar una cama), los anteriores ya quedaron guardados y la BD queda inconsistente.

### Impacto
- Pruebas: 558 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), usando `ConexionBD`, `BaseDAO` y `AuditoriaDAO` reales. 21 comprobaciones pasaron:
  - Antes del COMMIT otra conexión no ve los cambios; después ve el `UPDATE` y el `INSERT`.
  - Un error de MySQL en el tercer paso (1062 por `UNIQUE cama_vigente`, RN-05) y una excepción de negocio deshacen los pasos anteriores.
  - Un bloque anidado no confirma por su cuenta; un error en él deshace también lo del externo.
  - `AuditoriaDAO.registrar` contra MySQL real (JSON con tildes intacto). Si la operación falla, su auditoría se deshace; si la auditoría falla (FK, 1452), la operación se deshace.
  - Con la conexión cortada a mitad (`KILL`), el paso siguiente lanza `ConexionBDError` sin reconectar, MySQL deshace el paso anterior y la transacción queda cerrada; fuera de una transacción sí se reconecta.
  - Una sentencia suelta fuera de transacciones se guarda al instante (autocommit sigue activo).
- **Bug encontrado por la verificación real** (las pruebas con `MagicMock` no podían verlo): con la extensión C del conector, `rollback()` sobre una conexión cortada lanza `_mysql_connector.MySQLInterfaceError`, que **no hereda** de `mysql.connector.Error`; escapaba de `_deshacer` y tapaba el `ConexionBDError` original. `commit()` tiene el mismo comportamiento. Corregido: `terminar_transaccion` comprueba `is_connected()` antes; si la conexión se perdió, no llama a `rollback()` (MySQL ya deshizo lo pendiente) y confirmar lanza `ConexionBDError`. Tres pruebas reproducen el caso.

### Decisiones
- **Gestor de contexto en lugar de `autocommit=False` global:** con `autocommit=False` un `commit()` olvidado pierde datos y, en REPEATABLE READ, una conexión de larga vida lee una foto vieja (el mapa de camas no vería los cambios de otras PCs). `START TRANSACTION` suspende el autocommit solo mientras dura el bloque.
- **No procedimientos almacenados:** sacarían reglas de negocio de Python y serían difíciles de probar con pytest.
- **El controlador marca la unidad, el DAO hace COMMIT/ROLLBACK:** el controlador no escribe SQL; solo dice qué pasos van juntos.
- **Bloques anidados se unen al externo:** un método DAO de varios pasos (`cambiar_estado` + historial) usa `transaccion()` y sirve solo o dentro de la transacción de un controlador. Consecuencia: dentro de una transacción, las excepciones deben llegar al `with` más externo; si se capturan a mitad, lo demás se confirmaría.
- **`try/finally` con una bandera `exito`** en lugar de `except Exception`: deshace ante cualquier error sin capturarlo.
- **Sin reconexión durante una transacción:** los pasos siguientes irían a una conexión nueva, fuera de la transacción, con autocommit, y quedarían guardados aunque la operación estuviera a medias.
- **La auditoría va dentro de la transacción** (pendiente de `AuditoriaDAO`): nunca queda un cambio sensible sin auditar ni una auditoría de algo que no ocurrió.
- **Concurrencia entre PCs con `UPDATE` condicional** (`WHERE ... AND estado = <esperado>` y comprobar `rowcount`), como en `PacienteDAO.identificar`, respaldado por los `UNIQUE` de la BD. Más simple que `SELECT ... FOR UPDATE` y sin bloqueos en espera.
- La conexión es compartida: una sola transacción a la vez (la app de escritorio es de un hilo).

### Pendientes
- Limitación conocida: si la conexión se corta justo entre `is_connected()` y `commit()`/`rollback()`, el error de la extensión C escaparía igual. Es muy improbable.
- Usar `transaccion()` en `cama_dao.cambiar_estado`, `triaje_dao.py` y `asignacion_dao.py`.

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
