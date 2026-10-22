# SIGTAC — Project Status

> Estado de trabajo actual del proyecto.
> Este archivo debe mantenerse pequeño y actualizado después de cada sesión importante.
> Última actualización: 2026-10-21.

---

## Estado general

**Proyecto:** SIGTAC  
**Curso:** Programación Orientada a Objetos II  
**Estado:** Desarrollo activo

### Situación actual

- Base de datos (22 tablas) implementada con las restricciones de RN-05 y RN-10 y el bloqueo temporal de cuentas.
- **Fase 2 (models) cerrada:** todas las clases del plan existen y tienen pruebas automáticas.
- **Fase 3 (DAO) en curso:** `db_connection.py`, `base_dao.py`, `usuario_dao.py`, `paciente_dao.py`, `cama_dao.py` (lectura), `auditoria_dao.py` y `transaccion.py` están terminados y probados.
- `sigtac_db` recreada con el esquema actual (2026-10-21).
- `models/persona.py` alineado con las tablas `paciente` y `empleado`, con validaciones de entrada (2026-10-12).
- Pacientes y empleados se identifican con `DocumentoIdentidad` (DNI, carné de extranjería, pasaporte o CPP) (2026-10-21).
- Un paciente puede ingresar sin identificar (NN) e identificarse después (2026-10-21).
- Pruebas: **558 pasan** (`python -m pytest`), sin necesidad de MySQL ni `.env`.

### Tarea actual

Ninguna en curso. Siguiente tarea: **`cama_dao.cambiar_estado`** con historial, usando `transaccion()` y `UPDATE` condicional.

---

## Fases

| Fase | Estado |
|---|---|
| Fase 0 — Entorno y estructura | Completada (`.venv` recreado dentro del proyecto el 2026-10-11) |
| Fase 1 — Base de datos | Completada. Verificada en MySQL 8.0.46 (2026-10-12 y 2026-10-21) y antes en MariaDB 11.8 |
| Fase 2 — Models | Completada (2026-10-12) |
| Fase 3 — DAO | En curso: `db_connection.py`, `base_dao.py`, `usuario_dao.py`, `paciente_dao.py`, `cama_dao.py` (lectura), `auditoria_dao.py` y `transaccion.py` terminados |
| Fase 4 — Controllers | Pendiente (la carpeta `controllers/` aún no existe) |
| Fase 5 — Utils | Parcial: `security.py` y `logging_config.py` hechos; falta `pdf_generator.py` |
| Fase 6 — Views | Pendiente (la carpeta `views/` aún no existe) |
| Fase 7 — Integración y pruebas | Pendiente |

---

## Completado y verificado

### Fase 2 — Models

| Archivo | Contenido | Pruebas |
|---|---|---|
| `models/persona.py` | `Persona`, `Paciente` (incluye `no_identificado` e `identificar`), `Empleado`, `Enfermero`, `Medico`, `PersonalLimpieza` | `test_persona.py` (192) |
| `models/documento.py` | `TipoDocumento`, `DocumentoIdentidad` (objeto valor: tipo + número) | `test_documento.py` (53) |
| `models/cama.py` | `Cama` y 4 subtipos, máquina de estados, `es_compatible` | `test_cama.py` (32) |
| `models/estrategias.py` | `EstrategiaTriaje`, `ReglaManchester`, `ReglaMINSA` | `test_estrategias.py` (32) |
| `models/triaje.py` | `EpisodioEmergencia`, `Triaje`, `SignosVitales`, `Sintoma` | `test_triaje.py` (38) |
| `models/estados.py` | `EstadoCama`, `EstadoEpisodio` | `test_estados_vs_bd.py` (9: también comprueba sexo, turno, tipos de cama, tipos de documento, el paciente NN del seed, las tablas auditables y las acciones de auditoría) |
| `models/auditoria.py` | `AccionAuditoria` (INSERT, UPDATE, ANULAR, IDENTIFICAR) | `test_auditoria_dao.py` y `test_estados_vs_bd.py` |
| `models/excepciones.py` | `SigtacError` y 7 excepciones derivadas | Se usan en las pruebas anteriores |

### Fase 3 — DAO

- `dao/db_connection.py`: Singleton, credenciales obligatorias desde `.env`, `autocommit=True`, `FOUND_ROWS`, reconexión (salvo durante una transacción) y estado de transacción (`test_db_connection.py`, 23 pruebas).
- `dao/transaccion.py`: `with transaccion():` con COMMIT/ROLLBACK, bloques anidados que se unen al externo (`test_transaccion.py`, 16 pruebas). Verificado en MySQL 8.0.46 con una base temporal (21 comprobaciones, incluida una conexión cortada a mitad).
- `dao/base_dao.py`: clase base de los DAO (cursor, cierre y traducción de errores a `PersistenciaError`/`RegistroDuplicadoError`) (`test_base_dao.py`, 23 pruebas).
- `dao/paciente_dao.py`: buscar por id/documento, crear (también sin identificar), listar e identificar pacientes NN, actualizar (sin tocar el documento) y baja lógica (`test_paciente_dao.py`, 38 pruebas). Verificado en MySQL 8.0.46 con una base temporal (2026-10-12: 15 comprobaciones; 2026-10-21, con documentos y NN: 33).
- `dao/cama_dao.py`: búsqueda por id/código y listados; fábrica de subclases por `nombre_tipo_cama` (`test_cama_dao.py`, 25 pruebas). Verificado en MySQL 8.0.46 con una base temporal (11 comprobaciones). Falta cambiar estado (siguiente tarea).
- `dao/usuario_dao.py`: hereda de `BaseDAO`; login con tipo + número de documento, JOIN a `empleado`, `tipo_documento` y `rol`, bcrypt, usuario inactivo, señuelo y bloqueo de 5 intentos durante 15 min (`test_usuario_dao.py`, 39 pruebas).
- `dao/auditoria_dao.py`: `registrar` (bitácora de solo inserción; acción con `AccionAuditoria`, tabla con lista blanca, detalles como JSON) y `listar_por_registro` (`test_auditoria_dao.py`, 32 pruebas). Verificado en MySQL 8.0.46 con una base temporal junto con las transacciones (JSON con tildes, auditoría deshecha si falla la operación y viceversa).
- `seed.sql` tiene hashes bcrypt válidos. El login con un usuario del seed se verificó a mano contra una base temporal (ver CHANGELOG del 2026-10-11).

---

## Problemas abiertos

1. **Paciente NN que ya estaba registrado:** si al identificar a un NN su documento ya pertenece a otro paciente, `PacienteDAO.identificar` lanza `RegistroDuplicadoError`. Unir los dos registros (mover los episodios) no está implementado; se decidirá con el controlador.
2. **Permisos duplicados:** la tabla `rol` y `tiene_permiso()` en cada subclase. Se decidirá en la Fase 4. Las pruebas actuales fijan el comportamiento de `tiene_permiso()`.

### Resueltos el 2026-10-21

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
- Pruebas de integración permanentes contra una BD real (la verificación del 2026-10-12 fue un script temporal).
- Revisar la coherencia de `usuario_dao.py` con `auth_controller.py` cuando exista.
- Decidir si `seed.sql` mantiene los datos reales de los integrantes.
- PyCharm: cada integrante debe seleccionar `SIGTAC/.venv` como intérprete.
- Opcional: quitar a `sigtac_app` el permiso `UPDATE` sobre `bitacora_auditoria`, para que la bitácora no se pueda modificar ni por error del código (lo ejecuta el usuario con su cuenta de administrador).

---

## Próximo trabajo previsto

1. `cama_dao.cambiar_estado` con historial.
2. `triaje_dao.py`.
3. `asignacion_dao.py`.

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
