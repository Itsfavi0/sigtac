from datetime import date, datetime

import pytest

from controllers.periodo import ANIO_MAXIMO, ANIO_MINIMO, rango_de_dias


def test_incluye_el_ultimo_dia_completo():
    assert rango_de_dias(date(2026, 10, 1), date(2026, 10, 31)) == (datetime(2026, 10, 1), datetime(2026, 11, 1))


def test_un_solo_dia():
    assert rango_de_dias(date(2026, 12, 31), date(2026, 12, 31)) == (datetime(2026, 12, 31), datetime(2027, 1, 1))


def test_los_anios_limite_se_aceptan():  # valores límite del rango de DATETIME de MySQL
    inicio, fin = rango_de_dias(date(ANIO_MINIMO, 1, 1), date(ANIO_MAXIMO, 12, 31))
    assert (inicio, fin) == (datetime(1000, 1, 1), datetime(9999, 1, 1))


@pytest.mark.parametrize("desde, hasta, mensaje", [
    (date(2026, 10, 31), date(2026, 10, 1), "posterior"),
    (datetime(2026, 10, 1, 8), date(2026, 10, 31), "date"),   # datetime es subclase de date: se rechaza
    ("2026-10-01", date(2026, 10, 31), "date"),
    (date(2026, 10, 1), None, "date"),
    (date(2026, 10, 1), date(9999, 12, 31), "años"),          # sumarle un día desbordaría date
    (date(999, 12, 31), date(2026, 10, 1), "años"),
])
def test_periodo_invalido(desde, hasta, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        rango_de_dias(desde, hasta)
