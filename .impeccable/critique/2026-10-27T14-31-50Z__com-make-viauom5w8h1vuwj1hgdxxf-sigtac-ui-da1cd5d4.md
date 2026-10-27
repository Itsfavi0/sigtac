---
target: Figma Make SIGTAC - UI (primer diseño)
total_score: 18
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 4
target_identity: "url:https://www.figma.com/make/VIaUoM5W8h1VuwJ1hgDxXf/SIGTAC---UI"
timestamp: 2026-10-27T14-31-50Z
slug: com-make-viauom5w8h1vuwj1hgdxxf-sigtac-ui-da1cd5d4
---
# Crítica del primer diseño (Figma Make «SIGTAC - UI»)

> Fase D3 del plan de diseño (2026-10-27). Hecha con impeccable `critique` sobre la vista previa del prototipo
> a 1280×800 y al área mínima del brief, 1093×614.
> Método: dos agentes independientes. A hizo la revisión de diseño; B, el detector y las mediciones.
> **El detector automático no pudo ejecutarse**: el navegador integrado bloquea que una página pública cargue
> scripts desde localhost (`net::ERR_BLOCKED_BY_CLIENT`). B entregó mediciones directas con `getComputedStyle`.

## Puntaje de las heurísticas de Nielsen: 18/40 (Pobre)

| # | Heurística | Nota | Problema clave |
|---|---|---|---|
| 1 | Visibilidad del estado del sistema | 2 | Dice «EN VIVO», pero el reloj 10:42:18 está fijo y la fecha es de 2025. El KPI dice «14 / 86», pero el mapa tiene 32 camas. Guardar no da ningún aviso. |
| 2 | Coincidencia con el mundo real | 2 | Romanos I–III en lugar de 1–5 con nombre de color. La PA va en un solo campo de texto libre. «Escala de dolor» no existe en el modelo. «Tiempo objetivo: 0 minutos». |
| 3 | Control y libertad del usuario | 2 | «Reclasificar manualmente» no hace nada al pulsarlo. Sí hay «Cancelar» y botón atrás. |
| 4 | Consistencia y estándares | 2 | El azul #007AFF es primario, foco y «Reservada». Hay dos botones primarios: «Aceptar» y «Guardar triaje». La pantalla «Cola» tiene el título «Tablero de Camas». |
| 5 | Prevención de errores | 1 | La SatO2 acepta 150. Sugiere «PRIORIDAD I» con el formulario vacío y con signos normales. La justificación es obligatoria siempre. |
| 6 | Reconocer antes que recordar | 2 | Las camas escriben su estado y hay leyenda, pero la leyenda va a 8 px. El amarillo es «Limpieza» y también «Prioridad III». |
| 7 | Flexibilidad y eficiencia | 1 | No hay atajos. Confirmar exige dos clics (Aceptar + Guardar). 3 de las 5 entradas del menú llevan a pantallas vacías. |
| 8 | Diseño estético y minimalista | 3 | Lenguaje plano, sobrio y coherente. Pierde un punto porque la jerarquía se aplasta con texto de 7–9 px. |
| 9 | Reconocer, diagnosticar y recuperarse de errores | 1 | El estado de error está diseñado en la guía, pero la app usa la burbuja nativa del navegador. |
| 10 | Ayuda y documentación | 2 | «Criterios detectados» explica la sugerencia (bien). No se muestran rangos; las unidades solo están en el placeholder. |

## ¿Está hecho para este producto?

**Diseño (A):** es intercambiable con cualquier panel de administración oscuro.
- La paleta son los colores de sistema de iOS sin cambios (#FF3B30, #FFCC00, #34C759, #007AFF).
- El resto también es de plantilla: Inter sobre grises #242424/#2B2B2B, 4 tarjetas KPI con un ícono en una cajita, logo en un cuadrado azul y el punto «EN VIVO».
- Lo propio del dominio: la matriz de camas por área con «2 de 6 libres» y el panel de clasificación con sus criterios.
- **La gran oportunidad perdida:** que los 5 colores de triaje sean la columna vertebral visual del producto. Hoy compiten con los colores de estado de cama.

**Mediciones (B):** confirman los problemas de legibilidad y contraste.

| | Tablero | Nuevo Triaje |
|---|---|---|
| Elementos con texto < 12 px | **116** | **55** |
| Pares de color con contraste < 4.5:1 | 7 de 23 | 8 de 24 |
| Pesos de letra distintos | 8 | 9 |
| Grises de fondo distintos | 9 | 12 |

En los campos, el foco solo cambia el color de un borde de 0.8 px. En los botones, el anillo que aparece es el del propio navegador, no uno definido por el diseño.

## Lo que funciona

1. **El lenguaje visual ya es casi compatible con CustomTkinter:** sin sombras, degradados ni desenfoque, con bordes de 1 px y radios de 6–8 px. La migración no pierde la identidad.
2. **Las camas cumplen «nunca solo color»:** código, estado escrito y color, más el conteo por área y una leyenda.
3. **El triaje está bien planteado:** formulario en pasos a la izquierda y la sugerencia fija a la derecha, con el nombre de la acción y los criterios. La guía documenta todos los estados de botones y campos.

## Problemas prioritarios

### [P0] Texto ilegible: 7–10 px en todo lo operativo
- **Qué:** los tamaños medidos son:
  - estado de cama: 7 px, #888 sobre #292929 (4.10:1);
  - leyenda: 8 px;
  - etiquetas de campo: 9 px;
  - texto dentro de los campos y del botón «Aceptar»: 10 px.
- **Por qué importa:** el éxito es «en un vistazo». En el proyector y en el monitor viejo no se lee nada.
- **Arreglo:** una escala de 5 tamaños (12 / 13 / 15 / 18 / 24), solo normal y negrita. Estado de cama a 12 px en negrita, código a 13 px y cifras KPI a 24 px.
- **Comando:** `/impeccable typeset`

### [P1] Colores con dos significados, y una paleta que no sirve en modo claro
- **Qué:**
  - amarillo = Limpieza = Prioridad III;
  - verde = Disponible = «EN VIVO» = éxito (y chocará con el Nivel 4 Verde);
  - azul = Reservada = primario = foco (y chocará con el Nivel 5 Azul).
  
  Sobre blanco, esos tonos dan: amarillo 1.51:1, verde 2.22:1, rojo 3.55:1.
- **Arreglo:**
  - el color saturado se reserva para los niveles de triaje (chip con número y nombre);
  - las camas usan un tinte, texto e ícono, con un tono por estado que no se repita en los niveles;
  - el primario es un color de marca que no sea de estado;
  - cada color es un par (claro, oscuro) con 4.5:1 en ambos modos.
- **Comando:** `/impeccable colorize`

### [P1] La decisión de triaje no está modelada
- **Qué:**
  - sugerencia visible sin datos;
  - justificación siempre obligatoria;
  - «Reclasificar» sin efecto;
  - dos primarios y dos clics;
  - «Guardar» debajo del pliegue.
- **Arreglo:**
  - estado vacío: «Complete los signos vitales para ver la sugerencia»;
  - un único primario «Confirmar nivel N» (Enter), anclado al pie del panel;
  - «Reclasificar» (secundario) despliega el selector 1–5 y la justificación con contador;
  - «Cancelar» como botón de texto.
- **Comando:** `/impeccable clarify`

### [P1] Se rompe en el área mínima (1093×614)
- **Qué:**
  - la grilla de Trauma Shock (213 px) no cabe en 175 px e invade la de UCI;
  - hay estados truncados («Disponi…»);
  - la cola solo muestra unos 73 px;
  - la app tiene alto fijo de 720 px con `overflow:hidden`, así que «Guardar triaje» no se puede alcanzar.
  
  Tres columnas fijas no admiten 40 camas más el área de Hospitalización.
- **Arreglo:**
  - el mapa en filas por área, con casillas de ancho fijo (unos 96×52) que pasan a la línea siguiente al redimensionar;
  - la cola dentro de un `CTkScrollableFrame`;
  - el pie de acciones del triaje fuera del área con desplazamiento.
- **Comando:** `/impeccable layout`

### [P1] El foco de teclado casi no se ve, y la validación es nativa
- **Qué:**
  - el foco de los campos es un borde de 0.8 px;
  - el borde del campo en reposo tiene 1.75:1;
  - el orden de Tab pasa por los síntomas antes de llegar al panel;
  - los errores usan la burbuja del navegador.
- **Arreglo en CTk:**
  - con `<FocusIn>`/`<FocusOut>`, borde de 2 px en el color de foco para campos, botones y casillas;
  - el error en un `CTkLabel` bajo el campo, más el borde de error;
  - el orden de Tab definido a mano.
- **Comando:** `/impeccable harden`

## Alertas por persona

**Alex (usuario experto):**
- no hay atajos;
- Enter dispara la validación nativa en lugar de confirmar;
- confirmar exige dos clics;
- pierde tiempo en 3 entradas de menú vacías.

**Sam (accesibilidad):**
- texto de 7 px;
- #777/#2B2B2B = 3.16:1 y placeholder #666 = 2.7:1;
- casillas de verificación de 13×13 px;
- blanco sobre el botón azul = 4.02:1;
- «PRIORIDAD I» = 4.18:1.

**Rosa, enfermera de triaje** (laptop 1366×768 al 125 %, luz fluorescente):
- no ve «Guardar» porque queda recortado;
- escribe la PA como texto libre;
- no hay rangos visibles y la SatO2 150 se acepta;
- la sugerencia siempre dice I;
- tiene que justificar aunque esté de acuerdo;
- la pantalla oscura refleja la luz.

**Ing. Quispe, jurado** (proyector a unos 6 m):
- no lee nada por debajo de 12 px;
- los bordes de 1 px sobre gris oscuro se pierden en la proyección;
- el reloj «EN VIVO» no avanza;
- el KPI dice 86 camas y el mapa muestra 32.

## Observaciones menores

- Pesos intermedios (550–850) e interletrado: CTk no los reproduce. Se usa solo normal o negrita, y la jerarquía se marca con el tamaño.
- Tokens sin sistema: 8 grises de superficie, 6 de borde y espacios de 3, 6, 7, 10, 12, 14 y 18 px. Se unifican en una escala 4 / 8 / 12 / 16 / 24.
- La guía no coincide con la app: dice «Tablero de Camas 30px 800», pero la app lo muestra a 17 px.
- «Seleccione una cama para ver su detalle» promete algo que no existe; el brief pide el mapa de solo lectura.
- Textos: «Gestión de Urgencias» → «Emergencia» (como se dice en Perú). «Cola de espera de triaje» en el tablero → «de cama». «0 minutos» → «Inmediato».
- «Área recomendada: Trauma Shock» en el triaje adelanta una decisión que pertenece a la asignación de cama.

## Preguntas para el equipo

1. ¿Y si el nivel de triaje fuera lo único con color saturado, y las camas hablaran con tintes y texto?
2. ¿Por qué «Confirmar» y «Reclasificar» pesan igual, si una es la rutina y la otra la excepción auditada?
3. ¿El tablero tiene que ser una matriz de tarjetas, o una banda densa por área donde quepan 40 camas legibles en 1093×614?
4. ¿Qué entiende el jurado en los primeros 3 segundos, a 6 m del proyector?

## Qué se puede reproducir en CustomTkinter

| Recurso | ¿En CTk? | Sustituto |
|---|---|---|
| Superficies planas, bordes y radios | Sí | Reducir a 3–4 superficies, con pares claro/oscuro |
| Pesos 550–850 e interletrado | No | Solo normal o negrita; jerarquía por tamaño |
| Fuente Inter | Sí, cargando el TTF | Segoe UI como respaldo |
| Íconos SVG | No | PNG con `CTkImage(light_image, dark_image)` |
| Franja roja superior de 3 px | Parcial | `CTkFrame` de 3 px de alto |
| Anillo de foco | No | `<FocusIn>` → borde de 2 px |
| Spinner «Procesando» | No | Botón deshabilitado con el texto «Verificando…» |
| Modal con fondo oscurecido | Parcial | `CTkToplevel` con `grab_set()` y Esc para cerrar |
| Cifras tabulares | No | Las cifras de Segoe UI son de ancho fijo |
| Error bajo el campo, cola con desplazamiento, hover | Sí | — |
