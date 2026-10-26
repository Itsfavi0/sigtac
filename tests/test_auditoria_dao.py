import json
from datetime import datetime
from unittest.mock import MagicMock

import mysql.connector
import pytest
from mysql.connector import errorcode

from dao import base_dao
from dao.auditoria_dao import AuditoriaDAO
from models.auditoria import AccionAuditoria
from models.excepciones import ConexionBDError, PersistenciaError


def fila(**cambios):
    datos = {
        "id_bitacora": 2, "id_usuario": 3, "tabla_afectada": "paciente", "accion": "INSERT",
        "id_registro_afectado": 1, "fecha_hora": datetime(2026, 10, 21, 9, 30), "detalles_json": None,
    }
    datos.update(cambios)
    return datos


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, rows=None, lastrowid=None, error_en_execute=None):
        self.cursor = MagicMock()
        self.cursor.fetchall.return_value = rows or []
        self.cursor.lastrowid = lastrowid
        if error_en_execute:
            self.cursor.execute.side_effect = error_en_execute
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        self.clase.return_value.obtener_conexion.return_value = conexion
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)

    @property
    def sql(self) -> str:
        return " ".join(self.cursor.execute.call_args.args[0].split())

    @property
    def params(self) -> tuple:
        return self.cursor.execute.call_args.args[1]


# ---- registrar
def test_registrar_inserta_y_devuelve_el_id(monkeypatch):
    bd = BD(monkeypatch, lastrowid=10)
    assert AuditoriaDAO.registrar(3, "paciente", AccionAuditoria.INSERT, 1) == 10
    assert bd.sql.startswith("INSERT INTO bitacora_auditoria")
    assert bd.params == (3, "paciente", "INSERT", 1, None)


def test_la_fecha_la_pone_mysql(monkeypatch):
    bd = BD(monkeypatch, lastrowid=10)
    AuditoriaDAO.registrar(3, "paciente", AccionAuditoria.INSERT, 1)
    assert "fecha_hora" not in bd.sql  # usa el DEFAULT CURRENT_TIMESTAMP de la tabla


def test_la_accion_se_acepta_como_texto(monkeypatch):
    bd = BD(monkeypatch, lastrowid=10)
    AuditoriaDAO.registrar(3, "paciente", "IDENTIFICAR", 5)
    assert bd.params[2] == "IDENTIFICAR"


def test_los_detalles_se_guardan_como_json(monkeypatch):
    bd = BD(monkeypatch, lastrowid=10)
    AuditoriaDAO.registrar(3, "triaje", AccionAuditoria.UPDATE, 2, {"nivel_anterior": 3, "nivel_nuevo": 2})
    assert json.loads(bd.params[4]) == {"nivel_anterior": 3, "nivel_nuevo": 2}


def test_los_detalles_conservan_tildes(monkeypatch):
    bd = BD(monkeypatch, lastrowid=10)
    AuditoriaDAO.registrar(3, "cama", AccionAuditoria.UPDATE, 4, {"estado": "EN LIMPIEZA", "motivo": "alta médica"})
    assert "médica" in bd.params[4]  # ensure_ascii=False: se guarda legible, no como é


@pytest.mark.parametrize("cambio, mensaje", [
    (dict(id_usuario=0), "id_usuario"),
    (dict(id_usuario=-1), "id_usuario"),
    (dict(id_usuario="3"), "id_usuario"),
    (dict(id_usuario=None), "id_usuario"),
    (dict(id_usuario=True), "id_usuario"),
    (dict(tabla="bitacora_auditoria"), "Tabla"),  # la bitácora no se audita a sí misma
    (dict(tabla="PACIENTE"), "Tabla"),
    (dict(tabla="paciente; DROP TABLE usuario"), "Tabla"),
    (dict(tabla=None), "Tabla"),
    (dict(accion="update"), "Acción"),
    (dict(accion="BORRAR"), "Acción"),
    (dict(accion=None), "Acción"),
    (dict(id_registro=0), "id_registro"),
    (dict(id_registro=1.5), "id_registro"),
    (dict(detalles=["no", "es", "dict"]), "diccionario"),
    (dict(detalles={"fecha": datetime(2026, 1, 1)}), "JSON"),
])
def test_datos_invalidos_no_llegan_a_la_bd(monkeypatch, cambio, mensaje):
    bd = BD(monkeypatch, lastrowid=10)
    datos = dict(id_usuario=3, tabla="paciente", accion=AccionAuditoria.INSERT, id_registro=1, detalles=None)
    datos.update(cambio)
    with pytest.raises(ValueError, match=mensaje):
        AuditoriaDAO.registrar(**datos)
    bd.clase.assert_not_called()


def test_usuario_inexistente_lanza_persistencia_error(monkeypatch):
    fk = mysql.connector.IntegrityError(msg="FK", errno=errorcode.ER_NO_REFERENCED_ROW_2)
    BD(monkeypatch, error_en_execute=fk)
    with pytest.raises(PersistenciaError):
        AuditoriaDAO.registrar(99, "paciente", AccionAuditoria.INSERT, 1)


def test_sin_conexion_se_propaga(monkeypatch):
    bd = BD(monkeypatch)
    bd.clase.return_value.obtener_conexion.side_effect = ConexionBDError("sin servidor")
    with pytest.raises(ConexionBDError):
        AuditoriaDAO.registrar(3, "paciente", AccionAuditoria.INSERT, 1)


def test_el_log_no_incluye_los_detalles(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    BD(monkeypatch, lastrowid=10)
    AuditoriaDAO.registrar(3, "triaje", AccionAuditoria.UPDATE, 2, {"justificacion": "texto clínico sensible"})
    assert "texto clínico sensible" not in caplog.text
    assert "id_bitacora=10" in caplog.text


# ---- Solo inserción
def test_la_bitacora_no_tiene_metodos_para_modificar_ni_borrar():
    publicos = {nombre for nombre in vars(AuditoriaDAO) if not nombre.startswith("_")}
    assert publicos == {"TABLAS_AUDITABLES", "LIMITE_MAXIMO", "registrar", "listar_por_registro", "listar"}


# ---- listar_por_registro
def test_listar_por_registro_devuelve_el_historial(monkeypatch):
    bd = BD(monkeypatch, rows=[fila(), fila(id_bitacora=5, accion="ANULAR", detalles_json='{"motivo": "duplicado"}')])
    historial = AuditoriaDAO.listar_por_registro("paciente", 1)
    assert [r["id_bitacora"] for r in historial] == [2, 5]
    assert historial[0]["accion"] is AccionAuditoria.INSERT
    assert historial[0]["detalles"] is None
    assert historial[1]["detalles"] == {"motivo": "duplicado"}
    assert historial[0]["fecha_hora"] == datetime(2026, 10, 21, 9, 30)
    assert "WHERE tabla_afectada = %s AND id_registro_afectado = %s" in bd.sql
    assert "ORDER BY fecha_hora, id_bitacora" in bd.sql
    assert bd.params == ("paciente", 1)


def test_detalles_en_bytes_tambien_se_decodifican(monkeypatch):
    BD(monkeypatch, rows=[fila(detalles_json=b'{"nivel_nuevo": 2}')])
    assert AuditoriaDAO.listar_por_registro("paciente", 1)[0]["detalles"] == {"nivel_nuevo": 2}


def test_listar_sin_registros_devuelve_lista_vacia(monkeypatch):
    BD(monkeypatch, rows=[])
    assert AuditoriaDAO.listar_por_registro("paciente", 99) == []


@pytest.mark.parametrize("tabla, id_registro", [("no_existe", 1), ("paciente", 0), ("paciente", None)])
def test_listar_con_datos_invalidos_no_consulta_la_bd(monkeypatch, tabla, id_registro):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        AuditoriaDAO.listar_por_registro(tabla, id_registro)
    bd.clase.assert_not_called()


def test_accion_desconocida_en_la_bd_se_rechaza(monkeypatch):
    BD(monkeypatch, rows=[fila(accion="ACCION_RARA")])
    with pytest.raises(ValueError):
        AuditoriaDAO.listar_por_registro("paciente", 1)



# ---- listar (consulta de la bitácora)
DESDE, HASTA = datetime(2026, 10, 1), datetime(2026, 11, 1)


def test_listar_por_periodo_del_mas_reciente_al_mas_antiguo(monkeypatch):
    bd = BD(monkeypatch, rows=[fila(id_bitacora=3), fila(id_bitacora=2)])
    assert [r["id_bitacora"] for r in AuditoriaDAO.listar(DESDE, HASTA)] == [3, 2]
    assert "WHERE fecha_hora >= %s AND fecha_hora < %s ORDER BY fecha_hora DESC, id_bitacora DESC LIMIT %s" in bd.sql
    assert bd.params == (DESDE, HASTA, 200)


def test_listar_con_filtros(monkeypatch):
    bd = BD(monkeypatch)
    AuditoriaDAO.listar(DESDE, HASTA, tabla="paciente", id_usuario=3, limite=50)
    assert "AND tabla_afectada = %s AND id_usuario = %s" in bd.sql
    assert bd.params == (DESDE, HASTA, "paciente", 3, 50)


@pytest.mark.parametrize("limite", [1, 1000])
def test_listar_limites_validos(monkeypatch, limite):
    bd = BD(monkeypatch)
    AuditoriaDAO.listar(DESDE, HASTA, limite=limite)
    assert bd.params[-1] == limite


@pytest.mark.parametrize("argumentos", [
    dict(desde=HASTA, hasta=DESDE), dict(desde="2026-10-01", hasta=HASTA), dict(tabla="no_existe"),
    dict(id_usuario=0), dict(limite=0), dict(limite=1001), dict(limite=True), dict(limite="10"),
])
def test_listar_con_argumentos_invalidos_no_consulta_la_bd(monkeypatch, argumentos):
    bd = BD(monkeypatch)
    datos = dict(desde=DESDE, hasta=HASTA)
    datos.update(argumentos)
    with pytest.raises(ValueError):
        AuditoriaDAO.listar(**datos)
    bd.clase.assert_not_called()
