# Hojas de estudio por integrante

El criterio 8 dice: **«Cada integrante debe poder explicar su contribución.»**
Cada uno es responsable de una parte del proyecto. Tiene que poder abrir sus archivos, explicar qué hacen y
responder las preguntas de su hoja **sin leer**.

> **Cómo estudiar (una hora basta):**
> 1. Abre la aplicación sin MySQL y úsala 10 minutos: `python -m prototipo.ver`
> 2. Lee tu hoja y abre cada archivo que menciona.
> 3. Responde tus preguntas en voz alta. Si una no te sale, pregunta en el grupo.
> 4. Lee también [CRITERIOS.md](CRITERIOS.md): el profesor puede preguntarle cualquier cosa a cualquiera.

## Lo que todos deben saber (5 frases)

1. **Qué es:** SIGTAC registra el triaje de emergencia y asigna camas según la prioridad del paciente.
2. **Con qué está hecho:** Python, CustomTkinter para las ventanas y MySQL.
3. **Cómo se organiza:** cuatro capas: `views → controllers → models → dao`. Solo los DAO tienen SQL.
4. **Dónde está la POO:** en `models/`. Herencia en `Cama` y `Persona`, polimorfismo en `es_compatible`,
   encapsulamiento con `@property` y métodos que validan.
5. **Qué no es:** no es un sistema médico real. Es un prototipo académico; el triaje es una sugerencia.

---

## Favio Brañez — Líder: arquitectura, controladores y la demo

**Expone:** la presentación del proyecto, la demo en vivo y la decisión técnica (criterios 5 y 8).

**Archivos:** `main.py`, `controllers/` (sobre todo `cama_controller.py` y `auth_controller.py`), `models/permisos.py`.

**Qué explica:**

- Las capas y por qué las dependencias van solo hacia abajo.
- El patrón de toda operación que escribe: `exigir_permiso` → validar con el modelo → `with transaccion():` leer,
  aplicar la regla, guardar y auditar.
- La decisión técnica: la compatibilidad cama–paciente se resuelve con polimorfismo y no con una columna en SQL
  ([CRITERIOS.md](CRITERIOS.md), criterio 8).

**Preguntas probables:**

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué un controlador y no llamar al DAO desde la pantalla? | La pantalla solo muestra. Si mañana hay una versión web, los controladores sirven igual |
| ¿Dónde se comprueban los permisos? | En el controlador, al inicio de cada operación, con `exigir_permiso`. La matriz rol → permisos está solo en `models/permisos.py` |
| ¿Qué pasa si dos PCs asignan la misma cama? | El `UPDATE` lleva la condición «y que siga disponible». La segunda PC actualiza 0 filas, se lanza un error y se deshace su transacción |
| ¿Por qué el permiso depende del rol y no del cargo? | El cargo es un dato laboral; el rol es un permiso del software. Un médico puede ser jefe de guardia |

---

## Renzo Moya — Base de datos y capa DAO

**Expone:** la observación de la primera presentación (criterio 1) y la conexión a la base de datos (aporte adicional).

**Archivos:** `db_scripts/schema.sql`, `db_scripts/seed.sql`, `dao/db_connection.py`, `dao/base_dao.py`,
`dao/transaccion.py` y un DAO de ejemplo: `dao/cama_dao.py`.

**Qué explica:**

- Lee completo [OBSERVACIONES.md](OBSERVACIONES.md): es tu parte.
- 22 tablas: 10 catálogos, 4 maestras, 6 transaccionales y 2 de historial y auditoría. Normalizadas hasta 3FN.
- `ConexionBD` es un **Singleton**: una sola conexión para toda la aplicación.
- `transaccion()`: varias escrituras se guardan todas (COMMIT) o ninguna (ROLLBACK).
- Todo el SQL lleva parámetros (`%s`): nunca se arma con texto, así no hay inyección de SQL.

**Preguntas probables:**

| Pregunta | Respuesta corta |
|---|---|
| ¿Cómo migrarían a Oracle o SQL Server? | Solo cambia la carpeta `dao/` y los scripts. MySQL se importa en 3 archivos, y una prueba impide que otra capa lo use |
| ¿Qué es un DAO? | Una clase que es el único lugar con SQL de una tabla. Recibe y devuelve objetos, no filas |
| ¿Por qué Singleton en la conexión? | Para no abrir una conexión por operación. Todas las clases comparten la misma |
| ¿Por qué no borran registros? | Regla RN-11: se marca `estado_registro = FALSE`. Se conserva el historial para auditoría |
| ¿Qué pasa si se corta la luz a mitad de una asignación? | La transacción no se confirmó: MySQL la deshace. No queda una cama reservada sin paciente |
| ¿Por qué `paciente` y `episodio_emergencia` son tablas distintas? | El paciente es la persona; el episodio es una visita. Un paciente puede tener muchas |
| ¿Con qué usuario se conecta la aplicación? | Con `sigtac_app`, que solo tiene SELECT, INSERT y UPDATE. No es `root` y no puede borrar |

---

## Leonardo Veliz — Interfaz gráfica

**Expone:** las pantallas durante la demo y la organización del código (criterio 7).

**Archivos:** `views/tema.py`, `views/app_principal.py`, `views/triage_view.py`, `views/componentes/`
(`botones.py`, `tarjetas.py`, `matriz.py`).

**Qué explica:**

- CustomTkinter es Tkinter con un aspecto moderno y modo oscuro.
- `tema.py` es el **único** archivo con colores, letras y medidas. Cada color es un par (claro, oscuro).
  Ninguna pantalla escribe un color a mano.
- `views/componentes/` tiene las piezas que todas las pantallas reutilizan: botones, tarjetas, tablas, la matriz de camas.
- Una pantalla **nunca** tiene SQL ni reglas: recibe su controlador y solo muestra lo que este le devuelve.
- Cada rol ve solo sus módulos: el menú se arma con los permisos de la sesión.

**Preguntas probables:**

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué CustomTkinter y no Tkinter puro? | Es Tkinter por debajo (lo que pide el curso), con mejor aspecto y modo oscuro |
| ¿Cómo sabe la pantalla que un dato es inválido? | No lo sabe ella: el modelo lanza un `ValueError` y la pantalla muestra el mensaje y marca el campo |
| ¿Qué pasa si cambian el color de «Ocupada»? | Se cambia en un solo lugar (`utils/colores.py` y `tema.py`) y cambia en toda la aplicación y en el PDF |
| ¿Cómo se actualiza el tablero? | Solo, cada 30 segundos, mientras está a la vista |
| ¿Se puede usar sin mouse? | Sí: con Tab, Enter y las flechas |
| ¿Cómo prueban las pantallas? | Con controladores falsos: no necesitan MySQL |

---

## Ian Sevillano — Clases del dominio y encapsulamiento

**Expone:** las clases principales (criterio 2) y el encapsulamiento (criterio 3).

**Archivos:** `models/persona.py`, `models/documento.py`, `models/triaje.py`, `models/usuario.py`.

**Qué explica:**

- La tabla de clases del criterio 2 en [CRITERIOS.md](CRITERIOS.md): qué representa cada una, qué guarda y qué hace.
- Encapsulamiento con tres ejemplos:
  1. `Cama.reservar()`: el estado no se asigna, se cambia con un método que valida.
  2. `SignosVitales`: no se puede crear con una saturación de 150 %.
  3. `Triaje.reclasificar()`: exige una justificación de 10 caracteres.
- Los atributos empiezan con `_` (protegidos) y se leen con `@property`. No hay *setters*.

**Preguntas probables:**

| Pregunta | Respuesta corta |
|---|---|
| ¿Qué es encapsulamiento? | Que el objeto protege sus datos: solo se cambian por sus métodos, que validan |
| ¿Qué pasa si escribo `cama.estado = "OCUPADA"`? | Error (`AttributeError`): la propiedad es de solo lectura |
| ¿Por qué `_estado` y no `__estado`? | Con un guion es la convención de Python para «protegido». Las clases hijas lo necesitan; con dos guiones no lo verían fácilmente |
| ¿Qué es `@property`? | Permite leer `cama.estado` como un atributo, pero por dentro es un método: se controla el acceso |
| ¿Dónde se valida el DNI? | En `DocumentoIdentidad`: 8 dígitos exactos. Si no, `ValueError` |
| ¿Qué diferencia hay entre `ValueError` y `SigtacError`? | `ValueError`: el dato está mal escrito. `SigtacError`: el dato es válido, pero rompe una regla de negocio |
| ¿Por qué `Paciente` y `EpisodioEmergencia` son clases distintas? | El paciente es la persona; el episodio es una visita. Un paciente tiene muchos episodios |

---

## Percy Malpartida — Herencia, polimorfismo y el algoritmo de triaje

**Expone:** las relaciones entre clases (criterio 4).

**Archivos:** `models/cama.py`, `models/estrategias.py`, `models/asignacion.py`, `controllers/cama_controller.py`
(método `asignar`).

**Qué explica:**

- **Herencia:** `Cama` es abstracta y tiene 4 hijas. `Persona` → `Paciente` y `Empleado` → `Enfermero`, `Medico`, `PersonalLimpieza`.
- **Polimorfismo:** `es_compatible(nivel)` responde distinto en cada tipo de cama:
  Trauma Shock solo nivel 1; UCI 1 y 2; Observación 2, 3 y 4; Hospitalización 3, 4 y 5.
- **Strategy:** `EstrategiaTriaje` tiene dos implementaciones, `ReglaManchester` y `ReglaMINSA`. El controlador
  recibe una y no sabe cuál es.
- **Composición:** un episodio contiene sus triajes y sus signos. **Asociación:** `AsignacionCama` une un episodio con una cama.
- **Colaboración:** el método `asignar`, paso a paso ([CRITERIOS.md](CRITERIOS.md), criterio 4).

**Preguntas probables:**

| Pregunta | Respuesta corta |
|---|---|
| ¿Qué es polimorfismo? | El mismo mensaje (`es_compatible`) y cada objeto responde a su manera |
| ¿Por qué `Cama` es abstracta? | Porque no existe una «cama genérica»: siempre es de un tipo. Python no deja crear `Cama()` |
| ¿Cómo agregarían una cama pediátrica? | Una clase nueva que herede de `Cama` con su `es_compatible`, y una fila en el catálogo. El controlador no cambia |
| ¿Cómo decide el nivel la regla de Manchester? | Suma el peso de los síntomas y mira dos signos. Nivel 1 si el peso es ≥ 10, la saturación < 90 % o la presión sistólica < 80 |
| ¿Cómo agregarían otro algoritmo de triaje? | Una clase nueva que herede de `EstrategiaTriaje`. No se tocan las existentes |
| ¿Diferencia entre herencia y composición? | Herencia: «es un» (una cama UCI es una cama). Composición: «tiene un» (un episodio tiene triajes) |
| ¿El algoritmo es clínicamente válido? | No. Es una simulación para el curso; el profesional confirma o reclasifica |

---

## Preguntas difíciles para cualquiera

| Pregunta | Respuesta honesta |
|---|---|
| ¿Usaron inteligencia artificial? | Sí, como apoyo para revisar y documentar. Por eso cada uno estudió su parte y puede explicarla |
| ¿Por qué casi todos los commits son de una persona? | Favio integró el trabajo en el repositorio. El reparto por integrante es el de la matriz de responsabilidades del informe |
| ¿Qué falta? | Que cada usuario cambie su propia clave (hoy lo hace el administrador) y probarlo con varias PCs a la vez |
| ¿Sirve para un hospital real? | No todavía: las reglas de triaje no están validadas clínicamente |

> Favio: las dos primeras respuestas las decide el equipo. Lo importante es que **todos respondan lo mismo**
> y que sea verdad.
