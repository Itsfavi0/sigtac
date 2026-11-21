# Tarjeta de Renzo

**Tu parte:** Criterio 1 (min **2–5**) y los aportes adicionales con el cierre (min **34–36**).
Esta tarjeta es un apoyo: dilo con tus palabras. Lo que **sí** tiene que salir exacto está en negrita.

**Antes de entrar:** terminal abierta en la carpeta del proyecto, con el `grep` escrito (sin ejecutarlo).
Archivos: `tests/test_capas.py`, `dao/base_dao.py`, `dao/db_connection.py`, `dao/transaccion.py`.

---

## Criterio 1 · Min 2–5

1. **La observación:** «En la primera presentación nos preguntó: *¿cómo migrarían a otro motor de base de datos?*». Estado: **atendida**.
2. **La respuesta en una frase:** «Para cambiar de motor solo se toca la carpeta `dao/`. Los modelos, los controladores y las
   pantallas no saben que existe MySQL.»
3. **Evidencia 1 (terminal):** ejecuta
   `grep -rl "mysql" --include=*.py models controllers views utils dao main.py`
   → salen **3 archivos, todos de `dao/`**: `base_dao.py`, `db_connection.py`, `transaccion.py`.
4. **Evidencia 2:** «`tests/test_capas.py` falla si una pantalla o `main.py` importa `dao` o `mysql`. Si alguien rompe la separación,
   las pruebas dejan de pasar.»
5. **Evidencia 3:** `BaseDAO` traduce los errores de MySQL a excepciones propias (`PersistenciaError`, `RegistroDuplicadoError`,
   `ConexionBDError`). El resto del sistema nunca ve un error de MySQL.
6. **Qué cambia y qué no:** `views` 6 679 líneas, `controllers` 1 127 y `models` 1 368 **no cambian**; `dao` (1 853) es lo que se toca.
7. **Qué habría que cambiar** (si piden detalle): el conector (`db_connection.py`), la traducción de errores (`base_dao.py`),
   el id recién insertado (`_insertar`), las funciones de fecha y `IF`/`LIMIT` en los DAO y los scripts `schema.sql`/`seed.sql`.
8. **Honestidad (dilo tú, antes de que pregunten):** «No es cambiar una línea: hay SQL propio de MySQL en una docena de consultas.
   Lo que el diseño garantiza es que todo ese trabajo está en una sola carpeta. La migración **no se ejecutó**; lo probado es el aislamiento.»

**Por qué funciona:** un DAO recibe y devuelve objetos del dominio (`Paciente`, `Cama`), no filas. El controlador llama
`CamaDAO.listar_disponibles()` y recibe una lista de `Cama`, sin saber con qué SQL se obtuvo.

**Transición:** «Ian explica las clases principales.»

## Aportes adicionales · Min 34–36

Declararlos **expresamente** (el profesor lo pide): MySQL (22 tablas y transacciones), reporte PDF, búsqueda, 5 roles y permisos,
bitácora, claves con bcrypt, pruebas automáticas, modo oscuro.
**Cifra de pruebas: 2 332; 2 331 pasan y 1 se omite** (solo corre en Windows). Qué sigue: que cada usuario cambie su clave,
probarlo con varias PCs y un selector de norma de triaje. Cierra con «¿Preguntas?».

---

## No digas / di

| No digas | Di |
|---|---|
| «Solo cambiamos una línea» / «ya migramos» | «Solo se toca `dao/`; la migración no se ejecutó, el aislamiento sí está probado» |
| «Las 2 332 pruebas pasan» | «2 331 pasan y 1 se omite fuera de Windows» |
| «No tenemos SQL de MySQL en otras capas» (sin más) | «Todo el SQL está en `dao/`» |

## Si te bloqueas

Mira a Favio. Si pasan 5 segundos, él completa. Frase tuya para ganar tiempo: «Lo central es esto: solo cambia `dao/`.»
Si te cuesta la lista de cambios, no la leas: di «el conector, la traducción de errores y las consultas con funciones propias».

## Preguntas que te tocan (respuestas completas en [PREGUNTAS_PROFESOR.md](../PREGUNTAS_PROFESOR.md))

| Pregunta | Dónde |
|---|---|
| «¿Cómo migrarían a Oracle / SQL Server?» | arriba; apartado B6 |
| «¿Qué es una transacción? ¿Dónde la usan?» | C1 |
| «¿Qué pasa si dos PCs asignan la misma cama?» | C2 |
| «¿Por qué baja lógica?» | C5 |
| «¿Por qué normalizaron? ¿Hasta qué forma?» | C6 |
| «¿Cómo evitan la inyección de SQL?» | C7 |
| «¿Por qué Singleton en la conexión?» | B5 |
