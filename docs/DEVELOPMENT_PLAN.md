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
- [x] Estructura:
  - `models/`
  - `dao/`
  - `controllers/`
  - `views/`
  - `views/assets/`
  - `utils/`
- [x] `utils/security.py`
  - hash con bcrypt
  - verificación de contraseñas

**Nota:** `security.py` se adelantó a esta fase porque `usuario_dao.py` depende de él.

---

## Fase 1 — Persistencia y base de datos

**Estado documentado:** completado.

### Tareas

- [x] `schema.sql`
- [x] 21 tablas
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

**Estado documentado en el plan:** en curso.

**Objetivo:** traducir reglas clínicas y operativas a Python/POO sin tocar la base de datos.

### `excepciones.py`

- [x] `CamaEstadoInvalidoError`
- [x] `UsuarioSinPermisoError`

> `UsuarioSinPermisoError` se utiliza conceptualmente en controladores, no debe mezclarse con la responsabilidad de los modelos.

### `persona.py`

- [x] Clase abstracta `Persona`
- [] Clase `Empleado`
- [x] `Paciente`
- [x] `Enfermero`
- [x] `Medico`
- [x] `PersonalLimpieza`

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

### `usuario_dao.py`

**Prioridad actual del desarrollo.**

Debe:

1. Consultar `usuario`.
2. Cruzar con `empleado`.
3. Cruzar con `rol`.
4. Recuperar los datos necesarios para la sesión.
5. Verificar la contraseña con `utils/security.py`.
6. Comprobar `usuario.activo`.
7. Rechazar usuarios desactivados.
8. Utilizar consultas parametrizadas.

### `paciente_dao.py`

- [ ] Crear paciente.
- [ ] Buscar paciente.
- [ ] Buscar por DNI.
- [ ] Actualizar paciente.
- [ ] Borrado lógico con `estado_registro = FALSE`.

### `cama_dao.py`

- [ ] Consultar camas disponibles.
- [ ] Mapear registros a subclases.
- [ ] Utilizar fábrica simple.
- [ ] Filtrar SQL por disponibilidad.
- [ ] Evaluar compatibilidad con `cama.es_compatible(nivel)` en Python.

### `triaje_dao.py`

- [ ] Persistir información del episodio.
- [ ] Persistir signos vitales.
- [ ] Persistir síntomas mediante `triaje_sintoma`.

### `asignacion_dao.py`

- [ ] Consultas necesarias para asignación.
- [ ] Reserva/liberación según flujo definido.
- [ ] Preparar operaciones transaccionales requeridas.

### `auditoria_dao.py`

- [ ] `registrar(usuario, tabla, accion)`.
- [ ] Mantener auditoría explícita desde los controladores.

---

## Fase 4 — Controladores (`controllers/`)

**Objetivo:** orquestar las interacciones entre vistas, modelos y DAO.

### `auth_controller.py`

- [ ] Recibir usuario/contraseña.
- [ ] Delegar autenticación a `usuario_dao`.
- [ ] Mantener sesión activa.
- [ ] Determinar permisos por rol.

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
- [ ] Obtener cola de espera.
- [ ] Evaluar reglas de asignación.
- [ ] Obtener camas compatibles.
- [ ] Reservar mediante transacción atómica.
- [ ] Evitar inconsistencias por concurrencia.

### `reporte_controller.py`

- [ ] Consultar datos.
- [ ] Preparar AVG/COUNT y otros cálculos.
- [ ] Preparar KPIs.
- [ ] Entregar datos a las vistas.

---

## Fase 5 — Módulos transversales (`utils/`)

### `security.py`

- [x/adelantado] Hash/verificación con bcrypt.

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
