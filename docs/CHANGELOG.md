# SIGTAC — Changelog

> Registro cronológico de cambios, decisiones y avances relevantes del proyecto.
> No registrar cada modificación mínima de código; registrar cambios que afecten arquitectura, funcionalidad, reglas de negocio, estructura o dirección del desarrollo.

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
