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
  - [x] `controllers/` (Fase 4)
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
- [x] Criterios de la sugerencia (2026-10-30): `evaluar()` devuelve `Clasificacion(nivel, criterios)`; `clasificar()` lo da la clase base

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
- [x] Mantener auditoría explícita desde los controladores (Fase 4): cada escritura sensible se audita dentro de su transacción.

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

**Estado:** completado y probado (`tests/test_paciente_controller.py`, 2026-10-22).

- [x] Buscar o registrar al paciente (con documento o NN).
- [x] Abrir el episodio de emergencia (uno abierto por paciente; bloqueo de fila contra la doble admisión).
- [x] Identificar y fusionar pacientes NN (con auditoría).
- [x] Editar los datos (PACIENTES); dar de baja y reactivar (ADMINISTRACION).

### `admin_controller.py`

- [x] Cuentas de usuario: crear, cambiar rol, activar/desactivar, restablecer la clave y desbloquear.
- [x] Consultar la bitácora por período, tabla y usuario.

### `triaje_controller.py`

**Estado:** completado y probado (`tests/test_triaje_controller.py`, 2026-10-22).

- [x] Recibir datos del formulario (diccionario de signos vitales e ids de síntomas).
- [x] Crear objetos de dominio.
- [x] Invocar Strategy (recibida en el constructor; Manchester por defecto).
- [x] Obtener clasificación sugerida (`sugerir`; al registrar se recalcula, no se recibe de la vista).
- [x] Validar confirmación/reclasificación.
- [x] Exigir justificación cuando corresponda (RN-10).
- [x] Persistir mediante DAO (con bloqueo del episodio y auditoría).

### `cama_controller.py`

**Estado:** completado y probado (`tests/test_cama_controller.py`, 2026-10-22).

- [x] Orquestar asignación (y ocupar, cancelar, dar de alta y confirmar limpieza).
- [x] Obtener cola de espera (`EpisodioDAO.listar_por_estado` + `ordenar_por_prioridad`: nivel de triaje y luego llegada).
- [x] Evaluar reglas de asignación (RN-01, RN-05, compatibilidad).
- [x] Obtener camas compatibles.
- [x] Reservar mediante transacción atómica.
- [x] Evitar inconsistencias por concurrencia (`UPDATE` condicional; verificado en MySQL).
- [x] Fuera de servicio / volver a servicio (GESTION_CAMAS; sin paciente asignado ni limpieza pendiente).
- [x] Referir y registrar una fuga (liberan la cama si la había).

### `reporte_controller.py`

**Estado:** completado y probado (`tests/test_reporte_controller.py` y `tests/test_reporte_dao.py`, 2026-10-22).

- [x] Consultar datos.
- [x] Preparar AVG/COUNT y otros cálculos (el SQL va en `dao/reporte_dao.py`; el controlador calcula porcentajes).
- [x] Preparar KPIs (ocupación, reclasificación, tiempos de espera y estancia).
- [x] Entregar datos a las vistas (`EstadoGuardia` e `IndicadoresPeriodo`, inmutables).

---

## Fase 5 — Módulos transversales (`utils/`)

### `security.py`

- [x] Hash/verificación con bcrypt (adelantado a la Fase 0).
- [x] `simular_verificacion()` (señuelo contra ataques de tiempo).

### `logging_config.py`

- [x] `configurar_logging()`, que se llama una sola vez desde el punto de entrada.

### `pdf_generator.py`

**Estado:** completado y probado (`tests/test_pdf_generator.py`, 2026-10-26). Lo usa `ReporteController.exportar_pdf`.

- [x] Generar PDF con ReportLab.
- [x] Recibir datos preparados por los controladores (`IndicadoresPeriodo` y `EstadoGuardia`).
- [x] No colocar reglas de negocio en el generador (solo formato y diseño).

---

## Fase 6 — Presentación (`views/`)

**Objetivo:** construir las ventanas con CustomTkinter.

### Regla

Las vistas:
- no ejecutan SQL;
- no contienen reglas clínicas;
- se encargan de visualización, eventos y navegación.

### Alcance acordado (2026-10-26)

- Las 5 pantallas de esta lista. Gestión de camas (asignar, alta, fuera de servicio), limpieza, reportes con PDF y administración (cuentas, bitácora, baja y reactivación de pacientes) quedan para después; sus controladores ya existen.
- Piezas compartidas en `views/componentes/`, antes de las pantallas.
- Las vistas reciben sus controladores en el constructor (se prueban con controladores falsos, sin MySQL) y solo capturan `SigtacError` y `ValueError`, que muestran con `mostrar_error`.

### Archivos

- [x] `main.py` (punto de entrada: una sola ventana que cambia entre el login y la aplicación). Se ejecuta cuando existan `login_view.py` y `app_principal.py`.
- [x] `views/tema.py`: colores, fuentes, espaciado en base 8 y `color_texto_sobre`. Ninguna vista escribe un valor a mano.
- [x] `utils/colores.py`: tonos de los niveles de triaje y de los estados de cama, compartidos con el PDF.
- [x] `views/componentes/`: `mostrar_error`/`mostrar_info`/`confirmar`, `TablaDatos`, `InsigniaNivel`, `TarjetaKPI`, `TarjetaCama`, `CamposDocumento`, `MatrizCamas` y `marcar_foco`/`marcar_error`.
- [x] Diseño (2026-10-27): `PRODUCT.md`, `docs/diseno/` (brief, crítica, láminas, tablero aprobado) y tema con pares claro/oscuro e Inter (`views/assets/fonts/`).
- [x] `login_view.py` (2026-10-29)
- [x] `app_principal.py` (2026-10-29): las pantallas se registran en `PANTALLAS`
- [x] Piezas para las pantallas (2026-10-29): `BotonPrimario`/`BotonSecundario`, `Marca`, `campo_texto`/`etiqueta_campo`
- [x] `dashboard_view.py` (2026-10-30): KPIs, matriz de camas y cola de espera de cama; se actualiza cada 30 s
- [x] `views/formato.py` y `prototipo/` (controladores de demostración: `python -m prototipo.ver`)
- [x] `triage_view.py` (2026-10-30): paciente (buscar, registrar, NN o de la cola), signos con su rango, síntomas y el panel de clasificación con los criterios; reclasificar con justificación (RN-10)
- [x] Piezas para el triaje (2026-10-30): `Tarjeta` (extraída del tablero), `lista_opciones` (extraída de `CamposDocumento`), `casilla` y `Selector`
- [ ] `pacientes_view.py`
- [ ] `assets/` (por ahora no hace falta: la interfaz no usa imágenes)

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

En los controladores (sin interfaz), verificado en MySQL con `scripts/verificar_controladores.py` (2026-10-22); falta repetirlo desde las vistas:

- [x] Login → sesión → permisos (`verificar_controladores.py` inicia sesión con una cuenta creada por el administrador).
- [x] Paciente → episodio.
- [x] Episodio → signos/síntomas.
- [x] Triaje → clasificación.
- [x] Triaje → cola.
- [x] Cola → camas compatibles.
- [x] Asignación → estados de cama.
- [x] Liberación → limpieza → disponibilidad.
- [x] Operaciones sensibles → auditoría.
- [x] Reportes → indicadores/PDF (`ReporteController.exportar_pdf`; incluido en `verificar_controladores.py`).

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
