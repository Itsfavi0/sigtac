# Tarjeta de Ian

**Tu parte:** Criterio 2, clases principales (min **5–9**) y Criterio 3, encapsulamiento (min **9–12**).

> **Cómo usar el texto:** está escrito para que no te quedes en blanco. Léelo en voz alta 2 o 3 veces y luego dilo con
> tus palabras. Lo que **sí** debe salir exacto está en **negrita**. Cada párrafo dura unos 30–40 segundos al hablar con calma.

**Antes de entrar:** abre en el editor `models/persona.py`, `models/documento.py`, `models/triaje.py` y `models/cama.py`.
Ten a mano la diapositiva del diagrama de clases.

---

## Criterio 2: clases principales · Min 5–9 · Texto sugerido

**① Introducción (25 s)**
«Profesor, en este criterio explicamos las clases principales: qué representa cada una, qué datos guarda y qué operaciones
realiza. Vamos a seguir el diagrama. Casi toda la programación orientada a objetos del proyecto está en la carpeta `models/`.»

**② Las personas (50 s)** *(señala `Persona`, `Paciente`, `Empleado`)*
«Empezamos por `Persona`, que es una **clase abstracta**: representa a cualquier persona del sistema y guarda su documento,
nombres, apellidos y fecha de nacimiento. No se puede crear una `Persona` directamente. De ella heredan dos clases.
`Paciente` es quien llega a emergencia, y puede estar sin identificar, lo que llamamos un paciente NN. `Empleado` es el
personal, y de ella heredan `Enfermero`, `Medico` y `PersonalLimpieza`, cada una con su dato propio: área, especialidad o
turno, y cada una arma su propio resumen con `obtener_resumen`.»

**③ El documento (20 s)** *(`DocumentoIdentidad`)*
«`DocumentoIdentidad` representa un documento, con su tipo y su número. Se valida al crearse: un DNI son exactamente 8
dígitos, y si no, lanza un error. Una vez creado, no cambia.»

**④ El episodio (50 s)** *(`EpisodioEmergencia`)*
«Aquí hay una decisión importante: **el paciente es la persona; el episodio es una visita.** `EpisodioEmergencia` representa
una visita del paciente a emergencia. Guarda el motivo de consulta, el estado, las fechas, y contiene sus triajes y sus
signos vitales. Sabe agregar un triaje, asignar una cama, dar de alta, referir o registrar una fuga. Son dos clases
distintas porque un paciente puede venir muchas veces, y cada visita tiene su propio triaje, su propia cama y su propia alta.»

**⑤ Triaje y signos vitales (40 s)** *(`Triaje`, `SignosVitales`, `Sintoma`)*
«`SignosVitales` es una toma de signos: presión, frecuencia cardíaca, frecuencia respiratoria, temperatura y saturación de
oxígeno. Valida sus rangos al crearse. `Triaje` es una clasificación de prioridad: guarda el nivel sugerido por el sistema, el
nivel final, la justificación y los síntomas, y sabe reclasificar. Cada triaje se agrega al episodio; no se edita uno anterior,
de modo que se conserva el historial.»

**⑥ Las camas (45 s)** *(`Cama` y sus cuatro hijas)*
«`Cama` también es **abstracta**: no existe una cama genérica, siempre es de un tipo. Guarda su código, su área y su estado, y
sabe reservar, ocupar, dar de alta y liberarse tras la limpieza. De ella heredan cuatro tipos: Trauma Shock, UCI, Observación
y Hospitalización. Cada una responde de forma distinta a un mismo mensaje, `es_compatible`; eso lo explica Percy en un momento.»

**⑦ Estrategia y cuenta de usuario (35 s)**
«`EstrategiaTriaje` representa un algoritmo de clasificación, con dos implementaciones: Manchester y MINSA. Y `CuentaUsuario`
representa el acceso de un empleado al sistema: guarda su rol, si está activa y sus intentos fallidos, y se puede activar,
desactivar o cambiar de rol.»

**⑧ Cierre del bloque (15 s)**
«En resumen: cada clase es una cosa del hospital, con sus datos y sus acciones. Ahora veamos cómo se protegen esos datos.»

---

## Criterio 3: encapsulamiento · Min 9–12 · Texto sugerido

**① Qué es (20 s)** *(abre `models/cama.py`)*
«El encapsulamiento es que un objeto proteja sus datos: solo se cambian por sus métodos, y esos métodos validan. Les mostramos
tres ejemplos.»

**② Ejemplo 1: el estado de la cama (60 s)** *(muestra `_estado`, `@property` y `reservar`)*
«Primer ejemplo. En `Cama`, el estado se guarda en `_estado`, con un guion bajo, que en Python indica que es un atributo
protegido. Desde fuera solo se puede **leer**, con `@property`; **no hay *setter***. Si alguien escribe
`cama.estado = "OCUPADA"`, Python responde con un `AttributeError`. La única forma de cambiarlo es con un método con nombre de
acción: `reservar`, `ocupar`, `dar_alta` o `liberar_limpieza`, y cada uno comprueba que la transición sea válida. Por ejemplo,
`reservar` solo funciona si la cama está disponible; si está ocupada, lanza `CamaEstadoInvalidoError`.»

**③ Ejemplo 2: valores imposibles (50 s)** *(muestra `SignosVitales`)*
«Segundo ejemplo: `SignosVitales`. Tiene una tabla de rangos admitidos para cada signo, y en el constructor comprueba cada
valor. No puede existir un objeto con una saturación de 150 por ciento. Además, valida que la presión sistólica sea mayor que
la diastólica. **El objeto se valida al nacer: cualquier objeto que existe ya es válido.**»

**④ Ejemplo 3: reclasificar (40 s)** *(muestra `Triaje.reclasificar`)*
«Tercer ejemplo: `reclasificar`, en `Triaje`. Para cambiar el nivel que sugirió el sistema, exige un nivel entre 1 y 5 y una
justificación de **al menos 10 caracteres**; si no, lanza un error. Es la regla de negocio RN-10, y la vamos a ver funcionando
en la demostración.»

**⑤ Cierre (15 s)** *(con honestidad)*
«Aclaramos que en Python el guion bajo es una convención y no una barrera: confiamos en que nadie escriba `_estado` desde
fuera, y por eso las pruebas lo vigilan. Ahora Percy explica las relaciones entre las clases.»

---

## No digas / di

| No digas | Di |
|---|---|
| «`_estado` es privado» | «Es **protegido** por convención: en Python no hay `private` real» |
| «`__estado`» | «`_estado`, con un guion» |
| «El paciente tiene la cama» | «El **episodio** tiene la cama, por la `AsignacionCama`» |
| «Se puede crear una `Persona`» | «`Persona` es abstracta: no se instancia» |

## Si te bloqueas

Mira a Favio; a los 5 segundos completa. Frase para recuperar el hilo: «El estado de la cama no se asigna: se pide.»
Si olvidas una clase, sigue con la siguiente: no hace falta decirlas todas de memoria.

## Preguntas que te tocan (respuestas completas en [PREGUNTAS_PROFESOR.md](../PREGUNTAS_PROFESOR.md))

| Pregunta | Dónde |
|---|---|
| «¿Dónde aplicaste encapsulamiento? Python no tiene `private`» | A5 |
| «¿Por qué `_estado` y no `__estado`?» | A5 |
| «¿Diferencia entre `ValueError` y `SigtacError`?» | E1 |
| «¿Por qué `Paciente` y `EpisodioEmergencia` son distintas?» | A8 |
| «¿Dónde validan los datos, en la pantalla o en el modelo?» | E3 |
| «¿Por qué separaron rol de cargo?» | A9 |
