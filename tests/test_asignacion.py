from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta

import pytest

from models.asignacion import AsignacionCama, SolicitudLimpieza

INICIO = datetime(2026, 10, 21, 9, 0)


# ---- AsignacionCama
def test_asignacion_sin_liberar_esta_vigente():  # RN-05
    assert AsignacionCama(1, 1, 1, 2, INICIO).vigente is True


def test_asignacion_liberada_no_esta_vigente():
    assert AsignacionCama(1, 1, 1, 2, INICIO, INICIO + timedelta(hours=3)).vigente is False


def test_liberacion_en_el_mismo_instante_se_acepta():  # límite de CH_asignacion_fechas
    assert AsignacionCama(1, 1, 1, 2, INICIO, INICIO).vigente is False


def test_liberacion_anterior_a_la_asignacion_se_rechaza():  # CH_asignacion_fechas
    with pytest.raises(ValueError, match="fecha_liberacion"):
        AsignacionCama(1, 1, 1, 2, INICIO, INICIO - timedelta(seconds=1))


def test_asignacion_es_inmutable():
    asignacion = AsignacionCama(1, 1, 1, 2, INICIO)
    with pytest.raises(FrozenInstanceError):
        asignacion.fecha_liberacion = INICIO


# ---- SolicitudLimpieza
def test_solicitud_sin_atender_esta_pendiente():
    assert SolicitudLimpieza(1, 4, "UCI-02", INICIO).pendiente is True


def test_solicitud_atendida():
    solicitud = SolicitudLimpieza(1, 4, "UCI-02", INICIO, 4, INICIO + timedelta(minutes=20))
    assert solicitud.pendiente is False and solicitud.id_empleado == 4


def test_solicitud_atendida_sin_empleado_se_rechaza():
    with pytest.raises(ValueError, match="empleado"):
        SolicitudLimpieza(1, 4, "UCI-02", INICIO, None, INICIO + timedelta(minutes=20))


def test_atencion_anterior_a_la_solicitud_se_rechaza():  # CH_limpieza_fechas
    with pytest.raises(ValueError, match="fecha_atencion"):
        SolicitudLimpieza(1, 4, "UCI-02", INICIO, 4, INICIO - timedelta(seconds=1))


def test_solicitud_es_inmutable():
    solicitud = SolicitudLimpieza(1, 4, "UCI-02", INICIO)
    with pytest.raises(FrozenInstanceError):
        solicitud.fecha_atencion = INICIO
