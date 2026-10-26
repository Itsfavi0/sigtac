import pytest

from models.excepciones import ReglaNegocioError
from models.permisos import Rol
from models.usuario import CuentaUsuario, validar_clave_nueva, validar_rol


def cuenta(**cambios):
    datos = dict(id_usuario=3, id_empleado=3, nombres="Ana", apellidos="Pérez", cargo="Licenciado(a) en Enfermería",
                 rol=Rol.ENFERMERO, activo=True)
    datos.update(cambios)
    return CuentaUsuario(**datos)


# ---- Política de claves
@pytest.mark.parametrize("clave", ["abcdefg1", "Clave2026", "contraseña1", "a1" + "x" * 70])
def test_claves_validas(clave):
    assert validar_clave_nueva(clave) == clave


@pytest.mark.parametrize("clave, mensaje", [
    ("abcdef1", "al menos 8"),            # 7 caracteres: justo debajo del mínimo
    ("abcdefgh", "letras y números"),
    ("12345678", "letras y números"),
    (" clave123", "espacios"),
    ("clave123 ", "espacios"),
    ("a1" + "x" * 71, "72 bytes"),        # 73 bytes
    ("a1" + "ñ" * 36, "72 bytes"),        # 38 caracteres, pero 74 bytes en UTF-8
    (None, "texto"),
    (12345678, "texto"),
])
def test_claves_invalidas(clave, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        validar_clave_nueva(clave)


def test_el_mensaje_de_error_no_incluye_la_clave():
    with pytest.raises(ValueError) as error:
        validar_clave_nueva("secretoX")
    assert "secretoX" not in str(error.value)


def test_validar_rol():
    assert validar_rol("Administrador") is Rol.ADMINISTRADOR
    with pytest.raises(ValueError, match="Rol no reconocido"):
        validar_rol("administrador")


# ---- CuentaUsuario
def test_cuenta_con_datos_basicos():
    c = cuenta()
    assert (c.id_usuario, c.rol, c.activo, c.bloqueada, c.nombre_completo) == (3, Rol.ENFERMERO, True, False, "Ana Pérez")


@pytest.mark.parametrize("cambios", [dict(id_usuario=0), dict(id_empleado=True), dict(rol="Otro"),
                                     dict(activo=1), dict(bloqueada=None)])
def test_cuenta_con_datos_invalidos(cambios):
    with pytest.raises(ValueError):
        cuenta(**cambios)


def test_activar_y_desactivar():
    c = cuenta()
    c.desactivar()
    assert not c.activo
    with pytest.raises(ReglaNegocioError, match="ya está desactivada"):
        c.desactivar()
    c.activar()
    assert c.activo
    with pytest.raises(ReglaNegocioError, match="ya está activa"):
        c.activar()


def test_cambiar_rol():
    c = cuenta()
    c.cambiar_rol("Médico de Emergencia")
    assert c.rol is Rol.MEDICO
    with pytest.raises(ReglaNegocioError, match="ya tiene el rol"):
        c.cambiar_rol(Rol.MEDICO)
    with pytest.raises(ValueError):
        c.cambiar_rol("Superusuario")
    assert c.rol is Rol.MEDICO


@pytest.mark.parametrize("bloqueada, intentos", [(True, 5), (False, 2)])
def test_desbloquear(bloqueada, intentos):
    c = cuenta(bloqueada=bloqueada, intentos_fallidos=intentos)
    c.desbloquear()
    assert (c.bloqueada, c.intentos_fallidos) == (False, 0)


def test_desbloquear_una_cuenta_sin_intentos_fallidos():
    with pytest.raises(ReglaNegocioError, match="no está bloqueada"):
        cuenta().desbloquear()


def test_repr_sin_nombres():
    assert "Ana" not in repr(cuenta()) and "Pérez" not in repr(cuenta())
