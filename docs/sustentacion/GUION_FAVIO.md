# Guion de Favio: el que audita

Tu papel hoy: **abrir, manejar la demo, y estar atento a todo lo demás**. Si alguien se queda en blanco o dice algo
incorrecto, tú completas. Este archivo es solo para ti: [GUION_EXPOSICION.md](GUION_EXPOSICION.md) tiene los tiempos
de todos y [PREGUNTAS_PROFESOR.md](PREGUNTAS_PROFESOR.md) las respuestas largas.

---

## 1. Reglas para intervenir (léelas antes de entrar)

El riesgo de interrumpir demasiado es que parezca que los demás no dominan su parte, y el criterio 8 pide
justamente que cada uno pueda explicar la suya. Por eso:

| Situación | Qué haces |
|---|---|
| El compañero se queda callado **más de 5 segundos** | Intervienes con la frase de rescate del bloque. Cuenta mentalmente: 1… 5 |
| El compañero dice algo **falso o que te perjudica** (ver «Alarmas» de cada bloque) | Intervienes en cuanto termine la frase, no a la mitad |
| Se equivoca en un detalle menor (una cifra, el nombre de un archivo) | **No interrumpes.** Si importa, lo corriges al terminar el bloque, de pasada |
| Está explicando bien pero lento o con otras palabras | No intervienes |
| Está explicando bien y tú «quieres agregar» algo | **No.** Anótalo para las preguntas |
| Es la demo y alguien está escribiendo | No hablas ni intervienes: espera a que termine |

**Máximo, dos intervenciones por bloque.** Si ya hiciste dos, el resto lo anotas y lo dices en las preguntas.

### Frases para interrumpir sin dejar mal al compañero

Siempre «complemento», nunca «corrijo». Y siempre le devuelves la palabra por su nombre.

- «Si me permiten complementar a Ian…» → dices el dato → «…Ian, sigue».
- «Perdón, para precisar un punto…» → dices el dato → «…continúa, Percy».
- Cuando está bloqueado: «Lo ayudo con esto: …» → dices **una** idea corta → «…¿Leonardo?» (se la devuelves).
- Si el error es grave y ya lo dijo: «Una precisión, para ser exactos: …». Dilo sereno; el profesor valora la honestidad.

### Lo que **nunca** haces
- Contradecir a un compañero con tono de reproche delante del profesor.
- Inventar un dato para tapar un hueco. Si no lo sabes: «eso lo confirmamos y lo respondemos con precisión».
- Responder tú todas las preguntas: el profesor evalúa a cada integrante. Primero responde el dueño del tema.

---

## 2. Mapa de la exposición (tu guion)

| Min | Bloque | Quién | Tú haces |
|---|---|---|---|
| 0–2 | Problema y solución | **Tú** | Hablas |
| 2–5 | Criterio 1: observación anterior | Renzo | Escuchas y vigilas |
| 5–9 | Criterio 2: clases | Ian | Escuchas y vigilas |
| 9–12 | Criterio 3: encapsulamiento | Ian | Escuchas y vigilas |
| 12–18 | Criterio 4: relaciones | Percy | Escuchas y vigilas (el más delicado) |
| 18–27 | Demo | **Tú manejas**, Leonardo explica | Manejas, sin hablar mientras escribes |
| 27–30 | Criterio 7: organización del código | **Tú** | Hablas |
| 30–34 | Criterio 8: decisiones | **Tú** | Hablas (sigues sin pausa: son 7 minutos tuyos, del 27 al 34) |
| 34–36 | Aportes y cierre | Renzo | Escuchas y vigilas |
| 36 → | Preguntas | **Tú diriges** | Das la palabra al dueño del tema |

---

## 3. Bloque por bloque

### 0–2 · Tú · Problema y solución

> Texto para leer en voz alta 2 o 3 veces y decir con tus palabras. Lo que **sí** debe salir exacto está en **negrita**.

**Texto sugerido (2 min)**

«Buenos días, profesor. Somos Favio Brañez, Renzo Moya, Leonardo Veliz, Ian Sevillano y Percy Malpartida, del curso
Programación Orientada a Objetos II. Presentamos **SIGTAC: Sistema Integrado de Gestión de Triaje y Asignación de Camas.**

El problema es este: **en una emergencia no se atiende por orden de llegada, sino por gravedad.** Y en muchos servicios, la cama
se busca por teléfono y el estado de cada cama está en una pizarra. Eso genera demoras y errores, por ejemplo, ofrecer una cama
que ya estaba ocupada.

SIGTAC junta en un solo sistema el **triaje**, es decir, la clasificación de la prioridad del paciente, y la **asignación de
camas**. Maneja cinco roles, cada uno con sus permisos; guarda todo en una base de datos MySQL y deja una bitácora de quién
hizo qué.

Una aclaración importante: **es un prototipo académico.** El nivel de triaje que calcula el sistema es una sugerencia, no está
validado clínicamente, y el profesional siempre decide.

Vamos a seguir sus ocho criterios en orden: la observación de la primera presentación, las clases, el encapsulamiento, las
relaciones entre clases, el avance funcional con una demostración en vivo, la validación de datos, la organización del código y,
al final, las decisiones técnicas. Empieza Renzo con la observación que usted nos hizo.»

**Puntos clave (por si pierdes el hilo):**
1. «Buenos días, profesor. Somos [nombres]. Presentamos SIGTAC: Sistema Integrado de Gestión de Triaje y Asignación de Camas.»
2. «En una emergencia se atiende por **gravedad, no por orden de llegada**. Hoy, la cama se busca por teléfono y el estado
   está en una pizarra.»
3. «SIGTAC junta el triaje y las camas en un mismo sistema, con roles y bitácora.»
4. «Aclaración honesta: es un **prototipo académico**; el triaje es una **sugerencia** y el profesional decide.»
5. «Vamos a seguir sus 8 criterios en orden. Al final hay una demostración en vivo y las decisiones técnicas.»

**Transición:** «Renzo empieza con la observación que nos hizo en la primera presentación.»

---

### 2–5 · Renzo · Criterio 1: la observación anterior

**Debe decir:**
- La observación: «¿cómo migrarían a otro motor de base de datos?» → **atendida**.
- Todo el acceso a datos está en `dao/`; MySQL se importa en **3 archivos** (`base_dao.py`, `db_connection.py`, `transaccion.py`).
- Una prueba automática (`tests/test_capas.py`) falla si otra capa importa `dao` o `mysql`.
- Qué no cambia: `views` (6 679 líneas), `controllers` (1 127), `models` (1 368). Sí cambia `dao` (1 853).
- Honestidad: no es «cambiar una línea» (hay SQL propio de MySQL en una docena de consultas) y la migración **no se ejecutó**.

**Alarmas (interrumpes si dice):**
- «Solo cambiamos una línea / el motor es intercambiable al instante.» → «Precisión: el trabajo está concentrado en `dao/`, no es de una línea.»
- «Ya migramos a [otro motor].» → es falso: «No se ha ejecutado; lo que está comprobado es el aislamiento.»

**Rescate (20 s):** «La respuesta es que solo se toca la carpeta `dao/`. Los modelos, controladores y pantallas no saben que
existe MySQL, y hay una prueba automática que lo exige. Lo que no hicimos es ejecutar la migración: lo probado es el aislamiento.»

---

### 5–9 · Ian · Criterio 2: clases principales

**Debe decir (por cada clase: qué representa, qué guarda, qué hace):**
`Persona` (abstracta) → `Paciente` y `Empleado` (+ `Enfermero`, `Medico`, `PersonalLimpieza`) → `DocumentoIdentidad` →
`EpisodioEmergencia` → `Triaje` → `SignosVitales` → `Cama` (+ 4 tipos) → `EstrategiaTriaje` → `CuentaUsuario`.

**Frase clave:** «El paciente es la persona; el episodio es una visita. Por eso son dos clases.»

**Alarmas:**
- Confundir `Paciente` con `EpisodioEmergencia` (decir que el paciente «tiene la cama»): la cama la tiene el **episodio** (vía `AsignacionCama`).
- Decir que `Persona` se puede instanciar: es **abstracta**.

**Rescate:** «`EpisodioEmergencia` es la visita: guarda el motivo, el estado, sus triajes y signos, y sabe asignar cama, dar de
alta o referir. `Paciente` solo es la persona. Un paciente puede tener muchas visitas.»

---

### 9–12 · Ian · Criterio 3: encapsulamiento

**Debe decir (3 ejemplos):**
1. `Cama._estado` solo se lee con `@property`; cambia por `reservar()`, `ocupar()`, `dar_alta()`, `liberar_limpieza()`, que validan.
   «`cama.estado = "OCUPADA"` da `AttributeError`.»
2. `SignosVitales`: no se puede crear una saturación de 150 %; se valida al crearse.
3. `Triaje.reclasificar()`: mínimo 10 caracteres de justificación (RN-10).

**Alarmas:**
- «`_estado` es privado de verdad.» → «Precisión: en Python es una **convención** (protegido), no una barrera.»
- «`__estado`» (dos guiones): en el código es `_estado`, uno.

**Rescate:** «El estado de la cama no se asigna: se pide. Solo se cambia con un método con nombre de acción, y cada uno
comprueba que la transición sea válida; una cama ocupada no se puede reservar.»

---

### 12–18 · Percy · Criterio 4: relaciones entre clases  *(el bloque más delicado)*

**Debe decir:**
- **Herencia:** `Cama` abstracta con 4 hijas; `Persona` → `Paciente`/`Empleado` → 3 hijas.
- **Polimorfismo:** `es_compatible(nivel)`: Trauma Shock solo 1; UCI 1–2; Observación 2–4; Hospitalización 3–5.
  Muestra que `cama_controller.py:74` **no pregunta el tipo**.
- **Strategy:** `EstrategiaTriaje` con `ReglaManchester` y `ReglaMINSA`.
- **Composición:** el episodio contiene triajes y signos. **Asociación:** `AsignacionCama`.
- **Colaboración:** `asignar`: permiso → transacción → episodio valida triaje → cama valida compatibilidad y estado → DAO guardan → bitácora.

**Alarmas (aquí interrumpes con más cuidado, pero sí):**
- Usa **`obtener_resumen()`** como ejemplo de polimorfismo → «Precisión: ese está implementado y probado, pero ninguna pantalla lo
  llama todavía. El ejemplo que se ejecuta en la aplicación es `es_compatible`.»
- Dice que se puede **elegir** `ReglaMINSA` en la aplicación → «Precisión: está implementada y probada, pero no hay selector;
  el controlador usa Manchester por defecto.»
- Dice que el controlador pregunta el tipo de cama → falso: usa `cama.es_compatible(nivel)` sin preguntar.
- Dice que Trauma Shock acepta nivel 2 → falso: **solo nivel 1**.

**Rescate (polimorfismo):** «El controlador filtra camas con `cama.es_compatible(nivel)` sin saber de qué tipo es cada una;
cada tipo responde distinto. Si mañana hay una cama pediátrica, se crea una clase y esa línea no se toca.»

---

### 18–27 · La demo · Tú manejas, Leonardo explica

Sigue [GUION_DEMO.md](GUION_DEMO.md). **No hablas mientras escribes.** Si algo falla, **no insistas**.

| Paso | Qué haces | Si falla |
|---|---|---|
| 1–2 | Login con clave equivocada y luego correcto (DNI 22222222) | «Sin conexión»: abre `python -m prototipo.ver` y di «usamos los datos de demostración» |
| 3 | Triaje → DNI 45678912 → registrarlo | «Ya existe»: usa el DNI 45678913 |
| 4 | PA 95 / 150 (al revés) | Es el rechazo 1: debe marcar los dos campos |
| 5 | PA 150 / 95 + síntoma → debe sugerir **nivel 2** | Otro nivel: revisa que los 6 signos estén bien |
| 6 | «Reclasificar», nivel 3, «ok» → «Faltan 8 caracteres» | Rechazo 2 |
| 7 | Cancelar reclasificación → **Confirmar nivel** | — |
| 8 | Gestión de camas → buscar a **Jorge Luis Paredes Vega** | Elige por nombre, no «el primero» (hay 12 en cola) |
| 9 | Asignar cama de Observación → Con cama → **Llegó a la cama** → **Dar de alta** | — |
| 10 | Pacientes → DNI 70123456 → abrir otro episodio | Rechazo 3: «El paciente ya tiene un episodio abierto» |
| 11–12 | Limpieza (DNI 44444444) → elige **la cama del paso 9** (hay 8 solicitudes) | No confundas las camas |
| 13–14 | Administrador (DNI 11111111) → Reportes → PDF → Bitácora | — |
| 15 | Cierra la app, ábrela, busca el DNI 45678912 | Demuestra que persiste en MySQL |

**Qué cubres tú, si Leonardo se queda corto en un paso:** los textos de la columna «Qué se dice» de `GUION_DEMO.md`.

**Alarmas:** que alguien improvise un paso no ensayado, o escriba una clave a la vista.

---

### 27–30 · Tú · Criterio 7: organización del código y estructura de carpetas

> Este bloque antes era de Leonardo; ahora lo expones tú. Leonardo sigue explicando las pantallas **durante la demo**
> (hasta el min 27). Cuando termine el paso 15, tú tomas la palabra y pasas directo a este bloque. El texto largo de su
> versión está en [tarjetas/LEONARDO.md](tarjetas/LEONARDO.md) si quieres compararlo.
> Ten abierto el **árbol de carpetas en el editor** y, para el punto ②, `triage_view.py`, `triaje_controller.py` y `models/triaje.py`.

**Texto sugerido (3 min)**

**① Las capas y por qué cada carpeta existe (60 s)** *(muestra el árbol)*
«Profesor, así está organizado el código. Usamos una **arquitectura en capas**: lo separamos para que **cada carpeta tenga una sola responsabilidad** y para
que un cambio en una no obligue a tocar las demás. Las dependencias van **solo hacia abajo**: `views` → `controllers` →
`models` → `dao` → MySQL.

`views` es solo la interfaz: nunca tiene SQL ni reglas. `controllers` son los casos de uso: comprueban el permiso del rol,
abren la transacción y coordinan. `models` son las clases y las **reglas de negocio**; no saben que existe una base de
datos. Y `dao` es **el único lugar con SQL**. Además: `utils` para lo compartido, como las contraseñas con bcrypt y el PDF;
`db_scripts` para reconstruir la base desde cero; y `tests`, con un archivo de pruebas por módulo. El criterio que seguimos es
**una regla, un dueño**: no repetimos una regla en dos capas.»

**② Seguir una operación por las cuatro capas (60 s)** *(opcional: abre los archivos)*
«Lo vemos con la reclasificación que acabamos de hacer en la demo. La pantalla, `triage_view`, recoge lo que escribió el
usuario. El controlador, `TriajeController.registrar`, comprueba el permiso, abre la transacción y **recalcula el nivel sugerido
él mismo**, no lo recibe de la pantalla, para que "sugerido" sea siempre lo que dijo el algoritmo. El modelo,
`Triaje.reclasificar`, aplica la regla de los 10 caracteres. Y el DAO, `TriajeDAO`, guarda en MySQL. Si algo falla en
cualquier paso, se deshace todo.»

**③ Cómo comprobamos que se respeta (25 s)**
«Esto no depende de que nos acordemos: hay una prueba automática, `tests/test_capas.py`, que **falla si una pantalla importa
`dao` o `mysql`**. Por eso la respuesta a la observación de la primera presentación es verificable.»

**④ Los controladores: el patrón de cada operación (50 s)** *(abre `controllers/cama_controller.py`, método `asignar`, línea 103)*
«Nadie ha hablado todavía de los controladores, y son la capa que une todo. Tenemos seis: autenticación, pacientes, triaje, camas,
reportes y administración; unas 1 100 líneas en total. Cada uno recibe **la sesión del usuario cuando se crea**, no una variable
global, y **toda operación que escribe sigue el mismo patrón**, que se ve en `asignar`: primero **`exigir_permiso`**, que
comprueba que el rol puede hacerlo; después abre **`with transaccion()`**; dentro, carga los datos, le pide al **modelo** que aplique
la regla (`episodio.asignar_cama()`, `cama.reservar()`), le pide al **DAO** que guarde y **registra la auditoría**. Si algo falla,
la transacción se deshace entera. Y el controlador **no captura los errores**: suben a la pantalla, que sabe cómo mostrarlos. El
controlador no decide ninguna regla; solo coordina.»

**⑤ Orden y nombres (20 s)**
«Los colores, letras y medidas salen de un solo archivo, `views/tema.py`, y las piezas que se repiten están en `views/componentes`.
Los nombres están en español y dicen lo que hacen: `cama.reservar()`, `episodio.dar_alta()`, `exigir_permiso()`. Son unas 11 400
líneas de aplicación y unas 13 000 de pruebas. Con esto cerramos la organización del código; ahora explico las decisiones técnicas.»

**Puntos clave (por si pierdes el hilo):**
1. **Arquitectura en capas** (cuatro, más MySQL), dependencias solo hacia abajo: `views → controllers → models → dao → MySQL`.
2. **Una carpeta, una responsabilidad:** vistas muestran, controladores coordinan y dan permiso, modelos deciden, DAO guarda.
3. **Una regla, un dueño:** no se repite una regla en dos capas.
4. **Se comprueba:** `tests/test_capas.py`.
5. **Ejemplo:** la reclasificación (`triage_view` → `TriajeController.registrar` → `Triaje.reclasificar` → `TriajeDAO`).
6. **Controladores (6):** reciben la `Sesion`; cada operación = `exigir_permiso` → `with transaccion():` → el modelo aplica la regla → el DAO guarda → auditoría. No capturan errores y no deciden reglas.

**Transición:** «Ahora explico las decisiones técnicas: qué elegimos, qué descartamos y qué nos costó.» *(sigues con el bloque 30–34)*

#### Para qué sirve cada carpeta (si te piden «explícame esa estructura»)

| Carpeta | Qué hay | Por qué está separada |
|---|---|---|
| `views/` | Pantallas CustomTkinter, `tema.py`, `componentes/` | Solo interfaz. Si cambia el diseño, la lógica no se toca |
| `controllers/` | `auth`, `paciente`, `triaje`, `cama`, `reporte`, `admin` | Un caso de uso por operación; aquí se comprueban los permisos por rol y se abre la transacción |
| `models/` | Clases de dominio, estados, permisos, estrategias, excepciones | Las reglas de negocio, que se prueban sin MySQL ni ventana |
| `dao/` | `db_connection.py`, `base_dao.py`, `transaccion.py`, un `*_dao.py` por entidad | Único lugar con SQL; si cambia el motor, solo se toca aquí |
| `utils/` | bcrypt, logging, PDF, colores | Herramientas compartidas que no son dominio |
| `db_scripts/` | `schema.sql`, `seed.sql`, usuario de la app | La base se reconstruye desde cero |
| `tests/` | Un `test_*.py` por módulo, `conftest.py` | Cada capa se prueba aislada, con dobles de la de abajo |
| `prototipo/` | Datos de demostración (`python -m prototipo.ver`) | Plan B de la demo: abre la aplicación sin MySQL |

#### Preguntas que pueden venir sobre arquitectura y estructura

Las respuestas completas están en [PREGUNTAS_PROFESOR.md](PREGUNTAS_PROFESOR.md) (sección B). Esto es para contestar en 20–30 segundos.

| Pregunta | Qué respondes | Dónde |
|---|---|---|
| «¿Qué arquitectura es? ¿MVC?» | **Arquitectura en capas** (4 niveles + MySQL) con el patrón DAO. Se parece a MVC en separar interfaz, control y modelo, pero no es MVC puro: la vista no observa al modelo, el controlador es un caso de uso (permiso, transacción, coordinación) y hay una capa DAO aparte para el SQL. Ver el recuadro de abajo | B1 |
| «¿Por qué esas carpetas / por qué 4 capas?» | Cada capa tiene un motivo de cambio distinto: la interfaz, los casos de uso, las reglas y el SQL. Una responsabilidad por carpeta. **Costó:** más archivos y pasar datos de una capa a otra | B1 |
| «¿Por qué no pones el SQL en la pantalla, que es más rápido?» | Más rápido de escribir, pero no se puede probar sin abrir una ventana y la misma regla acabaría copiada en varias pantallas | B2 |
| «¿Qué hace un controlador?» | Es un caso de uso: comprueba el permiso del rol, abre la transacción y coordina modelos y DAO; no decide ninguna regla. Seis controladores, uno por área | B2 |
| «¿Dónde se comprueban los permisos?» | En el controlador, al inicio de cada operación, con `exigir_permiso(sesion, Permiso.X)`. La matriz rol → permisos está solo en `models/permisos.py` | B7 |
| «¿Por qué el controlador recibe la `Sesion` y no usa una variable global?» | Para que cada controlador sepa quién opera (permisos y auditoría) sin estado global; se cierra la sesión y el controlador deja de poder operar. También facilita las pruebas | B2 |
| «¿Por qué el controlador no captura las excepciones?» | No sabría qué hacer con ellas; suben a la pantalla, que muestra el mensaje y marca el campo. Nunca se usa `except Exception` | E2 |
| «¿Por qué un controlador entre la pantalla y el DAO?» | La pantalla solo muestra; el controlador comprueba el permiso, abre la transacción y coordina. Si mañana hay una versión web, los controladores sirven igual | B2 |
| «¿Cómo demuestran que se respeta la separación?» | `tests/test_capas.py` falla si `views/` o `main.py` importan `dao` o `mysql` | B1 |
| «¿Y si cambian de motor de base de datos?» | Solo se toca `dao/`; MySQL se importa en 3 archivos. **Honestidad:** hay SQL propio de MySQL en una docena de consultas y la migración **no se ejecutó**; lo probado es el aislamiento | B6, criterio 1 |
| «¿Por qué las reglas están en `models/` y no en el DAO o en la BD?» | El modelo es el dueño de la regla y se prueba sin BD. El DAO solo guarda. Algunas reglas críticas viven **también** en la BD (`UNIQUE`, `CHECK`) como último respaldo | B3, C4 |
| «¿Por qué `models/` no puede importar `dao/`?» | Si importara, las reglas dependerían de la base de datos y ya no se podrían probar solas. Por ejemplo, la compatibilidad cama–nivel es `Cama.es_compatible()` y no una consulta | B3 |
| «¿Dónde validan los datos?» | En el modelo (`ValueError` si el dato está mal escrito; `SigtacError` si se viola una regla). La pantalla solo pregunta y muestra el error. El permiso lo comprueba el controlador | E3 |
| «¿Qué patrones usaron y por qué?» | **DAO** (aísla el SQL), **Strategy** (`ReglaManchester`/`ReglaMINSA` intercambiables) y **Singleton** (`ConexionBD`, una sola conexión). **Costó:** el Singleton es estado global y dificulta las pruebas | A6, B5 |
| «¿Por qué DAO con métodos estáticos?» | Un DAO no guarda estado. **Costó:** es más difícil reemplazarlo; las pruebas usan `monkeypatch`. Con más tiempo se inyectarían | B4 |
| «¿Por qué no usaron un ORM?» | El curso pide entender el SQL y el patrón DAO. Con un ORM se pierde de vista qué consulta se ejecuta | B6 |
| «¿Cómo se agrega un rol o un módulo nuevo?» | Un valor en `Rol` y sus permisos en `models/permisos.py`; una entrada en `PANTALLAS` de `views/app_principal.py`. El menú se arma solo con los permisos de la sesión | B7 |
| «Muéstrame una operación completa» | La reclasificación: `triage_view` → `TriajeController.registrar` → `Triaje.reclasificar` → `TriajeDAO`. O la asignación de cama (permiso → transacción → modelos validan → DAO guarda → bitácora; si otra PC llegó primero, `rowcount` es 0 y se hace `ROLLBACK`) | C2 |

**Si preguntan «¿entonces es MVC o no?»** *(respuesta de 15 segundos)*

> «Usamos una **arquitectura en capas** de cuatro niveles: presentación, casos de uso, dominio y acceso a datos. Se parece a MVC en que
> separa interfaz, control y modelo, pero agregamos una capa DAO para aislar el SQL y las dependencias van solo hacia abajo, lo que se
> comprueba con una prueba automática. **Es MVC en espíritu, con una capa de persistencia explícita; el nombre más exacto es
> arquitectura en capas.**»

| Capa | Carpeta | Cómo se le llama |
|---|---|---|
| Presentación | `views/` | La «V» de MVC |
| Aplicación (casos de uso) | `controllers/` | Parecida a la «C», pero es un caso de uso: no recibe eventos, los coordina |
| Dominio | `models/` | La «M» de MVC, **sin** persistencia |
| Persistencia | `dao/` | No existe en MVC; patrón DAO |

Diferencias que puedes nombrar si insisten: en MVC clásico la vista **observa** al modelo y se actualiza sola; aquí la vista le pide los
datos al controlador y los muestra. Y MVC no exige que las dependencias vayan solo hacia abajo; aquí sí, y `tests/test_capas.py` lo comprueba.

**No digas:** «es MVC» a secas (te harán notar que no hay observador y que el DAO no encaja); «hexagonal» o «Clean» (el dominio no define
puertos ni interfaces de persistencia); «microservicios» ni «cliente–servidor» (es una aplicación de escritorio; varias PCs comparten MySQL).

**Si insisten en las debilidades, admite con calma:**
- Filtrar las camas compatibles en Python y no en SQL no escala a miles de camas; con decenas no se nota.
- La separación en capas añade archivos y pasos de más para una pantalla sencilla.
- El Singleton es estado global; se mitigó en las pruebas, pero un *pool* de conexiones sería mejor.

**No digas:** «las pantallas validan» (valida el modelo), «las pantallas llaman al DAO» (`test_capas.py` lo impide) ni
«el motor es intercambiable al instante» (el trabajo está concentrado en `dao/`, no es de una línea).

---

### 30–34 · Tú · Criterio 8: «por qué esto y no esto»

Cada decisión con la fórmula: **dónde → por qué → qué se descartó → qué costó.**

**Texto sugerido (4 min)**

«Para el último criterio, la sustentación técnica, queremos explicar **cuatro decisiones** y, en cada una, qué alternativa
descartamos y qué nos costó, porque ninguna decisión es gratis.

**Primera, y la principal: ¿qué camas sirven para un paciente de nivel 2?** Nuestra primera idea fue una columna `nivel_min` en
la tabla de tipos de cama y un filtro en SQL. La descartamos porque **un solo número no alcanza**: Observación acepta los niveles
2, 3 y 4, y Hospitalización los 3, 4 y 5; no es "de tal nivel en adelante". Además, la regla quedaba escrita dos veces, en SQL y
en Python, y podían contradecirse. Entonces la dejamos en **un solo lugar: el método `es_compatible` de cada cama**. El DAO trae
las camas disponibles y cada una responde por sí misma. Lo que nos costó: se filtra en Python y no en la base de datos. Con las
decenas de camas de una emergencia no se nota; con miles, habría que revisarlo.

**Segunda: la concurrencia.** ¿Qué pasa si dos computadoras asignan la misma cama? Usamos un **`UPDATE` condicional**: la cama
solo cambia si sigue en el estado que esperábamos, y comprobamos cuántas filas cambió. Si fueron cero, otro llegó primero: se
lanza una excepción y se deshace toda la transacción. Descartamos leer y luego escribir sin condición, porque la segunda
computadora pisaría a la primera. Lo que nos costó: la segunda computadora recibe un error y debe volver a consultar; para una
guardia es aceptable.

**Tercera: separamos el rol del cargo.** El cargo es un dato laboral, como médico o enfermera; el rol es un permiso del software,
como jefe de guardia. Un médico puede ser jefe de guardia; si los uniéramos, tendríamos que duplicar cargos. Por eso los permisos
dependen solo del rol, y la tabla de permisos está en un único archivo, `models/permisos.py`.

**Cuarta: no borramos registros; usamos baja lógica**, con `estado_registro` en falso. Es la regla RN-11. Así conservamos el
historial para auditoría y no rompemos claves foráneas. Además, la cuenta con la que se conecta la aplicación solo tiene
`SELECT`, `INSERT` y `UPDATE`: ni siquiera puede borrar. Lo que nos costó: cada consulta debe filtrar los registros activos.

Y para cerrar, con honestidad, **lo que no hicimos**: `ReglaMINSA` está implementada y probada, pero la aplicación no tiene un
selector para elegirla; la migración a otro motor de base de datos no se ejecutó, solo se comprobó el aislamiento; y el triaje
no está validado clínicamente, es una simulación didáctica.

Cada integrante explicó su contribución. Quedamos atentos a sus preguntas; responderá quien expuso el tema.»

**Puntos clave (por si pierdes el hilo):**

1. **Compatibilidad con polimorfismo y no en SQL.** `Cama.es_compatible()`. Se descartó una columna `nivel_min`: un solo número no
   alcanza (Observación acepta 2, 3 y 4) y la regla quedaba escrita dos veces. Costó: se filtra en Python; con miles de camas habría que revisarlo.
2. **`UPDATE` condicional contra la concurrencia.** `CamaDAO.cambiar_estado`: `WHERE id = %s AND estado = <esperado>` y se comprueba
   `rowcount`. Si otra PC llegó primero, 0 filas → excepción → ROLLBACK. Costó: la segunda PC recibe un error y debe reintentar.
3. **Rol separado de cargo.** El cargo es laboral; el rol es un permiso del software. Un médico puede ser jefe de guardia.
4. **Baja lógica y no borrar (RN-11).** `estado_registro = FALSE`; además `sigtac_app` solo tiene `SELECT, INSERT, UPDATE`. Costó: cada
   consulta debe filtrar los registros activos.

**Cierre:** «Cada integrante explicó su contribución. Las preguntas que sigan las responde quien expuso el tema.»

---

### 34–36 · Renzo · Aportes adicionales

**Debe declarar:** MySQL (22 tablas y transacciones), reporte PDF, búsqueda, 5 roles y permisos, bitácora, bcrypt, 2 332 pruebas
(2 331 pasan y 1 se omite fuera de Windows) y modo oscuro. Qué sigue: cada usuario cambia su clave; probarlo con varias PCs; selector de norma.

**Alarma:** «2 332 pruebas pasan.» → «Precisión: 2 331 pasan y 1 se omite porque solo corre en Windows.»

---

## 4. Las preguntas: cómo las diriges

1. Dejas que el profesor termine. Repites la pregunta en una frase si fue larga («¿Dónde aplicaron polimorfismo?»).
2. **Nombras al dueño:** «Percy, ¿quieres responder?». Eso demuestra que cada uno domina lo suyo.
3. Si pasan 5 segundos sin que empiece, **tú contestas**, con la fórmula de 4 partes.
4. Cuando termine, **solo completas si falta algo importante**; no repitas lo que ya dijo.
5. Si la pregunta es sobre el proyecto entero (arquitectura, decisiones, seguridad, IA, «¿quién hizo qué?»), contestas tú directamente.

| Si preguntan por… | Pásale la palabra a… |
|---|---|
| Herencia, polimorfismo, Strategy | Percy |
| Clases, encapsulamiento, excepciones | Ian |
| Base de datos, DAO, transacciones, concurrencia | Renzo |
| Cómo funciona cada pantalla en la demo, roles en el menú | Leonardo |
| Arquitectura, estructura de carpetas, decisiones, seguridad, IA, commits | Tú |

---

## 5. Datos de bolsillo (para completar sin dudar)

| Dato | Valor |
|---|---|
| Capas | `views → controllers → models → dao → MySQL` |
| Líneas | views 6 679 · controllers 1 127 · models 1 368 · dao 1 853 · utils 354 |
| Pruebas | 2 332: 2 331 pasan, 1 se omite (solo corre en Windows) |
| Base de datos | 22 tablas (10 catálogos, 4 maestras, 6 transaccionales, 2 de historial y auditoría); 3FN |
| Seed de la demo | 80 camas, 76 pacientes; cola de triaje 7 · cola de cama 11 · con cama 42 |
| Patrones | **DAO**, **Strategy** (`EstrategiaTriaje`), **Singleton** (`ConexionBD`, `db_connection.py:23`) |
| Compatibilidad cama–nivel | Trauma Shock 1 · UCI 1–2 · Observación 2–4 · Hospitalización 3–5 |
| Manchester | Nivel 1: peso ≥ 10, SatO₂ < 90 % o PA sistólica < 80 · Nivel 2: peso ≥ 7 o sistólica > 180 · Nivel 3: ≥ 4 · Nivel 4: ≥ 1 · si no, 5 |
| Paciente de la demo | DNI 45678912, «Dolor Torácico Opresivo» (peso 8,5) → nivel 2 |
| Reclasificar | Justificación de **10** caracteres como mínimo (RN-10) |
| Seguridad | bcrypt de 12 rondas · 5 intentos fallidos bloquean 15 minutos · `sigtac_app` solo `SELECT, INSERT, UPDATE` |
| Excepciones | `ValueError` = dato mal escrito · `SigtacError` = regla de negocio violada |
| Reglas | RN-01 sin triaje no hay cama · RN-05 solo se reserva una cama disponible · RN-07/08 alta → limpieza → disponible con confirmación · RN-09 historial de triajes · RN-10 justificación · RN-11 baja lógica |
| Cuentas de la demo | 22222222 Jefe de Guardia · 44444444 Limpieza · 11111111 Administrador (clave de desarrollo del `seed.sql`) |

### Lo que NO se aplicó (si lo preguntan, se dice con honestidad)
- **Sobrecarga de métodos:** Python no la tiene; solo parámetros con valor por defecto.
- **Selector de norma de triaje:** `ReglaMINSA` existe y está probada, pero la app no lo ofrece.
- **`obtener_resumen()`:** implementado y probado; ninguna pantalla lo llama todavía.
- **Migración a otro motor de base de datos:** no se ejecutó; lo comprobado es el aislamiento en `dao/`.
- **Validación clínica del triaje:** no existe; es una simulación didáctica.
- **Cambio de clave por cada usuario:** hoy lo hace el administrador.

---

## 6. Antes de entrar

- [ ] Editor abierto con `models/cama.py`, `controllers/cama_controller.py`, `models/estrategias.py`; terminal lista para el `grep` de Renzo.
- [ ] `seed.sql` recargado, MySQL encendido, `python main.py` abre el login. Plan B: `python -m prototipo.ver`.
- [ ] Ventana maximizada, modo claro, sin notificaciones.
- [ ] Los cinco acordaron **la misma respuesta** sobre la IA y los commits ([PREGUNTAS_PROFESOR.md](PREGUNTAS_PROFESOR.md), H1 y H2).
- [ ] Una seña acordada con el equipo para pedir/ceder la palabra (por ejemplo, levantar un poco la mano).
