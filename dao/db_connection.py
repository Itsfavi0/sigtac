import logging
import os
import threading

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error
from mysql.connector.constants import ClientFlag

from models.excepciones import ConexionBDError

logger = logging.getLogger(__name__)


def _variable_requerida(nombre: str) -> str:
    """Lee una variable de entorno obligatoria; falla con un mensaje claro si no existe."""
    valor = os.getenv(nombre)
    if valor is None:
        raise ConexionBDError(f"Falta la variable de entorno {nombre} (revisa tu archivo .env).")
    return valor


class ConexionBD:
    """
    Clase Singleton para gestionar la conexión a la base de datos MySQL.
    Garantiza que toda la aplicación comparta la misma conexión en lugar
    de saturar el servidor abriendo conexiones nuevas.
    """
    _instancia = None
    _lock = threading.Lock()

    def __new__(cls):
        # Doble comprobación con lock: seguro aunque dos hilos lo pidan a la vez
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    instancia = super().__new__(cls)
                    instancia._conexion = None
                    instancia._en_transaccion = False
                    cls._instancia = instancia
        return cls._instancia

    def _conectar(self):
        """Lee el archivo .env y establece la conexión física con MySQL."""
        load_dotenv()  # Carga las variables de entorno desde el archivo .env

        # Sin valores por defecto inseguros: si falta algo, se detiene con un error claro
        config = {
            "host": _variable_requerida("DB_HOST"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": _variable_requerida("DB_USER"),
            "password": _variable_requerida("DB_PASS"),
            "database": _variable_requerida("DB_NAME"),
            "autocommit": True,
            # rowcount de un UPDATE = filas encontradas, no solo las modificadas: así 0 significa "no existe"
            # aunque los datos nuevos sean iguales a los guardados.
            "client_flags": [ClientFlag.FOUND_ROWS],
        }

        try:
            self._conexion = mysql.connector.connect(**config)
        except Error as e:
            self._conexion = None
            raise ConexionBDError(f"No se pudo conectar a la base de datos: {e}") from e

        logger.info("Conexión a MySQL (%s) establecida con éxito.", config["database"])

    def obtener_conexion(self):
        """
        Retorna la conexión activa. Si el servidor de BD cerró la conexión
        por inactividad (timeout), la vuelve a levantar automáticamente.
        Lanza ConexionBDError si no es posible conectar.

        Durante una transacción no reconecta: los pasos siguientes se ejecutarían en una conexión
        nueva, fuera de la transacción, y se guardarían aunque la operación quedara a medias.
        """
        with self._lock:
            if self._conexion is None or not self._conexion.is_connected():
                if self._en_transaccion:
                    # Al perderse la conexión, MySQL deshace por su cuenta lo que no se confirmó.
                    logger.error("Conexión perdida durante una transacción; no se reconecta.")
                    raise ConexionBDError("Se perdió la conexión con la base de datos durante la operación.")
                if self._conexion is not None:
                    logger.warning("Conexión perdida, reconectando a la base de datos...")
                self._conectar()
            return self._conexion

    @property
    def en_transaccion(self) -> bool:
        """True mientras hay una transacción explícita abierta en la conexión compartida."""
        return self._en_transaccion

    def iniciar_transaccion(self):
        """
        Abre una transacción explícita (START TRANSACTION). Mientras dure, autocommit queda
        suspendido para esta conexión hasta terminar_transaccion(). Se usa a través de
        dao.transaccion.transaccion(), no directamente.
        """
        conexion = self.obtener_conexion()
        conexion.start_transaction()
        self._en_transaccion = True

    def terminar_transaccion(self, confirmar: bool):
        """
        COMMIT si `confirmar` es True; si no, ROLLBACK. En ambos casos la transacción queda cerrada.

        Si la conexión ya se perdió, MySQL deshizo por su cuenta lo no confirmado: no se llama a
        rollback(), que con la extensión C del conector lanzaría un error que no hereda de
        mysql.connector.Error y taparía el error original. Confirmar sin conexión lanza ConexionBDError.
        """
        try:
            if self._conexion is None or not self._conexion.is_connected():
                if confirmar:
                    raise ConexionBDError("Se perdió la conexión antes de confirmar la operación.")
                return
            if confirmar:
                self._conexion.commit()
            else:
                self._conexion.rollback()
        finally:
            self._en_transaccion = False

    def cerrar_conexion(self):
        """Cierra la conexión de forma segura al apagar el sistema."""
        with self._lock:
            if self._conexion and self._conexion.is_connected():
                self._conexion.close()
                logger.info("Conexión a MySQL cerrada correctamente.")
            self._conexion = None
            self._en_transaccion = False  # cerrar la conexión deshace en MySQL lo no confirmado
