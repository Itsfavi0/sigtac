from decimal import Decimal

import pytest

from utils.numeros import texto_decimal


@pytest.mark.parametrize("valor, texto", [
    (37.5, "37,5"),
    (39.0, "39"),             # sin ceros de sobra
    (Decimal("8.50"), "8,5"),  # como llega de la BD
    (120, "120"),
    (0, "0"),
])
def test_sin_decimales_fijos_usa_coma_y_quita_ceros(valor, texto):
    assert texto_decimal(valor) == texto


@pytest.mark.parametrize("valor, decimales, texto", [
    (45, 1, "45,0"),
    (59.94, 1, "59,9"),
    (12.06, 1, "12,1"),
    (100.0, 1, "100,0"),
])
def test_con_decimales_fijos_siempre_esa_cantidad(valor, decimales, texto):
    assert texto_decimal(valor, decimales) == texto
