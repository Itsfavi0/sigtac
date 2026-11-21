# Tarjeta de Ian

**Tu parte:** Criterio 2, clases principales (min **5–9**) y Criterio 3, encapsulamiento (min **9–12**).
Esta tarjeta es un apoyo: dilo con tus palabras. Lo que **sí** tiene que salir exacto está en negrita.

**Antes de entrar:** abre `models/persona.py`, `models/triaje.py`, `models/cama.py` y `models/documento.py` en el editor.

---

## Criterio 2: clases principales · Min 5–9

Por cada clase, una frase: **qué representa, qué guarda y qué hace**. Orden sugerido (con la diapositiva del diagrama):

| Clase | Qué representa | Qué hace (ejemplos) |
|---|---|---|
| `Persona` (abstracta) | Cualquier persona del sistema | `calcular_edad()`, `obtener_resumen()` |
| `Paciente` | Quien llega a emergencia (puede ser NN) | `identificar()`, `actualizar_datos()`, `anular()` |
| `Empleado` → `Enfermero`, `Medico`, `PersonalLimpieza` | El personal | `obtener_resumen()` propio de cada una |
| `DocumentoIdentidad` | Un documento (tipo + número) | Se valida al crearse (DNI: 8 dígitos) |
| `EpisodioEmergencia` | **Una visita** del paciente | `agregar_triaje()`, `asignar_cama()`, `dar_alta()`, `referir()` |
| `SignosVitales` | Una toma de signos | Valida rangos al crearse |
| `Triaje` | Una clasificación de prioridad | `agregar_sintoma()`, `reclasificar()` |
| `Cama` (abstracta) + 4 hijas | Una cama física | `reservar()`, `ocupar()`, `dar_alta()`, `liberar_limpieza()`, `es_compatible()` |
| `EstrategiaTriaje` + 2 hijas | Un algoritmo de clasificación | `evaluar()`, `clasificar()`, `justificar()` |
| `CuentaUsuario` | El acceso de un empleado al sistema | `activar()`, `desactivar()`, `cambiar_rol()` |

**Frase clave:** «El paciente es la persona; el episodio es **una visita**. Un paciente puede venir muchas veces, por eso son
dos clases.»

**Transición a encapsulamiento:** «Ahora, cómo protegen sus datos estas clases.»

## Criterio 3: encapsulamiento · Min 9–12

Abre `models/cama.py`. Tres ejemplos, en este orden:

1. **`Cama.reservar()`** (`cama.py`, método `reservar`):
   - `_estado` se **lee** con `@property`; no hay *setter*.
   - Solo cambia por `reservar()`, `ocupar()`, `dar_alta()`, `liberar_limpieza()`, y cada una comprueba la transición.
   - **«`cama.estado = "OCUPADA"` da `AttributeError`.»** Una cama ocupada no se puede reservar (`CamaEstadoInvalidoError`).
2. **`SignosVitales`** (`models/triaje.py`): los rangos están en `RANGOS`; no se puede crear una saturación de 150 %.
   «El objeto se valida al nacer: todo objeto que existe ya es válido.»
3. **`Triaje.reclasificar()`**: justificación de **mínimo 10 caracteres** (RN-10). «Esto lo vamos a ver en la demo.»

**Transición:** «Percy explica cómo se relacionan estas clases.»

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
