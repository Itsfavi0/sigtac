import logging
import re
from mysql.connector import Error as DBError
from dao.db_connection import ConexionBD
from models.excepciones import ConexionBDError
from utils.security import simular_verificacion, verificar_password

logger = logging.getLogger(__name__)

# DNI peruano: exactamente 8 dígitos
PATRON_DNI = re.compile(r"[0-9]{8}")


class UsuarioDAO:
    """
    DAO para gestionar el acceso, autenticación y validación de usuarios
    cruzando las tablas empleado, usuario y rol de nuestra base de datos.
    """

    @staticmethod
    def autenticar(dni: str, password_plano: str) -> dict | None:
        """
        Busca un empleado por su DNI, verifica que su acceso esté activo (activo = True),
        compara la clave plana con el hash almacenado usando bcrypt y retorna los datos de sesión.
        """
        # 1. Validación y saneamiento de entradas
        if not dni or not isinstance(dni, str) or not password_plano or not isinstance(password_plano, str):
            logger.warning("Intento de autenticación con credenciales nulas o en formato inválido.")
            return None

        dni_limpio = dni.strip()
        if not PATRON_DNI.fullmatch(dni_limpio):
            logger.warning("Intento de autenticación con DNI de formato inválido.")
            return None

        # 2. Conexión con la base de datos
        try:
            conexion = ConexionBD().obtener_conexion()
        except ConexionBDError as e:
            logger.error("No se pudo obtener una conexión válida a la base de datos: %s", e)
            return None

        cursor = None
        query = """
            SELECT 
                e.id_empleado, e.dni, e.nombres, e.apellidos, e.colegiatura, 
                c.nombre_cargo AS cargo_nombre, c.tipo AS cargo_tipo,
                u.id_usuario, u.hash_clave, u.activo,
                r.id_rol, r.nombre_rol
            FROM empleado e
            JOIN usuario u ON e.id_empleado = u.id_empleado
            JOIN rol r ON u.id_rol = r.id_rol
            JOIN cargo c ON e.id_cargo = c.id_cargo
            WHERE e.dni = %s AND e.estado_registro = TRUE
        """

        try:
            # 3. Cursor buffered dentro del try para proteger el Singleton
            cursor = conexion.cursor(dictionary=True, buffered=True)
            cursor.execute(query, (dni_limpio,))
            resultado = cursor.fetchone()

            if not resultado:
                simular_verificacion(password_plano)  # iguala el tiempo de respuesta
                logger.info("Fallo de autenticación: usuario no encontrado o dado de baja.")
                return None

            # 4. Validar si el usuario está inactivo en el sistema
            if not bool(resultado.get('activo')):
                simular_verificacion(password_plano)  # iguala el tiempo de respuesta
                logger.warning("Acceso denegado: cuenta desactivada (id_empleado=%s).", resultado["id_empleado"])
                return None

            # 5. Verificación de hash seguro
            hash_guardado = resultado.get('hash_clave')
            if not hash_guardado:
                simular_verificacion(password_plano)  # iguala el tiempo de respuesta
            if hash_guardado and verificar_password(password_plano, hash_guardado):
                logger.info("Autenticación exitosa (id_empleado=%s, rol=%s).", resultado["id_empleado"], resultado["nombre_rol"])
                usuario_sesion = resultado.copy()
                usuario_sesion.pop('hash_clave', None)
                return usuario_sesion
            else:
                logger.info("Fallo de autenticación: contraseña incorrecta (id_empleado=%s).", resultado["id_empleado"])
                return None

        except DBError as e:
            logger.error("ERROR DAO [autenticar]: error al consultar la base de datos: %s", e)
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except DBError:
                    pass
