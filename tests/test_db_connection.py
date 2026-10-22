from unittest.mock import MagicMock

import pytest
from mysql.connector import Error as DBError
from mysql.connector.constants import ClientFlag

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


def test_rowcount_cuenta_filas_encontradas(connect):
    ConexionBD().obtener_conexion()
    assert ClientFlag.FOUND_ROWS in connect.call_args.kwargs["client_flags"]


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


# ---- Estado de transacción
def test_sin_transaccion_al_inicio():
    assert ConexionBD().en_transaccion is False


def test_iniciar_transaccion(connect):
    bd = ConexionBD()
    bd.iniciar_transaccion()
    connect.return_value.start_transaction.assert_called_once_with()
    assert bd.en_transaccion is True
    assert connect.call_args.kwargs["autocommit"] is True  # autocommit no cambia: START TRANSACTION lo suspende


def test_si_start_transaction_falla_no_queda_en_transaccion(connect):
    connect.return_value.start_transaction.side_effect = DBError("fallo")
    bd = ConexionBD()
    with pytest.raises(DBError):
        bd.iniciar_transaccion()
    assert bd.en_transaccion is False


@pytest.mark.parametrize("confirmar, metodo, otro", [(True, "commit", "rollback"), (False, "rollback", "commit")])
def test_terminar_transaccion(connect, confirmar, metodo, otro):
    bd = ConexionBD()
    bd.iniciar_transaccion()
    bd.terminar_transaccion(confirmar)
    getattr(connect.return_value, metodo).assert_called_once()
    getattr(connect.return_value, otro).assert_not_called()
    assert bd.en_transaccion is False


def test_si_el_commit_falla_la_transaccion_igual_queda_cerrada(connect):
    connect.return_value.commit.side_effect = DBError("fallo")
    bd = ConexionBD()
    bd.iniciar_transaccion()
    with pytest.raises(DBError):
        bd.terminar_transaccion(True)
    assert bd.en_transaccion is False


def test_no_reconecta_si_la_conexion_se_pierde_durante_una_transaccion(connect):
    bd = ConexionBD()
    bd.iniciar_transaccion()
    connect.return_value.is_connected.return_value = False
    with pytest.raises(ConexionBDError, match="durante la operación"):
        bd.obtener_conexion()
    assert connect.call_count == 1  # no abrió una conexión nueva


def test_despues_de_terminar_la_transaccion_vuelve_a_reconectar(connect):
    bd = ConexionBD()
    bd.iniciar_transaccion()
    connect.return_value.is_connected.return_value = False
    bd.terminar_transaccion(False)
    bd.obtener_conexion()
    assert connect.call_count == 2


def test_rollback_con_la_conexion_perdida_no_llama_a_rollback(connect):
    # Con la extensión C, rollback() sobre una conexión muerta lanza MySQLInterfaceError, que no
    # hereda de mysql.connector.Error (encontrado al verificar contra MySQL real).
    bd = ConexionBD()
    bd.iniciar_transaccion()
    connect.return_value.is_connected.return_value = False
    connect.return_value.rollback.side_effect = RuntimeError("no debería llamarse")
    bd.terminar_transaccion(False)
    connect.return_value.rollback.assert_not_called()
    assert bd.en_transaccion is False


def test_confirmar_con_la_conexion_perdida_lanza_conexion_bd_error(connect):
    bd = ConexionBD()
    bd.iniciar_transaccion()
    connect.return_value.is_connected.return_value = False
    with pytest.raises(ConexionBDError, match="antes de confirmar"):
        bd.terminar_transaccion(True)
    connect.return_value.commit.assert_not_called()
    assert bd.en_transaccion is False


def test_cerrar_la_conexion_cierra_la_transaccion(connect):
    bd = ConexionBD()
    bd.iniciar_transaccion()
    bd.cerrar_conexion()
    assert bd.en_transaccion is False
    bd.terminar_transaccion(False)  # sin conexión no falla: MySQL ya deshizo lo pendiente
