# Guion de la demostración en vivo

Cubre los criterios **5** (avance funcional) y **6** (validación y errores), y el aporte adicional de la base de datos.
Dura unos 9 minutos en la exposición completa (ver [GUION_EXPOSICION.md](GUION_EXPOSICION.md)). Una persona maneja la PC y otra explica; quien maneja no habla mientras escribe.

> **Este guion se revisó contra el código y `seed.sql` el 21/11/2026** (textos de botones, mensajes y datos), y la
> conexión a MySQL funciona. **Todavía falta recorrerlo completo una vez con cronómetro** y corregir aquí lo que no
> coincida. Recargar `seed.sql` después de cada ensayo.

## Preparación (el día anterior y 10 minutos antes)

1. **Recargar los datos** (lo hace Favio, con su cuenta de administrador de MySQL):
   ```bash
   mysql -u <admin> -p < db_scripts/seed.sql           # incluye 80 camas y 76 pacientes (ver «Cómo queda la guardia»)
   ```
   `seed.sql` borra todo lo anterior. Hay que volver a cargarlo **después de cada ensayo**, porque el paciente de
   la demo ya quedaría registrado.
2. Abrir la aplicación: `python main.py`. Dejarla en el login.
3. Tener abierto el editor con `models/cama.py`, por si piden ver código.
4. Ventana maximizada y **modo claro** (se ve mejor en proyector).
5. Cerrar todo lo demás: sin notificaciones ni otras ventanas.

### Cómo queda la guardia después de cargar el seed

| Qué | Cantidad | Detalle |
|---|---|---|
| Camas | 80 | 26 disponibles, 37 ocupadas, 5 reservadas, 7 en limpieza y 5 fuera de servicio |
| En la cola de triaje | 7 | Dos son pacientes sin identificar (NN) |
| En la cola de cama | 11 | Niveles 2 (cuatro), 3 (tres), 4 (tres) y 5 (uno); **ninguno de nivel 1** |
| Con cama (pestaña «Con cama») | 42 | Entre ellos Rosa Mendoza (DNI 70123456) |
| Bandeja de limpieza | 7 | UCI-02, OBS-07, HOS-05, TRA-04, UCI-14, OBS-20 y HOS-23 |
| Episodios cerrados hoy | 14 | 10 altas, 2 referidos y 2 fugas: dan datos a Reportes |

Como hay más gente, en los pasos 8 y 12 hay que **elegir por nombre o por cama**, no «el primero».

### Cuentas (todas con la clave de desarrollo que está en `db_scripts/seed.sql`)

| Documento | Rol | Qué ve |
|---|---|---|
| DNI 22222222 | Jefe de Guardia | Tablero, Triaje, Gestión de camas, Pacientes, Reportes |
| DNI 44444444 | Personal de Limpieza | Tablero y Limpieza |
| DNI 11111111 | Administrador | Tablero, Reportes y Administración |
| DNI 33333333 | Enfermero de Triaje | Tablero, Triaje y Pacientes |
| DNI 77777777 | Médico de Emergencia | Tablero, Triaje, Gestión de camas y Pacientes |

La demo usa las tres primeras. Con solo tres inicios de sesión se muestra que cada rol ve módulos distintos.

### El paciente de la demo

| Dato | Valor |
|---|---|
| Documento | DNI **45678912** (no existe en el seed) |
| Nombres y apellidos | Jorge Luis · Paredes Vega |
| Motivo de consulta | Dolor en el pecho desde hace una hora |
| Signos | PA 150 / 95 · FC 110 · FR 24 · Temperatura 36,8 · SatO₂ 93 |
| Síntoma | Dolor Torácico Opresivo |
| Resultado esperado | **Nivel 2 (Naranja)**: «Peso de los síntomas 8,5 ≥ 7» |
| Camas compatibles | Las de UCI y Observación disponibles. **Ninguna de Trauma Shock** (solo nivel 1) |

## Los pasos

| N.º | Qué se hace | Qué se dice | Criterio |
|---|---|---|---|
| 1 | Login con DNI 22222222 y una **clave equivocada** | «El sistema no dice si falló el documento o la clave: no da pistas. Cinco fallos bloquean la cuenta 15 minutos.» | 6 |
| 2 | Login correcto. Se abre el **Tablero** | «Entramos como jefe de guardia. Este es el estado de la guardia: camas por tipo y quién espera, por prioridad.» | 5 |
| 3 | **Triaje** → buscar DNI 45678912 → no existe → registrarlo y escribir el motivo | «El paciente no estaba registrado: se registra aquí mismo.» | 5 |
| 4 | **Error 1 — dato incorrecto.** PA sistólica 95 y diastólica 150 (al revés) | «La diastólica no puede ser mayor que la sistólica. El sistema marca los dos campos y no deja continuar. La regla está en la clase `SignosVitales`.» | 6 |
| 5 | Corregir a 150 / 95, completar los signos, marcar «Dolor Torácico Opresivo» | «El sistema **sugiere** el nivel 2 y dice por qué. Usa la regla de Manchester; el profesional decide.» | 5 |
| 6 | **Error 2 — dato incompleto.** Pulsar «Reclasificar», elegir nivel 3 y escribir solo «ok» en la justificación | «Regla RN-10: cambiar la sugerencia exige una justificación de al menos 10 caracteres. El botón no deja continuar y dice cuántos faltan: "Faltan 8 caracteres (mínimo 10)". La regla está en el método `reclasificar` de la clase `Triaje`; la pantalla solo la consulta.» | 6 y 3 |
| 7 | Pulsar «Cancelar reclasificación» y **confirmar** el nivel 2 | «Queda guardado con quién lo clasificó y a qué hora.» | 5 |
| 8 | **Gestión de camas** → en la cola hay 12 pacientes: buscar a **Jorge Luis Paredes Vega** → elegirlo | «Solo aparecen las camas compatibles con el nivel 2: UCI y Observación. Las de Trauma Shock no, porque son solo para el nivel 1. Esto es polimorfismo: cada tipo de cama responde `es_compatible`.» | 4 y 5 |
| 9 | **Asignar** una cama de Observación → pestaña «Con cama» → **Llegó a la cama** → **Dar de alta** (pide confirmar) | «La cama pasa por sus estados: reservada, ocupada y, al dar de alta, en limpieza. No vuelve a estar disponible sola.» | 5 |
| 10 | **Error 3 — duplicado.** **Pacientes** → buscar DNI 70123456 (Rosa Mendoza, que ya está en una cama) → abrir otro episodio | «Un paciente no puede tener dos atenciones abiertas a la vez. El sistema lo rechaza.» | 6 |
| 11 | Cerrar sesión → login con DNI 44444444 (Limpieza) | «Otro rol, otro menú: Limpieza solo ve el tablero y su bandeja.» | 5 |
| 12 | **Limpieza** → hay 8 solicitudes: elegir la **cama de Observación del paso 9** (la más reciente) → **confirmar** | «Recién ahora la cama vuelve a estar disponible (RN-08).» | 5 |
| 13 | Cerrar sesión → login con DNI 11111111 (Administrador) → **Reportes** → exportar **PDF** y abrirlo | «Indicadores del período y un reporte que se puede imprimir.» | Aporte |
| 14 | **Administración → Bitácora** | «Todo lo que acabamos de hacer quedó registrado: quién, qué y cuándo.» | Aporte |
| 15 | **Cerrar la aplicación**, volver a abrirla, entrar y buscar DNI 45678912 en Pacientes | «El dato está en MySQL, no en memoria: cerramos el programa y el paciente sigue ahí.» | Aporte (BD) |

### Si hay poco tiempo

Pasos **2, 3, 5, 6, 8 y 15**: un flujo, un rechazo, el polimorfismo y la base de datos.

## Si algo falla

| Qué pasa | Qué hacer |
|---|---|
| MySQL no arranca o la aplicación dice «Sin conexión» | `python -m prototipo.ver` abre la misma aplicación con datos de demostración. Se dice: «usamos los datos de demostración». No sirve para el paso 15 |
| Un paso da un error inesperado | No insistir. Pasar al siguiente y mostrar la captura de ese paso en el Canva |
| El paciente de la demo «ya existe» | Quedó de un ensayo. Usar otro DNI (por ejemplo 45678913) y recargar `seed.sql` después |
| No hay camas compatibles | Faltó cargar el seed. Se aprovecha: «el sistema avisa que no hay cama compatible» |
| La cola de cama no tiene 11 pacientes | El seed quedó de un ensayo (los episodios se cierran): recargar `seed.sql` |
| El proyector recorta la ventana | La aplicación funciona desde 1093 × 540: achicar la ventana |

## Lo que NO se hace en la demo

- No se muestra el archivo `.env` ni se escribe una clave a la vista.
- No se improvisan pasos que no se ensayaron.
- No se corre `seed.sql` delante del profesor.
