# Tarjeta de Percy

**Tu parte:** Criterio 4, relaciones entre clases (min **12–18**). Es el bloque en el que más preguntas rebuscadas caen.

> **Cómo usar el texto:** está escrito para que no te quedes en blanco. Léelo en voz alta 2 o 3 veces y luego dilo con
> tus palabras. Lo que **sí** debe salir exacto está en **negrita**. Cada párrafo dura unos 30–40 segundos al hablar con calma.

**Antes de entrar:** abre `models/cama.py`, `controllers/cama_controller.py` (en `asignar` y en la línea 74),
`models/estrategias.py` y `models/persona.py`.

---

## Min 12–18 · Texto sugerido

**① Introducción (20 s)**
«Profesor, en este criterio explicamos cómo se relacionan las clases y qué relaciones aplicamos de verdad: herencia,
polimorfismo, composición y asociación. Y al final mostramos cómo varios objetos colaboran en una sola operación.»

**② Herencia (60 s)** *(diagrama)*
«Primero, la **herencia**, que es una relación del tipo "es un". `Cama` es una clase abstracta con cuatro hijas: `CamaTraumaShock`,
`CamaUCI`, `CamaObservacion` y `CamaHospitalizacion`. Todas son camas, pero admiten niveles de urgencia distintos. Y `Persona`
es la base de `Paciente` y de `Empleado`, que a su vez es la base de `Enfermero`, `Medico` y `PersonalLimpieza`. Un enfermero
**es un** empleado y **es una** persona. Las clases base son abstractas porque no existe una cama genérica ni una persona
genérica: siempre son de un tipo, y Python no deja crearlas.»

**③ Polimorfismo (2 min). Es el ejemplo principal** *(muestra las cuatro `es_compatible` en `cama.py`)*
«Ahora, el **polimorfismo**. Todas las camas responden al mismo mensaje, `es_compatible`, que recibe el nivel de triaje del
paciente, pero cada tipo responde distinto. **Trauma Shock acepta solo el nivel 1. UCI acepta los niveles 1 y 2. Observación,
los niveles 2, 3 y 4. Y Hospitalización, los niveles 3, 4 y 5.**» *(abre `cama_controller.py`, línea 74)*
«Y aquí está lo importante: quien lo usa. Esta línea del controlador recorre las camas disponibles y se queda con las que
responden que sí son compatibles. **El controlador nunca pregunta de qué tipo es la cama.** Si mañana se agrega una cama
pediátrica, se crea una clase nueva con su propio `es_compatible` y esta línea no se toca. La misma pregunta se repite en la
línea 115, cuando se valida la asignación.»

**④ Strategy (60 s)** *(muestra `EstrategiaTriaje`)*
«El polimorfismo también aparece en el patrón **Strategy**. `EstrategiaTriaje` es una clase abstracta que define dos métodos,
`evaluar` y `justificar`, y tiene dos implementaciones: `ReglaManchester` y `ReglaMINSA`. El controlador de triaje recibe una
estrategia y no sabe cuál es. Para agregar otro algoritmo, se crea otra clase y no se tocan las existentes. **Queremos ser
claros en algo: `ReglaMINSA` está implementada y probada, pero la aplicación todavía no tiene una pantalla para elegirla; por
defecto usa Manchester.**»

**⑤ Composición y asociación (35 s)**
«En cuanto a la **composición**, que es una relación "tiene un" donde la parte no existe sin el todo: un `EpisodioEmergencia`
contiene sus triajes y sus signos vitales, y cada triaje contiene sus síntomas. Y la **asociación**: `AsignacionCama` une un
episodio con una cama durante un tiempo, pero ninguno contiene al otro.»

**⑥ Colaboración: asignar una cama (90 s)** *(abre `CamaController.asignar`)*
«Veamos cómo colaboran los objetos al asignar una cama; es una sola operación con varios participantes. Primero, la **sesión**
comprueba que el rol del usuario tenga permiso para gestionar camas. Segundo, se abre una **transacción**: todo o nada.
Tercero, el **episodio** comprueba que tenga un triaje, que es la regla RN-01. Cuarto, la **cama** responde si es compatible con
el nivel del paciente; ahí actúa el polimorfismo. Quinto, la cama se reserva, y ella misma valida que esté disponible, la regla
RN-05. Sexto, los **DAO** guardan el episodio, la cama y la asignación. Y séptimo, se registra en la **bitácora** quién lo hizo.
**Si algo falla en cualquier paso, la transacción deshace todo.** Cada objeto decide lo suyo; el controlador solo los coordina.
Ahora vemos todo esto funcionando: Favio maneja la demostración.»

---

## No digas / di

| No digas | Di |
|---|---|
| «Polimorfismo: `obtener_resumen()`» como ejemplo principal | «`es_compatible`». `obtener_resumen()` está implementado y probado, pero **ninguna pantalla lo llama** |
| «Se puede elegir MINSA en la aplicación» | «Está implementada y probada, pero no hay selector» |
| «El controlador revisa si es UCI o Observación» | «El controlador solo llama `es_compatible(nivel)`» |
| «Trauma Shock acepta nivel 1 y 2» | «**Solo nivel 1.** UCI es 1 y 2» |
| «Usamos sobrecarga de métodos» | «Python no tiene sobrecarga; usamos parámetros con valor por defecto» |

## Si te bloqueas

Mira a Favio; a los 5 segundos completa. Frase para recuperar el hilo: «Un mensaje, cuatro respuestas: `es_compatible`.»
Si te pierdes en la colaboración, di solo cinco pasos: permiso, triaje, compatibilidad, reserva y bitácora.

## Preguntas que te tocan (respuestas completas en [PREGUNTAS_PROFESOR.md](../PREGUNTAS_PROFESOR.md))

| Pregunta | Dónde |
|---|---|
| **«¿Dónde aplicaste polimorfismo?»** | A1 |
| «¿Dónde aplicaste herencia? ¿Y sobreescritura?» | A2 |
| «¿Aplicaste sobrecarga de métodos?» | A3 |
| «¿Por qué `Cama` y `Persona` son abstractas?» | A4 |
| «Esa fábrica `CLASES_POR_TIPO`, ¿no es un `if` por tipo?» | A1 (qué costó) |
| «¿Qué es Strategy? ¿Dónde se usa `ReglaMINSA`?» | A6 |
| «¿Diferencia entre herencia y composición?» | A7 |
| «¿Cómo decide el nivel Manchester? ¿Está validado?» | F1 |
