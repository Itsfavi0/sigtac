from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta

import pytest

from models.excepciones import NivelTriajeInvalidoError, ReglaNegocioError
from models.triaje import EpisodioEmergencia, SignosVitales, Sintoma, Triaje, ordenar_por_prioridad

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


def test_sintomas_del_triaje():
    triaje = nuevo_triaje()
    tos, fiebre = Sintoma(10, "Tos Leve", 0.5), Sintoma(6, "Fiebre Alta (> 39°C)", 4.0)
    triaje.agregar_sintoma(tos)
    triaje.agregar_sintoma(fiebre)
    assert triaje.sintomas == (tos, fiebre)


def test_un_sintoma_no_se_registra_dos_veces():
    triaje = nuevo_triaje()
    triaje.agregar_sintoma(Sintoma(10, "Tos Leve", 0.5))
    with pytest.raises(ValueError, match="ya está registrado"):
        triaje.agregar_sintoma(Sintoma(10, "Tos Leve", 0.5))
    assert len(triaje.sintomas) == 1


@pytest.mark.parametrize("sintoma", [None, 10, "Tos"])
def test_agregar_sintoma_exige_un_sintoma(sintoma):
    with pytest.raises(ValueError):
        nuevo_triaje().agregar_sintoma(sintoma)


def test_los_sintomas_son_de_solo_lectura():
    triaje = nuevo_triaje()
    with pytest.raises(AttributeError):
        triaje.sintomas.append(Sintoma(1, "x", 1.0))


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


@pytest.mark.parametrize("campo, valor", [
    ("fc", -5), ("fc", 500), ("fr", -1), ("fr", 200), ("temp", 3.6), ("temp", 368.0), ("pa_sis", 5000),
])
def test_rechaza_valores_fisiologicamente_imposibles(campo, valor):
    datos = dict(pa_sis=120, pa_dia=80, fc=75, fr=16, temp=36.8, sato2=98, id_si=1)
    datos[campo] = valor
    with pytest.raises(ValueError, match=campo):
        SignosVitales(**datos)


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


def episodio_con_triaje():
    ep = nuevo_episodio()
    ep.agregar_triaje(nuevo_triaje())
    return ep


def test_asignar_cama_y_dar_alta_flujo_completo():
    ep = episodio_con_triaje()
    ep.asignar_cama()
    assert ep.estado == EpisodioEmergencia.ESTADO_EN_ATENCION
    ep.dar_alta()
    assert ep.estado == EpisodioEmergencia.ESTADO_ALTA
    assert ep.fecha_alta is not None


def test_no_se_puede_asignar_cama_sin_triaje():  # RN-01
    with pytest.raises(ReglaNegocioError):
        nuevo_episodio().asignar_cama()


def test_no_se_puede_asignar_cama_si_todos_los_triajes_estan_anulados():  # RN-01
    ep = episodio_con_triaje()
    ep.obtener_triaje_actual().anular()
    with pytest.raises(ReglaNegocioError):
        ep.asignar_cama()


def test_no_se_puede_asignar_cama_dos_veces():
    ep = episodio_con_triaje()
    ep.asignar_cama()
    with pytest.raises(ReglaNegocioError):
        ep.asignar_cama()


@pytest.mark.parametrize("preparar", [lambda ep: None, lambda ep: ep.agregar_triaje(nuevo_triaje())])
def test_no_se_puede_dar_de_alta_sin_cama(preparar):
    ep = nuevo_episodio()
    preparar(ep)
    with pytest.raises(ReglaNegocioError):
        ep.dar_alta()
    assert ep.fecha_alta is None


def test_triaje_actual_ignora_triajes_anulados():
    ep = nuevo_episodio()
    valido = nuevo_triaje(3, AHORA, id_triaje=1)
    anulado = nuevo_triaje(1, AHORA + timedelta(hours=1), id_triaje=2)
    anulado.anular()
    ep.agregar_triaje(valido)
    ep.agregar_triaje(anulado)
    assert ep.obtener_triaje_actual() is valido


def test_con_la_misma_hora_gana_el_ultimo_triaje_agregado():
    # La BD guarda la hora con segundos: dos triajes del mismo segundo no deben resolverse al azar.
    ep = nuevo_episodio()
    primero = nuevo_triaje(3, AHORA, id_triaje=1)
    segundo = nuevo_triaje(2, AHORA, id_triaje=2)
    ep.agregar_triaje(primero)
    ep.agregar_triaje(segundo)
    assert ep.obtener_triaje_actual() is segundo


def test_historial_de_triajes_y_signos_en_orden_y_de_solo_lectura():  # RN-09
    ep = nuevo_episodio()
    t1, t2 = nuevo_triaje(3, id_triaje=1), nuevo_triaje(2, id_triaje=2)
    t2.anular()
    sv = SignosVitales(120, 80, 75, 16, 36.8, 98, id_si=1)
    ep.agregar_triaje(t1)
    ep.agregar_triaje(t2)
    ep.agregar_signos_vitales(sv)
    assert ep.triajes == (t1, t2)  # incluye el anulado
    assert ep.signos_vitales == (sv,)
    with pytest.raises(AttributeError):
        ep.triajes.append(t1)  # es una tupla: el historial no se modifica desde fuera


def test_episodio_se_reconstruye_con_los_datos_de_la_bd():
    ingreso, alta = datetime(2026, 10, 21, 8, 0), datetime(2026, 10, 21, 14, 30)
    ep = EpisodioEmergencia(7, 2, "Fiebre", estado="ALTA MÉDICA", fecha_ingreso=ingreso, fecha_alta=alta, activo=False)
    assert (ep.fecha_ingreso, ep.fecha_alta, ep.activo) == (ingreso, alta, False)
    assert ep.estado is EpisodioEmergencia.ESTADO_ALTA


def test_episodio_nuevo_toma_la_hora_actual_y_esta_activo():
    ep = nuevo_episodio()
    assert ep.fecha_ingreso is not None and ep.fecha_alta is None and ep.activo is True


# ---- Episodio cerrado: no admite triajes ni signos nuevos
SIGNOS = SignosVitales(120, 80, 75, 16, 36.8, 98, id_si=None)


@pytest.mark.parametrize("estado", ["ALTA MÉDICA", "REFERIDO", "FUGADO / ABANDONO"])
def test_episodio_cerrado_no_admite_triaje_ni_signos(estado):
    ep = EpisodioEmergencia(1, 1, "Dolor torácico", estado=estado)
    assert ep.cerrado
    with pytest.raises(ReglaNegocioError, match="triaje"):
        ep.agregar_triaje(nuevo_triaje())
    with pytest.raises(ReglaNegocioError, match="signos"):
        ep.agregar_signos_vitales(SIGNOS)
    assert ep.triajes == () and ep.signos_vitales == ()


def test_episodio_anulado_no_admite_triaje_ni_signos():  # RN-11
    ep = nuevo_episodio()
    ep.anular()
    assert ep.cerrado
    with pytest.raises(ReglaNegocioError, match="anulado"):
        ep.agregar_triaje(nuevo_triaje())
    with pytest.raises(ReglaNegocioError, match="anulado"):
        ep.agregar_signos_vitales(SIGNOS)


@pytest.mark.parametrize("estado", ["EN ESPERA DE TRIAJE", "EN ESPERA DE CAMA", "EN ATENCIÓN (CON CAMA)"])
def test_episodio_abierto_admite_triaje_y_signos(estado):  # RN-09: reevaluar a quien sigue en emergencia
    ep = EpisodioEmergencia(1, 1, "Dolor torácico", estado=estado)
    assert not ep.cerrado
    ep.agregar_signos_vitales(SIGNOS)
    ep.agregar_triaje(nuevo_triaje())
    assert len(ep.triajes) == 1 and len(ep.signos_vitales) == 1


def test_episodio_cerrado_se_reconstruye_con_su_historial():
    t, sv = nuevo_triaje(), SIGNOS
    ep = EpisodioEmergencia(1, 1, "x", estado="ALTA MÉDICA", triajes=[t], signos_vitales=[sv])
    assert ep.triajes == (t,) and ep.signos_vitales == (sv,)
    assert ep.estado is EpisodioEmergencia.ESTADO_ALTA


def test_reconstruir_con_historial_no_cambia_el_estado():
    # agregar_triaje pasaría a EN ESPERA DE CAMA; el constructor respeta el estado guardado
    ep = EpisodioEmergencia(1, 1, "x", triajes=[nuevo_triaje()])
    assert ep.estado is EpisodioEmergencia.ESTADO_EN_ESPERA_TRIAJE


def test_el_historial_del_constructor_es_una_copia():
    origen = [nuevo_triaje()]
    ep = EpisodioEmergencia(1, 1, "x", triajes=origen)
    origen.append(nuevo_triaje(id_triaje=2))
    assert len(ep.triajes) == 1


# ---- Cancelar la asignación de cama
def test_cancelar_asignacion_vuelve_a_espera_de_cama():
    ep = episodio_con_triaje()
    ep.asignar_cama()
    ep.cancelar_asignacion()
    assert ep.estado == EpisodioEmergencia.ESTADO_EN_ESPERA
    ep.asignar_cama()  # puede recibir otra cama
    assert ep.estado == EpisodioEmergencia.ESTADO_EN_ATENCION


@pytest.mark.parametrize("estado", ["EN ESPERA DE TRIAJE", "EN ESPERA DE CAMA", "ALTA MÉDICA"])
def test_solo_se_cancela_la_asignacion_de_un_episodio_en_atencion(estado):
    ep = EpisodioEmergencia(1, 1, "x", estado=estado)
    with pytest.raises(ReglaNegocioError):
        ep.cancelar_asignacion()
    assert ep.estado == estado


def test_estado_inexistente_se_rechaza():
    with pytest.raises(ValueError):
        EpisodioEmergencia(1, 1, "motivo", estado="INVENTADO")


# ---- Síntoma inmutable
def test_sintoma_expone_su_peso_clinico():
    assert Sintoma(1, "Tos leve", 0.5).peso_clinico == 0.5


def test_sintoma_es_inmutable():
    sintoma = Sintoma(1, "Tos leve", 0.5)
    with pytest.raises(FrozenInstanceError):
        sintoma.peso_clinico = 10


def test_sintoma_rechaza_peso_negativo():
    with pytest.raises(ValueError):
        Sintoma(1, "Tos leve", -1)


@pytest.mark.parametrize("campo, valor", [("fc", "75"), ("temp", None), ("sato2", True), ("pa_sis", [120])])
def test_signos_vitales_deben_ser_numeros(campo, valor):
    datos = dict(pa_sis=120, pa_dia=80, fc=75, fr=16, temp=36.8, sato2=98, id_si=None)
    datos[campo] = valor
    with pytest.raises(ValueError, match=f"{campo} debe ser un número"):
        SignosVitales(**datos)


def test_signos_vitales_aceptan_enteros_y_decimales():
    assert SignosVitales(120, 80, 75, 16, 37, 98.0, id_si=None).a_diccionario()["temp"] == 37


# ---- Nivel actual y cola de espera
def test_nivel_actual_es_el_del_triaje_vigente():
    ep = nuevo_episodio()
    assert ep.nivel_actual is None
    ep.agregar_triaje(nuevo_triaje(3, AHORA, 1))
    reevaluado = nuevo_triaje(4, AHORA + timedelta(minutes=30), 2)
    reevaluado.reclasificar(2, "Empeoró el dolor y bajó la saturación.")
    ep.agregar_triaje(reevaluado)
    assert ep.nivel_actual == 2


def en_espera(id_episodio, nivel, minutos_desde_ingreso):
    ep = EpisodioEmergencia(id_episodio, 1, "Motivo", estado=EpisodioEmergencia.ESTADO_EN_ESPERA,
                            fecha_ingreso=AHORA - timedelta(minutes=minutos_desde_ingreso))
    if nivel is not None:
        ep.agregar_triaje(nuevo_triaje(nivel, AHORA, id_episodio))
    return ep


def ids(episodios):
    return [e.id_episodio for e in episodios]


def test_la_cola_ordena_por_nivel_y_luego_por_llegada():
    cola = [en_espera(1, 3, 60), en_espera(2, 1, 5), en_espera(3, 3, 90), en_espera(4, 2, 10)]
    assert ids(ordenar_por_prioridad(cola)) == [2, 4, 3, 1]


def test_a_igual_nivel_e_ingreso_va_primero_el_id_menor():
    assert ids(ordenar_por_prioridad([en_espera(7, 3, 10), en_espera(5, 3, 10)])) == [5, 7]


def test_sin_triaje_van_al_final_por_orden_de_llegada():
    cola = [en_espera(1, None, 5), en_espera(2, 5, 1), en_espera(3, None, 30)]
    assert ids(ordenar_por_prioridad(cola)) == [2, 3, 1]


def test_ordenar_no_modifica_la_lista_original():
    cola = [en_espera(1, 3, 5), en_espera(2, 1, 5)]
    ordenar_por_prioridad(cola)
    assert ids(cola) == [1, 2]
