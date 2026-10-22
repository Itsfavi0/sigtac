from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from dao import base_dao
from dao import transaccion as transaccion_mod
from dao.episodio_dao import EpisodioDAO
from models.estados import EstadoEpisodio
from models.excepciones import ReglaNegocioError
from models.triaje import EpisodioEmergencia, Triaje

INGRESO = datetime(2026, 10, 21, 8, 0)


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, row=None, filas_por_consulta=None, rowcount=1, lastrowid=None):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        self.cursor.fetchall.side_effect = list(filas_por_consulta or [])
        self.cursor.rowcount = rowcount
        self.cursor.lastrowid = lastrowid
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        self.clase.return_value.obtener_conexion.return_value = conexion
        self.clase.return_value.en_transaccion = False
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)
        monkeypatch.setattr(transaccion_mod, "ConexionBD", self.clase)

    @property
    def bd(self):
        return self.clase.return_value

    def sentencias(self) -> list[tuple[str, tuple]]:
        return [(" ".join(c.args[0].split()), c.args[1]) for c in self.cursor.execute.call_args_list]


def fila(**cambios):
    datos = {"id_episodio": 2, "id_paciente": 2, "motivo_consulta": "Caída de segundo piso",
             "nombre_estado_episodio": "EN ESPERA DE CAMA", "fecha_ingreso": INGRESO, "fecha_alta": None,
             "estado_registro": 1}
    datos.update(cambios)
    return datos


# ---- crear
def test_crear_registra_el_episodio_en_espera_de_triaje(monkeypatch):
    bd = BD(monkeypatch, lastrowid=9)
    assert EpisodioDAO.crear(EpisodioEmergencia(None, 2, "  Fiebre persistente  ")) == 9
    sql, params = bd.sentencias()[0]
    assert sql.startswith("INSERT INTO episodio_emergencia")
    assert "fecha_ingreso" not in sql  # la pone MySQL
    assert params == (2, "Fiebre persistente", "EN ESPERA DE TRIAJE")


def episodio_anulado():
    ep = EpisodioEmergencia(None, 2, "Fiebre")
    ep.anular()
    return ep


@pytest.mark.parametrize("episodio, mensaje", [
    ("episodio", "EpisodioEmergencia"),
    (EpisodioEmergencia(5, 2, "Fiebre"), "ya tiene id"),
    (episodio_anulado(), "anulado"),
    (EpisodioEmergencia(None, None, "Fiebre"), "id_paciente"),
    (EpisodioEmergencia(None, 0, "Fiebre"), "id_paciente"),
    (EpisodioEmergencia(None, 2, "   "), "motivo"),
    (EpisodioEmergencia(None, 2, None), "motivo"),
])
def test_crear_con_datos_invalidos_no_llega_a_la_bd(monkeypatch, episodio, mensaje):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError, match=mensaje):
        EpisodioDAO.crear(episodio)
    bd.clase.assert_not_called()


def test_el_log_no_incluye_el_motivo_de_consulta(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    BD(monkeypatch, lastrowid=9)
    EpisodioDAO.crear(EpisodioEmergencia(None, 2, "Dolor intenso en el pecho"))
    assert "pecho" not in caplog.text and "id_episodio=9" in caplog.text


# ---- buscar_por_id: el episodio con su historial
def test_buscar_por_id_devuelve_el_episodio_con_signos_y_triajes(monkeypatch):
    signos = [{"id_si": 2, "pa_sis": 130, "pa_dia": 85, "fc": 95, "fr": 20, "temp": Decimal("36.80"), "sato2": 97}]
    triajes = [{"id_triaje": 2, "nivel_final": 2, "nivel_sugerido": 3, "id_empleado": 3, "fecha_hora": INGRESO,
                "justificacion": "Antecedente de fractura expuesta previa.", "estado_registro": 1}]
    sintomas = [{"id_triaje": 2, "id_sintoma": 7, "nombre_sintoma": "Dolor Abdominal Intenso",
                 "peso_clinico": Decimal("5.00")}]
    bd = BD(monkeypatch, row=fila(), filas_por_consulta=[signos, triajes, sintomas])
    ep = EpisodioDAO.buscar_por_id(2)
    assert (ep.id_episodio, ep.id_paciente, ep.fecha_ingreso, ep.activo) == (2, 2, INGRESO, True)
    assert ep.estado is EstadoEpisodio.EN_ESPERA  # se conserva el estado leído de la BD
    assert [sv.id_si for sv in ep.signos_vitales] == [2]
    assert [t.id_triaje for t in ep.triajes] == [2]
    assert ep.obtener_triaje_actual().nivel_final == 2
    assert ep.triajes[0].sintomas[0].id_sintoma == 7
    assert "WHERE ep.id_episodio = %s" in bd.sentencias()[0][0]


def test_buscar_episodio_en_atencion_no_cambia_su_estado_al_agregar_los_triajes(monkeypatch):
    triajes = [{"id_triaje": 1, "nivel_final": 1, "nivel_sugerido": 1, "id_empleado": 3, "fecha_hora": INGRESO,
                "justificacion": None, "estado_registro": 1}]
    BD(monkeypatch, row=fila(nombre_estado_episodio="EN ATENCIÓN (CON CAMA)"),
       filas_por_consulta=[[], triajes, []])
    assert EpisodioDAO.buscar_por_id(1).estado is EstadoEpisodio.EN_ATENCION


def test_buscar_episodio_anulado_y_con_alta(monkeypatch):
    alta = datetime(2026, 10, 21, 14, 0)
    BD(monkeypatch, row=fila(nombre_estado_episodio="ALTA MÉDICA", fecha_alta=alta, estado_registro=0),
       filas_por_consulta=[[], []])
    ep = EpisodioDAO.buscar_por_id(2)
    assert (ep.estado, ep.fecha_alta, ep.activo) == (EstadoEpisodio.ALTA, alta, False)


def test_un_episodio_dado_de_alta_se_carga_con_su_historial(monkeypatch):
    # Antes el historial se cargaba con agregar_triaje, que ahora rechaza episodios cerrados.
    triajes = [{"id_triaje": 1, "nivel_final": 3, "nivel_sugerido": 3, "id_empleado": 3, "fecha_hora": INGRESO,
                "justificacion": None, "estado_registro": 1}]
    BD(monkeypatch, row=fila(nombre_estado_episodio="ALTA MÉDICA", fecha_alta=datetime(2026, 10, 21, 14, 0)),
       filas_por_consulta=[[], triajes, []])
    ep = EpisodioDAO.buscar_por_id(2)
    assert ep.cerrado and [t.id_triaje for t in ep.triajes] == [1]


def test_un_episodio_en_espera_de_triaje_con_historial_conserva_su_estado(monkeypatch):
    # El constructor no aplica la transición de agregar_triaje: el estado es el de la BD.
    triajes = [{"id_triaje": 1, "nivel_final": 3, "nivel_sugerido": 3, "id_empleado": 3, "fecha_hora": INGRESO,
                "justificacion": None, "estado_registro": 0}]
    BD(monkeypatch, row=fila(nombre_estado_episodio="EN ESPERA DE TRIAJE"), filas_por_consulta=[[], triajes, []])
    assert EpisodioDAO.buscar_por_id(2).estado is EstadoEpisodio.EN_ESPERA_TRIAJE


def test_buscar_inexistente_devuelve_none_sin_mas_consultas(monkeypatch):
    bd = BD(monkeypatch, row=None)
    assert EpisodioDAO.buscar_por_id(99) is None
    assert len(bd.sentencias()) == 1


def test_estado_desconocido_en_la_bd_se_rechaza(monkeypatch):
    BD(monkeypatch, row=fila(nombre_estado_episodio="PERDIDO"), filas_por_consulta=[[], []])
    with pytest.raises(ValueError):
        EpisodioDAO.buscar_por_id(2)


@pytest.mark.parametrize("id_episodio", [0, None, "2"])
def test_buscar_con_id_invalido_no_consulta_la_bd(monkeypatch, id_episodio):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        EpisodioDAO.buscar_por_id(id_episodio)
    bd.clase.assert_not_called()


# ---- cambiar_estado: UPDATE condicional
def episodio_triado(id_episodio=1):
    ep = EpisodioEmergencia(id_episodio, 3, "Fiebre")
    ep.agregar_triaje(Triaje(None, 3, 3, INGRESO))  # el modelo lo pasa a EN ESPERA DE CAMA (RN-01)
    return ep


def test_cambiar_estado_es_condicional_al_estado_anterior(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    EpisodioDAO.cambiar_estado(episodio_triado(), EstadoEpisodio.EN_ESPERA_TRIAJE)
    sql, params = bd.sentencias()[0]
    assert sql.startswith("UPDATE episodio_emergencia SET id_estado_ep = (SELECT")
    assert "WHERE id_episodio = %s AND estado_registro = TRUE AND id_estado_ep = (SELECT" in sql
    assert params == ("EN ESPERA DE CAMA", False, 1, "EN ESPERA DE TRIAJE")


def test_al_dar_de_alta_la_fecha_la_pone_mysql(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    ep = episodio_triado()
    ep.asignar_cama()
    ep.dar_alta()
    EpisodioDAO.cambiar_estado(ep, EstadoEpisodio.EN_ATENCION)
    sql, params = bd.sentencias()[0]
    assert "fecha_alta = IF(%s, NOW(), fecha_alta)" in sql
    assert params == ("ALTA MÉDICA", True, 1, "EN ATENCIÓN (CON CAMA)")


def test_si_otro_usuario_cambio_el_episodio_lanza_regla_negocio_error(monkeypatch):
    BD(monkeypatch, rowcount=0)
    with pytest.raises(ReglaNegocioError, match="otro usuario"):
        EpisodioDAO.cambiar_estado(episodio_triado(), EstadoEpisodio.EN_ESPERA_TRIAJE)


def test_cambiar_estado_no_abre_una_transaccion_propia(monkeypatch):
    # Es una sola sentencia; dentro de la transacción del controlador, su excepción la deshace.
    bd = BD(monkeypatch, rowcount=1)
    EpisodioDAO.cambiar_estado(episodio_triado(), "EN ESPERA DE TRIAJE")
    bd.bd.iniciar_transaccion.assert_not_called()


@pytest.mark.parametrize("episodio, anterior, mensaje", [
    ("ep", EstadoEpisodio.EN_ESPERA_TRIAJE, "EpisodioEmergencia"),
    (episodio_triado(id_episodio=None), EstadoEpisodio.EN_ESPERA_TRIAJE, "id_episodio"),
    (episodio_triado(), "ESPERANDO", "Estado anterior"),
    (episodio_triado(), None, "Estado anterior"),
    (episodio_triado(), EstadoEpisodio.EN_ESPERA, "no cambió"),
])
def test_cambiar_estado_con_datos_invalidos_no_llega_a_la_bd(monkeypatch, episodio, anterior, mensaje):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError, match=mensaje):
        EpisodioDAO.cambiar_estado(episodio, anterior)
    bd.clase.assert_not_called()
