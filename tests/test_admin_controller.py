from datetime import date, datetime

import pytest

from controllers import admin_controller
from controllers.admin_controller import AdminController
from models.auditoria import AccionAuditoria
from models.excepciones import RegistroDuplicadoError, ReglaNegocioError, UsuarioSinPermisoError
from models.permisos import Rol
from models.usuario import CuentaUsuario

CLAVE = "NuevaClave2026"
HASH = "$2b$12$hash-de-prueba"


def cuenta(id_usuario=3, rol=Rol.ENFERMERO, activo=True, bloqueada=False, intentos=0):
    return CuentaUsuario(id_usuario, 3, "Ana", "Pérez", "Licenciado(a) en Enfermería", rol, activo,
                         bloqueada=bloqueada, intentos_fallidos=intentos)


@pytest.fixture
def datos(capa_datos, monkeypatch):
    # bcrypt es lento y no es lo que se prueba aquí: se reemplaza por un hash fijo.
    monkeypatch.setattr(admin_controller, "generar_hash", lambda clave: HASH)
    return capa_datos(admin_controller, "UsuarioDAO", "AuditoriaDAO")


@pytest.fixture
def ctrl(sesion_de):
    return AdminController(sesion_de(Rol.ADMINISTRADOR, id_usuario=1, id_empleado=1))


# ---- Permisos

OPERACIONES = [
    ("listar_cuentas", ()), ("listar_empleados_sin_cuenta", ()), ("listar_roles", ()),
    ("bitacora", (date(2026, 10, 1), date(2026, 10, 31))), ("historial_de_registro", ("paciente", 1)),
    ("crear_cuenta", (3, Rol.ENFERMERO, CLAVE)), ("cambiar_rol", (3, Rol.MEDICO)), ("desactivar", (3,)),
    ("activar", (3,)), ("restablecer_clave", (3, CLAVE)), ("desbloquear", (3,)),
]


@pytest.mark.parametrize("metodo, args", OPERACIONES)
@pytest.mark.parametrize("rol", [Rol.JEFE_GUARDIA, Rol.MEDICO, Rol.ENFERMERO, Rol.LIMPIEZA])
def test_solo_el_administrador_administra(datos, sesion_de, metodo, args, rol):
    with pytest.raises(UsuarioSinPermisoError):
        getattr(AdminController(sesion_de(rol)), metodo)(*args)
    assert datos.llamadas() == []


@pytest.mark.parametrize("metodo, args", OPERACIONES)
def test_con_la_sesion_cerrada_no_se_opera(datos, sesion_de, metodo, args):
    sesion = sesion_de(Rol.ADMINISTRADOR)
    ctrl = AdminController(sesion)
    sesion.cerrar()
    with pytest.raises(UsuarioSinPermisoError, match="sesión activa"):
        getattr(ctrl, metodo)(*args)
    assert datos.llamadas() == []


# ---- Consultas

def test_listar_roles(datos, ctrl):
    assert ctrl.listar_roles() == list(Rol)


def test_bitacora_incluye_los_dos_dias(datos, ctrl):
    datos["AuditoriaDAO"].listar.return_value = ["registro"]
    assert ctrl.bitacora(date(2026, 10, 1), date(2026, 10, 1), tabla="paciente", limite=50) == ["registro"]
    datos["AuditoriaDAO"].listar.assert_called_once_with(
        datetime(2026, 10, 1), datetime(2026, 10, 2), tabla="paciente", id_usuario=None, limite=50)


@pytest.mark.parametrize("desde, hasta", [
    (date(2026, 10, 2), date(2026, 10, 1)),
    (datetime(2026, 10, 1, 8, 0), date(2026, 10, 2)),
    ("2026-10-01", date(2026, 10, 2)),
])
def test_bitacora_con_periodo_invalido(datos, ctrl, desde, hasta):
    with pytest.raises(ValueError):
        ctrl.bitacora(desde, hasta)
    datos["AuditoriaDAO"].listar.assert_not_called()


def test_historial_de_registro(datos, ctrl):
    ctrl.historial_de_registro("paciente", 4)
    datos["AuditoriaDAO"].listar_por_registro.assert_called_once_with("paciente", 4)


# ---- Crear cuenta

def test_crear_cuenta_guarda_el_hash_y_audita_sin_la_clave(datos, ctrl):
    datos["UsuarioDAO"].empleado_activo.return_value = True
    datos["UsuarioDAO"].crear_cuenta.return_value = 7
    datos["UsuarioDAO"].buscar_cuenta.return_value = "cuenta creada"
    assert ctrl.crear_cuenta(3, "Enfermero de Triaje", CLAVE) == "cuenta creada"
    datos["UsuarioDAO"].crear_cuenta.assert_called_once_with(3, Rol.ENFERMERO, HASH)
    assert datos.auditoria().args == (1, "usuario", AccionAuditoria.INSERT, 7, {"id_empleado": 3, "rol": "Enfermero de Triaje"})
    assert CLAVE not in repr(datos.registro.mock_calls)
    assert datos.llamadas()[-1] == "commit"


@pytest.mark.parametrize("clave", ["corta1", "solamenteletras", "1234567890", " Espacio123", None])
def test_crear_cuenta_con_clave_debil_no_toca_la_bd(datos, ctrl, clave):
    with pytest.raises(ValueError, match="clave"):
        ctrl.crear_cuenta(3, Rol.ENFERMERO, clave)
    assert datos.llamadas() == []


def test_crear_cuenta_con_rol_inexistente(datos, ctrl):
    with pytest.raises(ValueError, match="Rol"):
        ctrl.crear_cuenta(3, "Superusuario", CLAVE)
    assert datos.llamadas() == []


def test_crear_cuenta_de_un_empleado_dado_de_baja(datos, ctrl):
    datos["UsuarioDAO"].empleado_activo.return_value = False
    with pytest.raises(ReglaNegocioError, match="dado de baja"):
        ctrl.crear_cuenta(6, Rol.MEDICO, CLAVE)
    datos["UsuarioDAO"].crear_cuenta.assert_not_called()
    datos["AuditoriaDAO"].registrar.assert_not_called()


def test_crear_una_segunda_cuenta_para_el_mismo_empleado(datos, ctrl):
    datos["UsuarioDAO"].empleado_activo.return_value = True
    datos["UsuarioDAO"].crear_cuenta.side_effect = RegistroDuplicadoError("Ya existe")
    with pytest.raises(RegistroDuplicadoError):
        ctrl.crear_cuenta(3, Rol.ENFERMERO, CLAVE)
    datos["AuditoriaDAO"].registrar.assert_not_called()
    assert datos.llamadas()[-1] == "rollback"


# ---- Rol y activación

def test_cambiar_rol(datos, ctrl):
    datos["UsuarioDAO"].buscar_cuenta.return_value = cuenta()
    ctrl.cambiar_rol(3, Rol.MEDICO)
    guardada, anterior = datos["UsuarioDAO"].cambiar_rol.call_args.args
    assert (guardada.rol, anterior) == (Rol.MEDICO, Rol.ENFERMERO)
    assert datos.auditoria().args == (1, "usuario", AccionAuditoria.UPDATE, 3, {
        "rol_anterior": "Enfermero de Triaje", "rol_nuevo": "Médico de Emergencia",
    })


def test_cambiar_al_mismo_rol(datos, ctrl):
    datos["UsuarioDAO"].buscar_cuenta.return_value = cuenta()
    with pytest.raises(ReglaNegocioError, match="ya tiene el rol"):
        ctrl.cambiar_rol(3, Rol.ENFERMERO)
    assert datos.escrituras() == []


@pytest.mark.parametrize("metodo, args", [("cambiar_rol", (1, Rol.MEDICO)), ("desactivar", (1,))])
def test_el_administrador_no_se_modifica_a_si_mismo(datos, ctrl, metodo, args):
    with pytest.raises(ReglaNegocioError, match="otro administrador"):
        getattr(ctrl, metodo)(*args)
    assert datos.llamadas() == []


def test_desactivar_una_cuenta(datos, ctrl):
    datos["UsuarioDAO"].buscar_cuenta.return_value = cuenta()
    ctrl.desactivar(3)
    assert not datos["UsuarioDAO"].cambiar_activo.call_args.args[0].activo
    assert datos.auditoria().args == (1, "usuario", AccionAuditoria.UPDATE, 3, {"activo": False})


def test_activar_una_cuenta(datos, ctrl):
    datos["UsuarioDAO"].buscar_cuenta.return_value = cuenta(activo=False)
    ctrl.activar(3)
    assert datos["UsuarioDAO"].cambiar_activo.call_args.args[0].activo
    assert datos.auditoria().args[4] == {"activo": True}


@pytest.mark.parametrize("metodo, activo", [("activar", True), ("desactivar", False)])
def test_activar_o_desactivar_sin_cambio(datos, ctrl, metodo, activo):
    datos["UsuarioDAO"].buscar_cuenta.return_value = cuenta(activo=activo)
    with pytest.raises(ReglaNegocioError, match="ya está"):
        getattr(ctrl, metodo)(3)
    assert datos.escrituras() == []


@pytest.mark.parametrize("metodo, args", [("cambiar_rol", (3, Rol.MEDICO)), ("activar", (3,)),
                                          ("restablecer_clave", (3, CLAVE)), ("desbloquear", (3,))])
def test_cuenta_inexistente(datos, ctrl, metodo, args):
    datos["UsuarioDAO"].buscar_cuenta.return_value = None
    with pytest.raises(ReglaNegocioError, match="no existe"):
        getattr(ctrl, metodo)(*args)
    assert datos.escrituras() == []


# ---- Clave y bloqueo

def test_restablecer_clave(datos, ctrl):
    datos["UsuarioDAO"].buscar_cuenta.return_value = cuenta(bloqueada=True)
    ctrl.restablecer_clave(3, CLAVE)
    datos["UsuarioDAO"].restablecer_clave.assert_called_once_with(3, HASH)
    assert datos.auditoria().args == (1, "usuario", AccionAuditoria.UPDATE, 3, {"clave_restablecida": True})
    assert CLAVE not in repr(datos.registro.mock_calls)


def test_restablecer_con_clave_debil_no_toca_la_bd(datos, ctrl):
    with pytest.raises(ValueError):
        ctrl.restablecer_clave(3, "abc")
    assert datos.llamadas() == []


def test_desbloquear(datos, ctrl):
    datos["UsuarioDAO"].buscar_cuenta.return_value = cuenta(bloqueada=True, intentos=5)
    ctrl.desbloquear(3)
    datos["UsuarioDAO"].desbloquear.assert_called_once_with(3)
    assert datos.auditoria().args[4] == {"desbloqueada": True}


def test_desbloquear_una_cuenta_sin_bloqueo(datos, ctrl):
    datos["UsuarioDAO"].buscar_cuenta.return_value = cuenta()
    with pytest.raises(ReglaNegocioError, match="no está bloqueada"):
        ctrl.desbloquear(3)
    assert datos.escrituras() == []
