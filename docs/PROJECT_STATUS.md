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
- Pruebas: **183 pasan** (`python -m pytest`), sin necesidad de MySQL ni `.env`.

### Tarea actual

Ninguna en curso. Siguiente tarea: **`dao/paciente_dao.py`**, pero antes hay que resolver el
problema 1 de la sección "Problemas abiertos" (`Paciente` no tiene `sexo`).

---

## Fases

| Fase | Estado |
|---|---|
| Fase 0 — Entorno y estructura | Completada (`.venv` recreado dentro del proyecto el 2026-10-11) |
| Fase 1 — Base de datos | Completada. Verificada en MariaDB 11.8; falta probarla en MySQL 8.0 |
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
| `models/persona.py` | `Persona`, `Paciente`, `Empleado`, `Enfermero`, `Medico`, `PersonalLimpieza` | `test_persona.py` (29) |
| `models/cama.py` | `Cama` y 4 subtipos, máquina de estados, `es_compatible` | `test_cama.py` (32) |
| `models/estrategias.py` | `EstrategiaTriaje`, `ReglaManchester`, `ReglaMINSA` | `test_estrategias.py` (32) |
| `models/triaje.py` | `EpisodioEmergencia`, `Triaje`, `SignosVitales`, `Sintoma` | `test_triaje.py` (38) |
| `models/estados.py` | `EstadoCama`, `EstadoEpisodio` | `test_estados_vs_bd.py` (2) |
| `models/excepciones.py` | `SigtacError` y 7 excepciones derivadas | Se usan en las pruebas anteriores |

### Fase 3 — DAO

- `dao/db_connection.py`: Singleton, credenciales obligatorias desde `.env`, `autocommit=True`, reconexión (`test_db_connection.py`, 11 pruebas).
- `dao/usuario_dao.py`: login con JOIN a `empleado` y `rol`, bcrypt, usuario inactivo, señuelo, validación de DNI y bloqueo de 5 intentos durante 15 min (`test_usuario_dao.py`, 33 pruebas).
- `seed.sql` tiene hashes bcrypt válidos. El login con un usuario del seed se verificó a mano contra una base temporal (ver CHANGELOG del 2026-10-11).

---

## Problemas abiertos

Diferencias entre el código y la BD encontradas al cerrar la Fase 2. **No se corrigieron:**
cada una requiere una decisión del equipo antes de escribir el DAO correspondiente.

1. **`Paciente` no tiene `sexo`.** La tabla `paciente` exige `sexo CHAR(1) NOT NULL` con `CHECK (sexo IN ('M','F'))`,
   pero la clase no tiene ese atributo. `paciente_dao.py` no podrá insertar un paciente creado desde la clase. **Bloquea `paciente_dao.py`.**
2. **`Paciente.seguro` es texto** (por ejemplo, `"EsSalud"`) y la tabla guarda `id_seguro` (FK a `seguro`). El DAO tendrá que traducir entre los dos.
3. **`Empleado` no refleja `estado_registro`.** La tabla `empleado` lo tiene (el seed incluye un empleado anulado), pero la clase no tiene `activo` ni `anular()`, a diferencia de `Paciente`.
4. **Atributos de subclase sin columna en la BD:** `Enfermero.area`, `Medico.especialidad` y `PersonalLimpieza.turno` no existen en `empleado`. Además, no tienen `@property`, así que no se pueden leer desde fuera de la clase.
5. **`Persona` no valida sus datos.** No comprueba el formato del DNI ni que `fecha_nac` no sea futura (con una fecha futura, `calcular_edad()` devuelve un valor negativo). `UsuarioDAO` sí valida el DNI (8 dígitos), pero la columna admite `VARCHAR(15)`.
6. **Permisos duplicados:** la tabla `rol` y `tiene_permiso()` en cada subclase. Se decidirá en la Fase 4. Las pruebas actuales fijan el comportamiento de `tiene_permiso()`.
7. **Transacciones:** `ConexionBD` usa `autocommit=True` y una sola conexión. `triaje_dao.py` y `asignacion_dao.py` necesitan transacciones explícitas; hay que decidir cómo implementarlas antes de escribirlos.

---

## Pendientes conocidos (sin bloqueo inmediato)

- Actualizar `db_scripts/diagrama.png` (faltan `fecha_nac`, `intentos_fallidos`, `bloqueado_hasta` y las columnas generadas de `asignacion_cama`).
- Probar `schema.sql` y `seed.sql` en un MySQL 8.0 real.
- Pruebas de integración contra una BD real (temporal).
- Revisar la coherencia de `usuario_dao.py` con `auth_controller.py` cuando exista.
- Decidir si `seed.sql` mantiene los datos reales de los integrantes.
- PyCharm: cada integrante debe seleccionar `SIGTAC/.venv` como intérprete.

---

## Próximo trabajo previsto

1. Resolver el problema 1 (y decidir el 2) → `paciente_dao.py`.
2. `cama_dao.py`.
3. `auditoria_dao.py`.
4. Decidir el manejo de transacciones (problema 7).
5. `triaje_dao.py`.
6. `asignacion_dao.py`.

El orden respecto al plan original cambia en un punto: `auditoria_dao.py` pasa antes que `triaje_dao.py` y `asignacion_dao.py`,
porque es de una sola tabla y no depende de transacciones. El motivo queda registrado en `CHANGELOG.md`.

---

## Dependencias importantes

### `paciente_dao.py`

Depende de:
- `models/persona.py` (`Paciente`);
- tablas `paciente` y `seguro`;
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
