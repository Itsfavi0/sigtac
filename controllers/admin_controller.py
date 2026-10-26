from datetime import date, datetime, time, timedelta

from controllers.auth_controller import Sesion, exigir_permiso
from dao.auditoria_dao import AuditoriaDAO
from dao.transaccion import transaccion
from dao.usuario_dao import UsuarioDAO
from models.auditoria import AccionAuditoria
from models.excepciones import ReglaNegocioError
from models.permisos import Permiso, Rol
from models.usuario import CuentaUsuario, validar_clave_nueva, validar_rol
from utils.security import generar_hash


class AdminController:
    """
    Administración del sistema (permiso ADMINISTRACION): cuentas de usuario y consulta de la bitácora.

    Las claves llegan en texto plano solo hasta aquí: se validan con la política de models/usuario.py,
    se convierten en hash bcrypt y nunca se guardan, se devuelven ni se auditan.

    Un administrador no puede desactivar su propia cuenta ni cambiar su propio rol: así el sistema no
    se queda sin nadie que lo administre por un clic equivocado. Lo hace otro administrador.
    """

    def __init__(self, sesion: Sesion):
        self._sesion = sesion

    # ---- Consultas

    def listar_cuentas(self) -> list[CuentaUsuario]:
        exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        return UsuarioDAO.listar_cuentas()

    def listar_empleados_sin_cuenta(self) -> list[dict]:
        """Empleados activos a los que se les puede crear una cuenta."""
        exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        return UsuarioDAO.listar_empleados_sin_cuenta()

    def listar_roles(self) -> list[Rol]:
        exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        return list(Rol)

    def bitacora(self, desde: date, hasta: date, tabla: str | None = None, id_usuario: int | None = None,
                 limite: int = 200) -> list[dict]:
        """
        Registros de la bitácora entre dos días, ambos incluidos, del más reciente al más antiguo.
        Se consulta como [desde 00:00, hasta + 1 día 00:00), igual que los indicadores de ReporteController.
        """
        exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        for valor in (desde, hasta):
            if not isinstance(valor, date) or isinstance(valor, datetime):
                raise ValueError("El período se indica con fechas (date), sin hora.")
        if desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la final.")
        inicio = datetime.combine(desde, time.min)
        fin = datetime.combine(hasta + timedelta(days=1), time.min)
        return AuditoriaDAO.listar(inicio, fin, tabla=tabla, id_usuario=id_usuario, limite=limite)

    def historial_de_registro(self, tabla: str, id_registro: int) -> list[dict]:
        """Todo lo auditado sobre un registro (p. ej. un paciente), del más antiguo al más reciente."""
        exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        return AuditoriaDAO.listar_por_registro(tabla, id_registro)

    # ---- Cuentas

    def crear_cuenta(self, id_empleado: int, rol: Rol | str, clave: str) -> CuentaUsuario:
        """Crea la cuenta de un empleado activo que aún no tiene una. Devuelve la cuenta creada."""
        sesion = exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        rol = validar_rol(rol)
        hash_clave = generar_hash(validar_clave_nueva(clave))  # bcrypt tarda: se calcula fuera de la transacción
        with transaccion():
            if not UsuarioDAO.empleado_activo(id_empleado):
                raise ReglaNegocioError("El empleado no existe o está dado de baja.")
            # Si ya tiene cuenta, el UNIQUE de la BD lanza RegistroDuplicadoError.
            id_usuario = UsuarioDAO.crear_cuenta(id_empleado, rol, hash_clave)
            AuditoriaDAO.registrar(sesion.id_usuario, "usuario", AccionAuditoria.INSERT, id_usuario,
                                   {"id_empleado": id_empleado, "rol": rol.value})
            return UsuarioDAO.buscar_cuenta(id_usuario)

    def cambiar_rol(self, id_usuario: int, rol: Rol | str) -> None:
        sesion = exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        rol = validar_rol(rol)
        self._exigir_otra_cuenta(id_usuario, "cambiar su propio rol")
        with transaccion():
            cuenta = self._cargar(id_usuario)
            anterior = cuenta.rol
            cuenta.cambiar_rol(rol)
            UsuarioDAO.cambiar_rol(cuenta, anterior)
            AuditoriaDAO.registrar(sesion.id_usuario, "usuario", AccionAuditoria.UPDATE, id_usuario,
                                   {"rol_anterior": anterior.value, "rol_nuevo": cuenta.rol.value})

    def desactivar(self, id_usuario: int) -> None:
        """
        El empleado deja de poder iniciar sesión (la cuenta y su historial se conservan). Una sesión
        que ya está abierta en otra PC sigue hasta que se cierre: la sesión vive en esa aplicación.
        """
        self._exigir_otra_cuenta(id_usuario, "desactivar su propia cuenta")
        self._cambiar_activo(id_usuario, CuentaUsuario.desactivar)

    def activar(self, id_usuario: int) -> None:
        self._cambiar_activo(id_usuario, CuentaUsuario.activar)

    def _cambiar_activo(self, id_usuario: int, transicion) -> None:
        sesion = exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        with transaccion():
            cuenta = self._cargar(id_usuario)
            transicion(cuenta)
            UsuarioDAO.cambiar_activo(cuenta)
            AuditoriaDAO.registrar(sesion.id_usuario, "usuario", AccionAuditoria.UPDATE, id_usuario,
                                   {"activo": cuenta.activo})

    def restablecer_clave(self, id_usuario: int, clave_nueva: str) -> None:
        """Asigna una clave nueva (p. ej. el empleado la olvidó) y quita el bloqueo por intentos fallidos."""
        sesion = exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        hash_clave = generar_hash(validar_clave_nueva(clave_nueva))
        with transaccion():
            self._cargar(id_usuario)
            UsuarioDAO.restablecer_clave(id_usuario, hash_clave)
            # Ni la clave ni su hash van a la bitácora: solo que se cambió.
            AuditoriaDAO.registrar(sesion.id_usuario, "usuario", AccionAuditoria.UPDATE, id_usuario,
                                   {"clave_restablecida": True})

    def desbloquear(self, id_usuario: int) -> None:
        """Quita el bloqueo por intentos fallidos sin esperar los 15 minutos."""
        sesion = exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        with transaccion():
            cuenta = self._cargar(id_usuario)
            cuenta.desbloquear()
            UsuarioDAO.desbloquear(id_usuario)
            AuditoriaDAO.registrar(sesion.id_usuario, "usuario", AccionAuditoria.UPDATE, id_usuario,
                                   {"desbloqueada": True})

    # ---- Ayudantes

    def _exigir_otra_cuenta(self, id_usuario: int, accion: str) -> None:
        exigir_permiso(self._sesion, Permiso.ADMINISTRACION)
        if id_usuario == self._sesion.id_usuario:
            raise ReglaNegocioError(f"No puede {accion}: pídaselo a otro administrador.")

    @staticmethod
    def _cargar(id_usuario: int) -> CuentaUsuario:
        cuenta = UsuarioDAO.buscar_cuenta(id_usuario)
        if cuenta is None:
            raise ReglaNegocioError("La cuenta no existe.")
        return cuenta
