from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import mysql.connector
import pytest

from dao import base_dao
from dao import transaccion as transaccion_mod
from dao.triaje_dao import TriajeDAO
from models.excepciones import NivelTriajeInvalidoError, PersistenciaError
from models.triaje import SignosVitales, Sintoma, Triaje

AHORA = datetime(2026, 10, 21, 10, 0)
JUSTIFICACION = "Antecedente de fractura expuesta en la misma extremidad."


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, filas_por_consulta=None, lastrowid=None, en_transaccion=False):
        self.cursor = MagicMock()
        self.cursor.fetchall.side_effect = list(filas_por_consulta or [])  # una lista de filas por SELECT
        self.cursor.lastrowid = lastrowid
        self.cursor.rowcount = 1
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        self.clase.return_value.obtener_conexion.return_value = conexion
        self.clase.return_value.en_transaccion = en_transaccion
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)
        monkeypatch.setattr(transaccion_mod, "ConexionBD", self.clase)

    @property
    def bd(self):
        return self.clase.return_value

    def sentencias(self) -> list[tuple[str, tuple]]:
        return [(" ".join(c.args[0].split()), c.args[1]) for c in self.cursor.execute.call_args_list]


def signos(id_si=None):
    return SignosVitales(165, 98, 118, 26, 37.2, 89, id_si=id_si)


def triaje(nivel=2, sintomas=(), id_triaje=None, id_empleado=3):
    t = Triaje(id_triaje, nivel, id_empleado, AHORA)
    for s in sintomas:
        t.agregar_sintoma(s)
    return t


TORACICO = Sintoma(2, "Dolor Torácico Opresivo", 8.5)
DISNEA = Sintoma(3, "Dificultad Respiratoria Severa (Disnea)", 8.0)


# ---- Catálogo de síntomas
def test_listar_sintomas(monkeypatch):
    bd = BD(monkeypatch, filas_por_consulta=[[
        {"id_sintoma": 2, "nombre_sintoma": "Dolor Torácico Opresivo", "peso_clinico": Decimal("8.50")},
    ]])
    sintomas = TriajeDAO.listar_sintomas()
    assert sintomas == [Sintoma(2, "Dolor Torácico Opresivo", 8.5)]
    assert isinstance(sintomas[0].peso_clinico, float)  # DECIMAL llega como Decimal
    assert bd.sentencias()[0][0].endswith("ORDER BY nombre_sintoma")


# ---- registrar: signos + triaje + síntomas en una transacción
def test_registrar_guarda_signos_triaje_y_sintomas(monkeypatch):
    bd = BD(monkeypatch, lastrowid=12)
    assert TriajeDAO.registrar(1, signos(), triaje(2, [TORACICO, DISNEA])) == 12
    (sql_sv, p_sv), (sql_t, p_t), (sql_s1, p_s1), (sql_s2, p_s2) = bd.sentencias()
    assert sql_sv.startswith("INSERT INTO signos_vitales")
    assert p_sv == (1, 165, 98, 118, 26, 37.2, 89)
    assert sql_t.startswith("INSERT INTO triaje")
    assert "(SELECT id_nivel FROM nivel_triaje WHERE numero = %s)" in sql_t
    assert p_t == (1, 2, 2, 3, None)  # nivel final, sugerido, empleado, sin justificación
    assert sql_s1.startswith("INSERT INTO triaje_sintoma")
    assert (p_s1, p_s2) == ((12, 2), (12, 3))


def test_registrar_un_triaje_reclasificado_guarda_ambos_niveles_y_la_justificacion(monkeypatch):  # RN-10
    bd = BD(monkeypatch, lastrowid=12)
    t = triaje(3)
    t.reclasificar(2, JUSTIFICACION)
    TriajeDAO.registrar(1, signos(), t)
    assert bd.sentencias()[1][1] == (1, 2, 3, 3, JUSTIFICACION)


def test_registrar_sin_sintomas(monkeypatch):
    bd = BD(monkeypatch, lastrowid=12)
    TriajeDAO.registrar(1, signos(), triaje())
    assert len(bd.sentencias()) == 2


def test_la_fecha_la_pone_mysql(monkeypatch):
    bd = BD(monkeypatch, lastrowid=12)
    TriajeDAO.registrar(1, signos(), triaje())
    assert all("fecha_hora" not in sql for sql, _ in bd.sentencias())


def test_registrar_usa_una_transaccion_y_la_confirma(monkeypatch):
    bd = BD(monkeypatch, lastrowid=12)
    TriajeDAO.registrar(1, signos(), triaje(2, [TORACICO]))
    bd.bd.iniciar_transaccion.assert_called_once()
    bd.bd.terminar_transaccion.assert_called_once_with(confirmar=True)


def test_si_falla_un_sintoma_se_deshace_todo(monkeypatch):
    bd = BD(monkeypatch, lastrowid=12)
    bd.cursor.execute.side_effect = [None, None, mysql.connector.Error("FK sintoma")]
    with pytest.raises(PersistenciaError):
        TriajeDAO.registrar(1, signos(), triaje(2, [TORACICO]))
    bd.bd.terminar_transaccion.assert_called_once_with(confirmar=False)


def test_dentro_de_otra_transaccion_se_une_a_ella(monkeypatch):
    bd = BD(monkeypatch, lastrowid=12, en_transaccion=True)
    TriajeDAO.registrar(1, signos(), triaje())
    bd.bd.iniciar_transaccion.assert_not_called()
    bd.bd.terminar_transaccion.assert_not_called()


def anulado():
    t = triaje()
    t.anular()
    return t


@pytest.mark.parametrize("id_episodio, sv, t, mensaje", [
    (0, signos(), triaje(), "id_episodio"),
    ("1", signos(), triaje(), "id_episodio"),
    (1, {"pa_sis": 120}, triaje(), "SignosVitales"),
    (1, signos(), "triaje", "Triaje"),
    (1, signos(id_si=4), triaje(), "RN-09"),
    (1, signos(), triaje(id_triaje=7), "RN-09"),
    (1, signos(), anulado(), "anulado"),
    (1, signos(), triaje(id_empleado=None), "id_empleado"),
])
def test_datos_invalidos_no_llegan_a_la_bd(monkeypatch, id_episodio, sv, t, mensaje):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError, match=mensaje):
        TriajeDAO.registrar(id_episodio, sv, t)
    bd.clase.assert_not_called()


def test_el_log_no_incluye_la_justificacion(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    BD(monkeypatch, lastrowid=12)
    t = triaje(3)
    t.reclasificar(2, JUSTIFICACION)
    TriajeDAO.registrar(1, signos(), t)
    assert "fractura" not in caplog.text
    assert "id_triaje=12" in caplog.text


# ---- Lectura del historial
def fila_triaje(id_triaje, final, sugerido, justificacion=None, estado_registro=1, fecha=AHORA):
    return {"id_triaje": id_triaje, "nivel_final": final, "nivel_sugerido": sugerido, "id_empleado": 3,
            "fecha_hora": fecha, "justificacion": justificacion, "estado_registro": estado_registro}


def fila_sintoma(id_triaje, sintoma):
    return {"id_triaje": id_triaje, "id_sintoma": sintoma.id_sintoma, "nombre_sintoma": sintoma.nombre,
            "peso_clinico": Decimal(str(sintoma.peso_clinico))}


def test_listar_por_episodio_reconstruye_el_historial(monkeypatch):  # RN-09
    bd = BD(monkeypatch, filas_por_consulta=[
        [fila_triaje(1, 3, 3), fila_triaje(2, 2, 3, JUSTIFICACION), fila_triaje(3, 1, 1, estado_registro=0)],
        [fila_sintoma(1, TORACICO), fila_sintoma(2, TORACICO), fila_sintoma(2, DISNEA)],
    ])
    t1, t2, t3 = TriajeDAO.listar_por_episodio(1)
    assert (t1.nivel_final, t1.es_reclasificacion, t1.activo) == (3, False, True)
    assert (t2.nivel_sugerido, t2.nivel_final, t2.justificacion) == (3, 2, JUSTIFICACION)  # RN-10
    assert t3.activo is False  # RN-11: el anulado también se devuelve
    assert t1.sintomas == (TORACICO,) and t2.sintomas == (TORACICO, DISNEA) and t3.sintomas == ()
    (sql_t, p_t), (sql_s, p_s) = bd.sentencias()
    assert "LEFT JOIN nivel_triaje ns" in sql_t and sql_t.endswith("ORDER BY t.fecha_hora, t.id_triaje")
    assert p_t == (1,) and p_s == (1,)


def test_triaje_sin_nivel_sugerido_usa_el_final(monkeypatch):
    BD(monkeypatch, filas_por_consulta=[[fila_triaje(1, 2, None)], []])
    (t,) = TriajeDAO.listar_por_episodio(1)
    assert (t.nivel_sugerido, t.nivel_final, t.es_reclasificacion) == (2, 2, False)


def test_episodio_sin_triajes_no_consulta_los_sintomas(monkeypatch):
    bd = BD(monkeypatch, filas_por_consulta=[[]])
    assert TriajeDAO.listar_por_episodio(1) == []
    assert len(bd.sentencias()) == 1


def test_fila_con_nivel_invalido_no_se_convierte(monkeypatch):
    # Las reglas del modelo se aplican también a lo que llega de la BD
    BD(monkeypatch, filas_por_consulta=[[fila_triaje(1, 9, 9)], []])
    with pytest.raises(NivelTriajeInvalidoError):
        TriajeDAO.listar_por_episodio(1)


def test_listar_signos_por_episodio(monkeypatch):
    bd = BD(monkeypatch, filas_por_consulta=[[
        {"id_si": 1, "pa_sis": 165, "pa_dia": 98, "fc": 118, "fr": 26, "temp": Decimal("37.20"), "sato2": 89},
    ]])
    (sv,) = TriajeDAO.listar_signos_por_episodio(1)
    assert sv.id_si == 1
    assert sv.a_diccionario() == {"pa_sis": 165, "pa_dia": 98, "fc": 118, "fr": 26, "temp": 37.2, "sato2": 89}
    assert isinstance(sv.a_diccionario()["temp"], float)
    assert bd.sentencias()[0][0].endswith("ORDER BY fecha_hora, id_si")


@pytest.mark.parametrize("metodo", [TriajeDAO.listar_por_episodio, TriajeDAO.listar_signos_por_episodio])
@pytest.mark.parametrize("id_episodio", [0, None, "1", True])
def test_listar_con_id_invalido_no_consulta_la_bd(monkeypatch, metodo, id_episodio):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        metodo(id_episodio)
    bd.clase.assert_not_called()


def test_triaje_dao_no_tiene_metodos_para_modificar_ni_borrar():  # RN-09
    publicos = {nombre for nombre in vars(TriajeDAO) if not nombre.startswith("_")}
    assert publicos == {"listar_sintomas", "registrar", "listar_por_episodio", "listar_signos_por_episodio",
                        "listar_historial"}


# ---- listar_historial (varios episodios a la vez)
def fila_triaje_ep(id_episodio, id_triaje, nivel=3):
    return {"id_episodio": id_episodio, "id_triaje": id_triaje, "nivel_final": nivel, "nivel_sugerido": nivel,
            "id_empleado": 3, "fecha_hora": AHORA, "justificacion": None, "estado_registro": 1}


def test_listar_historial_agrupa_por_episodio(monkeypatch):
    bd = BD(monkeypatch, filas_por_consulta=[
        [fila_triaje_ep(1, 10), fila_triaje_ep(1, 11, nivel=2), fila_triaje_ep(2, 12)],
        [{"id_triaje": 11, "id_sintoma": 2, "nombre_sintoma": "Dolor Torácico Opresivo", "peso_clinico": Decimal("8.5")},
         {"id_triaje": 99, "id_sintoma": 3, "nombre_sintoma": "Disnea", "peso_clinico": Decimal("8")}],
        [{"id_episodio": 2, "id_si": 5, "pa_sis": 120, "pa_dia": 80, "fc": 85, "fr": 18,
          "temp": Decimal("37.20"), "sato2": 97}],
    ])
    triajes, signos = TriajeDAO.listar_historial("paciente", 1)
    assert {k: [t.id_triaje for t in v] for k, v in triajes.items()} == {1: [10, 11], 2: [12]}
    # el síntoma de un triaje que no se leyó (id 99) se ignora
    assert [s.id_sintoma for s in triajes[1][1].sintomas] == [2] and triajes[1][0].sintomas == ()
    assert list(signos) == [2] and signos[2][0].a_diccionario()["temp"] == 37.2
    assert all(params == (1,) and "ep.id_paciente = %s" in sql for sql, params in bd.sentencias())


def test_listar_historial_sin_triajes_no_consulta_los_sintomas(monkeypatch):
    bd = BD(monkeypatch, filas_por_consulta=[[], []])
    assert TriajeDAO.listar_historial("estado", "EN ESPERA DE CAMA") == ({}, {})
    assert len(bd.sentencias()) == 2


@pytest.mark.parametrize("filtro", ["id_episodio", "", "estado; DROP TABLE triaje"])
def test_listar_historial_con_filtro_fuera_de_la_lista_blanca(monkeypatch, filtro):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError, match="Filtro"):
        TriajeDAO.listar_historial(filtro, 1)
    bd.clase.assert_not_called()
