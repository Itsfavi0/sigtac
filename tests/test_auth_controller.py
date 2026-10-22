from unittest.mock import MagicMock

import pytest

from controllers.auth_controller import AuthController, Sesion, exigir_permiso
from dao.usuario_dao import UsuarioDAO
from models.excepciones import AutenticacionError, SigtacError, UsuarioSinPermisoError
from models.permisos import Permiso, Rol, tiene_permiso

CLAVE = "Clave#Prueba1"


def datos_login(**cambios):
    """Lo que devuelve UsuarioDAO.autenticar en un login correcto (ya sin hash ni contadores)."""
    datos = {
        "id_empleado": 3, "tipo_documento": "DNI", "num_documento": "33333333", "nombres": "Ana",
        "apellidos": "Pérez", "colegiatura": None, "cargo_nombre": "Licenciado(a) en Enfermería",
        "cargo_tipo": "Enfermería", "id_usuario": 7, "activo": 1, "id_rol": 4, "nombre_rol": "Enfermero de Triaje",
    }
    datos.update(cambios)
    return datos


@pytest.fixture
def autenticar(monkeypatch):
    """Reemplaza UsuarioDAO.autenticar: por defecto, login correcto."""
    espia = MagicMock(return_value=datos_login())
    monkeypatch.setattr(UsuarioDAO, "autenticar", espia)
    return espia


def sesion(rol=Rol.MEDICO, **cambios):
    datos = {"id_usuario": 1, "id_empleado": 2, "nombre_rol": rol, "nombres": "Luis", "apellidos": "Ramos"}
    datos.update(cambios)
    return Sesion(**datos)


# ---- Iniciar sesión

def test_login_correcto_crea_la_sesion(autenticar):
    auth = AuthController()
    s = auth.iniciar_sesion("DNI", "33333333", CLAVE)
    assert auth.autenticado and auth.sesion is s
    assert (s.id_usuario, s.id_empleado, s.nombre_rol) == (7, 3, "Enfermero de Triaje")
    assert s.nombre_completo == "Ana Pérez"
    assert s.cargo == "Licenciado(a) en Enfermería"
    assert s.activa


def test_login_delega_en_el_dao_con_los_datos_recibidos(autenticar):
    AuthController().iniciar_sesion("CE", "001234567", CLAVE)
    autenticar.assert_called_once_with("CE", "001234567", CLAVE)


def test_login_fallido_lanza_error_generico_y_no_deja_sesion(autenticar):
    autenticar.return_value = None
    auth = AuthController()
    with pytest.raises(AutenticacionError) as error:
        auth.iniciar_sesion("DNI", "33333333", "mala")
    assert str(error.value) == AuthController.MENSAJE_FALLO
    assert not auth.autenticado and auth.sesion is None


def test_el_error_de_login_es_un_error_del_sistema():
    # Las vistas capturan SigtacError para mostrar el mensaje
    assert issubclass(AutenticacionError, SigtacError)


def test_un_nuevo_login_cierra_la_sesion_anterior(autenticar):
    auth = AuthController()
    primera = auth.iniciar_sesion("DNI", "33333333", CLAVE)
    autenticar.return_value = datos_login(id_usuario=8, nombre_rol="Personal de Limpieza")
    segunda = auth.iniciar_sesion("DNI", "44444444", CLAVE)
    assert not primera.activa
    assert auth.sesion is segunda and segunda.nombre_rol == "Personal de Limpieza"


def test_un_login_fallido_despues_de_otro_correcto_no_deja_a_nadie_conectado(autenticar):
    auth = AuthController()
    anterior = auth.iniciar_sesion("DNI", "33333333", CLAVE)
    autenticar.return_value = None
    with pytest.raises(AutenticacionError):
        auth.iniciar_sesion("DNI", "44444444", "mala")
    assert not anterior.activa and auth.sesion is None


def test_la_sesion_no_guarda_la_clave_ni_el_documento(autenticar):
    auth = AuthController()
    s = auth.iniciar_sesion("DNI", "33333333", CLAVE)
    guardado = repr(vars(s)) + repr(vars(auth))
    assert CLAVE not in guardado
    assert "33333333" not in guardado


@pytest.mark.parametrize("campo, valor", [("id_usuario", None), ("id_empleado", 0), ("nombre_rol", None)])
def test_datos_incompletos_del_dao_no_crean_una_sesion(autenticar, campo, valor):
    autenticar.return_value = datos_login(**{campo: valor})
    auth = AuthController()
    with pytest.raises(ValueError):
        auth.iniciar_sesion("DNI", "33333333", CLAVE)
    assert auth.sesion is None


# ---- Cerrar sesión

def test_cerrar_sesion_invalida_la_sesion(autenticar):
    auth = AuthController()
    s = auth.iniciar_sesion("DNI", "33333333", CLAVE)
    auth.cerrar_sesion()
    assert not auth.autenticado and auth.sesion is None
    assert not s.activa


def test_cerrar_sesion_sin_sesion_no_falla():
    auth = AuthController()
    auth.cerrar_sesion()
    auth.cerrar_sesion()
    assert auth.sesion is None


def test_exigir_sesion(autenticar):
    auth = AuthController()
    with pytest.raises(UsuarioSinPermisoError, match="sesión activa"):
        auth.exigir_sesion()
    s = auth.iniciar_sesion("DNI", "33333333", CLAVE)
    assert auth.exigir_sesion() is s
    auth.cerrar_sesion()
    with pytest.raises(UsuarioSinPermisoError):
        auth.exigir_sesion()


# ---- exigir_permiso

@pytest.mark.parametrize("rol", list(Rol))
@pytest.mark.parametrize("permiso", list(Permiso))
def test_exigir_permiso_sigue_la_matriz(rol, permiso):
    s = sesion(rol)
    if tiene_permiso(rol, permiso):
        assert exigir_permiso(s, permiso) is s
    else:
        with pytest.raises(UsuarioSinPermisoError, match="no tiene permiso"):
            exigir_permiso(s, permiso)


def test_exigir_permiso_acepta_el_permiso_como_texto():
    assert exigir_permiso(sesion(Rol.ENFERMERO), "triaje")


def test_sin_sesion_no_hay_permisos():
    with pytest.raises(UsuarioSinPermisoError, match="sesión activa"):
        exigir_permiso(None, Permiso.VER_CAMAS)


def test_una_sesion_cerrada_ya_no_tiene_permisos():
    # Un controlador creado con la sesión deja de operar cuando el usuario cierra sesión
    s = sesion(Rol.JEFE_GUARDIA)
    s.cerrar()
    with pytest.raises(UsuarioSinPermisoError, match="sesión activa"):
        exigir_permiso(s, Permiso.VER_CAMAS)
    assert s.puede(Permiso.VER_CAMAS) is False


@pytest.mark.parametrize("s", [None, sesion()])
@pytest.mark.parametrize("permiso", ["camas", "TRIAJE", "", None])
def test_un_permiso_desconocido_es_un_error_de_programacion(s, permiso):
    with pytest.raises(ValueError, match="Permiso"):
        exigir_permiso(s, permiso)


def test_un_rol_desconocido_inicia_sesion_pero_no_tiene_permisos(autenticar):
    # Se deniega por defecto: un rol nuevo en la BD sin entrada en la matriz no puede hacer nada
    autenticar.return_value = datos_login(nombre_rol="Superusuario")
    s = AuthController().iniciar_sesion("DNI", "33333333", CLAVE)
    assert not any(s.puede(p) for p in Permiso)
    with pytest.raises(UsuarioSinPermisoError):
        exigir_permiso(s, Permiso.VER_CAMAS)


# ---- Sesion

def test_puede_sigue_la_matriz():
    s = sesion(Rol.LIMPIEZA)
    assert s.puede(Permiso.LIMPIEZA) and s.puede("ver_camas")
    assert not s.puede(Permiso.TRIAJE)


def test_puede_con_un_permiso_desconocido_lanza_error():
    with pytest.raises(ValueError):
        sesion().puede("camas")


@pytest.mark.parametrize("campo, valor", [
    ("id_usuario", 0), ("id_usuario", -1), ("id_usuario", "7"), ("id_usuario", True),
    ("id_empleado", None), ("id_empleado", 2.0),
    ("nombre_rol", ""), ("nombre_rol", "   "), ("nombre_rol", None),
])
def test_sesion_con_datos_invalidos(campo, valor):
    with pytest.raises(ValueError):
        sesion(**{campo: valor})


def test_el_repr_no_muestra_nombres():
    texto = repr(sesion(nombres="Luis", apellidos="Ramos"))
    assert "Luis" not in texto and "Ramos" not in texto
    assert "id_usuario=1" in texto and "activa" in texto


def test_los_datos_de_la_sesion_son_de_solo_lectura():
    s = sesion()
    with pytest.raises(AttributeError):
        s.nombre_rol = Rol.ADMINISTRADOR
