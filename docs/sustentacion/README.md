# Sustentación de SIGTAC — material del equipo

Avance del **sábado 21 de noviembre de 2026**; entrega final a mediados de diciembre (19/12/2026).
Todo lo que el profesor pide está en `puntos_poo2_pc03.pdf` (8 criterios y los aportes adicionales).

| Archivo | Para qué sirve | Quién lo lee |
|---|---|---|
| [CRITERIOS.md](CRITERIOS.md) | Qué mostrar en cada uno de los 8 criterios, con el código real | Todos |
| [OBSERVACIONES.md](OBSERVACIONES.md) | La observación de la primera presentación (migrar de motor de BD) y cómo se atendió | Todos; la expone Renzo |
| [GUION_EXPOSICION.md](GUION_EXPOSICION.md) | **Orden y tiempos de la exposición completa (unos 35 min), minuto a minuto, y la versión corta** | Todos |
| [PREGUNTAS_PROFESOR.md](PREGUNTAS_PROFESOR.md) | **Banco de preguntas «¿dónde aplicaste X?» / «¿por qué esto y no esto?», con la fórmula de 4 partes** | Todos; Favio dirige |
| [tarjetas/](tarjetas/) | **Una hoja por persona** (`RENZO.md`, `IAN.md`, `PERCY.md`, `LEONARDO.md`): su parte en orden, qué no decir y qué hacer si se bloquea | Cada uno, la suya |
| [GUION_FAVIO.md](GUION_FAVIO.md) | **Guion del que audita: reglas para intervenir, alarmas y rescates por bloque, y datos de bolsillo** | Favio |
| [GUION_DEMO.md](GUION_DEMO.md) | Paso a paso de la demostración en vivo, con los datos que se escriben | Quien maneja la PC |
| [HOJAS_DE_ESTUDIO.md](HOJAS_DE_ESTUDIO.md) | Qué expone cada integrante y las preguntas que le pueden hacer | Cada uno, la suya |
| [TABLA_PRUEBAS.md](TABLA_PRUEBAS.md) | Los casos probados y su resultado | Todos |
| [DIAPOSITIVAS.md](DIAPOSITIVAS.md) | El texto de cada diapositiva, para pasarlo al Canva | Quien edita el Canva |
| `capturas/` | Capturas de cada pantalla (datos de demostración) | Canva y Word |

## Orden de la exposición (unos 35 minutos, sin máximo)

| Min | Parte | Criterio | Expone |
|---|---|---|---|
| 0–2 | Qué es SIGTAC y qué problema resuelve | — | Favio |
| 2–5 | Observación de la primera presentación y cómo se atendió | 1 | Renzo |
| 5–9 | Clases principales | 2 | Ian |
| 9–12 | Encapsulamiento | 3 | Ian |
| 12–18 | Relaciones: herencia, polimorfismo, Strategy, composición, colaboración | 4 | Percy |
| 18–27 | Demo en vivo, con los tres rechazos | 5 y 6 | Favio maneja; Leonardo explica las pantallas |
| 27–30 | Organización del código | 7 | Leonardo |
| 30–34 | «Por qué esto y no esto»: 4 decisiones técnicas | 8 | Favio |
| 34–36 | Aportes adicionales y cierre | — | Renzo |
| 36 → | Preguntas (Favio dirige) | 8 | Quien expuso el tema |

Detalle minuto a minuto y versión corta: [GUION_EXPOSICION.md](GUION_EXPOSICION.md).
Las diapositivas ([DIAPOSITIVAS.md](DIAPOSITIVAS.md)) siguen el orden de 15 minutos: hay que ampliarlas a este orden.

## Antes del día

- [ ] Cada integrante leyó su hoja de estudio y abrió los archivos que le tocan.
- [ ] Un ensayo completo con cronómetro, en la PC que se va a usar.
- [ ] `seed.sql` recargado en `sigtac_db` (lo hace Favio con su cuenta de administrador de MySQL).
- [ ] MySQL encendido y `python main.py` abre el login.
- [ ] Plan B probado: `python -m prototipo.ver` abre la aplicación sin MySQL.
- [ ] El Canva tiene las capturas de `capturas/`, por si la demo falla.

## Otros archivos

- `recorrido.gif`: las 8 pantallas, una cada 2,5 segundos. Sirve para la portada del Canva.
- `../../SIGTAC_Proyecto_POO_II_v2.docx`: copia actualizada del informe (no está en el repositorio).
