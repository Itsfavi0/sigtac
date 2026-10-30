from decimal import Decimal

import pytest

from models.estrategias import SIN_CRITERIOS, Clasificacion, EstrategiaTriaje, ReglaManchester, ReglaMINSA, condicion
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


# ---- Criterios: las condiciones cumplidas en el nivel elegido
@pytest.mark.parametrize("peso, vitales, esperado", [
    (0, {"sato2": 89}, Clasificacion(1, ("SatO₂ 89 % < 90 %",))),
    (0, {"pa_sis": 79}, Clasificacion(1, ("PA sistólica 79 mmHg < 80 mmHg",))),
    (10, {"sato2": 85, "pa_sis": 70},   # nivel 1 por tres condiciones: aparecen todas, en orden
     Clasificacion(1, ("Peso de los síntomas 10 ≥ 10", "SatO₂ 85 % < 90 %", "PA sistólica 70 mmHg < 80 mmHg"))),
    (7, {}, Clasificacion(2, ("Peso de los síntomas 7 ≥ 7",))),
    (0, {"pa_sis": 181}, Clasificacion(2, ("PA sistólica 181 mmHg > 180 mmHg",))),
    (4, {}, Clasificacion(3, ("Peso de los síntomas 4 ≥ 4",))),
    (1, {}, Clasificacion(4, ("Peso de los síntomas 1 ≥ 1",))),
    (0, {"sato2": 90, "pa_sis": 180}, Clasificacion(5, (SIN_CRITERIOS,))),  # límites: ninguno se cumple
])
def test_manchester_explica_su_nivel(peso, vitales, esperado):
    assert ReglaManchester().evaluar({**VITALES_NORMALES_MANCHESTER, **vitales}, sintomas(peso)) == esperado


def test_un_nivel_urgente_no_muestra_criterios_de_niveles_menores():
    # Peso 8.5 cumple ≥ 7 (nivel 2) y ≥ 4 (nivel 3), pero con SatO₂ 88 el nivel es 1: solo cuenta lo del nivel 1
    resultado = ReglaManchester().evaluar({"sato2": 88, "pa_sis": 120}, sintomas(8.5))
    assert resultado == Clasificacion(1, ("SatO₂ 88 % < 90 %",))


def test_el_peso_de_varios_sintomas_se_muestra_sumado():
    varios = [Sintoma(1, "a", 2.5), Sintoma(2, "b", 2)]
    assert ReglaManchester().evaluar(VITALES_NORMALES_MANCHESTER, varios).criterios == ("Peso de los síntomas 4.5 ≥ 4",)


@pytest.mark.parametrize("peso, vitales, esperado", [
    (0, {"fc": 131}, Clasificacion(1, ("FC 131 lpm > 130 lpm",))),
    (9, {}, Clasificacion(1, ("Peso de los síntomas 9 ≥ 9",))),
    (6, {}, Clasificacion(2, ("Peso de los síntomas 6 ≥ 6",))),
    (0, {"temp": 39.5}, Clasificacion(3, ("Temperatura 39.5 °C ≥ 39.5 °C",))),
    (3, {"temp": 40.1}, Clasificacion(3, ("Peso de los síntomas 3 ≥ 3", "Temperatura 40.1 °C ≥ 39.5 °C"))),
    (1, {}, Clasificacion(4, ("Peso de los síntomas 1 ≥ 1",))),
    (0, {"fc": 130, "temp": 39.4}, Clasificacion(5, (SIN_CRITERIOS,))),
])
def test_minsa_explica_su_nivel(peso, vitales, esperado):
    assert ReglaMINSA().evaluar({**VITALES_NORMALES_MINSA, **vitales}, sintomas(peso)) == esperado


@pytest.mark.parametrize("simbolo, valor, cumple", [
    ("<", 89, True), ("<", 90, False),
    (">", 181, True), (">", 180, False),
    ("≥", 7, True), ("≥", 6.9, False),
])
def test_condicion_compara_y_arma_el_texto(simbolo, valor, cumple):
    umbral = {"<": 90, ">": 180, "≥": 7}[simbolo]
    assert condicion("X", valor, simbolo, umbral, " u") == (cumple, f"X {valor:g} u {simbolo} {umbral} u")


def test_condicion_muestra_un_decimal_sin_ceros_de_sobra():
    assert condicion("Peso", Decimal("5.00"), "≥", 4) == (True, "Peso 5 ≥ 4")
    assert condicion("Temp", Decimal("39.50"), "≥", 39.5, " °C") == (True, "Temp 39.5 °C ≥ 39.5 °C")


def test_condicion_rechaza_un_simbolo_desconocido():
    with pytest.raises(KeyError):
        condicion("X", 1, "<=", 2)


# ---- Contrato común (polimorfismo)
@pytest.mark.parametrize("estrategia", [ReglaManchester(), ReglaMINSA()])
def test_toda_estrategia_devuelve_nivel_valido_y_una_justificacion(estrategia):
    signos = {**VITALES_NORMALES_MANCHESTER, **VITALES_NORMALES_MINSA}
    assert estrategia.clasificar(signos, sintomas(5)) in range(1, 6)
    assert estrategia.justificar()


@pytest.mark.parametrize("estrategia", [ReglaManchester(), ReglaMINSA()])
@pytest.mark.parametrize("peso", [0, 1, 3, 4, 6, 7, 9, 10])
def test_clasificar_es_el_nivel_de_evaluar_y_siempre_hay_criterios(estrategia, peso):
    signos = {**VITALES_NORMALES_MANCHESTER, **VITALES_NORMALES_MINSA}
    resultado = estrategia.evaluar(signos, sintomas(peso))
    assert estrategia.clasificar(signos, sintomas(peso)) == resultado.nivel
    assert resultado.criterios and all(isinstance(c, str) and c for c in resultado.criterios)


def test_una_estrategia_nueva_solo_implementa_evaluar_y_justificar():
    # Template Method: clasificar() lo da la clase base a partir de evaluar()
    class Fija(EstrategiaTriaje):
        def evaluar(self, signos_vitales, sintomas):
            return Clasificacion(2, ("motivo",))

        def justificar(self):
            return "prueba"

    assert Fija().clasificar({}, []) == 2


def test_una_estrategia_sin_evaluar_no_se_puede_crear():
    class Incompleta(EstrategiaTriaje):
        def justificar(self):
            return "prueba"

    with pytest.raises(TypeError):
        Incompleta()
