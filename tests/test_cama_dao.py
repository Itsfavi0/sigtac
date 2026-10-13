from unittest.mock import MagicMock

import mysql.connector
import pytest

from dao import base_dao
from dao.cama_dao import CamaDAO
from models.cama import CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.estados import EstadoCama
from models.excepciones import PersistenciaError


def fila(id_cama=3, codigo="UCI-01", area="Unidad de Cuidados Intensivos (UCI)",
         tipo="Cama UCI con Ventilador", estado="DISPONIBLE"):
    return {"id_cama": id_cama, "codigo": codigo, "nombre_area": area,
            "nombre_tipo_cama": tipo, "nombre_estado_cama": estado}


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, row=None, rows=None, error_en_execute=None):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        self.cursor.fetchall.return_value = rows or []
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


# ---- Fábrica: cada tipo de la BD crea su subclase
@pytest.mark.parametrize("tipo, clase", [
    ("Cama de Trauma Shock", CamaTraumaShock),
    ("Cama UCI con Ventilador", CamaUCI),
    ("Cama de Observación con Monitor", CamaObservacion),
    ("Cama de Hospitalización General", CamaHospitalizacion),
])
def test_cada_tipo_crea_su_subclase(monkeypatch, tipo, clase):
    BD(monkeypatch, row=fila(tipo=tipo))
    assert type(CamaDAO.buscar_por_id(3)) is clase


def test_la_fila_se_convierte_en_cama(monkeypatch):
    BD(monkeypatch, row=fila(estado="EN LIMPIEZA"))
    cama = CamaDAO.buscar_por_id(3)
    assert (cama.id_cama, cama.codigo, cama.area) == (3, "UCI-01", "Unidad de Cuidados Intensivos (UCI)")
    assert cama.estado is EstadoCama.EN_LIMPIEZA


def test_la_compatibilidad_sale_del_polimorfismo(monkeypatch):
    # La regla vive en el modelo: el DAO solo elige la subclase correcta
    BD(monkeypatch, row=fila(tipo="Cama UCI con Ventilador"))
    cama = CamaDAO.buscar_por_id(3)
    assert cama.es_compatible(2) and not cama.es_compatible(3)


def test_tipo_desconocido_lanza_value_error(monkeypatch):
    BD(monkeypatch, row=fila(tipo="Cama Pediátrica"))
    with pytest.raises(ValueError, match="Tipo de cama"):
        CamaDAO.buscar_por_id(3)


def test_estado_desconocido_lanza_value_error(monkeypatch):
    BD(monkeypatch, row=fila(estado="ROTA"))
    with pytest.raises(ValueError):
        CamaDAO.buscar_por_id(3)


# ---- Búsquedas
def test_buscar_por_id(monkeypatch):
    bd = BD(monkeypatch, row=fila())
    CamaDAO.buscar_por_id(3)
    assert "c.id_cama = %s" in bd.sql and bd.params == (3,)


def test_buscar_por_codigo_limpia_espacios(monkeypatch):
    bd = BD(monkeypatch, row=fila())
    assert CamaDAO.buscar_por_codigo("  UCI-01 ").codigo == "UCI-01"
    assert "c.codigo = %s" in bd.sql and bd.params == ("UCI-01",)
    assert "UCI-01" not in bd.sql  # el dato viaja aparte, nunca dentro del SQL


@pytest.mark.parametrize("codigo", ["", "   ", None, 5])
def test_codigo_invalido_se_rechaza_sin_consultar_la_bd(monkeypatch, codigo):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        CamaDAO.buscar_por_codigo(codigo)
    bd.clase.assert_not_called()


@pytest.mark.parametrize("metodo, argumento", [("buscar_por_id", 99), ("buscar_por_codigo", "XXX-99")])
def test_inexistente_devuelve_none(monkeypatch, metodo, argumento):
    BD(monkeypatch, row=None)
    assert getattr(CamaDAO, metodo)(argumento) is None


# ---- Listados
def test_listar_activas_devuelve_todas_en_cualquier_estado(monkeypatch):
    bd = BD(monkeypatch, rows=[fila(estado="OCUPADA"), fila(id_cama=6, codigo="OBS-01",
                               tipo="Cama de Observación con Monitor", estado="DISPONIBLE")])
    camas = CamaDAO.listar_activas()
    assert [c.codigo for c in camas] == ["UCI-01", "OBS-01"]
    assert [type(c) for c in camas] == [CamaUCI, CamaObservacion]
    assert "nombre_estado_cama = %s" not in bd.sql
    assert bd.sql.endswith("ORDER BY a.nombre_area, c.codigo")


def test_listar_disponibles_filtra_por_estado_con_parametro(monkeypatch):
    bd = BD(monkeypatch, rows=[fila()])
    assert len(CamaDAO.listar_disponibles()) == 1
    assert "e.nombre_estado_cama = %s" in bd.sql
    assert bd.params == ("DISPONIBLE",)  # el valor sale del Enum, no está escrito en el SQL


@pytest.mark.parametrize("metodo", ["listar_activas", "listar_disponibles"])
def test_listado_vacio_devuelve_lista_vacia(monkeypatch, metodo):
    BD(monkeypatch, rows=[])
    assert getattr(CamaDAO, metodo)() == []


@pytest.mark.parametrize("llamada", [
    lambda: CamaDAO.buscar_por_id(1),
    lambda: CamaDAO.buscar_por_codigo("UCI-01"),
    CamaDAO.listar_activas,
    CamaDAO.listar_disponibles,
])
def test_todas_las_consultas_excluyen_camas_dadas_de_baja(monkeypatch, llamada):
    bd = BD(monkeypatch, row=fila(), rows=[fila()])
    llamada()
    assert "c.estado_registro = TRUE" in bd.sql


def test_error_de_bd_se_propaga_como_persistencia_error(monkeypatch):
    BD(monkeypatch, error_en_execute=mysql.connector.Error("boom"))
    with pytest.raises(PersistenciaError):
        CamaDAO.listar_disponibles()
