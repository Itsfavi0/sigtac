from datetime import datetime
from unittest.mock import MagicMock

import pytest

from models.estados import EstadoCama
from models.excepciones import PersistenciaError, ReglaNegocioError
from prototipo.demo import CamasDemo, TriajeDemo
from views import camas_view
from views.componentes.tabla import SIN_LECTURA
from views.camas_view import (ELIJA_PACIENTE, NADIE_ESPERA, SIN_LECTURA_COMPATIBLES, TEXTO_ELEGIR_CAMA, TEXTO_ELEGIR_CON_CAMA,
                              TEXTO_ELEGIR_MANTENIMIENTO, TEXTO_ELEGIR_PACIENTE, TITULOS, GestionCamasView,
                              sin_compatibles)

AHORA = datetime(2026, 10, 30, 10, 0)


@pytest.fixture
def dialogos(monkeypatch):
    """Los diálogos de la pantalla, anotados en lugar de abrirse. `confirmar` responde lo que diga la prueba."""
    anotados = {"error": [], "info": [], "pregunta": [], "respuesta": True}
    monkeypatch.setattr(camas_view, "mostrar_error", lambda ventana, error: anotados["error"].append(error))
    monkeypatch.setattr(camas_view, "mostrar_info", lambda ventana, texto: anotados["info"].append(texto))

    def confirmar(ventana, pregunta):
        anotados["pregunta"].append(pregunta)
        return anotados["respuesta"]

    monkeypatch.setattr(camas_view, "confirmar", confirmar)
    return anotados


@pytest.fixture
def crear(raiz_tk, dialogos):
    """La pantalla con el controlador de demostración envuelto en MagicMock(wraps=...): reglas reales y llamadas anotadas."""
    def crear(camas=None):
        camas = camas or MagicMock(wraps=CamasDemo(lambda: AHORA))
        vista = GestionCamasView(raiz_tk, camas, reloj=lambda: AHORA)
        vista.camas, vista.dialogos, vista.raiz = camas, dialogos, raiz_tk
        return vista
    return crear


def filas(tabla) -> list[tuple]:
    return [tabla._arbol.item(iid, "values") for iid in tabla._arbol.get_children()]


def elegir(vista, tabla, id_fila):
    tabla.seleccionar(id_fila)
    vista.raiz.update()  # el evento de selección se procesa en el ciclo de Tk


def visible(widget) -> bool:
    return widget.winfo_manager() != ""


def con_cama(vista, codigo):
    """El id_episodio de la fila de esa cama en «Con cama»."""
    return next(id_ep for id_ep, p in vista._con_cama.items() if p.cama.codigo == codigo)


def cama(vista, codigo):
    return next(c for c in vista.camas.mapa_camas() if c.codigo == codigo)


# ---- Al abrir

def test_al_abrir_muestra_la_cola_por_prioridad_y_los_conteos(crear):
    vista = crear()
    assert (vista._tarjeta.titulo, vista._tarjeta.subtitulo) == TITULOS["espera"]
    assert vista._modo.texto("espera") == "Esperan cama (4)"
    assert vista._modo.texto("con_cama") == "Con cama (15)"
    assert [f[0] for f in filas(vista._tabla_cola)] == ["1 · Rojo", "2 · Naranja", "3 · Amarillo", "3 · Amarillo"]
    assert filas(vista._tabla_cola)[0] == ("1 · Rojo", "M. Salazar", "Dolor torácico agudo", "02 min")
    assert vista._tabla_compatibles._vacio.cget("text") == ELIJA_PACIENTE
    assert vista._boton_asignar.cget("text") == TEXTO_ELEGIR_PACIENTE
    assert vista._boton_asignar.cget("state") == "disabled"


def test_si_la_bd_falla_al_abrir_hay_un_solo_aviso(crear):
    camas = MagicMock()
    camas.cola_de_espera.side_effect = PersistenciaError("No se pudo leer la cola.")
    vista = crear(camas=camas)
    assert [str(e) for e in vista.dialogos["error"]] == ["No se pudo leer la cola."]
    # ni «(0)» ni «Nadie espera cama»: no se pudo leer
    assert vista._modo.texto("espera") == "Esperan cama" and vista._modo.texto("con_cama") == "Con cama"
    for tabla in (vista._tabla_cola, vista._tabla_con_cama, vista._tabla_mantenimiento):
        assert tabla.cantidad == 0 and tabla._vacio.cget("text") == SIN_LECTURA
    camas.cola_de_espera.side_effect = None  # la BD volvió
    camas.cola_de_espera.return_value = []
    camas.pacientes_con_cama.return_value = []
    camas.mapa_camas.return_value = []
    vista._recargar()
    assert vista._tabla_cola._vacio.cget("text") == NADIE_ESPERA
    assert vista._modo.texto("espera") == "Esperan cama (0)"


# ---- Esperan cama

def test_al_elegir_un_paciente_se_ven_sus_camas_compatibles(crear):
    vista = crear()
    elegir(vista, vista._tabla_cola, 1)  # nivel 1: trauma shock y UCI
    vista.camas.camas_compatibles.assert_called_with(1)
    assert filas(vista._tabla_compatibles) == [("TS-03", "Trauma shock", "Trauma Shock"), ("UCI-03", "UCI", "UCI"),
                                               ("UCI-06", "UCI", "UCI")]
    assert vista._boton_asignar.cget("text") == TEXTO_ELEGIR_CAMA
    assert vista._boton_asignar.cget("state") == "disabled"


def test_elegir_la_cama_habilita_asignar_con_su_codigo(crear):
    vista = crear()
    elegir(vista, vista._tabla_cola, 2)  # nivel 2: UCI y observación
    assert [f[0] for f in filas(vista._tabla_compatibles)][:2] == ["UCI-03", "UCI-06"]
    elegir(vista, vista._tabla_compatibles, cama(vista, "UCI-06").id_cama)
    assert vista._boton_asignar.cget("text") == "Asignar cama UCI-06"
    assert vista._boton_asignar.cget("state") == "normal"


def test_sin_camas_compatibles_la_tabla_lo_dice_con_el_nivel(crear):
    vista = crear()
    vista.camas.camas_compatibles.return_value = []
    elegir(vista, vista._tabla_cola, 1)
    assert vista._tabla_compatibles._vacio.cget("text") == sin_compatibles(1)
    assert sin_compatibles(1) == "No hay camas disponibles compatibles con el nivel 1 · Rojo."


def test_asignar_reserva_la_cama_y_el_paciente_sale_de_la_cola(crear):
    vista = crear()
    elegir(vista, vista._tabla_cola, 1)
    ts03 = cama(vista, "TS-03").id_cama
    elegir(vista, vista._tabla_compatibles, ts03)
    vista.asignar()
    vista.camas.asignar.assert_called_once_with(1, ts03)
    assert vista.dialogos["info"] == ["Cama TS-03 reservada para M. Salazar. Cuando llegue, márquelo en «Con cama»."]
    assert vista._modo.texto("espera") == "Esperan cama (3)" and vista._modo.texto("con_cama") == "Con cama (16)"
    assert cama(vista, "TS-03").estado == EstadoCama.RESERVADA
    assert vista._boton_asignar.cget("text") == TEXTO_ELEGIR_PACIENTE  # sin elección después de guardar


def test_si_asignar_falla_se_avisa_y_se_conserva_la_eleccion(crear):
    vista = crear()
    elegir(vista, vista._tabla_cola, 2)
    elegir(vista, vista._tabla_compatibles, cama(vista, "UCI-03").id_cama)
    vista.camas.asignar.side_effect = ReglaNegocioError("Otra PC reservó esa cama.")
    vista.asignar()
    assert [str(e) for e in vista.dialogos["error"]] == ["Otra PC reservó esa cama."]
    assert vista.dialogos["info"] == []
    assert vista._tabla_cola.seleccionado() == 2


def test_asignar_sin_eleccion_no_llama_al_controlador(crear):
    vista = crear()
    vista.asignar()
    vista.camas.asignar.assert_not_called()


# ---- Con cama

def test_con_cama_cambia_el_titulo_y_lista_cama_estado_y_paciente(crear):
    vista = crear()
    vista._modo.elegir("con_cama")
    assert (vista._tarjeta.titulo, vista._tarjeta.subtitulo) == TITULOS["con_cama"]
    assert visible(vista._paneles["con_cama"]) and not visible(vista._paneles["espera"])
    primera = filas(vista._tabla_con_cama)[0]
    assert primera[:3] == ("TS-01", "Ocupada", "1 · Rojo")
    assert vista._boton_cama.cget("text") == TEXTO_ELEGIR_CON_CAMA
    assert all(b.cget("state") == "disabled"
               for b in (vista._boton_cama, vista._boton_cancelar, vista._boton_referir, vista._boton_fuga))


def test_una_cama_reservada_ofrece_llego_y_cancelar(crear):
    vista = crear()
    vista._modo.elegir("con_cama")
    elegir(vista, vista._tabla_con_cama, con_cama(vista, "TS-04"))
    assert vista._boton_cama.cget("text") == "Llegó a la cama"
    assert vista._boton_cancelar.cget("state") == "normal" and vista._boton_referir.cget("state") == "normal"


def test_llego_a_la_cama_la_deja_ocupada(crear):
    vista = crear()
    vista._modo.elegir("con_cama")
    elegir(vista, vista._tabla_con_cama, con_cama(vista, "TS-04"))
    vista._accion_principal()
    vista.camas.ocupar.assert_called_once_with(cama(vista, "TS-04").id_cama)
    assert cama(vista, "TS-04").estado == EstadoCama.OCUPADA
    assert vista.dialogos["info"][0].endswith("llegó a la cama TS-04: queda ocupada.")


def test_cancelar_la_reserva_devuelve_al_paciente_a_la_cola(crear):
    vista = crear()
    vista._modo.elegir("con_cama")
    episodio = con_cama(vista, "TS-04")
    elegir(vista, vista._tabla_con_cama, episodio)
    vista.cancelar_reserva()
    vista.camas.cancelar_asignacion.assert_called_once_with(episodio)
    assert vista._modo.texto("espera") == "Esperan cama (5)" and vista._modo.texto("con_cama") == "Con cama (14)"
    assert cama(vista, "TS-04").estado == EstadoCama.DISPONIBLE
    assert vista.dialogos["pregunta"] == []  # se puede deshacer: no pregunta


def test_una_cama_ocupada_ofrece_el_alta_y_no_cancelar(crear):
    vista = crear()
    vista._modo.elegir("con_cama")
    elegir(vista, vista._tabla_con_cama, con_cama(vista, "TS-01"))
    assert vista._boton_cama.cget("text") == "Dar de alta"
    assert vista._boton_cancelar.cget("state") == "disabled"


def test_dar_de_alta_pregunta_y_la_cama_pasa_a_limpieza(crear):  # RN-07
    vista = crear()
    vista._modo.elegir("con_cama")
    episodio = con_cama(vista, "TS-01")
    elegir(vista, vista._tabla_con_cama, episodio)
    vista._accion_principal()
    assert "No se puede deshacer" in vista.dialogos["pregunta"][0]
    assert "la cama TS-01 pasa a limpieza" in vista.dialogos["pregunta"][0]
    vista.camas.dar_alta.assert_called_once_with(episodio)
    assert cama(vista, "TS-01").estado == EstadoCama.EN_LIMPIEZA
    assert vista.dialogos["info"] == ["Alta registrada. La cama TS-01 espera limpieza."]


def test_si_no_confirma_el_alta_no_pasa_nada(crear):
    vista = crear()
    vista.dialogos["respuesta"] = False
    vista._modo.elegir("con_cama")
    elegir(vista, vista._tabla_con_cama, con_cama(vista, "TS-01"))
    vista.dar_alta()
    vista.camas.dar_alta.assert_not_called()
    assert cama(vista, "TS-01").estado == EstadoCama.OCUPADA


@pytest.mark.parametrize("codigo, destino, estado", [
    ("TS-04", "queda disponible", EstadoCama.DISPONIBLE),       # solo reservada: vuelve sin limpieza
    ("TS-01", "pasa a limpieza", EstadoCama.EN_LIMPIEZA),  # ocupada: como en el alta
])
@pytest.mark.parametrize("accion, metodo", [("referir", "referir"), ("registrar_fuga", "registrar_fuga")])
def test_referir_y_fuga_preguntan_y_dicen_que_pasa_con_la_cama(crear, codigo, destino, estado, accion, metodo):
    vista = crear()
    vista._modo.elegir("con_cama")
    episodio = con_cama(vista, codigo)
    elegir(vista, vista._tabla_con_cama, episodio)
    getattr(vista, accion)()
    assert f"la cama {codigo} {destino}. No se puede deshacer." in vista.dialogos["pregunta"][0]
    getattr(vista.camas, metodo).assert_called_once_with(episodio)
    assert cama(vista, codigo).estado == estado
    assert vista.dialogos["info"][0].endswith(f"La cama {codigo} {destino}.")


def test_referir_pregunta_con_el_estado_recien_leido(crear):
    vista = crear()
    vista._modo.elegir("con_cama")
    episodio = con_cama(vista, "TS-04")  # la pantalla la leyó reservada
    elegir(vista, vista._tabla_con_cama, episodio)
    vista.camas.ocupar(cama(vista, "TS-04").id_cama)  # otra PC marca la llegada
    vista.referir()
    assert "la cama TS-04 pasa a limpieza" in vista.dialogos["pregunta"][0]
    assert vista.dialogos["info"] == ["Referencia registrada. La cama TS-04 pasa a limpieza."]


def test_si_otra_pc_ya_dio_el_alta_se_avisa_y_se_recarga(crear):
    vista = crear()
    vista._modo.elegir("con_cama")
    episodio = con_cama(vista, "TS-01")
    elegir(vista, vista._tabla_con_cama, episodio)
    vista.camas.dar_alta.side_effect = ReglaNegocioError("El episodio no tiene una cama asignada.")
    lecturas = vista.camas.pacientes_con_cama.call_count
    vista.dar_alta()
    assert [str(e) for e in vista.dialogos["error"]] == ["El episodio no tiene una cama asignada."]
    assert vista.camas.pacientes_con_cama.call_count == lecturas + 1
    assert vista._tabla_con_cama.seleccionado() == episodio  # sigue en la lista: sigue elegido


# ---- Mantenimiento

def test_mantenimiento_lista_solo_camas_libres_o_fuera_de_servicio(crear):
    vista = crear()
    vista._modo.elegir("mantenimiento")
    assert (vista._tarjeta.titulo, vista._tarjeta.subtitulo) == TITULOS["mantenimiento"]
    estados = {f[3] for f in filas(vista._tabla_mantenimiento)}
    assert estados == {"Disponible", "Fuera de servicio"}
    assert vista._boton_mantenimiento.cget("text") == TEXTO_ELEGIR_MANTENIMIENTO
    assert not visible(vista._con_motivo)


def test_una_cama_libre_pide_el_motivo_para_salir_de_servicio(crear):
    vista = crear()
    vista._modo.elegir("mantenimiento")
    elegir(vista, vista._tabla_mantenimiento, cama(vista, "UCI-03").id_cama)
    assert visible(vista._con_motivo)
    assert vista._boton_mantenimiento.cget("text") == "Poner UCI-03 fuera de servicio"
    vista._motivo.insert(0, "Monitor sin señal")
    vista.mantenimiento()
    vista.camas.poner_fuera_de_servicio.assert_called_once_with(cama(vista, "UCI-03").id_cama, "Monitor sin señal")
    assert cama(vista, "UCI-03").estado == EstadoCama.FUERA_SERVICIO
    assert vista.dialogos["info"] == ["La cama UCI-03 quedó fuera de servicio."]
    assert vista._motivo.get() == ""


def test_sin_motivo_se_explica_bajo_el_campo_sin_dialogo(crear):
    vista = crear()
    vista._modo.elegir("mantenimiento")
    elegir(vista, vista._tabla_mantenimiento, cama(vista, "UCI-03").id_cama)
    vista.mantenimiento()
    assert vista.dialogos["error"] == []
    assert visible(vista._aviso_motivo) and vista._aviso_motivo.cget("text") == "El motivo es obligatorio."
    assert cama(vista, "UCI-03").estado == EstadoCama.DISPONIBLE
    vista._motivo_editado()  # soltar el Enter que lo envió: el texto no cambió, el aviso sigue
    assert visible(vista._aviso_motivo)
    vista._motivo.insert(0, "M")
    vista._motivo_editado()  # soltar una tecla que sí cambió el texto
    assert not visible(vista._aviso_motivo)


def test_volver_de_otra_opcion_conserva_el_paciente_y_la_cama_elegidos(crear):
    vista = crear()
    elegir(vista, vista._tabla_cola, 2)
    uci06 = cama(vista, "UCI-06").id_cama
    elegir(vista, vista._tabla_compatibles, uci06)
    vista._modo.elegir("con_cama")
    vista._modo.elegir("espera")
    vista.raiz.update()  # los avisos de selección de ttk llegan después: no deben borrar la cama elegida
    assert vista._tabla_cola.seleccionado() == 2 and vista._tabla_compatibles.seleccionado() == uci06
    assert vista._boton_asignar.cget("text") == "Asignar cama UCI-06"


def test_una_recarga_lee_una_sola_vez_las_camas_compatibles(crear):
    vista = crear()
    elegir(vista, vista._tabla_cola, 2)
    lecturas = vista.camas.camas_compatibles.call_count
    vista._recargar(conservar=True)
    vista.raiz.update()
    assert vista.camas.camas_compatibles.call_count == lecturas + 1


def test_si_una_recarga_no_puede_leer_las_camas_compatibles_no_abre_dialogo(crear):
    vista = crear()
    elegir(vista, vista._tabla_cola, 2)
    vista.camas.camas_compatibles.side_effect = PersistenciaError("Sin conexión.")
    vista._modo.elegir("con_cama")
    vista._modo.elegir("espera")
    vista.raiz.update()
    assert vista.dialogos["error"] == []
    assert vista._tabla_compatibles._vacio.cget("text") == SIN_LECTURA_COMPATIBLES


def test_si_la_bd_falla_el_motivo_escrito_se_conserva(crear):
    vista = crear()
    vista._modo.elegir("mantenimiento")
    uci03 = cama(vista, "UCI-03").id_cama
    elegir(vista, vista._tabla_mantenimiento, uci03)
    vista._motivo.insert(0, "Ventilador con alarma")
    vista.camas.poner_fuera_de_servicio.side_effect = PersistenciaError("No se pudo guardar.")
    vista.mantenimiento()
    assert [str(e) for e in vista.dialogos["error"]] == ["No se pudo guardar."]
    assert vista._tabla_mantenimiento.seleccionado() == uci03
    assert vista._motivo.get() == "Ventilador con alarma"


def test_una_cama_fuera_de_servicio_vuelve_sin_motivo(crear):
    vista = crear()
    vista._modo.elegir("mantenimiento")
    uci08 = cama(vista, "UCI-08").id_cama
    elegir(vista, vista._tabla_mantenimiento, uci08)
    assert not visible(vista._con_motivo)
    assert vista._boton_mantenimiento.cget("text") == "Volver UCI-08 a servicio"
    vista.mantenimiento()
    vista.camas.volver_a_servicio.assert_called_once_with(uci08)
    assert cama(vista, "UCI-08").estado == EstadoCama.DISPONIBLE
    assert vista.dialogos["info"] == ["La cama UCI-08 volvió a servicio: queda disponible."]


def test_en_la_demo_un_paciente_triado_pasa_a_esperar_cama():
    camas = CamasDemo(lambda: AHORA)
    triaje = TriajeDemo(lambda: AHORA, al_triar=camas.esperar_cama)
    entrada = triaje.cola_de_triaje()[0]
    signos = {"pa_sis": 120, "pa_dia": 80, "fc": 80, "fr": 16, "temp": 36.8, "sato2": 98}
    triaje.registrar(entrada.episodio.id_episodio, signos, [])
    llegado = next(e for e in camas.cola_de_espera() if e.episodio.id_episodio == entrada.episodio.id_episodio)
    assert llegado.paciente == entrada.paciente and llegado.nivel is not None
    assert camas.camas_compatibles(llegado.episodio.id_episodio)  # con triaje ya puede recibir cama (RN-01)


def test_cambiar_de_opcion_vuelve_a_leer_las_camas(crear):
    vista = crear()
    lecturas = vista.camas.mapa_camas.call_count
    vista._modo.elegir("mantenimiento")
    assert vista.camas.mapa_camas.call_count == lecturas + 1


def test_al_volver_relee_sin_dialogo_aunque_falle(crear):
    vista = crear()
    leidas = vista.camas.cola_de_espera.call_count
    vista.al_mostrar()
    assert vista.camas.cola_de_espera.call_count == leidas + 1
    vista.camas.cola_de_espera.side_effect = PersistenciaError("Sin conexión.")
    vista.al_mostrar()
    assert vista.dialogos["error"] == []
