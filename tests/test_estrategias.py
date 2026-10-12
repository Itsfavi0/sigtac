import pytest

from models.estrategias import ReglaManchester, ReglaMINSA
from models.excepciones import SignosVitalesIncompletosError
from models.triaje import Sintoma


def sintomas(peso_total):
    """Un único síntoma con el peso indicado (sin síntomas si el peso es 0)."""
    return [Sintoma(1, "síntoma", peso_total)] if peso_total else []


VITALES_NORMALES_MANCHESTER = {"sato2": 98, "pa_sis": 120}
VITALES_NORMALES_MINSA = {"temp": 37.0, "fc": 80}


# ---- Manchester
@pytest.mark.parametrize("peso, vitales, esperado", [
    (10, {}, 1),                 # peso alto
    (0, {"sato2": 89}, 1),       # hipoxemia
    (0, {"sato2": 90}, 5),       # límite: 90 ya no es crítico
    (0, {"pa_sis": 79}, 1),      # shock
    (0, {"pa_sis": 80}, 5),      # límite
    (7, {}, 2),
    (0, {"pa_sis": 181}, 2),     # hipertensión severa
    (0, {"pa_sis": 180}, 5),     # límite
    (4, {}, 3),
    (1, {}, 4),
    (0, {}, 5),
])
def test_manchester_clasifica(peso, vitales, esperado):
    signos = {**VITALES_NORMALES_MANCHESTER, **vitales}
    assert ReglaManchester().clasificar(signos, sintomas(peso)) == esperado


def test_manchester_suma_el_peso_de_varios_sintomas():
    varios = [Sintoma(1, "a", 5), Sintoma(2, "b", 5)]
    assert ReglaManchester().clasificar(VITALES_NORMALES_MANCHESTER, varios) == 1


@pytest.mark.parametrize("signos", [{"pa_sis": 120}, {"sato2": 98}, {"sato2": None, "pa_sis": 120}, {}])
def test_manchester_exige_signos_vitales(signos):
    with pytest.raises(SignosVitalesIncompletosError):
        ReglaManchester().clasificar(signos, [])


# ---- MINSA
@pytest.mark.parametrize("peso, vitales, esperado", [
    (9, {}, 1),
    (0, {"fc": 131}, 1),
    (0, {"fc": 130}, 5),         # límite
    (6, {}, 2),
    (3, {}, 3),
    (0, {"temp": 39.5}, 3),      # fiebre muy alta
    (0, {"temp": 39.4}, 5),
    (1, {}, 4),
    (0, {}, 5),
])
def test_minsa_clasifica(peso, vitales, esperado):
    signos = {**VITALES_NORMALES_MINSA, **vitales}
    assert ReglaMINSA().clasificar(signos, sintomas(peso)) == esperado


@pytest.mark.parametrize("signos", [{"fc": 80}, {"temp": 37.0}, {"temp": 37.0, "fc": None}, {}])
def test_minsa_exige_signos_vitales(signos):
    with pytest.raises(SignosVitalesIncompletosError):
        ReglaMINSA().clasificar(signos, [])


def test_mensaje_de_error_indica_que_signos_faltan():
    with pytest.raises(SignosVitalesIncompletosError, match="temp, fc"):
        ReglaMINSA().clasificar({}, [])


# ---- Contrato común (polimorfismo)
@pytest.mark.parametrize("estrategia", [ReglaManchester(), ReglaMINSA()])
def test_toda_estrategia_devuelve_nivel_valido_y_una_justificacion(estrategia):
    signos = {**VITALES_NORMALES_MANCHESTER, **VITALES_NORMALES_MINSA}
    assert estrategia.clasificar(signos, sintomas(5)) in range(1, 6)
    assert estrategia.justificar()
