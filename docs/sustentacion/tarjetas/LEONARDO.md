# Tarjeta de Leonardo

**Tu parte:** explicar las pantallas durante la demo (min **18–27**) y el Criterio 7, organización del código (min **27–30**).
Esta tarjeta es un apoyo: dilo con tus palabras. Lo que **sí** tiene que salir exacto está en negrita.

**Antes de entrar:** editor con `views/tema.py`, `views/triage_view.py` y `views/app_principal.py`; el árbol de carpetas visible.

---

## Demo · Min 18–27

Favio maneja la PC y **no habla mientras escribe**; tú explicas. Detalle en [GUION_DEMO.md](../GUION_DEMO.md). Lo esencial por paso:

| Paso | Qué ocurre en pantalla | Tú dices |
|---|---|---|
| 1 | Login con clave equivocada | «No dice si falló el documento o la clave. Cinco fallos bloquean la cuenta 15 minutos» |
| 2 | Tablero | «Estado de la guardia: camas por tipo y quién espera, por prioridad. Se actualiza solo cada 30 segundos» |
| 3 | Triaje: paciente nuevo | «No estaba registrado: se registra aquí mismo» |
| 4 | **Rechazo 1:** PA 95 / 150 | «La diastólica no puede ser mayor que la sistólica. Marca los dos campos. **La regla está en `SignosVitales`; la pantalla solo muestra el error**» |
| 5 | Sugerencia de nivel 2 | «El sistema **sugiere** y dice por qué (Manchester). El profesional decide» |
| 6 | **Rechazo 2:** «ok» como justificación | «RN-10: mínimo 10 caracteres. Dice cuántos faltan. La regla está en `Triaje.reclasificar`» |
| 7 | Confirmar nivel 2 | «Queda guardado con quién y a qué hora» |
| 8 | Gestión de camas | «Solo aparecen camas compatibles: UCI y Observación. Es el polimorfismo de Percy» |
| 9 | Asignar → llegó → alta | «La cama pasa por reservada, ocupada y, al dar de alta, en limpieza. No vuelve a estar disponible sola» |
| 10 | **Rechazo 3:** duplicado | «Un paciente no puede tener dos atenciones abiertas a la vez» |
| 11–12 | Otro rol: Limpieza | «Otro rol, otro menú. Recién ahora la cama vuelve a disponible (RN-08)» |
| 13–14 | PDF y bitácora | «Indicadores del período; todo queda registrado: quién, qué y cuándo» |
| 15 | Cerrar y reabrir | «El dato está en MySQL, no en memoria» |

Anuncia los tres rechazos: «un dato **incorrecto**, uno **incompleto** y uno **duplicado**».

## Criterio 7: organización del código · Min 27–30

1. Muestra el árbol: `views/`, `controllers/`, `models/`, `dao/`, `utils/`, `db_scripts/`, `tests/`.
2. **`views → controllers → models → dao → MySQL`: las dependencias van solo hacia abajo.**
3. Sigue una operación por las 4 capas: `triage_view.py` → `TriajeController.registrar()` → `Triaje.reclasificar()` → `TriajeDAO`.
4. `views/tema.py` es el **único** archivo con colores y letras (cada color es un par claro/oscuro); `views/componentes/` tiene las
   piezas que todas las pantallas reutilizan (botones, tarjetas, tablas, la matriz de camas).
5. Una pantalla **nunca** tiene SQL ni reglas: `tests/test_capas.py` lo exige.
6. Nombres en español que dicen lo que hacen: `cama.reservar()`, `episodio.dar_alta()`, `exigir_permiso()`.
7. Tamaño: unas 11 400 líneas de aplicación y 13 000 de pruebas.

**Transición:** «Favio explica las decisiones técnicas.»

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
| «¿Por qué 4 capas?» | B1 |
| «¿Por qué un controlador y no llamar al DAO desde la pantalla?» | B2 |
| «¿Cómo sabe la pantalla que un dato es inválido?» | E2, E3 |
| «¿Qué pasa si cambian el color de “Ocupada”?» | HOJAS, hoja de Leonardo |
| «¿Por qué CustomTkinter y no Tkinter puro?» | HOJAS: es Tkinter por debajo, con mejor aspecto y modo oscuro |
| «¿Cómo se agrega un rol o módulo nuevo?» | B7 |
| «¿Cómo prueban las pantallas?» | G1 |
