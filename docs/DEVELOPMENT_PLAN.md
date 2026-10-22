# SIGTAC — Development Plan

> Ruta de desarrollo derivada del `Plan_de_Desarrollo_de_Software.md` y alineada con el documento académico.
> Este archivo describe el orden previsto; no debe interpretarse automáticamente como evidencia de que una tarea ya está terminada.

---

## Fase 0 — Configuración del entorno y estructura base

**Objetivo:** preparar el entorno, dependencias y estructura inicial.

### Tareas

- [x] `requirements.txt`
  - `mysql-connector-python`
  - `customtkinter`
  - `python-dotenv`
  - `bcrypt`
  - `reportlab`
  - `matplotlib`
- [x] `.env` para credenciales.
- [x] `.gitignore` para excluir `.env`, cachés y archivos sensibles.
- [x] `requirements-dev.txt` (dependencias de la aplicación + `pytest`) y `pytest.ini`.
- [x] `.env.example` como plantilla versionada.
- [x] `tests/` con pytest.
- [ ] Estructura:
  - [x] `models/`
  - [x] `dao/`
  - [ ] `controllers/` (se crea en la Fase 4)
  - [ ] `views/` (se crea en la Fase 6)
  - [ ] `views/assets/` (se crea en la Fase 6)
  - [x] `utils/`
- [x] `utils/security.py`
  - hash con bcrypt
  - verificación de contraseñas

**Nota:** `security.py` se adelantó a esta fase porque `usuario_dao.py` depende de él.

---

## Fase 1 — Persistencia y base de datos

**Estado documentado:** completado.

### Tareas

- [x] `schema.sql`
- [x] 22 tablas (`tipo_documento` añadida el 2026-10-21)
- [x] Claves primarias
- [x] Claves foráneas
- [x] Restricciones
- [x] `BOOLEAN` donde corresponde
- [x] Borrado lógico donde corresponde
- [x] `seed.sql`
- [x] Datos de prueba

### Aspectos que deben conservarse

- MySQL 8.0.
- InnoDB.
- Integridad referencial.
- Transacciones.
- Modelo normalizado hasta 3FN.

---

## Fase 2 — Lógica de negocio (`models/`)

**Estado:** completada (2026-10-12). Todas las clases tienen pruebas en `tests/`.

**Objetivo:** traducir reglas clínicas y operativas a Python/POO sin tocar la base de datos.

### `excepciones.py`

- [x] `SigtacError` (clase base)
- [x] `CamaEstadoInvalidoError`
- [x] `CamaNoDisponibleError`
- [x] `UsuarioSinPermisoError`
- [x] `NivelTriajeInvalidoError`
- [x] `ReglaNegocioError`
- [x] `ConexionBDError`
- [x] `SignosVitalesIncompletosError`

> `UsuarioSinPermisoError` se utiliza conceptualmente en controladores, no debe mezclarse con la responsabilidad de los modelos.

### `estados.py`

- [x] `EstadoCama` (`StrEnum`)
- [x] `EstadoEpisodio` (`StrEnum`)
- [x] Prueba que compara sus valores con los catálogos de `seed.sql`

### `persona.py`

- [x] Clase abstracta `Persona` (recibe un `DocumentoIdentidad`; valida nombres y fecha de nacimiento)
- [x] `DocumentoIdentidad` y `TipoDocumento` (`models/documento.py`): DNI, CE, pasaporte y CPP
- [x] Paciente sin identificar (NN): `Paciente.no_identificado` e `identificar`
- [x] Clase abstracta `Empleado` (con `activo` y baja lógica `anular()`, RN-11)
- [x] `Paciente` (con `sexo`, `id_seguro` y baja lógica `anular()`, RN-11)
- [x] `Enfermero` (`area`)
- [x] `Medico` (`especialidad`)
- [x] `PersonalLimpieza` (`turno`)
- [x] Alineado con las tablas `paciente` y `empleado` (2026-10-12)
- [x] Pruebas (`tests/test_persona.py`)

### `cama.py`

- [x] Clase abstracta `Cama`
- [x] Validación de estados
- [x] `es_compatible(nivel)`
- [x] `CamaUCI`
- [x] `CamaObservacion`
- [x] `CamaHospitalizacion`
- [x] `CamaTraumaShock`

### `estrategias.py`

- [x] `EstrategiaTriaje`
- [x] `ReglaManchester`
- [x] `ReglaMINSA`
- [x] Aplicación del patrón Strategy

### `triaje.py`

- [x] `EpisodioEmergencia`
- [x] `Triaje`
- [x] `SignosVitales`
- [x] `Sintoma`
- [x] Historial de reclasificaciones
- [x] Justificación obligatoria al reclasificar

---

## Fase 3 — Acceso a datos (`dao/`)

**Objetivo:** conectar los objetos Python con MySQL mediante SQL parametrizado.

### `db_connection.py`

- [x] Conexión centralizada a MySQL.
- [x] Patrón Singleton según diseño.
- [x] Credenciales desde `.env`.
- [x] Manejo correcto de cursor/conexión.
- [x] Cierre/commit/rollback según corresponda.
- [x] Estado de transacción; no se reconecta a mitad de una transacción.

### `transaccion.py`

**Estado:** completado, probado (`tests/test_transaccion.py`) y verificado en MySQL 8.0.46 con una base temporal.

- [x] `with transaccion():` (Unit of Work): COMMIT si todo sale bien, ROLLBACK ante cualquier excepción.
- [x] Un bloque anidado se une a la transacción abierta.
- [x] La auditoría va dentro de la transacción de la operación auditada.

### `usuario_dao.py`

**Estado:** completado y probado (`tests/test_usuario_dao.py`).

- [x] Consultar `usuario`.
- [x] Cruzar con `empleado`.
- [x] Cruzar con `rol`.
- [x] Recuperar los datos necesarios para la sesión.
- [x] Verificar la contraseña con `utils/security.py`.
- [x] Comprobar `usuario.activo`.
- [x] Rechazar usuarios desactivados.
- [x] Utilizar consultas parametrizadas.
- [x] Bloqueo temporal tras 5 intentos fallidos (15 min).

### `base_dao.py`

**Estado:** completado y probado (`tests/test_base_dao.py`).

- [x] Conexión, cursor y cierre en un solo lugar.
- [x] Errores de MySQL → `PersistenciaError` / `RegistroDuplicadoError`.
- [x] `usuario_dao.py` hereda de `BaseDAO`.

### Orden de implementación de los DAO restantes

`paciente_dao.py` → `cama_dao.py` → `auditoria_dao.py` → (decisión sobre transacciones) → `triaje_dao.py` + `episodio_dao.py` → `asignacion_dao.py` + `solicitud_limpieza_dao.py`. **Fase 3 completada (2026-10-21).**
Motivo del orden: ver `CHANGELOG.md` (2026-10-12).

### `paciente_dao.py`

> Requisitos del modelo: convertir `estado_registro` (0/1) a `bool` para `activo` y obtener `nombre_seguro` con un JOIN a `seguro`.

**Estado:** completado, probado (`tests/test_paciente_dao.py`) y verificado en MySQL 8.0.46 con una base temporal.

- [x] Crear paciente.
- [x] Buscar paciente.
- [x] Buscar por documento (tipo + número).
- [x] Actualizar paciente (el documento no se modifica).
- [x] Pacientes sin identificar: crear, `listar_no_identificados` e `identificar`.
- [x] Borrado lógico con `estado_registro = FALSE`.

### `cama_dao.py`

**Estado:** completado (lectura y cambio de estado), probado (`tests/test_cama_dao.py`) y verificado en MySQL 8.0.46 con una base temporal.

- [x] Consultar camas disponibles.
- [x] Mapear registros a subclases.
- [x] Utilizar fábrica simple (`CLASES_POR_TIPO`, por `nombre_tipo_cama`).
- [x] Filtrar SQL por disponibilidad.
- [x] Evaluar compatibilidad con `cama.es_compatible(nivel)` en Python: lo hace el controlador sobre `listar_disponibles()`.
- [x] Cambiar estado + registrar en `historial_estado_cama` (`cambiar_estado`: `transaccion()` y `UPDATE` condicional).

### `triaje_dao.py` y `episodio_dao.py`

**Estado:** completados, probados (`tests/test_triaje_dao.py`, `tests/test_episodio_dao.py`) y verificados en MySQL 8.0.46 con una base temporal. El episodio tiene su propio DAO (un DAO por entidad); ver `CHANGELOG.md` del 2026-10-21.

- [x] Persistir información del episodio (`EpisodioDAO.crear`, `buscar_por_id`, `cambiar_estado`).
- [x] Persistir signos vitales (`TriajeDAO.registrar`).
- [x] Persistir síntomas mediante `triaje_sintoma` (`TriajeDAO.registrar`).
- [x] Leer el historial de triajes (RN-09) y el catálogo de síntomas.

### `asignacion_dao.py` y `solicitud_limpieza_dao.py`

**Estado:** completados, probados (`tests/test_asignacion_dao.py`) y verificados en MySQL 8.0.46 con el ciclo completo de una cama. La solicitud de limpieza tiene su propio DAO (un DAO por entidad).

- [x] Consultas necesarias para asignación (asignación vigente por episodio o por cama).
- [x] Reserva/liberación según flujo definido (`crear`, `liberar`; RN-05, RN-07).
- [x] Solicitudes de limpieza: crear al dar de alta, listar pendientes y atender (RN-07, RN-08).
- [x] Operaciones transaccionales: cada método es una sentencia y se combina en `transaccion()` desde el controlador.

### `auditoria_dao.py`

**Estado:** completado y probado (`tests/test_auditoria_dao.py`).

- [x] `registrar(id_usuario, tabla, accion, id_registro, detalles=None)`: solo inserción; `AccionAuditoria` y lista blanca de tablas.
- [x] `listar_por_registro(tabla, id_registro)`.
- [ ] Mantener auditoría explícita desde los controladores (Fase 4).

---

## Fase 4 — Controladores (`controllers/`)

**Objetivo:** orquestar las interacciones entre vistas, modelos y DAO.

### `auth_controller.py`

**Estado:** completado y probado (`tests/test_auth_controller.py`, 2026-10-21).

- [x] Recibir tipo y número de documento y contraseña (`iniciar_sesion`).
- [x] Delegar autenticación a `usuario_dao` (login fallido → `AutenticacionError` con mensaje genérico).
- [x] Mantener sesión activa (`Sesion`, inyectada en los demás controladores; `cerrar_sesion` la invalida).
- [x] Determinar permisos por rol: `exigir_permiso(sesion, permiso)` usa `tiene_permiso` de `models/permisos.py` y lanza `UsuarioSinPermisoError` si falta el permiso.

### `paciente_controller.py`

- [ ] Buscar o registrar al paciente (con documento o NN).
- [ ] Abrir el episodio de emergencia.
- [ ] Identificar y fusionar pacientes NN (con auditoría).

### `triaje_controller.py`

- [ ] Recibir datos del formulario.
- [ ] Crear objetos de dominio.
- [ ] Invocar Strategy.
- [ ] Obtener clasificación sugerida.
- [ ] Validar confirmación/reclasificación.
- [ ] Exigir justificación cuando corresponda.
- [ ] Persistir mediante DAO.

### `cama_controller.py`

- [ ] Orquestar asignación.
- [ ] Obtener cola de espera (requiere un listado por estado en `EpisodioDAO`; orden: nivel de triaje y luego llegada).
- [ ] Evaluar reglas de asignación.
- [ ] Obtener camas compatibles.
- [ ] Reservar mediante transacción atómica.
- [ ] Evitar inconsistencias por concurrencia.

### `reporte_controller.py`

- [ ] Consultar datos.
- [ ] Preparar AVG/COUNT y otros cálculos (el SQL va en un `dao/reporte_dao.py`; el controlador solo da formato).
- [ ] Preparar KPIs.
- [ ] Entregar datos a las vistas.

---

## Fase 5 — Módulos transversales (`utils/`)

### `security.py`

- [x] Hash/verificación con bcrypt (adelantado a la Fase 0).
- [x] `simular_verificacion()` (señuelo contra ataques de tiempo).

### `logging_config.py`

- [x] `configurar_logging()`, que se llama una sola vez desde el punto de entrada.

### `pdf_generator.py`

- [ ] Generar PDF con ReportLab.
- [ ] Recibir datos preparados por los controladores.
- [ ] No colocar reglas de negocio en el generador.

---

## Fase 6 — Presentación (`views/`)

**Objetivo:** construir las ventanas con CustomTkinter.

### Regla

Las vistas:
- no ejecutan SQL;
- no contienen reglas clínicas;
- se encargan de visualización, eventos y navegación.

### Archivos

- [ ] `login_view.py`
- [ ] `app_principal.py`
- [ ] `dashboard_view.py`
- [ ] `triage_view.py`
- [ ] `pacientes_view.py`
- [ ] `assets/`

### Dashboard

Debe mostrar:
- tarjetas KPI;
- mapa de camas;
- estados visuales.

### Triaje

Debe permitir:
- filiación;
- signos vitales;
- síntomas;
- visualización de sugerencia;
- confirmación/reclasificación.

---

## Fase 7 — Integración y pruebas finales

### Integración

- [ ] Login → sesión → permisos.
- [ ] Paciente → episodio.
- [ ] Episodio → signos/síntomas.
- [ ] Triaje → clasificación.
- [ ] Triaje → cola.
- [ ] Cola → camas compatibles.
- [ ] Asignación → estados de cama.
- [ ] Liberación → limpieza → disponibilidad.
- [ ] Operaciones sensibles → auditoría.
- [ ] Reportes → indicadores/PDF.

### Pruebas

- [ ] Autenticación correcta.
- [ ] Contraseña incorrecta.
- [ ] Usuario desactivado.
- [ ] CRUD paciente.
- [ ] Borrado lógico.
- [ ] Clasificación.
- [ ] Reclasificación con justificación.
- [ ] Reclasificación sin justificación.
- [ ] Compatibilidad de camas.
- [ ] Reserva de cama no disponible.
- [ ] Transacciones/rollback.
- [ ] Auditoría.
- [ ] Reportes.

---

## Orden de trabajo recomendado

```text
FASE 0
  ↓
FASE 1
  ↓
FASE 2 (models)
  ↓
FASE 3 (DAO)
  ↓
FASE 4 (controllers)
  ↓
FASE 5 (utils)
  ↓
FASE 6 (views)
  ↓
FASE 7 (integración y pruebas)
```

### Regla de actualización

Este documento es el **plan previsto**, no el registro del estado real.

El estado real debe actualizarse en `PROJECT_STATUS.md`.

Si durante el desarrollo se cambia el orden, registrar el motivo en `CHANGELOG.md`.
