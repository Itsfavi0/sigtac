from datetime import datetime, timedelta

import pytest

from models.excepciones import NivelTriajeInvalidoError
from models.triaje import EpisodioEmergencia, SignosVitales, Sintoma, Triaje

AHORA = datetime(2026, 10, 11, 12, 0)


def nuevo_triaje(nivel=3, fecha=AHORA, id_triaje=1):
    return Triaje(id_triaje, nivel, 3, fecha)


# ---- Triaje
@pytest.mark.parametrize("nivel", [0, 6, -1])
def test_triaje_rechaza_nivel_sugerido_fuera_de_rango(nivel):
    with pytest.raises(NivelTriajeInvalidoError):
        nuevo_triaje(nivel)


def test_por_defecto_el_nivel_final_es_el_sugerido():
    triaje = nuevo_triaje(3)
    assert triaje.nivel_final == 3
    assert not triaje.es_reclasificacion


def test_reclasificar_cambia_el_nivel_final_y_guarda_la_justificacion():  # RN-10
    triaje = nuevo_triaje(3)
    triaje.reclasificar(2, "Antecedente de fractura expuesta en la misma extremidad.")
    assert triaje.nivel_sugerido == 3
    assert triaje.nivel_final == 2
    assert triaje.es_reclasificacion
    assert triaje.justificacion


@pytest.mark.parametrize("justificacion", [None, "", "   ", "corta"])
def test_reclasificar_exige_justificacion_valida(justificacion):  # RN-10
    triaje = nuevo_triaje(3)
    with pytest.raises(ValueError):
        triaje.reclasificar(2, justificacion)
    assert triaje.nivel_final == 3  # no cambió nada


def test_reclasificar_rechaza_nivel_invalido():
    with pytest.raises(NivelTriajeInvalidoError):
        nuevo_triaje(3).reclasificar(9, "Justificación suficientemente larga.")


def test_anular_es_baja_logica():  # RN-11
    triaje = nuevo_triaje()
    assert triaje.activo
    triaje.anular()
    assert not triaje.activo


# ---- Signos vitales
def test_signos_vitales_a_diccionario():
    sv = SignosVitales(120, 80, 75, 16, 36.8, 98, id_si=1)
    assert sv.a_diccionario() == {"pa_sis": 120, "pa_dia": 80, "fc": 75, "fr": 16, "temp": 36.8, "sato2": 98}


@pytest.mark.parametrize("sis, dia", [(80, 80), (70, 90)])
def test_presion_sistolica_debe_superar_la_diastolica(sis, dia):
    with pytest.raises(ValueError):
        SignosVitales(sis, dia, 75, 16, 36.8, 98, id_si=1)


@pytest.mark.parametrize("sato2", [-1, 101])
def test_saturacion_entre_0_y_100(sato2):
    with pytest.raises(ValueError):
        SignosVitales(120, 80, 75, 16, 36.8, sato2, id_si=1)


# ---- Episodio de emergencia
def nuevo_episodio():
    return EpisodioEmergencia(1, 1, "Dolor torácico")


def test_episodio_nuevo_espera_triaje():
    assert nuevo_episodio().estado == EpisodioEmergencia.ESTADO_EN_ESPERA_TRIAJE


def test_primer_triaje_pasa_a_espera_de_cama():  # RN-01
    ep = nuevo_episodio()
    ep.agregar_triaje(nuevo_triaje())
    assert ep.estado == EpisodioEmergencia.ESTADO_EN_ESPERA


def test_sin_triajes_no_hay_triaje_actual():
    assert nuevo_episodio().obtener_triaje_actual() is None


def test_triaje_actual_es_el_mas_reciente_y_se_conserva_el_historial():  # RN-09
    ep = nuevo_episodio()
    viejo = nuevo_triaje(3, AHORA, id_triaje=1)
    nuevo = nuevo_triaje(1, AHORA + timedelta(hours=2), id_triaje=2)
    ep.agregar_triaje(nuevo)   # se agrega primero el más reciente a propósito
    ep.agregar_triaje(viejo)
    assert ep.obtener_triaje_actual() is nuevo
    assert len(ep._historial_triajes) == 2


def test_dar_alta_registra_fecha():
    ep = nuevo_episodio()
    ep.dar_alta()
    assert ep.estado == EpisodioEmergencia.ESTADO_ALTA
    assert ep.fecha_alta is not None


def test_sintoma_expone_su_peso_clinico():
    assert Sintoma(1, "Tos leve", 0.5).peso_clinico == 0.5


# ---- Brechas conocidas de la revisión (xfail strict: cuando se corrijan, el test avisará)
@pytest.mark.xfail(strict=True, reason="Pendiente: asignar_cama no valida que exista un triaje (RN-01)")
def test_no_se_puede_asignar_cama_sin_triaje():
    ep = nuevo_episodio()
    with pytest.raises(Exception):
        ep.asignar_cama()


@pytest.mark.xfail(strict=True, reason="Pendiente: obtener_triaje_actual no ignora los triajes anulados")
def test_triaje_actual_ignora_triajes_anulados():
    ep = nuevo_episodio()
    valido = nuevo_triaje(3, AHORA, id_triaje=1)
    anulado = nuevo_triaje(1, AHORA + timedelta(hours=1), id_triaje=2)
    anulado.anular()
    ep.agregar_triaje(valido)
    ep.agregar_triaje(anulado)
    assert ep.obtener_triaje_actual() is valido
