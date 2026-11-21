# Guion de la exposición, minuto a minuto

Unos **35 minutos de exposición** y las preguntas después, sin máximo. Si el profesor da menos tiempo, ver
«Versión corta» al final. La demo detallada está en [GUION_DEMO.md](GUION_DEMO.md); las respuestas a las preguntas,
en [PREGUNTAS_PROFESOR.md](PREGUNTAS_PROFESOR.md).

**Roles de hoy:** Favio maneja la PC en la demo y **dirige las preguntas** (audita: completa o corrige lo que falte).
Responde primero quien expuso el tema.

| Min | Bloque | Criterio | Expone | Diapositivas |
|---|---|---|---|---|
| 0–2 | Problema y solución | — | Favio | 1–2 |
| 2–5 | Observación anterior y migración de motor | 1 | Renzo | 3–4 |
| 5–9 | Clases principales | 2 | Ian | 5 |
| 9–12 | Encapsulamiento | 3 | Ian | 6 |
| 12–18 | Relaciones: herencia, polimorfismo, Strategy, composición, colaboración | 4 | Percy | 7–9 |
| 18–27 | Demo en vivo | 5 y 6 | Favio maneja; Leonardo explica | 10–11 |
| 27–30 | Organización del código | 7 | Leonardo | 12 |
| 30–34 | «Por qué esto y no esto» | 8 | Favio | 13 |
| 34–36 | Aportes adicionales y cierre | — | Renzo | 14–15 |
| 36 → | Preguntas | 8 | Favio dirige | — |

**Cambios de turno:** quien termina dice el nombre del siguiente («…y ahora Ian explica las clases»). Nadie se
levanta durante la demo; quien maneja la PC no habla mientras escribe.

---

## 0–2 · Favio — Problema y solución

- «En emergencia se atiende por gravedad, no por orden de llegada.»
- Antes: la cama se busca por teléfono y el estado está en una pizarra. Con SIGTAC: triaje y camas en un solo sistema.
- Aclarar: «es un **prototipo académico**; el triaje es una sugerencia y el profesional decide».
- Anunciar el orden: «vamos por los 8 criterios; al final, la demo y las decisiones».

## 2–5 · Renzo — Criterio 1: la observación de la primera presentación

- Leer la observación: *«¿Cómo harían para migrar a otro motor de base de datos?»* → «Atendida».
- Respuesta: «solo se toca `dao/`». Mostrar en **terminal** el `grep` de [OBSERVACIONES.md](OBSERVACIONES.md): MySQL
  aparece en 3 archivos, todos de `dao/`.
- Decir: «una prueba automática (`tests/test_capas.py`) falla si otra capa importa MySQL».
- Mostrar qué cambia y qué no: `views` 6 679 líneas, `controllers` 1 127 y `models` 1 368 **no cambian**; `dao` 1 853 sí.
- Honestidad: «no es cambiar una línea; hay SQL propio de MySQL en una docena de consultas. Lo que se garantiza es que
  todo ese trabajo está en una sola carpeta. La migración no se ejecutó; lo probado es el aislamiento».

## 5–9 · Ian — Criterio 2: clases principales

- Diapositiva con el diagrama (solo nombres y flechas). Recorrer la tabla de [CRITERIOS.md](CRITERIOS.md) §2: por cada
  clase, una frase: **qué representa, qué guarda y qué hace**.
- Orden sugerido: `Persona` → `Paciente` y `Empleado` → `DocumentoIdentidad` → `EpisodioEmergencia` → `Triaje` →
  `SignosVitales` → `Cama` → `EstrategiaTriaje` → `CuentaUsuario`.
- Frase clave: «un paciente es una persona; un episodio es una visita. Por eso son dos clases».

## 9–12 · Ian — Criterio 3: encapsulamiento

Abrir `models/cama.py` en el editor.

1. `Cama.reservar()`: `_estado` solo se lee (`@property`, sin *setter*); cambia con un método que valida.
   Decir: «`cama.estado = "OCUPADA"` da `AttributeError`».
2. `SignosVitales`: no se puede crear una saturación de 150 %.
3. `Triaje.reclasificar()`: exige 10 caracteres (RN-10). «Esto lo vamos a ver en la demo».

Si preguntan por `_` frente a `__` o por `private`: [PREGUNTAS_PROFESOR.md](PREGUNTAS_PROFESOR.md) A5.

## 12–18 · Percy — Criterio 4: relaciones entre clases

1. **Herencia (1 min):** `Cama` abstracta con 4 hijas; `Persona` → `Paciente` y `Empleado` → 3 hijas.
2. **Polimorfismo (2 min):** las 4 líneas de `es_compatible`; abrir `controllers/cama_controller.py:74` y mostrar que
   el controlador **no pregunta el tipo**. Decir: «si mañana hay una cama pediátrica, esta línea no se toca».
3. **Strategy (1 min):** `EstrategiaTriaje` con Manchester y MINSA. **Decir que MINSA está implementada pero la app
   no tiene un selector** (se cambia pasando la estrategia al constructor).
4. **Composición y asociación (30 s):** el episodio contiene triajes y signos; `AsignacionCama` une episodio y cama.
5. **Colaboración (1,5 min):** `CamaController.asignar` paso a paso: permiso → transacción → episodio valida triaje →
   cama valida compatibilidad y estado → DAO guardan → bitácora. «Si algo falla, se deshace todo».

> No usar `obtener_resumen()` como ejemplo central: ninguna pantalla lo llama (ver A1 del banco).

## 18–27 · Demo en vivo (9 min) — Favio maneja, Leonardo explica

Seguir [GUION_DEMO.md](GUION_DEMO.md), los 15 pasos. Reparto: Leonardo dice el «qué se dice» de cada paso; Favio no habla
mientras escribe. Tiempo de referencia: pasos 1–2 (1 min), 3–7 (3,5 min), 8–9 (1,5 min), 10 (30 s), 11–12 (1 min), 13–15 (1,5 min).

Los tres rechazos se anuncian: «ahora un dato **incorrecto**, uno **incompleto** y uno **duplicado**».

## 27–30 · Leonardo — Criterio 7: organización del código

- Árbol de carpetas en el editor y `views → controllers → models → dao`.
- Seguir **una operación por las 4 capas**: `triage_view.py` → `TriajeController.registrar()` → `Triaje.reclasificar()` → `TriajeDAO`.
- `tema.py` es el único archivo con colores y letras (cada color es un par claro/oscuro); `views/componentes/` reúne lo reutilizable.
- Nombres en español que dicen lo que hacen: `cama.reservar()`, `episodio.dar_alta()`, `exigir_permiso()`.
- Tamaño: unas 11 400 líneas de aplicación y 13 000 de pruebas.

## 30–34 · Favio — Criterio 8: «por qué esto y no esto»

Cuatro decisiones, cada una con la fórmula de 4 partes (dónde, por qué, qué se descartó, qué costó):

1. **Compatibilidad con polimorfismo y no en SQL** (la principal; banco C3).
2. **`UPDATE` condicional para la concurrencia** y no leer-y-escribir (banco C2).
3. **Rol separado de cargo** (banco A9).
4. **Baja lógica y no borrar** (banco C5).

Cerrar con: «cada integrante explicó su contribución; las preguntas que sigan las responde quien expuso el tema».

## 34–36 · Renzo — Aportes adicionales y cierre

- Declarar expresamente: MySQL con 22 tablas y transacciones, reporte PDF, búsqueda, 5 roles y permisos, bitácora,
  claves con bcrypt, 2 332 pruebas (2 331 pasan, 1 se omite fuera de Windows) y modo oscuro.
- Qué sigue: que cada usuario cambie su propia clave, probarlo con varias PCs y un selector de norma de triaje.
- «¿Preguntas?»

---

## Versión corta (si el profesor da menos tiempo)

| Min | Bloque |
|---|---|
| 0–1 | Problema (Favio) |
| 1–3 | Observación anterior (Renzo) |
| 3–7 | Clases + encapsulamiento (Ian) |
| 7–10 | Herencia, polimorfismo y colaboración (Percy) |
| 10–16 | Demo recortada: pasos 2, 3, 5, 6, 8 y 15 del guion (Favio + Leonardo) |
| 16–18 | Organización del código y decisión técnica (Leonardo y Favio) |

## Ensayo (hoy, antes de entrar)

- [ ] Cada uno dice su bloque en voz alta, con cronómetro.
- [ ] Ronda de 10 preguntas trampa (final de [PREGUNTAS_PROFESOR.md](PREGUNTAS_PROFESOR.md)): uno pregunta, otro responde, Favio audita.
- [ ] Todos tienen la misma respuesta a las preguntas sobre IA y sobre los commits (H1 y H2).
- [ ] Editor abierto con `models/cama.py`, `controllers/cama_controller.py` y `models/estrategias.py`; terminal lista para el `grep`.
