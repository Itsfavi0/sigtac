import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


class ConexionBD:
    """
    Clase Singleton para gestionar la conexión a la base de datos MySQL.
    Garantiza que toda la aplicación comparta la misma conexión en lugar
    de saturar el servidor abriendo conexiones nuevas.
    """
    _instancia = None
    _conexion = None

    def __new__(cls):
        # Implementación estricta del patrón Singleton
        if cls._instancia is None:
            cls._instancia = super(ConexionBD, cls).__new__(cls)
            cls._instancia._inicializar_conexion()
        return cls._instancia

    def _inicializar_conexion(self):
        """Lee el archivo .env y establece la conexión física con MySQL."""
        load_dotenv()  # Carga las variables de entorno desde el archivo .env

        try:
            self._conexion = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASS", ""),
                database=os.getenv("DB_NAME", "sigtac_db")
            )
            if self._conexion.is_connected():
                print("LOG: Conexión a MySQL (sigtac_db) establecida con éxito.")
        except Error as e:
            print(f"ERROR FATAL: No se pudo conectar a la base de datos.\nDetalles: {e}")
            self._conexion = None

    def obtener_conexion(self):
        """
        Retorna la conexión activa. Si el servidor de BD cerró la conexión
        por inactividad (timeout), la vuelve a levantar automáticamente.
        """
        if self._conexion is None or not self._conexion.is_connected():
            print("LOG: Reconectando a la base de datos...")
            self._inicializar_conexion()
        return self._conexion

    def cerrar_conexion(self):
        """Cierra la conexión de forma segura al apagar el sistema."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.close()
            print("LOG: Conexión a MySQL cerrada correctamente.")
            self._conexion = None


# ==========================================
# PRUEBA DE CONEXIÓN
# ==========================================
if __name__ == "__main__":
    # Este bloque solo se ejecuta si corres este archivo directamente.
    # Demostración del Singleton:
    print("Iniciando prueba de Singleton...")

    bd1 = ConexionBD()
    con1 = bd1.obtener_conexion()

    bd2 = ConexionBD()
    con2 = bd2.obtener_conexion()

    # Comprobación de que ambas variables apuntan exactamente al mismo objeto en memoria
    if bd1 is bd2:
        print("¡ÉXITO! El patrón Singleton funciona: ambas instancias son la misma.")

    bd1.cerrar_conexion()