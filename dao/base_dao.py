import logging

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
