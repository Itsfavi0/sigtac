from unittest.mock import MagicMock

import mysql.connector
import pytest
from mysql.connector import errorcode

from dao import base_dao
from dao.base_dao import BaseDAO
from models.excepciones import (ConexionBDError, PersistenciaError, RegistroDuplicadoError,
                                SigtacError)

SQL = "SELECT * FROM paciente WHERE dni = %s"
DNI = "12345678"


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, error_en_execute=None, error_de_conexion=None):
        self.cursor = MagicMock()
        if error_en_execute:
            self.cursor.execute.side_effect = error_en_execute
        self.conexion = MagicMock()
        self.conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        if error_de_conexion:
            self.clase.return_value.obtener_conexion.side_effect = error_de_conexion
        else:
            self.clase.return_value.obtener_conexion.return_value = self.conexion
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)


def error_duplicado():
    return mysql.connector.IntegrityError(
        msg=f"Duplicate entry '{DNI}' for key 'paciente.UN_paciente_dni'", errno=errorcode.ER_DUP_ENTRY)


# ---- Resultados
def test_consultar_uno_devuelve_la_fila(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.fetchone.return_value = {"id_paciente": 1}
    assert BaseDAO._consultar_uno(SQL, (DNI,)) == {"id_paciente": 1}


def test_consultar_uno_sin_resultado_devuelve_none(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.fetchone.return_value = None
    assert BaseDAO._consultar_uno(SQL, (DNI,)) is None


def test_consultar_varios_devuelve_todas_las_filas(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.fetchall.return_value = [{"id_cama": 1}, {"id_cama": 2}]
    assert BaseDAO._consultar_varios("SELECT * FROM cama") == [{"id_cama": 1}, {"id_cama": 2}]


def test_consultar_varios_sin_resultados_devuelve_lista_vacia(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.fetchall.return_value = []
    assert BaseDAO._consultar_varios("SELECT * FROM cama") == []


def test_insertar_devuelve_el_id_generado(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.lastrowid = 42
    assert BaseDAO._insertar("INSERT INTO seguro (nombre_seguro) VALUES (%s)", ("SIS",)) == 42


def test_ejecutar_devuelve_las_filas_afectadas(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.rowcount = 1
    assert BaseDAO._ejecutar("UPDATE paciente SET estado_registro = FALSE WHERE id_paciente = %s", (1,)) == 1


def test_el_cursor_devuelve_diccionarios(monkeypatch):
    bd = BD(monkeypatch)
    BaseDAO._consultar_uno(SQL, (DNI,))
    bd.conexion.cursor.assert_called_once_with(dictionary=True, buffered=True)


# ---- Parámetros
def test_los_parametros_se_pasan_aparte_y_sin_envolver(monkeypatch):
    bd = BD(monkeypatch)
    BaseDAO._consultar_uno(SQL, (DNI,))
    bd.cursor.execute.assert_called_once_with(SQL, (DNI,))  # no ((DNI,),)


@pytest.mark.parametrize("params", [DNI, [DNI], None, {"dni": DNI}])
def test_parametros_que_no_son_tupla_se_rechazan_sin_tocar_la_bd(monkeypatch, params):
    bd = BD(monkeypatch)
    with pytest.raises(TypeError):
        BaseDAO._consultar_uno(SQL, params)
    bd.clase.assert_not_called()


# ---- Cierre del cursor
def test_el_cursor_se_cierra_tras_una_consulta_correcta(monkeypatch):
    bd = BD(monkeypatch)
    BaseDAO._consultar_uno(SQL, (DNI,))
    bd.cursor.close.assert_called_once()


def test_el_cursor_se_cierra_aunque_falle_la_consulta(monkeypatch):
    bd = BD(monkeypatch, error_en_execute=mysql.connector.Error("boom"))
    with pytest.raises(PersistenciaError):
        BaseDAO._consultar_uno(SQL, (DNI,))
    bd.cursor.close.assert_called_once()


def test_un_error_al_cerrar_el_cursor_no_pierde_el_resultado(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.fetchone.return_value = {"id_paciente": 1}
    bd.cursor.close.side_effect = mysql.connector.Error("conexión cerrada")
    assert BaseDAO._consultar_uno(SQL, (DNI,)) == {"id_paciente": 1}


# ---- Traducción de errores
def test_error_de_mysql_se_traduce_a_persistencia_error(monkeypatch):
    error = mysql.connector.Error("boom")
    BD(monkeypatch, error_en_execute=error)
    with pytest.raises(PersistenciaError) as info:
        BaseDAO._consultar_varios(SQL, (DNI,))
    assert info.value.__cause__ is error  # el error original se conserva para depurar


def test_dni_duplicado_lanza_registro_duplicado(monkeypatch):
    BD(monkeypatch, error_en_execute=error_duplicado())
    with pytest.raises(RegistroDuplicadoError):
        BaseDAO._insertar("INSERT INTO paciente (dni) VALUES (%s)", (DNI,))


def test_otra_violacion_de_integridad_no_es_un_duplicado(monkeypatch):
    error_fk = mysql.connector.IntegrityError(msg="Cannot add or update a child row", errno=errorcode.ER_NO_REFERENCED_ROW_2)
    BD(monkeypatch, error_en_execute=error_fk)
    with pytest.raises(PersistenciaError) as info:
        BaseDAO._insertar("INSERT INTO paciente (id_seguro) VALUES (%s)", (99,))
    assert not isinstance(info.value, RegistroDuplicadoError)


def test_sin_conexion_se_propaga_conexion_bd_error(monkeypatch):
    BD(monkeypatch, error_de_conexion=ConexionBDError("sin servidor"))
    with pytest.raises(ConexionBDError):
        BaseDAO._consultar_uno(SQL, (DNI,))


def test_errores_de_programacion_no_se_disfrazan(monkeypatch):
    # Solo se traducen los errores de MySQL; un fallo de Python debe verse tal cual
    bd = BD(monkeypatch)
    bd.cursor.fetchone.side_effect = KeyError("columna")
    with pytest.raises(KeyError):
        BaseDAO._consultar_uno(SQL, (DNI,))


# ---- Datos personales
def test_ni_logs_ni_mensajes_contienen_el_dato_duplicado(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    BD(monkeypatch, error_en_execute=error_duplicado())
    with pytest.raises(RegistroDuplicadoError) as info:
        BaseDAO._insertar("INSERT INTO paciente (dni) VALUES (%s)", (DNI,))
    assert DNI not in caplog.text
    assert DNI not in str(info.value)


# ---- Jerarquía: el controlador puede capturar todo con PersistenciaError
@pytest.mark.parametrize("excepcion", [ConexionBDError, RegistroDuplicadoError])
def test_errores_de_bd_derivan_de_persistencia_error(excepcion):
    assert issubclass(excepcion, PersistenciaError)
    assert issubclass(PersistenciaError, SigtacError)
