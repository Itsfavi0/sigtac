import logging
from mysql.connector import Error as DBError
from dao.db_connection import ConexionBD
from utils.security import verificar_password

logger = logging.getLogger(__name__)


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

        # 2. Conexión con la base de datos
        conexion = ConexionBD().obtener_conexion()
        if not conexion:
            logger.error("No se pudo obtener una conexión válida a la base de datos.")
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
                logger.info(f"Fallo de autenticación para DNI: {dni_limpio} (Usuario no encontrado o dado de baja).")
                return None

            # 4. Validar si el usuario está inactivo en el sistema
            if not bool(resultado.get('activo')):
                logger.warning(f"Acceso denegado: La cuenta vinculada al DNI {dni_limpio} está desactivada.")
                return None

            # 5. Verificación de hash seguro
            hash_guardado = resultado.get('hash_clave')
            if hash_guardado and verificar_password(password_plano, hash_guardado):
                logger.info(f"Autenticación exitosa: {resultado['nombres']} {resultado['apellidos']} ({resultado['nombre_rol']}).")
                usuario_sesion = resultado.copy()
                usuario_sesion.pop('hash_clave', None)
                return usuario_sesion
            else:
                logger.info(f"Fallo de autenticación para DNI: {dni_limpio} (Contraseña incorrecta).")
                return None

        except DBError as e:
            logger.error(f"ERROR DAO [autenticar]: Ocurrió un error al consultar la base de datos. Detalles: {e}")
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except DBError:
                    pass
