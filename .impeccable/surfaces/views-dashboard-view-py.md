---
version: 1
slug: "views-dashboard-view-py"
primary_target: "views/dashboard_view.py"
related_targets: ["views/tema.py","views/componentes"]
---

# Tablero de camas (y mundo visual de SIGTAC)

Modo: Operate. Aplicación de escritorio en CustomTkinter. Público: todos los roles de la guardia de emergencia,
y el jurado del curso en la demo (proyector). Tarea: saber en un vistazo cuántas camas hay libres, en qué estado
está cada una y quién espera cama. Restricciones: solo lo que CTk dibuja (sin sombras, degradados ni
transparencias), letra de 12 px como mínimo, contraste de 4.5:1 en modo claro (predeterminado) y en oscuro.

## Direction contract

THESIS: El primer diseño del equipo (Figma Make), conservado y corregido. Una superficie plana de grises neutros
donde el único color es información: el borde de cada cama dice su estado y la etiqueta rellena con número dice la
prioridad. Rechaza el panel de KPIs coloreado y la paleta usada como decoración.

OWN-WORLD: Grises neutros sin tinte (oscuro #242424/#2B2B2B/#202020; claro #F5F5F7/#FFFFFF), bordes de 1 px,
esquinas de 6–8 px, Inter (Regular, Medium, SemiBold, Bold). Azul #0A6CDE solo para la acción principal y el ítem
activo. Estados de cama como borde de color (verde, rojo, amarillo, violeta, gris) con el estado escrito; los
niveles 1–5 como cuadros rellenos con su número.

STORY: El visitante ve primero la matriz de camas por área y entiende cuántas quedan libres. Después ve quién espera
cama, en orden de prioridad, y si alguien se pasó del plazo de su nivel.

FIRST VIEWPORT: A la izquierda, la barra lateral de 200 px (marca, menú, estado de la conexión, usuario). Encima,
el encabezado de 72 px (título; a la derecha, la hora de actualización, la fecha y la hora). Debajo, una fila de 4
KPIs, la tarjeta «Matriz de camas» con una columna por tipo de cama y la leyenda arriba a la derecha, y al pie, la
cola «Esperan cama» a lo ancho. No hay acción principal: el tablero es de lectura.

FORM: El tablero del Figma del equipo, elegido por el equipo sobre la propuesta «señalética» (primera de la lista
del equipo). Gesto distintivo: la matriz que se reacomoda sola, con el menor número de filas en el que caben todas
las áreas, y que se desplaza por dentro cuando no alcanza el alto. seed: none (unavailable)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
