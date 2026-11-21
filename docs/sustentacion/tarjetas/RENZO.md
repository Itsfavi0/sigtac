# Tarjeta de Renzo

**Tu parte:** Criterio 1 (min **2–5**) y los aportes adicionales con el cierre (min **34–36**).

> **Cómo usar el texto:** está escrito para que no te quedes en blanco. Léelo en voz alta 2 o 3 veces y luego dilo con
> tus palabras; no hace falta que sea idéntico. Lo que **sí** debe salir exacto está en **negrita**. Cada párrafo dura
> unos 30–40 segundos al hablar con calma.

**Antes de entrar:** terminal abierta en la carpeta del proyecto, con este comando escrito (sin ejecutarlo):
`grep -rl "mysql" --include=*.py models controllers views utils dao main.py`
Archivos a mano: `tests/test_capas.py`, `dao/base_dao.py`, `dao/db_connection.py`, `dao/transaccion.py`.

---

## Criterio 1 · Min 2–5 · Texto sugerido

**① La observación (30 s)**
«Profesor, en la primera presentación usted nos hizo una pregunta que anotamos: **¿cómo harían para migrar a otro motor de base
de datos?**, por ejemplo Oracle o SQL Server. En ese momento le respondimos que bastaba con cambiar los DAO, pero era solo una
intención. Hoy queremos mostrarle que ya es un hecho que se puede comprobar.»

**② La respuesta (20 s)**
«La respuesta es esta: **para cambiar de motor solo se toca la carpeta `dao/`.** Los modelos, los controladores y las
pantallas no saben que existe MySQL.»

**③ Evidencia 1: la terminal (40 s)** *(ejecuta el `grep`)*
«Este comando busca en todo el código dónde se importa el conector de MySQL. Salen **tres archivos, y los tres están dentro de
`dao/`**: `base_dao`, `db_connection` y `transaccion`. No aparece ninguna pantalla, ningún controlador y ningún modelo.»

**④ Evidencia 2: la prueba automática (30 s)**
«Pero no queremos que esto dependa de que nos acordemos. Por eso hay una prueba automática, **`test_capas`**, que falla si una
pantalla o el `main` importan `dao` o `mysql`. Si alguien rompe la separación, las pruebas dejan de pasar.»

**⑤ Evidencia 3: los errores (30 s)**
«Un tercer detalle: los errores. Cuando MySQL falla, `BaseDAO` lo traduce a una excepción propia del sistema, como
`PersistenciaError`, `RegistroDuplicadoError` o `ConexionBDError`. El resto del programa nunca ve un error de MySQL.»

**⑥ Qué cambiaría y qué no (40 s)**
«Si migráramos, habría que cambiar el conector en `db_connection`, la traducción de errores en `base_dao`, la forma de obtener
el identificador recién insertado, algunas funciones de fecha y de paginación que son propias de MySQL, y los scripts de la
base de datos. Todo eso está en una sola carpeta. Las **6 679 líneas de pantallas, las 1 127 de controladores y las 1 368 de
modelos no cambian**; lo que se toca son las 1 853 líneas de `dao`.»

**⑦ Por qué funciona (20 s)**
«Funciona porque cada DAO recibe y devuelve **objetos del dominio**, como `Paciente` o `Cama`, y no filas de la base de datos.
El controlador pide las camas disponibles y recibe una lista de `Cama`, sin saber con qué SQL se obtuvo.»

**⑧ La honestidad (30 s)** *(dilo tú antes de que pregunten)*
«Queremos ser honestos: **no es cambiar una línea.** Hay SQL propio de MySQL en una docena de consultas, y **la migración no la
hemos ejecutado**. Lo que sí está comprobado es el aislamiento: sabemos exactamente dónde habría que trabajar. Con esto damos
por atendida la observación. Ahora Ian explica las clases principales.»

---

## Aportes adicionales · Min 34–36 · Texto sugerido

**① Declaración (60 s)**
«Además de los ocho criterios, queremos declarar expresamente los aportes adicionales. Uno: una **base de datos MySQL** con
22 tablas y transacciones, de modo que los datos persisten. Dos: un **reporte en PDF** con indicadores de un período. Tres:
**búsqueda** de pacientes por documento y por nombre. Cuatro: **cinco roles con permisos**, donde cada usuario ve solo los
módulos que le corresponden. Cinco: una **bitácora de auditoría**, que registra quién hizo qué y cuándo. Seis: **claves
cifradas con bcrypt** y bloqueo tras cinco intentos fallidos. Siete: **pruebas automáticas**; hoy son **2 332, de las cuales
2 331 pasan y una se omite porque solo corre en Windows**. Y ocho: modo oscuro en toda la interfaz.»

**② Qué sigue (30 s)**
«Lo que sigue es que cada usuario pueda cambiar su propia clave, que hoy lo hace el administrador; probarlo con varias PC al
mismo tiempo, y agregar una pantalla para elegir la norma de triaje.»

**③ Cierre (10 s)**
«Eso es todo de nuestra parte. Quedamos atentos a sus preguntas.»

---

## No digas / di

| No digas | Di |
|---|---|
| «Solo cambiamos una línea» / «ya migramos» | «Solo se toca `dao/`; la migración no se ejecutó, el aislamiento sí está probado» |
| «Las 2 332 pruebas pasan» | «2 331 pasan y 1 se omite fuera de Windows» |
| «No hay SQL de MySQL en otras capas» (sin más) | «Todo el SQL está en `dao/`» |

## Si te bloqueas

Mira a Favio. Si pasan 5 segundos, él completa. Frase tuya para ganar tiempo: «Lo central es esto: solo cambia `dao/`.»
Si te pierdes en el punto ⑥, no leas la lista: di «el conector, la traducción de errores y las consultas con funciones propias».

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
