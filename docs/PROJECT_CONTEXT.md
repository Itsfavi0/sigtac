# SIGTAC — Project Context

> Documento de contexto técnico y funcional para asistentes de IA.
> Fuente principal: `SIGTAC_Proyecto_POO_II_Actualizado(1).docx`.
> Complemento de planificación: `Plan_de_Desarrollo_de_Software.md`.
> Última actualización: 2026-10-05.

---

## 1. Identidad del proyecto

**SIGTAC** significa **Sistema Integrado de Gestión de Triaje y Asignación de Camas**.

Es el proyecto integrador del curso **Programación Orientada a Objetos II** de la Universidad Nacional del Callao.

### Ficha técnica

| Elemento | Definición |
|---|---|
| Tipo | Prototipo de aplicación de escritorio para contexto académico |
| Lenguaje | Python 3.12+ |
| GUI | Tkinter + CustomTkinter |
| Base de datos | MySQL 8.0 |
| Conector | mysql-connector-python |
| Arquitectura | Por capas: presentación, control, lógica de negocio y acceso a datos |
| Patrones | DAO, Strategy y Singleton |
| Equipo | Favio Brañez Choquemamani (líder), Renzo Moya Ángeles, Leonardo Veliz Neyra, Ian Sevillano Quispe y Percy Malpartida Salinas |
| Entrega indicada en el documento | 19/12/2026 |

---

## 2. Objetivo general

Desarrollar un prototipo funcional de aplicación de escritorio orientada a objetos que permita modelar el proceso de triaje y la asignación de camas de emergencia, integrando los principales elementos del dominio mediante clases y reglas de negocio definidas para el proyecto académico.

### Objetivos técnicos

- Modelar el dominio usando encapsulamiento, abstracción, herencia y polimorfismo.
- Diseñar una base de datos relacional normalizada.
- Construir una interfaz gráfica con Tkinter/CustomTkinter.
- Separar presentación, control, lógica de negocio y acceso a datos.
- Aplicar patrones de diseño relevantes al curso.
- Mantener un alcance que pueda ser explicado y sustentado por el equipo.

---

## 3. Problema que resuelve

El sistema busca apoyar el proceso de atención de emergencia, especialmente:

1. Registro y recuperación de pacientes.
2. Registro de episodios de emergencia.
3. Registro de signos vitales y síntomas.
4. Clasificación de triaje.
5. Confirmación o reclasificación por parte del profesional.
6. Búsqueda y asignación de camas compatibles.
7. Gestión de estados de las camas.
8. Auditoría de operaciones sensibles.
9. Indicadores y reportes.

El proceso propuesto no sustituye la responsabilidad clínica: el sistema **sugiere** una clasificación y el profesional debe confirmarla o reclasificarla.

---

## 4. Módulos funcionales

El prototipo contempla cinco módulos principales:

### 4.1 Seguridad y acceso
- Inicio de sesión.
- Control de acceso por rol.
- Cierre de sesión.

### 4.2 Gestión de pacientes
- Registro.
- Búsqueda.
- Edición.
- Consulta de pacientes y episodios.

### 4.3 Triaje
- Registro de signos vitales.
- Registro de síntomas.
- Clasificación sugerida.
- Confirmación.
- Reclasificación con justificación.

### 4.4 Gestión y asignación de camas
- Visualización de camas.
- Actualización de estados.
- Cola priorizada.
- Búsqueda de compatibilidad.
- Reserva.
- Liberación.
- Flujo de limpieza mediante cambios de estado.

### 4.5 Reportes y auditoría
- Indicadores básicos.
- Consultas.
- Reportes.
- Registro de operaciones sensibles.

---

## 5. Arquitectura

La arquitectura separa responsabilidades en capas:

```text
┌──────────────────────────────┐
│          VIEWS               │
│ Tkinter / CustomTkinter      │
└──────────────┬───────────────┘
               │ interacción
┌──────────────▼───────────────┐
│        CONTROLLERS           │
│ Orquestación / validación    │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│       MODELS / DOMAIN        │
│ POO + reglas de negocio      │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│            DAO               │
│ SQL parametrizado            │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│            MySQL             │
└──────────────────────────────┘
```

### Regla arquitectónica fundamental

- Las vistas no deben contener SQL.
- Los modelos no deben contener SQL.
- Los DAO encapsulan las consultas a la base de datos.
- Los controladores orquestan interacción entre vista, modelos y DAO.
- Las reglas de negocio deben permanecer en la capa de dominio/control correspondiente.
- No duplicar lógica entre capas.

---

## 6. Patrones de diseño

### DAO
Aplicado para aislar SQL de las clases del dominio.

Ejemplos previstos:
- `PacienteDAO`
- `CamaDAO`
- `TriajeDAO`
- `AsignacionDAO`

### Strategy
Aplicado al algoritmo de clasificación de triaje.

Estructura conceptual:
- `EstrategiaTriaje`
- `ReglaManchester`
- `ReglaMINSA`

Permite intercambiar el algoritmo sin modificar el resto del sistema.

### Singleton
Aplicado a `ConexionBD` / `db_connection.py`.

Su objetivo es centralizar la conexión a MySQL y evitar abrir una conexión nueva para cada operación.

---

## 7. Modelo orientado a objetos

### Jerarquía de personas

El diseño contempla una relación:

```text
Persona
├── Paciente
└── Empleado
    ├── Enfermero
    ├── Medico
    └── PersonalLimpieza
```

### Jerarquía de camas

```text
Cama (abstracta)
├── CamaUCI
├── CamaObservacion
├── CamaHospitalizacion
└── CamaTraumaShock
```

`Cama` define el comportamiento común y `es_compatible(nivel_triaje)` se resuelve mediante polimorfismo en los subtipos.

### Triaje

El modelo contempla:
- `EpisodioEmergencia`
- `Triaje`
- `SignosVitales`
- `Sintoma`

El episodio puede tener múltiples registros de triaje para conservar reclasificaciones.

---

## 8. Base de datos

El documento indica **21 tablas implementadas** en `schema.sql`, con datos de prueba en `seed.sql`.

Categorías principales:

- Catálogos: estados, tipos, áreas, niveles de triaje, síntomas, etc.
- Maestras: empleado, usuario, paciente, cama.
- Transaccionales: episodio, signos vitales, triaje, relación triaje-síntoma, asignación de cama, solicitud de limpieza.
- Historial/auditoría: historial de estado de cama y bitácora de auditoría.

La base utiliza:
- MySQL 8.0.
- InnoDB.
- Claves primarias y foráneas.
- Restricciones.
- Transacciones.
- Normalización hasta tercera forma normal.

### Decisiones importantes

- `usuario` se separa de `empleado` porque no todo empleado necesita acceso al sistema y el historial del empleado no debe depender de eliminar sus credenciales.
- `rol` se separa de `cargo` porque el cargo laboral y los permisos del software son conceptos distintos.
- Se conserva el estado actual de la cama en `cama` y el historial en `historial_estado_cama`.
- `triaje_sintoma` resuelve la relación muchos-a-muchos entre triaje y síntomas.
- La relación episodio → triaje es uno-a-muchos para conservar reclasificaciones.

El documento también indica que se añadieron:
- `usuario.activo`
- `triaje.id_nivel_sugerido`
- `triaje.justificacion`

para poder cumplir las reglas de negocio correspondientes.

---

## 9. Reglas técnicas críticas para los DAO

### `usuario_dao.py`

Debe:
- Consultar `usuario` junto con `empleado` y `rol`.
- Verificar la contraseña mediante las funciones de `utils/security.py`.
- Validar `usuario.activo`.
- Impedir el inicio de sesión de usuarios desactivados aunque la contraseña sea correcta.

### `paciente_dao.py`

Debe:
- Implementar CRUD.
- Permitir búsquedas por DNI.
- Aplicar borrado lógico mediante `estado_registro = FALSE`, asociado a RN-11.

### `cama_dao.py`

Debe:
- Consultar camas disponibles.
- Mapear cada fila al subtipo correcto.
- Utilizar una fábrica simple basada en el tipo de cama.
- Filtrar en SQL únicamente por `estado_cama = DISPONIBLE` para la disponibilidad.
- Determinar la compatibilidad final mediante `cama.es_compatible(nivel)` en Python.

**No trasladar la lógica de compatibilidad al SQL comparando directamente `tipo_cama.nivel_min`.** El diseño del proyecto considera que ese único umbral no representa correctamente los rangos de compatibilidad de todos los subtipos.

### `triaje_dao.py`

Debe:
- Insertar la cabecera del episodio cuando corresponda al flujo.
- Guardar signos vitales.
- Gestionar la relación `triaje_sintoma`.

### `auditoria_dao.py`

Debe exponer una operación conceptual:

```text
registrar(usuario, tabla, accion)
```

Los controladores realizan explícitamente el registro después de operaciones sensibles.

Para el alcance del curso se prefiere esta solución explícita frente a AOP/decoradores.

---

## 10. Seguridad

- Las contraseñas no deben almacenarse en texto plano.
- Se utiliza `bcrypt` para hash/verificación.
- Las credenciales de BD se gestionan mediante `.env`.
- `.env` no debe versionarse.
- Las consultas DAO deben ser parametrizadas.
- El acceso por rol se resolverá en la capa de controladores.

`UsuarioSinPermisoError` está planificada para la Fase 4, donde se resolverá el control de permisos por rol.

---

## 11. Reglas de responsabilidad clínica

El sistema no toma la decisión clínica final.

Flujo conceptual:

```text
Datos del paciente
      ↓
Signos + síntomas
      ↓
Regla de triaje
      ↓
Nivel sugerido
      ↓
Profesional confirma
      │
      └── si reclasifica → justificación obligatoria
```

Esta decisión debe conservarse durante la implementación y sustentación.

---

## 12. Indicadores

El proyecto contempla seis indicadores:

1. Tiempo de puerta a triaje.
2. Tiempo de triaje a cama.
3. Tiempo de rotación de cama.
4. Porcentaje de ocupación.
5. Cumplimiento del tiempo objetivo por nivel.
6. Tasa de reclasificación.

---

## 13. Documentos de referencia

Dentro del repositorio, estos documentos cumplen funciones distintas:

- `PROJECT_CONTEXT.md`: contexto compacto y estable para IA.
- `DEVELOPMENT_PLAN.md`: ruta de implementación.
- `PROJECT_STATUS.md`: estado real actual.
- `CHANGELOG.md`: historial de cambios y decisiones.
- Documento Word del proyecto: documento académico completo / fuente funcional y de diseño.

---

## 14. Regla para cualquier asistente de IA

Antes de modificar código:

1. Revisar el código existente.
2. Revisar los documentos relevantes.
3. Identificar dependencias.
4. Verificar que el cambio respete la arquitectura.
5. Verificar reglas de negocio afectadas.
6. Evitar inventar funcionalidades o clases no contempladas.
7. Si existe contradicción entre documentación y código, señalarla antes de resolverla silenciosamente.
8. Mantener los nombres y estructuras existentes salvo que exista una razón técnica clara.
9. No crear archivos innecesarios.
10. Al terminar, informar archivos modificados, cambios, reglas afectadas, problemas pendientes y siguiente tarea.

---

## 15. Fuente de verdad

En caso de duda, utilizar este orden:

1. **Código real del repositorio** para saber qué está implementado.
2. **`PROJECT_STATUS.md`** para saber qué se está trabajando actualmente.
3. **Documento académico oficial** para requisitos, reglas, arquitectura y decisiones del proyecto.
4. **`DEVELOPMENT_PLAN.md`** para saber cuál es la ruta prevista.
5. **`CHANGELOG.md`** para conocer decisiones y evolución histórica.

Si una fuente contradice otra, no ocultar la contradicción: reportarla y pedir/establecer una decisión explícita.
