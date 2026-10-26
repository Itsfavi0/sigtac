import logging
from dao.base_dao import BaseDAO
from models.excepciones import PersistenciaError, ReglaNegocioError
from models.documento import DocumentoIdentidad
from models.permisos import Rol
from models.usuario import CuentaUsuario
from utils.security import simular_verificacion, verificar_password

logger = logging.getLogger(__name__)

# Bloqueo temporal tras intentos fallidos consecutivos
MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15


class UsuarioDAO(BaseDAO):
    """
    DAO para gestionar el acceso, autenticación y validación de usuarios
    cruzando las tablas empleado, usuario y rol de nuestra base de datos.

    A diferencia del resto de DAO, autenticar() no propaga los errores de BD:
    ante cualquier fallo devuelve None, para no revelar la causa del rechazo.

    La administración de cuentas (listar, crear, cambiar rol, activar, restablecer la clave) sí
    propaga los errores, como los demás DAO. Ningún método devuelve ni registra el hash de la clave.
    """

    _SELECT_CUENTA = """
        SELECT u.id_usuario, u.id_empleado, e.nombres, e.apellidos, c.nombre_cargo, r.nombre_rol, u.activo,
               u.intentos_fallidos, (u.bloqueado_hasta IS NOT NULL AND u.bloqueado_hasta > NOW()) AS bloqueada
        FROM usuario u
        JOIN empleado e ON u.id_empleado = e.id_empleado
        JOIN cargo c ON e.id_cargo = c.id_cargo
        JOIN rol r ON u.id_rol = r.id_rol
    """
    # El id del rol se obtiene de su nombre (UNIQUE): los ids dependen del orden del seed.
    _ID_ROL = "(SELECT id_rol FROM rol WHERE nombre_rol = %s)"

    @staticmethod
    def _ejecutar_actualizacion(sentencia: str, parametros: tuple, descripcion: str) -> None:
        """Ejecuta un UPDATE auxiliar; un fallo aquí se registra pero no interrumpe el login."""
        try:
            UsuarioDAO._ejecutar(sentencia, parametros)
        except PersistenciaError as e:
            logger.error("ERROR DAO [autenticar]: no se pudo %s: %s", descripcion, e)

    @staticmethod
    def _reiniciar_intentos(id_usuario: int) -> None:
        UsuarioDAO._ejecutar_actualizacion(
            "UPDATE usuario SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id_usuario = %s",
            (id_usuario,),
            "reiniciar los intentos fallidos",
        )

    @staticmethod
    def _registrar_fallo(id_usuario: int) -> None:
        # Se incrementa en la propia BD (atómico). El orden importa: bloqueado_hasta se calcula
        # primero, con el contador anterior; MySQL/MariaDB evalúan las asignaciones de izquierda a derecha.
        UsuarioDAO._ejecutar_actualizacion(
            """
            UPDATE usuario
            SET bloqueado_hasta = IF(intentos_fallidos + 1 >= %s, NOW() + INTERVAL %s MINUTE, bloqueado_hasta),
                intentos_fallidos = intentos_fallidos + 1
            WHERE id_usuario = %s
            """,
            (MAX_INTENTOS_FALLIDOS, MINUTOS_BLOQUEO, id_usuario),
            "registrar el intento fallido",
        )

    @staticmethod
    def autenticar(tipo_documento: str, num_documento: str, password_plano: str) -> dict | None:
        """
        Busca un empleado por su documento (tipo y número), verifica que su acceso esté activo (activo = True),
        compara la clave plana con el hash almacenado usando bcrypt y retorna los datos de sesión.
        """
        # 1. Validación y saneamiento de entradas
        if not password_plano or not isinstance(password_plano, str):
            logger.warning("Intento de autenticación con credenciales nulas o en formato inválido.")
            return None

        # DocumentoIdentidad valida el tipo y el formato del número (y lo limpia de espacios).
        try:
            documento = DocumentoIdentidad(tipo_documento, num_documento)
        except ValueError:
            logger.warning("Intento de autenticación con documento de formato inválido.")
            return None

        # 2. Consulta: empleado + tipo de documento + usuario + rol + cargo
        query = """
            SELECT 
                e.id_empleado, td.codigo AS tipo_documento, e.num_documento, e.nombres, e.apellidos, e.colegiatura, 
                c.nombre_cargo AS cargo_nombre, c.tipo AS cargo_tipo,
                u.id_usuario, u.hash_clave, u.activo,
                u.intentos_fallidos, u.bloqueado_hasta,
                (u.bloqueado_hasta IS NOT NULL AND u.bloqueado_hasta > NOW()) AS bloqueada,
                r.id_rol, r.nombre_rol
            FROM empleado e
            JOIN tipo_documento td ON e.id_tipo_documento = td.id_tipo_documento
            JOIN usuario u ON e.id_empleado = u.id_empleado
            JOIN rol r ON u.id_rol = r.id_rol
            JOIN cargo c ON e.id_cargo = c.id_cargo
            WHERE td.codigo = %s AND e.num_documento = %s AND e.estado_registro = TRUE
        """
        try:
            resultado = UsuarioDAO._consultar_uno(query, (documento.tipo.value, documento.numero))
        except PersistenciaError as e:  # incluye ConexionBDError
            logger.error("ERROR DAO [autenticar]: no se pudo consultar el usuario: %s", e)
            return None

        if not resultado:
            simular_verificacion(password_plano)  # iguala el tiempo de respuesta
            logger.info("Fallo de autenticación: usuario no encontrado o dado de baja.")
            return None

        # 3. Validar si el usuario está inactivo en el sistema
        if not bool(resultado.get('activo')):
            simular_verificacion(password_plano)  # iguala el tiempo de respuesta
            logger.warning("Acceso denegado: cuenta desactivada (id_empleado=%s).", resultado["id_empleado"])
            return None

        # 4. Cuenta bloqueada temporalmente por intentos fallidos
        if resultado.get('bloqueada'):
            simular_verificacion(password_plano)  # iguala el tiempo de respuesta
            logger.warning("Acceso denegado: cuenta bloqueada temporalmente (id_empleado=%s).", resultado["id_empleado"])
            return None
        if resultado.get('bloqueado_hasta') is not None:
            # El bloqueo ya venció: se empieza de cero antes de evaluar este intento
            UsuarioDAO._reiniciar_intentos(resultado['id_usuario'])
            resultado['intentos_fallidos'] = 0

        # 5. Verificación de hash seguro
        hash_guardado = resultado.get('hash_clave')
        if not hash_guardado:
            simular_verificacion(password_plano)  # iguala el tiempo de respuesta
        if hash_guardado and verificar_password(password_plano, hash_guardado):
            logger.info("Autenticación exitosa (id_empleado=%s, rol=%s).", resultado["id_empleado"], resultado["nombre_rol"])
            if resultado.get('intentos_fallidos'):
                UsuarioDAO._reiniciar_intentos(resultado['id_usuario'])
            usuario_sesion = resultado.copy()
            for campo in ('hash_clave', 'intentos_fallidos', 'bloqueado_hasta', 'bloqueada'):
                usuario_sesion.pop(campo, None)
            return usuario_sesion
        else:
            logger.info("Fallo de autenticación: contraseña incorrecta (id_empleado=%s).", resultado["id_empleado"])
            if hash_guardado:
                UsuarioDAO._registrar_fallo(resultado['id_usuario'])
            return None

    # ---- Administración de cuentas

    @staticmethod
    def _validar_hash(hash_clave) -> str:
        # Defensa: este DAO nunca debe guardar una clave en texto plano por error.
        if not isinstance(hash_clave, str) or not hash_clave.startswith("$2"):
            raise ValueError("hash_clave debe ser un hash bcrypt.")
        return hash_clave

    @staticmethod
    def _a_cuenta(fila: dict) -> CuentaUsuario:
        return CuentaUsuario(
            fila["id_usuario"], fila["id_empleado"], fila["nombres"], fila["apellidos"], fila["nombre_cargo"],
            Rol(fila["nombre_rol"]),  # ValueError si el rol de la BD no existe en el Enum
            activo=bool(fila["activo"]), bloqueada=bool(fila["bloqueada"]),  # MySQL devuelve BOOLEAN como 0/1
            intentos_fallidos=fila["intentos_fallidos"],
        )

    @staticmethod
    def listar_cuentas() -> list[CuentaUsuario]:
        """Todas las cuentas (activas y desactivadas), ordenadas por apellidos y nombres."""
        filas = UsuarioDAO._consultar_varios(
            UsuarioDAO._SELECT_CUENTA + " ORDER BY e.apellidos, e.nombres, u.id_usuario"
        )
        return [UsuarioDAO._a_cuenta(fila) for fila in filas]

    @staticmethod
    def buscar_cuenta(id_usuario: int) -> CuentaUsuario | None:
        """La cuenta con ese id, o None si no existe."""
        UsuarioDAO._validar_id(id_usuario, "id_usuario")
        fila = UsuarioDAO._consultar_uno(UsuarioDAO._SELECT_CUENTA + " WHERE u.id_usuario = %s", (id_usuario,))
        return UsuarioDAO._a_cuenta(fila) if fila else None

    @staticmethod
    def listar_empleados_sin_cuenta() -> list[dict]:
        """Empleados activos que aún no tienen cuenta: [{"id_empleado", "nombres", "apellidos", "nombre_cargo"}]."""
        return UsuarioDAO._consultar_varios(
            """
            SELECT e.id_empleado, e.nombres, e.apellidos, c.nombre_cargo
            FROM empleado e
            JOIN cargo c ON e.id_cargo = c.id_cargo
            LEFT JOIN usuario u ON u.id_empleado = e.id_empleado
            WHERE u.id_usuario IS NULL AND e.estado_registro = TRUE
            ORDER BY e.apellidos, e.nombres
            """
        )

    @staticmethod
    def empleado_activo(id_empleado: int) -> bool:
        """True si el empleado existe y no está dado de baja."""
        UsuarioDAO._validar_id(id_empleado, "id_empleado")
        return UsuarioDAO._consultar_uno(
            "SELECT 1 FROM empleado WHERE id_empleado = %s AND estado_registro = TRUE", (id_empleado,)
        ) is not None

    @staticmethod
    def crear_cuenta(id_empleado: int, rol: Rol | str, hash_clave: str) -> int:
        """
        Crea la cuenta de un empleado y devuelve su id. `hash_clave` ya viene calculado con bcrypt
        (utils/security.py). Si el empleado ya tiene cuenta, el UNIQUE de la BD lanza RegistroDuplicadoError.
        """
        UsuarioDAO._validar_id(id_empleado, "id_empleado")
        rol = Rol(rol)
        id_nuevo = UsuarioDAO._insertar(
            "INSERT INTO usuario (id_empleado, id_rol, hash_clave) VALUES (%s, " + UsuarioDAO._ID_ROL + ", %s)",
            (id_empleado, rol.value, UsuarioDAO._validar_hash(hash_clave)),
        )
        logger.info("Cuenta creada (id_usuario=%s, id_empleado=%s, rol=%s).", id_nuevo, id_empleado, rol.value)
        return id_nuevo

    @staticmethod
    def cambiar_rol(cuenta: CuentaUsuario, rol_anterior: Rol | str) -> None:
        """
        Guarda el rol actual de la cuenta (antes se llama a cuenta.cambiar_rol()). UPDATE condicional:
        si en la BD el rol ya no es `rol_anterior` (otro administrador lo cambió), lanza ReglaNegocioError.
        """
        if not isinstance(cuenta, CuentaUsuario):
            raise ValueError("cuenta debe ser una CuentaUsuario.")
        rol_anterior = Rol(rol_anterior)
        if cuenta.rol == rol_anterior:
            raise ValueError("La cuenta no cambió de rol.")
        filas = UsuarioDAO._ejecutar(
            "UPDATE usuario SET id_rol = " + UsuarioDAO._ID_ROL
            + " WHERE id_usuario = %s AND id_rol = " + UsuarioDAO._ID_ROL,
            (cuenta.rol.value, UsuarioDAO._validar_id(cuenta.id_usuario, "id_usuario"), rol_anterior.value),
        )
        if filas == 0:
            raise ReglaNegocioError("El rol de la cuenta ya no es el que se leyó: otro usuario lo cambió.")
        logger.info("Rol cambiado (id_usuario=%s): %s -> %s.", cuenta.id_usuario, rol_anterior.value, cuenta.rol.value)

    @staticmethod
    def cambiar_activo(cuenta: CuentaUsuario) -> None:
        """
        Guarda si la cuenta está activa (antes se llama a cuenta.activar() o cuenta.desactivar()).
        UPDATE condicional: si en la BD ya tenía ese valor (otro administrador llegó antes), lanza
        ReglaNegocioError.
        """
        if not isinstance(cuenta, CuentaUsuario):
            raise ValueError("cuenta debe ser una CuentaUsuario.")
        filas = UsuarioDAO._ejecutar(
            "UPDATE usuario SET activo = %s WHERE id_usuario = %s AND activo = %s",
            (cuenta.activo, UsuarioDAO._validar_id(cuenta.id_usuario, "id_usuario"), not cuenta.activo),
        )
        if filas == 0:
            raise ReglaNegocioError("Otro usuario ya cambió el estado de esta cuenta.")
        logger.info("Cuenta %s (id_usuario=%s).", "activada" if cuenta.activo else "desactivada", cuenta.id_usuario)

    @staticmethod
    def restablecer_clave(id_usuario: int, hash_clave: str) -> None:
        """Guarda una clave nueva (ya convertida en hash) y quita el bloqueo por intentos fallidos."""
        UsuarioDAO._validar_id(id_usuario, "id_usuario")
        filas = UsuarioDAO._ejecutar(
            "UPDATE usuario SET hash_clave = %s, intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id_usuario = %s",
            (UsuarioDAO._validar_hash(hash_clave), id_usuario),
        )
        if filas == 0:
            raise ReglaNegocioError("La cuenta no existe.")
        logger.info("Clave restablecida (id_usuario=%s).", id_usuario)

    @staticmethod
    def desbloquear(id_usuario: int) -> None:
        """Pone en cero los intentos fallidos y quita el bloqueo temporal (antes: cuenta.desbloquear())."""
        UsuarioDAO._validar_id(id_usuario, "id_usuario")
        # A diferencia de _reiniciar_intentos (parte del login), aquí un fallo de BD sí se propaga.
        filas = UsuarioDAO._ejecutar(
            "UPDATE usuario SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id_usuario = %s", (id_usuario,)
        )
        if filas == 0:
            raise ReglaNegocioError("La cuenta no existe.")
        logger.info("Cuenta desbloqueada (id_usuario=%s).", id_usuario)
