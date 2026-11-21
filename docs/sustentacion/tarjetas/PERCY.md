# Tarjeta de Percy

**Tu parte:** Criterio 4, relaciones entre clases (min **12–18**). Es el bloque en el que más preguntas rebuscadas caen.
Esta tarjeta es un apoyo: dilo con tus palabras. Lo que **sí** tiene que salir exacto está en negrita.

**Antes de entrar:** abre `models/cama.py`, `controllers/cama_controller.py` (método `asignar`), `models/estrategias.py`
y `models/persona.py`.

---

## Min 12–18, con tiempos

**1. Herencia (1 min).** `Cama` es abstracta con 4 hijas (`CamaTraumaShock`, `CamaUCI`, `CamaObservacion`, `CamaHospitalizacion`).
`Persona` → `Paciente` y `Empleado` → `Enfermero`, `Medico`, `PersonalLimpieza`. «Un enfermero **es un** empleado y **es una** persona.»

**2. Polimorfismo (2 min). Es el ejemplo principal.**
- En `models/cama.py` muestra `es_compatible` en las cuatro hijas:
  **Trauma Shock solo nivel 1 · UCI 1 y 2 · Observación 2, 3 y 4 · Hospitalización 3, 4 y 5.**
- Luego abre `controllers/cama_controller.py:74`:
  `[cama for cama in CamaDAO.listar_disponibles() if cama.es_compatible(nivel)]`
- **Frase clave:** «El controlador nunca pregunta de qué tipo es la cama. Si mañana hay una cama pediátrica, se crea una clase
  nueva y esta línea no se toca.»

**3. Strategy (1 min).** `EstrategiaTriaje` define `evaluar()` y `justificar()`; `ReglaManchester` y `ReglaMINSA` la implementan.
El controlador recibe una estrategia y no sabe cuál es. **Di tú: «`ReglaMINSA` está implementada y probada, pero la aplicación
no tiene un selector; usa Manchester por defecto».**

**4. Composición y asociación (30 s).** El episodio **contiene** sus triajes y signos; un triaje contiene sus síntomas.
`AsignacionCama` es una **asociación**: une un episodio con una cama durante un tiempo.

**5. Colaboración (1,5 min): asignar una cama, en pasos.** Abre `CamaController.asignar`:
1. `exigir_permiso`: ¿puede este rol?
2. `with transaccion()`: todo o nada.
3. `episodio.asignar_cama()`: valida RN-01 (debe tener triaje).
4. `cama.es_compatible(nivel)`: la cama responde (polimorfismo).
5. `cama.reservar()`: valida RN-05.
6. Los DAO guardan (episodio, cama, asignación).
7. La bitácora registra quién lo hizo.
- «Si algo falla, la transacción deshace todo.»

**Transición:** «Y ahora lo vemos funcionando: Favio maneja la demostración.»

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
Si te pierdes en la colaboración, di solo los pasos 1, 3, 4, 5 y 7 (permiso, triaje, compatibilidad, reserva, bitácora).

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
