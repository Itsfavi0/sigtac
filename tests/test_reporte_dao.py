from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from dao import base_dao
from dao.reporte_dao import ReporteDAO
from models.estados import EstadoCama, EstadoEpisodio

DESDE, HASTA = datetime(2026, 10, 1), datetime(2026, 11, 1)


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, row=None, rows=None):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        self.cursor.fetchall.return_value = rows or []
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


def test_camas_por_estado(monkeypatch):
    bd = BD(monkeypatch, rows=[{"nombre_estado_cama": "DISPONIBLE", "total": 4},
                               {"nombre_estado_cama": "FUERA DE SERVICIO", "total": 0}])
    assert ReporteDAO.contar_camas_por_estado() == {EstadoCama.DISPONIBLE: 4, EstadoCama.FUERA_SERVICIO: 0}
    # LEFT JOIN desde el catálogo: los estados sin camas también aparecen; las camas de baja no cuentan
    assert "FROM estado_cama e LEFT JOIN cama c" in bd.sql and "c.estado_registro = TRUE" in bd.sql


def test_episodios_por_estado(monkeypatch):
    bd = BD(monkeypatch, rows=[{"nombre_estado_episodio": "EN ESPERA DE CAMA", "total": 2}])
    assert ReporteDAO.contar_episodios_por_estado() == {EstadoEpisodio.EN_ESPERA: 2}
    assert "ep.estado_registro = TRUE" in bd.sql


def test_estado_desconocido_en_la_bd_es_un_error(monkeypatch):
    BD(monkeypatch, rows=[{"nombre_estado_cama": "ROTA", "total": 1}])
    with pytest.raises(ValueError):
        ReporteDAO.contar_camas_por_estado()


def test_ingresos_del_periodo(monkeypatch):
    bd = BD(monkeypatch, row={"total": 12})
    assert ReporteDAO.contar_ingresos(DESDE, HASTA) == 12
    assert bd.params == (DESDE, HASTA)
    assert "fecha_ingreso >= %s AND fecha_ingreso < %s" in bd.sql  # [desde, hasta)


def test_triajes_por_nivel(monkeypatch):
    bd = BD(monkeypatch, rows=[{"numero": n, "total": t} for n, t in [(1, 2), (2, 0), (3, 5), (4, 1), (5, 0)]])
    assert ReporteDAO.contar_triajes_por_nivel(DESDE, HASTA) == {1: 2, 2: 0, 3: 5, 4: 1, 5: 0}
    assert "FROM nivel_triaje n LEFT JOIN triaje t" in bd.sql and bd.params == (DESDE, HASTA)


def test_reclasificaciones(monkeypatch):
    BD(monkeypatch, row={"total": 8, "reclasificados": Decimal("3")})
    assert ReporteDAO.contar_reclasificaciones(DESDE, HASTA) == (8, 3)


@pytest.mark.parametrize("metodo", ["promedio_espera_triaje_min", "promedio_espera_cama_min",
                                    "promedio_estancia_min"])
def test_promedios_en_minutos(monkeypatch, metodo):
    bd = BD(monkeypatch, row={"promedio": Decimal("42.5000")})
    assert getattr(ReporteDAO, metodo)(DESDE, HASTA) == 42.5
    assert "TIMESTAMPDIFF(MINUTE" in bd.sql and bd.params[:2] == (DESDE, HASTA)


@pytest.mark.parametrize("metodo", ["promedio_espera_triaje_min", "promedio_espera_cama_min",
                                    "promedio_estancia_min"])
def test_promedio_sin_datos_es_none(monkeypatch, metodo):
    BD(monkeypatch, row={"promedio": None})
    assert getattr(ReporteDAO, metodo)(DESDE, HASTA) is None


def test_la_espera_de_cama_no_cuenta_las_reservas_canceladas(monkeypatch):
    bd = BD(monkeypatch, row={"promedio": None})
    ReporteDAO.promedio_espera_cama_min(DESDE, HASTA)
    assert "a.estado_registro = TRUE" in bd.sql


@pytest.mark.parametrize("desde, hasta", [
    (HASTA, DESDE), (DESDE, DESDE), (date(2026, 10, 1), HASTA), (DESDE, "2026-11-01"), (None, HASTA),
])
@pytest.mark.parametrize("metodo", ["contar_ingresos", "contar_triajes_por_nivel", "contar_reclasificaciones",
                                    "promedio_espera_triaje_min", "promedio_espera_cama_min", "promedio_estancia_min"])
def test_periodo_invalido_no_consulta_la_bd(monkeypatch, metodo, desde, hasta):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        getattr(ReporteDAO, metodo)(desde, hasta)
    bd.clase.assert_not_called()


def test_reporte_dao_solo_lee():
    publicos = {n for n in vars(ReporteDAO) if not n.startswith("_")}
    assert all(n.startswith(("contar_", "promedio_")) for n in publicos)


def test_la_estancia_solo_cuenta_las_altas_medicas(monkeypatch):
    # fecha_alta guarda también el egreso de referidos y fugados: no deben acortar la estancia.
    bd = BD(monkeypatch, row={"promedio": None})
    ReporteDAO.promedio_estancia_min(DESDE, HASTA)
    assert "nombre_estado_episodio = %s" in bd.sql
    assert bd.params == (DESDE, HASTA, "ALTA MÉDICA")
