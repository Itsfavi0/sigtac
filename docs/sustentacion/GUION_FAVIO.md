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
| 27–30 | Criterio 7: organización | Leonardo | Escuchas y vigilas |
| 30–34 | Criterio 8: decisiones | **Tú** | Hablas |
| 34–36 | Aportes y cierre | Renzo | Escuchas y vigilas |
| 36 → | Preguntas | **Tú diriges** | Das la palabra al dueño del tema |

---

## 3. Bloque por bloque

### 0–2 · Tú · Problema y solución

**Dices (en este orden):**
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

### 27–30 · Leonardo · Criterio 7: organización del código

**Debe decir:**
- Capas: `views → controllers → models → dao → MySQL`; las dependencias van solo hacia abajo.
- Seguir una operación por las 4 capas: `triage_view.py` → `TriajeController.registrar()` → `Triaje.reclasificar()` → `TriajeDAO`.
- `views/tema.py` es el único archivo con colores y letras; `views/componentes/` reúne lo reutilizable.
- Nombres en español que dicen lo que hacen (`cama.reservar()`, `episodio.dar_alta()`, `exigir_permiso()`).

**Alarmas:**
- «Las pantallas validan los datos.» → falso: valida el **modelo**; la pantalla solo muestra el error.
- «Las pantallas llaman al DAO.» → falso: `test_capas.py` lo impide.

**Rescate:** «La pantalla solo muestra: recibe su controlador y lo que este le devuelve. El controlador comprueba el permiso y abre
la transacción; el modelo aplica la regla; el DAO guarda. Cada capa solo conoce la de abajo.»

---

### 30–34 · Tú · Criterio 8: «por qué esto y no esto»

Cada decisión con la fórmula: **dónde → por qué → qué se descartó → qué costó.**

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
| Pantallas, tema, roles en el menú | Leonardo |
| Arquitectura, decisiones, seguridad, IA, commits | Tú |

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
