import logging
from datetime import datetime

import mysql.connector
from mysql.connector import errorcode

from dao.db_connection import ConexionBD
from models.excepciones import PersistenciaError, RegistroDuplicadoError

logger = logging.getLogger(__name__)


class BaseDAO:
    """
    Clase base de los DAO. Concentra en un solo lugar la parte que todos repiten:
    pedir la conexión, abrir y cerrar el cursor, y traducir los errores de MySQL
    a excepciones del dominio. Las subclases solo escriben su SQL y el mapeo a objetos.

    Errores que pueden lanzar sus métodos (todos derivan de PersistenciaError):
    - ConexionBDError: no hay conexión con la base de datos.
    - RegistroDuplicadoError: se violó una restricción UNIQUE.
    - PersistenciaError: cualquier otro fallo de MySQL.
    """

    @staticmethod
    def _validar_id(valor, nombre: str) -> int:
        """Un id recibido como parámetro debe ser un entero positivo (bool no cuenta). Lanza ValueError."""
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ValueError(f"{nombre} debe ser un entero positivo.")
        return valor

    @staticmethod
    def _validar_periodo(desde: datetime, hasta: datetime) -> tuple[datetime, datetime]:
        """Un período [desde, hasta) con fechas y horas: el límite superior no se incluye. Lanza ValueError."""
        if not isinstance(desde, datetime) or not isinstance(hasta, datetime):
            raise ValueError("El período debe indicarse con fechas y horas (datetime).")
        if desde >= hasta:
            raise ValueError("El inicio del período debe ser anterior al final.")
        return desde, hasta

    @staticmethod
    def _consultar_uno(sql: str, params: tuple = ()) -> dict | None:
        """Ejecuta un SELECT y devuelve la primera fila como diccionario, o None si no hay filas."""
        return BaseDAO._ejecutar_con_cursor(sql, params, lambda cursor: cursor.fetchone())

    @staticmethod
    def _consultar_varios(sql: str, params: tuple = ()) -> list[dict]:
        """Ejecuta un SELECT y devuelve todas las filas (lista vacía si no hay ninguna)."""
        return BaseDAO._ejecutar_con_cursor(sql, params, lambda cursor: cursor.fetchall())

    @staticmethod
    def _insertar(sql: str, params: tuple) -> int:
        """Ejecuta un INSERT y devuelve el id generado (AUTO_INCREMENT)."""
        return BaseDAO._ejecutar_con_cursor(sql, params, lambda cursor: cursor.lastrowid)

    @staticmethod
    def _ejecutar(sql: str, params: tuple) -> int:
        """Ejecuta un UPDATE y devuelve la cantidad de filas afectadas."""
        return BaseDAO._ejecutar_con_cursor(sql, params, lambda cursor: cursor.rowcount)

    @staticmethod
    def _bloquear(sql: str, params: tuple) -> bool:
        """
        Ejecuta un SELECT ... FOR UPDATE: bloquea las filas leídas hasta el COMMIT o ROLLBACK, así otra
        PC que quiera la misma fila espera a que termine esta operación. Devuelve False si no hay filas.

        Solo tiene sentido dentro de transaccion(): con autocommit el bloqueo se libera al instante.
        Debe ser la primera lectura de la transacción, para que las consultas siguientes vean los
        cambios que otra PC confirmó mientras se esperaba el bloqueo.
        """
        if not ConexionBD().en_transaccion:
            raise RuntimeError("Un bloqueo de filas (FOR UPDATE) solo funciona dentro de transaccion().")
        return BaseDAO._consultar_uno(sql, params) is not None

    @staticmethod
    def _ejecutar_con_cursor(sql: str, params: tuple, obtener_resultado):
        """Abre un cursor, ejecuta la sentencia, extrae el resultado y cierra el cursor siempre."""
        if not isinstance(params, tuple):
            raise TypeError("params debe ser una tupla; para un solo valor: (valor,)")

        conexion = ConexionBD().obtener_conexion()  # ConexionBDError se propaga tal cual
        cursor = None
        try:
            cursor = conexion.cursor(dictionary=True, buffered=True)
            cursor.execute(sql, params)
            return obtener_resultado(cursor)
        except mysql.connector.IntegrityError as e:
            if e.errno == errorcode.ER_DUP_ENTRY:
                logger.warning("ERROR DAO: registro duplicado (errno=%s).", e.errno)
                raise RegistroDuplicadoError("Ya existe un registro con esos datos.") from e
            logger.error("ERROR DAO: restricción de integridad violada (errno=%s).", e.errno)
            raise PersistenciaError("Los datos no cumplen las restricciones de la base de datos.") from e
        except mysql.connector.Error as e:
            # Solo se registra el código: el mensaje de MySQL puede incluir los valores enviados (documentos, nombres).
            logger.error("ERROR DAO: fallo de MySQL (errno=%s).", e.errno)
            raise PersistenciaError("No se pudo completar la operación en la base de datos.") from e
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except mysql.connector.Error:
                    pass
