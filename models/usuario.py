from models.excepciones import ReglaNegocioError
from models.permisos import Rol

# bcrypt solo usa los primeros 72 bytes de la clave (y bcrypt 5 rechaza las más largas): una clave
# más larga daría una falsa sensación de seguridad, así que se limita aquí, con un mensaje claro.
LONGITUD_MINIMA_CLAVE = 8
MAXIMO_BYTES_CLAVE = 72


def validar_clave_nueva(clave) -> str:
    """
    Política de claves para crear o restablecer una cuenta: al menos 8 caracteres, con letras y
    números, y como máximo 72 bytes (límite de bcrypt). Lanza ValueError; nunca incluye la clave en
    el mensaje.
    """
    if not isinstance(clave, str):
        raise ValueError("La clave debe ser un texto.")
    if len(clave) < LONGITUD_MINIMA_CLAVE:
        raise ValueError(f"La clave debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres.")
    if len(clave.encode("utf-8")) > MAXIMO_BYTES_CLAVE:
        raise ValueError(f"La clave no puede superar los {MAXIMO_BYTES_CLAVE} bytes.")
    if clave != clave.strip():
        raise ValueError("La clave no puede empezar ni terminar con espacios.")
    if not any(c.isalpha() for c in clave) or not any(c.isdigit() for c in clave):
        raise ValueError("La clave debe combinar letras y números.")
    return clave


def validar_rol(rol) -> Rol:
    try:
        return Rol(rol)
    except ValueError:
        raise ValueError("Rol no reconocido.") from None


class CuentaUsuario:
    """
    Cuenta de acceso de un empleado (tabla usuario): su rol y si puede iniciar sesión. No guarda la
    clave ni su hash: esos solo los maneja UsuarioDAO.

    El modelo decide las transiciones (activar, desactivar, cambiar de rol, desbloquear) y el DAO las
    guarda con un UPDATE condicional, como con las camas y los episodios.
    """

    def __init__(self, id_usuario: int, id_empleado: int, nombres: str, apellidos: str, cargo: str,
                 rol: Rol | str, activo: bool, bloqueada: bool = False, intentos_fallidos: int = 0):
        for nombre, valor in (("id_usuario", id_usuario), ("id_empleado", id_empleado)):
            if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
                raise ValueError(f"{nombre} debe ser un entero positivo.")
        if not isinstance(activo, bool) or not isinstance(bloqueada, bool):
            raise ValueError("activo y bloqueada deben ser True o False.")
        self._id_usuario = id_usuario
        self._id_empleado = id_empleado
        self._nombres = nombres
        self._apellidos = apellidos
        self._cargo = cargo
        self._rol = validar_rol(rol)
        self._activo = activo
        self._bloqueada = bloqueada
        self._intentos_fallidos = intentos_fallidos

    @property
    def id_usuario(self): return self._id_usuario

    @property
    def id_empleado(self): return self._id_empleado

    @property
    def nombres(self): return self._nombres

    @property
    def apellidos(self): return self._apellidos

    @property
    def nombre_completo(self) -> str:
        return f"{self._nombres} {self._apellidos}"

    @property
    def cargo(self): return self._cargo

    @property
    def rol(self): return self._rol

    @property
    def activo(self): return self._activo

    @property
    def bloqueada(self) -> bool:
        """True si la cuenta está bloqueada temporalmente por intentos fallidos."""
        return self._bloqueada

    @property
    def intentos_fallidos(self): return self._intentos_fallidos

    def activar(self):
        if self._activo:
            raise ReglaNegocioError("La cuenta ya está activa.")
        self._activo = True

    def desactivar(self):
        """El empleado deja de poder iniciar sesión; la cuenta y su historial de auditoría se conservan."""
        if not self._activo:
            raise ReglaNegocioError("La cuenta ya está desactivada.")
        self._activo = False

    def cambiar_rol(self, rol: Rol | str):
        rol = validar_rol(rol)
        if rol == self._rol:
            raise ReglaNegocioError(f"La cuenta ya tiene el rol {rol}.")
        self._rol = rol

    def desbloquear(self):
        """Quita el bloqueo por intentos fallidos sin esperar los 15 minutos."""
        if not self._bloqueada and not self._intentos_fallidos:
            raise ReglaNegocioError("La cuenta no está bloqueada.")
        self._bloqueada = False
        self._intentos_fallidos = 0

    def __repr__(self):
        # Sin nombres: el repr puede terminar en un log
        return f"CuentaUsuario(id_usuario={self._id_usuario}, rol={self._rol!r}, activo={self._activo})"
