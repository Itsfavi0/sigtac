import logging

from dao.usuario_dao import UsuarioDAO
from models.excepciones import AutenticacionError, UsuarioSinPermisoError
from models.permisos import Permiso, tiene_permiso

logger = logging.getLogger(__name__)


class Sesion:
    """
    Usuario que inició sesión. Los demás controladores la reciben al crearse (inyección) y la usan para
    comprobar permisos y para registrar quién hizo cada operación en la auditoría.

    Solo guarda lo necesario: ni la clave, ni el hash, ni el número de documento. Al cerrar la sesión se
    invalida, y todo controlador que aún la tenga deja de poder operar.
    """

    def __init__(self, id_usuario: int, id_empleado: int, nombre_rol: str, nombres: str, apellidos: str,
                 cargo: str | None = None):
        for nombre, valor in (("id_usuario", id_usuario), ("id_empleado", id_empleado)):
            # bool es subclase de int: True no es un id válido
            if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
                raise ValueError(f"{nombre} debe ser un entero positivo.")
        if not isinstance(nombre_rol, str) or not nombre_rol.strip():
            raise ValueError("La sesión necesita el nombre del rol.")
        self._id_usuario = id_usuario
        self._id_empleado = id_empleado
        self._nombre_rol = nombre_rol
        self._nombres = nombres
        self._apellidos = apellidos
        self._cargo = cargo
        self._activa = True

    @property
    def id_usuario(self): return self._id_usuario

    @property
    def id_empleado(self): return self._id_empleado

    @property
    def nombre_rol(self): return self._nombre_rol

    @property
    def nombres(self): return self._nombres

    @property
    def apellidos(self): return self._apellidos

    @property
    def cargo(self): return self._cargo

    @property
    def activa(self): return self._activa

    @property
    def nombre_completo(self) -> str:
        return f"{self._nombres} {self._apellidos}"

    def puede(self, permiso: Permiso | str) -> bool:
        """Indica si el rol tiene el permiso (las vistas lo usan para mostrar u ocultar opciones)."""
        return tiene_permiso(self._nombre_rol, permiso) and self._activa

    def cerrar(self):
        self._activa = False

    def __repr__(self):
        # Sin nombres: el repr puede terminar en un log
        estado = "activa" if self._activa else "cerrada"
        return f"Sesion(id_usuario={self._id_usuario}, rol={self._nombre_rol!r}, {estado})"


def exigir_permiso(sesion: Sesion | None, permiso: Permiso | str) -> Sesion:
    """
    Punto único donde los controladores comprueban un permiso antes de operar. Devuelve la sesión
    para usarla a continuación (p. ej. su id_usuario en la auditoría).

    Lanza UsuarioSinPermisoError si no hay sesión, si está cerrada o si el rol no tiene el permiso,
    y ValueError si el permiso no existe (error de programación).
    """
    # Se valida primero: un permiso mal escrito debe fallar siempre, haya sesión o no
    try:
        permiso = Permiso(permiso)
    except ValueError:
        raise ValueError("Permiso no reconocido.") from None
    if sesion is None or not sesion.activa:
        raise UsuarioSinPermisoError("No hay una sesión activa. Inicie sesión de nuevo.")
    if not tiene_permiso(sesion.nombre_rol, permiso):
        logger.warning("Permiso denegado (id_usuario=%s, rol=%s, permiso=%s).",
                       sesion.id_usuario, sesion.nombre_rol, permiso)
        raise UsuarioSinPermisoError(f"Su rol ({sesion.nombre_rol}) no tiene permiso para: {permiso}.")
    return sesion


class AuthController:
    """Inicia y cierra la sesión. Hay una sola sesión activa por instancia de la aplicación."""

    MENSAJE_FALLO = "Documento o contraseña incorrectos, o la cuenta no está habilitada."

    def __init__(self):
        self._sesion = None

    @property
    def sesion(self) -> Sesion | None:
        return self._sesion

    @property
    def autenticado(self) -> bool:
        return self._sesion is not None and self._sesion.activa

    def iniciar_sesion(self, tipo_documento: str, num_documento: str, password: str) -> Sesion:
        """
        Delega la verificación en UsuarioDAO.autenticar (bcrypt, bloqueo por intentos, señuelo de
        tiempo). Si falla, lanza AutenticacionError con un mensaje genérico.

        Un nuevo intento cierra antes la sesión anterior: si falla, no queda nadie conectado.
        """
        self.cerrar_sesion()
        datos = UsuarioDAO.autenticar(tipo_documento, num_documento, password)
        if datos is None:
            raise AutenticacionError(self.MENSAJE_FALLO)
        self._sesion = self._a_sesion(datos)
        return self._sesion

    def cerrar_sesion(self):
        """Invalida la sesión actual (si la hay). Se puede llamar aunque no haya sesión."""
        if self._sesion is None:
            return
        self._sesion.cerrar()
        logger.info("Sesión cerrada (id_usuario=%s).", self._sesion.id_usuario)
        self._sesion = None

    def exigir_sesion(self) -> Sesion:
        """Devuelve la sesión activa o lanza UsuarioSinPermisoError si no la hay."""
        if not self.autenticado:
            raise UsuarioSinPermisoError("No hay una sesión activa. Inicie sesión de nuevo.")
        return self._sesion

    @staticmethod
    def _a_sesion(datos: dict) -> Sesion:
        """Único punto que convierte los datos de UsuarioDAO.autenticar en una Sesion."""
        return Sesion(
            id_usuario=datos["id_usuario"], id_empleado=datos["id_empleado"], nombre_rol=datos["nombre_rol"],
            nombres=datos["nombres"], apellidos=datos["apellidos"], cargo=datos.get("cargo_nombre"),
        )
