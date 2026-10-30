from datetime import date, datetime

import pytest

from models.documento import DocumentoIdentidad
from models.persona import Paciente
from views import formato


def paciente(documento=("DNI", "43215619"), nombres="María Elena", apellidos="Salazar Quispe", sexo="F"):
    doc = DocumentoIdentidad(*documento) if documento else None
    return Paciente(1, doc, nombres, apellidos, date(1980, 5, 10), sexo, 1)


def test_nombre_corto():
    assert formato.nombre_corto(paciente()) == "M. Salazar"


def test_nombre_corto_de_un_nn(monkeypatch):
    nn = Paciente.no_identificado("M", 40, 1)
    assert formato.nombre_corto(nn) == f"NN · varón, ~{nn.calcular_edad()} años"


@pytest.mark.parametrize("documento, texto", [
    (("DNI", "43215619"), "DNI 43•••19"),
    (("CE", "X1234567"), "CE X1•••67"),
    (("PAS", "AB1234"), "PAS AB•••34"),  # el número más corto admitido (6)
])
def test_documento_enmascarado(documento, texto):
    assert formato.documento_enmascarado(paciente(documento)) == texto


def test_documento_de_un_nn():
    assert formato.documento_enmascarado(Paciente.no_identificado("F", 30, 1)) == "Sin documento"


@pytest.mark.parametrize("segundos, minutos", [(0, 0), (59, 0), (60, 1), (125, 2), (-300, 0)])
def test_minutos_desde(segundos, minutos):
    inicio = datetime(2026, 10, 27, 10, 0, 0)
    assert formato.minutos_desde(inicio, datetime.fromtimestamp(inicio.timestamp() + segundos)) == minutos


@pytest.mark.parametrize("minutos, texto", [(0, "00 min"), (7, "07 min"), (59, "59 min"), (60, "1 h 00 min"),
                                            (75, "1 h 15 min")])
def test_texto_minutos(minutos, texto):
    assert formato.texto_minutos(minutos) == texto


@pytest.mark.parametrize("nivel, texto", [(1, "Inmediato"), (2, "Plazo 10 min"), (3, "Plazo 60 min"),
                                          (5, "Plazo 240 min")])
def test_texto_plazo(nivel, texto):
    assert formato.texto_plazo(nivel) == texto


@pytest.mark.parametrize("dia, texto", [(date(2026, 10, 26), "Lun, 26 oct 2026"),
                                       (date(2026, 11, 1), "Dom, 1 nov 2026")])
def test_fecha_corta(dia, texto):
    assert formato.fecha_corta(dia) == texto


def test_hora():
    momento = datetime(2026, 10, 27, 9, 5, 7)
    assert (formato.hora(momento), formato.hora(momento, con_segundos=True)) == ("09:05", "09:05:07")


@pytest.mark.parametrize("parte, total, texto", [(15, 36, "42 %"), (0, 36, "0 %"), (36, 36, "100 %"), (0, 0, "—")])
def test_porcentaje(parte, total, texto):
    assert formato.porcentaje(parte, total) == texto


def test_texto_minutos_sin_cero():
    assert formato.texto_minutos(8, con_cero=False) == "8 min"
    assert formato.texto_minutos(75, con_cero=False) == "1 h 15 min"


# ---- Lo que escribe el usuario

@pytest.mark.parametrize("texto, decimales, valor", [
    ("120", False, 120), (" 88 ", False, 88), ("37,5", True, 37.5), ("37.5", True, 37.5), ("38", True, 38.0),
])
def test_leer_numero(texto, decimales, valor):
    assert formato.leer_numero(texto, "Campo", decimales) == valor


@pytest.mark.parametrize("texto, decimales, mensaje", [
    ("", False, "Campo debe ser un número entero."), ("9x", False, "Campo debe ser un número entero."),
    ("37,5", False, "Campo debe ser un número entero."),  # un signo entero no acepta decimales
    ("abc", True, "Campo debe ser un número."),
])
def test_leer_numero_invalido(texto, decimales, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        formato.leer_numero(texto, "Campo", decimales)


def test_leer_fecha():
    assert formato.leer_fecha(" 14/03/1985 ", "La fecha") == date(1985, 3, 14)


@pytest.mark.parametrize("texto", ["", "1985-03-14", "31/02/1985", "14/3/85"])
def test_leer_fecha_invalida(texto):
    with pytest.raises(ValueError, match="La fecha debe tener la forma dd/mm/aaaa"):
        formato.leer_fecha(texto, "La fecha")
