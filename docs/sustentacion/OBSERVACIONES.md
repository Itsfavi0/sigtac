# Criterio 1 — Observaciones de la primera presentación

> Favio: esta es la observación que recordamos. Si el equipo recuerda otra, se agrega una fila a la tabla.

| N.º | Observación del profesor | Qué se hizo | Estado |
|---|---|---|---|
| 1 | «¿Cómo harían para migrar a otro motor de base de datos (Oracle, SQL Server u otro)?» | Todo el acceso a datos quedó aislado en la capa `dao/`. Hay una prueba automática que impide que otra capa use MySQL. | Atendida y comprobable |

## La respuesta en una frase

> «Para cambiar de motor solo se toca la carpeta `dao/`. Los modelos, los controladores y las pantallas no saben
> que existe MySQL, y hay una prueba automática que lo comprueba.»

En la primera presentación era una intención. Ahora es un hecho que se puede enseñar.

## La evidencia (se muestra en pantalla)

**1. El conector de MySQL solo se importa en tres archivos, todos de `dao/`.**

```bash
grep -rl "mysql" --include=*.py models controllers views utils dao main.py
# dao/base_dao.py
# dao/db_connection.py
# dao/transaccion.py
```

(`scripts/verificar_controladores.py` también lo usa, pero es una herramienta de prueba, no parte de la aplicación.)

**2. Una prueba lo exige.** `tests/test_capas.py` falla si alguna pantalla o `main.py` importa `dao` o `mysql`.
Si alguien rompe la separación, las pruebas dejan de pasar.

**3. Los errores de MySQL no salen de `dao/`.** `BaseDAO` los traduce a excepciones propias
(`PersistenciaError`, `RegistroDuplicadoError`, `ConexionBDError`). El resto del sistema nunca ve un error de MySQL.

## Qué habría que cambiar para migrar, por ejemplo, a SQL Server u Oracle

| Qué | Archivo | Cambio |
|---|---|---|
| El conector | `dao/db_connection.py` | Cambiar `mysql.connector` por el del otro motor (`pyodbc`, `oracledb`) |
| La traducción de errores | `dao/base_dao.py` | Los códigos de error son propios de cada motor (duplicado: `ER_DUP_ENTRY` en MySQL) |
| Inicio y fin de transacción | `dao/transaccion.py` | Solo el tipo de excepción que se captura |
| El id recién insertado | `dao/base_dao.py` (`_insertar`) | `lastrowid` en MySQL; `SCOPE_IDENTITY()` u `RETURNING` en otros |
| Funciones de fecha | 9 consultas en los `*_dao.py` | `NOW()` → `GETDATE()` / `SYSDATE`; `TIMESTAMPDIFF` → `DATEDIFF`; `IF()` → `CASE` |
| Paginación | `dao/auditoria_dao.py` (1 consulta) | `LIMIT` → `TOP` u `OFFSET … FETCH` |
| Los scripts | `db_scripts/schema.sql`, `seed.sql` | `AUTO_INCREMENT` → `IDENTITY` o secuencias; tipos de dato |

**Lo que no cambia:** las 1 368 líneas de `models/`, las 1 127 de `controllers/` y las 6 679 de `views/`.

## Por qué funciona (el patrón DAO)

- Un DAO **recibe y devuelve objetos del dominio** (`Paciente`, `Cama`), no filas.
  Cada DAO tiene un método `_a_<entidad>(fila)` que es el único punto que convierte una fila en un objeto.
- El controlador llama `CamaDAO.listar_disponibles()` y recibe una lista de `Cama`. No sabe con qué SQL se obtuvo.
- El SQL usa parámetros (`%s`), nunca texto concatenado.

## Lo que hay que decir con honestidad si preguntan más

- No es «cambiar una línea»: hay SQL propio de MySQL en una docena de consultas (fechas, `IF`, `LIMIT`, `FOR UPDATE`).
  Lo que el diseño garantiza es que **todo ese trabajo está en una sola carpeta**.
- No se usó un ORM (como SQLAlchemy) a propósito: el curso pide entender el SQL y el patrón DAO se explica mejor a mano.
- La migración a otro motor no se ha ejecutado; lo que está probado es el aislamiento.
