# SIGTAC — Brief de diseño de las pantallas

> Fase D2 del plan de diseño (2026-10-27). Dice qué debe hacer y mostrar cada pantalla; los colores,
> fuentes y medidas se definen en D4 (`DESIGN.md`). El contexto del producto está en `PRODUCT.md`.
> Punto de partida: el diseño del equipo en Figma Make (modo oscuro, «Tablero de Camas» y «Nuevo Triaje»).

## Decisiones del equipo

| Decisión | Respuesta |
|---|---|
| Modo de color | Claro por defecto; el oscuro del Figma, corregido, como modo opcional para la noche |
| Flujo de triaje | **Unificado**: en «Triaje» se busca o registra al paciente, se abre el episodio y se tría en una sola pantalla |
| Tamaño del tablero | Debe verse bien con **30 a 40 camas** |
| Pantallas | Login, ventana principal, tablero, triaje y pacientes |
| Identidad | Solo la marca SIGTAC |
| Personalidad (tras la crítica D3) | **Señalética de triaje**: los 5 colores del triaje son el protagonista visual; todo lo demás es sobrio y neutro |
| Cuánto se conserva del Figma | **Libertad total**: se reorganiza lo que la crítica justifique |
| Criterios de la sugerencia | **Se amplía la estrategia** para que devuelva los motivos, que el panel mostrará |

## Reglas para todas las pantallas

- **Modo «Operate»:** el usuario viene a completar una tarea. Lo que importa es que se lea rápido, que todo sea
  coherente y que no haya sorpresas; la expresión de marca va en los detalles.
- **Espacio útil:** una laptop de 1366×768 con el zoom de Windows al 125 % deja unos **1093×614 px** útiles.
  Es el tamaño mínimo en el que todo debe caber sin desplazarse horizontalmente. En pantallas grandes, el
  contenido se reparte sin estirarse sin límite.
- **Nunca solo color:** cada nivel lleva su número y su nombre, y cada cama, su estado escrito.
- **Errores:** dicen qué pasó y qué hacer, en el idioma de la guardia. El controlador ya escribe esos mensajes.
- **Nada animado** en lo que se repite (navegar, elegir filas, escribir). Al pasar el mouse o presionar, solo
  cambia el color.
- **Teclado:** Tab en el orden de lectura, Enter para la acción principal y Esc para cancelar en los diálogos.

## 1. Inicio de sesión (no está en el Figma)

- **Quién y para qué:** cualquier empleado, al empezar el turno o al cambiar de usuario en una PC compartida.
- **Lo primero que se ve:** la marca SIGTAC y los dos campos. Nada más compite.
- **Contenido:**
  - la marca;
  - el documento (tipo y número);
  - la contraseña;
  - el botón «Ingresar»;
  - el aviso «Prototipo académico — no validado clínicamente».
- **Estados:**
  - **datos incorrectos o cuenta bloqueada:** el mismo mensaje genérico, para no revelar la causa (regla de
    seguridad). Se borra la contraseña y el foco vuelve a ella;
  - **sin conexión a la BD:** un mensaje distinto y claro;
  - **mientras verifica** (bcrypt tarda unos 0.3 s): el botón queda deshabilitado.

## 2. Ventana principal (marco)

- **Barra lateral:**
  - la marca;
  - la navegación, que muestra solo los módulos que el rol puede usar (Tablero para todos; Triaje y Pacientes
    según el permiso);
  - al pie: el usuario (nombre y rol), el cambio de modo claro/oscuro y «Cerrar sesión».
  - En el alcance actual **no se muestran** «Cola de Espera», «Limpieza» ni «Reportes»: el Figma las tenía como
    marcadores «próximamente», y un botón que lleva a una pantalla vacía hace perder tiempo.
- **Encabezado de cada pantalla:** el título, una línea que explica qué muestra y la hora de la última
  actualización.
  - El Figma decía «EN VIVO», pero la pantalla se actualiza cada 30 s, así que «Actualizado 10:42» es lo cierto.
- **Cambio de módulo:** inmediato, sin transición.

## 3. Tablero (base: «Tablero de Camas» del Figma)

- **Quién:** todos los roles. Es la pantalla de inicio.
- **Para qué:** saber en un vistazo cuántas camas hay libres, cuál está en qué estado y quién espera cama.
- **Lo primero que se ve:** el **mapa de camas**. Es el centro de la pantalla.
- **Indicadores** (una fila de 4):
  - camas disponibles sobre las camas en servicio;
  - camas en limpieza;
  - pacientes de prioridad I–II que esperan cama;
  - espera promedio.
  - Los tres primeros salen del mapa y de la cola, así que **los ve cualquier rol**. La espera promedio
    necesita el permiso de reportes: para los demás roles, esa tarjeta muestra «En espera de triaje».
- **Mapa:**
  - 30 a 40 camas agrupadas por tipo (Trauma shock, UCI, Observación, Hospitalización);
  - cada casilla muestra el código y el estado escrito en letra legible, con el color del estado;
  - una leyenda con los 5 estados.
  - **Solo lectura:** las casillas no reaccionan al clic, para no prometer una acción que todavía no existe
    (asignar cama es de la pantalla de camas, que viene después).
- **Cola de espera de cama:** los pacientes triados sin cama, por prioridad y luego por llegada (nivel,
  paciente, motivo y tiempo de espera). Con muchos pacientes, la lista se desplaza dentro de su recuadro.
- **Estados:**
  - **sin camas registradas:** se explica, no aparece una grilla vacía;
  - **nadie espera cama:** «Nadie espera cama»;
  - **error al actualizar:** se mantiene lo último y se avisa.
- **Actualización:** automática cada 30 s y con un botón «Actualizar».

## 4. Triaje — flujo unificado (base: «Nuevo Triaje Clínico» del Figma)

- **Quién:** el enfermero de triaje, el médico y el jefe de guardia. Es el flujo más repetido del sistema.
- **Para qué:** pasar de «llegó una persona» a «tiene nivel de triaje y está en la cola de cama» en el menor
  número de pasos.
- **Disposición:** el formulario a la izquierda y el **panel de clasificación** fijo a la derecha, como en el
  Figma.
- **Paso 1. Paciente**, con dos entradas:
  - **Nuevo:**
    - documento (los 4 tipos) y buscar. Si el paciente existe, se muestra su ficha compacta; si no, aparecen los
      campos para registrarlo (nombres, apellidos, fecha de nacimiento, sexo y seguro);
    - «Sin identificar (NN)»: solo sexo, edad aparente y seguro;
    - motivo de consulta, obligatorio, porque abre el episodio.
  - **En cola (N):** los pacientes que ya se registraron y esperan triaje. Se elige uno y se salta al paso 2.
- **Paso 2. Signos vitales:**
  - 6 campos: **PA sistólica y PA diastólica por separado**, FC, FR, temperatura y SatO2;
  - cada uno con su unidad y el rango admitido;
  - **sin escala de dolor**: el modelo no la tiene, así que se quita del Figma.
- **Paso 3. Síntomas:** las casillas del catálogo, en dos columnas.
- **Panel de clasificación:**
  - **sugerencia:** el nivel grande, con número, nombre y color, y el protocolo (Manchester);
  - se calcula **solo, en cuanto los 6 signos son válidos**, y se recalcula si cambia un signo o un síntoma;
  - sin datos completos: «Complete los signos vitales para ver la sugerencia».
- **Acciones:**
  - «Confirmar nivel N» es la principal;
  - «Reclasificar» despliega la elección del nivel 1–5 y la **justificación, obligatoria solo al reclasificar**
    (en el Figma figuraba siempre como obligatoria; RN-10), con el mínimo de caracteres a la vista.
- **Después de registrar:** un aviso breve, el formulario se limpia y el paciente pasa a la cola de cama.
- **Errores:**
  - un signo fuera de rango o un documento inválido se señala junto al campo, no solo en un diálogo;
  - un episodio cerrado desde otra PC u otros errores de regla de negocio salen en un diálogo;
  - en todos los casos, el formulario conserva lo escrito.
- **Por dentro:** la pantalla llama, en orden, a buscar o registrar al paciente → abrir el episodio → registrar
  el triaje. Son operaciones separadas. Si falla el triaje, el paciente ya quedó registrado y aparece en «En
  cola», así que no se pierde nada.

## 5. Pacientes (no está en el Figma)

- **Quién:** quienes tienen el permiso PACIENTES (enfermero, médico y jefe de guardia).
- **Para qué:** consultar y corregir datos de pacientes, y resolver a los «NN».
- **Pestaña «Buscar»:**
  - documento → ficha (datos, seguro y estado) con «Editar datos». El documento no se edita;
  - «Abrir episodio» queda como acción secundaria, para quien registra sin triar (por ejemplo, admisión).
- **Pestaña «Sin identificar»:**
  - la lista de NN;
  - «Identificar», que pide los datos reales;
  - si ese documento ya existe, ofrece «Fusionar con el paciente existente», con confirmación.
- **Estados:** búsqueda sin resultado («No hay un paciente con ese documento» y el enlace a Triaje para
  registrarlo); lista de NN vacía.

## Lo que queda abierto (se decide en D3–D4)

- **Tiempo objetivo por nivel** (el Figma mostraba «Tiempo objetivo: 0 minutos»). Hoy solo está en `seed.sql`
  (`nivel_triaje.tiempo_max_min`), no en Python. Mostrarlo exige agregarlo al modelo, con su prueba contra el
  seed.
- ~~**«Criterios detectados»**~~ Decidido (2026-10-27): se amplía la estrategia para que devuelva los motivos.
  Es un cambio de lógica, con sus pruebas, que va antes del prototipo de la pantalla de triaje.
- **Datos de la demo:** el seed tiene 8 camas; para que el tablero luzca con 30 a 40 hace falta ampliar
  `seed.sql`. Es una tarea aparte que se ejecuta contra la BD.
- **Errores junto al campo:** hoy los modelos lanzan `ValueError` con un mensaje. Mostrar el error junto al
  campo exige saber de qué campo es: hay que decidir cómo se asocia el mensaje a su campo.
