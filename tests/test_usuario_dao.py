from unittest.mock import MagicMock

import pytest
from mysql.connector import Error as DBError

from dao import usuario_dao
from dao.usuario_dao import UsuarioDAO
from models.excepciones import ConexionBDError
from utils.security import generar_hash

DNI = "33333333"
CLAVE = "Clave#Prueba1"


@pytest.fixture(scope="module")
def hash_clave():
    return generar_hash(CLAVE)  # bcrypt es lento: se calcula una sola vez


def fila(hash_clave, activo=1):
    return {
        "id_empleado": 3, "dni": DNI, "nombres": "Ana", "apellidos": "Pérez", "colegiatura": None,
        "cargo_nombre": "Licenciado(a) en Enfermería", "cargo_tipo": "Enfermería",
        "id_usuario": 3, "hash_clave": hash_clave, "activo": activo,
        "id_rol": 4, "nombre_rol": "Enfermero de Triaje",
    }


class BD:
    """Conexión simulada: devuelve la fila indicada y recuerda cómo se usó."""

    def __init__(self, monkeypatch, row=None, error_en_execute=None, error_de_conexion=None):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        if error_en_execute:
            self.cursor.execute.side_effect = error_en_execute
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        if error_de_conexion:
            self.clase.return_value.obtener_conexion.side_effect = error_de_conexion
        else:
            self.clase.return_value.obtener_conexion.return_value = conexion
        monkeypatch.setattr(usuario_dao, "ConexionBD", self.clase)


@pytest.fixture
def senuelo(monkeypatch):
    """Espía la verificación señuelo para comprobar cuándo se usa."""
    espia = MagicMock()
    monkeypatch.setattr(usuario_dao, "simular_verificacion", espia)
    return espia


# ---- Login correcto
def test_login_correcto_devuelve_la_sesion_sin_el_hash(monkeypatch, senuelo, hash_clave):
    BD(monkeypatch, fila(hash_clave))
    sesion = UsuarioDAO.autenticar(DNI, CLAVE)
    assert sesion["nombre_rol"] == "Enfermero de Triaje"
    assert sesion["id_empleado"] == 3
    assert "hash_clave" not in sesion
    senuelo.assert_not_called()


def test_el_dni_se_limpia_de_espacios(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave))
    assert UsuarioDAO.autenticar(f"  {DNI}  ", CLAVE) is not None
    assert bd.cursor.execute.call_args.args[1] == (DNI,)


def test_la_consulta_esta_parametrizada(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave))
    UsuarioDAO.autenticar(DNI, CLAVE)
    consulta, parametros = bd.cursor.execute.call_args.args
    assert "%s" in consulta
    assert DNI not in consulta      # el dato viaja aparte, nunca dentro del SQL
    assert parametros == (DNI,)


# ---- Fallos de autenticación
def test_clave_incorrecta(monkeypatch, senuelo, hash_clave):
    BD(monkeypatch, fila(hash_clave))
    assert UsuarioDAO.autenticar(DNI, "otra-clave") is None


def test_usuario_inexistente_usa_el_senuelo(monkeypatch, senuelo):
    BD(monkeypatch, row=None)
    assert UsuarioDAO.autenticar(DNI, CLAVE) is None
    senuelo.assert_called_once_with(CLAVE)


def test_cuenta_desactivada_se_rechaza_aunque_la_clave_sea_correcta(monkeypatch, senuelo, hash_clave):
    BD(monkeypatch, fila(hash_clave, activo=0))
    assert UsuarioDAO.autenticar(DNI, CLAVE) is None
    senuelo.assert_called_once_with(CLAVE)


@pytest.mark.parametrize("hash_vacio", [None, ""])
def test_usuario_sin_hash_usa_el_senuelo(monkeypatch, senuelo, hash_vacio):
    BD(monkeypatch, fila(hash_vacio))
    assert UsuarioDAO.autenticar(DNI, CLAVE) is None
    senuelo.assert_called_once_with(CLAVE)


# ---- Validación de entradas: ni siquiera se consulta la BD
@pytest.mark.parametrize("dni, clave", [
    (None, CLAVE), ("", CLAVE), (DNI, None), (DNI, ""), (12345678, CLAVE), (DNI, 123456),
    ("1234", CLAVE),               # muy corto
    ("123456789", CLAVE),          # muy largo
    ("abcdefgh", CLAVE),           # no numérico
    ("1111111١", CLAVE),           # dígito árabe: \d lo aceptaría, [0-9] no
    ("11111111; DROP TABLE usuario", CLAVE),
    ("11111111\nINFO falso", CLAVE),
])
def test_entradas_invalidas_no_llegan_a_la_bd(monkeypatch, senuelo, dni, clave):
    bd = BD(monkeypatch, row=None)
    assert UsuarioDAO.autenticar(dni, clave) is None
    bd.clase.assert_not_called()


# ---- Errores de infraestructura
def test_sin_conexion_devuelve_none(monkeypatch, senuelo):
    BD(monkeypatch, error_de_conexion=ConexionBDError("sin servidor"))
    assert UsuarioDAO.autenticar(DNI, CLAVE) is None


def test_error_de_consulta_devuelve_none_y_cierra_el_cursor(monkeypatch, senuelo):
    bd = BD(monkeypatch, error_en_execute=DBError("boom"))
    assert UsuarioDAO.autenticar(DNI, CLAVE) is None
    bd.cursor.close.assert_called_once()


def test_el_cursor_se_cierra_tambien_en_un_login_correcto(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave))
    UsuarioDAO.autenticar(DNI, CLAVE)
    bd.cursor.close.assert_called_once()


# ---- Los logs no filtran datos personales
def test_los_logs_no_contienen_dni_ni_nombres(monkeypatch, senuelo, hash_clave, caplog):
    caplog.set_level("DEBUG")
    BD(monkeypatch, fila(hash_clave))
    UsuarioDAO.autenticar(DNI, CLAVE)
    UsuarioDAO.autenticar(DNI, "mala")
    texto = caplog.text
    assert DNI not in texto and "Ana" not in texto and "Pérez" not in texto
