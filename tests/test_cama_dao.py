from unittest.mock import MagicMock

import mysql.connector
import pytest

from dao import base_dao
from dao import transaccion as transaccion_mod
from dao.cama_dao import CamaDAO
from models.cama import CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.estados import EstadoCama
from models.excepciones import CamaNoDisponibleError, PersistenciaError


def fila(id_cama=3, codigo="UCI-01", area="Unidad de Cuidados Intensivos (UCI)",
         tipo="Cama UCI con Ventilador", estado="DISPONIBLE"):
    return {"id_cama": id_cama, "codigo": codigo, "nombre_area": area,
            "nombre_tipo_cama": tipo, "nombre_estado_cama": estado}


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, row=None, rows=None, error_en_execute=None, rowcount=1, en_transaccion=False):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        self.cursor.fetchall.return_value = rows or []
        self.cursor.rowcount = rowcount
        if error_en_execute:
            self.cursor.execute.side_effect = error_en_execute
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        self.clase.return_value.obtener_conexion.return_value = conexion
        # transaccion() pregunta a ConexionBD si ya hay una transacción abierta
        self.clase.return_value.en_transaccion = en_transaccion
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)
        monkeypatch.setattr(transaccion_mod, "ConexionBD", self.clase)

    @property
    def bd(self):
        """La instancia simulada de ConexionBD (para revisar iniciar/terminar_transaccion)."""
        return self.clase.return_value

    def sentencias(self) -> list[tuple[str, tuple]]:
        return [(" ".join(c.args[0].split()), c.args[1]) for c in self.cursor.execute.call_args_list]

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


# ---- cambiar_estado: UPDATE condicional + historial, en una transacción
def cama_reservada():
    """Una cama que el modelo ya pasó de DISPONIBLE a RESERVADA (aún sin guardar)."""
    cama = CamaUCI(3, "UCI-01", "Unidad de Cuidados Intensivos (UCI)", EstadoCama.DISPONIBLE)
    cama.reservar()
    return cama


def test_cambiar_estado_actualiza_y_registra_el_historial(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    CamaDAO.cambiar_estado(cama_reservada(), EstadoCama.DISPONIBLE)
    (update, p_update), (insert, p_insert) = bd.sentencias()
    assert update.startswith("UPDATE cama SET id_estado_cama = (SELECT id_estado_cama FROM estado_cama")
    assert p_update == ("RESERVADA", 3, "DISPONIBLE")
    assert insert.startswith("INSERT INTO historial_estado_cama")
    assert p_insert == (3, "RESERVADA")


def test_el_update_es_condicional_al_estado_anterior(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    CamaDAO.cambiar_estado(cama_reservada(), EstadoCama.DISPONIBLE)
    update = bd.sentencias()[0][0]
    assert "WHERE id_cama = %s AND estado_registro = TRUE AND id_estado_cama = (SELECT" in update


def test_cambiar_estado_usa_una_transaccion_y_la_confirma(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    CamaDAO.cambiar_estado(cama_reservada(), EstadoCama.DISPONIBLE)
    bd.bd.iniciar_transaccion.assert_called_once()
    bd.bd.terminar_transaccion.assert_called_once_with(confirmar=True)


def test_el_estado_anterior_se_acepta_como_texto(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    CamaDAO.cambiar_estado(cama_reservada(), "DISPONIBLE")
    assert bd.sentencias()[0][1][2] == "DISPONIBLE"


def test_si_otro_usuario_cambio_la_cama_lanza_error_y_no_registra_historial(monkeypatch):
    bd = BD(monkeypatch, rowcount=0)  # el UPDATE no encontró la cama en el estado esperado
    with pytest.raises(CamaNoDisponibleError, match="UCI-01"):
        CamaDAO.cambiar_estado(cama_reservada(), EstadoCama.DISPONIBLE)
    assert len(bd.sentencias()) == 1  # no llegó al INSERT del historial
    bd.bd.terminar_transaccion.assert_called_once_with(confirmar=False)


def test_si_falla_el_historial_se_deshace_el_cambio_de_estado(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    bd.cursor.execute.side_effect = [None, mysql.connector.Error("fallo en el INSERT")]
    with pytest.raises(PersistenciaError):
        CamaDAO.cambiar_estado(cama_reservada(), EstadoCama.DISPONIBLE)
    bd.bd.terminar_transaccion.assert_called_once_with(confirmar=False)


def test_dentro_de_otra_transaccion_se_une_a_ella(monkeypatch):
    bd = BD(monkeypatch, rowcount=1, en_transaccion=True)  # el controlador ya abrió una
    CamaDAO.cambiar_estado(cama_reservada(), EstadoCama.DISPONIBLE)
    bd.bd.iniciar_transaccion.assert_not_called()
    bd.bd.terminar_transaccion.assert_not_called()  # la confirma el bloque del controlador
    assert len(bd.sentencias()) == 2


@pytest.mark.parametrize("cama, anterior, mensaje", [
    ("UCI-01", EstadoCama.DISPONIBLE, "Cama"),
    (None, EstadoCama.DISPONIBLE, "Cama"),
    (CamaUCI(None, "UCI-09", "UCI", EstadoCama.RESERVADA), EstadoCama.DISPONIBLE, "id"),
    (CamaUCI(0, "UCI-09", "UCI", EstadoCama.RESERVADA), EstadoCama.DISPONIBLE, "id"),
    (CamaUCI(True, "UCI-09", "UCI", EstadoCama.RESERVADA), EstadoCama.DISPONIBLE, "id"),
    (CamaUCI(3, "UCI-01", "UCI", EstadoCama.RESERVADA), "LIBRE", "Estado anterior"),
    (CamaUCI(3, "UCI-01", "UCI", EstadoCama.RESERVADA), "disponible", "Estado anterior"),
    (CamaUCI(3, "UCI-01", "UCI", EstadoCama.RESERVADA), None, "Estado anterior"),
    (CamaUCI(3, "UCI-01", "UCI", EstadoCama.RESERVADA), EstadoCama.RESERVADA, "no cambió"),
])
def test_datos_invalidos_no_llegan_a_la_bd(monkeypatch, cama, anterior, mensaje):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError, match=mensaje):
        CamaDAO.cambiar_estado(cama, anterior)
    bd.clase.assert_not_called()


@pytest.mark.parametrize("transicion, anterior, nuevo", [
    (lambda c: c.reservar(), EstadoCama.DISPONIBLE, EstadoCama.RESERVADA),
    (lambda c: c.ocupar(), EstadoCama.RESERVADA, EstadoCama.OCUPADA),
    (lambda c: c.dar_alta(), EstadoCama.OCUPADA, EstadoCama.EN_LIMPIEZA),        # RN-07
    (lambda c: c.liberar_limpieza(), EstadoCama.EN_LIMPIEZA, EstadoCama.DISPONIBLE),  # RN-08
    (lambda c: c.fuera_de_servicio(), EstadoCama.OCUPADA, EstadoCama.FUERA_SERVICIO),
    (lambda c: c.volver_a_servicio(), EstadoCama.FUERA_SERVICIO, EstadoCama.DISPONIBLE),
])
def test_cada_transicion_del_modelo_se_guarda(monkeypatch, transicion, anterior, nuevo):
    bd = BD(monkeypatch, rowcount=1)
    cama = CamaObservacion(6, "OBS-01", "Sala de Observación Adultos", anterior)
    transicion(cama)
    CamaDAO.cambiar_estado(cama, anterior)
    assert bd.sentencias()[0][1] == (nuevo.value, 6, anterior.value)
    assert bd.sentencias()[1][1] == (6, nuevo.value)
