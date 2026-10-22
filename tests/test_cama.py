import pytest

from models.cama import Cama, CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.excepciones import CamaEstadoInvalidoError


def nueva_cama(estado=Cama.ESTADO_DISPONIBLE):
    return CamaObservacion(1, "OBS-01", "Sala de Observación", estado)


def test_cama_es_abstracta():
    with pytest.raises(TypeError):
        Cama(1, "X-01", "Área")


def test_estado_inicial_por_defecto_es_disponible():
    assert nueva_cama().estado == Cama.ESTADO_DISPONIBLE


# ---- Transiciones válidas
def test_ciclo_completo_de_una_cama():
    cama = nueva_cama()
    cama.reservar()
    assert cama.estado == Cama.ESTADO_RESERVADA
    cama.ocupar()
    assert cama.estado == Cama.ESTADO_OCUPADA
    cama.dar_alta()
    assert cama.estado == Cama.ESTADO_EN_LIMPIEZA  # RN-07: no queda disponible
    cama.liberar_limpieza()
    assert cama.estado == Cama.ESTADO_DISPONIBLE   # RN-08


def test_ocupar_directamente_desde_disponible():
    cama = nueva_cama()
    cama.ocupar()
    assert cama.estado == Cama.ESTADO_OCUPADA


# ---- Transiciones inválidas
@pytest.mark.parametrize("estado", [
    Cama.ESTADO_RESERVADA, Cama.ESTADO_OCUPADA, Cama.ESTADO_EN_LIMPIEZA, Cama.ESTADO_FUERA_SERVICIO,
])
def test_reservar_solo_si_esta_disponible(estado):  # RN-05
    with pytest.raises(CamaEstadoInvalidoError):
        nueva_cama(estado).reservar()


@pytest.mark.parametrize("estado", [Cama.ESTADO_OCUPADA, Cama.ESTADO_EN_LIMPIEZA, Cama.ESTADO_FUERA_SERVICIO])
def test_ocupar_solo_desde_disponible_o_reservada(estado):
    with pytest.raises(CamaEstadoInvalidoError):
        nueva_cama(estado).ocupar()


@pytest.mark.parametrize("estado", [
    Cama.ESTADO_DISPONIBLE, Cama.ESTADO_RESERVADA, Cama.ESTADO_EN_LIMPIEZA, Cama.ESTADO_FUERA_SERVICIO,
])
def test_dar_alta_solo_si_esta_ocupada(estado):
    with pytest.raises(CamaEstadoInvalidoError):
        nueva_cama(estado).dar_alta()


@pytest.mark.parametrize("estado", [
    Cama.ESTADO_DISPONIBLE, Cama.ESTADO_RESERVADA, Cama.ESTADO_OCUPADA, Cama.ESTADO_FUERA_SERVICIO,
])
def test_liberar_limpieza_solo_desde_limpieza(estado):
    with pytest.raises(CamaEstadoInvalidoError):
        nueva_cama(estado).liberar_limpieza()


# ---- Cancelar una reserva
def test_cancelar_reserva_devuelve_la_cama_a_disponible_sin_limpieza():
    cama = nueva_cama()
    cama.reservar()
    cama.cancelar_reserva()
    assert cama.estado == Cama.ESTADO_DISPONIBLE  # no se usó: no pasa por limpieza


@pytest.mark.parametrize("estado", [
    Cama.ESTADO_DISPONIBLE, Cama.ESTADO_OCUPADA, Cama.ESTADO_EN_LIMPIEZA, Cama.ESTADO_FUERA_SERVICIO,
])
def test_solo_se_cancela_una_cama_reservada(estado):
    # Una cama ocupada ya se usó: debe salir por dar_alta() y pasar por limpieza (RN-07)
    cama = nueva_cama(estado)
    with pytest.raises(CamaEstadoInvalidoError):
        cama.cancelar_reserva()
    assert cama.estado == estado


# ---- Fuera de servicio
@pytest.mark.parametrize("estado", [
    Cama.ESTADO_DISPONIBLE, Cama.ESTADO_RESERVADA, Cama.ESTADO_OCUPADA,
    Cama.ESTADO_EN_LIMPIEZA, Cama.ESTADO_FUERA_SERVICIO,
])
def test_fuera_de_servicio_se_puede_decretar_desde_cualquier_estado(estado):
    cama = nueva_cama(estado)
    cama.fuera_de_servicio()
    assert cama.estado == Cama.ESTADO_FUERA_SERVICIO


def test_volver_a_servicio():
    cama = nueva_cama(Cama.ESTADO_FUERA_SERVICIO)
    cama.volver_a_servicio()
    assert cama.estado == Cama.ESTADO_DISPONIBLE


def test_volver_a_servicio_exige_estar_fuera_de_servicio():
    with pytest.raises(CamaEstadoInvalidoError):
        nueva_cama().volver_a_servicio()


# ---- Compatibilidad con el nivel de triaje (polimorfismo)
@pytest.mark.parametrize("clase, niveles_validos", [
    (CamaTraumaShock, {1}),
    (CamaUCI, {1, 2}),
    (CamaObservacion, {2, 3, 4}),
    (CamaHospitalizacion, {3, 4, 5}),
])
def test_es_compatible_por_tipo_de_cama(clase, niveles_validos):
    cama = clase(1, "C-01", "Área", Cama.ESTADO_DISPONIBLE)
    for nivel in range(1, 6):
        assert cama.es_compatible(nivel) == (nivel in niveles_validos), f"{clase.__name__} nivel {nivel}"


def test_estado_inexistente_se_rechaza():
    with pytest.raises(ValueError):
        nueva_cama("INVENTADO")


def test_el_estado_sigue_comparandose_con_texto():
    # EstadoCama es un StrEnum: los valores coinciden con los de la BD
    assert nueva_cama().estado == "DISPONIBLE"
    assert str(nueva_cama(Cama.ESTADO_EN_LIMPIEZA).estado) == "EN LIMPIEZA"
