# SIGTAC — Project Status

> Estado de trabajo actual del proyecto.
> Este archivo debe mantenerse pequeño y actualizado después de cada sesión importante.
> Última actualización: 2026-10-12.

---

## Estado general

**Proyecto:** SIGTAC  
**Curso:** Programación Orientada a Objetos II  
**Estado:** Desarrollo activo

### Situación actual

- Base de datos (21 tablas) implementada con las restricciones de RN-05 y RN-10 y el bloqueo temporal de cuentas.
- **Fase 2 (models) cerrada:** todas las clases del plan existen y tienen pruebas automáticas.
- **Fase 3 (DAO) iniciada:** `db_connection.py` y `usuario_dao.py` están terminados y probados.
- `models/persona.py` alineado con las tablas `paciente` y `empleado`, con validaciones de entrada (2026-10-12).
- Pruebas: **341 pasan** (`python -m pytest`), sin necesidad de MySQL ni `.env`.

### Tarea actual

Ninguna en curso. Siguiente tarea: **`dao/paciente_dao.py`** (ya no está bloqueado).
Antes hay que volver a ejecutar `schema.sql` y `seed.sql` sobre `sigtac_db`: tiene el esquema anterior al 2026-10-12.

---

## Fases

| Fase | Estado |
|---|---|
| Fase 0 — Entorno y estructura | Completada (`.venv` recreado dentro del proyecto el 2026-10-11) |
| Fase 1 — Base de datos | Completada. Verificada en MySQL 8.0.46 (2026-10-12) y antes en MariaDB 11.8 |
| Fase 2 — Models | Completada (2026-10-12) |
| Fase 3 — DAO | En curso: `db_connection.py` y `usuario_dao.py` terminados |
| Fase 4 — Controllers | Pendiente (la carpeta `controllers/` aún no existe) |
| Fase 5 — Utils | Parcial: `security.py` y `logging_config.py` hechos; falta `pdf_generator.py` |
| Fase 6 — Views | Pendiente (la carpeta `views/` aún no existe) |
| Fase 7 — Integración y pruebas | Pendiente |

---

## Completado y verificado

### Fase 2 — Models

| Archivo | Contenido | Pruebas |
|---|---|---|
| `models/persona.py` | `Persona`, `Paciente`, `Empleado`, `Enfermero`, `Medico`, `PersonalLimpieza`, `es_dni_valido` | `test_persona.py` (185) |
| `models/cama.py` | `Cama` y 4 subtipos, máquina de estados, `es_compatible` | `test_cama.py` (32) |
| `models/estrategias.py` | `EstrategiaTriaje`, `ReglaManchester`, `ReglaMINSA` | `test_estrategias.py` (32) |
| `models/triaje.py` | `EpisodioEmergencia`, `Triaje`, `SignosVitales`, `Sintoma` | `test_triaje.py` (38) |
| `models/estados.py` | `EstadoCama`, `EstadoEpisodio` | `test_estados_vs_bd.py` (4: también comprueba sexo y turno contra los `CHECK`) |
| `models/excepciones.py` | `SigtacError` y 7 excepciones derivadas | Se usan en las pruebas anteriores |

### Fase 3 — DAO

- `dao/db_connection.py`: Singleton, credenciales obligatorias desde `.env`, `autocommit=True`, reconexión (`test_db_connection.py`, 11 pruebas).
- `dao/usuario_dao.py`: login con JOIN a `empleado` y `rol`, bcrypt, usuario inactivo, señuelo, validación de DNI y bloqueo de 5 intentos durante 15 min (`test_usuario_dao.py`, 33 pruebas).
- `seed.sql` tiene hashes bcrypt válidos. El login con un usuario del seed se verificó a mano contra una base temporal (ver CHANGELOG del 2026-10-11).

---

## Problemas abiertos

1. **`sigtac_db` desactualizada:** no se ha vuelto a ejecutar `schema.sql`/`seed.sql` sobre ella tras los cambios del 2026-10-12. Hacerlo borra los datos de desarrollo.
2. **Pacientes sin DNI peruano** (extranjeros o pacientes sin identificar): `Persona` exige 8 dígitos, así que hoy no se pueden registrar. Requiere una decisión del equipo.
3. **Permisos duplicados:** la tabla `rol` y `tiene_permiso()` en cada subclase. Se decidirá en la Fase 4. Las pruebas actuales fijan el comportamiento de `tiene_permiso()`.
4. **Transacciones:** `ConexionBD` usa `autocommit=True` y una sola conexión. `triaje_dao.py` y `asignacion_dao.py` necesitan transacciones explícitas; hay que decidir cómo implementarlas antes de escribirlos.

### Resueltos el 2026-10-12

- `Paciente` tiene `sexo` e `id_seguro` (+ `nombre_seguro` opcional); ya no bloquea `paciente_dao.py`.
- `Empleado` tiene `activo` y `anular()` (espejo de `estado_registro`).
- `area`, `especialidad` y `turno` tienen columna en `empleado` y `@property` en su subclase.
- `Persona` y sus subclases validan sus datos (DNI, nombres, fecha de nacimiento, ids, sexo, turno).
- `schema.sql` y `seed.sql` verificados en MySQL 8.0.46 con una base temporal (32 comprobaciones, incluidas RN-05 y RN-10).
- Los `CHECK` de `sexo` y `turno` aceptaban minúsculas y variantes sin acento por la *collation*; corregido con `utf8mb4_bin`.

---

## Pendientes conocidos (sin bloqueo inmediato)

- Actualizar `db_scripts/diagrama.png` (faltan `fecha_nac`, `id_area`, `especialidad`, `turno`, `intentos_fallidos`, `bloqueado_hasta`, las columnas generadas de `asignacion_cama` y el área "Triaje").
- Pruebas de integración permanentes contra una BD real (la verificación del 2026-10-12 fue un script temporal).
- Revisar la coherencia de `usuario_dao.py` con `auth_controller.py` cuando exista.
- Decidir si `seed.sql` mantiene los datos reales de los integrantes.
- PyCharm: cada integrante debe seleccionar `SIGTAC/.venv` como intérprete.
- El `.env` local usa `root`: crear `sigtac_app` con `db_scripts/crear_usuario_app.sql` y cambiar `DB_USER`/`DB_PASS`.

---

## Próximo trabajo previsto

1. Volver a ejecutar `schema.sql` y `seed.sql` sobre `sigtac_db` (problema 1).
2. `paciente_dao.py`: debe convertir `estado_registro` (0/1) a `bool` y obtener `nombre_seguro` con un JOIN.
3. `cama_dao.py`.
4. `auditoria_dao.py`.
5. Decidir el manejo de transacciones (problema 4).
6. `triaje_dao.py`.
7. `asignacion_dao.py`.

El orden respecto al plan original cambia en un punto: `auditoria_dao.py` pasa antes que `triaje_dao.py` y `asignacion_dao.py`,
porque es de una sola tabla y no depende de transacciones. El motivo queda registrado en `CHANGELOG.md`.

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
