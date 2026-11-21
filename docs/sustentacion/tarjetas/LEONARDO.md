# Tarjeta de Leonardo

**Tu parte:** explicar las pantallas durante la demo (min **18–27**). El criterio 7, organización del código (min 27–30), lo expone Favio.

> **Cómo usar el texto:** está escrito para que no te quedes en blanco. Léelo en voz alta 2 o 3 veces y luego dilo con
> tus palabras. Lo que **sí** debe salir exacto está en **negrita**. Favio maneja la PC y **no habla mientras escribe**: tú
> llenas esos momentos. Detalle de los pasos en [GUION_DEMO.md](../GUION_DEMO.md).

**Antes de entrar:** editor con `views/tema.py`, `views/triage_view.py` y `views/app_principal.py`.

---

## Demo · Min 18–27 · Texto sugerido (un párrafo por paso)

**Apertura (20 s)**
«Vamos a recorrer el flujo completo de una emergencia, desde que llega el paciente hasta que la cama vuelve a estar disponible,
con la base de datos real. En el camino vamos a provocar **tres rechazos**: un dato incorrecto, uno incompleto y uno duplicado.»

**Paso 1 · Login con clave equivocada (30 s)**
«Empezamos con una clave equivocada. Fíjense que el sistema no dice si falló el documento o la clave: no da pistas a quien
intenta entrar. Y tras **cinco intentos fallidos la cuenta se bloquea 15 minutos**.»

**Paso 2 · Tablero (40 s)**
«Entramos como jefe de guardia. Este es el tablero: el estado de la guardia de un vistazo, con las camas agrupadas por tipo y
los pacientes que esperan, ordenados por prioridad. Se actualiza solo cada 30 segundos. Y observen el menú: solo muestra los
módulos que este rol puede usar.»

**Paso 3 · Triaje, paciente nuevo (40 s)**
«Llega un paciente. Busco su documento y no existe, así que se registra aquí mismo, en la misma pantalla de triaje, con su
motivo de consulta. Esto es un solo flujo para que el profesional no tenga que ir de pantalla en pantalla.»

**Paso 4 · Rechazo 1: dato incorrecto (60 s)**
«Primer rechazo. Escribo la presión al revés: sistólica 95 y diastólica 150. El sistema marca los dos campos y no deja
continuar, porque la diastólica no puede ser mayor que la sistólica. **Esta regla no está en la pantalla: está en la clase
`SignosVitales`.** La pantalla solo muestra el mensaje del modelo.»

**Paso 5 · Sugerencia del sistema (50 s)**
«Corrijo la presión a 150 sobre 95, completo los signos y marco el síntoma dolor torácico opresivo. El sistema **sugiere** el
nivel 2, naranja, y dice por qué: el peso de los síntomas, 8,5, supera el umbral de 7. Usa la regla de Manchester. Es una
sugerencia: el profesional decide.»

**Paso 6 · Rechazo 2: dato incompleto (70 s)**
«Segundo rechazo. Supongamos que el médico no está de acuerdo y quiere reclasificar. Pulso "Reclasificar", elijo el nivel 3 y
escribo solo "ok" como justificación. El botón no deja continuar y dice cuántos caracteres faltan: **"Faltan 8 caracteres,
mínimo 10"**. Es la regla RN-10: cambiar lo que sugirió el sistema exige una justificación escrita. La regla vive en el método
`reclasificar` de la clase `Triaje`; la pantalla solo la consulta.»

**Paso 7 · Confirmar (30 s)**
«Cancelo la reclasificación y confirmo el nivel 2. Queda guardado con quién lo clasificó y a qué hora, y el nivel sugerido
queda separado del final, para auditoría.»

**Paso 8 · Gestión de camas (60 s)**
«Pasamos a Gestión de camas. El paciente está en la cola, entre otros que esperan. Al elegirlo aparecen solo las camas
compatibles con el nivel 2: las de UCI y Observación. **No aparecen las de Trauma Shock, porque son solo para el nivel 1.**
Esto es el polimorfismo que explicó Percy: cada tipo de cama responde por sí misma si es compatible.»

**Paso 9 · Asignar, llegada y alta (70 s)**
«Asigno una cama de Observación: queda reservada. En la pestaña "Con cama" marco que el paciente llegó, y la cama pasa a
ocupada. Ahora doy de alta; el sistema pide confirmación. **Al dar de alta, la cama pasa a limpieza y no vuelve a estar
disponible sola**; eso es la regla RN-07.»

**Paso 10 · Rechazo 3: duplicado (50 s)**
«Tercer rechazo. Voy a Pacientes, busco a una paciente que ya está en una cama e intento abrirle otro episodio. El sistema lo
rechaza: **un paciente no puede tener dos atenciones abiertas a la vez.** Además, la base de datos tiene sus propias
restricciones como última barrera, por si dos computadoras intentan lo mismo a la vez.»

**Pasos 11–12 · Otro rol: Limpieza (60 s)**
«Cierro sesión y entro como personal de limpieza. Otro rol, otro menú: solo ve el tablero y su bandeja de limpieza. Elijo la
cama que acabamos de dar de alta y confirmo la limpieza. **Recién ahora la cama vuelve a estar disponible**; es la regla RN-08.»

**Pasos 13–14 · Reportes y bitácora (60 s)**
«Entro como administrador. En Reportes veo los indicadores del período y exporto un PDF que se puede imprimir. Y en
Administración, la bitácora: todo lo que acabamos de hacer quedó registrado, con quién lo hizo, qué hizo y cuándo.»

**Paso 15 · Persistencia (40 s)**
«Por último, cierro la aplicación por completo, la abro de nuevo y busco al paciente que registramos al inicio. Sigue ahí: el
dato está en MySQL y no en la memoria del programa. Con esto cubrimos el flujo completo y los tres rechazos. Ahora Favio explica la organización del código.»

---

## No digas / di

| No digas | Di |
|---|---|
| «La pantalla valida el dato» | «El **modelo** valida; la pantalla muestra el mensaje y marca el campo» |
| «La pantalla consulta la base de datos» | «Recibe su controlador; nunca toca el DAO» |
| «Cambiar el color es tocar cada pantalla» | «Se cambia en un solo lugar (`tema.py` y `utils/colores.py`)» |
| Escribir una clave a la vista | Nunca. Tampoco abrir el `.env` |

## Si te bloqueas

Mira a Favio; a los 5 segundos completa. Si en la demo no recuerdas qué decir de un paso, di qué regla se está mostrando
(RN-10, RN-08) y qué clase la guarda; Favio añade el resto. No improvises pasos que no se ensayaron.

## Preguntas que te tocan (respuestas completas en [PREGUNTAS_PROFESOR.md](../PREGUNTAS_PROFESOR.md) y [HOJAS_DE_ESTUDIO.md](../HOJAS_DE_ESTUDIO.md))

| Pregunta | Dónde |
|---|---|
| «¿Cómo sabe la pantalla que un dato es inválido?» | E2, E3 |
| «¿Qué pasa si cambian el color de “Ocupada”?» | Se cambia en un solo lugar (`utils/colores.py` y `views/tema.py`) y cambia en toda la aplicación y en el PDF |
| «¿Por qué CustomTkinter y no Tkinter puro?» | HOJAS: es Tkinter por debajo, con mejor aspecto y modo oscuro |
| «¿Cómo se agrega un rol o módulo nuevo?» | B7 |
| «¿Cómo prueban las pantallas?» | G1 |
| «¿Por qué 4 capas?» / «¿por qué un controlador?» | Favio las responde (B1, B2); tú puedes completar con «la pantalla solo muestra» |
