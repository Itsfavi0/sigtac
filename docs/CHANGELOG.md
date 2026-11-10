# SIGTAC — Changelog

> Registro cronológico de cambios, decisiones y avances relevantes del proyecto.
> No registrar cada modificación mínima de código; registrar cambios que afecten arquitectura, funcionalidad, reglas de negocio, estructura o dirección del desarrollo.

---

## [2026-11-10] — Correcciones de la revisión de experiencia de uso

### Cambio
Revisión hecha con el usuario siguiendo un caso de punta a punta en una guardia de noche (triaje → cama → alta → limpieza → tablero), a 1093×614, con los principios de `PRODUCT.md`. Se corrigió:
- **Seguridad:**
  - **Limpieza:** Enter y el doble clic en una casilla solo eligen; se confirma únicamente con el botón, que nombra la cama. Una cama confirmada por error quedaría «disponible» estando sucia.
  - **Confirmaciones** (alta, referir, fuga, fusionar…) con «No» elegido de entrada: un Enter apurado no confirma.
- **Teclado:** al pasar con Tab a un campo que quedó bajo el borde, la pantalla baja hasta él (`Desplazable`, con `<<TraverseIn>>`). En Triaje, SatO₂ quedaba con 14 de sus 36 px a la vista y «3. Síntomas», oculta.
- **Tablero:** el indicador «Prioridad 1–2 sin cama» dice en rojo «N fuera de plazo» si alguno de nivel 1–2 pasó su plazo, y el pie de la cola avisa si alguno de los que no caben, de cualquier nivel, lo está. El NN que llevaba 1 h 11 min quedaba escondido en «2 pacientes más en espera».
- **Rapidez:**
  - **Avisos sin diálogo:** las operaciones de todos los días avisan en el encabezado («✓ Alta registrada…», en verde, unos segundos) y ya no abren un diálogo que había que cerrar (`avisar_exito`). La clave entregada en persona y el PDF guardado siguen con diálogo.
  - **Gestión de camas:**
    - la primera cama compatible queda elegida («Asignar OBS-01 a …» en dos clics, o Enter y Enter);
    - «Con cama» muestra primero las reservadas;
    - se puede buscar por nombre o código de cama (Escape borra).
- **Claridad:**
  - **El botón principal deshabilitado se ve gris**: en azul parecía disponible. Su texto sigue diciendo qué falta. «Reclasificar» nace deshabilitado.
  - **Triaje, en «Nuevo»:** un botón «2 esperan triaje · Ver la cola» lleva a la cola; el selector de arriba se pasaba por alto.
  - **Textos que no caben terminan en «…»** (`EtiquetaRecortada`): «Médico de Emerge…» en la barra lateral y los motivos largos en las listas de Gestión de camas.
- **`ListaSeleccion`:** su barra estiraba la lista a 200 px (el alto por omisión de `CTkScrollbar`), y las camas compatibles mostraban 4 filas en lugar de 2.

### Archivos afectados
- `views/componentes/errores.py`, `botones.py`, `desplazable.py`, `seleccion.py`, `tarjetas.py`, `recorte.py` (nuevo), `__init__.py`; `views/tema.py`
- `views/app_principal.py`, `triage_view.py`, `camas_view.py`, `limpieza_view.py`, `pacientes_view.py`, `admin_view.py`, `dashboard_view.py`
- Pruebas: `tests/test_recorte.py` (nuevo), `test_componentes.py`, `test_app_principal.py`, `test_tema.py`, `test_seleccion.py`, `test_camas_view.py`, `test_triage_view.py`, `test_limpieza_view.py`, `test_dashboard_view.py` y los dobles de `test_admin_view.py` y `test_pacientes_view.py`
- `docs/`

### Motivo
La revisión con el usuario: 15 puntos, ordenados por impacto en una guardia real. El usuario pidió corregirlos todos.

### Impacto
- Pruebas: **2332 pasan** (antes 2274).
- Sin cambios de controladores, modelos ni esquema.
- **Decisión pendiente del equipo resuelta:** el botón principal deshabilitado (pendiente desde el 2026-10-30) ahora se ve gris.
- **Revisión independiente** (con calibración: un color escrito a mano plantado en una copia del tablero, que el revisor encontró). Encontró y se corrigió:
  - Escape en la búsqueda dejaba el texto guía como texto escrito y el filtro dejaba de funcionar;
  - el desplazamiento al foco usaba `<FocusIn>`, que llega también con un clic, por cada contenedor y al volver a la ventana o cerrar un diálogo, y movía la vista sin motivo. Ahora usa `<<TraverseIn>>`, que Tk genera solo al recorrer con Tab;
  - en una recarga, la cama preelegida reemplazaba en silencio a la que el usuario había elegido y otra PC reservó: ahora se preelige solo al elegir al paciente;
  - «2 fuera de plazo» bajo «Prioridad 1–2 sin cama» contaba también al nivel 3: ahora cuenta solo los del título;
  - con la lectura fallida, borrar la búsqueda hacía decir «Ninguna cama tiene un paciente asignado»; y la búsqueda quedaba puesta tras una operación;
  - el recordatorio de Triaje era una etiqueta clicable a la que no se llegaba con el teclado: ahora es un botón;
  - en oscuro, el botón deshabilitado (#2F2F2F) no se distinguía de la tarjeta: ahora #3A3A3A (contraste 4,51:1);
  - comentarios que contaban la historia del código (van aquí, no en el código);
  - en la segunda pasada: borrar la búsqueda vacía tras una operación le quitaba el texto guía (ahora se borra solo si hay algo escrito), y el foco que pone el código (Triaje, al pasar al registro o a los signos) también baja la pantalla hasta el campo (`Desplazable.mostrar_foco`).

### Pendientes
- Los `BotonSecundario` deshabilitados se distinguen poco de los habilitados (solo cambia el tono del texto); junto al principal gris, parecen más disponibles que él. Se podría atenuar su borde.

### Decisiones
- **Punto 4 descartado** («textos guía poco legibles»): `COLOR_PLACEHOLDER` ya tiene ~5,5:1 de contraste (AA). Oscurecerlo lo confundiría con un valor escrito.
- **Punto 15 queda para el equipo:** el rojo significa «Ocupada» en la matriz y «Nivel 1» en la cola. Es un cambio de la paleta aprobada.
- **La cola del tablero no se reordena** por plazo: el orden por gravedad es clínico. El aviso va en el indicador y en el pie.
- **El aviso de éxito va en el encabezado**, en el lugar de la descripción (dos renglones como mucho), y no en una ventana flotante: ese lugar no tapa ningún botón.

---

## [2026-11-10] — Administración usa la fila de acciones compartida

### Cambio
- `views/admin_view.py` usa `fila_acciones` (`views/componentes/columnas.py`) en sus 4 filas de botones (acceso y desbloqueo, crear cuenta, ver bitácora, dar de baja) y se borra su `_fila_acciones` propio, que era igual.

### Archivos afectados
- `views/admin_view.py`, `docs/`

### Motivo
El pendiente de la entrada anterior: con dos copias, cambiar la separación de los botones en `columnas.py` habría dejado a Administración distinta de Gestión de camas y Limpieza sin que nadie lo decidiera (una regla, un dueño).

### Impacto
- Sin cambio visible: la misma separación (`ESPACIO_2`). Pruebas: **2274 pasan**.

---

## [2026-11-10] — Limpieza con el estilo de Gestión de camas; el tablero se acomoda una sola vez

### Cambio
- **Limpieza** (`views/limpieza_view.py`), con la forma de la pestaña Mantenimiento de Gestión de camas (vista previa aprobada por el usuario):
  - **resumen** arriba: «4 camas por limpiar» (con el punto del color de «En limpieza») y «La más antigua: 1 h 00 min». Sin camas, solo «0 camas por limpiar»;
  - a la izquierda, **las camas como casillas** (código y tipo), de la más antigua a la más reciente, que se eligen con clic o teclado; Enter confirma;
  - a la derecha, **la cama elegida**: código, tipo · área y «En limpieza desde las 09:00 (1 h 00 min)», y el botón «Confirmar limpieza de HOS-06». Sin elegir, dice qué hacer;
  - al volver a la pantalla o si otra PC ya la confirmó, la cama elegida sigue elegida si sigue en la lista.
- **`views/componentes/columnas.py`** (nuevo; extracción aprobada por el usuario): `dos_columnas`, `etiqueta_resumen`, `aviso_columna` y `fila_acciones`, que eran métodos privados de Gestión de camas. Gestión de camas las usa sin cambiar cómo se ve.
- **Tablero tras el login:** la matriz de camas, cuando va a necesitar su barra, se reparte ya para el ancho que le deja. Antes se acomodaba dos veces y la segunda redibujaba las 34 casillas (de 1,75 s a 1,44 s en la demo). Con la cubierta del login, el tablero aparece completo de una vez; lo único que cambia después es el reloj.
- **`ListaSeleccion`:** todas las casillas de una fila miden lo mismo; antes la última era 8 px más ancha y en Limpieza se cortaba «Hospitalización».
- **`Desplazable`:** no decide la barra mientras la pantalla se construye (lo visible mide 1 px). Una barra colocada y quitada en ese momento quedaba a la vista sin lugar, tapando el borde derecho de la tarjeta.
- **Demo:** `CamasDemo.solicitudes_limpieza` ordena como el DAO (la más antigua primero); antes devolvía el orden inverso.

### Archivos afectados
- `views/limpieza_view.py`, `views/camas_view.py`
- `views/componentes/columnas.py` (nuevo), `views/componentes/__init__.py`, `views/componentes/seleccion.py`, `views/componentes/desplazable.py`, `views/componentes/matriz.py`
- `prototipo/demo.py`
- Pruebas: `tests/test_limpieza_view.py`, `tests/test_columnas.py` (nuevo), `tests/test_seleccion.py`, `tests/test_matriz.py`, `tests/test_componentes.py`
- `docs/`

### Motivo
Los dos opcionales de «Para retomar»: Limpieza era la única pantalla de trabajo con una tabla gris y un botón, y el tablero se reacomodaba unos segundos después del login.

### Impacto
- Pruebas: **2274 pasan** (antes 2251).
- Sin cambios de controladores, modelos ni esquema: RN-07 y RN-08 siguen igual.
- Gestión de camas se ve igual: el revisor comparó el árbol completo de widgets de sus tres pestañas antes y después de la extracción (597 líneas); solo cambiaron los márgenes de las casillas.

### Decisiones
- **La causa del tablero no era la precarga** (la hipótesis anotada antes): sin precarga se reacomodaba igual. Medido: la matriz se acomodaba para 1027 px, mostraba su barra y volvía a acomodarse para 1011 px, 0,85 s después.
- **Limpieza sigue a Mantenimiento** y no a «Esperan cama»: se elige una cama, no un paciente. Las casillas llevan el tipo en el segundo renglón, como las camas compatibles, porque todas están «En limpieza».
- **Una solicitud sin su cama en el mapa** (una cama dada de baja mientras esperaba limpieza: el mapa solo trae las activas) no se muestra, y el resumen cuenta solo las que se muestran.
- **Minutos en texto corrido sin el cero** («7 min»), como en el tablero y en Reportes; «07 min» queda para las columnas alineadas.
- **Proceso de la interfaz** (skill ui-consistency):
  - checklist de 12 puntos desde Gestión de camas;
  - calibración con otro agente sobre una copia con un aviso escrito a mano en lugar de `aviso_columna`, que encontró;
  - revisión de un agente que no escribió el código. Encontró, y se corrigió:
    - el resumen contaba también las solicitudes sin casilla («4» con 3 casillas);
    - «07 min» en texto corrido;
    - «Ninguna espera» sin camas, un texto que no estaba aprobado;
    - pruebas que comparaban márgenes sin escalar (fallarían con el zoom de Windows al 125 %);
    - una prueba de Enter que no pasaba por la lista;
    - faltaba el caso de otra PC que ya confirmó la cama y esta sale de la lista.

### Pendientes
- `views/admin_view.py` conserva su propio `_fila_acciones`, igual a `fila_acciones`: unificarlo en otra tarea.
- Con zoom de pantalla, el margen entre casillas de `ListaSeleccion` puede quedar 1 px menor que la separación (se redondea antes de escalar).

---

## [2026-11-10] — Cambio de pantalla en un solo paso (Cubierta)

### Cambio
- **`Cubierta`** (`views/componentes/cubierta.py`), pieza compartida nueva:
  - al cambiar de pantalla, fotografía el área (`PIL.ImageGrab`) y pone la foto encima, en una ventana aparte sin bordes;
  - hace el cambio debajo;
  - quita la foto cuando Windows avisa que ya no queda nada visible por pintar (`GetUpdateRect` sobre cada widget, con `ctypes`). Revisa cada 15 ms, cuando Tk está libre, y como máximo espera 1,5 s de reloj;
  - resultado: la pantalla nueva aparece completa, de una vez, en lugar de dibujarse por partes.
- **Cambio de módulo** (`views/app_principal.py`): `mostrar()` abre el módulo bajo una cubierta que tapa el encabezado y el contenido. El menú queda fuera y se marca al instante.
- **Login ↔ ventana principal** (`main.py`): `Aplicacion._cambiar` recibe una fábrica y hace el cambio bajo una cubierta de toda la ventana. Primero construye la pantalla nueva y después quita la anterior: si la construcción falla, la anterior sigue.

### Archivos afectados
- `views/componentes/cubierta.py` (nuevo), `views/componentes/__init__.py`
- `views/app_principal.py`, `main.py`
- Pruebas: `tests/test_cubierta.py` y `tests/test_main.py` (nuevos), `tests/test_app_principal.py`
- `docs/`

### Motivo
El usuario veía «toscos» los cambios de pantalla. Medido en la demo con capturas de pantalla desde otro proceso:
- después de un clic en el menú, la pantalla seguía cambiando unos 250 ms (casi 1 s en el tablero), en 6 a 16 pasos visibles: fondo vacío, cajas grises y, al final, los textos;
- del login a la ventana principal se veían 39 pasos.

### Impacto
- **Cambio de módulo:** 16 de 16 cambios medidos en un solo paso con la versión final (antes, de 6 a 16). La pantalla final aparece unos 100 ms más tarde que antes; en el tablero, la anterior queda quieta hasta ~0,6 s. La ventana nunca perdió el primer plano.
- **Login → ventana principal:** la foto tapa hasta el límite (1,5 s) y después se ve el tablero terminando de acomodarse (ver Pendientes). Cerrar sesión: 2 pasos.
- **Fuera de Windows,** con la ventana oculta (las pruebas) o si la foto falla, el cambio se hace sin foto, a la vista.
- Pruebas: **2251 pasan** (antes 2227).

### Decisiones
- **Por qué una foto en otra ventana.** Tk dibuja cada widget directamente en la ventana, sin una imagen intermedia, y CustomTkinter no permite animaciones ni transparencias (`PRODUCT.md`). Se midieron y descartaron:
  - **un telón del color del fondo dentro de la ventana:** Windows no pinta lo que otra parte de la misma ventana tapa, así que la pantalla se dibujaba por partes igual al quitarlo;
  - **preparar la pantalla nueva tapada por la anterior:** por la misma razón;
  - **deslizar o fundir pantallas:** con `place()` cada cuadro redibuja decenas de widgets y se ve entrecortado; además, el brief pide «cambio de módulo inmediato, sin transición».
  - Debajo de *otra* ventana, Windows sí pinta: por eso la foto va en una ventana aparte.
- **Decisión del usuario:** aplicarlo en el cambio de módulo y en el login, a cambio de la pequeña espera con la pantalla anterior quieta y de usar la API de Windows. El menú se marca al instante, aunque la foto todavía muestre el título anterior.
- **Sin `update()`:**
  - la foto se pinta directamente con Windows (`StretchDIBits`) y se le quita la animación de aparición (`DwmSetWindowAttribute`): sin ella, en 2 de 16 cambios se veía un instante el área vacía;
  - la etiqueta de la foto se coloca con `place` y medidas fijas: con `pack` mediría 1×1 hasta que Tk atienda sus eventos, y se pintaba un solo píxel;
  - así, mientras se pone la foto, no corren clics ni temporizadores. Con `update()` (la primera versión), un segundo clic rápido se perdía, la precarga podía correr con la sesión ya cerrada y cerrar sesión en ese instante daba `TclError`.
- **Cuándo se quita:**
  - dos revisiones seguidas sin nada por pintar;
  - cada revisión corre cuando Tk está libre (`after_idle`) y antes hace sus tareas pendientes (`update_idletasks`). Windows da una zona por pintada apenas Tk recibe el aviso, aunque Tk la dibuje después;
  - el límite se mide con reloj, no contando revisiones, porque con Tk ocupado las revisiones se atrasan;
  - las revisiones se programan en la ventana raíz: si el área se destruye con una revisión pendiente, esta termina sin error.
- **Si la foto o su ventana fallan** (`OSError`, `TclError`), el cambio se hace igual, sin foto, y no queda ninguna ventana suelta.
- **Las mediciones** se hicieron con capturas desde otro proceso, porque capturar desde un hilo frenaba a Tk. Una medición quedó descartada: la ventana medida estaba tapada por otra aplicación, y Windows no pinta lo que tapa la ventana de otra aplicación.
- **Proceso de la interfaz** (skill ui-consistency):
  - checklist de 10 puntos para esta zona;
  - calibración con otro agente sobre una copia con un log en f-string plantado, que encontró;
  - la revisión la hizo, en dos pasadas, un agente que no escribió el código. Encontró:
    - los problemas de `update()`;
    - que `pintar_ya` pintaba un solo píxel (la etiqueta aún medía 1×1);
    - dos pruebas que no comprobaban que el cambio ocurriera dentro de la cubierta;
    - una prueba de «ya está pintada» que no miraba el tamaño;
    - tareas `after` huérfanas en las pruebas;
    - llamadas a Windows sin tipos declarados.
  - Todo corregido. También se quitó un filtro de ventanas ocultas que no hacía nada: Windows no les guarda partes por pintar.

### Pendientes
- **Tablero tras el login:** la primera vez, la matriz de camas se sigue reacomodando entre 2 y 4 s (las casillas cambian de ancho y los textos pasan de cortados a completos). Pasa igual sin la cubierta: coincide con la precarga de las otras pantallas, que empieza a los 500 ms (`MS_ANTES_DE_PRECARGAR`). Se podría esperar a que el tablero termine de dibujarse antes de precargar.
- Probar con la pantalla al 125–150 % y con dos monitores de distinto DPI (en esta PC no se pudo).

---

## [2026-11-06] — Gestión de camas rediseñada y lista elegible compartida (ListaSeleccion)

### Cambio
- **Gestión de camas** (`views/camas_view.py`), con el diseño aprobado por el usuario a partir de una vista previa:
  - **resumen** bajo el título: «4 esperan cama · 2 con prioridad 1–2 · 15 camas libres» (etiquetas grises como las del tablero; la de prioridad y la de camas libres, con un punto de color). Si la carga falla, no se muestra;
  - cada pestaña tiene **dos columnas**: a la izquierda la lista para elegir y a la derecha lo elegido y sus acciones;
  - **«Esperan cama»:**
    - la cola como en el tablero: el cuadro del nivel, nombre, motivo y la espera, en rojo si pasó el plazo;
    - a la derecha, la ficha del paciente: el nivel en grande, «Nivel 1 · Rojo · Inmediato», documento y motivo;
    - debajo, sus camas compatibles como casillas, con el tipo en el segundo renglón;
    - el botón dice la acción completa: «Asignar TS-03 a M. Salazar»;
  - **«Con cama»:**
    - cada paciente con su nivel, el estado de la cama desde cuándo («Ocupada desde las 12:36») y el código de la cama con el tinte de su estado;
    - a la derecha, la ficha del paciente, la casilla de su cama junto a la acción principal y las otras acciones;
  - **«Mantenimiento»:** las camas libres o fuera de servicio como casillas; a la derecha, la cama elegida, el motivo (si está libre) y la acción.
- **`ListaSeleccion`** (`views/componentes/seleccion.py`), pieza compartida nueva (extracción aprobada por el usuario):
  - una lista de filas o casillas que se eligen con un clic o con el teclado (Tab entra, las flechas eligen y Enter activa), con el borde de foco alrededor;
  - se usa como `TablaDatos`: `cargar`, `seleccionado`, `seleccionar`, `sin_lectura`, `cambiar_texto_vacio`. Además tiene `elegir` (como el usuario, avisa) y `elemento(id)`.
- **`TarjetaCama(detalle=...)`:** un segundo renglón opcional en lugar del estado.

### Archivos afectados
- `views/componentes/seleccion.py` (nuevo), `views/componentes/tarjetas.py`, `views/componentes/__init__.py`
- `views/camas_view.py`
- Pruebas: `tests/test_seleccion.py` (nuevo), `tests/test_camas_view.py`, `tests/test_componentes.py`
- `docs/`

### Motivo
El usuario veía Gestión de camas «algo simple», sin vida: eran dos tablas grises y un botón. Hoy se ve quién es el más urgente, cuánto lleva esperando y qué camas le sirven, con los mismos colores y piezas del tablero.

### Impacto
- Pruebas: **2227 pasan** (antes 2197).
- Sin cambios de controladores, modelos ni esquema: las reglas y los mensajes siguen igual (RN-01, RN-05, RN-07).
- **Tiempos medidos en la demo** (hasta que se ve, en 1093×614):
  - cambiar de pestaña: de 0,35 a 0,6 s, como la versión anterior con tablas (0,2–0,6 s);
  - elegir: de 0,05 a 0,2 s;
  - recargar al volver a la pantalla: 0,2–0,4 s.

### Decisiones
- **Rendimiento:**
  - **Lo que costaba:** una fila o casilla de CustomTkinter tarda de 60 a 100 ms en construirse en esta PC, y la primera versión tardaba de 1,5 a 2,5 s en cada cambio. Se midió cada paso y se perfiló.
  - **Reutilizar:** la lista repinta las filas que siguen (`actualizar`) y solo crea las nuevas. Una fila o casilla que no cambió no se repinta.
  - **De a pocos:** se crean al instante las que se ven (5 filas o 12 casillas); el resto, de a 2 por turno, con la ventana respondiendo. Las listas de las pestañas ocultas se preparan de fondo, así al abrirlas ya existen.
  - **La barra de cada lista** se mueve cuando la ventana termina de acomodarse, y solo si cambió: `CTkScrollbar` redibuja toda la ventana cada vez que se mueve.
  - **El alto de la tarjeta no cambia al elegir.** Si crecía, aparecía la barra de la pantalla, cambiaba el ancho y todo se volvía a acomodar varias veces (1,8 s). Por eso:
    - la ficha de «Esperan cama» ocupa su lugar aunque no haya paciente (dice qué hacer);
    - se ven 2 filas de camas compatibles;
    - en «Con cama», la casilla va junto al botón principal.
  - **Lo que se descartó:** se probó escribir los textos de las filas con `tk.Label` (solo un 35 % más rápido, con colores a mano en cada modo) y quitar las esquinas de los marcos invisibles (15 %).
- **La lista elegida y la elegida en la lista:**
  - la fila elegida lleva el borde del azul de foco y el fondo gris de lo activo; la casilla, solo el borde (su fondo es el de su estado);
  - el foco de teclado es un borde alrededor de toda la lista, como en los campos.
- **Teclado:**
  - Enter en la cola lleva a las camas, y Enter en una cama la asigna;
  - en Mantenimiento, Enter en una cama libre lleva al motivo (es obligatorio) y en una fuera de servicio la devuelve.
- **El texto de la columna derecha sin nada elegido** dice qué hacer («Elija un paciente de la lista para ver su cama y sus acciones.»).
- **Proceso de la interfaz** (skill ui-consistency):
  - checklist de 11 puntos a partir de la vista previa y de la fila del tablero;
  - la revisión la hizo un agente que no escribió el código. Antes se probó con otro agente y una diferencia plantada (un color escrito a mano), que encontró;
  - el revisor marcó 17 puntos. Corregidos:
    - las camas compatibles se rehacían enteras en cada recarga, porque la pantalla vaciaba la lista antes de volver a elegir al paciente; ahora se repintan;
    - su título decía «(0)» cuando no se pudieron leer, y el nivel sin su color («nivel 1» → «nivel 1 · Rojo»);
    - sin paciente elegido, la ficha repetía la instrucción de la lista y del botón; ahora dice «Ningún paciente elegido»;
    - las etiquetas de «Con cama» y Mantenimiento repetían el título de la tarjeta («Reservadas u ocupadas», «Por tipo de cama»);
    - la espera, alineada a la derecha y con ancho fijo, como en el tablero;
    - `ListaSeleccion` usa `tema.escala` y no un método interno de CustomTkinter; una lista oculta no calcula su desplazamiento (no tiene alto); su docstring dice que `seleccionar` no avisa.
  - Dejados así, con su motivo:
    - la fila mide 52 px y su nivel 28, como en la vista previa, con aire para el borde de la fila elegida;
    - las etiquetas del resumen miden 28 px (el 26 de la píldora del tablero no es múltiplo de 4);
    - en «Con cama», cada fila lleva el código de la cama teñido: una casilla entera no cabe en una fila;
    - la elegida se marca con el borde azul, y el foco con otro borde alrededor de toda la lista.
  - No son de este cambio, porque ya estaban: «espera limpieza» frente a «pasa a limpieza» en los avisos, y «Cama X…» frente a «La cama X…».

### Pendientes
- Limpieza y el Tablero podrían usar `ListaSeleccion` (casillas elegibles), si se quiere el mismo estilo.
- Las pruebas de foco comprueban que se pide (la ventana de pruebas está oculta y no recibe el foco).

---

## [2026-11-06] — Paleta fría en claro, casillas de cama con tinte y cambio de pantalla sin reconstruir

### Cambio
- **Paleta del modo claro** (pedido del usuario: «demasiado fuerte a la vista»), en `views/tema.py`:
  - sin blanco puro ni negro puro: superficies `#FAFBFC` sobre un fondo gris azulado `#ECEFF3`, barra `#F6F8FA` y texto `#252A31`;
  - grises fríos para bordes, divisores, etiquetas y textos secundarios;
  - el azul principal, algo menos saturado (`#2563B8`);
  - el modo oscuro no cambia.
- **Casillas de la matriz de camas** (`TarjetaCama`): un fondo teñido del color del estado, un borde suavizado y, a la izquierda, una franja del color del estado. Los colores están en `tema.py` (`COLOR_FONDO_ESTADO_CAMA`, `COLOR_BORDE_ESTADO_CAMA`). El gris de «Fuera de servicio» en claro pasa a `#7A7F87`. La leyenda del tablero usa la misma muestra.
- **Cambio de pantalla** (`AppPrincipal`):
  - cada pantalla se construye una sola vez por sesión; al cambiar de módulo se oculta y al volver se muestra como quedó;
  - al volver, la pantalla relee sus datos sin diálogo (`al_mostrar()`); el tablero deja de actualizarse mientras está oculto (`al_ocultar()`);
  - con `precargar=True` (`main.py` y la demo), después de abrir la primera pantalla se construyen las demás, ocultas, una por vez.
- **El tablero ya no rehace sus 36 casillas al releer:** si las camas son las mismas, `MatrizCamas.cargar` repinta las que ya tiene (`TarjetaCama.mostrar`), y una cama que no cambió no se repinta. Vale también para la actualización cada 30 s.

### Archivos afectados
- `views/tema.py`, `utils/colores.py` (el gris de «Fuera de servicio»)
- `views/app_principal.py`, `main.py`, `prototipo/ver.py`
- `views/componentes/tarjetas.py`, `views/componentes/matriz.py`
- Las 7 pantallas de `views/` (`al_mostrar`; el tablero, también `al_ocultar` y la leyenda)
- Pruebas: `test_tema.py`, `test_app_principal.py`, `test_componentes.py`, `test_matriz.py` y una por pantalla
- `docs/`

### Motivo
Pedidos del usuario tras revisar la app: el modo claro cansaba la vista, el mapa de camas se veía «flojo» y el cambio de pantalla era brusco.

### Impacto
- Pruebas: **2197 pasan** (antes 2161).
- Sin cambios de esquema ni de controladores.
- **Cambio de pantalla, medido en la demo** (de pulsar el menú a terminar de dibujar):
  - antes, de 0,4 a 1,3 s;
  - ahora, al volver a un módulo, de 0,1 a 0,4 s: construir pasa de 300–760 ms a 11–53 ms;
  - el tablero pasa de 1,3 s a 0,39 s.
- **Cambios visibles:**
  - el modo claro, más suave;
  - las casillas de cama, teñidas;
  - al volver a un módulo se encuentra como se dejó (p. ej. un triaje a medio escribir).

### Decisiones
- **Tono frío** (elegido por el usuario entre frío y cálido, con capturas de ambos): se ve clínico y descansa la vista.
- **Contrastes de la paleta:**
  - el texto de ejemplo de los campos quedaba en 4,02:1 sobre el fondo nuevo; se oscureció a `#626974` (4,8:1), y sigue más claro que el texto secundario para no confundirse con un dato escrito;
  - el texto del estado en la casilla va en el color de texto principal: el secundario bajaba a 3,8:1 sobre el tinte oscuro de «En limpieza».
- **Tinte de las casillas, «franja + tinte»** (aprobado por el usuario con vista previa; también se probó un borde de 2 px): el estado se indica con la franja (3:1 sobre su tinte, comprobado en `test_tema.py`) y con el texto, nunca solo con el color.
- **Sin animaciones:** CustomTkinter no las hace bien y `PRODUCT.md` pide que navegar sea inmediato. Lo que molestaba era la espera, no la falta de transición.
- **La precarga se detiene si la BD no respondió:** si no, cada pantalla abriría su propio diálogo de error. Mientras se construye una pantalla oculta, su aviso de actualización no cambia el encabezado de la visible. Si una pantalla oculta pone el foco en su primer campo, la ventana se lo devuelve a la visible.
- **`precargar` es opcional:** en las pruebas, una precarga pendiente construiría pantallas cuando otra prueba procese eventos.
- **La pantalla nueva se construye antes de ocultar la anterior:** mientras tanto se sigue viendo la anterior, no un hueco.

### Pendientes
- **Gestión de camas con más vida** (cola con la etiqueta del nivel, camas compatibles como casillas, resumen y estados vacíos): la propuesta va primero como vista previa.

---

## [2026-11-06] — Fase 7: detalles menores de la revisión de tester

### Cambio
- **Mensajes sin nombres técnicos:**
  - los errores de estado dicen «en estado «En atención (con cama)»», no «EN ATENCIÓN (CON CAMA)» (`EpisodioEmergencia`, `Cama`, y los de concurrencia de `CamaDAO` y `EpisodioDAO`, con `EstadoX.texto`);
  - un texto obligatorio vacío dice «Los nombres son obligatorios.», no «nombres es obligatorio.». `_validar_texto` (`models/persona.py`) recibe el mensaje completo;
  - el filtro y la columna «Tabla» de la bitácora dicen «Síntoma», «Área», «Episodio de emergencia»… (`NOMBRES_TABLA` en `admin_view.py`).
- **Trato de usted en el PDF:** «Compruebe que la carpeta exista…» e «Indique dónde guardar el reporte.».
- **Sin género supuesto:** «Se dio de baja a Carmen Rojas Llanos.» y «Se reactivó a…» (antes «quedó dado de baja» y «fue reactivado»).
- **Coma decimal** en todo lo que lee el usuario: el PDF («45,5 min», «37,5 %»), los criterios del triaje («Temperatura 39,5 °C ≥ 39,5 °C») y los rangos de los signos («25–45»). Un solo dueño: `utils/numeros.py` (`texto_decimal`), que usan el modelo, la vista y el PDF.
- **Síntomas largos:** «Alteración de la Conciencia (Glasgow < 8)» y «Dificultad Respiratoria Severa (Disnea)» se parten en dos líneas en lugar de cortarse a 1093 de ancho (`ajustar_casilla` en `campos.py`; Triaje la aplica al cambiar el ancho de la lista).
- **Todos los errores a la vez:** al confirmar sin datos se marcan todos los campos que no se pueden leer, no solo el primero; el mensaje sigue siendo el del primero. `leer_todos` (`campos.py`) lo usan `CamposPaciente` (Triaje y Pacientes), el paciente sin identificar del Triaje y `CamposPeriodo` (Reportes y Bitácora).
- **PA diastólica ≥ sistólica:** se marcan los dos campos de la presión y se explica bajo los signos («La PA sistólica debe ser mayor que la diastólica.»). La regla sigue siendo del modelo: `SignosVitales.validar_presion`, que también usa el constructor.
- **El botón de Triaje distingue faltar de estar mal:** «Corrija los signos vitales» si hay uno inválido, «Complete los signos vitales» si falta alguno.
- **Tablero:** el cuarto indicador del jefe de guardia se llama «Asignación de cama» (antes «Espera de cama»), con la nota «hoy».
- **Ventana principal:** el aviso de un módulo sin pantalla dice «Esta pantalla no está disponible.» (decía «se agrega en el siguiente paso de la Fase 6»), y su docstring y comentario ya no hablan de pantallas pendientes.
- **Una prueba dependía del zoom de Windows:** `test_sin_barra_el_formulario...` (Triaje) comparaba el margen sin escala y fallaba al 125 %, también con el código anterior. Ahora lo compara con la escala real.

### Archivos afectados
- `utils/numeros.py` (nuevo), `utils/pdf_generator.py`
- `models/persona.py`, `models/triaje.py`, `models/cama.py`, `models/estrategias.py`
- `dao/cama_dao.py`, `dao/episodio_dao.py` (solo el texto del error)
- `views/triage_view.py`, `views/dashboard_view.py`, `views/admin_view.py`, `views/app_principal.py`, `views/reportes_view.py` (un comentario)
- `views/componentes/campos.py`, `views/componentes/paciente.py`, `views/componentes/periodo.py`
- Pruebas: `test_numeros.py` (nueva), `test_estrategias.py`, `test_pdf_generator.py`, `test_persona.py`, `test_triaje.py`, `test_cama.py`, `test_triaje_controller.py`, `test_admin_view.py`, `test_componentes.py`, `test_triage_view.py`, `test_dashboard_view.py`
- `docs/`

### Motivo
Cerrar los detalles menores que dejó la revisión de tester del 2026-11-05: mensajes que el usuario lee con nombres internos o con otro trato, números en otro formato que el resto de la app y formularios que no muestran de una vez todo lo que hay que corregir.

### Impacto
- Pruebas: **2161 pasan** (antes 2136).
- Sin cambios de esquema ni de controladores. Un método nuevo del modelo (`SignosVitales.validar_presion`), con la misma regla de antes.
- **Cambios visibles:** los textos de arriba, la coma decimal, los síntomas en dos líneas, todos los campos con error marcados a la vez y el título del indicador del tablero.

### Decisiones
- **Coma decimal en todo, no solo en el PDF:** el tester lo vio en el PDF, pero la pantalla también mostraba punto («Temperatura 39.5 °C»). Un mismo dato se lee igual en los dos. Los campos siguen aceptando coma y punto (`formato.leer_numero`). La función vive en `utils/` porque la usan `models/`, `views/` y el PDF, como `utils/colores.py`.
- **Los nombres vacíos no se marcan en la pantalla:** `CamposPaciente` solo lee lo escrito; que sean obligatorios lo decide el modelo, que ahora lo dice en castellano. Marcarlos en la vista repetiría esa regla.
- **La PA se valida en la vista llamando al modelo** (`validar_presion`), no copiando la comparación: así la vista sabe qué dos campos marcar y la regla tiene un solo dueño.
- **«Asignación de cama» y la nota «hoy»:** el valor es el promedio de quienes ya recibieron cama hoy, no la espera de quien sigue en la cola. Se probaron «Espera promedio de cama», «Demora en asignar cama» y la nota «asignadas hoy»: a 1093×614 se cortaban (medido con capturas, también con «2 h 05 min», el valor más ancho). Reportes conserva «Espera de cama»: allí la línea de arriba ya dice que son promedios del período y no hay una cola al lado.
- **El aviso de un módulo sin pantalla se conserva:** las pruebas de la ventana principal pasan `pantallas={}` para no construir pantallas reales.

### Pendientes
- **El botón principal deshabilitado se ve igual que el habilitado:** sigue como se decidió el 2026-10-30 (su texto dice qué falta). Cambiarlo afecta a todas las pantallas; queda para que lo decida el equipo.
- **Del segundo triaje:** el aviso final usa el estado leído al buscar (ver la entrada del 2026-11-05).
- **Verificación contra MySQL:** el usuario ejecutó `scripts/verificar_controladores.py` con este código: **97 de 97 comprobaciones correctas**. Ya no queda pendiente.

---

## [2026-11-05] — Fase 7: revisión de tester y tres correcciones de Triaje y la ventana

### Cambio
- **Revisión de tester** (unos 60 casos):
  - Hecha con la app real contra `sigtac_db`, manejando la ventana como un usuario, y con un recorrido de todas las pantallas en la demo (5 roles, claro y oscuro, 4 tamaños).
  - Pasan las 13 pruebas de la Fase 7 de `DEVELOPMENT_PLAN.md` (resumen para el equipo en `docs/ESTADO_EQUIPO.md`).
  - Aparecieron 3 problemas, corregidos aquí, y detalles menores (en «Pendientes»).
- **Segundo triaje desde la pantalla (RN-09):**
  - Antes, buscar en Triaje a alguien que ya estaba en emergencia pedía un motivo y, recién al confirmar, decía que ya tenía un episodio abierto. Al paciente que empeora mientras espera cama no se lo podía volver a triar.
  - Ahora, al buscarlo, Triaje no pide motivo y muestra bajo la ficha dónde está («En emergencia desde las 04:29 · en espera de cama · nivel 3 · Amarillo»). El triaje se agrega a ese mismo episodio.
  - El aviso final dice adónde va el paciente: pasa a la cola de cama, sigue en ella con el nivel nuevo o sigue en su cama.
  - Lógica nueva: `PacienteController.episodio_abierto` (permiso PACIENTES), la regla que ya usaba `abrir_episodio`, ahora pública. `TriajeController.registrar` ya admitía cualquier episodio abierto y no cambió.
- **Cambiar de paciente en Triaje borra los datos clínicos:**
  - Se borran el motivo, los signos, los síntomas y la reclasificación (`_limpiar_clinico`, que también usa `limpiar()`).
  - Ocurre al pasar entre Nuevo y En cola o entre Con documento y Sin identificar, al cambiar el documento ya buscado y al elegir otra fila de la cola.
  - Antes, lo medido a un paciente podía quedar en el triaje de otro.
- **Tamaño mínimo de la ventana: 1093×540** (antes 960×540). Por debajo de 1093 de ancho se cortaban textos, títulos de indicadores y pestañas; en Triaje, «En cola» quedaba en 3 px y no se podía llegar a la cola.
- **Demo:** `TriajeDemo(otro_episodio=...)`, `CamasDemo.abiertos/episodio` y `PacientesDemo.episodio_abierto`, para mostrar el segundo triaje en `prototipo.ver`.

### Archivos afectados
- `controllers/paciente_controller.py`, `views/triage_view.py`, `views/tema.py`
- `prototipo/demo.py`, `prototipo/ver.py`
- Pruebas: `test_triage_view.py`, `test_paciente_controller.py`, `test_tema.py`
- `docs/` (`ESTADO_EQUIPO.md`, nuevo)

### Motivo
Lo encontrado en la revisión de tester de la Fase 7: una regla de negocio (RN-09) sin camino desde la interfaz, un riesgo de mezclar datos clínicos de dos pacientes y una ventana que podía achicarse más de lo que soportan las pantallas.

### Impacto
- Pruebas: **2136 pasan** (antes 2115).
- Sin cambios de esquema. Un método nuevo de controlador, de solo lectura.
- **Cambios visibles:**
  - Triaje reconoce a quien ya está en emergencia;
  - los datos clínicos se borran al cambiar de paciente;
  - la ventana no se achica por debajo de 1093 de ancho.

### Decisiones
- **El segundo triaje se hace en Triaje**, no con un botón en Gestión de camas: quien vuelve a evaluar es la enfermera, y su rol no tiene Gestión de camas. Vale para los tres estados abiertos (espera triaje, espera cama, con cama), como admite el modelo (`agregar_triaje`).
- **Borrar sin preguntar** (decisión del usuario): mezclar datos de dos pacientes es más grave que volver a escribir unos signos. Se borra también el motivo, los síntomas y la reclasificación, que son del mismo paciente. Buscar de nuevo el mismo documento (un segundo Enter) no borra nada, y lo medido antes de la primera búsqueda se conserva para el paciente que se busca.
- **Revisión independiente** (un agente que no escribió el cambio): encontró un caso real, ya corregido. Al ir de la cola a «Nuevo» y volver, la tabla seguía marcando al paciente anterior y elegir otro no borraba lo medido. Corregidos además: un error de la BD al buscar otro documento ya no deja como destino del triaje al paciente anterior (`buscar` olvida antes al paciente si el documento cambió), la línea bajo la ficha lleva la fecha si llegó otro día, y la demo ya edita a quien espera cama.
- **El alto mínimo se mantiene en 540:** CustomTkinter multiplica el mínimo por el zoom de Windows. En una laptop de 1366×768 al 125 %, maximizada, quedan unos 540 px lógicos de alto, así que un mínimo mayor haría la ventana más alta que la pantalla. Lo que no entra a lo alto ya se desplaza.

### Pendientes
- **Detalles menores de la revisión:**
  - mensajes con nombres técnicos («EN ATENCIÓN (CON CAMA)», «nombres es obligatorio.», tablas sin tilde en el filtro de la bitácora);
  - el error del PDF trata de «tú»;
  - «quedó dado de baja» en masculino;
  - punto decimal en el PDF;
  - dos síntomas largos que no caben en su casilla a 1093 de ancho;
  - al confirmar sin datos se marca solo el primer error;
  - PA diastólica ≥ sistólica: el botón dice «Complete los signos vitales» y los campos no se marcan;
  - el indicador «Espera de cama» (esperas ya resueltas) junto a un paciente que lleva horas esperando.
- **Del segundo triaje, menores:** el aviso final («sigue en la cola de cama») usa el estado leído al buscar; si otra PC le asigna cama justo antes de confirmar, el aviso queda desactualizado (el triaje sí se registra bien). Las pruebas del documento editado llaman al manejador, no producen la tecla (la ventana de pruebas está oculta).
- **El botón principal deshabilitado se ve igual que el habilitado:** es una decisión ya tomada (su texto dice qué falta, ver `test_triage_view.py`). Se deja así salvo que el equipo decida otra cosa.
- **Datos de prueba en `sigtac_db`:** «Prueba QA Tester Sigtac» (DNI 48707483), un NN fusionado con ella, un episodio abierto de Rosa Mendoza y una cuenta para el empleado 55555555. Se limpian volviendo a cargar `seed.sql`.
- **Pendiente del usuario:** `scripts/verificar_controladores.py` contra MySQL.

---

## [2026-11-04] — Etapa 1: detalles visuales comunes e íconos

### Cambio
- **Piezas compartidas** (extracciones aprobadas por el usuario):
  - **`Desplazable`** (`views/componentes/desplazable.py`), el contenedor de las 6 pantallas que se desplazan:
    - su barra solo aparece si el contenido no cabe, separada del contenido por `ESPACIO_MINIMO`; sin barra, el contenido llega al borde (no queda un margen vacío);
    - `mostrar_al_pie()` reemplaza el `_parent_canvas` de Pacientes;
    - `reacomodar()` vuelve arriba al cambiar de panel;
    - `al_cambiar_barra` avisa a la pantalla, y el Triaje lo usa para ajustar el margen entre el formulario y el panel.
    - Los atributos internos de CustomTkinter quedan solo en este archivo.
  - **`TablaDatos`:**
    - el borde se pinta con el color de las tarjetas en los dos modos (en oscuro era blanco);
    - la barra solo aparece si no se ven todas las filas. Lo decide Tk por la fracción visible (`yscrollcommand`), sin estimar altos;
    - `sin_lectura()` muestra «No se pudieron leer los datos.» hasta la próxima carga;
    - `al_activar`: Enter, o doble clic sobre la fila elegida.
  - **El texto de un estado** («En limpieza») tiene un solo dueño, `EstadoCama.texto` y `EstadoEpisodio.texto` (`models/estados.py`). Lo usan `formato.texto_estado_cama` (tablero, casillas, Gestión de camas, Reportes) y el PDF.
  - **Medidas a `tema.py`:** `ANCHO_TIPO_DOCUMENTO`, `GROSOR_BORDE`, `DENTRO_DE_TARJETA`, `MUESTRA_LEYENDA`, `RADIO_MUESTRA`, `LADO_ICONO`, `LADO_ICONO_KPI` y `LADO_MARCADOR_KPI`. Se corrigió además el comentario de `ESPACIO`.
- **Pantallas:**
  - **Cuando falla la carga,** las tablas de Camas, Limpieza, Triaje (cola) y Pacientes (NN) dicen que no se pudieron leer los datos, en lugar de «Nadie espera cama». Los contadores del selector van sin cifra («Esperan cama», no «(0)»). Reportes y Administración usan la misma pieza.
  - **Pacientes:**
    - cambiar solo el tipo de documento retira la ficha (`CamposDocumento.al_cambiar_tipo`);
    - después de identificar, el foco vuelve al documento;
    - al elegir el primer NN, la pantalla baja hasta «Identificar», pero no al recorrer la lista con las flechas. Baja solo lo justo (`Desplazable.mostrar_hasta`, con `TablaDatos.y_elegida`): se ven el botón y la fila elegida, sin cortarse. Al volver al panel, elegir otro NN vuelve a bajar.
  - **Triaje:**
    - el mismo arreglo del tipo de documento;
    - Enter o doble clic en un paciente de la cola llevan el foco al primer signo vital (brief §4).
  - **Administración:** en la propia cuenta no se ofrecen «Desactivar» ni «Cambiar rol», y el título explica por qué. La regla sigue en el controlador.
- **Íconos** (aprobados por el usuario): Tabler Icons 2.47 en PNG, licencia MIT (`views/assets/icons/`, con `LICENSE-tabler-icons.txt`).
  - `views/componentes/iconos.py` pinta cada PNG con un par de colores del tema, uno para claro y otro para oscuro.
  - **Menú:** un ícono por módulo, gris y azul en el ítem activo.
  - **Logo:** una línea de pulso blanca sobre el cuadro azul.
  - **Indicadores:** el ícono va dentro del marcador, del color del dato.
  - **El azul de íconos y marcadores** es `COLOR_PRIMARIO_GRAFICO` (`#3D8BF2` en oscuro): el primario daba 2,7–2,8:1 sobre las tarjetas y el ítem activo, y ahora llega a 3,9–4,2:1. `test_tema.py` lo comprueba sobre la tarjeta, el ítem activo, el fondo y la barra.
  - **El borde de foco** (`views/componentes/foco.py`) usa el mismo azul: en oscuro daba 2,84:1 sobre las tarjetas (campos, listas y botones secundarios). Lo encontró el verificador; venía de antes de esta etapa.
  - `requirements.txt` fija Pillow, que la interfaz ahora usa directamente.
- **Pruebas:** nuevas en `test_componentes.py` (tabla, `Desplazable`, íconos), `test_tema.py`, `test_formato.py`, `test_pacientes_view.py`, `test_triage_view.py`, `test_admin_view.py`, `test_camas_view.py`, `test_limpieza_view.py`, `test_reportes_view.py` y `test_app_principal.py`.

### Archivos afectados
- `views/componentes/desplazable.py`, `views/componentes/iconos.py` y `views/assets/icons/` (nuevos)
- `views/componentes/` (`tabla.py`, `tarjetas.py`, `marca.py`, `documento.py`, `foco.py`, `__init__.py`), `views/tema.py` y `views/formato.py`
- Las 7 pantallas de `views/` y `views/app_principal.py`
- `models/estados.py`, `utils/pdf_generator.py` y `requirements.txt`
- Pruebas: las 10 nombradas arriba
- `docs/`

### Motivo
Cerrar la Fase 6: los detalles que dejaron anotados las revisiones de cada pantalla, hechos de una vez y de la misma forma en todas. También los íconos que el Figma tenía como marcadores.

### Impacto
- Pruebas: **2115 pasan** (antes 2059).
- Sin cambios de esquema ni de controladores.
- **Una dependencia fijada:** Pillow, que ya venía instalada con reportlab y matplotlib.
- **Cambios visibles:**
  - las barras de desplazamiento solo aparecen cuando hacen falta;
  - el borde de las tablas en oscuro;
  - los íconos, los marcadores y el borde de foco, con el azul algo más claro en modo oscuro.

### Decisiones
- **Un azul propio para íconos y marcadores, no aclarar el primario:** sobre el primario va el texto blanco de los botones, que necesita 4,5:1 y lo perdería con un tono más claro. Separados, cada uno cumple su mínimo (4,5:1 el texto, 3:1 el gráfico). En claro los dos son el mismo azul.
- **«Lo justo» conserva la fila elegida, no la lista entera:** a 1093×614 la lista de NN (5 filas y el encabezado, 192 px) más el formulario hasta «Identificar» miden 540 px, y se ven 518. Conservando la lista, el botón quedaba cortado; lo encontró el verificador midiendo en una ventana real. Desde la fila elegida hasta el pie del botón hay 516 px: caben, pero sin el aire de 8 px en los dos extremos, así que cede primero el aire de arriba. Medido en ventana real (claro y oscuro): fila y botón completos.
- **El cálculo es una función aparte** (`desplazamiento_justo`), sin ventana: las pruebas cubren sus límites con números. La ventana de pruebas está oculta y `Treeview.bbox` no da la fila; por eso `y_elegida` vuelve al borde de la tabla cuando Tk no la dibujó.
- **El indicador lateral del ítem activo** usa el mismo azul que su ícono (antes `COLOR_PRIMARIO`, 3,27:1, ya cumplía).
- **«No se pudieron leer los datos», no «no hay»:** una lista vacía por un fallo diría algo falso (que nadie espera cama). Por lo mismo, el contador va sin cifra.
- **El texto de los estados vive en el modelo** porque lo usan las vistas y el PDF, y `utils/` no puede importar `views/`. Una regla, un dueño.
- **Íconos en PNG:** CustomTkinter no dibuja SVG y no hay en el proyecto cómo convertirlo. Tabler publica sus PNG con licencia MIT, y un ícono siempre va junto a su texto.
- **Proceso de la interfaz** (skill ui-consistency):
  - la calibración plantó un rol tipográfico cambiado («fuerte» en lugar de «pequena» en un aviso), y el revisor lo encontró;
  - un verificador y un auditor revisaron en paralelo. Lo que encontraron está corregido:
    - Pacientes saltaba con cada flecha;
    - quedaba un margen de 4 px reservado para una barra oculta;
    - la línea de la leyenda había cambiado 1 px sin querer;
    - los contadores decían «(0)» al fallar;
    - un doble clic en el encabezado activaba la fila;
    - una prueba de Camas no probaba lo que decía;
    - la barra de las tablas se estimaba con un alto de encabezado equivocado;
    - el contenido podía quedar en blanco al acortarse.
  - En el camino apareció un error que no llegó a producirse: `CTkScrollableFrame` no redirige `grid_configure()` a su marco exterior. El Triaje usa `grid()`.

### Pendientes
- **La casilla marcada** (`campos.py`) se rellena de `#0A6CDE`, a 2,84:1 sobre la tarjeta en oscuro. Se reconoce por su marca blanca (4,98:1), así que se dejó igual.
- **Las pruebas de Enter y doble clic llaman al manejador, no producen el evento:** la ventana de pruebas está oculta y no recibe el foco.
- **Fase 7:** integración y pruebas desde las vistas.

---

## [2026-11-04] — Fase 6: pantalla de Administración (cierre de las pantallas)

### Cambio
- **`views/admin_view.py`** (`AdminView`, módulo «Administración», permiso ADMINISTRACION: solo el administrador). Es una tarjeta con «Cuentas (N) / Nueva cuenta (N) / Bitácora / Pacientes»:
  - **Cuentas:** tabla con empleado, cargo, rol y estado (Activa / Bloqueada / Desactivada). Para la cuenta elegida:
    - «Desactivar» o «Activar»;
    - «Desbloquear», que también borra intentos fallidos que aún no bloquean;
    - el rol con «Cambiar rol», que solo responde si el rol elegido es otro;
    - la clave y su repetición, con «Restablecer clave».
  - **Nueva cuenta:** los empleados activos sin cuenta, el rol (empieza sin elegir), la clave y su repetición, y «Crear cuenta para X».
  - **Bitácora:**
    - el período (al abrir, hoy) y los filtros por tabla y por usuario;
    - una tabla con fecha y hora, usuario, acción en castellano (Creación, Cambio, Baja…), tabla, registro y detalle;
    - el detalle completo del registro elegido, bajo la tabla;
    - si se llega al tope de 200 registros, una línea lo avisa.
  - **Pacientes:** documento + «Buscar»; muestra nombre, documento y estado, con «Dar de baja» o «Reactivar» (RN-11).
- **`controllers/periodo.py`:** `rango_de_dias`, la validación del período de días completos (tipos, orden y rango de años de MySQL).
  - Antes estaba duplicada en `ReporteController.indicadores` y `AdminController.bitacora`, y la bitácora tenía el mismo `OverflowError` con «31/12/9999» que se corrigió en Reportes.
  - Una regla, un dueño: los dos controladores la usan.
- **Controladores:**
  - `PacienteController.buscar_para_administrar` (permiso ADMINISTRACION): el administrador no tiene PACIENTES, pero necesita encontrar el registro que corrige (decisión del usuario);
  - `AdminController.listar_tablas_auditables`: la lista vive en `AuditoriaDAO`, y una vista no importa `dao`.
- **Piezas compartidas:**
  - **`CamposPeriodo`** (`views/componentes/periodo.py`, extracción aprobada): los atajos y las fechas de Reportes, ahora también en la Bitácora. Reportes pasó a usarla sin cambiar lo que ve el usuario;
  - `CamposDocumento.al_cambiar_tipo`;
  - `formato.abreviar` («L. Ramos»), que reemplaza tres copias.
- **Ventana principal:** `MODULOS` suma «Administración» al final. Ahora cada permiso tiene su módulo (hay una prueba que lo exige).
- **`prototipo/`:**
  - `AdminDemo`: cuentas y bitácora con las reglas reales (`CuentaUsuario`, `validar_clave_nueva`, `rango_de_dias`);
  - `PacientesDemo` da de baja y reactiva. Antes perdía el estado «activo» al rearmar un paciente; eso se corrigió;
  - `PacientesDemo` también consulta las camas, para no dar de baja a quien tiene un episodio abierto.
  - La bitácora de la demo anota lo que se hace en ella.
- **Pruebas:**
  - nuevas: `test_admin_view.py` (47) y `test_periodo.py` (9);
  - ampliadas: `test_componentes.py` (`CamposPeriodo`, `al_cambiar_tipo`), `test_reportes_view.py`, `test_admin_controller.py`, `test_paciente_controller.py`, `test_formato.py` y `test_app_principal.py`.

### Archivos afectados
- `views/admin_view.py`, `views/componentes/periodo.py` y `controllers/periodo.py` (nuevos)
- `views/reportes_view.py`, `views/app_principal.py`, `views/formato.py`, `views/componentes/documento.py` y `views/componentes/__init__.py`
- `controllers/admin_controller.py`, `controllers/reporte_controller.py` y `controllers/paciente_controller.py`
- `prototipo/demo.py` y `prototipo/ver.py`
- Pruebas: `tests/test_admin_view.py` y `tests/test_periodo.py` (nuevos), y los ampliados de arriba
- `docs/`

### Motivo
Era la última pantalla de la Fase 6. Las cuentas, la bitácora y la baja de pacientes solo se podían usar desde código. Con esta pantalla, cada permiso de `models/permisos.py` tiene su lugar en la interfaz.

### Impacto
- Pruebas: **2059 pasan** (antes 1976).
- Sin cambios de esquema.
- **Regla nueva en la bitácora:** se rechazan los años fuera de 1000–9998, como en los indicadores.
- **Cambio de texto:** el mensaje de un período con hora dice «días (date)» en lugar de «fechas (date)».
- El administrador ve «Tablero de camas», «Reportes» y «Administración».

### Decisiones
- **Forma de la pantalla (acordada con el usuario):**
  - una tarjeta con selector, como Gestión de camas;
  - la búsqueda propia del administrador;
  - la clave escrita dos veces;
  - el período de la bitácora igual que el de Reportes.
- **Nada pide confirmación:** todo se deshace (activar ↔ desactivar, baja ↔ reactivar). En el proyecto solo se confirma lo irreversible.
- **En «Cuentas» todos los botones son secundarios.** Ninguna acción es la principal. Hay precedente: la ficha de Pacientes, con «Editar datos» y «Abrir episodio».
- **Que las dos claves coincidan es de la pantalla, no una regla de negocio:** es la forma de escribir sin ver. La política de claves sigue en el modelo.
- **Seguridad de las claves:**
  - de una clave rechazada solo se guarda un resumen SHA-256, para saber si cambió;
  - al elegir otra cuenta, los campos de clave se vacían;
  - una prueba comprueba que la clave no aparece en diálogos, avisos ni en el log.
- **Pacientes muestra solo nombre, documento y estado:** el administrador no atiende pacientes (`PRODUCT.md`).
- **La columna y el filtro «Usuario» usan el nombre completo.** Dos homónimos se distinguen por el número de su cuenta.
- **Proceso de la interfaz** (skill ui-consistency):
  - la calibración plantó un `messagebox` propio en lugar de `mostrar_error` en una copia de Gestión de camas, y el revisor lo encontró;
  - un verificador y un auditor revisaron en paralelo. Encontraron, y quedó corregido:
    - el resultado que se borraba al soltar Enter;
    - el borde rojo que seguía tras una búsqueda correcta;
    - el doble diálogo cuando la BD falla al dar de baja;
    - la nueva búsqueda tras la baja, que usaba lo escrito y no lo buscado;
    - el cambio de tipo de documento, que no retiraba el resultado;
    - la clave en texto plano en un atributo, y una clave que pasaba a otra cuenta;
    - la bitácora que fallaba sin avisar al abrir;
    - los homónimos en el filtro;
    - las tablas que decían «no hay cuentas» cuando la BD no respondía;
    - en la segunda revisión: cada recarga borraba la clave que se estaba escribiendo para la misma cuenta.

### Pendientes
- **Un paciente sin identificar (NN) no tiene documento**, así que no se puede dar de baja desde aquí. Si hace falta, se podría agregar la lista de NN, como en Pacientes.
- **El filtro «Tabla» ofrece las 21 tablas auditables,** también catálogos que hoy nunca se auditan.
- **«Desactivar» y «Cambiar rol» aparecen habilitados en la propia cuenta.** El controlador los rechaza con un mensaje claro.
- **Si la recarga tras una operación correcta falla,** la tabla queda con el estado anterior hasta la siguiente lectura.
- **`PacientesView` tiene el mismo hueco que se corrigió aquí:** cambiar solo el tipo de documento no retira la ficha. Ya puede usar `CamposDocumento.al_cambiar_tipo`.
- Con la Fase 6 completa, siguen los detalles visuales comunes y la Fase 7.

---

## [2026-11-04] — Fase 6: pantalla de Reportes

### Cambio
- **`views/reportes_view.py`** (`ReportesView`, módulo «Reportes», permiso REPORTES: jefe de guardia y administrador):
  - **Período:**
    - «Desde» y «Hasta» (dd/mm/aaaa);
    - los atajos «Hoy / Últimos 7 días / Este mes» en la cabecera;
    - «Ver indicadores» (principal, también con Enter) y «Exportar PDF…».
    - Al abrir se muestra el mes en curso.
  - **Indicadores:** una línea que dice qué período muestran y que los tiempos son promedios desde el ingreso. Debajo, 4 tarjetas: ingresos, espera de triaje, espera de cama y estancia.
  - **Dos tarjetas lado a lado:**
    - «Triajes por nivel»: tabla con el nivel, los triajes y el porcentaje, y la reclasificación;
    - «Ahora en la guardia»: las camas por estado, la ocupación y los pacientes en emergencia por estado.
  - **Al pie:** el aviso «Prototipo académico: los indicadores no tienen validez clínica» (`PRODUCT.md`).
  - **Exportar:** primero muestra el período escrito, así la pantalla dice lo mismo que el PDF. Después pide la ruta («Guardar como», con un nombre propuesto) y llama a `ReporteController.exportar_pdf`.
- **Piezas compartidas:**
  - `pedir_ruta_pdf` en `views/componentes/errores.py`: el diálogo «Guardar como», junto a los demás diálogos (aprobado por el usuario);
  - `Selector.quitar_eleccion()` y el parámetro `repetir`: sin opción marcada, y volver a pedir la opción ya marcada;
  - `formato.texto_porcentaje`: un porcentaje ya calculado, entero como los del tablero.
- **`ReporteController.indicadores`** rechaza con `ValueError` los años fuera de 1000–9998, el rango de DATETIME de MySQL. Con «31/12/9999», sumar el día siguiente lanzaba `OverflowError`, que ninguna vista espera.
- **Ventana principal:** `MODULOS` suma «Reportes», al final, con `crear_reportes` en `PANTALLAS`. Como el tablero, avisa al encabezado («Actualizado HH:MM» o «Sin conexión»).
- **`prototipo/`:**
  - `ReportesDemo` hace indicadores que crecen con los días del período;
  - el estado de la guardia sale de las camas y las colas de las otras demos;
  - el PDF se exporta con el generador real;
  - el tablero y Reportes comparten la misma demo.
- **Pruebas:**
  - nueva: `test_reportes_view.py` (34);
  - ampliadas: `test_componentes.py` (diálogo y selector), `test_formato.py`, `test_reporte_controller.py` (años límite) y `test_app_principal.py` (el menú del jefe de guardia y del administrador).

### Archivos afectados
- `views/reportes_view.py` (nuevo)
- `views/app_principal.py`, `views/formato.py`, `views/componentes/errores.py`, `views/componentes/selector.py` y `views/componentes/__init__.py`
- `controllers/reporte_controller.py`
- `prototipo/demo.py` y `prototipo/ver.py`
- Pruebas: `tests/test_reportes_view.py` (nuevo), `tests/test_componentes.py`, `tests/test_formato.py`, `tests/test_reporte_controller.py` y `tests/test_app_principal.py`
- `docs/`

### Motivo
Los indicadores y el PDF existían desde la Fase 5, pero solo se podían usar desde código o desde `verificar_controladores.py`. El jefe de guardia y el administrador no tenían cómo verlos ni exportarlos. Es una de las dos pantallas que faltaban para cerrar la Fase 6; la otra es la de administración.

### Impacto
- Pruebas: **1976 pasan** (antes 1928).
- Sin cambios de esquema.
- Una regla nueva en el controlador: el rango de años del período.
- El administrador ve ahora «Tablero de camas» y «Reportes». Antes solo veía el tablero.

### Decisiones
- **Forma de la pantalla (acordada con el usuario, porque el brief no la describía):**
  - el período, los 4 indicadores y las dos tarjetas: lo mismo que trae el PDF;
  - atajos y fechas escritas;
  - el diálogo «Guardar como» en `componentes/errores.py`, para que ninguna vista llame a tkinter directamente.
- **El atajo marcado sigue a las fechas escritas.** Si no corresponde a ninguno, no se marca ninguno. Pulsar el marcado vuelve a pedir su período, por ejemplo «Hoy» en una pantalla abierta desde ayer. El día 1, «Hoy» y «Este mes» son el mismo período, y se conserva el que eligió el usuario.
- **Tras un fallo se conserva lo último mostrado,** como en el tablero. La línea sobre los indicadores dice de qué período es, así no se confunde con lo que dicen los campos.
- **Las notas de los tiempos van vacías.** A 1093×614, «5 h 12 min» no deja lugar para una nota en la tarjeta; que son promedios lo dice la línea de arriba.
- **Porcentajes enteros en pantalla**, como el tablero; el PDF conserva el decimal del controlador. Una misma pantalla no mezcla los dos formatos.
- **Las fechas marcadas en rojo pierden la marca cuando lo escrito cambia,** no con cualquier tecla, igual que el motivo en Camas. Así soltar el Enter que envió la fecha no la desmarca. Un período que rechaza el controlador (la inicial después de la final) marca las dos fechas, porque no se sabe cuál está mal.
- **«Sin conexión» solo ante un error de la BD.** Un PDF abierto en otro programa (`ReporteError`) muestra su mensaje, pero no cambia el encabezado.
- **«Espera de cama» se mide desde el ingreso**, como la calcula el controlador; `PROJECT_CONTEXT.md` §12 habla de «triaje a cama». La pantalla muestra lo que entrega el controlador.
- **Proceso de la interfaz** (skill ui-consistency):
  - la lista de comprobación salió de Limpieza (estructura) y del tablero (indicadores);
  - la revisión se calibró con un `16` escrito a mano en lugar de `tema.ESPACIO_2`, plantado en una copia de Limpieza en un worktree temporal, y el revisor lo encontró;
  - después revisaron la pantalla, en paralelo, un verificador de la interfaz y un auditor de código, ninguno de los dos autor de la pantalla. Lo que encontraron está corregido: la línea de pacientes cortada, el atajo marcado que no respondía, los dos formatos de porcentaje, el singular de «Ingresos», el marcador de los indicadores, el período mostrado tras un fallo y el `OverflowError`.

### Pendientes
- **Indicadores que el controlador no calcula** (`PROJECT_CONTEXT.md` §12):
  - rotación de cama;
  - cumplimiento del tiempo objetivo por nivel.
- **El texto del estado de cama** (`estado.value.capitalize()`) ya está escrito en tablero, `TarjetaCama`, Gestión de camas, Reportes y el PDF: conviene llevarlo a `formato.py`. `texto_tiempo` repite el cálculo del cuarto indicador del tablero.
- **Al exportar, «Ahora en la guardia» se vuelve a leer.** Si pasa tiempo en el diálogo «Guardar como», el PDF puede diferir de lo que se ve.
- **Mostrar «Sin conexión» con cualquier `SigtacError`:** el tablero lo hace así y Reportes, al consultar, también. Sería más preciso filtrar por `PersistenciaError`.
- **Común a toda la familia:**
  - el borde claro de `TablaDatos` en modo oscuro;
  - la barra de desplazamiento visible aunque las filas quepan.
- **Administración** sigue sin pantalla.

---

## [2026-10-31] — Gestión de camas y Limpieza

### Cambio
- **`views/camas_view.py`** (`GestionCamasView`, módulo «Gestión de camas», permiso GESTION_CAMAS). Es una tarjeta con «Esperan cama (N) / Con cama (N) / Mantenimiento» en la cabecera:
  - **Esperan cama:**
    - la cola por prioridad (nivel, paciente, motivo y espera);
    - al elegir un paciente, sus camas libres compatibles;
    - «Asignar cama X» la reserva (RN-01, RN-05).
  - **Con cama:** cama, estado, nivel, paciente y hora de asignación.
    - Una cama reservada ofrece «Llegó a la cama» y «Cancelar reserva».
    - Una ocupada ofrece «Dar de alta», y la cama pasa a limpieza (RN-07).
    - «Referir» y «Registrar fuga» sirven para las dos.
    - El alta, referir y la fuga piden confirmación.
  - **Mantenimiento:** las camas libres o fuera de servicio.
    - Una libre sale de servicio con su motivo. Si falta el motivo, se explica bajo el campo.
    - Una fuera de servicio vuelve a servicio.
- **`views/limpieza_view.py`** (`LimpiezaView`, módulo «Limpieza», permiso LIMPIEZA):
  - las camas por limpiar, de la más antigua a la más reciente;
  - «Confirmar limpieza de X» deja la cama libre (RN-08).
- **Lógica que faltaba:**
  - `CamaController.pacientes_con_cama()` devuelve `PacienteEnCama`: la cama, el episodio, el paciente y la fecha de asignación. Sigue el orden del mapa y hace las lecturas en una transacción, como `armar_cola`;
  - `AsignacionDAO.listar_vigentes()`;
  - `CamaController.validar_motivo` pasa a ser público: la demo usa la misma regla.
- **`TablaDatos`** (extracción aprobada):
  - `filas=N` fija el alto de la tabla. Triaje y Pacientes lo usan en lugar de su marco de alto fijo;
  - `cambiar_texto_vacio`.
- **Ventana principal:** `MODULOS` suma «Gestión de camas» (después de Triaje) y «Limpieza» (al final), con `crear_camas` y `crear_limpieza` en `PANTALLAS`.
- **`prototipo/`:**
  - `CamasDemo` recorre el ciclo completo con las reglas reales de `Cama` y `EpisodioEmergencia`, y recuerda lo que se hace;
  - un paciente triado en `TriajeDemo` pasa a esperar cama (`al_triar`);
  - todas las pantallas de la demo comparten los mismos datos.
- **`scripts/verificar_controladores.py`:** 2 comprobaciones de `pacientes_con_cama` contra MySQL.
- **Pruebas:**
  - nuevas: `test_camas_view.py` (31) y `test_limpieza_view.py` (6);
  - ampliadas: `test_cama_controller.py`, `test_asignacion_dao.py`, `test_componentes.py`, `test_app_principal.py`, `test_triage_view.py` y `test_dashboard_view.py`.

### Archivos afectados
- `views/camas_view.py` y `views/limpieza_view.py` (nuevos)
- `views/app_principal.py`, `views/componentes/tabla.py`, `views/triage_view.py` y `views/pacientes_view.py`
- `controllers/cama_controller.py` y `dao/asignacion_dao.py`
- `prototipo/demo.py` y `prototipo/ver.py`
- `scripts/verificar_controladores.py`
- Pruebas: `tests/test_camas_view.py` y `tests/test_limpieza_view.py` (nuevos), `tests/test_cama_controller.py`, `tests/test_asignacion_dao.py`, `tests/test_componentes.py`, `tests/test_app_principal.py`, `tests/test_triage_view.py` y `tests/test_dashboard_view.py`
- `docs/`

### Motivo
El sistema es de triaje **y asignación de camas**, pero la interfaz solo llegaba hasta el triaje. Las reglas centrales no se podían demostrar desde la aplicación:
- RN-01 y RN-05: asignar;
- RN-07 y RN-08: alta → limpieza → disponible.

Además, la Fase 7 pide repetir desde las vistas la integración «cola → camas compatibles → asignación → liberación → limpieza». Los controladores ya existían. Limpieza va en esta misma tarea porque solo el rol de limpieza confirma una limpieza: sin su pantalla, una cama dada de alta nunca volvía a estar libre.

### Impacto
- Pruebas: **1928 pasan** (antes 1878).
- Sin cambios de esquema ni de reglas de negocio.
- El médico y el jefe de guardia ven «Gestión de camas»; el personal de limpieza ve «Limpieza».
- **La demo tenía la cola de cama fuera de orden:** dos pacientes de nivel 3 salían en el orden de la lista, no por llegada. Ahora `CamasDemo` usa `ordenar_por_prioridad`, como el controlador real, y se corrigió la prueba del tablero que dependía de ese orden.

### Decisiones
- **Forma de la pantalla (acordada con el usuario):**
  - un selector como en Pacientes, que solo reutiliza piezas que ya existen;
  - se descartaron las dos columnas, como en Triaje, y la matriz clicable. La matriz habría cambiado un componente que el brief dejó solo de lectura.
- **Qué pide confirmación:**
  - el alta, referir y la fuga cierran el episodio y no se deshacen;
  - cancelar una reserva sí se deshace (el paciente vuelve a la cola), así que no pregunta;
  - confirmar una limpieza tampoco: el botón ya es la confirmación (RN-08).
- **El botón principal de «Con cama» cambia con el estado de la cama:** «Llegó a la cama» para una reservada y «Dar de alta» para una ocupada. «Cancelar reserva» se deshabilita, en lugar de ocultarse, para que la fila de botones no cambie de forma.
- **Los datos se releen** al abrir, al cambiar de opción y después de cada operación, porque otra PC pudo cambiarlos. Tras un error se conserva la elección; tras un éxito, no, para que la acción siguiente no recaiga por inercia sobre la misma fila.
- **El motivo escrito se conserva** si la operación falla. Se borra al guardarlo.
- **Mantenimiento lista solo camas libres o fuera de servicio.** El controlador rechaza las demás (con paciente o con limpieza pendiente), y listarlas solo ofrecería acciones que van a fallar.
- **Los textos de éxito no suponen el género del paciente** («Referencia registrada», no «quedó referido»).
- **«Disponible», no «libre», en lo que lee el usuario:** es el nombre del estado en las columnas y en la leyenda del tablero.
- **Corregido tras la revisión independiente:**
  - soltar el Enter que envió un motivo vacío borraba su aviso. Ahora el aviso solo se va si el texto cambia, como el documento en Pacientes. El motivo de admisión de Pacientes tenía el mismo fallo y se corrigió igual;
  - al volver de otra opción, o tras un error, se perdía la cama compatible elegida. Ahora se conserva si sigue disponible;
  - ttk avisa más tarde la selección que hace el código. Cada recarga leía dos veces las camas compatibles y podía abrir un diálogo. Ahora el paciente que ya se muestra no se relee, y una recarga no abre diálogos;
  - referir o registrar una fuga preguntaba con el estado leído antes: si otra PC había marcado la llegada, decía «queda disponible» cuando la cama iba a limpieza. Ahora relee antes de preguntar, y el aviso final sale de lo que devolvió el controlador.
- **Proceso de la interfaz** (skill ui-consistency):
  - la pantalla no tenía diseño en el brief, así que la forma se acordó con el usuario antes del código;
  - la lista de comprobación salió de Pacientes, la pantalla más reciente del mismo tipo;
  - la revisión se calibró con una diferencia plantada en una copia de Pacientes (un diálogo propio en lugar de `mostrar_error`), y el revisor la encontró;
  - después revisó las dos pantallas un agente que no las escribió.

### Pendientes
- Ejecutar `scripts/verificar_controladores.py` para confirmar `pacientes_con_cama` contra MySQL (lo hace el usuario con su cuenta de administrador).
- Lo que dejó abierto la revisión:
  - el motivo escrito para una cama se conserva al elegir otra (la familia conserva lo escrito). El botón dice qué cama sale de servicio;
  - `estado.value.capitalize()` está escrito en tres lugares (tablero, `TarjetaCama` y esta pantalla).
- Fuera de esta tarea:
  - en modo oscuro, el borde de las tablas (`TablaDatos`) se ve muy claro;
  - la barra de `CTkScrollableFrame` se ve aunque el contenido quepa.
- Traslado de cama (sigue abierto): una cama con paciente no se puede poner fuera de servicio.
- Reportes con PDF y administración siguen sin pantalla.

---

## [2026-10-30] — Fase 6: pantalla de pacientes

### Cambio
- **`views/pacientes_view.py`** (`PacientesView`, brief §5), con «Buscar / Sin identificar (N)» en la cabecera de la tarjeta:
  - **Buscar:**
    - el documento → la ficha ampliada (documento, fecha de nacimiento, edad, sexo, seguro y si está dado de baja);
    - «Editar datos» corrige nombres, apellidos, fecha, sexo y seguro. El documento no se edita;
    - «Abrir episodio» pide el motivo, y el paciente pasa a esperar triaje;
    - sin resultado: «No hay un paciente con ese documento» y «Registrarlo en Triaje», que abre Triaje con el documento ya buscado;
    - un paciente dado de baja no se edita ni se admite (lo reactiva un administrador).
  - **Sin identificar:**
    - la lista de NN;
    - al elegir uno: documento, nombres, apellidos y fecha → «Identificar»;
    - si el documento ya es de otro paciente, pregunta (`confirmar`) si fusionar ambos registros. Los episodios del NN pasan al paciente registrado.
- **Piezas compartidas** (aprobadas por el usuario), en `views/componentes/paciente.py`:
  - `CamposPaciente`: rellenar desde un paciente, leer los valores marcando el campo culpable y limpiar;
  - `FichaPaciente`: corta o ampliada.
  El triaje pasa a usar las dos.
- **`views/componentes/campos.py`:**
  - la rejilla de campos que el triaje tenía como métodos privados (`celda`, `campo_en_rejilla`, `lista_en_rejilla`);
  - la lectura con el campo marcado (`leer_campo`, `leer_opcion`);
  - `limpiar_al_corregir` y `sin_error`.
- `Tarjeta.cambiar_textos`, `AppPrincipal.pantalla_actual`, `TriageView.buscar_documento` y `formato.fecha_numerica`.
- **`prototipo/`:**
  - `PacientesDemo` con dos NN, edición, identificación y fusión, todo con las reglas reales del modelo;
  - Triaje y Pacientes comparten los datos de la demo.
- **Pruebas:**
  - nueva: `test_pacientes_view.py` (30);
  - ampliadas: `test_componentes.py` (piezas de paciente y rejilla), `test_triage_view.py` y `test_app_principal.py`.

### Archivos afectados
- `views/pacientes_view.py` y `views/componentes/paciente.py` (nuevos)
- `views/componentes/` (`campos.py`, `tarjetas.py` y `__init__.py`), `views/triage_view.py`, `views/app_principal.py` y `views/formato.py`
- `prototipo/demo.py` y `prototipo/ver.py`
- Pruebas: `tests/test_pacientes_view.py` (nuevo), `tests/test_componentes.py`, `tests/test_triage_view.py` y `tests/test_app_principal.py`
- `docs/`

### Motivo
Es la última pantalla de la Fase 6. Resuelve a los pacientes que llegan sin identificar y permite corregir datos o admitir a alguien sin triarlo en el momento (por ejemplo, desde admisión).

### Impacto
- Pruebas: **1878 pasan** (antes 1836).
- Sin cambios de esquema, de controladores ni de modelos.
- El triaje se comporta igual con las piezas extraídas: sus 55 pruebas pasan.
- **La demo tenía un dato incoherente:** Carmen Rojas figuraba con el seguro 1 (EsSalud) y se mostraba como «SIS». Lo encontró la prueba de editar. Ahora el id y el nombre salen del mismo catálogo.

### Decisiones
- **La fusión se ofrece, no se impone.** `identificar()` rechaza un documento que ya existe, porque duplicaría a la persona. Por eso la pantalla busca primero el documento: si existe, pregunta antes de fusionar, porque la fusión no se puede deshacer. Si el usuario no confirma, el formulario conserva lo escrito.
- **«Registrarlo en Triaje» lleva el documento.** Triaje se abre con él ya buscado y muestra el registro, así no se escribe dos veces. Solo se ofrece si el rol tiene Triaje en el menú.
- **Mientras se edita o se admite, se ocultan «Editar datos» y «Abrir episodio».** A la vista queda un solo formulario, con su botón principal y «Cancelar».
- **Dar de baja y reactivar no están aquí.** Exigen el permiso de administración (`PacienteController`) y el brief los deja para la pantalla de administración.
- **La lista de NN muestra el número de registro.** Dos NN del mismo sexo y la misma edad aparente solo se distinguen por él, que es el que se anota en la pulsera o en la historia provisional.
- **El título de la tarjeta cambia con el selector** («Buscar paciente» / «Pacientes sin identificar»), porque son dos tareas distintas. En el triaje es fijo porque las dos opciones llevan al mismo paso.
- **Corregido tras la revisión:**
  - un dato mal escrito al identificar ya no recarga la lista, que borraba la elección;
  - al cancelar o terminar, el foco vuelve al documento;
  - cambiar el documento buscado retira la ficha, y «Registrarlo en Triaje» lleva el documento que se buscó;
  - el motivo vacío se explica bajo el campo;
  - el margen bajo el documento es el mismo que en el triaje;
  - la pregunta de fusión avisa que los datos escritos no se usan;
  - al abrir un formulario, la pantalla se desplaza para mostrarlo entero.
- **Proceso de la interfaz** (skill ui-consistency):
  - lista de comprobación a partir del triaje, la pantalla más reciente del mismo tipo;
  - revisión calibrada con una fuente escrita a mano, plantada en una copia del triaje, que el revisor encontró;
  - después, la revisión de la pantalla por un agente que no la escribió.

### Pendientes
- **Abierto tras la segunda revisión:**
  - Después de identificar, el foco no vuelve al documento: se queda en el botón, ya deshabilitado.
  - En «Sin identificar», a 1093×614, «Identificar» queda fuera de la vista hasta desplazar (a «Editar datos» y «Abrir episodio» ya se las desplaza solas).
  - `_mostrar_al_pie` usa `_parent_canvas`, un atributo interno de `CTkScrollableFrame`: conviene llevarlo a un componente.
- **Para el equipo:** el número de registro de un NN solo se ve en esta lista. Ni el aviso al registrarlo en Triaje ni la cola lo muestran, así que quien anota la pulsera no tiene de dónde sacarlo.
- Común con el triaje: cambiar solo el tipo de documento, sin tocar el número, no retira la ficha.
- Detalles visuales de las pantallas, para el final (los que anotan las entradas del triaje y del tablero).

---

## [2026-10-30] — Cuentas de prueba en el seed: anotadas y una de médico

### Cambio
- **`db_scripts/seed.sql`:**
  - un comentario sobre `INSERT INTO usuario` con la clave de desarrollo y, por cada cuenta, su documento, su rol y si puede ingresar;
  - la empleada 7, Valeria Quispe Torres (DNI 77777777, médica), con la cuenta 6, rol «Médico de Emergencia», activa y con la misma clave de desarrollo (hash bcrypt nuevo, costo 12).
- **`README.md`:** remite a ese comentario. Antes remitía a este CHANGELOG.

### Archivos afectados
- `db_scripts/seed.sql` y `README.md`

### Motivo
Para probar el login hay que saber con qué documento y qué clave entra cada rol. Hasta ahora la clave solo estaba en una entrada antigua de este CHANGELOG, y el documento de cada cuenta había que deducirlo cruzando `usuario` con `empleado`. Además no había ninguna cuenta activa de médico: la única con ese rol está desactivada a propósito, para probar el rechazo.

### Impacto
- El seed crea un empleado y una cuenta más. Para tenerlos en `sigtac_db` hay que volver a cargar el seed, lo que borra los datos existentes; lo decide el usuario.
- La clave anotada es la del CHANGELOG del inicio del proyecto. Se comprobó con bcrypt contra los 6 hashes, y coincide en todos.
- `scripts/verificar_controladores.py` no cambia: sigue esperando que el único empleado sin cuenta sea el 5. Falta ejecutarlo contra MySQL para confirmar que el seed carga (lo ejecuta el usuario).

### Decisiones
- **La cuenta de médico es de una empleada nueva, no de Leonardo Veliz (empleado 5).** El script de verificación crea la cuenta del empleado 5 para probar `crear_cuenta`, y el esquema admite una sola cuenta por empleado (`UN_usuario_empleado`). Si el seed se la diera, esa prueba fallaría por registro duplicado.
- **La clave va en el seed, junto a los hashes que la usan.** Es una clave de prueba, ya registrada en el repositorio, y el seed ya dice que es solo para desarrollo. Cualquier clave real sigue en el `.env`, que no se versiona.

### Pendientes
- Ejecutar `scripts/verificar_controladores.py` para confirmar que el seed carga en MySQL.

---

## [2026-10-30] — Fase 6: pantalla de triaje

### Cambio
- **`views/triage_view.py`** (`TriageView`): el flujo unificado del brief §4.
  - **1. Paciente:**
    - «Nuevo / En cola (N)»;
    - con documento: buscar → ficha, o los campos para registrarlo (nombres, apellidos, fecha dd/mm/aaaa, sexo y seguro);
    - sin identificar (NN): sexo, edad aparente y seguro;
    - el motivo de consulta;
    - en cola: la tabla de los que esperan triaje (llegada, nombre corto, motivo y espera).
  - **2. Signos vitales:** 6 campos con su unidad y, como ayuda, el rango que admite el modelo (`SignosVitales.RANGOS`). Un signo inválido se marca en rojo y se explica bajo los campos.
  - **3. Síntomas:** casillas en dos columnas.
  - **Panel de clasificación:**
    - fijo a la derecha, con el nivel, su plazo, los criterios y el protocolo;
    - sin datos: «Complete los signos vitales para ver la sugerencia»;
    - se recalcula solo, 300 ms después de la última tecla;
    - «Reclasificar» despliega el nivel final y la justificación (RN-10);
    - el único botón azul dice qué registra («Confirmar nivel 2») y, deshabilitado, por qué no responde: «Complete los signos vitales» o «Faltan 3 caracteres (mínimo 10)».
  - **Confirmar:** registrar o buscar al paciente → abrir el episodio → registrar el triaje. Si algo falla, la pantalla recuerda lo que ya hizo y el reintento no lo repite.
- **Piezas compartidas** (aprobadas por el usuario):
  - `Tarjeta`, extraída del tablero;
  - `lista_opciones`/`mover_opcion`, extraídas de `CamposDocumento` (ahora avisan como el mouse y pueden empezar vacías);
  - `casilla`;
  - `Selector`: lo elegido se marca como el ítem activo del menú lateral.
- `marcar_error(campo, False)` vuelve al borde de foco si el campo lo tiene. Antes, al corregir un signo mientras se escribía, el foco desaparecía.
- **`views/formato.py`:** `leer_numero` (acepta coma o punto) y `leer_fecha`.
- **`views/app_principal.py`:** `crear_triaje` en `PANTALLAS`.
- **`prototipo/`:**
  - `PacientesDemo`;
  - `TriajeDemo` con `listar_sintomas`, `sugerir` y `registrar`, usando la estrategia real y el catálogo del seed;
  - `python -m prototipo.ver --pantalla triaje`.
- **Pruebas:**
  - nueva: `test_triage_view.py` (55);
  - ampliadas: `test_componentes.py` (piezas nuevas), `test_formato.py` (lectura) y `test_app_principal.py`.

### Archivos afectados
- `views/triage_view.py` y `views/componentes/selector.py` (nuevos)
- `views/componentes/` (`campos.py`, `tarjetas.py`, `documento.py`, `foco.py` y `__init__.py`), `views/dashboard_view.py`, `views/app_principal.py` y `views/formato.py`
- `prototipo/demo.py` y `prototipo/ver.py`
- Pruebas: `tests/test_triage_view.py` (nuevo), `tests/test_componentes.py`, `tests/test_formato.py` y `tests/test_app_principal.py`
- `CLAUDE.md` y `docs/`

### Motivo
Es la pantalla más usada (PRODUCT.md): pasar de «llegó una persona» a «tiene nivel y está en la cola de cama» con el menor número de pasos. Corrige lo que la crítica marcó en el Figma ([P1]):
- la sugerencia ya no se muestra sin datos;
- la justificación es obligatoria solo al reclasificar;
- hay un único botón principal, anclado al pie del panel.

### Impacto
- Pruebas: **1836 pasan** (antes 1751).
- Sin cambios de esquema, de controladores ni de modelos.
- Capturas revisadas: 1280×800 en claro (vacía, con sugerencia y con registro) y 1093×614 en oscuro (reclasificando, con el botón a la vista).

### Decisiones
- **Las piezas nuevas van en `views/componentes/`.** Pacientes las reutilizará. Lo decidió el usuario al preguntársele por cada una.
- **La sugerencia se calcula en el controlador real, también mientras se escribe.** La vista no repite la regla. Solo lee los rangos del modelo para señalar el campo culpable.
- **Un error al recalcular se lee en el panel, no en un diálogo.** Se recalcula con cada pausa al escribir, y un diálogo tras otro sería inusable. Al abrir la pantalla sí hay un único diálogo, como en el tablero.
- **El sexo y el seguro empiezan sin elegir** (`lista_opciones(vacia=True)`). Un valor por omisión que nadie revisó sería un dato falso del paciente.
- **La ficha del paciente buscado muestra su nombre completo**, porque quien tría tiene que confirmar la identidad. La cola usa el nombre corto y el documento enmascarado, como el tablero.
- **El reintento no repite pasos.** Si el triaje falla después de abrir el episodio (otra PC lo cerró, la BD cayó), la pantalla guarda el paciente y el episodio. Así, el segundo intento no registra dos veces al paciente ni choca con «ya tiene un episodio abierto».
- **El botón deshabilitado dice por qué.** `BotonPrimario` conserva el texto blanco al deshabilitarse y se ve igual que activo: el texto explica qué falta, como el «Verificando…» del login. Reemplaza al contador, que a 1093×614 quedaba fuera del panel.
- **La cola de triaje no muestra el documento.** Con 4 columnas cabe a 1093×614 sin desplazarse en horizontal; para identificar al paciente bastan el nombre corto, la hora de llegada y el motivo.
- **Un borde rojo nunca queda sin explicación.** Un campo del paciente marcado al confirmar o al buscar pierde el rojo en cuanto se corrige (al escribir o al elegir otra opción), y todos se limpian al cambiar «Nuevo/En cola» o «Con documento/Sin identificar». El documento compara el texto: soltar el Enter que buscó no borra el error recién marcado. Lo encontró la segunda revisión y se corrigió a pedido del usuario.
- **`Tarjeta` usa ESPACIO_MEDIO arriba** (antes 12 − 2 = 10 px, fuera de la base de 4): el tablero baja 2 px su cabecera.
- **Proceso de la interfaz** (skill ui-consistency):
  - lista de comprobación a partir del tablero y del login;
  - revisión calibrada con un error plantado en una copia del tablero, que el revisor encontró;
  - después, la revisión de la pantalla por un agente que no la escribió.

### Pendientes
- **Abierto tras la segunda revisión:**
  - Con 3 o más criterios a 1093×614, la justificación podría recortarse: hoy mide 58 de 72 px con 2 criterios.
  - Brief §4 («se elige uno y se salta al paso 2»): que Enter o el doble clic en una fila de la cola lleven el foco al primer signo. Con las flechas no, para no romper el teclado.
- Nombres, apellidos y motivo inválidos solo se avisan con un diálogo, sin marcar el campo: marcarlos obligaría a la vista a repetir la validación del modelo.
- `TarjetaKPI` conserva `ESPACIO_2 - 2` y `ESPACIO_MEDIO - 2` (anterior a este trabajo).
- `pacientes_view.py` (buscar, editar, identificar y fusionar NN), con las mismas piezas.
- Íconos del logo, el menú y los KPIs.

---

## [2026-10-30] — Criterios de la sugerencia de triaje

### Cambio
- **`models/estrategias.py`:**
  - `evaluar(signos, sintomas) -> Clasificacion(nivel, criterios)` es el nuevo método abstracto. Los criterios son las condiciones cumplidas en el nivel elegido, por ejemplo «SatO₂ 89 % < 90 %» o «Peso de los síntomas 8.5 ≥ 7». En el nivel 5 hay uno solo: «Ningún criterio de los niveles 1 a 4».
  - `clasificar()` pasa a la clase base y devuelve `evaluar(...).nivel`.
  - `condicion(etiqueta, valor, símbolo, umbral, unidad)` arma cada condición: si se cumple y su texto.
  - `_decidir(...)` recorre los niveles del más urgente al menos urgente.
  - `ReglaManchester` y `ReglaMINSA` se reescriben con estas piezas, **con los mismos umbrales**.
- **`TriajeController.sugerir()`:** `Sugerencia` lleva `criterios` además del nivel y el protocolo.
- **`scripts/verificar_controladores.py`:** comprueba el criterio de la sugerencia con el catálogo real de síntomas.
- **Pruebas:** `test_estrategias.py`, con los criterios de cada nivel y sus límites, varias condiciones a la vez, Decimal y el contrato de la clase base; `test_triaje_controller.py`, donde el doble `EstrategiaFija` implementa `evaluar`.

### Archivos afectados
- `models/estrategias.py` y `controllers/triaje_controller.py`
- `tests/test_estrategias.py` y `tests/test_triaje_controller.py`
- `scripts/verificar_controladores.py`
- `CLAUDE.md` y `docs/`

### Motivo
Lo decidió el equipo el 2026-10-27 (`docs/diseno/BRIEF.md`). El panel de clasificación de la pantalla de triaje muestra por qué el sistema sugiere un nivel: el profesional decide si lo confirma o lo reclasifica, y para eso necesita ver los motivos. Va antes de la pantalla para que la vista no tenga que deducir los criterios: esa regla pertenece al modelo.

### Impacto
- Pruebas: **1751 pasan** (antes 1707). Las pruebas anteriores de `clasificar()` pasan sin cambios: los niveles son los mismos.
- Sin cambios de esquema. `registrar()` y la auditoría no cambian: los criterios no se guardan, porque se pueden recalcular a partir de los signos y los síntomas.

### Decisiones
- **Template Method dentro del Strategy.** Cada estrategia implementa solo `evaluar()`, y `clasificar()` se deriva de él en la clase base. Si `clasificar()` y unos «criterios» aparte fueran dos métodos, cada umbral se escribiría dos veces y podrían quedar distintos.
- **El umbral se escribe una sola vez.** La misma llamada a `condicion()` decide y arma el texto, así que el texto que ve el profesional no puede contradecir la regla.
- **Solo los criterios del nivel elegido.** Con SatO₂ 88 % y síntomas de peso 8.5, el nivel es 1 y se muestra solo «SatO₂ 88 % < 90 %». El peso 8.5 también cumple el nivel 2, pero no fue lo que decidió.
- **Se tocaron las estrategias existentes**, aunque la regla es crear una nueva para un algoritmo nuevo. Aquí el algoritmo no cambia, cambia el contrato. Las pruebas de límites de antes lo demuestran.
- **Los números van sin ceros de sobra** (`float(...)` con formato `g`): «5», no «5.00», aunque el valor llegue como Decimal.

### Pendientes
- `triage_view.py`: el panel de clasificación muestra `Sugerencia.criterios` bajo el nivel.
- `TriajeDemo.sugerir` para el prototipo.
- Ejecutar `scripts/verificar_controladores.py` (lo hace el usuario con su cuenta de administrador).

---

## [2026-10-30] — Fase 6: tablero de camas en la ventana principal

### Cambio
- **`views/dashboard_view.py`** (`DashboardView`): el tablero aprobado (`docs/diseno/`).
  - **KPIs:** camas libres sobre las camas en servicio, en limpieza y prioridad 1–2 sin cama. El cuarto depende del rol: espera de cama con REPORTES, esperan triaje con TRIAJE y, si no, fuera de servicio.
  - **Matriz de camas.**
  - **Cola «Esperan cama»:** nivel, nombre abreviado y documento enmascarado, motivo, espera (en rojo si excede el plazo) y plazo del nivel.
  - **Actualización:** al abrirse y cada 30 s. Si falla, conserva lo último y avisa a la ventana principal.
- **`views/app_principal.py`:**
  - el tablero queda registrado en `PANTALLAS` (`crear_tablero`), con los controladores reales de la sesión;
  - `informar_actualizacion(correcta, momento)` es el aviso del tablero: «● Actualizado HH:MM» en verde o «● Sin conexión» en rojo (`marcar_sin_conexion`);
  - la fecha y la hora usan `views/formato.py`. Se quitó `formatear_fecha`, que repetía `formato.fecha_corta`.
- **`views/formato.py`:** nombre corto («M. Salazar», «NN · varón, ~40 años»), documento enmascarado («DNI 43•••19»), minutos, plazo, fecha en español y porcentaje.
- **`models/triaje.py`:** `TIEMPO_MAXIMO_POR_NIVEL` (el `tiempo_max_min` del seed) y `excede_plazo(nivel, minutos)`.
- **`prototipo/`:** controladores de demostración con datos inventados (36 camas, 4 pacientes que esperan cama y 2 que esperan triaje). `python -m prototipo.ver` abre la aplicación sin MySQL y guarda capturas. Le pasa a `AppPrincipal` sus propias `PANTALLAS_DEMO`.
- **Pruebas:**
  - nuevas: `test_dashboard_view.py` (14) y `test_formato.py` (28);
  - ampliadas: `test_app_principal.py` (tablero registrado, sus controladores y «Sin conexión»), `test_triaje.py` (plazo y sus límites) y `test_estados_vs_bd.py` (plazos contra el seed).

### Archivos afectados
- `views/dashboard_view.py`, `views/formato.py` y `prototipo/` (nuevos)
- `views/app_principal.py` y `models/triaje.py`
- `tests/` (2 archivos nuevos y 3 ampliados), `docs/diseno/prototipo_*.png` y `docs/diseno/app.png`, `docs/`, `CLAUDE.md`

### Motivo
El tablero se hizo en una máquina (fase D5 del plan de diseño) mientras el login y la ventana principal se hacían en otra. Cada máquina tenía su propio `app_principal.py`. Se conservó el de la otra máquina, el más reciente, y el tablero se conectó a él mediante `PANTALLAS`.

### Impacto
- Pruebas: **1707 pasan** (antes 1646). La suite tarda unos 30 s: cada prueba del tablero arma sus 36 casillas reales.
- Capturas de `docs/diseno/` rehechas en la ventana nueva: 1280×800 (`app.png`), 1280×720 (claro), y 1093×614 en oscuro y con el rol de limpieza.
- Sin cambios de esquema.

### Decisiones
- **La cola de pacientes solo la ven los roles clínicos (permiso PACIENTES).** Limpieza y administración ven la matriz a toda altura, porque no necesitan nombres de pacientes para su trabajo (Ley 29733, datos personales de salud). Además, el nombre va abreviado y el documento enmascarado: la pantalla puede verla cualquiera en la guardia.
- **«Camas libres» se cuenta sobre las camas en servicio** (15 / 34, no 15 / 36), igual que la ocupación de `ReporteController`.
- **Un error de la actualización automática no abre un diálogo cada 30 s.** El diálogo solo aparece al abrir la pantalla. Después, el error se ve en el encabezado como «● Sin conexión».
- **La tarjeta «Conectado» de la barra no vuelve.** El estado de la conexión se muestra solo en el encabezado, que ya existía. Así se respeta la línea que la reemplazó en la barra (entrada del 2026-10-29).
- **Una sola fábrica para el tablero.** `crear_tablero` crea los controladores reales salvo que reciba otros. El prototipo le pasa los de demostración con `functools.partial`, sin una clase intermedia de controladores.
- **Los márgenes exteriores los pone `AppPrincipal`, no cada pantalla.** El tablero sumaba los suyos y quedaba 20 px corrido respecto del título; ahora se alinea con el encabezado. Las pantallas que vienen tampoco agregan margen exterior.
- **El plazo por nivel vive en el modelo**, no en la vista. Una prueba lo compara con `seed.sql`.

### Pendientes
- Triaje (antes, ampliar la estrategia para que devuelva los criterios) y pacientes, que se registran en `PANTALLAS` y en `PANTALLAS_DEMO`.
- Íconos del logo, el menú y los KPIs.
- Acelerar las pruebas del tablero.
- `git stash drop` del respaldo de la integración, cuando el usuario lo confirme.

---

## [2026-10-29] — Fase 6: inicio de sesión y ventana principal

### Cambio
- **`views/login_view.py`** (`LoginView`): una tarjeta centrada con:
  - la marca;
  - el documento (`CamposDocumento`) y la contraseña;
  - el botón «Ingresar»;
  - el aviso «Prototipo académico — no validado clínicamente».

  Funciona así:
  - Enter ingresa desde cualquiera de los dos campos;
  - mientras bcrypt verifica, el botón se deshabilita y dice «Verificando…»;
  - si los datos son incorrectos, se muestra el mensaje genérico, se borra la contraseña y el foco vuelve a ella;
  - si no hay conexión, se muestra un mensaje propio y se conservan los datos.
- **`views/app_principal.py`** (`AppPrincipal`): el marco de la aplicación, como en el tablero aprobado.
  - **Barra lateral:**
    - la marca;
    - el menú, con los módulos que el rol puede usar (`sesion.puede`);
    - al pie: el usuario (iniciales, nombre y rol), el interruptor «Modo oscuro» y «Cerrar sesión».
  - **Encabezado:** el título y la descripción del módulo, «Actualizado HH:MM», la fecha y el reloj.
  - **Módulos:** cada pantalla se registra en `PANTALLAS` con `crear(padre, sesion, principal)`. Un módulo que todavía no tiene pantalla muestra un aviso.
- **Piezas nuevas en `views/componentes/`** (aprobadas por el usuario):
  - `botones.py`: `BotonPrimario` y `BotonSecundario`;
  - `marca.py`: `Marca`;
  - `campos.py`: `campo_texto` y `etiqueta_campo`. `CamposDocumento` ahora los usa y expone `campo_numero`.
- **Teclado** (`views/componentes/foco.py`): `marcar_foco_control`, `activar` y `fijar_borde`. Los botones y el interruptor de CustomTkinter son un lienzo que Tab salta. Con estas funciones:
  - aceptan el foco y lo muestran con un borde de 2 px;
  - se activan con Enter o con espacio.

  Las usan los dos botones, los ítems del menú y el interruptor. Tab recorre las pantallas en el orden de lectura (comprobado con `tk_focusNext`).
- **Tipo de documento con teclado** (`CamposDocumento`): la lista muestra el foco, ↑/↓ cambian el tipo (`cambiar_tipo`) y espacio o Alt+↓ la abren. Antes, sin mouse no se podía elegir CE, pasaporte ni CPP.
- **`UsuarioDAO.autenticar`** deja pasar `ConexionBDError` con `MENSAJE_SIN_CONEXION`. Cualquier otro fallo sigue devolviendo `None`.
- `python main.py` ya abre la aplicación.

### Archivos afectados
- `views/login_view.py` y `views/app_principal.py` (nuevos)
- `views/componentes/` (nuevos: `botones.py`, `marca.py` y `campos.py`; cambian `documento.py` y `__init__.py`)
- `dao/usuario_dao.py`
- Pruebas:
  - nuevos: `tests/test_login_view.py` y `tests/test_app_principal.py`;
  - cambian: `tests/test_componentes.py`, `tests/test_usuario_dao.py` y `tests/test_auth_controller.py`.
- `CLAUDE.md` y `docs/`

### Motivo
El login y la ventana principal son la entrada a las demás pantallas de la Fase 6. Con ellos, cada pantalla nueva se prueba en la ventana real.

Los botones, la marca y el campo de texto se repiten en las dos pantallas y en las que vienen. Por eso se escriben una sola vez.

### Impacto
- Pruebas: **1646 pasan** (antes 1586).
- Las pantallas se revisaron con capturas en 1280×800 y 1093×614, en claro y en oscuro.
- Las revisó contra la lista de comprobación un agente que no las escribió. Antes, ese tipo de revisión se calibró con un error plantado a propósito, y lo encontró.
- Sin cambios de esquema.

### Decisiones
- **Sin conexión no es lo mismo que una clave incorrecta.** Que la BD no responda no dice nada de la cuenta: no revela si el documento existe ni si la clave es correcta. Avisarlo no rompe la regla de no revelar la causa de un rechazo.
  - El mensaje no incluye el detalle técnico (servidor y usuario de la BD), que va solo al log.
  - Cuando el problema es la conexión, el login conserva lo escrito para que se pueda reintentar.
- **Teclas en cola durante la verificación.** Mientras bcrypt verifica, Tk no atiende el teclado. Un Enter pulsado entonces queda en cola, así que se atiende antes de volver a habilitar el botón. Si no, iniciaría otro intento con la contraseña ya borrada y sumaría un fallo al bloqueo.
- **Campo de contraseña sin placeholder.** `campo_texto` pasa `placeholder_text=None`, no `""`: mientras CustomTkinter muestra un placeholder, aunque sea vacío, quita el `show` y la contraseña se vería.
- **Líneas divisorias con `tkinter.Frame`.** CustomTkinter no dibuja un `CTkFrame` de 1 px (comprobado en las capturas). Se repintan al cambiar de modo, como el lienzo de `MatrizCamas`.
- **La barra se crea en el orden de lectura y se coloca en otro.** Tk tabula en el orden de creación, así que el menú va antes que el pie. Pero el pie se coloca primero: en una ventana baja se recorta el menú y «Cerrar sesión» siempre queda a la vista.
- **El foco del botón principal se marca con el color del texto:** un borde azul no se vería sobre el azul.
- **Una línea separa el pie del menú.** Ocupa el lugar de la tarjeta «Conectado».
- **El círculo del interruptor cambia de color con su estado:** blanco sobre el azul cuando está encendido, y gris oscuro (`COLOR_TEXTO_SECUNDARIO`) cuando está apagado. Blanco se perdería contra la barra blanca.
- **El bloque del usuario repite la forma de la marca** (un círculo y dos líneas) con las mismas medidas de `Marca`, sin copiarlas.
- **No se copia del diseño la tarjeta «Conectado · se actualiza cada 30 s».** Hoy nada informa el estado de la conexión, y el refresco es del tablero. Va con `dashboard_view.py`.
- **Cerrar sesión no pide confirmación:** no se pierde nada.

### Pendientes
- `dashboard_view.py`, `triage_view.py` y `pacientes_view.py`, que se registran en `PANTALLAS`.
- Decidir si las medidas propias de un componente (`Marca.LADO_LOGO`, `TarjetaCama.ALTO`, `AppPrincipal.LADO_AVATAR`) se quedan en su clase o pasan a `tema.py`.
- Literales anteriores a este trabajo: `width=200` del tipo de documento en `documento.py`.
- El comentario de `tema.ESPACIO` dice que es la separación entre una etiqueta y su campo, pero los campos usan `ESPACIO_MINIMO`. Hay que alinear el comentario o el código.

---

## [2026-10-27] — Diseño de la interfaz: del Figma del equipo al tema y los componentes

### Cambio
- **Proceso de diseño** (skills impeccable, ui-ux-pro-max, frontend-design y emil-design-eng):
  - `PRODUCT.md` (contexto del producto, entrevista con el usuario);
  - `docs/diseno/BRIEF.md` (qué hace cada pantalla);
  - `docs/diseno/CRITICA.md` (crítica del primer diseño en Figma Make: 18/40, 1 P0 y 4 P1);
  - láminas y tablero aprobado en `docs/diseno/`;
  - contrato de dirección en `.impeccable/surfaces/views-dashboard-view-py.md`.
- **Decisiones del equipo:**
  - modo claro por defecto y el oscuro del Figma como opcional;
  - flujo de triaje unificado;
  - tablero pensado para 30–40 camas;
  - solo la marca SIGTAC;
  - **conservar el lenguaje y la distribución del Figma**, corrigiendo solo lo que señaló la crítica;
  - ampliar la estrategia de triaje para que devuelva los criterios de la sugerencia (pendiente).
- **`views/tema.py` reescrito.**
  - Cada color es un par (claro, oscuro): `COLOR_FONDO`, `COLOR_SUPERFICIE`, `COLOR_TEXTO`, `COLOR_PRIMARIO`…
  - Las medidas del tablero aprobado: `ANCHO_BARRA` 200, `ALTO_ENCABEZADO` 72, `ALTO_CONTROL` 36, radios 6/8.
  - Funciones nuevas: `color_actual`, `texto_sobre`, `modo_oscuro` y `cargar_fuentes`.
- **Fuente Inter** (v4.1, licencia OFL), descargada del repositorio oficial `rsms/inter`, en `views/assets/fonts/`: Regular, Medium, SemiBold y Bold, más la licencia.
  - Cada peso es una familia aparte («Inter SemiBold»), así que se pueden usar pesos intermedios aunque Tk solo tenga normal y negrita.
  - Si faltan los archivos, el tema usa Segoe UI.
- **`utils/colores.py`:** `NIVEL` y `ESTADO_CAMA` como pares; el PDF usa el tono claro.
- **Componentes:**
  - `InsigniaNivel` pasa a ser el cuadro relleno con el número;
  - `TarjetaKPI` sigue el estilo del Figma: marcador, título, valor y nota;
  - `TarjetaCama` es la casilla con borde del color del estado, el estado escrito y el código tachado si está fuera de servicio;
  - `TablaDatos` toma los tonos del modo activo y se vuelve a pintar al cambiarlo;
  - `CamposDocumento` usa los colores nuevos y muestra el foco.
- **Nuevos:**
  - `MatrizCamas`: una columna por tipo de cama. `distribuir()` busca el menor número de filas en el que caben todas, y la matriz **se desplaza por dentro solo si no alcanza el alto**: es el caso de 1093×614;
  - `marcar_foco` y `marcar_error`: borde de 2 px al enfocar y en error.
- **`Cama.NOMBRE_CORTO`** («Trauma shock», «UCI»…): el título de cada columna de la matriz.

### Archivos afectados
- `PRODUCT.md`, `docs/diseno/` (nuevos), `.impeccable/` (crítica y contrato de dirección)
- `views/tema.py`, `views/componentes/` (nuevos `matriz.py` y `foco.py`), `views/assets/fonts/` (nuevo)
- `utils/colores.py`, `utils/pdf_generator.py`, `models/cama.py`
- `tests/test_tema.py`, `tests/test_componentes.py`, `tests/test_matriz.py` (nuevo), `tests/test_cama.py`
- `docs/`, `CLAUDE.md`

### Motivo
El tema y las piezas del 2026-10-26 se hicieron sin conocer el diseño del equipo. La crítica mostró que ese diseño tenía una buena base y problemas puntuales:
- letra de 7–10 px;
- contrastes bajos;
- colores con dos significados;
- solo modo oscuro;
- se rompía en pantallas chicas.

El equipo rechazó una dirección nueva («señalética») y prefirió conservar su lenguaje visual corregido.

### Impacto
- Pruebas: **1586 pasan** (antes 1478). `test_tema.py` comprueba **en los dos modos** todos los contrastes:
  - texto: 4.5:1;
  - bordes de campo y de cama: 3:1;
  - el número sobre cada nivel.
- Verificado con capturas de los componentes reales en 1280×800 (claro y oscuro) y en 1093×614 (la matriz muestra su barra y se desplaza).
- Sin cambios de esquema.

### Decisiones
- **El rojo no es el color de marca:** significa nivel 1 y cama ocupada. El azul (#0A6CDE) queda solo para la acción principal.
- **«Reservada» pasa de azul a violeta,** para no confundirse con la acción principal.
- **Los niveles son cuadros rellenos con número; las camas, casillas con borde.** El verde y el rojo aparecen en las dos cosas, como en el Figma, pero la forma distingue qué es cada una y el texto siempre va escrito.
- **Tonos corregidos para cumplir el contraste en los dos modos:**
  - secundario #888 → #A3A3A3;
  - azul #007AFF → #0A6CDE;
  - placeholder oscuro #959595;
  - verde del nivel 4 en modo claro #188038.
- **El mapa agrupa por tipo de cama, no por área:** los nombres de área del seed («Unidad de Cuidados Intensivos (UCI)») no caben en una columna angosta.
- **«F. de servicio» dentro de la casilla:** «Fuera de servicio» no cabe en el ancho mínimo (100 px); la leyenda lleva el término completo.
- **Desplazamiento interno en lugar de achicar la letra:** en 1093×614, Observación necesita 8 filas. Achicar las casillas habría vuelto a la letra ilegible del Figma.
- **`ttk` con el tema «clam»:** es el que permite pintar el encabezado de la tabla; el tema predeterminado de Windows lo ignora.
- **Foco visible a mano:** CustomTkinter no dibuja un anillo de foco. Las pruebas llaman directamente a `al_entrar`/`al_salir`, porque Tk no entrega eventos de foco sintéticos a una ventana oculta.

### Pendientes
- Íconos de KPIs, logo y menú (descarga pendiente).
- Ampliar la estrategia de triaje para que devuelva los criterios, antes de la pantalla de triaje.
- D5: prototipo de las 5 pantallas sobre este tema. D6: revisión independiente. D7: Figma para el equipo. D8: `DESIGN.md`.

---

## [2026-10-26] — Fase 6: piezas compartidas de la interfaz (`views/componentes/`)

### Cambio
- **`views/componentes/`**: las piezas que usarán las pantallas.
  - `errores.py`: `mostrar_error(ventana, error)`, `mostrar_info` y `confirmar` (diálogos de `tkinter.messagebox` con el título «SIGTAC»).
  - `documento.py`: `CamposDocumento`, el tipo (lista) y el número del documento. Tiene `valores()`, `fijar()`, `limpiar()` y `bloquear()`, y no valida.
  - `nivel.py`: `texto_nivel(n)` («3 · Amarillo», «Sin triaje») e `InsigniaNivel`, el nivel sobre su color.
  - `tarjetas.py`: `TarjetaKPI` (título y valor, «—» sin dato) y `TarjetaCama` (código y estado sobre el color del estado; 120 × 72 px).
  - `tabla.py`: `TablaDatos`, un `ttk.Treeview` con el estilo del tema y una barra de desplazamiento. Cada fila tiene un id oculto (`seleccionado()`, `seleccionar(id)`, callback `al_seleccionar`) y, si no hay filas, muestra un texto.
- **`Cama.NOMBRE_TIPO`** (`models/cama.py`): cada subclase declara el nombre de su tipo (el de `tipo_cama`). `CamaDAO.CLASES_POR_TIPO` se arma a partir de ellas, y el mapa de camas lo usará como título de cada grupo.
- **Tema**:
  - nuevas entradas `COLOR_SIN_DATO`, `COLOR_SUPERFICIE` y la fuente `"cifra"`;
  - `escala(widget)`, `fuente_ttk(uso, widget)` y `color_acento()`.
- Pruebas:
  - `tests/test_componentes.py` (36);
  - `test_tema.py` (+4);
  - `test_cama.py` (+1: `NOMBRE_TIPO`);
  - `test_capas.py` cubre los archivos nuevos.

### Archivos afectados
- `views/componentes/` (nuevo: `__init__.py`, `errores.py`, `documento.py`, `nivel.py`, `tarjetas.py`, `tabla.py`)
- `views/tema.py`, `models/cama.py`, `dao/cama_dao.py`
- `tests/test_componentes.py` (nuevo), `tests/test_tema.py`, `tests/test_cama.py`
- `docs/`

### Motivo
Las 5 pantallas repiten tablas, el nivel de triaje, tarjetas, el documento y el manejo de errores. Con una pieza por cosa, cada una se escribe y se prueba una sola vez, y todas las pantallas se ven y se comportan igual (acordado en el plan de la Fase 6).

### Impacto
- Pruebas: **1478 pasan** (antes 1431).
- Sin cambios de esquema. `CLASES_POR_TIPO` tiene las mismas claves que antes, y `test_estados_vs_bd.py` lo sigue comparando con `seed.sql`.

### Decisiones
- **La tabla escala su letra a mano.** CustomTkinter mide sus fuentes en píxeles y las multiplica por el zoom de Windows. Un widget `ttk` recibe la misma fuente pero interpreta el 13 como puntos, así que en la primera captura la tabla se veía más grande que el resto. Ahora `fuente_ttk` la pasa en píxeles escalados, y el alto de fila y el ancho de columna también se multiplican por la escala.
- **Las piezas se revisaron en una captura** (ventana de muestra con controladores falsos). Así aparecieron:
  - la letra grande de la tabla;
  - el fondo gris del texto de tabla vacía, que ahora usa `COLOR_SUPERFICIE`;
  - el texto de tabla vacía que tapaba el encabezado, que ahora se centra en la zona de filas.
- **`CamposDocumento` no valida.** El formato del DNI lo valida solo `DocumentoIdentidad`, y su `ValueError` vuelve por `mostrar_error`; si la vista lo validara también, la regla quedaría en dos capas. `fijar()` funciona aun con los campos bloqueados (al editar un paciente).
- **El tipo de cama va en el título del grupo, no en cada tarjeta.** El plan decía «código, tipo y estado», pero repetir «Cama UCI con Ventilador» en cada casilla no cabe en 120 px y no aporta nada si el mapa ya agrupa por tipo.
- **`NOMBRE_TIPO` en el modelo, no en la vista.** La vista no puede leer `CamaDAO.CLASES_POR_TIPO` (regla de capas). Un diccionario clase → nombre en la vista repetiría lo que ya sabe el DAO. Con el atributo, cada clase dice su nombre (polimorfismo) y el DAO lo reutiliza.
- **`confirmar()` se sumó a `errores.py`.** Pacientes la necesita para fusionar, y así todos los diálogos salen del mismo lugar.
- **La fila elegida de la tabla usa el color de los botones** (`color_acento()`, leído del tema de CustomTkinter), con el texto oscuro: contraste de 4.57:1.

### Pendientes
- Las 5 pantallas, empezando por `login_view.py`, que pasa a ser la referencia y con la que se calibra la revisión.

---

## [2026-10-26] — Fase 6 (inicio): plan de las vistas, tema y punto de entrada

### Cambio
- **Plan de la Fase 6 acordado.**
  - Alcance: las 5 pantallas del plan (login, ventana principal, dashboard, triaje y pacientes).
  - Piezas compartidas en `views/componentes/`.
  - Detalle en `docs/DEVELOPMENT_PLAN.md`.
- **`views/tema.py`:** único lugar de los valores de la interfaz:
  - modo claro y tema "blue" de CustomTkinter;
  - espaciado en base 8 (`ESPACIO`, `ESPACIO_2`, `ESPACIO_3`);
  - colores de nivel, de estado de cama, de error y de texto secundario;
  - `fuente(uso)` para título, subtítulo, normal y pequeña;
  - `color_texto_sobre(fondo)`: elige texto claro u oscuro según el contraste (fórmula de luminancia de WCAG).
- **`utils/colores.py`:** tonos de los niveles de triaje y de los estados de cama.
  - El PDF ya no tiene su propia copia (`_RGB_POR_NIVEL`): usa `HEX_POR_NIVEL`, igual que las vistas.
- **`main.py`:** punto de entrada (`python main.py`).
  - La clase `Aplicacion` maneja una sola ventana y cambia entre `LoginView` y `AppPrincipal`. Las dos pantallas reciben callbacks (`al_iniciar`, `al_cerrar`) y no se conocen entre sí.
  - Al cerrar la ventana, también se cierra la sesión.
- **`Triaje.MIN_JUSTIFICACION = 10`** (`models/triaje.py`): reemplaza el 10 escrito a mano en `reclasificar`. La vista de triaje mostrará el mínimo leyéndolo de aquí.
- Pruebas:
  - `tests/test_tema.py` (28);
  - `tests/test_capas.py` (4): ningún archivo de `views/` ni `main.py` importa `dao` o `mysql`;
  - el límite de la justificación en `test_triaje.py`;
  - `MIN_JUSTIFICACION` contra el `CHECK CH_triaje_rn10` en `test_estados_vs_bd.py`;
  - nuevo fixture `raiz_tk` en `conftest.py`.

### Archivos afectados
- `main.py`, `views/__init__.py`, `views/tema.py`, `utils/colores.py` (nuevos)
- `utils/pdf_generator.py`, `models/triaje.py`
- `tests/conftest.py`, `tests/test_tema.py` y `tests/test_capas.py` (nuevos), `tests/test_triaje.py`, `tests/test_estados_vs_bd.py`
- `docs/`, `CLAUDE.md`

### Motivo
Es la base que necesitan todas las pantallas de la Fase 6. Si cada vista escribiera sus propios colores y tamaños, se verían distintas y un cambio de diseño habría que repetirlo en cada archivo.

### Impacto
- Pruebas: **1431 pasan** (antes 1397).
- `main.py` todavía no se puede ejecutar: importa `views/login_view.py` y `views/app_principal.py`, que son las próximas tareas.
- Sin cambios de esquema.

### Decisiones
- **Una sola ventana** (`ctk.CTk`) cuyo contenido se reemplaza, en lugar de abrir una ventana por pantalla. Es más simple de cerrar (una sola sesión) y no deja ventanas huérfanas.
- **`fuente(uso)` es una función, no una constante:** Tk solo crea fuentes cuando la ventana ya existe; una constante `CTkFont` al importar el módulo fallaría.
- **`color_texto_sobre`** calcula el contraste en lugar de fijar a mano qué texto va sobre cada color. Por ejemplo, el ámbar (reservada, nivel 3) necesita texto oscuro y el rojo, blanco. Una prueba comprueba que todos los colores del tema queden con un contraste de al menos 4.5:1.
- **Tonos (hex) en `utils/` y nombres de color en `models/`:** «Rojo» es un dato del dominio (está en el catálogo `nivel_triaje`); `#C62828` es solo cómo se dibuja.
- **Una ventana Tk por sesión de pruebas:** crear y destruir una por prueba fallaba de forma intermitente (Tcl no terminaba de iniciarse: `init.tcl`, `tk.tcl`, `tcl_findLibrary`). Con una sola ventana, ocho corridas seguidas pasaron sin fallos. Cada prueba destruye al terminar los widgets que creó.
- **`test_capas.py`** convierte en prueba la regla «las vistas nunca acceden a la BD».

### Pendientes
- `views/componentes/` y las 5 pantallas.
- Probar `python main.py` contra `sigtac_db` cuando existan el login y la ventana principal (lo hace el usuario).

---

## [2026-10-26] — Fase 5: reporte de indicadores en PDF (`utils/pdf_generator.py`)

### Cambio
- **Nuevo `utils/pdf_generator.py`** (ReportLab). Recibe `IndicadoresPeriodo` y `EstadoGuardia` ya calculados y arma un PDF A4 con:
  - el período, la fecha de generación y quién lo generó;
  - la tabla de indicadores del período y un gráfico de barras de los triajes por nivel, cada barra con el color de su nivel (el gráfico se omite si no hubo triajes);
  - el estado de la guardia al generar el reporte (camas por estado, ocupación, pacientes en emergencia);
  - notas con la definición de cada indicador y un pie de página con el aviso de prototipo académico y el número de página.
- Funciones públicas:
  - `filas_indicadores`, `filas_camas`, `filas_pacientes`, `formatear_minutos` y `formatear_porcentaje`: arman el texto de las tablas y se prueban sin abrir el PDF;
  - `construir_reporte(...) -> bytes`: arma el PDF en memoria;
  - `validar_ruta_pdf(ruta)`: exige la extensión `.pdf` (`ValueError`);
  - `guardar_reporte(ruta, ...)`: escribe el archivo; si no puede (carpeta inexistente, sin permisos, PDF abierto en otro programa) lanza `ReporteError`.
- **`ReporteController.exportar_pdf(desde, hasta, ruta)`** (permiso REPORTES): valida la ruta, obtiene `indicadores` y `estado_actual` y guarda el PDF. Devuelve la ruta.
- Nuevos `ReporteError` (`models/excepciones.py`) y `COLOR_POR_NIVEL` (`models/triaje.py`: 1 Rojo … 5 Azul).
- `scripts/verificar_controladores.py` exporta el PDF con los datos reales de la base temporal y comprueba que no escribe en la bitácora.
- Pruebas: nuevo `tests/test_pdf_generator.py` (39); `test_reporte_controller.py` (+8: exportar) y `test_estados_vs_bd.py` (+1: `COLOR_POR_NIVEL` contra `nivel_triaje` del seed).

### Archivos afectados
- `utils/pdf_generator.py` (nuevo), `controllers/reporte_controller.py`, `models/excepciones.py`, `models/triaje.py`
- `scripts/verificar_controladores.py`, `tests/test_pdf_generator.py` (nuevo), `tests/test_reporte_controller.py`, `tests/test_estados_vs_bd.py`
- `docs/`, `CLAUDE.md`

### Motivo
Era lo único pendiente de la Fase 5. Además completa el punto "Reportes → indicadores/PDF" de la integración (Fase 7).

### Impacto
- Pruebas: **1397 pasan** (antes 1349).
- Sin cambios de esquema ni de dependencias: `reportlab==5.0.1` ya estaba en `requirements.txt`.
- La vista de reportes (Fase 6) solo tiene que pedir el período y la ruta (diálogo "Guardar como") y llamar a `exportar_pdf`.

### Decisiones
- **El generador solo presenta:**
  - no consulta la BD, no comprueba permisos y no calcula indicadores;
  - lo único que decide es el formato (minutos → "2 h 05 min", `None` → "Sin datos").
- **La exportación es una operación del controlador** (`exportar_pdf`), no de la vista. El permiso y la obtención de los datos quedan en un solo lugar, y la vista no necesita conocer `pdf_generator`.
- **Importación circular evitada con `TYPE_CHECKING`:**
  - `reporte_controller` importa `pdf_generator`;
  - el generador importa `EstadoGuardia` e `IndicadoresPeriodo` solo para las anotaciones de tipo;
  - así no hay que mover esas clases de lugar.
- **La ruta se valida antes de consultar la BD:** un error de la vista (extensión equivocada) no hace consultas inútiles. Es el mismo patrón que en el resto de controladores (validar → BD).
- **El PDF se arma en memoria y luego se escribe:** si ReportLab falla, no queda un archivo a medias en el disco.
- **`OSError` → `ReporteError`:** la vista captura `SigtacError` y muestra el mensaje. El caso típico en Windows es intentar sobrescribir un PDF que está abierto en el visor (`PermissionError`).
- **Indicadores y estado actual en dos transacciones:** son dos lecturas independientes a segundos de distancia. Unirlas no cambiaría lo que el reporte muestra.
- **Exportar no se audita:** la bitácora registra los cambios de datos, y exportar es una lectura. Queda un `logger.info` con el período, sin el nombre del usuario.
- **El nombre de quien genera el reporte sí va en el PDF:** es un documento para imprimir y firmar, no un log. Se escapa con `xml.sax.saxutils.escape`, porque `Paragraph` interpreta `<` y `&` como marcado.
- **Gráfico con ReportLab y no con matplotlib:** se dibuja como vectores dentro del PDF, sin imagen intermedia. matplotlib queda para el dashboard (Fase 6).
- **`COLOR_POR_NIVEL` en `models/triaje.py`:** el color es un dato del dominio que también usarán las vistas. Los tonos RGB de las barras son presentación y viven en el generador.

### Pendientes
- Ejecutar `scripts/verificar_controladores.py` (lo hace el usuario con su cuenta de administrador) para confirmar la exportación con datos reales.
- Vista de reportes (Fase 6): selector de período, diálogo "Guardar como" y botón "Exportar PDF".

---

## [2026-10-26] — Pendientes de la Fase 4: referir, fuga, fuera de servicio, edición de pacientes y administración

### Cambio
- **Cierre de episodios** (`models/triaje.py`): `EpisodioEmergencia.referir()` (solo desde EN ESPERA DE CAMA o EN ATENCIÓN: exige triaje) y `registrar_fuga()` (desde cualquier estado abierto). Ambos, y `dar_alta`, cierran con `_cerrar`, que guarda la fecha de egreso.
  - `EpisodioDAO.cambiar_estado` pone `fecha_alta = NOW()` en cualquier cierre (alta, referido o fuga), no solo en el alta.
  - `ReporteDAO.promedio_estancia_min` ahora filtra por ALTA MÉDICA.
  - `CamaController.referir` y `registrar_fuga` liberan la cama si el paciente tenía una: si solo estaba reservada vuelve a DISPONIBLE y la asignación se anula; si estaba ocupada pasa a EN LIMPIEZA con su solicitud (RN-07).
- **Mantenimiento de camas** (`CamaController`): `poner_fuera_de_servicio(id_cama, motivo)` y `volver_a_servicio(id_cama)`.
  - El motivo es obligatorio (máx. 200 caracteres) y queda en la bitácora.
  - Se rechaza una cama con paciente asignado, con limpieza pendiente o que ya está fuera de servicio.
  - Nuevo `SolicitudLimpiezaDAO.buscar_pendiente_por_cama`.
- **Pacientes** (`models/persona.py`):
  - `Paciente.actualizar_datos(...)` devuelve los campos que cambiaron. Un NN conserva "NN" como nombre hasta que se identifica.
  - `Paciente.reactivar()`: un NN dado de baja no se reactiva.
  - En `PacienteController`:
    - `actualizar_datos`: permiso PACIENTES; bloquea la fila primero. La auditoría guarda solo los nombres de los campos.
    - `dar_de_baja` y `reactivar`: permiso ADMINISTRACION. No se da de baja a un paciente con un episodio abierto.
  - `PacienteDAO.actualizar` solo modifica pacientes activos.
  - Nuevos `PacienteDAO.reactivar` (UPDATE condicional) y la acción de auditoría `REACTIVAR`.
- **Administración** (nuevos `models/usuario.py` y `controllers/admin_controller.py`, permiso ADMINISTRACION):
  - `CuentaUsuario`, con las transiciones `activar`, `desactivar`, `cambiar_rol` y `desbloquear`.
  - `validar_clave_nueva`: mínimo 8 caracteres, letras y números, máximo 72 bytes y sin espacios en los extremos.
  - `AdminController` ofrece: `listar_cuentas`, `listar_empleados_sin_cuenta`, `listar_roles`, `crear_cuenta`, `cambiar_rol`, `desactivar`, `activar`, `restablecer_clave`, `desbloquear`, `bitacora(desde, hasta, tabla, id_usuario, limite)` e `historial_de_registro`.
  - `UsuarioDAO` gana los métodos de administración de cuentas: `listar_cuentas`, `buscar_cuenta`, `crear_cuenta`, `cambiar_rol` y `cambiar_activo` (los dos últimos con UPDATE condicional), `restablecer_clave` y `desbloquear`.
  - `AuditoriaDAO.listar` consulta la bitácora por período, con filtros opcionales y un tope de 1000 filas.
- `BaseDAO._validar_periodo` (antes solo en `ReporteDAO`): ahora también lo usa `AuditoriaDAO`.
- `scripts/verificar_controladores.py` se amplía con todos estos flujos. Incluye un **login real** con una cuenta creada por el administrador: cambio de rol, desactivación, bloqueo por 5 intentos, desbloqueo y clave restablecida.
- Pruebas:
  - nuevas: `tests/test_admin_controller.py` (86) y `tests/test_usuario.py` (27);
  - ampliadas: `test_cama_controller` (92), `test_paciente_controller` (78), `test_usuario_dao`, `test_auditoria_dao`, `test_paciente_dao`, `test_asignacion_dao`, `test_episodio_dao`, `test_reporte_dao`, `test_triaje` y `test_persona`.

### Archivos afectados
- `models/triaje.py`, `models/persona.py`, `models/auditoria.py`, `models/usuario.py` (nuevo)
- `dao/base_dao.py`, `dao/episodio_dao.py`, `dao/reporte_dao.py`, `dao/paciente_dao.py`, `dao/solicitud_limpieza_dao.py`, `dao/usuario_dao.py`, `dao/auditoria_dao.py`
- `controllers/cama_controller.py`, `controllers/paciente_controller.py`, `controllers/admin_controller.py` (nuevo)
- `scripts/verificar_controladores.py`, `tests/`, `docs/`, `CLAUDE.md`

### Motivo
Eran los "pendientes conocidos" de la Fase 4:
- operaciones sin controlador (camas fuera de servicio, editar y reactivar pacientes, cuentas y bitácora);
- estados del catálogo sin transición en el modelo (REFERIDO y FUGADO).

Las vistas de la Fase 6 los necesitan.

### Impacto
- Pruebas: **1349 pasan** (antes 1104).
- `promedio_estancia_min` ya no cuenta los referidos ni las fugas, aunque todos tienen fecha de egreso.
- Sin cambios de esquema (`accion` de la bitácora es `VARCHAR` sin `CHECK`): no hace falta recrear `sigtac_db`.
- Verificación ampliada en MySQL (`scripts/verificar_controladores.py`, ejecutada por el usuario con su cuenta de administrador): **todas las comprobaciones correctas**, incluido el login real con la cuenta creada por el administrador.

### Decisiones
- **`fecha_alta` es la fecha de egreso:** se guarda en todo cierre, porque el episodio terminó igual. Por eso el indicador de estancia filtra por ALTA MÉDICA: si no, una fuga a los pocos minutos acortaría el promedio.
- **Referir exige triaje y la fuga no:** referir es una decisión clínica sobre un paciente evaluado; irse se puede antes de que lo vean.
- **Referir y fuga con permiso GESTION_CAMAS (médico y jefe de guardia):** liberan una cama, igual que el alta. Queda por validar con el equipo si el enfermero también debe registrar una fuga desde la sala de espera.
- **Fuera de servicio con GESTION_CAMAS:**
  - El modelo admite decretarlo desde cualquier estado (no cambió).
  - El controlador lo impide si hay una asignación vigente o una limpieza pendiente; si no, quedarían abiertas sobre una cama fuera de servicio.
  - Para una cama con un paciente dentro falta el **traslado de cama**.
- **Baja y reactivación de pacientes con ADMINISTRACION:** son correcciones de registros (un duplicado, una baja por error), no parte de la atención. Editar los datos sí es de PACIENTES.
- **Un administrador no se desactiva ni cambia su propio rol:** así el sistema no se queda sin administrador por un clic equivocado. Lo hace otro administrador.
- **Política de claves en el modelo, hash en el controlador:** el DAO rechaza cualquier valor que no sea un hash bcrypt, como defensa por si se le pasara la clave en texto plano por error. Ni la clave ni el hash van a la bitácora ni a los logs.
- **72 bytes como máximo:** bcrypt ignora (y bcrypt 5 rechaza) lo que pase de 72 bytes. Se mide en bytes UTF-8: "ñ" ocupa 2.

### Pendientes
- Traslado de cama, para un paciente cuya cama falla.
- Validar con el equipo los permisos nuevos: fuga con GESTION_CAMAS, y baja y reactivación con ADMINISTRACION.
- Una cuenta desactivada que ya tenía la sesión abierta en otra PC la conserva hasta cerrarla: la sesión vive en la aplicación.
- Que cada usuario pueda cambiar su propia clave (hoy solo la restablece el administrador).
- Actualizar `db_scripts/diagrama.png`.

---

## [2026-10-22] — Revisión de la Fase 4 antes de fusionar con `main`

### Cambio
- `models/triaje.py`: `Triaje` (nivel sugerido) y `Triaje.reclasificar` (nivel nuevo) solo aceptan enteros del 1 al 5 (`_es_nivel_valido`). Antes `True` pasaba como nivel 1 y `2.0` como nivel 2, porque `True in range(1, 6)` y `2.0 in range(1, 6)` son verdaderos en Python.
- `scripts/verificar_controladores.py`: se quita un import sin usar y se comenta por qué el `DROP DATABASE` arma el nombre con una constante (un nombre de base no puede ir como parámetro).
- Pruebas: `test_el_nivel_debe_ser_un_entero` en `tests/test_triaje.py` (5 casos).

### Archivos afectados
- `models/triaje.py`, `scripts/verificar_controladores.py`, `tests/test_triaje.py`, `docs/`

### Motivo
Revisión de la rama `feat/fase4-controladores` antes de fusionarla. Con los controladores, el nivel final llega desde la vista (`TriajeController.registrar(..., nivel_final=...)`): un valor mal convertido (un checkbox, un `float`) no debe aceptarse como nivel.

### Impacto
- Pruebas: 1104 pasan. Verificación en MySQL repetida: 56 de 56.
- Sin cambios de comportamiento para niveles enteros válidos.

### Decisiones
- **La regla queda en el modelo:** es la validación del nivel de triaje; el controlador no la repite.

### Pendientes
- Ninguno nuevo.

---

## [2026-10-22] — Verificación de la Fase 4 en MySQL 8.0.46 (`scripts/verificar_controladores.py`)

### Cambio
- Nuevo `scripts/verificar_controladores.py`: crea `sigtac_scratch_tmp`, carga `schema.sql` y `seed.sql`, recorre el flujo completo a través de los cinco controladores (admisión → triaje → cola → asignación → ocupación → alta → limpieza → reportes) y elimina la base al terminar. Es el primer script de verificación que queda en el repositorio (los anteriores eran temporales).
- `CLAUDE.md`: comando del script y reglas de los controladores (patrón de cada operación, `bloquear`, pruebas con `CapaDatosFalsa`).

### Archivos afectados
- `scripts/verificar_controladores.py` (nuevo), `CLAUDE.md`, `docs/`

### Motivo
Las pruebas de los controladores simulan la BD; faltaba comprobar contra MySQL real el SQL nuevo (historial en bloque, `FOR UPDATE`, consultas de reportes) y el flujo de punta a punta.

### Impacto
- **56 de 56 comprobaciones correctas** en MySQL 8.0.46, entre ellas:
  - Dos PCs admiten a la misma paciente a la vez: la segunda espera el bloqueo (1,5 s) y luego rechaza el segundo episodio; queda uno solo.
  - Otra PC da de alta un episodio mientras se registra su triaje: el triaje espera el bloqueo, ve el alta y no guarda nada.
  - El historial cargado en bloque (`listar_por_estado`) es igual al de `buscar_por_id`.
  - Asignar a una cama incompatible o ya reservada se rechaza y no cambia el episodio; dar de alta una cama solo reservada se deshace por completo.
  - Ciclo completo de la cama con historial, asignación, solicitud de limpieza y bitácora; cancelar una reserva no pasa por limpieza.
  - Reportes: ocupación, pacientes en emergencia, ingresos, triajes por nivel, reclasificación y tiempos promedio coinciden con consultas directas (p. ej. estancia 30 min = (45 + 15) / 2).
- No se tocó `sigtac_db`.

### Decisiones
- **El script queda en `scripts/`, no en `tests/`:** necesita MySQL y una cuenta de administrador; `python -m pytest` debe seguir funcionando sin BD.
- **Clave por variable de entorno o `getpass`:** `SIGTAC_ADMIN_PWD` (solo para ese proceso) permite ejecutarlo sin escribir la clave; nunca se guarda en un archivo.
- **Concurrencia con una segunda conexión real en otro hilo:** la única forma de comprobar que `FOR UPDATE` hace esperar y que, después de esperar, se ven los datos confirmados por la otra PC.

### Pendientes
- Convertirlo en pruebas de integración de pytest (marcadas y omitidas si no hay BD) cuando se acuerde cómo dar la cuenta de administrador en el equipo.

---

## [2026-10-22] — Fase 4: `reporte_dao.py` y `reporte_controller.py` (indicadores)

### Cambio
- Nuevo `dao/reporte_dao.py` (`ReporteDAO`, solo lectura): `contar_camas_por_estado`, `contar_episodios_por_estado`, `contar_ingresos`, `contar_triajes_por_nivel`, `contar_reclasificaciones`, `promedio_espera_triaje_min`, `promedio_espera_cama_min` y `promedio_estancia_min`. Los períodos son `[desde, hasta)` con `datetime`.
- Nuevo `controllers/reporte_controller.py` con `ReporteController(sesion)` (permiso `REPORTES`):
  - `estado_actual() -> EstadoGuardia`: camas por estado, porcentaje de ocupación y pacientes en emergencia por estado.
  - `indicadores(desde, hasta) -> IndicadoresPeriodo`: ingresos, triajes por nivel, porcentaje de reclasificación y tiempos promedio (puerta-triaje, espera de cama y estancia), entre dos días incluidos.
- Pruebas: `tests/test_reporte_dao.py` (44) y `tests/test_reporte_controller.py` (17).

### Archivos afectados
- `dao/reporte_dao.py`, `controllers/reporte_controller.py` (nuevos), `tests/test_reporte_dao.py`, `tests/test_reporte_controller.py` (nuevos), `docs/`

### Motivo
Último controlador del plan de la Fase 4 ("consultar datos, preparar AVG/COUNT y KPIs, entregar datos a las vistas").

### Impacto
- Pruebas: 1099 pasan.
- Las vistas reciben objetos inmutables (`dataclass(frozen=True)`) con los números ya calculados.

### Decisiones
- **SQL en el DAO, porcentajes en el controlador:** contar y promediar se hace en MySQL (no se traen miles de filas a Python); el plan pedía que el controlador "preparara AVG/COUNT", pero el SQL solo puede vivir en un DAO.
- **LEFT JOIN desde los catálogos:** un estado o nivel sin filas aparece con 0, así la vista siempre recibe todas las categorías.
- **Período `[desde, hasta)`:** el controlador recibe días (`date`) y consulta desde las 00:00 del primero hasta las 00:00 del día siguiente al último; así el último día entra completo sin depender de `23:59:59`.
- **Ocupación = (reservadas + ocupadas) / (camas activas − fuera de servicio):** una cama reservada ya está comprometida; una en limpieza no está en uso pero sí en servicio.
- **Pacientes en emergencia:** se descartan los estados cerrados con `EpisodioEmergencia.ESTADOS_CERRADOS` del modelo (la regla no se repite en el controlador).
- **Lecturas en una transacción:** todas las cifras de un reporte salen de la misma foto de la BD.
- **Las reservas canceladas no cuentan** en la espera de cama (`asignacion_cama.estado_registro = FALSE`).

### Pendientes
- Exportar los indicadores a PDF (`utils/pdf_generator.py`, Fase 5).
- Indicador de pacientes atendidos dentro del tiempo máximo de su nivel (`nivel_triaje.tiempo_max_min`).

---

## [2026-10-22] — Fase 4: `cama_controller.py` (ciclo de la cama)

### Cambio
- Nuevo `controllers/cama_controller.py` con `CamaController(sesion)`:
  - `VER_CAMAS`: `mapa_camas()`, `cola_de_espera()` (episodios EN ESPERA DE CAMA por prioridad).
  - `GESTION_CAMAS`: `camas_compatibles(id_episodio)`, `asignar(id_episodio, id_cama)`, `ocupar(id_cama)`, `cancelar_asignacion(id_episodio)`, `dar_alta(id_episodio)`.
  - `LIMPIEZA`: `solicitudes_limpieza()`, `confirmar_limpieza(id_solicitud)`.
- Pruebas: `tests/test_cama_controller.py` (57).

### Archivos afectados
- `controllers/cama_controller.py` (nuevo), `tests/test_cama_controller.py` (nuevo), `docs/`

### Motivo
Es el núcleo del sistema (asignación de camas): une los modelos `Cama` y `EpisodioEmergencia` con los DAO de cama, episodio, asignación, limpieza y auditoría en transacciones atómicas.

### Impacto
- Pruebas: 1038 pasan.
- Flujos y lo que guarda cada uno (todo en una transacción, con auditoría):

  | Operación | Episodio | Cama | Además |
  |---|---|---|---|
  | `asignar` | EN ESPERA DE CAMA → EN ATENCIÓN | DISPONIBLE → RESERVADA | `AsignacionDAO.crear` |
  | `ocupar` | — | RESERVADA → OCUPADA | exige asignación vigente |
  | `cancelar_asignacion` | EN ATENCIÓN → EN ESPERA DE CAMA | RESERVADA → DISPONIBLE | `AsignacionDAO.anular` |
  | `dar_alta` | EN ATENCIÓN → ALTA MÉDICA | OCUPADA → EN LIMPIEZA | `AsignacionDAO.liberar` + `SolicitudLimpiezaDAO.crear` |
  | `confirmar_limpieza` | — | EN LIMPIEZA → DISPONIBLE | `SolicitudLimpiezaDAO.atender` |

### Decisiones
- **Compatibilidad en el controlador, con la regla del modelo:** `asignar` rechaza una cama que no sea `es_compatible` con el nivel actual; el controlador solo la aplica, la regla sigue siendo de cada subclase de `Cama`.
- **Primero RN-01, después la compatibilidad:** `episodio.asignar_cama()` va antes del chequeo de compatibilidad para que, sin triaje, el error diga "RN-01" y no "cama incompatible".
- **Concurrencia por `UPDATE` condicional:** si otra PC tomó la cama (o cambió el episodio) entre la lectura y la escritura, `cambiar_estado` lanza la excepción y se deshace todo, también el cambio del episodio que ya se había guardado. No hace falta bloquear filas porque estas operaciones siempre cambian el estado.
- **`ocupar` exige una asignación vigente:** el modelo permite ocupar desde DISPONIBLE, pero sin asignación no se sabría qué paciente está en la cama.
- **No se da de alta una cama solo reservada:** primero se ocupa (el paciente llegó) o se cancela; así una reserva que no se usó no pasa por limpieza.
- **Auditoría por operación:** asignación (`INSERT`/`ANULAR` en `asignacion_cama`), ocupación (`UPDATE` en `cama`), alta (`UPDATE` en `episodio_emergencia`, con la solicitud de limpieza) y limpieza (`UPDATE` en `solicitud_limpieza`). El historial de estados de la cama ya lo guarda `CamaDAO`, pero no dice quién: la bitácora sí.

### Pendientes
- Fuera de servicio / volver a servicio (el modelo lo tiene; falta decidir quién puede y qué pasa con un paciente en una cama que falla).
- Transiciones a REFERIDO y FUGADO (siguen pendientes en el modelo).

---

## [2026-10-22] — Fase 4: `triaje_controller.py` y colas de espera

### Cambio
- Nuevo `controllers/triaje_controller.py` con `TriajeController(sesion, estrategia=None)` (permiso `TRIAJE`; la estrategia por defecto es `ReglaManchester`):
  - `listar_sintomas()`, `cola_de_triaje()` (episodios EN ESPERA DE TRIAJE por orden de llegada).
  - `sugerir(signos, ids_sintomas) -> Sugerencia(nivel, protocolo)`: lo que propone la estrategia, sin guardar.
  - `registrar(id_episodio, signos, ids_sintomas, nivel_final=None, justificacion=None) -> id_triaje`: signos vitales + triaje + síntomas, cambio de estado del primer triaje y auditoría, en una transacción.
- Nuevo `controllers/colas.py`: `EntradaCola(posicion, episodio, paciente)` y `armar_cola(estado)`, que comparten el triaje y la gestión de camas.
- Pruebas: `tests/test_triaje_controller.py` (41) y `tests/test_colas.py` (3).

### Archivos afectados
- `controllers/triaje_controller.py`, `controllers/colas.py` (nuevos), `tests/test_triaje_controller.py`, `tests/test_colas.py` (nuevos), `docs/`

### Motivo
Siguiente paso del flujo: el episodio abierto en admisión necesita su triaje (RN-01) para entrar en la cola de cama.

### Impacto
- Pruebas: 981 pasan.
- La vista recibe la sugerencia y el protocolo para mostrarlos, y luego llama a `registrar` con lo que el profesional decidió.

### Decisiones
- **El nivel sugerido se recalcula al registrar:** no se recibe de la vista. Así el "sugerido" de la BD es siempre lo que dijo el algoritmo y no puede alterarse para esquivar la justificación de RN-10.
- **Reclasificar solo si el nivel cambia:** si `nivel_final` es igual al sugerido (o `None`) se confirma la sugerencia y no se guarda justificación. Resuelve en el controlador el pendiente "reclasificar al mismo nivel": el controlador nunca llama a `reclasificar` con el mismo nivel (el modelo aún lo admite).
- **Bloqueo del episodio:** un segundo triaje no cambia el estado, así que no hay `UPDATE` condicional que detecte a otra PC; `EpisodioDAO.bloquear` impide que lo den de alta a mitad del registro.
- **Errores de formulario antes de la BD:** signo faltante → `SignosVitalesIncompletosError` (el mismo que usan las estrategias); signo desconocido, texto en vez de número o síntoma repetido o inexistente → `ValueError`.
- **La auditoría guarda niveles y protocolo, no la justificación:** es texto clínico (ya queda en `triaje.justificacion`).
- **Colas en un módulo aparte:** la cola de triaje y la de cama son la misma operación con distinto estado; `armar_cola` lee episodios y pacientes en una sola transacción (misma foto de la BD) y ordena con `ordenar_por_prioridad` del modelo. El permiso lo comprueba cada controlador.

### Pendientes
- Mostrar en la cola si se superó el tiempo máximo de espera del nivel (`nivel_triaje.tiempo_max_min`).

---

## [2026-10-22] — Fase 4: `paciente_controller.py` (admisión y pacientes NN)

### Cambio
- Nuevo `controllers/paciente_controller.py` con `PacienteController(sesion)`, todo con el permiso `PACIENTES`:
  - Consultas: `listar_seguros()`, `buscar_por_documento(tipo, numero)`, `listar_no_identificados()`.
  - `registrar(...)`: paciente con documento; rechaza un documento ya registrado (activo o dado de baja).
  - `registrar_no_identificado(sexo, edad_estimada, id_seguro)`: paciente NN.
  - `abrir_episodio(id_paciente, motivo_consulta)`: el episodio empieza EN ESPERA DE TRIAJE; un paciente no puede tener dos episodios abiertos.
  - `identificar(id_paciente, ...)`: si el documento ya es de otro paciente, pide fusionar en lugar de duplicar a la persona.
  - `fusionar(id_nn, id_destino)`: no fusiona si los dos tienen un episodio abierto.
  - Cada escritura va con su auditoría (`INSERT`, `IDENTIFICAR`, `FUSIONAR`) dentro de la misma transacción.
- `tests/conftest.py` (nuevo): `CapaDatosFalsa` (reemplaza los DAO y `transaccion()` de un controlador y anota el orden de las llamadas) y la fábrica `sesion_de(rol)`.
- Pruebas: `tests/test_paciente_controller.py` (54).

### Archivos afectados
- `controllers/paciente_controller.py` (nuevo), `tests/conftest.py` (nuevo), `tests/test_paciente_controller.py` (nuevo), `docs/`

### Motivo
Sin admisión no hay episodio, y sin episodio no hay triaje ni cama. Los pacientes NN ya estaban resueltos en modelos y DAO; faltaba quien orquestara las reglas con permisos, transacción y auditoría.

### Impacto
- Pruebas: 937 pasan.
- Patrón de todos los controladores: `exigir_permiso` → validar datos con el modelo (sin tocar la BD) → `with transaccion():` leer, aplicar la regla del modelo, guardar y auditar.

### Decisiones
- **Leer dentro de la transacción:** los datos se cargan en la misma transacción que los guarda; así ninguna operación trabaja con un objeto que quedó viejo tras un fallo o tras el cambio de otra PC.
- **Validar antes de abrir la transacción:** un dato inválido (`ValueError`) no llega a la BD.
- **Un episodio abierto por paciente:** la persona sigue en emergencia; abrir otro duplicaría su cola y su cama. La fila del paciente se bloquea (`PacienteDAO.bloquear`) para que dos PCs no lo admitan a la vez. No hay restricción en la BD (no es fácil expresarla con `UNIQUE`); queda en el controlador.
- **Documento existente:** se avisa con `ReglaNegocioError` antes de insertar (mensaje claro para la vista); el `UNIQUE` sigue respaldando la regla si dos PCs registran a la vez (`RegistroDuplicadoError`, se deshace todo).
- **Identificar con un documento ajeno:** se rechaza y se indica fusionar; identificar duplicaría a la persona (y el `UNIQUE` lo impediría con un error menos claro).
- **Auditoría sin datos personales:** solo ids (`{"id_destino": 1, "episodios_movidos": 1}`).
- **Pruebas con un registro de llamadas:** `CapaDatosFalsa` permite comprobar el orden exacto (`inicio` → escrituras → auditoría → `commit`) y que ante un error haya `rollback` sin auditoría.

### Pendientes
- Reactivar un paciente dado de baja (hoy solo se informa; no hay método).
- Editar los datos de un paciente identificado (`PacienteDAO.actualizar` existe; falta decidir quién puede y si se audita con `UPDATE`).

---

## [2026-10-22] — Base para los controladores: colas, historial en bloque y bloqueo de filas

### Cambio
- `models/triaje.py`:
  - `EpisodioEmergencia.nivel_actual`: nivel final del triaje vigente (o `None`).
  - `ordenar_por_prioridad(episodios)`: orden de la cola de espera (nivel más urgente primero; a igual nivel, el que llegó antes; sin triaje, al final por llegada).
  - `SignosVitales` rechaza valores que no sean números (`ValueError`), p. ej. el texto `"120"` de un formulario o `True`.
- `dao/filtros_episodio.py` (nuevo): lista blanca de condiciones SQL fijas (`estado`, `paciente`) para cargar varios episodios a la vez.
- `TriajeDAO.listar_historial(filtro, valor)`: triajes con síntomas y signos vitales de muchos episodios en 3 consultas fijas.
- `EpisodioDAO.listar_por_estado(estado)` y `listar_por_paciente(id_paciente)`: episodios con su historial completo (4 consultas, no 3 por episodio); `EpisodioDAO.bloquear(id_episodio)`.
- `PacienteDAO.listar_seguros()`, `listar_por_estado_de_episodio(estado)` (id_episodio → Paciente, para mostrar nombres en una cola) y `bloquear(id_paciente)`.
- `SolicitudLimpiezaDAO.buscar_por_id(id_solicitud)`.
- `BaseDAO._bloquear(sql, params)`: `SELECT ... FOR UPDATE`; lanza `RuntimeError` fuera de `transaccion()`.

### Archivos afectados
- `models/triaje.py`, `dao/filtros_episodio.py` (nuevo), `dao/base_dao.py`, `dao/triaje_dao.py`, `dao/episodio_dao.py`, `dao/paciente_dao.py`, `dao/solicitud_limpieza_dao.py`
- `tests/test_triaje.py`, `tests/test_triaje_dao.py`, `tests/test_episodio_dao.py`, `tests/test_paciente_dao.py`, `tests/test_asignacion_dao.py`

### Motivo
Los controladores de la Fase 4 necesitaban: la cola de espera (RN-01: solo con triaje; prioridad por nivel), saber si un paciente ya tiene un episodio abierto, y evitar que dos PCs pisen la misma operación cuando no hay un cambio de estado que sirva de `UPDATE` condicional (p. ej. un segundo triaje mientras otra PC da de alta).

### Impacto
- Pruebas: 883 pasan tras este cambio. SQL nuevo pendiente de verificar en base temporal (se verifica junto con los controladores, ver la entrada de la verificación).

### Decisiones
- **Historial en bloque, no N+1:** cargar 20 episodios de la cola con `buscar_por_id` serían 60 consultas; con `listar_historial` son 3, filtrando por el mismo criterio que la lista de episodios (JOIN con `episodio_emergencia`).
- **Filtros como lista blanca:** el criterio (`estado` o `paciente`) elige un fragmento SQL fijo; el valor viaja siempre como parámetro. Se evitó generar `IN (%s, %s, ...)` dinámico.
- **La prioridad de la cola es del modelo:** `ordenar_por_prioridad` usa `obtener_triaje_actual`; repetir esa regla en SQL (último triaje activo por episodio) la duplicaría.
- **`SELECT ... FOR UPDATE` en una consulta propia y sin JOIN:** bloquear con el `_SELECT` de paciente también bloquearía las filas de `seguro` y `tipo_documento` y pondría en fila a todas las admisiones con el mismo seguro. `FOR UPDATE OF p` lo evitaría, pero MariaDB (usada en desarrollo) no lo admite.
- **El bloqueo va primero en la transacción:** en REPEATABLE READ la foto de la BD se toma en la primera lectura normal; si el bloqueo va antes, las lecturas siguientes ven lo que otra PC confirmó mientras se esperaba.
- **`_bloquear` exige transacción:** con autocommit el bloqueo se libera al instante y no protegería nada; es un error de programación (`RuntimeError`).
- **`SignosVitales` valida el tipo:** antes un texto llegaba a la comparación de rangos y lanzaba `TypeError` (que no es `ValueError` y la vista no capturaría).

### Pendientes
- Verificar el SQL nuevo y los bloqueos en una base temporal.

---

## [2026-10-21] — Fase 4: `auth_controller.py` (sesión y permisos)

### Cambio
- Nueva carpeta `controllers/` con `auth_controller.py`:
  - `Sesion`: el usuario que inició sesión (`id_usuario`, `id_empleado`, `nombre_rol`, `nombres`, `apellidos`, `cargo`). Datos de solo lectura, `puede(permiso)` para las vistas y `cerrar()` para invalidarla.
  - `exigir_permiso(sesion, permiso)`: punto único donde los controladores comprueban un permiso; lanza `UsuarioSinPermisoError` si no hay sesión, si está cerrada o si el rol no tiene el permiso. Devuelve la sesión (para usar su `id_usuario` en la auditoría).
  - `AuthController`: `iniciar_sesion(tipo_documento, num_documento, password)`, `cerrar_sesion()`, `exigir_sesion()`, `sesion` y `autenticado`.
- `models/excepciones.py`: nueva `AutenticacionError` (login fallido, siempre con el mismo mensaje).
- Pruebas: nuevo `tests/test_auth_controller.py` (73), con `UsuarioDAO.autenticar` simulado.

### Archivos afectados
- `controllers/__init__.py` y `controllers/auth_controller.py` (nuevos), `models/excepciones.py`
- `tests/test_auth_controller.py` (nuevo)
- `CLAUDE.md`, `docs/`

### Motivo
Primer paso de la Fase 4: sin sesión no se pueden aplicar los permisos ni saber quién hizo cada operación (auditoría). Los demás controladores dependen de este.

### Impacto
- Pruebas: 848 pasan. Sin cambios en la BD ni en los DAO (no requiere verificación en base temporal).
- Los próximos controladores se crean con la sesión (`TriajeController(sesion)`) y empiezan cada operación con `exigir_permiso(self._sesion, Permiso.X)`.

### Decisiones
- **Sesión inyectada, no global:** cada controlador recibe la `Sesion` al crearse. Una variable global obligaría a las pruebas a modificar estado compartido; así, una prueba crea una sesión de cualquier rol en una línea.
- **Cerrar sesión invalida el objeto:** como los controladores guardan la sesión que recibieron, `cerrar_sesion()` marca esa misma `Sesion` como cerrada; cualquier controlador que aún la tenga deja de poder operar (`exigir_permiso` falla).
- **Un nuevo login cierra antes la sesión anterior:** si el intento falla, no queda nadie conectado (evita que una persona opere con la sesión de otra).
- **Login fallido = excepción con mensaje genérico:** `AutenticacionError` (subclase de `SigtacError`, como el resto de errores que la vista muestra). El mensaje no dice si falló el documento, la clave o el bloqueo, igual que `UsuarioDAO.autenticar`, que devuelve `None` sin revelar la causa.
- **La sesión guarda lo mínimo:** ni clave, ni hash, ni número de documento; el `repr` muestra solo `id_usuario` y rol (puede terminar en un log).
- **Rol desconocido:** el usuario inicia sesión pero no tiene ningún permiso (denegar por defecto, como `tiene_permiso`).
- **Permiso mal escrito:** `exigir_permiso` lo valida antes que la sesión y lanza `ValueError` (error de programación), haya sesión o no.
- **Login y logout no van a la bitácora:** `bitacora_auditoria` registra cambios sobre tablas (`tabla` + `id_registro`); el inicio y el fallo de sesión ya quedan en el log de `UsuarioDAO.autenticar` (sin documentos ni nombres).

### Pendientes
- `paciente_controller.py`, `triaje_controller.py`, `cama_controller.py` y `reporte_controller.py` (en ese orden).
- Antes de `cama_controller`: un método de `EpisodioDAO` para listar la cola de espera. Antes de `reporte_controller`: `dao/reporte_dao.py` con las consultas AVG/COUNT.

---

## [2026-10-21] — Permisos por rol (`models/permisos.py`)

### Cambio
- Nuevo `models/permisos.py`: `Rol` (`StrEnum` con los 5 roles de la tabla `rol`), `Permiso` (`StrEnum` con los módulos del sistema), la matriz `PERMISOS_POR_ROL` (`frozenset` por rol) y `tiene_permiso(rol, permiso)`.
- `models/persona.py`: se quita `tiene_permiso()` de `Empleado` (era abstracto) y de `Enfermero`, `Medico` y `PersonalLimpieza`. `Empleado` deja de ser abstracta y puede representar al personal sin profesión específica (p. ej. el administrador).
- Pruebas: nuevo `tests/test_permisos.py` (52); en `tests/test_persona.py` se reemplazan las pruebas de `tiene_permiso()` por subclase y la de `Empleado` abstracto; `tests/test_estados_vs_bd.py` compara `Rol` con la tabla `rol` de `seed.sql`.
- `CLAUDE.md`: regla de permisos en los controladores.

### Archivos afectados
- `models/permisos.py` (nuevo), `models/persona.py`
- `tests/test_permisos.py` (nuevo), `tests/test_persona.py`, `tests/test_estados_vs_bd.py`
- `CLAUDE.md`, `docs/`

### Motivo
Era el último problema abierto antes de la Fase 4: los permisos existían en dos lugares (tabla `rol` y `tiene_permiso()` en cada subclase) y no coincidían. Los controladores necesitan una sola fuente para aplicar los permisos.

### Impacto
- Pruebas: 775 pasan. Sin cambios en la BD (no requiere verificación en base temporal); los nombres de `Rol` se comparan con `seed.sql`.
- Matriz aplicada (pendiente de validar con el equipo):

  | Permiso | Admin | Jefe de Guardia | Médico | Enfermero de Triaje | Limpieza |
  |---|:-:|:-:|:-:|:-:|:-:|
  | `PACIENTES` (registrar, identificar, fusionar NN) | | ✅ | ✅ | ✅ | |
  | `TRIAJE` (registrar, reclasificar) | | ✅ | ✅ | ✅ | |
  | `GESTION_CAMAS` (asignar, cancelar reserva, alta) | | ✅ | ✅ | | |
  | `VER_CAMAS` (mapa de camas) | ✅ | ✅ | ✅ | ✅ | ✅ |
  | `LIMPIEZA` (confirmar, RN-08) | | | | | ✅ |
  | `REPORTES` | ✅ | ✅ | | | |
  | `ADMINISTRACION` (usuarios y auditoría) | ✅ | | | | |

- Cambios respecto a `tiene_permiso()` anterior: el enfermero ya no gestiona camas (asignar es decisión médica) y desaparece `historias_clinicas`, que no es un módulo del alcance.

### Decisiones
- **El permiso depende del rol, no de la profesión:** el proyecto separó `rol` de `cargo` porque "el cargo laboral y los permisos del software son conceptos distintos"; `tiene_permiso()` en las subclases volvía a atar el permiso a la profesión. Además, el administrador y el jefe de guardia no tenían subclase, y un mismo médico puede tener roles distintos.
- **Matriz en Python, no tabla `rol_permiso`:** los permisos casi no cambian; en Python es un archivo, sin SQL ni pantalla de edición, y se prueba sin MySQL. Si más adelante se pide editarlos en vivo, se migra a una tabla sin tocar los controladores (siguen llamando a `tiene_permiso`).
- **Denegar por defecto:** un rol desconocido no tiene ningún permiso (distingue mayúsculas y tildes, como el nombre en la BD). Un permiso desconocido sí es un error de programación (`ValueError`).
- **El modelo responde, el controlador lanza:** `tiene_permiso` devuelve `True`/`False`; `UsuarioSinPermisoError` la lanza el controlador, como indica `DEVELOPMENT_PLAN.md`.
- **`Empleado` instanciable:** sin `tiene_permiso` abstracto ya no hay razón para impedirlo, y así el personal administrativo tiene una clase. Las subclases conservan lo propio de la profesión (área, especialidad, turno).
- **Matriz duplicada a propósito en la prueba:** `test_permisos.py` escribe la matriz esperada aparte; un cambio accidental en `PERMISOS_POR_ROL` hace fallar la prueba.

### Pendientes
- Validar la matriz con el equipo (o con el documento Word del proyecto, que manda si define permisos).
- Aplicar los permisos en los controladores de la Fase 4.

---

## [2026-10-21] — Fusión de pacientes NN, cancelación de reservas y episodios cerrados

### Cambio
- **Fusión de un paciente NN con uno ya registrado:**
  - `Paciente.fusionar_en(destino)` valida la regla (NN sin identificar y activo; destino identificado y activo; distintos) y anula el NN en memoria.
  - `PacienteDAO.fusionar(nn, destino)`, en una transacción: comprueba que el destino siga activo e identificado, anula el NN (`UPDATE` condicional) y pasa sus episodios al destino. Devuelve cuántos episodios movió.
  - `AccionAuditoria.FUSIONAR`.
  - `Paciente.identificar` rechaza un NN anulado, y `PacienteDAO.identificar` exige además `estado_registro = TRUE`.
- **Cancelar una reserva:**
  - `Cama.cancelar_reserva()` (RESERVADA → DISPONIBLE, sin limpieza).
  - `EpisodioEmergencia.cancelar_asignacion()` (EN ATENCIÓN → EN ESPERA DE CAMA).
  - `AsignacionDAO.anular(id_asignacion)`: baja lógica (`estado_registro = FALSE`), sin fecha de liberación.
- **Episodios cerrados:**
  - `EpisodioEmergencia.cerrado` (ALTA, REFERIDO, FUGADO o anulado); `agregar_triaje` y `agregar_signos_vitales` lanzan `ReglaNegocioError` en un episodio cerrado.
  - El constructor de `EpisodioEmergencia` recibe `triajes` y `signos_vitales` para reconstruirlo desde la BD; `EpisodioDAO.buscar_por_id` los pasa ahí en lugar de usar `agregar_triaje`.
- Pruebas: 41 nuevas o ajustadas en `test_persona.py`, `test_triaje.py`, `test_cama.py`, `test_paciente_dao.py`, `test_episodio_dao.py` y `test_asignacion_dao.py`.

### Archivos afectados
- `models/persona.py`, `models/triaje.py`, `models/cama.py`, `models/auditoria.py`
- `dao/paciente_dao.py`, `dao/episodio_dao.py`, `dao/asignacion_dao.py`
- `tests/test_persona.py`, `tests/test_triaje.py`, `tests/test_cama.py`, `tests/test_paciente_dao.py`, `tests/test_episodio_dao.py`, `tests/test_asignacion_dao.py`, `docs/`

### Motivo
Tres decisiones pendientes que afectan a los flujos que orquestarán los controladores de la Fase 4. Resolverlas antes evita que el controlador tenga que improvisar reglas que pertenecen al modelo.

### Impacto
- Pruebas: 725 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), con los DAO reales en transacciones como las de los futuros controladores. 22 comprobaciones pasaron:
  - Fusión: un NN con un episodio triado resulta ser Rosa (DNI del seed); el episodio, con su triaje, pasa a ella; el NN queda anulado y sin documento (no se borra), sale de la lista de no identificados y la fusión queda auditada; los datos de Rosa no cambian. Fusionarlo otra vez con datos viejos falla; identificar en la BD al NN ya fusionado devuelve `False`; fusionar con un destino anulado en la BD lanza `ReglaNegocioError` y deshace la anulación del NN.
  - Cancelar una reserva: el episodio vuelve a EN ESPERA DE CAMA y la cama a DISPONIBLE sin solicitud de limpieza; la asignación queda anulada sin fecha de liberación; el historial registra RESERVADA y DISPONIBLE; el episodio puede recibir otra cama; anular otra vez falla; una cama OCUPADA no se puede cancelar.
  - Episodio cerrado: un episodio dado de alta se carga con su historial (con la versión anterior, `buscar_por_id` habría fallado al aplicar la nueva regla) y registrar un triaje en él lanza `ReglaNegocioError` sin guardar nada.

### Decisiones
- **Fusionar en lugar de identificar:** si el documento del NN ya pertenece a otro paciente, identificarlo duplicaría la persona. Los episodios pasan al paciente real y el NN se anula (RN-11): queda como rastro, y la auditoría `FUSIONAR` registra a quién se unió. Los datos provisionales del NN (nombres "NN", edad estimada) se descartan.
- **El destino se comprueba dentro de la transacción** con un `SELECT` antes de anular el NN. No se usó `SELECT ... FOR UPDATE`: el margen para que otro usuario anule al destino justo en ese instante es mínimo y el resultado sería un episodio de un paciente anulado, recuperable.
- **Reserva cancelada = asignación anulada, no liberada:** `fecha_liberacion` significa "se usó y se dio de alta"; `estado_registro = FALSE` significa "no llegó a usarse". Los reportes (p. ej. estancia media) podrán distinguirlas. La cama no pasa por limpieza porque nunca se ocupó; una cama OCUPADA debe salir por el alta (RN-07).
- **Reconstruir ≠ registrar:** el historial de un episodio leído de la BD se pasa al constructor, sin aplicar las reglas de un triaje nuevo. Así un episodio cerrado tiene historial y se conserva el estado guardado.
- **Episodio cerrado incluye REFERIDO y FUGADO / ABANDONO** aunque el modelo aún no tenga esas transiciones: existen en el catálogo y un episodio en esos estados tampoco debe recibir triajes.

### Pendientes
- Transiciones a REFERIDO y FUGADO / ABANDONO (el modelo no las tiene).
- Decidir si `Triaje.reclasificar` al mismo nivel sugerido debe rechazarse.
- Permisos por rol antes de los controladores.

---

## [2026-10-21] — `AsignacionDAO` y `SolicitudLimpiezaDAO` (cierre de la Fase 3)

### Cambio
- Nuevo `models/asignacion.py`: `AsignacionCama` y `SolicitudLimpieza`, registros inmutables (`dataclass(frozen=True)`) con `vigente` / `pendiente`. Validan las mismas fechas que `CH_asignacion_fechas` y `CH_limpieza_fechas`, y que una solicitud atendida indique el empleado.
- Nuevo `dao/asignacion_dao.py` (`AsignacionDAO`): `crear`, `buscar_vigente_por_episodio`, `buscar_vigente_por_cama` y `liberar` (`UPDATE` condicional).
- Nuevo `dao/solicitud_limpieza_dao.py` (`SolicitudLimpiezaDAO`): `crear`, `listar_pendientes` (con el código de la cama) y `atender` (`UPDATE` condicional).
- Pruebas: `tests/test_asignacion.py` (10) y `tests/test_asignacion_dao.py` (26), nuevos.

### Archivos afectados
- `models/asignacion.py` (nuevo), `dao/asignacion_dao.py` (nuevo), `dao/solicitud_limpieza_dao.py` (nuevo)
- `tests/test_asignacion.py` (nuevo), `tests/test_asignacion_dao.py` (nuevo), `docs/`

### Motivo
Último DAO de la Fase 3. Con él se cierra el ciclo de una cama (RN-05, RN-07, RN-08) y `cama_controller` (Fase 4) tiene todo lo que necesita para asignar, dar de alta y confirmar la limpieza.

### Impacto
- Pruebas: 684 pasan. **Fase 3 completada.**
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), con funciones que imitan los futuros controladores (cada operación en una transacción con auditoría) y una segunda conexión como "otra PC". 24 comprobaciones pasaron:
  - Seed: TRA-01 tiene la asignación vigente del episodio 1; una cama libre no tiene; la solicitud pendiente es la de UCI-02.
  - Asignar (episodio 2, nivel 2): las camas compatibles son OBS-01, OBS-02 y UCI-01 (TRA-02 no); el episodio pasa a EN ATENCIÓN, UCI-01 a RESERVADA, la asignación queda vigente para ambos y auditada.
  - Conflictos: otra PC que asigna la misma cama con datos viejos recibe `CamaNoDisponibleError` y el cambio de estado de su episodio se deshace; asignar otra cama al mismo episodio con datos viejos lanza `ReglaNegocioError` y la otra cama sigue DISPONIBLE; una segunda asignación vigente de TRA-01 la rechaza el `UNIQUE` de la BD (`RegistroDuplicadoError`, RN-05).
  - Ocupar y dar de alta (RN-07): UCI-01 OCUPADA → EN LIMPIEZA (no DISPONIBLE), episodio en ALTA MÉDICA, asignación liberada con fecha de MySQL y una solicitud de limpieza pendiente. Repetir el alta con datos viejos falla y no crea otra solicitud.
  - Limpieza (RN-08): UCI-01 vuelve a DISPONIBLE, la solicitud queda atendida por el empleado 4 y sale de pendientes; atenderla otra vez lanza `ReglaNegocioError`. Historial de UCI-01: RESERVADA > OCUPADA > EN LIMPIEZA > DISPONIBLE.
  - Una cama liberada se puede volver a asignar: el `UNIQUE` solo cuenta las asignaciones vigentes.

### Decisiones
- **Dos DAO, uno por entidad:** la solicitud de limpieza es otra tabla con su propio ciclo (pendiente → atendida).
- **Cada método es una sola sentencia y no abre transacción propia:** el controlador los combina con `CamaDAO.cambiar_estado` y `EpisodioDAO.cambiar_estado` en `transaccion()`. Ver la tabla de flujos en `PROJECT_CONTEXT.md`.
- **`liberar` y `atender` son `UPDATE` condicionales** (`fecha_liberacion IS NULL`, `fecha_atencion IS NULL`); 0 filas → `ReglaNegocioError` para que se deshaga la transacción. Las fechas las pone MySQL.
- **El `UNIQUE` de `cama_vigente`/`episodio_vigente` es el respaldo de RN-05:** el conflicto normal lo detecta antes el `UPDATE` condicional de la cama; el `UNIQUE` lo detiene incluso si un controlador olvidara cambiar el estado. `crear` deja pasar el `RegistroDuplicadoError` sin traducirlo, porque no se sabe si el duplicado es de la cama o del episodio.
- **Una sola solicitud pendiente por cama** sin restricción en la BD: el `UPDATE` condicional de la cama deja pasar una sola transición a EN LIMPIEZA por ciclo, y la solicitud se crea en esa misma transacción.
- **Las asignaciones no se borran:** se liberan y quedan como historial; un test comprueba que el DAO no tiene métodos para borrar.
- **La compatibilidad cama–triaje no está en estos DAO:** la comprueba el controlador con `cama.es_compatible(nivel)`.

### Pendientes
- Cola de espera (episodios EN ESPERA DE CAMA por nivel y tiempo de espera): en `cama_controller`, Fase 4.
- Cancelar una reserva (cama RESERVADA cuyo paciente nunca llegó): el modelo no tiene esa transición; `cama.dar_alta()` exige OCUPADA. Decidirlo con el controlador.
- Permisos por rol ("Permisos duplicados" en `PROJECT_STATUS.md`) antes de los controladores.

---

## [2026-10-21] — `TriajeDAO` y `EpisodioDAO`

### Cambio
- Nuevo `dao/triaje_dao.py` (`TriajeDAO`): `listar_sintomas`, `registrar(id_episodio, signos, triaje)` (signos vitales + triaje + `triaje_sintoma` en una transacción), `listar_por_episodio` y `listar_signos_por_episodio`.
- Nuevo `dao/episodio_dao.py` (`EpisodioDAO`): `crear`, `buscar_por_id` (con su historial de signos y triajes) y `cambiar_estado` (`UPDATE` condicional).
- `models/triaje.py`:
  - `Triaje.sintomas` (tupla de solo lectura); `agregar_sintoma` rechaza lo que no es `Sintoma` y un síntoma repetido.
  - `EpisodioEmergencia`: propiedades `triajes` y `signos_vitales` (tuplas de solo lectura) y parámetros opcionales `fecha_ingreso`, `fecha_alta` y `activo` para reconstruirlo desde la BD.
  - `obtener_triaje_actual`: con la misma fecha y hora gana el último triaje agregado.
- `dao/base_dao.py`: nuevo `BaseDAO._validar_id`; `AuditoriaDAO` usaba una copia idéntica y ahora usa este.
- Pruebas: `tests/test_triaje_dao.py` (31, nuevo), `tests/test_episodio_dao.py` (26, nuevo), 10 nuevas en `tests/test_triaje.py` y 1 en `tests/test_estados_vs_bd.py` (los niveles 1–5 del seed coinciden con el modelo).
- `CLAUDE.md`: reglas de cambios de estado (el modelo decide, el DAO guarda), fechas puestas por MySQL y `_validar_id`.

### Archivos afectados
- `dao/triaje_dao.py` (nuevo), `dao/episodio_dao.py` (nuevo), `dao/base_dao.py`, `dao/auditoria_dao.py`, `models/triaje.py`
- `tests/test_triaje_dao.py` (nuevo), `tests/test_episodio_dao.py` (nuevo), `tests/test_triaje.py`, `tests/test_estados_vs_bd.py`
- `CLAUDE.md`, `docs/`

### Motivo
Siguiente paso de la Fase 3: el triaje es el centro del sistema y `triaje_controller` (Fase 4) lo necesita. Con `transaccion()` ya decidida, las varias escrituras de un triaje se pueden guardar de forma atómica.

### Impacto
- Pruebas: 648 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), recorriendo el flujo que hará `triaje_controller` (Manchester sugiere, la enfermera confirma, todo en una transacción con auditoría) y con una segunda conexión como "otra PC". 22 comprobaciones pasaron:
  - Catálogo: 10 síntomas ordenados, con peso como `float`. El episodio 2 del seed se reconstruye con su triaje reclasificado (sugerido 3, final 2, con justificación y síntoma); el episodio 1 conserva su estado EN ATENCIÓN; uno inexistente devuelve `None`.
  - Llegada y primer triaje (paciente extranjera): el episodio nace EN ESPERA DE TRIAJE con fecha de MySQL; se guardan signos, triaje (nivel final, sugerido, justificación, enfermera), 2 síntomas y la auditoría; el episodio pasa a EN ESPERA DE CAMA (RN-01).
  - Reevaluación (RN-09): un triaje nuevo, el anterior intacto; el triaje actual es la reevaluación y el estado no cambia.
  - Dos enfermeros triando el mismo episodio: el segundo recibe `ReglaNegocioError` y su triaje, signos y auditoría se deshacen.
  - Un síntoma inexistente (FK, 1452) deshace todo el triaje y el cambio de estado.
  - Asignar cama y dar de alta guardan los estados; la fecha de alta la pone MySQL (≥ ingreso). Un episodio con datos desactualizados lanza `ReglaNegocioError`.
- **No ejercitado contra MySQL:** guardar un triaje *nuevo* con nivel final distinto del sugerido. En la verificación, Manchester sugirió 1 y la "reclasificación" también fue a 1. Lo cubren las pruebas unitarias (parámetros del `INSERT`), la lectura del triaje reclasificado del seed y la verificación del `CHECK CH_triaje_rn10` del 2026-10-12.

### Decisiones
- **Dos DAO, uno por entidad:** el plan solo nombraba `triaje_dao.py`, pero el episodio es otra entidad (`CLAUDE.md`: un `*_dao.py` por entidad). `EpisodioDAO.buscar_por_id` usa `TriajeDAO` para cargar el historial, así el modelo puede aplicar RN-01 sobre datos reales.
- **`TriajeDAO` solo inserta y lee (RN-09):** una reevaluación es un triaje nuevo; un test comprueba que no hay métodos para modificar ni borrar.
- **`registrar` no cambia el estado del episodio:** la transición la decide el modelo (`agregar_triaje`) y la guarda `EpisodioDAO.cambiar_estado`, en la misma transacción del controlador. Si dos enfermeros trían a la vez, el `UPDATE` condicional del segundo encuentra 0 filas y deshace todo su triaje.
- **`EpisodioDAO.cambiar_estado` no abre transacción propia:** es una sola sentencia; dentro de la del controlador, su excepción deshace los pasos anteriores.
- **0 filas → `ReglaNegocioError`** (no `False`), por la misma razón que en `CamaDAO.cambiar_estado`.
- **Las fechas las pone MySQL** (triaje, signos, ingreso y alta): un solo reloj para todas las PCs, y `CH_episodio_fechas` se cumple aunque el reloj de una PC esté desfasado. La fecha de alta se pone al pasar a ALTA MÉDICA (`IF(%s, NOW(), fecha_alta)`).
- **Niveles por número:** `id_nivel` e `id_nivel_sugerido` se obtienen con subconsultas sobre `nivel_triaje.numero`, no por id. Un `id_nivel_sugerido` `NULL` se lee como "sin sugerencia" (sugerido = final).
- **Reconstrucción con los métodos del modelo:** `_a_triaje` usa `reclasificar()` y `anular()`, así las reglas (RN-10, RN-11) se aplican también a lo que llega de la BD.
- **Desempate de `obtener_triaje_actual`:** la BD guarda segundos; dos triajes en el mismo segundo devolvían el más antiguo. Ahora gana el último agregado, que en un historial leído por `fecha_hora, id_triaje` es el más reciente.
- **Síntoma repetido:** lo rechaza el modelo (`agregar_sintoma`) antes de llegar al `INSERT`, que fallaría por la clave primaria de `triaje_sintoma`.
- **Sin datos clínicos en los logs:** ni la justificación ni el motivo de consulta; solo ids, niveles y estados.

### Pendientes
- Decidir si se puede registrar un triaje en un episodio ya dado de alta, referido o fugado (hoy el modelo no lo impide).
- `Triaje.reclasificar` acepta "reclasificar" al mismo nivel sugerido y guarda la justificación aunque `es_reclasificacion` sea `False`. No viola RN-10, pero conviene decidir si debe rechazarse.
- Cola de espera (episodios EN ESPERA DE CAMA ordenados por nivel y tiempo): con `asignacion_dao.py` / `cama_controller`.

---

## [2026-10-21] — `CamaDAO.cambiar_estado` con historial

### Cambio
- `dao/cama_dao.py`: nuevo `CamaDAO.cambiar_estado(cama, estado_anterior)`. Dentro de `transaccion()` ejecuta un `UPDATE` condicional (solo cambia la cama si en la BD sigue en `estado_anterior`, está activa y existe) y un `INSERT` en `historial_estado_cama`.
- `models/excepciones.py`: el docstring de `CamaNoDisponibleError` cubre cualquier cambio de estado en conflicto, no solo la asignación.
- `tests/test_cama_dao.py`: 22 pruebas nuevas (47 en total). La clase `BD` simulada también reemplaza `ConexionBD` en `dao.transaccion`.

### Archivos afectados
- `dao/cama_dao.py`, `models/excepciones.py`, `tests/test_cama_dao.py`, `docs/`

### Motivo
Primer uso real de `transaccion()`. Cambiar el estado de una cama son dos escrituras: sin transacción, un fallo en el historial dejaría un cambio sin registrar. Lo necesitarán la asignación de camas, el alta (RN-07) y la confirmación de limpieza (RN-08).

### Impacto
- Pruebas: 580 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), con `CamaDAO`, `AuditoriaDAO` y `transaccion()` reales y una segunda conexión que hace de "otra PC". 19 comprobaciones pasaron:
  - Ciclo completo de TRA-02: DISPONIBLE → RESERVADA → OCUPADA → EN LIMPIEZA → DISPONIBLE; cada paso queda guardado y el historial tiene los 4 cambios en orden.
  - Conflicto entre dos PCs: esta PC carga OBS-01 (DISPONIBLE), la otra la ocupa, y esta intenta reservarla con datos desactualizados → `CamaNoDisponibleError`; la cama conserva el estado de la otra PC, no se escribe historial y la transacción queda cerrada.
  - Una cama inexistente y una dada de baja (RN-11) lanzan `CamaNoDisponibleError` y no cambian.
  - Dentro de la transacción de un controlador: si falla un paso posterior se deshacen estado, historial y auditoría; si todo sale bien, la otra PC no ve nada hasta el COMMIT y después ve los tres.

### Decisiones
- **El modelo decide, el DAO guarda:** las transiciones válidas siguen siendo de la máquina de estados de `Cama` (`reservar`, `dar_alta`, `liberar_limpieza`...). El DAO no repite esas reglas; solo recibe la cama ya cambiada y el estado del que partió.
- **`UPDATE` condicional para la concurrencia:** el objeto en memoria puede estar desactualizado (el modelo permitió reservar porque creía que la cama estaba DISPONIBLE). La condición `id_estado_cama = <estado_anterior>` hace que la BD tenga la última palabra.
- **0 filas → excepción, no `False`:** dentro de la transacción de un controlador, la excepción deshace toda la operación; un `False` que nadie revise dejaría confirmar el resto. Por la misma razón, una cama inexistente o dada de baja también lanza `CamaNoDisponibleError` (el `UPDATE` no distingue esos casos de un conflicto).
- **No se registra un "cambio" al mismo estado:** `cambiar_estado` lanza `ValueError` si el estado no cambió (p. ej. `fuera_de_servicio()` sobre una cama que ya lo estaba).
- **Los ids de estado se obtienen del catálogo por nombre** con subconsultas sobre `estado_cama` (el valor del Enum), igual que `CamaDAO.listar_disponibles`.
- **La auditoría la registra el controlador**, dentro de la misma transacción; el DAO no audita por su cuenta.

### Pendientes
- Usar `cambiar_estado` desde `asignacion_dao.py` y desde los controladores de la Fase 4.

---

## [2026-10-21] — Transacciones explícitas (`dao/transaccion.py`)

### Cambio
- Nuevo `dao/transaccion.py`: gestor de contexto `with transaccion():` que agrupa varias escrituras en una unidad (patrón *Unit of Work*). Hace COMMIT si el bloque termina bien y ROLLBACK ante cualquier excepción, que luego se vuelve a lanzar. Un bloque anidado se une a la transacción abierta.
- `dao/db_connection.py`: `ConexionBD` conoce el estado de transacción (`en_transaccion`, `iniciar_transaccion`, `terminar_transaccion`). Durante una transacción, `obtener_conexion` **no se reconecta**: lanza `ConexionBDError`.
- Nuevo `tests/test_transaccion.py` (16 pruebas) y 11 pruebas nuevas en `tests/test_db_connection.py`.
- `CLAUDE.md`: reglas de uso de `transaccion()` y de concurrencia con `UPDATE` condicional.

### Archivos afectados
- `dao/transaccion.py` (nuevo), `dao/db_connection.py`, `tests/test_transaccion.py` (nuevo), `tests/test_db_connection.py`, `CLAUDE.md`, `docs/`

### Motivo
Era el problema abierto que bloqueaba `cama_dao.cambiar_estado`, `triaje_dao.py` y `asignacion_dao.py`. Con `autocommit=True`, si falla un paso intermedio de una operación (p. ej. el tercer paso de asignar una cama), los anteriores ya quedaron guardados y la BD queda inconsistente.

### Impacto
- Pruebas: 558 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), usando `ConexionBD`, `BaseDAO` y `AuditoriaDAO` reales. 21 comprobaciones pasaron:
  - Antes del COMMIT otra conexión no ve los cambios; después ve el `UPDATE` y el `INSERT`.
  - Un error de MySQL en el tercer paso (1062 por `UNIQUE cama_vigente`, RN-05) y una excepción de negocio deshacen los pasos anteriores.
  - Un bloque anidado no confirma por su cuenta; un error en él deshace también lo del externo.
  - `AuditoriaDAO.registrar` contra MySQL real (JSON con tildes intacto). Si la operación falla, su auditoría se deshace; si la auditoría falla (FK, 1452), la operación se deshace.
  - Con la conexión cortada a mitad (`KILL`), el paso siguiente lanza `ConexionBDError` sin reconectar, MySQL deshace el paso anterior y la transacción queda cerrada; fuera de una transacción sí se reconecta.
  - Una sentencia suelta fuera de transacciones se guarda al instante (autocommit sigue activo).
- **Bug encontrado por la verificación real** (las pruebas con `MagicMock` no podían verlo): con la extensión C del conector, `rollback()` sobre una conexión cortada lanza `_mysql_connector.MySQLInterfaceError`, que **no hereda** de `mysql.connector.Error`; escapaba de `_deshacer` y tapaba el `ConexionBDError` original. `commit()` tiene el mismo comportamiento. Corregido: `terminar_transaccion` comprueba `is_connected()` antes; si la conexión se perdió, no llama a `rollback()` (MySQL ya deshizo lo pendiente) y confirmar lanza `ConexionBDError`. Tres pruebas reproducen el caso.

### Decisiones
- **Gestor de contexto en lugar de `autocommit=False` global:** con `autocommit=False` un `commit()` olvidado pierde datos y, en REPEATABLE READ, una conexión de larga vida lee una foto vieja (el mapa de camas no vería los cambios de otras PCs). `START TRANSACTION` suspende el autocommit solo mientras dura el bloque.
- **No procedimientos almacenados:** sacarían reglas de negocio de Python y serían difíciles de probar con pytest.
- **El controlador marca la unidad, el DAO hace COMMIT/ROLLBACK:** el controlador no escribe SQL; solo dice qué pasos van juntos.
- **Bloques anidados se unen al externo:** un método DAO de varios pasos (`cambiar_estado` + historial) usa `transaccion()` y sirve solo o dentro de la transacción de un controlador. Consecuencia: dentro de una transacción, las excepciones deben llegar al `with` más externo; si se capturan a mitad, lo demás se confirmaría.
- **`try/finally` con una bandera `exito`** en lugar de `except Exception`: deshace ante cualquier error sin capturarlo.
- **Sin reconexión durante una transacción:** los pasos siguientes irían a una conexión nueva, fuera de la transacción, con autocommit, y quedarían guardados aunque la operación estuviera a medias.
- **La auditoría va dentro de la transacción** (pendiente de `AuditoriaDAO`): nunca queda un cambio sensible sin auditar ni una auditoría de algo que no ocurrió.
- **Concurrencia entre PCs con `UPDATE` condicional** (`WHERE ... AND estado = <esperado>` y comprobar `rowcount`), como en `PacienteDAO.identificar`, respaldado por los `UNIQUE` de la BD. Más simple que `SELECT ... FOR UPDATE` y sin bloqueos en espera.
- La conexión es compartida: una sola transacción a la vez (la app de escritorio es de un hilo).

### Pendientes
- Limitación conocida: si la conexión se corta justo entre `is_connected()` y `commit()`/`rollback()`, el error de la extensión C escaparía igual. Es muy improbable.
- Usar `transaccion()` en `cama_dao.cambiar_estado`, `triaje_dao.py` y `asignacion_dao.py`.

---

## [2026-10-21] — `AuditoriaDAO` y `sigtac_db` recreada

### Cambio
- Nuevo `dao/auditoria_dao.py` (`AuditoriaDAO`, hereda de `BaseDAO`): `registrar(id_usuario, tabla, accion, id_registro, detalles=None)` y `listar_por_registro(tabla, id_registro)`.
- Nuevo `models/auditoria.py`: `AccionAuditoria` (`INSERT`, `UPDATE`, `ANULAR`, `IDENTIFICAR`).
- Nuevo `tests/test_auditoria_dao.py` (32 pruebas) y 2 pruebas en `tests/test_estados_vs_bd.py`: la lista de tablas auditables coincide con `schema.sql` y las acciones del seed existen en el Enum.
- El usuario recreó `sigtac_db` con `schema.sql` y `seed.sql` actuales.

### Archivos afectados
- `dao/auditoria_dao.py` (nuevo), `models/auditoria.py` (nuevo), `tests/test_auditoria_dao.py` (nuevo), `tests/test_estados_vs_bd.py`, `CLAUDE.md`, `docs/`

### Motivo
Siguiente DAO del plan. Es de una sola tabla y no necesita transacciones, y los controladores de la Fase 4 lo usarán después de cada operación sensible.

### Impacto
- Pruebas: 531 pasan.
- `listar_por_registro` se comprobó en solo lectura contra `sigtac_db` (usuario `sigtac_app`): devuelve las 2 filas del seed con `AccionAuditoria`, `fecha_hora` como `datetime` y `detalles` en `None`, y una lista vacía para un registro sin auditoría. `registrar` no se probó contra MySQL real para no dejar filas de prueba en `sigtac_db`: la bitácora no admite borrado.

### Decisiones
- **Solo inserción:** el DAO no tiene métodos para modificar ni borrar; un test lo comprueba. Una auditoría editable no sirve como evidencia.
- **`accion` con Enum:** evita que la misma acción quede escrita de varias formas y no se pueda agrupar en reportes. `AccionAuditoria` está en `models/` porque la usarán los controladores.
- **Lista blanca de tablas (`TABLAS_AUDITABLES`):** el nombre de la tabla viaja como parámetro, así que no es un riesgo de inyección; la lista evita registros que apunten a tablas inexistentes. Incluye todas las tablas del esquema salvo la propia bitácora.
- **`detalles` se convierte a JSON en el DAO** (`ensure_ascii=False`, para que las tildes queden legibles). Debe contener solo ids y valores no sensibles, nunca documentos, nombres ni claves. El log solo registra id, tabla y acción, nunca los detalles.
- **La fecha la pone MySQL** (`DEFAULT CURRENT_TIMESTAMP`): todos los registros usan el mismo reloj, el del servidor.
- **Un fallo al auditar lanza `PersistenciaError`**, como el resto de los DAO. Si la operación auditada debe deshacerse en ese caso se decidirá junto con las transacciones.
- `id_usuario` es obligatorio en la tabla, así que los intentos de login de usuarios inexistentes no se auditan (quedan cubiertos por el bloqueo de intentos y los logs).

### Pendientes
- Llamar a `AuditoriaDAO.registrar` desde los controladores (Fase 4).
- Opcional: quitar a `sigtac_app` el permiso `UPDATE` sobre `bitacora_auditoria`.

---

## [2026-10-21] — Pacientes sin identificar (NN)

### Cambio
- `paciente.id_tipo_documento` y `paciente.num_documento` admiten `NULL` (paciente sin identificar). Nuevo `CHECK CH_paciente_documento`: los dos son `NULL` o los dos tienen valor. La FK a `tipo_documento` pasa a `ON UPDATE RESTRICT`. `empleado` no cambia: su documento sigue siendo obligatorio.
- `Persona` admite `documento=None` solo en las subclases que lo permiten (`_ADMITE_SIN_DOCUMENTO`, `True` solo en `Paciente`).
- `Paciente`: propiedad `identificado`, fábrica `Paciente.no_identificado(sexo, edad_estimada, id_seguro)` y método `identificar(documento, nombres, apellidos, fecha_nac)`.
- `PacienteDAO`: `LEFT JOIN tipo_documento`, `crear` acepta pacientes sin documento, nuevos `listar_no_identificados()` e `identificar(paciente)`.
- `seed.sql`: un paciente NN.

### Archivos afectados
- `db_scripts/schema.sql`, `db_scripts/seed.sql`, `models/persona.py`, `dao/paciente_dao.py`
- `tests/test_persona.py`, `tests/test_paciente_dao.py`, `tests/test_estados_vs_bd.py`, `docs/`

### Motivo
A emergencia llegan pacientes inconscientes o sin papeles que hay que atender (y registrar su triaje) antes de saber quiénes son. Hasta ahora el registro exigía documento, nombres y fecha de nacimiento reales.

### Impacto
- Pruebas: 497 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), junto con el cambio de `tipo_documento`. Se cargaron `schema.sql` y `seed.sql` y se usaron los DAO reales. 33 comprobaciones pasaron:
  - Esquema: 22 tablas; los códigos de `tipo_documento` coinciden con `TipoDocumento`; `codigo` distingue mayúsculas (`'dni'` no encuentra `'DNI'`); el seed tiene 5 pacientes, 1 de ellos NN.
  - Restricciones: tipo + número repetido → 1062; el mismo número con otro tipo se acepta; tipo sin número o número sin tipo → 3819 (`CH_paciente_documento`); varios NN a la vez se aceptan; tipo inexistente → 1452; empleado sin documento → 1048.
  - `PacienteDAO`: busca por DNI y por CE; el mismo número con otro tipo no encuentra a nadie; `buscar_por_id` devuelve un NN (confirma el `LEFT JOIN`); `crear` guarda el pasaporte normalizado y un duplicado lanza `RegistroDuplicadoError`; un NN se guarda con tipo y número `NULL` y conserva su edad estimada; `listar_no_identificados` lo incluye; `actualizar` no le pone documento.
  - `identificar`: con el documento de otro paciente → `RegistroDuplicadoError` y el NN queda igual; con un documento nuevo → `True`, se encuentra por documento con el mismo id y sale de la lista de NN; un segundo `identificar` con un objeto desactualizado → `False` y se conserva el primer documento.
  - `UsuarioDAO.autenticar`: con DNI encuentra al empleado (suma un intento fallido con clave incorrecta); con el mismo número y tipo CE no lo encuentra.
- El futuro controlador de pacientes debe ofrecer "registrar NN" y, más adelante, "identificar".

### Decisiones
- **Documento `NULL`, no un tipo "SIN DOCUMENTO":** un tipo falso obligaría a inventar un número único. Un `UNIQUE` de MySQL admite varios `NULL`, así que puede haber varios NN a la vez, y el `CHECK` impide un tipo sin número o al revés.
- **Fecha de nacimiento estimada en lugar de `NULL`:** la edad aproximada es útil en la atención y así `calcular_edad()` sigue funcionando para todos. Se guarda el 1 de enero de (año actual − edad), con lo que la edad calculada coincide con la estimada todo el año. No se añadió una columna "fecha estimada": mientras el paciente no esté identificado, sus datos se consideran provisionales.
- **Nombres "NN":** convención de los hospitales para pacientes sin nombre. La constante vive en `Paciente.NOMBRE_NO_IDENTIFICADO` y un test comprueba que el seed la use.
- **Identificar es una operación aparte y se hace una sola vez:** `actualizar` sigue sin tocar el documento. `Paciente.identificar` lanza `ReglaNegocioError` si ya está identificado y valida todo antes de modificar. En la BD, `WHERE num_documento IS NULL` impide sobrescribir el documento aunque dos usuarios identifiquen al mismo paciente a la vez.
- **Atributo de clase `_ADMITE_SIN_DOCUMENTO` en lugar de repetir la validación en `Empleado`:** por defecto toda persona exige documento; solo `Paciente` lo relaja.
- No se creó una subclase `PacienteNoIdentificado`: al identificarlo, el objeto tendría que cambiar de clase.

### Pendientes
- Si el documento del NN ya pertenece a otro paciente, `identificar` lanza `RegistroDuplicadoError`. Unir los dos registros queda para la Fase 4.
- Recrear `sigtac_db` con los scripts nuevos; actualizar `diagrama.png`.

---

## [2026-10-21] — Documento de identidad para personas extranjeras

### Cambio
- Nueva tabla de catálogo `tipo_documento` (DNI, CE, PAS, CPP). En `paciente` y `empleado`, la columna `dni` se reemplaza por `id_tipo_documento` (FK) + `num_documento`, con `UNIQUE (id_tipo_documento, num_documento)`. El esquema pasa a 22 tablas.
- Nuevo `models/documento.py`: `TipoDocumento` (`StrEnum`) y `DocumentoIdentidad` (objeto valor inmutable: tipo + número, con `__eq__`/`__hash__`).
- `Persona` y sus subclases reciben un `DocumentoIdentidad` en lugar de `dni: str` (propiedad `documento`). Se elimina `es_dni_valido`.
- `PacienteDAO.buscar_por_dni(dni)` pasa a `buscar_por_documento(documento)`; `crear` obtiene `id_tipo_documento` con una subconsulta por código.
- `UsuarioDAO.autenticar(tipo_documento, num_documento, password_plano)`: el login pide tipo y número; la sesión devuelve `tipo_documento` y `num_documento` en lugar de `dni`.
- `seed.sql`: catálogo de tipos y una paciente extranjera con carné de extranjería.

### Archivos afectados
- `db_scripts/schema.sql`, `db_scripts/seed.sql`, `models/documento.py` (nuevo), `models/persona.py`, `dao/paciente_dao.py`, `dao/usuario_dao.py`, comentarios en `dao/base_dao.py`, `models/excepciones.py` y `utils/security.py`
- `tests/test_documento.py` (nuevo, 53 pruebas), `tests/test_persona.py`, `tests/test_paciente_dao.py`, `tests/test_usuario_dao.py`, `tests/test_estados_vs_bd.py`
- `CLAUDE.md`, `docs/`

### Motivo
El sistema solo aceptaba DNI peruano (8 dígitos): un paciente o un empleado extranjero no se podía registrar (problema abierto 2 de `PROJECT_STATUS.md`). Un hospital debe atender a cualquier persona sin importar su nacionalidad.

### Impacto
- Pruebas: 466 pasan.
- Verificado en MySQL 8.0.46 junto con el cambio de pacientes NN (ver la entrada siguiente). `sigtac_db` necesita volver a crearse con `schema.sql` y `seed.sql` (borra los datos de desarrollo).
- Quien llame a `autenticar` o a `buscar_por_documento` (futuros `auth_controller` y vistas) debe enviar el tipo de documento: el formulario de login necesita un selector de tipo.

### Decisiones
- **Tipo + número juntos identifican a la persona:** el mismo número puede ser un DNI de una persona y el pasaporte de otra. Por eso el `UNIQUE` es compuesto.
- **Catálogo en lugar de `CHECK`:** añadir un tipo es un `INSERT`, no un cambio de esquema; sigue el patrón de `seguro` y `estado_cama`. Un test compara `TipoDocumento` con `seed.sql`.
- **El formato vive en un solo lugar (`DocumentoIdentidad`):** el DNI exige exactamente 8 dígitos; los documentos extranjeros aceptan de 6 a 12 letras o dígitos, porque su formato varía según el país y la fecha de emisión. No se verificó el formato oficial exacto de CE, pasaporte ni CPP.
- **Normalización en el objeto valor:** el número se guarda sin espacios en los extremos y en mayúsculas. Antes `Persona` rechazaba un DNI con espacios y `UsuarioDAO` lo limpiaba; ahora lo hace `DocumentoIdentidad` para todos.
- **Objeto en lugar de dos atributos sueltos:** `Persona` recibe un `DocumentoIdentidad` ya validado, así el tipo y el número no pueden quedar desincronizados. `__repr__` oculta el número para que no termine en un log.
- El documento sigue sin poder actualizarse (`PacienteDAO.actualizar`), igual que antes el DNI.

### Pendientes
- Recrear `sigtac_db` con los scripts nuevos.
- Actualizar `db_scripts/diagrama.png`.
- Pacientes sin identificar (NN): requieren otra decisión (sin documento, nombre ni fecha de nacimiento conocidos).

---

## [2026-10-13] — `CamaDAO` (lectura) y reglas nuevas en `CLAUDE.md`

### Cambio
- Nuevo `dao/cama_dao.py` (`CamaDAO`, hereda de `BaseDAO`): `buscar_por_id`, `buscar_por_codigo`, `listar_activas` y `listar_disponibles`. Una fábrica (`CLASES_POR_TIPO`) convierte cada fila en su subclase de `Cama`.
- Nuevo `tests/test_cama_dao.py` (25 pruebas) y una prueba en `tests/test_estados_vs_bd.py` que compara la fábrica con los tipos de `seed.sql`.
- `CLAUDE.md`: no añadir `Co-Authored-By` de Claude; mensajes con cuerpo con `git commit -F` en PowerShell; no reescribir commits ya subidos; método `_a_<entidad>` en cada DAO; `FOUND_ROWS`; no escribir operaciones multi-paso antes de decidir las transacciones; la verificación en base temporal requiere cuenta de administrador.

### Archivos afectados
- `dao/cama_dao.py` (nuevo), `tests/test_cama_dao.py` (nuevo), `tests/test_estados_vs_bd.py`, `CLAUDE.md`, `docs/`

### Motivo
Siguiente DAO del plan. Las reglas de `CLAUDE.md` recogen lo aprendido el 2026-10-12/13: un commit con varios `-m` quedó con el título roto en PowerShell y tuvo que reescribirse, y el usuario pidió que Claude no figure como coautor.

### Impacto
- Pruebas: 419 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada). 11 comprobaciones pasaron:
  - La fábrica crea la subclase correcta con los nombres reales de `tipo_cama`, y todos los estados de la BD existen en `EstadoCama`.
  - `listar_activas` devuelve las 8 camas del seed; `listar_disponibles`, solo las 4 `DISPONIBLE`, ordenadas por área y código.
  - Compatibilidad por polimorfismo sobre datos reales: nivel 1 → Trauma Shock y UCI; nivel 4 → solo Observación.
  - Búsqueda por código e id con JOIN a área y estado; inexistente → `None`.
  - Una cama dada de baja no aparece en búsquedas, en el mapa ni entre las disponibles.

### Decisiones
- **Solo lectura por ahora.** Cambiar el estado de una cama son dos escrituras (`UPDATE cama` + `INSERT historial_estado_cama`); sin transacción, un fallo en la segunda dejaría un cambio sin historial. Se implementará después de decidir las transacciones (problema 4).
- **La fábrica usa el nombre del tipo, no el id:** `nombre_tipo_cama` es `UNIQUE` y los ids dependen del orden de inserción. Un tipo sin clase lanza `ValueError`, y una prueba asegura que la fábrica y `seed.sql` coincidan.
- **La compatibilidad no se filtra en el DAO ni en SQL:** `listar_disponibles` filtra solo por estado; el controlador aplica `cama.es_compatible(nivel)`. Así la regla tiene un solo dueño (el modelo) y el DAO no contiene reglas de negocio.
- **Solo camas activas:** el modelo `Cama` no tiene `activo`, así que una cama dada de baja (`estado_registro = FALSE`) no se devuelve en ninguna consulta.
- El estado se filtra con un parámetro tomado del Enum (`EstadoCama.DISPONIBLE.value`), no escrito en el SQL.
- Las partes fijas del SQL (`_SELECT`, `_ORDEN`) se concatenan entre sí; los valores siempre van como parámetros.
- `listar_activas` (todas las camas en cualquier estado) se añade para el futuro mapa de camas.

### Pendientes
- `cambiar_estado` + `historial_estado_cama`, tras la decisión sobre transacciones.

---

## [2026-10-12] — `PacienteDAO` y `FOUND_ROWS` en la conexión

### Cambio
- Nuevo `dao/paciente_dao.py` (`PacienteDAO`, hereda de `BaseDAO`): `buscar_por_id`, `buscar_por_dni`, `crear`, `actualizar` y `anular`.
- `dao/db_connection.py`: la conexión se abre con `ClientFlag.FOUND_ROWS`.
- Nuevo `tests/test_paciente_dao.py` (28 pruebas) y 1 prueba nueva en `tests/test_db_connection.py`.

### Archivos afectados
- `dao/paciente_dao.py` (nuevo), `dao/db_connection.py`, `tests/test_paciente_dao.py` (nuevo), `tests/test_db_connection.py`, `docs/`

### Motivo
Siguiente paso de la Fase 3. `FOUND_ROWS` es necesario para `actualizar`: sin él, MySQL devuelve en `rowcount` las filas *modificadas*, y guardar un paciente sin cambios daría 0, que el DAO confundiría con "no existe". Con `FOUND_ROWS`, `rowcount` cuenta las filas *encontradas*.

### Impacto
- Pruebas: 393 pasan.
- Verificado en MySQL 8.0.46 con una base temporal (`sigtac_scratch_tmp`, ya eliminada), creada con una cuenta de administrador porque `sigtac_app` no puede crear bases. 15 comprobaciones pasaron:
  - Búsqueda por DNI e id, JOIN a `seguro`, `fecha_nac` como `date`, DNI inexistente → `None`.
  - `crear` devuelve el id; DNI duplicado → `RegistroDuplicadoError` (1062); seguro inexistente → `PersistenciaError` (1452), no duplicado.
  - `actualizar` sin cambios devuelve `True` (confirma `FOUND_ROWS`); con cambios los guarda; id inexistente → `False`.
  - `anular`: el paciente sigue existiendo con `activo=False`; anular dos veces devuelve `True`; id inexistente → `False`.
  - Los mensajes de error registrados solo muestran el `errno`, sin el DNI.

### Decisiones
- **El DNI no se actualiza:** `actualizar` solo modifica nombres, apellidos, fecha de nacimiento, sexo y seguro. El DNI identifica a la persona; un DNI mal registrado se corrige anulando el registro y creando uno nuevo.
- **`buscar_por_dni` incluye a los anulados:** el `UNIQUE` del DNI también los cubre, así que el controlador debe saber que el paciente existe (para reactivarlo) en lugar de intentar un `INSERT` que fallaría.
- `actualizar` y `anular` devuelven `False` si el id no existe; `anular` es idempotente (anular dos veces devuelve `True`).
- `crear` rechaza un paciente que ya tiene id o que está anulado (`ValueError`), sin consultar la BD.
- El DAO no repite validaciones: si una fila tiene datos inválidos, el constructor de `Paciente` lanza `ValueError`.
- Los logs solo registran `id_paciente`, nunca DNI ni nombres.

### Pendientes
- Reactivar un paciente anulado (`estado_registro = TRUE`): se añadirá cuando el controlador lo necesite.
- Búsqueda por nombre o listado: se añadirá cuando la vista lo necesite.

---

## [2026-10-12] — `BaseDAO` y política de errores de la capa DAO

### Cambio
- Nuevo `dao/base_dao.py`: clase `BaseDAO` con `_consultar_uno`, `_consultar_varios`, `_insertar` (devuelve el id generado) y `_ejecutar` (devuelve las filas afectadas). Pide la conexión, abre y cierra el cursor y traduce los errores de MySQL.
- `models/excepciones.py`: nuevas `PersistenciaError` y `RegistroDuplicadoError`. `ConexionBDError` pasa a derivar de `PersistenciaError`.
- `dao/usuario_dao.py`: `UsuarioDAO` hereda de `BaseDAO`; ya no maneja cursores. Su comportamiento no cambia (las 33 pruebas pasan sin modificar sus aserciones).
- Nuevo `tests/test_base_dao.py` (23 pruebas).

### Archivos afectados
- `dao/base_dao.py` (nuevo), `dao/usuario_dao.py`, `models/excepciones.py`, `tests/test_base_dao.py` (nuevo), `tests/test_usuario_dao.py`, `CLAUDE.md`, `docs/`

### Motivo
Cada DAO repetía unas 15 líneas (conexión, cursor, `try/except`, cierre en `finally`). Con cinco DAO más, un error en una copia sería difícil de encontrar. Además, devolver `None` ante cualquier fallo, como hace el login, no sirve en el resto de DAO: el controlador no podría distinguir "el paciente no existe" de "MySQL está caído".

### Impacto
- Política de errores de los DAO (salvo `UsuarioDAO.autenticar`): `None` o lista vacía significan "no encontrado"; los fallos lanzan `PersistenciaError` o una subclase (`ConexionBDError`, `RegistroDuplicadoError` para el error 1062).
- Pruebas: 364 pasan. Las pruebas de `usuario_dao` reemplazan `ConexionBD` en `base_dao`, que es donde ahora se usa.

### Decisiones
- **Jerarquía:** `SigtacError → PersistenciaError → {ConexionBDError, RegistroDuplicadoError}`. Un controlador puede capturar todos los fallos de BD con una sola cláusula y, si quiere, tratar el duplicado aparte.
- **Sin `commit()`/`rollback()` en `BaseDAO`:** con `autocommit=True` no tienen efecto, y dentro de la futura transacción de asignar cama un `commit` por sentencia la rompería. Las transacciones se decidirán aparte (problema 4 de `PROJECT_STATUS.md`).
- **Los logs y mensajes no incluyen el texto de MySQL**, solo el código (`errno`): MySQL arma la consulta en el cliente y sus mensajes pueden traer los valores enviados (por ejemplo `Duplicate entry '12345678'`). El error original queda encadenado (`raise ... from e`) para depurar.
- Solo se traducen errores de `mysql.connector`; un error de programación (p. ej. `KeyError`) se propaga tal cual para no ocultarlo.
- `params` debe ser una tupla (`TypeError` si no): evita el error clásico de pasar `(valor)` en lugar de `(valor,)`.
- `BaseDAO` no es abstracta: no tiene métodos que las subclases deban implementar, solo métodos que heredan.

---

## [2026-10-12] — Script para crear el usuario de BD de la aplicación

### Cambio
- Nuevo `db_scripts/crear_usuario_app.sql`: crea `sigtac_app@localhost` con `SELECT, INSERT, UPDATE` sobre `sigtac_db.*` y muestra sus permisos. La clave va como marcador (`<una_clave_segura>`).
- `README.md` remite al script.

### Archivos afectados
- `db_scripts/crear_usuario_app.sql` (nuevo), `README.md`, `docs/`

### Motivo
El `.env` local usaba `root`. Con mínimo privilegio, un error de programación, una inyección SQL o un `.env` filtrado solo pueden leer y escribir datos de `sigtac_db`. No pueden borrar, alterar tablas ni tocar otras bases del servidor.

### Impacto
- Verificado en MySQL 8.0.46 con un usuario temporal (`sigtac_verif_tmp`, ya eliminado):
  - El script se ejecuta sin errores y se puede repetir.
  - `SHOW GRANTS` muestra solo `USAGE` global y `SELECT, INSERT, UPDATE` en `sigtac_db`.
  - El usuario puede leer `cama`; MySQL le deniega `DELETE`, `DROP`, `CREATE` y leer otra base (error 1142).
- `schema.sql`, `seed.sql` y las verificaciones con base temporal siguen necesitando una cuenta de administrador.

### Decisiones
- Sin `DELETE`: la BD hace cumplir la RN-11 (baja lógica) aunque un DAO intente borrar.
- `CREATE USER IF NOT EXISTS` + `ALTER USER`: el script se puede ejecutar de nuevo sin error y deja la clave indicada.
- La clave nunca se escribe en el archivo versionado.

---

## [2026-10-12] — Verificación en MySQL 8.0 real y CHECK de texto sensibles a mayúsculas

### Cambio
- `schema.sql`: las columnas `paciente.sexo` y `empleado.turno` usan ahora `COLLATE utf8mb4_bin`.
- Se cargaron `schema.sql` y `seed.sql` en una base temporal (`sigtac_scratch_tmp`, ya eliminada) en **MySQL 8.0.46** y se ejecutaron 32 comprobaciones; todas pasaron:
  - Carga de ambos scripts sin errores; 21 tablas.
  - Columnas nuevas de `empleado` con los datos del seed (área "Triaje", especialidades, turno `MAÑANA` con su acento intacto).
  - `CHECK` de `turno` y `sexo`: rechazan `MADRUGADA`, `mañana`, `MANANA`, `Mañana`, `noche`, `m`, `f` y `X`; aceptan `NOCHE` y `NULL`. La FK de `id_area` rechaza un área inexistente.
  - RN-10 (`CH_triaje_rn10`): rechaza la reclasificación sin justificación, con 9 caracteres y con solo espacios; acepta 10 caracteres.
  - RN-05 (columnas generadas con `UNIQUE`): rechaza una segunda asignación vigente de la misma cama o del mismo episodio; acepta una cama libre y una asignación ya liberada.
  - Los modelos aceptan los datos reales: los 3 pacientes y los 5 empleados con subclase se construyen sin errores desde las filas de la BD.
  - `UsuarioDAO.autenticar` contra la base real: login correcto, clave incorrecta, usuario desactivado y DNI inválido.

### Archivos afectados
- `db_scripts/schema.sql`, `docs/`

### Motivo
La primera ejecución de la verificación mostró que la BD **aceptaba `'mañana'`** aunque el `CHECK` solo permite `'MAÑANA'`. La *collation* de la base (`utf8mb4_0900_ai_ci`) no distingue acentos (`ai`) ni mayúsculas (`ci`), así que `IN ('MAÑANA', ...)` daba por iguales `'mañana'` y `'MANANA'`. Lo mismo ocurría con `sexo` (`'m'` pasaba como `'M'`). Python rechaza esas variantes, de modo que un dato así entraría en la BD y luego fallaría al reconstruir el objeto. Con `utf8mb4_bin`, la comparación es exacta, igual que en Python.

### Impacto
- Pruebas: 341 pasan. La verificación en BD se hizo con un script temporal (no versionado), según la regla de `CLAUDE.md`.
- `sigtac_db` **no se modificó**. Para aplicar los cambios del 2026-10-12 hay que volver a ejecutar `schema.sql` y `seed.sql` sobre ella (borra los datos de desarrollo).
- Queda cerrado el pendiente "Probar `schema.sql` y `seed.sql` en un MySQL 8.0 real".

### Decisiones
- La *collation* binaria se aplica **solo a las dos columnas** cuyo `CHECK` compara texto. El resto de la base conserva `utf8mb4_0900_ai_ci`: es lo deseable para las búsquedas (por ejemplo, encontrar "Pérez" al buscar "perez").
- **Corrección:** el CHANGELOG del 2026-10-11 dice que el servidor de desarrollo es MariaDB 11.8. En este equipo el servidor es MySQL 8.0.46 (servicio `MySQL80`). Las verificaciones anteriores probablemente se hicieron en otra máquina.

### Pendientes
- El `.env` local usa `root`. Sirvió para crear la base temporal, pero la aplicación debería usar un usuario con solo `SELECT, INSERT, UPDATE`.
- Convertir la verificación en pruebas de integración permanentes (opcionales, que se salten si no hay BD).

---

## [2026-10-12] — Alineación de `persona.py` con la BD y validaciones de entrada

### Cambio
**Modelos (`models/persona.py`)**
- `Paciente`:
  - Nuevo atributo `sexo` (`'M'` o `'F'`, igual que `CH_paciente_sexo`).
  - `seguro` (texto) se reemplaza por `id_seguro` (entero obligatorio, FK a `seguro`) y `nombre_seguro` (opcional, solo para mostrar; el DAO lo obtendrá con un JOIN).
  - `id_paciente` admite `None` para un paciente aún no guardado en la BD.
  - Nueva firma: `Paciente(id_paciente, dni, nombres, apellidos, fecha_nac, sexo, id_seguro, activo=True, nombre_seguro=None)`.
- `Empleado`: nuevo atributo `activo` y método `anular()` (espejo de `empleado.estado_registro`, RN-11), igual que `Paciente`. Las tres subclases reciben `activo=True` como último parámetro.
- Subclases: `Enfermero.area`, `Medico.especialidad` y `PersonalLimpieza.turno` ahora tienen `@property` y aparecen en `obtener_resumen()`.
- Validaciones nuevas (lanzan `ValueError`):
  - DNI de exactamente 8 dígitos (`[0-9]`, sin espacios).
  - `nombres`, `apellidos`, `cargo`, `area` y `especialidad` obligatorios y no vacíos; se guardan sin espacios en los extremos.
  - `fecha_nac` debe ser `date` (no `datetime` ni texto) y no puede ser futura.
  - Los ids son enteros positivos (o `None` si aún no se guardaron); se rechaza `bool`.
  - `activo` debe ser `bool`: el DAO debe convertir el 0/1 de MySQL.
  - `colegiatura` es opcional, pero si se envía no puede estar vacía.
  - `turno` debe ser `MAÑANA`, `TARDE` o `NOCHE`.
  - Los mensajes de error no incluyen el valor recibido, porque podría ser un dato personal y acabar en un log.
- Nueva función `es_dni_valido()` y constante `PATRON_DNI` en `models/persona.py`.

**DAO (`dao/usuario_dao.py`)**
- Usa `es_dni_valido()` de `models/persona.py` en lugar de su propio `PATRON_DNI`. El comportamiento no cambia.

**Base de datos**
- `schema.sql`, tabla `empleado`: nuevas columnas `id_area` (FK a `area`), `especialidad` y `turno`, todas `NULL`, y la restricción `CH_empleado_turno`.
- `seed.sql`: nueva área `(5, 'Triaje')`, sin camas. Los empleados tienen ahora área (enfermería), especialidad (médicos) o turno (limpieza).

**Pruebas**
- `tests/test_persona.py` reescrito: 29 → 185 pruebas. Cubre cada validación con valores límite (DNI de 7 y 9 dígitos, fecha de hoy frente a mañana, etc.), la baja lógica de `Empleado` y los atributos de las subclases.
- `tests/test_estados_vs_bd.py`: nueva prueba que compara `Paciente.SEXOS_VALIDOS` y `PersonalLimpieza.TURNOS_VALIDOS` con los `CHECK` de `schema.sql`.

### Archivos afectados
`models/persona.py`, `dao/usuario_dao.py`, `db_scripts/schema.sql`, `db_scripts/seed.sql`, `tests/test_persona.py`, `tests/test_estados_vs_bd.py`, `docs/`

### Motivo
Resolver los problemas abiertos 1 a 5 de `PROJECT_STATUS.md`. `paciente_dao.py` no podía insertar un `Paciente` (faltaba `sexo`, que es `NOT NULL`). Un futuro `EmpleadoDAO` no podía reconstruir el estado ni los datos propios de cada subclase. Y los objetos aceptaban datos que la BD rechazaría (o peor, que aceptaría siendo incorrectos).

### Eliminado
- `Paciente.seguro` (texto): reemplazado por `id_seguro` + `nombre_seguro`. La tabla guarda un id, y con solo el nombre el DAO tendría que buscar el id por texto en cada inserción.
- `PATRON_DNI` de `dao/usuario_dao.py`: movido a `models/persona.py`. Una regla, un dueño: si el formato del DNI cambia, se cambia en un solo lugar.
- Comentario incorrecto en `Enfermero.registrar_triaje()` ("cerrar el episodio", copiado de `Medico.dar_alta`).

### Impacto
- Pruebas: 341 pasan (antes 183).
- Hay que volver a ejecutar `schema.sql` y `seed.sql` en cada entorno de desarrollo (borra los datos).
- **El SQL no se verificó contra una BD real:** el usuario del `.env` fue rechazado por el servidor (`Access denied`). Solo se comprobó de forma estática que cada fila del `INSERT INTO empleado` tenga 11 valores para 11 columnas.
- Cualquier código que cree `Paciente` con el parámetro `seguro` debe cambiar a `id_seguro` (hoy solo las pruebas lo hacían).

### Decisiones
- **`area`, `especialidad` y `turno` se guardan en la tabla `empleado`** como columnas que admiten `NULL` (una sola tabla para toda la jerarquía), en lugar de crear una tabla por subclase. Es más simple para el alcance del curso. La desventaja: la BD no puede impedir que, por ejemplo, un operario de limpieza tenga especialidad, porque el tipo de empleado está en otra tabla (`cargo.tipo`). Esa coherencia la garantizan las clases Python, que exigen cada atributo a su subclase.
- **`area` es una FK** a la tabla `area` ya existente, no texto libre. Se añadió el área "Triaje" porque el único enfermero del seed tiene rol "Enfermero de Triaje" y no existía un área que la representara.
- **`especialidad` es texto libre** (`VARCHAR(100)`), no un catálogo. Se solapa en parte con `cargo` ("Médico Internista" / "Medicina Interna"), pero son conceptos distintos (el puesto frente al título profesional), con el mismo criterio con el que se separaron `rol` y `cargo`. Si se necesitan reportes por especialidad, conviene convertirla en catálogo.
- **`turno` usa `CHECK`** con tres valores, como `sexo`; Python y la BD se mantienen sincronizados con una prueba.
- **DNI solo de 8 dígitos**, como ya exigía el login. La columna sigue siendo `VARCHAR(15)` y no se cambió.
- `activo` exige `bool` estricto, para que un 0/1 mal convertido en un DAO se detecte de inmediato.

### Pendientes
- Verificar `schema.sql` y `seed.sql` en una base temporal con un usuario administrador.
- Pacientes sin DNI peruano (extranjeros) o sin identificar (inconscientes): hoy no se pueden registrar. Requiere una decisión del equipo.
- Actualizar `db_scripts/diagrama.png` con las columnas nuevas de `empleado`.
- El `.env` local usa `root`. `CLAUDE.md` indica usar un usuario con solo `SELECT, INSERT, UPDATE`.

---

## [2026-10-12] — Cierre de la Fase 2: pruebas de `persona.py` y documentación al día

### Cambio
- Nuevo `tests/test_persona.py` con 29 pruebas de `Persona`, `Paciente`, `Empleado`, `Enfermero`, `Medico` y `PersonalLimpieza`:
  - `Persona` y `Empleado` son abstractas (no se pueden instanciar).
  - Propiedades de solo lectura.
  - `Paciente`: activo por defecto, reconstrucción como inactivo desde la BD y `anular()` como baja lógica (RN-11).
  - `calcular_edad()` con valores límite: el día antes, el día del cumpleaños y el día después; recién nacido; nacido el 29 de febrero en años bisiestos y no bisiestos. La fecha de hoy se fija con `monkeypatch` para que la prueba no dependa del día en que se ejecute.
  - `obtener_resumen()` polimórfico, con y sin colegiatura.
  - `tiene_permiso()` de cada subclase, incluidos módulos no permitidos y vacíos.
- `PROJECT_STATUS.md` reescrito con el estado real: Fase 2 completada, Fase 3 en curso, problemas abiertos y próximo trabajo.
- `DEVELOPMENT_PLAN.md`: casillas alineadas con el código (`Empleado` estaba sin marcar aunque existía; faltaban `estados.py`, 6 excepciones, `logging_config.py` y los archivos de pruebas; `controllers/` y `views/` figuraban como creados y no existen).

### Archivos afectados
- `tests/test_persona.py` (nuevo)
- `docs/PROJECT_STATUS.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/CHANGELOG.md`

### Motivo
- `Paciente` y `Empleado` eran las únicas clases del dominio sin pruebas (pendiente registrado el 2026-10-11). `paciente_dao.py` construirá objetos `Paciente`, así que su comportamiento debía quedar fijado antes.
- `PROJECT_STATUS.md` llevaba fecha del 2026-10-05 y no recogía los cambios del 2026-10-11. Como el proyecto lo usa como fuente de verdad del estado actual, estaba induciendo a error.

### Impacto
- Pruebas: 183 pasan (antes 154). No se modificó código de producción.
- La Fase 2 se da por cerrada.

### Decisiones
- **No se añadieron validaciones nuevas a `Persona`** (formato de DNI, fecha de nacimiento futura): ninguna regla del proyecto las define todavía. Se registran como problema abierto en `PROJECT_STATUS.md`, en lugar de inventarlas o marcarlas como `xfail`.
- Las pruebas de `tiene_permiso()` fijan el comportamiento actual. Si en la Fase 4 los permisos pasan a depender solo de la tabla `rol`, habrá que actualizarlas.
- **Cambio de orden de los DAO:** `auditoria_dao.py` se adelanta antes que `triaje_dao.py` y `asignacion_dao.py`. Es de una sola tabla, no necesita transacciones y lo usarán todos los controladores. Los dos DAO de varios pasos esperan la decisión sobre transacciones (`ConexionBD` usa `autocommit=True`).

### Pendientes
Diferencias entre el código y la BD encontradas al escribir las pruebas (detalle en `PROJECT_STATUS.md`, "Problemas abiertos"):
- `Paciente` no tiene `sexo`, que es `NOT NULL` en la tabla `paciente`. **Bloquea `paciente_dao.py`.**
- `Paciente.seguro` es texto; la tabla guarda `id_seguro`.
- `Empleado` no refleja `estado_registro`.
- `Enfermero.area`, `Medico.especialidad` y `PersonalLimpieza.turno` no tienen columna en la BD ni `@property`.
- `Persona` no valida el DNI ni la fecha de nacimiento.

---

## [2026-10-11] — Entorno virtual recreado dentro del proyecto

### Cambio
Se eliminó y se recreó `.venv` con `python -m venv` e instalando `requirements-dev.txt`.

### Archivos afectados
- `.venv/` (no versionado), `CLAUDE.md`

### Motivo
El `.venv` original era una copia de otro entorno (`Proyectos Personales/.venv`) y su script `pip` seguía apuntando a esa carpeta: un `pip install` instalaba los paquetes fuera del proyecto. Los entornos virtuales guardan rutas absolutas y no deben copiarse ni moverse.

### Impacto
- `pip` y `python` del `.venv` apuntan ahora a `SIGTAC/.venv`. Verificado con `pip --version` y 154 pruebas en verde.
- El entorno antiguo de la carpeta padre no se tocó.
- PyCharm: el intérprete configurado en `.idea/misc.xml` sigue apuntando al entorno de la carpeta padre; hay que seleccionar `SIGTAC/.venv` en la configuración del proyecto (archivo local no versionado).

### Pendientes
- Cada integrante del equipo debe crear su propio `.venv` (no se comparte).

---

## [2026-10-11] — Cierre de la revisión: reglas en modelos y BD, bloqueo de cuentas y dependencias (paso 7)

### Cambio
**Modelos**
- `EpisodioEmergencia.asignar_cama()` exige estado "en espera de cama" y un triaje activo (RN-01); `dar_alta()` exige estar en atención con cama. Ambos lanzan `ReglaNegocioError`.
- `obtener_triaje_actual()` ignora los triajes anulados, usa `max()` y su tipo de retorno es `Triaje | None`.
- Nuevo `models/estados.py` con `EstadoCama` y `EstadoEpisodio` (`StrEnum`). `Cama` y `EpisodioEmergencia` validan el estado recibido (un estado inexistente lanza `ValueError`). Las constantes `ESTADO_*` se conservan como alias. El Enum de episodio incluye `REFERIDO` y `FUGADO`, que ya existían en la BD.
- `SignosVitales` rechaza valores fisiológicamente imposibles (rangos amplios en `RANGOS`).
- `Sintoma` es ahora un `dataclass(frozen=True)` realmente inmutable y rechaza pesos negativos.
- Añadidos `__init__.py` en `dao/`, `models/` y `utils/`.

**Base de datos** (`schema.sql`, `seed.sql`)
- `usuario`: nuevas columnas `intentos_fallidos` y `bloqueado_hasta`.
- `triaje`: `CHECK` que hace cumplir la RN-10 en la BD (si el nivel final difiere del sugerido, la justificación es obligatoria y de al menos 10 caracteres).
- `asignacion_cama`: columnas generadas `cama_vigente` y `episodio_vigente` con índice `UNIQUE`: la BD impide dos asignaciones vigentes de la misma cama (RN-05) o del mismo episodio.
- Todas las columnas `estado_registro` son `NOT NULL`; `bitacora_auditoria.detalles_json` pasa a tipo `JSON`.
- Aviso visible al inicio de ambos scripts: destruyen datos, solo para desarrollo.

**Autenticación** (`UsuarioDAO`)
- Bloqueo temporal: 5 intentos fallidos consecutivos bloquean la cuenta 15 minutos (`MAX_INTENTOS_FALLIDOS`, `MINUTOS_BLOQUEO`). Un bloqueo se rechaza aunque la clave sea correcta, usa el señuelo y no suma intentos. Un login correcto reinicia el contador; un bloqueo vencido se reinicia antes de evaluar.
- El contador se incrementa dentro de la propia BD (operación atómica).

**Dependencias**: versiones fijadas con `==` en `requirements.txt` y `requirements-dev.txt`.

### Archivos afectados
`models/estados.py` (nuevo), `models/cama.py`, `models/triaje.py`, `dao/usuario_dao.py`, `db_scripts/schema.sql`, `db_scripts/seed.sql`, `requirements.txt`, `requirements-dev.txt`, `README.md`, `tests/` y los `__init__.py`.

### Motivo
Cerrar los hallazgos pendientes de la revisión: reglas de negocio que solo existían como comentarios, estados como texto repetido sin validar, ausencia de límite de intentos de login y dependencias sin versión fija.

### Impacto
- Es necesario volver a ejecutar `schema.sql` y `seed.sql` (borra los datos de desarrollo).
- El usuario de BD de la aplicación necesita `UPDATE` sobre `usuario` (ya contemplado en el README).
- Un servicio que llame a `asignar_cama()` o `dar_alta()` debe capturar `ReglaNegocioError`.
- Pruebas: 154 pasan. Se eliminaron los dos `xfail` porque las brechas están corregidas, y un nuevo test compara los Enum con los catálogos de `seed.sql`.
- Las restricciones de la BD y el bloqueo se verificaron contra una base temporal real (ya eliminada): datos inválidos rechazados, válidos aceptados, y simulación de un ataque de 5 claves erróneas.

### Decisiones
- **Servidor de desarrollo:** es MariaDB 11.8.8, no MySQL 8. **Corrección:** el README afirmaba que el proyecto no funciona en MariaDB; era una suposición no verificada y es falsa para esta versión. Las verificaciones de los pasos 5 a 7 se hicieron en MariaDB; el objetivo documentado sigue siendo MySQL 8.0.
- Los `CHECK` de `triaje` obligaron a cambiar las FK de `id_nivel` e `id_nivel_sugerido` a `ON UPDATE RESTRICT` (una columna usada en un `CHECK` no admite `CASCADE`). Es inocuo: los ids de catálogo no cambian.
- Criterio de excepciones: `ValueError` para datos de entrada inválidos (fuera de rango, formato) y excepciones de `SigtacError` para reglas de negocio violadas.
- El bloqueo es temporal (15 min) y no permanente, para que un atacante no pueda dejar fuera a un empleado de forma indefinida. Aun así permite un bloqueo temporal intencional; es el costo conocido de esta medida.
- Los rangos de `SignosVitales` son amplios y solo descartan errores de digitación; no definen qué es clínicamente normal.
- Las versiones se fijaron a las instaladas en desarrollo. `customtkinter`, `reportlab` y `matplotlib` aún no se usan en el código, por lo que no se han probado.

### Pendientes (fuera del alcance de la revisión)
- Permisos duplicados entre la tabla `rol` y `tiene_permiso` en las clases: se decidirá en la Fase 4 (controladores).
- Actualizar `db_scripts/diagrama.png` (faltan `fecha_nac`, `intentos_fallidos`, `bloqueado_hasta` y las columnas generadas).
- Probar `schema.sql` y `seed.sql` en un MySQL 8.0 real (aquí solo había MariaDB).
- Pruebas de integración contra una BD real y pruebas de `Paciente`/`Empleado`.
- Recrear el `.venv` dentro del proyecto (su `pip` apunta aún a otro entorno; usar `python -m pip`).
- Datos reales de integrantes en `seed.sql`: decisión del equipo.

---

## [2026-10-11] — Pruebas automáticas con pytest (revisión de seguridad, paso 6)

### Cambio
- Nueva carpeta `tests/` con 127 pruebas (125 pasan, 2 `xfail`):
  - `test_cama.py`: máquina de estados de `Cama` (RN-05, RN-07, RN-08) y `es_compatible` por tipo.
  - `test_triaje.py`: `Triaje`, `SignosVitales` y `EpisodioEmergencia` (RN-01, RN-09, RN-10, RN-11).
  - `test_estrategias.py`: umbrales y límites de `ReglaManchester` y `ReglaMINSA`, y signos vitales obligatorios.
  - `test_security.py`: bcrypt (formato, sal, hash inválido).
  - `test_db_connection.py`: variables obligatorias, `autocommit`, Singleton y reconexión.
  - `test_usuario_dao.py`: login, cuenta desactivada, señuelo, validación de DNI, consulta parametrizada, cierre del cursor y logs sin datos personales.
- Nuevos `pytest.ini` y `requirements-dev.txt` (dependencias de desarrollo separadas de las de la aplicación).
- Sección "Pruebas" en el README.

### Archivos afectados
- `tests/` (nuevo), `pytest.ini` (nuevo), `requirements-dev.txt` (nuevo), `README.md`

### Motivo
Hasta ahora las comprobaciones de los pasos 1 a 5 eran scripts desechables. Con pruebas permanentes, cualquier cambio que reintroduzca uno de los fallos corregidos se detecta de inmediato.

### Impacto
- Las pruebas no necesitan MySQL ni `.env`: la conexión se simula.
- Verificado reintroduciendo a propósito 4 fallos (`\d` en el DNI, `sato2` por defecto, falta del señuelo y `autocommit` desactivado): las pruebas detectaron los 4.

### Decisiones
- Las dos brechas conocidas están como `xfail(strict=True)`: `asignar_cama` sin triaje (RN-01) y `obtener_triaje_actual` que no ignora triajes anulados. Cuando se corrijan, la prueba fallará y obligará a quitar la marca.
- No se miden tiempos en las pruebas (serían inestables): se comprueba que se invoque el señuelo.
- Pendiente de cobertura: pruebas de integración contra MySQL real (por ahora solo se verificó a mano).

### Pendientes
- Corregir las dos brechas marcadas como `xfail` en `models/triaje.py`.
- Pruebas de `Paciente`, `Empleado` y sus subclases.

---

## [2026-10-11] — Alineación del modelo con la BD: fecha_nac y nivel_min (revisión de seguridad, paso 5)

### Cambio
- `empleado`: nueva columna `fecha_nac DATE NOT NULL`, para que la tabla coincida con la clase `Empleado` (que hereda `fecha_nac` de `Persona`).
- `seed.sql`: los 6 empleados incluyen fecha de nacimiento (ficticia).
- `tipo_cama.nivel_min`: el `COMMENT` indica ahora que es **solo informativo** y que la compatibilidad la decide `Cama.es_compatible()` en Python.

### Archivos afectados
- `db_scripts/schema.sql`
- `db_scripts/seed.sql`

### Motivo
- Un futuro `EmpleadoDAO` no podía construir un `Empleado` porque la tabla no guardaba la fecha de nacimiento.
- `nivel_min` contradecía a `es_compatible` (p. ej. Observación: `nivel_min = 4` en la BD, pero la clase acepta niveles 2, 3 y 4). La decisión documentada en `PROJECT_CONTEXT.md` es no comparar contra `nivel_min` en SQL; la columna quedaba como dato engañoso.

### Impacto
- Es necesario volver a ejecutar `schema.sql` y `seed.sql` en cada entorno de desarrollo (borra los datos).
- Los DAOs de empleado deben leer `fecha_nac`.
- Verificado cargando ambos scripts en una base temporal (ya eliminada) y autenticando con un usuario real del seed.

### Decisiones
- Se mantiene la compatibilidad de camas en Python (decisión previa del proyecto); se descartó crear `nivel_max` porque duplicaría la regla en la BD.
- `fecha_nac` es `NOT NULL` por coherencia con `Persona`. Es un dato personal: en un sistema real habría que justificar su recolección.

### Pendientes
- Actualizar `db_scripts/diagrama.png` (aún muestra `empleado` sin `fecha_nac`).
- Permisos duplicados (tabla `rol` frente a `tiene_permiso` en las clases): se resolverá en la Fase 4 (controladores), según el plan de desarrollo.
- Unificar los estados de cama y episodio entre Python y la BD (usar `Enum`; la BD tiene `REFERIDO` y `FUGADO / ABANDONO` que el código no conoce).

---

## [2026-10-11] — Higiene del repositorio: .gitignore, .env.example y README (revisión de seguridad, paso 4)

### Cambio
- `.gitignore` reescrito y ordenado por secciones:
  - Corregido `.mwb` (solo ignoraba un archivo con ese nombre exacto) por `*.mwb`.
  - Añadidos `__pycache__/`, `*.py[cod]`, `.pytest_cache/` y `.env.*` (con la excepción `!.env.example`).
  - Eliminados `node_modules/` y `vendor/`, que no aplican a un proyecto Python.
- Nuevo `.env.example`: plantilla con las variables de conexión, sin valores secretos.
- Nuevo `README.md` en la raíz: descripción, aviso de proyecto académico, requisitos, instalación, configuración, scripts de BD (con advertencia de que destruyen datos) y estructura.

### Archivos afectados
- `.gitignore`
- `.env.example` (nuevo)
- `README.md` (nuevo)

### Motivo
- Sin `__pycache__/` ignorado, los archivos compilados terminarían en el repositorio.
- Sin plantilla, quien clone el proyecto no sabe qué variables definir y la aplicación (que ahora exige las variables) no arrancaría.
- El README documenta los requisitos (Python 3.12+, MySQL 8) y avisa de que `schema.sql` y `seed.sql` borran datos.

### Impacto
- Todo el equipo: cada integrante crea su `.env` a partir de `.env.example`.

### Decisiones
- El README recomienda un usuario de BD con permisos `SELECT, INSERT, UPDATE` sobre `sigtac_db` y no `root`. Si un DAO necesita otro permiso (por ejemplo `DELETE`), se ampliará aquí.
- Se declara en el README que MariaDB no es compatible (collation `utf8mb4_0900_ai_ci`).

### Pendientes
- Añadir instrucciones de ejecución cuando exista `main.py`.
- Fijar versiones en `requirements.txt` (punto de la revisión sobre dependencias).

---

## [2026-10-11] — Estrategias de triaje sin valores por defecto (revisión de seguridad, paso 3)

### Cambio
- `ReglaManchester` y `ReglaMINSA` ya no sustituyen un signo vital ausente por un valor "normal" (`sato2=100`, `pa_sis=120`, `temp=37.0`, `fc=80`). Si falta alguno, o es `None`, lanzan `SignosVitalesIncompletosError` indicando cuáles faltan.
- Nueva validación compartida `EstrategiaTriaje._exigir_signos()` en la clase base.
- Nueva excepción `SignosVitalesIncompletosError` en `models/excepciones.py`.
- Cada estrategia exige únicamente los signos que usa: Manchester `sato2` y `pa_sis`; MINSA `temp` y `fc`.

### Archivos afectados
- `models/estrategias.py`
- `models/excepciones.py`

### Motivo
En triaje, "no medido" no equivale a "normal". Con los valores por defecto, un paciente sin saturación registrada se evaluaba como si tuviera 100 %, lo que podía clasificarlo en un nivel menos urgente del que le corresponde (infraclasificación).

### Impacto
- Módulo de Triaje: quien llame a `clasificar()` debe capturar `SignosVitalesIncompletosError` y pedir al enfermero que complete la medición.

### Decisiones
- No se modificaron los umbrales ni los pesos: los criterios clínicos requieren validación con la norma y se dejan fuera de este cambio.
- Se usa una excepción de dominio (`SigtacError`) en lugar de `ValueError` para poder distinguirla de otros errores de validación.

### Pendientes
- Las dos estrategias dan resultados distintos para el mismo paciente: con los datos del seed del episodio 1 (`sato2=89`, `pa_sis=165`, dolor torácico), Manchester sugiere nivel 1 y MINSA nivel 2, porque MINSA no evalúa saturación ni presión. Revisar con la norma si es intencional.
- Documentar en el README que los algoritmos son una simulación didáctica y no deben usarse con pacientes reales.
- Pruebas automatizadas (`pytest`) de ambas estrategias.

---

## [2026-10-11] — Endurecimiento de autenticación (revisión de seguridad, paso 2)

### Cambio
- `UsuarioDAO.autenticar` valida que el DNI tenga exactamente 8 dígitos (`[0-9]{8}`) antes de consultar la BD.
- Nueva función `utils.security.simular_verificacion()`: ejecuta bcrypt contra un hash señuelo (calculado una vez al importar el módulo). Se invoca cuando el login falla sin comparar contra un hash real (usuario inexistente, cuenta desactivada o sin hash).
- `db_scripts/seed.sql`: los 5 usuarios de prueba tienen ahora hashes bcrypt reales y válidos (60 caracteres) en lugar del placeholder `$2b$12$EjemploHash...`.
- `utils/security.py` (`__main__`): el generador de hashes pide la clave con `getpass` en vez de usar claves fijas escritas en el código.

### Archivos afectados
- `dao/usuario_dao.py`
- `utils/security.py`
- `db_scripts/seed.sql`

### Motivo
- El placeholder del seed tenía 61 caracteres (bcrypt exige 60): `checkpw` lanzaba `ValueError` y ningún usuario de prueba podía iniciar sesión.
- Sin el señuelo, un DNI inexistente respondía al instante y uno existente tardaba ~180 ms (bcrypt), lo que permitía descubrir DNIs válidos midiendo tiempos. Medido tras el cambio: inexistente 185 ms, clave incorrecta 182 ms, desactivado 181 ms.
- Rechazar DNIs mal formados evita consultas innecesarias y cadenas arbitrarias en los logs.

### Impacto
- Módulo de Seguridad y Acceso (autenticación).
- Para cargar los nuevos hashes hay que volver a ejecutar `db_scripts/seed.sql` (hace `TRUNCATE`, solo en BD de desarrollo).

### Decisiones
- Clave de desarrollo de todos los usuarios del seed: `Sigtac#Dev2026`. Es **solo para desarrollo**; nunca debe usarse en un entorno real.
- El formato de DNI se fijó en 8 dígitos aunque la columna `dni` admite 15 caracteres. Si se necesitan carnés de extranjería u otros documentos, habrá que ampliar `PATRON_DNI`.
- Se usa `[0-9]` en vez de `\d` porque en Python `\d` acepta también dígitos de otros alfabetos.
- Los cambios históricos se registran aquí y no como texto dentro de docstrings o comentarios del código.

### Pendientes
- Límite de intentos fallidos / bloqueo temporal de cuenta (requiere columnas nuevas en `usuario`).

---

## [2026-10-11] — Conexión a BD y logging (revisión de seguridad, paso 1)

### Cambio
- `ConexionBD`: ya no usa valores por defecto inseguros (`root` / contraseña vacía); si falta `DB_HOST`, `DB_USER`, `DB_PASS` o `DB_NAME` lanza `ConexionBDError` con un mensaje claro. Se lee `DB_PORT` (3306 por defecto).
- La conexión usa `autocommit=True` y se abre de forma perezosa en `obtener_conexion()`. Singleton y reconexión protegidos con `threading.Lock`.
- Nueva excepción `ConexionBDError` en `models/excepciones.py`; `obtener_conexion()` la lanza en vez de devolver `None`.
- Se eliminó el bloque `__main__` de demostración de `db_connection.py` y los `print` pasaron a `logging`.
- `UsuarioDAO`: captura `ConexionBDError`; los logs dejaron de incluir DNI y nombres (usan `id_empleado` y rol) y usan formato diferido (`%s`) en vez de f-strings.
- Nuevo `utils/logging_config.py` con `configurar_logging()`, a llamar una vez desde el punto de entrada.

### Archivos afectados
- `dao/db_connection.py`
- `dao/usuario_dao.py`
- `models/excepciones.py`
- `utils/logging_config.py` (nuevo)

### Motivo
- Con `autocommit=False` y una única conexión compartida, una consulta quedaba atada a una "foto" antigua de la transacción (`REPEATABLE READ`): un usuario desactivado por un administrador podía seguir viéndose como activo.
- Los valores por defecto ocultaban errores de configuración e intentaban entrar como `root` sin clave.
- DNI y nombres son datos personales; no deben quedar en los logs. Con f-strings, un DNI con saltos de línea podía falsear entradas del log.

### Impacto
- Capa DAO y arranque de la aplicación (falta de configuración ahora es un error explícito).
- Cualquier DAO nuevo debe capturar `ConexionBDError`.

### Decisiones
- `autocommit=True` es una solución provisional válida mientras solo haya lecturas. Cuando se implementen DAOs de escritura que necesiten transacciones (asignar cama, dar de alta), migrar a un pool de conexiones (`mysql.connector.pooling`) con `commit`/`rollback` explícitos.

### Pendientes
- Llamar a `configurar_logging()` desde `main.py` cuando exista.

---

## [2026-10-05] — Robustecimiento y corrección de excepciones en UsuarioDAO

### Cambio
Refactorización del método `autenticar` en `UsuarioDAO`:
- Validación y saneamiento de entradas (`dni`, `password_plano`).
- Uso de cursor en modo `buffered=True` dentro del bloque `try` para proteger el Singleton de MySQL (`ConexionBD`).
- Reemplazo de captura genérica de excepciones (`Exception`) por `mysql.connector.Error as DBError`, eliminando la advertencia de inspección de PyCharm (`Too broad exception clause`).
- Cierre seguro del cursor dentro del bloque `finally` protegido contra desconexiones inesperadas.
- Migración de mensajes por consola (`print`) a la biblioteca estándar `logging`.

### Archivos afectados
- `dao/usuario_dao.py`

### Motivo
Evitar desincronizaciones de socket (`InternalError: Unread result found`) en la conexión compartida por la aplicación, prevenir excepciones no controladas ante entradas vacías o nulas y cumplir las directrices de inspección estática y manejo de excepciones específicas de Python y PyCharm.

### Impacto
- Módulo de Seguridad y Acceso (autenticación).
- Robustez y resiliencia en la capa DAO y en el ciclo de vida de los cursores MySQL.

### Decisiones
- Se captura específicamente `DBError` (`mysql.connector.Error`) tanto en la consulta como en el cierre del cursor en `finally` para apegarse a las recomendaciones de PEP 8 y PyCharm.
- Se mantiene el retorno del diccionario de sesión limpio (removiendo `hash_clave`) a la espera de la integración con `auth_controller.py`.

### Pendientes
- Actualizar `db_scripts/seed.sql` con un hash bcrypt válido para el administrador de pruebas.
- Continuar con la implementación de `paciente_dao.py`.

---

## [2026-10-05] — Estado inicial registrado

### Avance informado

El desarrollo actual se encuentra trabajando en:

```text
dao/usuario_dao.py
```

La documentación de planificación mantiene la Fase 2 (`models/`) como **En curso**, mientras que el trabajo actual ya ha comenzado a entrar en la Fase 3 (`dao/`).

Por este motivo, el estado no se marca como “Fase 3 completada”.

### Nota

El contenido concreto y el grado de finalización de `usuario_dao.py` deben verificarse contra el código real antes de marcar sus funcionalidades como completadas.

---

## [2026-10-05] — Decisiones técnicas documentadas

Se conservaron como decisiones importantes del proyecto:

### Arquitectura

Arquitectura por capas:

```text
Views
  ↓
Controllers
  ↓
Models / Domain
  ↓
DAO
  ↓
MySQL
```

### Patrones

- DAO para separar SQL del dominio.
- Strategy para algoritmos de clasificación de triaje.
- Singleton para la conexión a MySQL.

### Camas

La compatibilidad no debe resolverse comparando directamente `tipo_cama.nivel_min` en SQL.

La consulta DAO obtiene camas disponibles y el objeto correspondiente decide la compatibilidad mediante:

```text
cama.es_compatible(nivel)
```

### Seguridad

- `bcrypt` para contraseñas.
- `.env` para credenciales.
- Consultas parametrizadas.
- Validación de `usuario.activo`.

### Auditoría

La auditoría de operaciones sensibles se realizará mediante llamadas explícitas desde los controladores a `auditoria_dao`.

---

## Plantilla para futuras entradas

Copiar esta estructura:

```markdown
## [YYYY-MM-DD] — Título del cambio

### Cambio
Descripción breve.

### Archivos afectados
- `ruta/archivo.py`
- `ruta/otro_archivo.py`

### Motivo
Por qué se hizo.

### Impacto
Qué módulos/reglas afecta.

### Decisiones
Si hubo una decisión técnica importante.

### Pendientes
Qué queda por hacer.
```

---

## Reglas del changelog

Registrar especialmente:

- cambios de arquitectura;
- cambios de base de datos;
- cambios de reglas de negocio;
- nuevos patrones;
- cambios de flujo;
- correcciones importantes;
- decisiones que deban explicarse en la sustentación;
- cambios de orden en el plan;
- problemas relevantes y su solución.

No usar el changelog como sustituto del código ni como documentación de cada línea modificada.
