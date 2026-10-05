# SIGTAC — Project Status

> Estado de trabajo actual del proyecto.
> Este archivo debe mantenerse pequeño y actualizado después de cada sesión importante.
> Última actualización: 2026-10-05.

---

## Estado general

**Proyecto:** SIGTAC  
**Curso:** Programación Orientada a Objetos II  
**Estado:** Desarrollo activo

### Situación actual

El proyecto ya cuenta con una base de datos definida e implementada según la documentación del proyecto y la ruta de desarrollo.

El plan académico marca la **Fase 2 (models) como “En curso”**, pero actualmente también se ha iniciado trabajo en la **Fase 3 (DAO)**.

### Tarea actual

**`dao/usuario_dao.py`**

Revisión técnica, depuración de manejo de recursos e inspección estática completadas.

---

## Fases

| Fase | Estado |
|---|---|
| Fase 0 — Entorno y estructura | Preparación documentada |
| Fase 1 — Base de datos | Completada según documentación |
| Fase 2 — Models | En curso según plan |
| Fase 3 — DAO | Iniciada (`usuario_dao.py` verificado) |
| Fase 4 — Controllers | Pendiente |
| Fase 5 — Utils | Parcial/adelantada según plan |
| Fase 6 — Views | Pendiente |
| Fase 7 — Integración y pruebas | Pendiente |

---

## Trabajo actual: `dao/usuario_dao.py`

### Requisitos funcionales conocidos

El DAO debe:

- consultar la tabla `usuario`;
- relacionarla con `empleado`;
- relacionarla con `rol`;
- verificar la contraseña utilizando `utils/security.py`;
- comprobar `usuario.activo`;
- impedir el acceso de un usuario desactivado;
- retornar la información necesaria para la sesión;
- utilizar consultas parametrizadas.

### Checklist de implementación

- [x] Consulta `usuario`.
- [x] JOIN con `empleado`.
- [x] JOIN con `rol`.
- [x] Consulta parametrizada.
- [x] Verificación mediante `security.py`.
- [x] Validación de `usuario.activo`.
- [x] Manejo de credenciales incorrectas.
- [x] Manejo de usuario inexistente.
- [x] Manejo de errores de BD (`DBError`).
- [x] Cierre correcto de recursos (`cursor.close()` con `buffered=True`).
- [ ] Pruebas con base de datos poblada (`seed.sql` requiere hashes válidos).
- [ ] Revisión de coherencia con `auth_controller.py`.

---

## Próximo trabajo previsto

Una vez revisado y cerrado `usuario_dao.py`, continuar con los DAO restantes según dependencias:

1. `paciente_dao.py`
2. `cama_dao.py`
3. `triaje_dao.py`
4. `asignacion_dao.py`
5. `auditoria_dao.py`

El orden exacto puede cambiar si el código existente introduce una dependencia diferente. Cualquier cambio de orden debe registrarse en `CHANGELOG.md`.

---

## Dependencias importantes

### `usuario_dao.py`

Depende de:
- `db_connection.py`
- `utils/security.py`
- estructura real de las tablas `usuario`, `empleado` y `rol`.

### `cama_dao.py`

Depende de:
- jerarquía de clases de `models/cama.py`;
- método `es_compatible(nivel)`;
- estructura de `tipo_cama`, `cama` y estados.

### `triaje_dao.py`

Depende de:
- `EpisodioEmergencia`;
- `Triaje`;
- `SignosVitales`;
- `Sintoma`;
- estructura de `triaje_sintoma`.

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
