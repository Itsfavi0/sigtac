import pytest

from models.permisos import PERMISOS_POR_ROL, Permiso, Rol, tiene_permiso

# Matriz esperada, escrita aparte a propósito: si alguien cambia PERMISOS_POR_ROL sin querer,
# esta prueba lo detecta. Un cambio intencional se hace en los dos lugares.
P = Permiso
MATRIZ = {
    Rol.ADMINISTRADOR: {P.VER_CAMAS, P.REPORTES, P.ADMINISTRACION},
    Rol.JEFE_GUARDIA: {P.PACIENTES, P.TRIAJE, P.GESTION_CAMAS, P.VER_CAMAS, P.REPORTES},
    Rol.MEDICO: {P.PACIENTES, P.TRIAJE, P.GESTION_CAMAS, P.VER_CAMAS},
    Rol.ENFERMERO: {P.PACIENTES, P.TRIAJE, P.VER_CAMAS},
    Rol.LIMPIEZA: {P.VER_CAMAS, P.LIMPIEZA},
}


@pytest.mark.parametrize("rol", list(Rol))
@pytest.mark.parametrize("permiso", list(Permiso))
def test_matriz_completa_de_permisos(rol, permiso):
    assert tiene_permiso(rol, permiso) is (permiso in MATRIZ[rol])


def test_todos_los_roles_tienen_una_entrada():
    assert set(PERMISOS_POR_ROL) == set(Rol)


def test_todos_pueden_ver_el_mapa_de_camas():
    assert all(tiene_permiso(rol, Permiso.VER_CAMAS) for rol in Rol)


def test_solo_el_administrador_administra_usuarios_y_auditoria():
    assert [r for r in Rol if tiene_permiso(r, Permiso.ADMINISTRACION)] == [Rol.ADMINISTRADOR]


def test_solo_el_personal_de_limpieza_confirma_la_limpieza():  # RN-08
    assert [r for r in Rol if tiene_permiso(r, Permiso.LIMPIEZA)] == [Rol.LIMPIEZA]


def test_el_enfermero_no_asigna_camas():
    assert tiene_permiso(Rol.ENFERMERO, Permiso.GESTION_CAMAS) is False


def test_se_acepta_el_nombre_de_rol_de_la_sesion():
    # UsuarioDAO.autenticar devuelve nombre_rol como texto
    assert tiene_permiso("Médico de Emergencia", "triaje") is True
    assert tiene_permiso("Personal de Limpieza", "triaje") is False


@pytest.mark.parametrize("rol", ["Superusuario", "", None, "administrador", "Medico de Emergencia"])
def test_un_rol_desconocido_no_tiene_ningun_permiso(rol):
    # Se deniega por defecto; distingue mayúsculas y tildes, como el nombre en la BD
    assert all(tiene_permiso(rol, permiso) is False for permiso in Permiso)


@pytest.mark.parametrize("permiso", ["camas", "historias_clinicas", "TRIAJE", "", None])
def test_un_permiso_desconocido_es_un_error_de_programacion(permiso):
    with pytest.raises(ValueError, match="Permiso"):
        tiene_permiso(Rol.ADMINISTRADOR, permiso)


def test_la_matriz_no_se_puede_modificar_por_accidente():
    with pytest.raises(AttributeError):
        PERMISOS_POR_ROL[Rol.LIMPIEZA].add(Permiso.REPORTES)  # frozenset
