# Banco de preguntas del profesor

El profesor hace preguntas de tipo **«¿dónde aplicaste X?»** y **«¿por qué hiciste esto y no esto otro?»**.
Este archivo tiene las respuestas, con el archivo y la línea donde se comprueban (revisadas el 21/11/2026; si el
código cambia, las líneas se mueven: buscar por el nombre del método).

## La fórmula de 4 partes

Toda respuesta «técnica» se dice en este orden. Dura 20–30 segundos y siempre suena preparada:

1. **Dónde:** el archivo y el método (se puede abrir en el editor).
2. **Por qué:** el problema que resuelve.
3. **Qué se descartó:** la alternativa y por qué no.
4. **Qué costó:** la limitación. Decirla uno mismo da más confianza que esperar a que la encuentre el profesor.

## Reglas del equipo

- **Responde quien expuso el tema.** Si pasan 3 segundos sin que nadie hable, Favio contesta o completa.
- Si no se sabe: «eso no lo tengo presente; lo que sí sé es…» y se cuenta lo cercano. Nunca inventar.
- Si la pregunta es «¿dónde está X?» y X **no está**, se dice: «no lo aplicamos». Mejor eso que inventar un ejemplo.
- Abrir el código solo si lo piden o si ayuda; no abrir archivos sin saber qué hay en ellos.

| Tema | Responde primero |
|---|---|
| Herencia, polimorfismo, Strategy | Percy |
| Clases, encapsulamiento, excepciones | Ian |
| BD, DAO, transacciones, concurrencia | Renzo |
| Pantallas, tema, roles en el menú | Leonardo |
| Arquitectura, decisiones, seguridad, IA, «¿quién hizo qué?» | Favio |

---

## A. Programación orientada a objetos

### A1. «¿Dónde aplicaste polimorfismo?»  *(la más probable)*

| Dónde se ejecuta de verdad | Archivo |
|---|---|
| `Cama.es_compatible(nivel)`: 4 hijas, cada una responde distinto | `models/cama.py:80` (abstracto), `:100`, `:113`, `:126`, `:139` |
| Quien lo usa sin preguntar el tipo | `controllers/cama_controller.py:74` (listar compatibles) y `:115` (validar al asignar) |
| `EstrategiaTriaje.evaluar()`: `ReglaManchester` y `ReglaMINSA` | `models/estrategias.py:33`, `:77`, `:104`; se inyecta en `controllers/triaje_controller.py:41` |

- **Por qué:** el controlador trabaja con «una cama» sin saber cuál. Agregar una cama pediátrica es una clase nueva y
  una fila en el catálogo; `cama_controller.py:74` no se toca.
- **Qué se descartó:** un `if tipo == "UCI" … elif …` en el controlador, o una columna `nivel_min` en SQL
  (ver [C3](#c3-por-qué-la-compatibilidad-se-filtra-en-python-y-no-en-sql)).
- **Qué costó:** hay un único lugar que sí conoce los tipos concretos: la fábrica `CamaDAO.CLASES_POR_TIPO`
  (`dao/cama_dao.py:26`). Es a propósito: convierte una fila de la BD en la clase correcta y ahí termina.

> **No lo presentes como ejemplo central:** `obtener_resumen()` (`models/persona.py:84` y las hijas). Es polimorfismo
> real en el diseño, pero **ninguna pantalla lo llama todavía**; solo lo usan las pruebas. Si lo mencionan,
> decir: «está implementado y probado; la interfaz aún no lo muestra».

### A2. «¿Dónde aplicaste herencia? ¿Y sobreescritura?»

- **Herencia:** `Persona` → `Paciente`, `Empleado` → `Enfermero`, `Medico`, `PersonalLimpieza` (`models/persona.py:55, 90, 254, 297, 314, 331`);
  `Cama` → 4 tipos (`models/cama.py:91–139`).
- **Sobreescritura:** cada hija redefine `es_compatible`; `Enfermero`, `Medico` y `PersonalLimpieza` redefinen
  `obtener_resumen` y llaman a `super().obtener_resumen()` para reutilizar lo de la clase padre (`persona.py:308, 324, 347`).
- **Qué costó:** la jerarquía de `Empleado` casi no aporta comportamiento (cada hija agrega un dato: área,
  especialidad o turno). Se mantuvo porque el curso pide herencia y porque `Empleado` sí comparte documento y cargo.

### A3. «¿Aplicaste sobrecarga de métodos?»

**No.** Python no tiene sobrecarga como Java. Lo más parecido es el uso de **parámetros con valor por defecto**
(`Cama.__init__(…, estado=ESTADO_DISPONIBLE)`, `TriajeController(sesion, estrategia=None)`). Se dice así, sin forzar un ejemplo.

### A4. «¿Por qué `Cama` y `Persona` son abstractas?»

- **Dónde:** `class Cama(ABC)` (`models/cama.py:6`), `class Persona(ABC)` (`models/persona.py:55`), `EstrategiaTriaje(ABC)` (`estrategias.py:33`).
- **Por qué:** no existe «una cama genérica»: siempre es de un tipo. Con `@abstractmethod`, Python impide `Cama()`
  y obliga a cada hija a implementar `es_compatible`.
- **Qué costó:** nada relevante; solo hay que acordarse de implementar el método en cada hija nueva.

### A5. «¿Dónde aplicaste encapsulamiento? Python no tiene `private`.»

- **Dónde:** `Cama._estado` solo se lee con `@property` y solo cambia con `reservar()`, `ocupar()`, `dar_alta()`,
  `liberar_limpieza()` (`models/cama.py:32–62`), que validan la transición. Igual `SignosVitales` (rangos al crearse,
  `triaje.py:41`) y `Triaje.reclasificar` (justificación ≥ 10, RN-10).
- **Por qué `_estado` y no `__estado`:** en Python un guion bajo es la convención de «protegido». Dos guiones hacen
  *name mangling* (`_Cama__estado`), que complica a las clases hijas sin dar seguridad real.
- **Qué costó:** es una convención, no una barrera: alguien podría escribir `cama._estado = …`. Lo evitamos por
  disciplina y porque las pruebas fallarían; Python confía en el programador.

### A6. «¿Qué es el patrón Strategy y por qué lo usaron? ¿Dónde se usa `ReglaMINSA`?»

- **Dónde:** `EstrategiaTriaje` define `evaluar()` y `justificar()`; `clasificar()` lo da la clase base
  (`estrategias.py:33–76`). Cada regla solo declara sus condiciones y `_decidir()` elige el nivel.
- **Por qué:** el algoritmo de triaje cambia según la norma (Manchester, MINSA). Con Strategy se agrega otra clase y
  no se toca ni el controlador ni las reglas existentes.
- **¿Dónde se usa `ReglaMINSA`?** Está implementada y probada, pero **la aplicación no tiene un selector**: el
  controlador usa `ReglaManchester()` por defecto (`triaje_controller.py:42`). Cambiar de norma es pasar otra
  estrategia al constructor. **No se hizo la pantalla para elegirla.**
- **Qué se descartó:** un `if norma == "manchester"` dentro de `clasificar()`.
- **Qué costó:** la base de pesos y umbrales está en el código, no en la BD; cambiarlos exige tocar Python.

### A7. «¿Diferencia entre herencia y composición? ¿Cuál usaron más?»

- **Herencia = «es un»:** una cama UCI es una cama. **Composición = «tiene un»:** un episodio tiene triajes y signos
  (`EpisodioEmergencia.agregar_triaje`, `models/triaje.py:260`); un triaje tiene síntomas.
- **Se prefirió composición** donde no había «es un»: `Paciente` y `EpisodioEmergencia` no heredan; el episodio *apunta*
  a un paciente. Un paciente tiene muchos episodios.
- **Asociación:** `AsignacionCama` une un episodio con una cama durante un tiempo (`models/asignacion.py:12`).

### A8. «¿Por qué `Paciente` y `EpisodioEmergencia` son clases distintas?»

El paciente es la persona; el episodio es **una visita**. Un paciente puede venir muchas veces, y cada visita tiene
su propio motivo, triajes, cama y alta. Si fuera una sola clase, se repetirían los datos de la persona en cada visita.

### A9. «¿Por qué separaron `rol` de `cargo`?»

El **cargo** es un dato laboral («médico», «enfermera»). El **rol** es un permiso del software («jefe de guardia»).
Un médico puede ser jefe de guardia. Los permisos dependen solo del rol (`models/permisos.py:27`).

---

## B. Arquitectura y diseño

### B1. «¿Por qué 4 capas?»

- **Dónde:** `views → controllers → models → dao → MySQL`; las dependencias van solo hacia abajo.
- **Por qué:** cada capa tiene un motivo de cambio distinto (la interfaz, los casos de uso, las reglas, el SQL).
  Cambiar de motor de BD solo toca `dao/` (criterio 1).
- **Se comprueba:** `tests/test_capas.py` falla si una pantalla importa `dao` o `mysql`.
- **Qué costó:** más archivos y pasar los datos de una capa a otra. Para una pantalla sencilla parece de más.

### B2. «¿Por qué un controlador y no llamar al DAO desde la pantalla?»

La pantalla solo muestra. El controlador comprueba el permiso, abre la transacción y coordina modelos y DAO.
Si mañana hay una versión web, los controladores sirven igual.

### B3. «¿Por qué las reglas están en `models/` y no en el DAO o en la BD?»

- **Dónde:** `cama.reservar()`, `episodio.asignar_cama()`, `Triaje.reclasificar()`.
- **Por qué:** el modelo es el dueño de la regla y se prueba sin BD ni pantalla. El DAO solo guarda el resultado.
- **Qué costó:** hay reglas que viven también en la BD (`UNIQUE`, `CHECK`) → ver [C4](#c4-no-dijeron-que-una-regla-tiene-un-solo-dueño-y-tienen-reglas-en-python-y-en-la-bd).

### B4. «¿Por qué los DAO usan métodos estáticos y no objetos?»

- **Por qué:** un DAO no guarda estado; solo ejecuta consultas con la conexión compartida. Estático es lo más simple.
- **Qué se descartó:** instanciar y pasar el DAO a cada controlador (inyección de dependencias).
- **Qué costó:** es más difícil reemplazar un DAO. Por eso las pruebas usan `monkeypatch` / `MagicMock`
  (fixture `capa_datos` en `tests/conftest.py`). Con más tiempo, se inyectarían.

### B5. «¿Por qué Singleton en la conexión? ¿No es una variable global disfrazada?»

- **Dónde:** `ConexionBD` (`dao/db_connection.py:23–41`): `__new__` devuelve siempre la misma instancia, con un candado
  para que dos hilos no creen dos.
- **Por qué:** una sola conexión compartida; no se abre una por operación.
- **Qué costó:** tiene razón la objeción: es estado global y dificulta las pruebas. Se mitigó con pruebas que reemplazan
  la conexión. Otra opción era un *pool* de conexiones.

### B6. «¿Por qué no usaron un ORM como SQLAlchemy?»

El curso pide entender el SQL y el patrón DAO. Con un ORM, el motor sería casi intercambiable, pero se pierde de
vista qué consulta se ejecuta. **Costo:** hay SQL propio de MySQL en una docena de consultas (`NOW()`, `IF()`,
`LIMIT`, `FOR UPDATE`); migrar exige reescribirlas, todas dentro de `dao/`.

### B7. «¿Cómo se agregaría un rol o un módulo nuevo?»

Un valor en `Rol` y sus permisos en `PERMISOS_POR_ROL` (`models/permisos.py:27`); una entrada en `PANTALLAS`
(`views/app_principal.py:120`). El menú se arma solo con los permisos de la sesión.

---

## C. Base de datos y concurrencia

### C1. «¿Qué es una transacción y dónde la usan?»

- **Dónde:** `with transaccion():` (`dao/transaccion.py:12`). Asignar una cama escribe en cuatro tablas
  (episodio, cama + historial, asignación, auditoría): o se guardan todas (COMMIT) o ninguna (ROLLBACK).
- **Ejemplo:** si se corta la luz a mitad de la asignación, MySQL la deshace; no queda una cama reservada sin paciente.
- **Qué costó:** dentro del bloque las excepciones deben llegar al `with` externo; capturarlas a mitad dejaría datos a medias.

### C2. «¿Qué pasa si dos PCs asignan la misma cama a la vez?»

- **Dónde:** `CamaDAO.cambiar_estado` (`dao/cama_dao.py:79`): `UPDATE … WHERE id = %s AND estado = <esperado>` y se
  comprueba `rowcount`. La segunda PC actualiza 0 filas y se lanza `CamaNoDisponibleError`, que deshace su transacción.
- **Qué se descartó:** leer y luego escribir sin condición (la segunda PC pisaría a la primera) y bloquear siempre con
  `SELECT … FOR UPDATE`.
- **Cuándo sí se bloquea:** si la operación no cambia un estado (abrir un episodio, un segundo triaje) se usa
  `EpisodioDAO.bloquear` / `PacienteDAO.bloquear` (`FOR UPDATE`).
- **Qué costó:** la PC perdedora recibe un error y debe volver a consultar. Para una guardia es aceptable.

### C3. «¿Por qué la compatibilidad se filtra en Python y no en SQL?»  *(la decisión del criterio 8)*

- **Idea inicial:** columna `nivel_min` en `tipo_cama` y un `WHERE`.
- **Por qué se descartó:** un número no alcanza. Observación acepta 2, 3 y 4; Hospitalización 3, 4 y 5: no es «de tal
  nivel en adelante». Además la regla quedaba escrita dos veces y podían contradecirse.
- **Lo que se hizo:** un solo dueño, `Cama.es_compatible`. El DAO trae las camas disponibles y cada una responde.
- **Qué costó:** se filtra en memoria. Con decenas de camas no se nota; con miles habría que revisarlo.

### C4. «¿No dijeron que una regla tiene un solo dueño y tienen reglas en Python **y** en la BD?»

Buena pregunta, y la respuesta es honesta: **tienen propósitos distintos.**

- Python (`cama.reservar()`) da el mensaje claro y rechaza **antes** de tocar la BD.
- La BD (`UNIQUE`, `CHECK`; RN-05 y RN-10) es la **última barrera** cuando dos PCs actúan a la vez y las dos pasaron la
  validación de Python. Sin ella, la concurrencia podría dejar datos inválidos.
- **Qué costó:** hay que mantener ambas; por eso `tests/test_estados_vs_bd.py` compara los valores fijos de Python con
  `seed.sql` y `schema.sql`.

### C5. «¿Por qué baja lógica y no borrar?»

Regla RN-11: se marca `estado_registro = FALSE`. Se conserva el historial para auditoría y no se rompen las claves
foráneas. Además el usuario de la app (`sigtac_app`) solo tiene `SELECT, INSERT, UPDATE`: **ni siquiera puede borrar**.
**Costo:** las tablas crecen y toda consulta debe filtrar `estado_registro = TRUE`.

### C6. «¿Por qué normalizaron? ¿Hasta qué forma?»

Hasta 3FN: 22 tablas (10 catálogos, 4 maestras, 6 transaccionales y 2 de historial y auditoría). Los catálogos
(estado de cama, nivel de triaje, tipo de documento) evitan repetir texto. **Costo:** más `JOIN` en las consultas.

### C7. «¿Cómo evitan la inyección de SQL?»

Todo SQL lleva parámetros: `cursor.execute(sql, (valor,))`, nunca texto concatenado. Si un nombre de columna o un
`ORDER BY` fuera dinámico, se valida contra una lista blanca.

---

## D. Seguridad

### D1. «¿Por qué bcrypt y no SHA-256 o MD5?»

- **Dónde:** `utils/security.py:9–19`, 12 rondas.
- **Por qué:** bcrypt es **lento a propósito** y lleva una sal propia en cada hash; SHA-256 es rápido y un atacante
  probaría miles de millones de claves por segundo.
- **Qué costó:** cada login tarda una fracción de segundo; es el precio de la seguridad.

### D2. «¿Por qué el login no dice si falló el documento o la clave?»

Para no revelar qué cuentas existen. Incluso cuando el documento no existe se ejecuta `simular_verificacion`
(`utils/security.py:46`) para que el tiempo de respuesta sea parecido. Cinco fallos bloquean la cuenta 15 minutos
(`dao/usuario_dao.py:12–13`).

### D3. «¿Y la contraseña del seed, es real?»

No: son claves de desarrollo, solo para local. **Nunca usarlas fuera de local.** El `.env` no se versiona.

---

## E. Errores y validación

### E1. «¿Diferencia entre `ValueError` y `SigtacError`?»

- `ValueError`: el dato está **mal escrito** (saturación de 150 %, DNI de 7 dígitos). Lo detecta el constructor del modelo.
- `SigtacError` y sus hijas (`models/excepciones.py`): el dato es válido pero **rompe una regla de negocio**
  (reservar una cama ocupada, asignar sin triaje).

### E2. «¿Por qué el controlador no captura las excepciones?»

Porque no sabría qué hacer con ellas: quien sabe cómo mostrarlas es la pantalla. Suben hasta la vista, que muestra
el mensaje y marca el campo. Nunca se usa `except Exception`, solo excepciones específicas.

### E3. «¿Dónde validan los datos, en la pantalla o en el modelo?»

En el modelo. La pantalla solo pregunta («¿es válido?») y muestra la respuesta. Por ejemplo, el rango de la saturación
lo lee de `SignosVitales.RANGOS`; no lo escribe ella.

---

## F. Dominio

### F1. «¿Cómo decide el sistema el nivel de triaje? ¿Está validado clínicamente?»

- **Cómo:** `ReglaManchester.evaluar` (`estrategias.py:80`) suma el **peso clínico** de los síntomas y mira dos
  signos (SatO₂ y presión sistólica). Nivel 1 si el peso es ≥ 10, SatO₂ < 90 % o sistólica < 80; nivel 2 si el peso
  es ≥ 7 o la sistólica > 180; y así hasta el 5.
- **Validado:** **no**. Es una simulación didáctica. El sistema **sugiere** y el profesional confirma o reclasifica
  (con justificación escrita). Por eso el nivel sugerido y el final se guardan por separado.

### F2. «¿Qué pasa si falta un signo vital?»

Se lanza `SignosVitalesIncompletosError`: **un dato no medido nunca se asume como normal** (`EstrategiaTriaje._exigir_signos`,
`models/estrategias.py`). Asumir «normal» podría clasificar mal a un paciente grave.

### F3. «¿Qué es RN-01…RN-11?»

Las reglas de negocio numeradas. Las que se ven en la demo: RN-01 (sin triaje no hay cama), RN-05 (solo se reserva una
cama disponible), RN-07/08 (al dar de alta la cama pasa a limpieza y solo vuelve con confirmación), RN-09 (el
historial de triajes se conserva), RN-10 (reclasificar exige justificación), RN-11 (baja lógica).

---

## G. Pruebas

### G1. «¿Cómo prueban sin MySQL?»

Los tests de DAO usan `MagicMock`/`monkeypatch`; los de controladores usan los dobles `capa_datos` y `sesion_de`
(`tests/conftest.py`), que permiten comprobar el **orden** de las llamadas (inicio → escrituras → auditoría → commit/rollback).
Las pantallas se prueban con controladores falsos y una ventana Tk oculta.
Además, `scripts/verificar_controladores.py` recorre el flujo completo contra un MySQL real en una base temporal.

### G2. «¿Cuántas pruebas hay?»

**2 332**: 2 331 pasan y 1 se omite (la omitida solo corre en Windows: `tests/test_cubierta.py:267`, depende de una
función de Windows). Resultado del 21/11/2026 con `python -m pytest`.

---

## H. Equipo y proceso

### H1. «¿Usaron inteligencia artificial?»

> *Respuesta propuesta; el equipo debe confirmarla y decir todos lo mismo.* «Sí, como apoyo para revisar y documentar.
> Cada integrante estudió su parte y puede explicarla.»

### H2. «¿Por qué casi todos los commits son de una persona?»

> *Respuesta propuesta.* «Favio integró el trabajo en el repositorio. El reparto por integrante está en la matriz de
> responsabilidades del informe.»

### H3. «¿Qué falta? ¿Sirve para un hospital real?»

Falta que cada usuario cambie su propia clave (hoy lo hace el administrador), probarlo con varias PCs a la vez y un
selector de norma de triaje. **No sirve todavía para un hospital real:** las reglas de triaje no están validadas
clínicamente.

---

## Las preguntas trampa (para ensayar en voz alta)

Un integrante las hace, otro responde con la fórmula de 4 partes, y Favio audita la respuesta.

1. «Muéstrame dónde aplicaste polimorfismo.» → A1 (abrir `cama_controller.py:74`).
2. «¿Y si agrego una cama pediátrica, qué archivos tocas?» → una clase en `models/cama.py`, una entrada en `CLASES_POR_TIPO`, una fila en el catálogo.
3. «¿Por qué `es_compatible` no está en el DAO?» → es una regla de negocio; el DAO no contiene reglas.
4. «Esa fábrica `CLASES_POR_TIPO`, ¿no es un `if` por tipo disfrazado?» → A1, «qué costó».
5. «¿Por qué `ReglaMINSA` si nadie la usa?» → A6.
6. «Dices que cada regla tiene un dueño, pero hay reglas en la BD.» → C4.
7. «¿Por qué Singleton y no un pool?» → B5.
8. «¿Esto escala a 500 camas?» → C3 (filtrar en Python) y B5 (una sola conexión).
9. «¿Y si la BD se cae a mitad de una operación?» → C1 y `ConexionBDError`.
10. «¿Quién hizo qué?» → cada uno explica su hoja; Favio audita (H2).
