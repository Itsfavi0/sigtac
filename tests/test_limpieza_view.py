from datetime import datetime
from unittest.mock import MagicMock

import pytest

from models.estados import EstadoCama
from models.excepciones import PersistenciaError, ReglaNegocioError
from prototipo.demo import CamasDemo
from views import limpieza_view
from views.componentes.tabla import SIN_LECTURA
from views.limpieza_view import NADA_POR_LIMPIAR, TEXTO_ELEGIR, LimpiezaView

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


def filas(tabla) -> list[tuple]:
    return [tabla._arbol.item(iid, "values") for iid in tabla._arbol.get_children()]


def elegir(vista, id_solicitud):
    vista._tabla.seleccionar(id_solicitud)
    vista.raiz.update()


def estado(vista, codigo):
    return next(c.estado for c in vista.camas.mapa_camas() if c.codigo == codigo)


def test_al_abrir_lista_las_camas_por_limpiar_de_la_mas_antigua(crear):
    vista = crear()
    assert [f[0] for f in filas(vista._tabla)] == ["UCI-07", "OBS-04", "OBS-10", "HOS-06"]
    assert filas(vista._tabla)[0] == ("UCI-07", "UCI", "UCI", "09:45", "15 min")
    assert vista._boton.cget("text") == TEXTO_ELEGIR and vista._boton.cget("state") == "disabled"


def test_si_la_bd_falla_al_abrir_hay_un_solo_aviso(crear):
    camas = MagicMock()
    camas.solicitudes_limpieza.side_effect = PersistenciaError("No se pudo leer la lista.")
    vista = crear(camas=camas)
    assert [str(e) for e in vista.dialogos["error"]] == ["No se pudo leer la lista."]
    assert vista._tabla.cantidad == 0 and vista._tabla._vacio.cget("text") == SIN_LECTURA  # no «no hay»: no se sabe


def test_confirmar_la_limpieza_deja_la_cama_libre(crear):  # RN-08
    vista = crear()
    elegir(vista, 1)
    assert vista._boton.cget("text") == "Confirmar limpieza de UCI-07" and vista._boton.cget("state") == "normal"
    vista.confirmar()
    vista.camas.confirmar_limpieza.assert_called_once_with(1)
    assert estado(vista, "UCI-07") == EstadoCama.DISPONIBLE
    assert "UCI-07" not in [f[0] for f in filas(vista._tabla)]
    assert vista.dialogos["info"] == ["Cama UCI-07 lista: vuelve a estar disponible."]
    assert vista._boton.cget("state") == "disabled"


def test_si_otra_pc_ya_la_confirmo_se_avisa_y_se_recarga(crear):
    vista = crear()
    elegir(vista, 2)
    vista.camas.confirmar_limpieza.side_effect = ReglaNegocioError("La solicitud de limpieza ya fue atendida.")
    vista.confirmar()
    assert [str(e) for e in vista.dialogos["error"]] == ["La solicitud de limpieza ya fue atendida."]
    assert vista.camas.solicitudes_limpieza.call_count == 2  # al abrir y al recargar
    assert vista._tabla.seleccionado() == 2


def test_confirmar_sin_eleccion_no_llama_al_controlador(crear):
    vista = crear()
    vista.confirmar()
    vista.camas.confirmar_limpieza.assert_not_called()


def test_una_cama_dada_de_alta_aparece_por_limpiar(raiz_tk, crear):  # RN-07: el alta pide la limpieza
    demo = CamasDemo(lambda: AHORA)
    ocupada = next(p for p in demo.pacientes_con_cama() if p.cama.estado == EstadoCama.OCUPADA)
    demo.dar_alta(ocupada.episodio.id_episodio)
    vista = crear(camas=MagicMock(wraps=demo))
    assert filas(vista._tabla)[-1][0] == ocupada.cama.codigo


def test_al_volver_relee_las_camas_por_limpiar(crear):
    vista = crear()
    leidas = vista.camas.solicitudes_limpieza.call_count
    vista.al_mostrar()
    assert vista.camas.solicitudes_limpieza.call_count == leidas + 1 and vista.dialogos["error"] == []
