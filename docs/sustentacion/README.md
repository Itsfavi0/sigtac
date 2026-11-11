# Sustentación de SIGTAC — material del equipo

Avance del **sábado 21 de noviembre de 2026**; entrega final a mediados de diciembre (19/12/2026).
Todo lo que el profesor pide está en `puntos_poo2_pc03.pdf` (8 criterios y los aportes adicionales).

| Archivo | Para qué sirve | Quién lo lee |
|---|---|---|
| [CRITERIOS.md](CRITERIOS.md) | Qué mostrar en cada uno de los 8 criterios, con el código real | Todos |
| [OBSERVACIONES.md](OBSERVACIONES.md) | La observación de la primera presentación (migrar de motor de BD) y cómo se atendió | Todos; la expone Renzo |
| [GUION_DEMO.md](GUION_DEMO.md) | Paso a paso de la demostración en vivo, con los datos que se escriben | Quien maneja la PC |
| [HOJAS_DE_ESTUDIO.md](HOJAS_DE_ESTUDIO.md) | Qué expone cada integrante y las preguntas que le pueden hacer | Cada uno, la suya |
| [TABLA_PRUEBAS.md](TABLA_PRUEBAS.md) | Los casos probados y su resultado | Todos |
| [DIAPOSITIVAS.md](DIAPOSITIVAS.md) | El texto de cada diapositiva, para pasarlo al Canva | Quien edita el Canva |
| `capturas/` | Capturas de cada pantalla (datos de demostración) | Canva y Word |

## Orden de la exposición (15 minutos)

| Min | Parte | Criterio | Expone |
|---|---|---|---|
| 0–1 | Qué es SIGTAC y qué problema resuelve | — | Favio |
| 1–3 | Observación de la primera presentación y cómo se atendió | 1 | Renzo |
| 3–5 | Clases principales | 2 | Ian |
| 5–6 | Encapsulamiento | 3 | Ian |
| 6–8 | Relaciones: herencia, polimorfismo, composición | 4 | Percy |
| 8–13 | Demo en vivo, con los tres rechazos | 5 y 6 | Favio maneja; Leonardo explica las pantallas |
| 13–14 | Organización del código | 7 | Leonardo |
| 14–15 | Una decisión técnica y aportes adicionales | 8 | Favio y Renzo |

Si el profesor da menos tiempo, se recorta la demo a los pasos 1, 2, 4, 5 y 10 del guion.

## Antes del día

- [ ] Cada integrante leyó su hoja de estudio y abrió los archivos que le tocan.
- [ ] Un ensayo completo con cronómetro, en la PC que se va a usar.
- [ ] `seed.sql` recargado en `sigtac_db` (lo hace Favio con su cuenta de administrador de MySQL).
- [ ] MySQL encendido y `python main.py` abre el login.
- [ ] Plan B probado: `python -m prototipo.ver` abre la aplicación sin MySQL.
- [ ] El Canva tiene las capturas de `capturas/`, por si la demo falla.

## Otros archivos

- `recorrido.gif`: las 8 pantallas, una cada 2,5 segundos. Sirve para la portada del Canva.
- `../../db_scripts/demo_camas.sql`: 22 camas más para la demo (opcional; ver el guion).
- `../../SIGTAC_Proyecto_POO_II_v2.docx`: copia actualizada del informe (no está en el repositorio).
