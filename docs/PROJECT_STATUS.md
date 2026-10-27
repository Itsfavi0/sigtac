# SIGTAC — Project Status

> Estado de trabajo actual del proyecto.
> Este archivo debe mantenerse pequeño y actualizado después de cada sesión importante.
> Última actualización: 2026-10-26.

---

## Estado general

**Proyecto:** SIGTAC  
**Curso:** Programación Orientada a Objetos II  
**Estado:** Desarrollo activo

### Situación actual

- Base de datos (22 tablas) implementada con las restricciones de RN-05 y RN-10 y el bloqueo temporal de cuentas.
- **Fase 2 (models) cerrada:** todas las clases del plan existen y tienen pruebas automáticas.
- **Fase 3 (DAO) cerrada (2026-10-21):** todos los DAO del plan, más `episodio_dao.py`, `solicitud_limpieza_dao.py` y `transaccion.py`, están terminados, probados y verificados en MySQL 8.0.46 con bases temporales.
- `sigtac_db` recreada con el esquema actual (2026-10-21).
- `models/persona.py` alineado con las tablas `paciente` y `empleado`, con validaciones de entrada (2026-10-12).
- Pacientes y empleados se identifican con `DocumentoIdentidad` (DNI, carné de extranjería, pasaporte o CPP) (2026-10-21).
- Un paciente puede ingresar sin identificar (NN) e identificarse después (2026-10-21).
- **Fase 4 (controllers) cerrada (2026-10-22)** y fusionada en `main`: los cinco controladores del plan están hechos, probados y verificados en MySQL 8.0.46 (56 comprobaciones, `scripts/verificar_controladores.py`).
- **Pendientes de la Fase 4 resueltos (2026-10-26)**, verificados en MySQL y fusionados en `main`:
  - referir y registrar una fuga;
  - poner y sacar camas de servicio;
  - editar, dar de baja y reactivar pacientes;
  - `admin_controller.py` (cuentas y bitácora).
- **Fase 5 (utils) cerrada (2026-10-26):** `utils/pdf_generator.py` exporta a PDF los indicadores y el estado de la guardia (`ReporteController.exportar_pdf`).
- **Fase 6 (views) iniciada (2026-10-26):** base hecha (`main.py`, `views/tema.py`, `utils/colores.py`, `Triaje.MIN_JUSTIFICACION`) y piezas compartidas de `views/componentes/`.
- **Diseño de la interfaz (2026-10-27):** contexto en `PRODUCT.md`; brief, crítica, láminas y tablero aprobado en `docs/diseno/`. El tema y los componentes siguen el Figma del equipo, corregido (claro por defecto, oscuro opcional, Inter).
- Pruebas: **1586 pasan** (`python -m pytest`), sin necesidad de MySQL ni `.env`. Las de las vistas usan una ventana Tk oculta.

### Tarea actual

Fase 6: siguiente paso, el prototipo de las pantallas sobre el diseño aprobado (D5): tablero, login, ventana principal, triaje y pacientes.
Antes del triaje: ampliar la estrategia de triaje para que devuelva los criterios de la sugerencia (decisión del 2026-10-27).
Falta que el usuario ejecute `scripts/verificar_controladores.py` para confirmar el PDF con datos reales.

---

## Fases

| Fase | Estado |
|---|---|
| Fase 0 — Entorno y estructura | Completada (`.venv` recreado dentro del proyecto el 2026-10-11) |
| Fase 1 — Base de datos | Completada. Verificada en MySQL 8.0.46 (2026-10-12 y 2026-10-21) y antes en MariaDB 11.8 |
| Fase 2 — Models | Completada (2026-10-12) |
| Fase 3 — DAO | Completada (2026-10-21) |
| Fase 4 — Controllers | Completada (2026-10-22). Verificada en MySQL 8.0.46 |
| Fase 5 — Utils | Completada (2026-10-26): `security.py`, `logging_config.py` y `pdf_generator.py` |
| Fase 6 — Views | En curso: diseño aprobado; base, tema y componentes hechos; faltan las 5 pantallas |
| Fase 7 — Integración y pruebas | Pendiente |

---

## Completado y verificado

### Fase 2 — Models

| Archivo | Contenido | Pruebas |
|---|---|---|
| `models/persona.py` | `Persona`, `Paciente` (incluye `no_identificado`, `identificar` y `fusionar_en`), `Empleado` (instanciable: personal sin profesión específica), `Enfermero`, `Medico`, `PersonalLimpieza` | `test_persona.py` (197) |
| `models/documento.py` | `TipoDocumento`, `DocumentoIdentidad` (objeto valor: tipo + número) | `test_documento.py` (53) |
| `models/cama.py` | `Cama` y 4 subtipos, máquina de estados (incluye `cancelar_reserva`), `es_compatible` | `test_cama.py` (37) |
| `models/estrategias.py` | `EstrategiaTriaje`, `ReglaManchester`, `ReglaMINSA` | `test_estrategias.py` (32) |
| `models/triaje.py` | `EpisodioEmergencia` (historial de solo lectura, `cerrado`, `cancelar_asignacion`), `Triaje` (con `sintomas`), `SignosVitales`, `Sintoma` | `test_triaje.py` (62) |
| `models/estados.py` | `EstadoCama`, `EstadoEpisodio` | `test_estados_vs_bd.py` (11: también comprueba roles, sexo, turno, tipos de cama, tipos de documento, niveles de triaje, el paciente NN del seed, las tablas auditables y las acciones de auditoría) |
| `models/auditoria.py` | `AccionAuditoria` (INSERT, UPDATE, ANULAR, IDENTIFICAR, FUSIONAR) | `test_auditoria_dao.py` y `test_estados_vs_bd.py` |
| `models/asignacion.py` | `AsignacionCama` y `SolicitudLimpieza` (registros inmutables) | `test_asignacion.py` (10) |
| `models/permisos.py` | `Rol`, `Permiso`, matriz `PERMISOS_POR_ROL` y `tiene_permiso(rol, permiso)` | `test_permisos.py` (52) |
| `models/excepciones.py` | `SigtacError` y 7 excepciones derivadas | Se usan en las pruebas anteriores |

### Fase 3 — DAO

- `dao/db_connection.py`: Singleton, credenciales obligatorias desde `.env`, `autocommit=True`, `FOUND_ROWS`, reconexión (salvo durante una transacción) y estado de transacción (`test_db_connection.py`, 23 pruebas).
- `dao/transaccion.py`: `with transaccion():` con COMMIT/ROLLBACK, bloques anidados que se unen al externo (`test_transaccion.py`, 16 pruebas). Verificado en MySQL 8.0.46 con una base temporal (21 comprobaciones, incluida una conexión cortada a mitad).
- `dao/base_dao.py`: clase base de los DAO (cursor, cierre y traducción de errores a `PersistenciaError`/`RegistroDuplicadoError`) (`test_base_dao.py`, 23 pruebas).
- `dao/paciente_dao.py`: buscar por id/documento, crear (también sin identificar), listar, identificar y fusionar pacientes NN, actualizar (sin tocar el documento) y baja lógica (`test_paciente_dao.py`, 47 pruebas). Verificado en MySQL 8.0.46 con una base temporal (2026-10-12: 15 comprobaciones; 2026-10-21, con documentos y NN: 33).
- `dao/cama_dao.py`: búsqueda por id/código y listados; fábrica de subclases por `nombre_tipo_cama`; `cambiar_estado` (UPDATE condicional + historial en una transacción) (`test_cama_dao.py`, 47 pruebas). Verificado en MySQL 8.0.46 con una base temporal (lectura: 11 comprobaciones; `cambiar_estado`: ver CHANGELOG del 2026-10-21).
- `dao/usuario_dao.py`: hereda de `BaseDAO`; login con tipo + número de documento, JOIN a `empleado`, `tipo_documento` y `rol`, bcrypt, usuario inactivo, señuelo y bloqueo de 5 intentos durante 15 min (`test_usuario_dao.py`, 39 pruebas).
- `dao/auditoria_dao.py`: `registrar` (bitácora de solo inserción; acción con `AccionAuditoria`, tabla con lista blanca, detalles como JSON) y `listar_por_registro` (`test_auditoria_dao.py`, 32 pruebas). Verificado en MySQL 8.0.46 con una base temporal junto con las transacciones (JSON con tildes, auditoría deshecha si falla la operación y viceversa).
- `dao/triaje_dao.py`: catálogo de síntomas; `registrar` (signos vitales + triaje + síntomas en una transacción; solo inserción, RN-09) y lectura del historial de triajes y signos por episodio (`test_triaje_dao.py`, 31 pruebas).
- `dao/episodio_dao.py`: crear, `buscar_por_id` (con su historial de signos y triajes) y `cambiar_estado` (`UPDATE` condicional; la fecha de alta la pone MySQL) (`test_episodio_dao.py`, 26 pruebas). Ambos verificados en MySQL 8.0.46 con una base temporal (ver CHANGELOG del 2026-10-21).
- `dao/asignacion_dao.py`: crear, buscar la asignación vigente por episodio o por cama, `liberar` (alta) y `anular` (reserva cancelada), ambos `UPDATE` condicionales. `dao/solicitud_limpieza_dao.py`: crear, `listar_pendientes` y `atender` (`UPDATE` condicional) (`test_asignacion_dao.py`, 29 pruebas). Verificados con el ciclo completo de una cama en una base temporal (ver CHANGELOG del 2026-10-21).
- `dao/reporte_dao.py`: COUNT/AVG para los indicadores (`test_reporte_dao.py`, 44 pruebas).
- Carga en bloque del historial (`EpisodioDAO.listar_por_estado`/`listar_por_paciente`, `TriajeDAO.listar_historial`) y bloqueo de filas (`EpisodioDAO.bloquear`, `PacienteDAO.bloquear`, `SELECT ... FOR UPDATE`). Verificados en MySQL 8.0.46 (ver CHANGELOG del 2026-10-22).
- `seed.sql` tiene hashes bcrypt válidos. El login con un usuario del seed se verificó a mano contra una base temporal (ver CHANGELOG del 2026-10-11).

### Fase 4 — Controllers

| Archivo | Contenido | Pruebas |
|---|---|---|
| `controllers/auth_controller.py` | `Sesion`, `exigir_permiso`, `AuthController` (login y logout) | `test_auth_controller.py` (73) |
| `controllers/paciente_controller.py` | Registro (con documento o NN), abrir episodio (uno abierto por paciente), identificar y fusionar NN | `test_paciente_controller.py` |
| `controllers/triaje_controller.py` | Sugerencia de la estrategia, registro con reclasificación justificada, cola de triaje | `test_triaje_controller.py` (41) |
| `controllers/cama_controller.py` | Mapa, cola de espera, camas compatibles, asignar, ocupar, cancelar, alta y limpieza | `test_cama_controller.py` |
| `controllers/reporte_controller.py` | Estado actual de la guardia, indicadores de un período y `exportar_pdf` | `test_reporte_controller.py` (25) |
| `controllers/colas.py` | `EntradaCola` y `armar_cola` (cola por prioridad, en una transacción) | `test_colas.py` (3) |
| `controllers/admin_controller.py` | Cuentas de usuario (crear, rol, activar, clave, desbloqueo) y consulta de la bitácora | `test_admin_controller.py` (86) |
| `models/usuario.py` | `CuentaUsuario` y la política de claves (`validar_clave_nueva`) | `test_usuario.py` (27) |

`cama_controller.py` también refiere, registra fugas y saca o devuelve camas al servicio (92 pruebas). `paciente_controller.py` también edita, da de baja y reactiva pacientes (78 pruebas).

Todo el flujo, incluidas dos pruebas de concurrencia entre PCs, verificado en MySQL 8.0.46 con `scripts/verificar_controladores.py` (56 comprobaciones).

### Fase 5 — Utils

| Archivo | Contenido | Pruebas |
|---|---|---|
| `utils/security.py` | bcrypt y `simular_verificacion` (señuelo) | `test_security.py` |
| `utils/logging_config.py` | `configurar_logging()` | — |
| `utils/pdf_generator.py` | Reporte PDF (ReportLab): indicadores, gráfico de triajes por nivel, estado de la guardia; `ReporteError` si no se puede guardar | `test_pdf_generator.py` (39) |

---

## Problemas abiertos

Ninguno bloqueante. Las decisiones menores están en "Pendientes conocidos".

### Resueltos el 2026-10-21

- Permisos duplicados: los permisos dependen del rol del usuario, con la matriz de `models/permisos.py`; se quitó `tiene_permiso()` de las subclases de `Empleado`.

- Paciente NN que ya estaba registrado: `Paciente.fusionar_en` + `PacienteDAO.fusionar` (sus episodios pasan al paciente real y el NN se anula).
- Cancelar una reserva: `Cama.cancelar_reserva`, `EpisodioEmergencia.cancelar_asignacion` y `AsignacionDAO.anular`.
- Un episodio cerrado (alta, referido, fuga o anulado) no admite triajes ni signos nuevos.

- Pacientes y empleados extranjeros: `DocumentoIdentidad` (DNI, CE, pasaporte, CPP) y tabla `tipo_documento`.
- Pacientes sin identificar (NN): `Paciente.no_identificado`, `Paciente.identificar` y `PacienteDAO.identificar`.
- `sigtac_db` recreada con `schema.sql` y `seed.sql` actuales.
- Transacciones: `dao/transaccion.py`; la auditoría va dentro de la transacción de la operación auditada.

### Resueltos el 2026-10-12

- `Paciente` tiene `sexo` e `id_seguro` (+ `nombre_seguro` opcional); ya no bloquea `paciente_dao.py`.
- `Empleado` tiene `activo` y `anular()` (espejo de `estado_registro`).
- `area`, `especialidad` y `turno` tienen columna en `empleado` y `@property` en su subclase.
- `Persona` y sus subclases validan sus datos (DNI, nombres, fecha de nacimiento, ids, sexo, turno).
- `schema.sql` y `seed.sql` verificados en MySQL 8.0.46 con una base temporal (32 comprobaciones, incluidas RN-05 y RN-10).
- Los `CHECK` de `sexo` y `turno` aceptaban minúsculas y variantes sin acento por la *collation*; corregido con `utf8mb4_bin`.

---

## Pendientes conocidos (sin bloqueo inmediato)

- Actualizar `db_scripts/diagrama.png` (faltan `tipo_documento` y el cambio de `dni` a `id_tipo_documento` + `num_documento`, `fecha_nac`, `id_area`, `especialidad`, `turno`, `intentos_fallidos`, `bloqueado_hasta`, las columnas generadas de `asignacion_cama` y el área "Triaje").
- Pruebas de integración en pytest contra una BD real (hoy: `scripts/verificar_controladores.py`, que se ejecuta a mano).
- Decidir si `seed.sql` mantiene los datos reales de los integrantes.
- PyCharm: cada integrante debe seleccionar `SIGTAC/.venv` como intérprete.
- `Triaje.reclasificar` al mismo nivel: el controlador ya no lo llama (confirma la sugerencia); falta decidir si el modelo también debe rechazarlo.
- Traslado de cama (un paciente cuya cama falla): hoy una cama con paciente no se puede poner fuera de servicio.
- Validar con el equipo los permisos nuevos:
  - registrar una fuga exige GESTION_CAMAS: ¿también el enfermero?
  - dar de baja y reactivar pacientes exige ADMINISTRACION.
- Que cada usuario cambie su propia clave. Hoy solo la restablece el administrador.
- Una cuenta desactivada conserva la sesión que ya tenía abierta en otra PC hasta cerrarla.
- Un paciente con un episodio abierto se controla en el controlador (con bloqueo de fila), no con una restricción de la BD.
- Opcional: quitar a `sigtac_app` el permiso `UPDATE` sobre `bitacora_auditoria`, para que la bitácora no se pueda modificar ni por error del código (lo ejecuta el usuario con su cuenta de administrador).

---

## Próximo trabajo previsto

1. Validar con el equipo la matriz de permisos (`models/permisos.py`; ver CHANGELOG del 2026-10-21 y 2026-10-26).
2. Ejecutar `scripts/verificar_controladores.py` para confirmar la exportación a PDF con datos reales.
3. Fase 6: vistas con CustomTkinter (`login_view.py` → `app_principal.py` → `dashboard_view.py` → `triage_view.py` → `pacientes_view.py`), que ya pueden usar todos los controladores.

Respecto al plan original, `auditoria_dao.py` se hizo antes que `triaje_dao.py` y `asignacion_dao.py` porque es de una sola tabla y no depende de transacciones (ver `CHANGELOG.md` del 2026-10-12).

---

## Dependencias importantes

### `paciente_dao.py`

Depende de:
- `models/persona.py` (`Paciente`: `sexo`, `id_seguro`, `nombre_seguro`, `activo`);
- tablas `paciente` y `seguro` (JOIN para `nombre_seguro`);
- RN-11 (`estado_registro = FALSE`).

### `cama_dao.py`

Depende de:
- jerarquía de clases de `models/cama.py`;
- método `es_compatible(nivel)`;
- estructura de `tipo_cama`, `cama` y estados (`EstadoCama`).

### `triaje_dao.py`

Depende de:
- `EpisodioEmergencia`;
- `Triaje`;
- `SignosVitales`;
- `Sintoma`;
- estructura de `triaje_sintoma`;
- decisión sobre transacciones.

---

## Decisiones que no deben romperse

1. El SQL pertenece a DAO.
2. Las reglas de negocio pertenecen a la capa correspondiente, no a las vistas.
3. Las vistas no deben consultar MySQL directamente.
4. La compatibilidad de camas se decide mediante polimorfismo (`es_compatible`).
5. La contraseña se almacena como hash, no texto plano.
6. Un usuario inactivo no puede iniciar sesión.
7. La reclasificación exige justificación.
8. El borrado de pacientes es lógico cuando corresponda.
9. La auditoría sensible se registra explícitamente desde los controladores.
10. El proyecto debe seguir siendo explicable y sustentable para el curso.

---

## Archivos de referencia

```text
docs/
├── PROJECT_CONTEXT.md
├── DEVELOPMENT_PLAN.md
├── PROJECT_STATUS.md
└── CHANGELOG.md
```

Además:
- Documento Word académico oficial.
- Código real del repositorio.
- `schema.sql`.
- `seed.sql`.

---

## Cómo actualizar este archivo

Después de una sesión de desarrollo, actualizar únicamente:

### 1. Tarea actual
¿Qué archivo/módulo se está trabajando?

### 2. Completado
¿Qué se verificó realmente?

### 3. Pendiente
¿Qué falta?

### 4. Problemas
¿Qué errores o decisiones están bloqueando?

### 5. Próxima tarea
¿Cuál es el siguiente paso lógico?

No usar este archivo para guardar explicaciones largas. La historia debe ir en `CHANGELOG.md`.
