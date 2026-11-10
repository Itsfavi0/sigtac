from datetime import datetime
from unittest.mock import MagicMock

import pytest

from models.estados import EstadoCama
from models.excepciones import PersistenciaError, ReglaNegocioError
from prototipo.demo import CamasDemo
from views import limpieza_view, tema
from views.componentes import TarjetaCama
from views.componentes.seleccion import SIN_LECTURA
from views.limpieza_view import ELIJA_CAMA, NADA_POR_LIMPIAR, TEXTO_ELEGIR, LimpiezaView, texto_resumen

AHORA = datetime(2026, 10, 30, 10, 0)


@pytest.fixture
def dialogos(monkeypatch):
    anotados = {"error": [], "info": []}
    monkeypatch.setattr(limpieza_view, "mostrar_error", lambda ventana, error: anotados["error"].append(error))
    monkeypatch.setattr(limpieza_view, "mostrar_info", lambda ventana, texto: anotados["info"].append(texto))
    return anotados


@pytest.fixture
def crear(raiz_tk, dialogos):
    """La pantalla con el controlador de demostración envuelto en MagicMock(wraps=...): reglas reales y llamadas anotadas."""
    def crear(camas=None):
        camas = camas or MagicMock(wraps=CamasDemo(lambda: AHORA))
        vista = LimpiezaView(raiz_tk, camas, reloj=lambda: AHORA)
        vista.camas, vista.dialogos, vista.raiz = camas, dialogos, raiz_tk
        return vista
    return crear


def codigos(vista) -> list[str]:
    return [vista._lista.elemento(id_).cama.codigo for id_ in vista._lista._ids]


def elegir(vista, id_solicitud):
    vista._lista.elegir(id_solicitud)  # como el usuario: con un clic o las flechas
    vista.raiz.update()


def visible(widget) -> bool:
    return bool(widget.winfo_manager())


def estado(vista, codigo):
    return next(c.estado for c in vista.camas.mapa_camas() if c.codigo == codigo)


# ---- Al abrir

def test_al_abrir_muestra_las_camas_por_limpiar_de_la_mas_antigua_como_casillas(crear):
    vista = crear()
    assert codigos(vista) == ["HOS-06", "OBS-10", "OBS-04", "UCI-07"]  # 09:00, 09:15, 09:30, 09:45
    casilla = vista._lista.elemento(1)  # UCI-07
    assert isinstance(casilla, TarjetaCama) and casilla._estado.cget("text") == "UCI"  # el tipo en el 2.º renglón
    assert vista._boton.cget("text") == TEXTO_ELEGIR and vista._boton.cget("state") == "disabled"
    assert visible(vista._sin_eleccion) and vista._sin_eleccion.cget("text") == ELIJA_CAMA
    assert not visible(vista._detalle)


def test_el_resumen_dice_cuantas_esperan_y_cuanto_la_mas_antigua(crear):
    vista = crear()
    assert [e.cget("text") for e in vista._etiquetas_resumen] == ["4 camas por limpiar", "La más antigua: 1 h 00 min"]
    assert visible(vista._resumen)


def test_textos_del_resumen():
    una = MagicMock(fecha_solicitud=datetime(2026, 10, 30, 9, 15))
    otra = MagicMock(fecha_solicitud=datetime(2026, 10, 30, 9, 50))
    reciente = MagicMock(fecha_solicitud=datetime(2026, 10, 30, 9, 53))
    assert texto_resumen([otra, una], AHORA) == ("2 camas por limpiar", "La más antigua: 45 min")
    # En texto corrido, sin el cero que alinea columnas: «7 min», no «07 min»
    assert texto_resumen([reciente], AHORA) == ("1 cama por limpiar", "La más antigua: 7 min")
    assert texto_resumen([], AHORA) == ("0 camas por limpiar", None)


def test_sin_camas_por_limpiar_la_lista_lo_dice_y_el_resumen_solo_cuenta(crear):
    camas = MagicMock(wraps=CamasDemo(lambda: AHORA))
    camas.solicitudes_limpieza.side_effect = None
    camas.solicitudes_limpieza.return_value = []
    vista = crear(camas=camas)
    assert vista._lista.cantidad == 0 and vista._lista._vacio.cget("text") == NADA_POR_LIMPIAR
    assert vista._etiquetas_resumen[0].cget("text") == "0 camas por limpiar"
    assert not visible(vista._etiquetas_resumen[1].master)  # «La más antigua» no tiene nada que decir


def test_una_solicitud_sin_su_cama_en_el_mapa_no_se_muestra_ni_se_cuenta(crear):
    # El mapa solo trae camas activas: una dada de baja mientras esperaba limpieza no tiene casilla
    demo = CamasDemo(lambda: AHORA)
    camas = MagicMock(wraps=demo)
    camas.mapa_camas.side_effect = None
    camas.mapa_camas.return_value = [c for c in demo.mapa_camas() if c.codigo != "HOS-06"]
    vista = crear(camas=camas)
    assert codigos(vista) == ["OBS-10", "OBS-04", "UCI-07"]
    assert [e.cget("text") for e in vista._etiquetas_resumen] == ["3 camas por limpiar", "La más antigua: 45 min"]


def test_si_la_bd_falla_al_abrir_hay_un_solo_aviso(crear):
    camas = MagicMock()
    camas.solicitudes_limpieza.side_effect = PersistenciaError("No se pudo leer la lista.")
    vista = crear(camas=camas)
    assert [str(e) for e in vista.dialogos["error"]] == ["No se pudo leer la lista."]
    assert vista._lista.cantidad == 0 and vista._lista._vacio.cget("text") == SIN_LECTURA  # no «no hay»: no se sabe
    assert not visible(vista._resumen)  # «0 camas por limpiar» diría que no hay ninguna, y no se sabe


# ---- Elegir

def test_al_elegir_una_cama_se_ve_su_detalle_y_el_boton_dice_cual(crear):
    vista = crear()
    elegir(vista, 2)
    assert not visible(vista._sin_eleccion) and visible(vista._detalle)
    assert vista._codigo.cget("text") == "OBS-04"
    assert vista._datos.cget("text").startswith("Observación")
    assert vista._desde.cget("text").startswith("En limpieza desde las ")
    assert vista._boton.cget("text") == "Confirmar limpieza de OBS-04" and vista._boton.cget("state") == "normal"


def test_el_detalle_no_repite_el_area_si_se_llama_como_el_tipo(crear):
    vista = crear()
    elegir(vista, 1)  # UCI-07: tipo UCI, área UCI
    assert vista._datos.cget("text") == "UCI"


def test_el_detalle_dice_desde_cuando_sin_el_cero_de_las_columnas(crear):
    vista = crear()
    elegir(vista, 4)  # HOS-06, desde las 09:00
    assert vista._desde.cget("text") == "En limpieza desde las 09:00 (1 h 00 min)"


def test_enter_en_una_cama_confirma_su_limpieza(crear):
    # La ventana de pruebas está oculta y Tk no le entrega teclas: se prueba lo que hace Enter en la lista (su
    # vínculo llama a _activar, que usa la casilla elegida)
    vista = crear()
    elegir(vista, 1)
    assert vista._lista._lienzo.bind("<Return>")
    vista._lista._activar()
    vista.camas.confirmar_limpieza.assert_called_once_with(1)


# ---- Confirmar

def test_confirmar_la_limpieza_deja_la_cama_libre(crear):  # RN-08
    vista = crear()
    elegir(vista, 1)
    vista.confirmar()
    vista.camas.confirmar_limpieza.assert_called_once_with(1)
    assert estado(vista, "UCI-07") == EstadoCama.DISPONIBLE
    assert "UCI-07" not in codigos(vista)
    assert vista.dialogos["info"] == ["Cama UCI-07 lista: vuelve a estar disponible."]
    assert vista._lista.seleccionado() is None and vista._boton.cget("state") == "disabled"
    assert vista._etiquetas_resumen[0].cget("text") == "3 camas por limpiar"


def test_si_otra_pc_ya_la_confirmo_se_avisa_y_se_recarga_conservando_la_eleccion(crear):
    vista = crear()
    elegir(vista, 2)
    vista.camas.confirmar_limpieza.side_effect = ReglaNegocioError("La solicitud de limpieza ya fue atendida.")
    vista.confirmar()
    assert [str(e) for e in vista.dialogos["error"]] == ["La solicitud de limpieza ya fue atendida."]
    assert vista.camas.solicitudes_limpieza.call_count == 2  # al abrir y al recargar
    assert vista._lista.seleccionado() == 2 and vista._boton.cget("text") == "Confirmar limpieza de OBS-04"


def test_si_otra_pc_ya_la_confirmo_y_sale_de_la_lista_queda_sin_eleccion(crear):
    vista = crear()
    elegir(vista, 2)
    demo = vista.camas._mock_wraps

    def otra_pc(id_solicitud):
        demo.confirmar_limpieza(id_solicitud)  # la otra PC llegó primero
        raise ReglaNegocioError("La solicitud de limpieza ya fue atendida.")

    vista.camas.confirmar_limpieza.side_effect = otra_pc
    vista.confirmar()
    assert [str(e) for e in vista.dialogos["error"]] == ["La solicitud de limpieza ya fue atendida."]
    assert "OBS-04" not in codigos(vista) and vista._lista.seleccionado() is None
    assert visible(vista._sin_eleccion) and not visible(vista._detalle)
    assert vista._boton.cget("text") == TEXTO_ELEGIR and vista._boton.cget("state") == "disabled"


def test_confirmar_sin_eleccion_no_llama_al_controlador(crear):
    vista = crear()
    vista.confirmar()
    vista.camas.confirmar_limpieza.assert_not_called()


def test_una_cama_dada_de_alta_aparece_por_limpiar(raiz_tk, crear):  # RN-07: el alta pide la limpieza
    demo = CamasDemo(lambda: AHORA)
    ocupada = next(p for p in demo.pacientes_con_cama() if p.cama.estado == EstadoCama.OCUPADA)
    demo.dar_alta(ocupada.episodio.id_episodio)
    vista = crear(camas=MagicMock(wraps=demo))
    assert codigos(vista)[-1] == ocupada.cama.codigo


# ---- Al volver

def test_al_volver_relee_y_conserva_la_cama_elegida(crear):
    vista = crear()
    elegir(vista, 3)
    leidas = vista.camas.solicitudes_limpieza.call_count
    vista.al_mostrar()
    assert vista.camas.solicitudes_limpieza.call_count == leidas + 1 and vista.dialogos["error"] == []
    assert vista._lista.seleccionado() == 3 and visible(vista._detalle)


def test_al_volver_las_casillas_se_repintan_sin_rehacerse(crear):
    vista = crear()
    casilla = vista._lista.elemento(1)
    vista.al_mostrar()
    assert vista._lista.elemento(1) is casilla


def test_el_punto_del_resumen_es_del_color_de_en_limpieza(crear):
    vista = crear()
    punto = vista._etiquetas_resumen[0].master.winfo_children()[0]
    assert tuple(punto.cget("fg_color")) == tema.COLOR_ESTADO_CAMA[EstadoCama.EN_LIMPIEZA]
