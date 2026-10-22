from unittest.mock import MagicMock

import mysql.connector
import pytest
from mysql.connector import Error as DBError
from mysql.connector import errorcode

from dao import db_connection
from dao.base_dao import BaseDAO
from dao.db_connection import ConexionBD
from dao.transaccion import transaccion
from models.excepciones import (
    CamaNoDisponibleError, ConexionBDError, PersistenciaError, RegistroDuplicadoError,
)

VARIABLES = {"DB_HOST": "127.0.0.1", "DB_USER": "u", "DB_PASS": "p", "DB_NAME": "sigtac_db"}


@pytest.fixture(autouse=True)
def entorno_aislado(monkeypatch):
    """Singleton nuevo en cada prueba, sin leer el .env real ni conectar a MySQL."""
    monkeypatch.setattr(ConexionBD, "_instancia", None)
    monkeypatch.setattr(db_connection, "load_dotenv", lambda *a, **k: None)
    for k, v in VARIABLES.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def conexion(monkeypatch):
    """La conexión simulada que devolverá mysql.connector.connect."""
    conexion = MagicMock()
    conexion.is_connected.return_value = True
    monkeypatch.setattr(db_connection.mysql.connector, "connect", MagicMock(return_value=conexion))
    return conexion


# ---- Confirmar y deshacer
def test_si_todo_sale_bien_confirma(conexion):
    with transaccion():
        assert ConexionBD().en_transaccion is True
    conexion.start_transaction.assert_called_once()
    conexion.commit.assert_called_once()
    conexion.rollback.assert_not_called()
    assert ConexionBD().en_transaccion is False


@pytest.mark.parametrize("error", [
    CamaNoDisponibleError("la tomó otro usuario"),  # regla de negocio
    PersistenciaError("fallo de MySQL"),
    ValueError("dato inválido"),
])
def test_cualquier_error_deshace_todo_y_se_vuelve_a_lanzar(conexion, error):
    with pytest.raises(type(error)):
        with transaccion():
            raise error
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    assert ConexionBD().en_transaccion is False


def test_salir_del_bloque_con_return_confirma(conexion):
    def operacion():
        with transaccion():
            return 7
    assert operacion() == 7
    conexion.commit.assert_called_once()


# ---- Transacciones anidadas: el bloque interno se une al externo
def test_bloque_anidado_no_abre_otra_transaccion(conexion):
    with transaccion():
        with transaccion():
            pass
        conexion.commit.assert_not_called()  # el interno no confirma por su cuenta
    conexion.start_transaction.assert_called_once()
    conexion.commit.assert_called_once()


def test_error_en_el_bloque_anidado_deshace_tambien_lo_del_externo(conexion):
    with pytest.raises(CamaNoDisponibleError):
        with transaccion():
            with transaccion():
                raise CamaNoDisponibleError("ocupada")
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()


def test_despues_de_una_transaccion_se_puede_abrir_otra(conexion):
    with transaccion():
        pass
    with transaccion():
        pass
    assert conexion.start_transaction.call_count == 2
    assert conexion.commit.call_count == 2


# ---- Fallos de la propia transacción
def test_sin_conexion_al_iniciar_se_propaga_conexion_bd_error(monkeypatch):
    monkeypatch.setattr(db_connection.mysql.connector, "connect", MagicMock(side_effect=DBError("sin servidor")))
    with pytest.raises(ConexionBDError):
        with transaccion():
            pytest.fail("el bloque no debe ejecutarse")
    assert ConexionBD().en_transaccion is False


def test_si_no_se_puede_iniciar_lanza_persistencia_error(conexion):
    conexion.start_transaction.side_effect = DBError("fallo")
    with pytest.raises(PersistenciaError):
        with transaccion():
            pytest.fail("el bloque no debe ejecutarse")


def test_si_el_commit_falla_deshace_y_lanza_persistencia_error(conexion):
    conexion.commit.side_effect = DBError("fallo al confirmar")
    with pytest.raises(PersistenciaError, match="confirmar"):
        with transaccion():
            pass
    conexion.rollback.assert_called_once()
    assert ConexionBD().en_transaccion is False


def test_si_el_rollback_falla_se_conserva_el_error_original(conexion):
    conexion.rollback.side_effect = DBError("sin conexión")
    with pytest.raises(CamaNoDisponibleError):  # no lo tapa el error del rollback
        with transaccion():
            raise CamaNoDisponibleError("ocupada")
    assert ConexionBD().en_transaccion is False


# ---- Con los DAO: todos los pasos usan la misma conexión
def test_los_pasos_del_bloque_usan_la_conexion_de_la_transaccion(conexion):
    with transaccion():
        BaseDAO._ejecutar("UPDATE cama SET id_estado_cama = %s WHERE id_cama = %s", (2, 1))
        BaseDAO._insertar("INSERT INTO historial_estado_cama (id_cama, id_estado_cama) VALUES (%s, %s)", (1, 2))
    assert conexion.cursor.return_value.execute.call_count == 2
    conexion.commit.assert_called_once()


def test_un_error_de_mysql_en_un_paso_deshace_los_anteriores(conexion):
    duplicado = mysql.connector.IntegrityError(msg="Duplicate entry", errno=errorcode.ER_DUP_ENTRY)
    conexion.cursor.return_value.execute.side_effect = [None, duplicado]  # el 2.º paso falla
    with pytest.raises(RegistroDuplicadoError):
        with transaccion():
            BaseDAO._ejecutar("UPDATE cama SET id_estado_cama = %s WHERE id_cama = %s", (2, 1))
            BaseDAO._insertar("INSERT INTO asignacion_cama (id_cama) VALUES (%s)", (1,))
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()


def test_si_la_conexion_se_pierde_a_mitad_no_se_reconecta(conexion, monkeypatch):
    # rollback() sobre la conexión muerta lanzaría un error ajeno a mysql.connector.Error (extensión C)
    conexion.rollback.side_effect = RuntimeError("Lost connection to MySQL server during query")
    with pytest.raises(ConexionBDError):
        with transaccion():
            BaseDAO._ejecutar("UPDATE cama SET id_estado_cama = %s WHERE id_cama = %s", (2, 1))
            conexion.is_connected.return_value = False  # se cae la conexión
            BaseDAO._insertar("INSERT INTO historial_estado_cama (id_cama, id_estado_cama) VALUES (%s, %s)", (1, 2))
    assert db_connection.mysql.connector.connect.call_count == 1  # no abrió otra conexión
    assert conexion.cursor.return_value.execute.call_count == 1   # el 2.º paso nunca se ejecutó
    conexion.commit.assert_not_called()
    conexion.rollback.assert_not_called()  # MySQL ya deshizo lo pendiente al perder la conexión
    assert ConexionBD().en_transaccion is False


def test_si_la_conexion_se_pierde_antes_del_commit_lanza_conexion_bd_error(conexion):
    with pytest.raises(ConexionBDError, match="antes de confirmar"):
        with transaccion():
            BaseDAO._ejecutar("UPDATE cama SET id_estado_cama = %s WHERE id_cama = %s", (2, 1))
            conexion.is_connected.return_value = False
    conexion.commit.assert_not_called()
    assert ConexionBD().en_transaccion is False
