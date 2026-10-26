from datetime import datetime
from unittest.mock import MagicMock

import mysql.connector
import pytest
from mysql.connector import errorcode

from dao import base_dao
from dao import transaccion as transaccion_mod
from dao.asignacion_dao import AsignacionDAO
from dao.solicitud_limpieza_dao import SolicitudLimpiezaDAO
from models.asignacion import AsignacionCama, SolicitudLimpieza
from models.excepciones import ReglaNegocioError, RegistroDuplicadoError

INICIO = datetime(2026, 10, 21, 9, 0)


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, row=None, rows=None, rowcount=1, lastrowid=None, error_en_execute=None):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        self.cursor.fetchall.return_value = rows or []
        self.cursor.rowcount = rowcount
        self.cursor.lastrowid = lastrowid
        if error_en_execute:
            self.cursor.execute.side_effect = error_en_execute
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        self.clase.return_value.obtener_conexion.return_value = conexion
        self.clase.return_value.en_transaccion = False
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)
        monkeypatch.setattr(transaccion_mod, "ConexionBD", self.clase)

    @property
    def sql(self) -> str:
        return " ".join(self.cursor.execute.call_args.args[0].split())

    @property
    def params(self) -> tuple:
        return self.cursor.execute.call_args.args[1]


def fila_asignacion(**cambios):
    datos = {"id_asignacion": 1, "id_episodio": 1, "id_cama": 1, "id_empleado": 2,
             "fecha_asignacion": INICIO, "fecha_liberacion": None}
    datos.update(cambios)
    return datos


# ---- AsignacionDAO.crear
def test_crear_asignacion(monkeypatch):
    bd = BD(monkeypatch, lastrowid=5)
    assert AsignacionDAO.crear(2, 3, 2) == 5
    assert bd.sql == "INSERT INTO asignacion_cama (id_episodio, id_cama, id_empleado) VALUES (%s, %s, %s)"
    assert bd.params == (2, 3, 2)  # la fecha la pone MySQL


def test_cama_o_episodio_con_asignacion_vigente_lanza_registro_duplicado(monkeypatch):  # RN-05 en la BD
    duplicado = mysql.connector.IntegrityError(msg="Duplicate entry", errno=errorcode.ER_DUP_ENTRY)
    BD(monkeypatch, error_en_execute=duplicado)
    with pytest.raises(RegistroDuplicadoError):
        AsignacionDAO.crear(2, 1, 2)


def test_crear_no_abre_una_transaccion_propia(monkeypatch):
    bd = BD(monkeypatch, lastrowid=5)
    AsignacionDAO.crear(2, 3, 2)
    bd.clase.return_value.iniciar_transaccion.assert_not_called()


@pytest.mark.parametrize("ids", [(0, 3, 2), (2, None, 2), (2, 3, "2"), (True, 3, 2)])
def test_crear_con_ids_invalidos_no_llega_a_la_bd(monkeypatch, ids):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        AsignacionDAO.crear(*ids)
    bd.clase.assert_not_called()


# ---- Búsqueda de la asignación vigente
@pytest.mark.parametrize("metodo, columna", [
    (AsignacionDAO.buscar_vigente_por_episodio, "id_episodio"),
    (AsignacionDAO.buscar_vigente_por_cama, "id_cama"),
])
def test_buscar_vigente(monkeypatch, metodo, columna):
    bd = BD(monkeypatch, row=fila_asignacion())
    asignacion = metodo(1)
    assert asignacion == AsignacionCama(1, 1, 1, 2, INICIO, None) and asignacion.vigente
    assert f"WHERE {columna} = %s AND fecha_liberacion IS NULL AND estado_registro = TRUE" in bd.sql
    assert bd.params == (1,)


@pytest.mark.parametrize("metodo", [AsignacionDAO.buscar_vigente_por_episodio, AsignacionDAO.buscar_vigente_por_cama])
def test_sin_asignacion_vigente_devuelve_none(monkeypatch, metodo):
    BD(monkeypatch, row=None)
    assert metodo(3) is None


@pytest.mark.parametrize("metodo", [AsignacionDAO.buscar_vigente_por_episodio, AsignacionDAO.buscar_vigente_por_cama])
def test_buscar_con_id_invalido_no_consulta_la_bd(monkeypatch, metodo):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        metodo(0)
    bd.clase.assert_not_called()


# ---- AsignacionDAO.liberar (RN-07)
def test_liberar_pone_la_fecha_con_el_reloj_de_mysql(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    AsignacionDAO.liberar(1)
    assert bd.sql.startswith("UPDATE asignacion_cama SET fecha_liberacion = NOW() WHERE id_asignacion = %s")
    assert bd.sql.endswith("AND fecha_liberacion IS NULL AND estado_registro = TRUE")  # condicional
    assert bd.params == (1,)


def test_liberar_una_asignacion_ya_liberada_lanza_regla_negocio_error(monkeypatch):
    BD(monkeypatch, rowcount=0)
    with pytest.raises(ReglaNegocioError, match="ya fue liberada"):
        AsignacionDAO.liberar(1)


def test_liberar_con_id_invalido_no_llega_a_la_bd(monkeypatch):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        AsignacionDAO.liberar(None)
    bd.clase.assert_not_called()


# ---- AsignacionDAO.anular (reserva cancelada)
def test_anular_es_baja_logica_sin_fecha_de_liberacion(monkeypatch):  # RN-11
    bd = BD(monkeypatch, rowcount=1)
    AsignacionDAO.anular(1)
    assert bd.sql.startswith("UPDATE asignacion_cama SET estado_registro = FALSE WHERE id_asignacion = %s")
    assert bd.sql.endswith("AND fecha_liberacion IS NULL AND estado_registro = TRUE")
    assert "fecha_liberacion = " not in bd.sql and "DELETE" not in bd.sql.upper()
    assert bd.params == (1,)


def test_anular_una_asignacion_no_vigente_lanza_regla_negocio_error(monkeypatch):
    BD(monkeypatch, rowcount=0)
    with pytest.raises(ReglaNegocioError, match="anulada"):
        AsignacionDAO.anular(1)


def test_anular_con_id_invalido_no_llega_a_la_bd(monkeypatch):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        AsignacionDAO.anular(0)
    bd.clase.assert_not_called()


def test_asignacion_dao_no_borra():  # el historial de asignaciones se conserva
    publicos = {nombre for nombre in vars(AsignacionDAO) if not nombre.startswith("_")}
    assert publicos == {"crear", "buscar_vigente_por_episodio", "buscar_vigente_por_cama", "liberar", "anular"}


# ---- SolicitudLimpiezaDAO
def fila_solicitud(**cambios):
    datos = {"id_solicitud": 1, "id_cama": 4, "codigo": "UCI-02", "fecha_solicitud": INICIO,
             "id_empleado": None, "fecha_atencion": None}
    datos.update(cambios)
    return datos


def test_crear_solicitud(monkeypatch):
    bd = BD(monkeypatch, lastrowid=3)
    assert SolicitudLimpiezaDAO.crear(4) == 3
    assert bd.sql == "INSERT INTO solicitud_limpieza (id_cama) VALUES (%s)" and bd.params == (4,)


def test_crear_solicitud_con_id_invalido_no_llega_a_la_bd(monkeypatch):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        SolicitudLimpiezaDAO.crear(0)
    bd.clase.assert_not_called()


def test_listar_pendientes(monkeypatch):
    bd = BD(monkeypatch, rows=[fila_solicitud(), fila_solicitud(id_solicitud=2, id_cama=1, codigo="TRA-01")])
    pendientes = SolicitudLimpiezaDAO.listar_pendientes()
    assert pendientes[0] == SolicitudLimpieza(1, 4, "UCI-02", INICIO)
    assert [s.codigo_cama for s in pendientes] == ["UCI-02", "TRA-01"]
    assert all(s.pendiente for s in pendientes)
    assert "WHERE s.fecha_atencion IS NULL ORDER BY s.fecha_solicitud, s.id_solicitud" in bd.sql


def test_listar_pendientes_vacio(monkeypatch):
    BD(monkeypatch, rows=[])
    assert SolicitudLimpiezaDAO.listar_pendientes() == []


def test_atender_solicitud(monkeypatch):  # RN-08
    bd = BD(monkeypatch, rowcount=1)
    SolicitudLimpiezaDAO.atender(1, 4)
    assert bd.sql.startswith("UPDATE solicitud_limpieza SET id_empleado = %s, fecha_atencion = NOW()")
    assert bd.sql.endswith("WHERE id_solicitud = %s AND fecha_atencion IS NULL")
    assert bd.params == (4, 1)


def test_atender_una_solicitud_ya_atendida_lanza_regla_negocio_error(monkeypatch):
    BD(monkeypatch, rowcount=0)
    with pytest.raises(ReglaNegocioError, match="ya fue atendida"):
        SolicitudLimpiezaDAO.atender(1, 4)


@pytest.mark.parametrize("ids", [(0, 4), (1, None), ("1", 4)])
def test_atender_con_ids_invalidos_no_llega_a_la_bd(monkeypatch, ids):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        SolicitudLimpiezaDAO.atender(*ids)
    bd.clase.assert_not_called()


def test_buscar_solicitud_por_id(monkeypatch):
    bd = BD(monkeypatch, row=fila_solicitud(id_solicitud=3))
    assert SolicitudLimpiezaDAO.buscar_por_id(3).id_solicitud == 3
    assert "s.id_solicitud = %s" in bd.sql and bd.params == (3,)


def test_buscar_solicitud_inexistente_o_id_invalido(monkeypatch):
    BD(monkeypatch, row=None)
    assert SolicitudLimpiezaDAO.buscar_por_id(3) is None
    with pytest.raises(ValueError):
        SolicitudLimpiezaDAO.buscar_por_id(0)


def test_buscar_pendiente_por_cama(monkeypatch):
    bd = BD(monkeypatch, row=fila_solicitud())
    assert SolicitudLimpiezaDAO.buscar_pendiente_por_cama(4) == SolicitudLimpieza(1, 4, "UCI-02", INICIO)
    assert "WHERE s.id_cama = %s AND s.fecha_atencion IS NULL" in bd.sql and bd.params == (4,)


def test_buscar_pendiente_por_cama_sin_solicitud(monkeypatch):
    BD(monkeypatch, row=None)
    assert SolicitudLimpiezaDAO.buscar_pendiente_por_cama(4) is None


def test_buscar_pendiente_con_id_invalido_no_llega_a_la_bd(monkeypatch):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        SolicitudLimpiezaDAO.buscar_pendiente_por_cama(None)
    bd.clase.assert_not_called()
