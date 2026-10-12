import logging
import os
import threading

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

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
        """
        with self._lock:
            if self._conexion is None or not self._conexion.is_connected():
                if self._conexion is not None:
                    logger.warning("Conexión perdida, reconectando a la base de datos...")
                self._conectar()
            return self._conexion

    def cerrar_conexion(self):
        """Cierra la conexión de forma segura al apagar el sistema."""
        with self._lock:
            if self._conexion and self._conexion.is_connected():
                self._conexion.close()
                logger.info("Conexión a MySQL cerrada correctamente.")
            self._conexion = None
