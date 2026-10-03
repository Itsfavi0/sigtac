from dao.db_connection import ConexionBD
from utils.security import verificar_password


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
        conexion = ConexionBD().obtener_conexion()
        if not conexion:
            return None

        # Usamos dictionary=True para que las filas de MySQL se mapeen directamente como diccionarios
        cursor = conexion.cursor(dictionary=True)

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
            cursor.execute(query, (dni,))
            resultado = cursor.fetchone()

            if not resultado:
                print(f"LOG: No se encontró ningún empleado activo con el DNI: {dni}")
                return None

            # Auditoría técnica / Regla de negocio: Validar si el usuario está inactivo
            if not resultado['activo']:
                print(f"LOG: Acceso denegado. La cuenta del DNI {dni} se encuentra desactivada.")
                return None

            # Verificación del hash de la contraseña con bcrypt
            hash_guardado = resultado['hash_clave']
            if verificar_password(password_plano, hash_guardado):
                print(
                    f"LOG: ¡Autenticación exitosa para {resultado['nombres']} {resultado['apellidos']} (Rol: {resultado['nombre_rol']})!")
                # Retornamos el diccionario limpio (removiendo el hash por seguridad)
                usuario_sesion = resultado.copy()
                usuario_sesion.pop('hash_clave', None)
                return usuario_sesion
            else:
                print("LOG: Contraseña incorrecta.")
                return None

        except Exception as e:
            print(f"ERROR DAO [autenticar]: Ocurrió un error al consultar la base de datos. Detalles: {e}")
            return None
        finally:
            cursor.close()


# ==========================================
# PRUEBA RÁPIDA DEL DAO DE USUARIO
# ==========================================
if __name__ == "__main__":
    print("--- PRUEBA DE AUTENTICACIÓN (LOGIN) ---")

    # Probamos con el Administrador que configuramos en el seed.sql (DNI: 11111111, Clave: admin123)
    dni_prueba = "11111111"
    clave_prueba = "admin123"

    print(f"Intentando iniciar sesión con DNI: {dni_prueba} y Clave: {clave_prueba}")
    sesion = UsuarioDAO.autenticar(dni_prueba, clave_prueba)

    if sesion:
        print("Datos de sesión obtenidos con éxito:")
        for k, v in sesion.items():
            print(f"  - {k}: {v}")
    else:
        print("La prueba de autenticación falló.")