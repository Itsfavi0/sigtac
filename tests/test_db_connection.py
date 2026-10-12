from unittest.mock import MagicMock

import pytest
from mysql.connector import Error as DBError

from dao import db_connection
from dao.db_connection import ConexionBD
from models.excepciones import ConexionBDError

VARIABLES = {"DB_HOST": "127.0.0.1", "DB_USER": "u", "DB_PASS": "p", "DB_NAME": "sigtac_db"}


@pytest.fixture(autouse=True)
def entorno_aislado(monkeypatch):
    """Cada prueba parte de un Singleton nuevo, sin leer el .env real ni conectar a MySQL."""
    monkeypatch.setattr(ConexionBD, "_instancia", None)
    monkeypatch.setattr(db_connection, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("DB_PORT", raising=False)
    for k, v in VARIABLES.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def connect(monkeypatch):
    mock = MagicMock()
    mock.return_value.is_connected.return_value = True
    monkeypatch.setattr(db_connection.mysql.connector, "connect", mock)
    return mock


def test_es_singleton():
    assert ConexionBD() is ConexionBD()


def test_conecta_con_autocommit_y_puerto_por_defecto(connect):
    ConexionBD().obtener_conexion()
    kwargs = connect.call_args.kwargs
    assert kwargs["autocommit"] is True
    assert kwargs["port"] == 3306
    assert kwargs["database"] == "sigtac_db"


def test_lee_el_puerto_del_entorno(connect, monkeypatch):
    monkeypatch.setenv("DB_PORT", "3307")
    ConexionBD().obtener_conexion()
    assert connect.call_args.kwargs["port"] == 3307


@pytest.mark.parametrize("variable", list(VARIABLES))
def test_falla_con_mensaje_claro_si_falta_una_variable(variable, monkeypatch, connect):
    monkeypatch.delenv(variable)
    with pytest.raises(ConexionBDError, match=variable):
        ConexionBD().obtener_conexion()
    connect.assert_not_called()  # nunca intenta conectar con valores por defecto


def test_error_de_mysql_se_convierte_en_conexion_bd_error(connect):
    connect.side_effect = DBError("rechazado")
    with pytest.raises(ConexionBDError):
        ConexionBD().obtener_conexion()


def test_reutiliza_la_conexion_mientras_siga_activa(connect):
    bd = ConexionBD()
    assert bd.obtener_conexion() is bd.obtener_conexion()
    assert connect.call_count == 1


def test_reconecta_si_la_conexion_se_perdio(connect):
    bd = ConexionBD()
    bd.obtener_conexion()
    connect.return_value.is_connected.return_value = False
    bd.obtener_conexion()
    assert connect.call_count == 2


def test_cerrar_conexion(connect):
    bd = ConexionBD()
    bd.obtener_conexion()
    bd.cerrar_conexion()
    connect.return_value.close.assert_called_once()
