import logging
import sys
import time
import tkinter as tk
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest
from PIL import Image

from views.componentes import cubierta
from views.componentes.cubierta import Cubierta


@pytest.fixture
def area(raiz_tk, monkeypatch):
    """Un área «visible» (la ventana de pruebas está oculta) en Windows, con la foto simulada."""
    marco = ctk.CTkFrame(raiz_tk)
    monkeypatch.setattr(marco, "winfo_viewable", lambda: 1)
    monkeypatch.setattr(cubierta, "EN_WINDOWS", True)
    return marco


@pytest.fixture
def fotos(monkeypatch):
    """Reemplaza la captura de pantalla; anota cada llamada."""
    llamadas = []

    def grab(**opciones):
        llamadas.append(opciones)
        return Image.new("RGB", (4, 4))

    monkeypatch.setattr(cubierta.ImageGrab, "grab", grab)
    return llamadas


def cubierta_sin_ventana(area) -> Cubierta:
    """Una cubierta cuya ventana con la foto es un doble: las pruebas no abren ventanas reales."""
    c = Cubierta(area)
    c._mostrar_foto = MagicMock(name="_mostrar_foto")
    return c


def pendientes(monkeypatch, *respuestas):
    """falta_pintar responde, en orden, lo indicado (True = a algo le falta pintarse)."""
    cola = list(respuestas)
    monkeypatch.setattr(cubierta, "falta_pintar", lambda hwnd: cola.pop(0))


def revisar(c: Cubierta):
    """Hace ya la revisión programada (cancela su tarea after: si no, quedaría viva y fallaría al destruir el área)."""
    if c._tarea is not None:
        c._raiz.after_cancel(c._tarea)
        c._tarea = None
    c._revisar()


# ---- Cuándo no tapa

def test_con_el_area_oculta_el_cambio_se_hace_sin_foto(raiz_tk, fotos):
    c = Cubierta(ctk.CTkFrame(raiz_tk))  # la ventana de pruebas está oculta
    assert c.cambiar(lambda: "hecho") == "hecho"
    assert fotos == [] and not c.tapando


def test_fuera_de_windows_no_tapa(area, fotos, monkeypatch):
    monkeypatch.setattr(cubierta, "EN_WINDOWS", False)
    c = cubierta_sin_ventana(area)
    c.cambiar(lambda: None)
    assert fotos == [] and not c.tapando


def test_si_la_foto_falla_el_cambio_se_hace_igual(area, monkeypatch, caplog):
    def falla(**_):
        raise OSError("screen grab failed")

    monkeypatch.setattr(cubierta.ImageGrab, "grab", falla)
    hechos = []
    c = cubierta_sin_ventana(area)
    with caplog.at_level(logging.WARNING, logger=cubierta.__name__):
        c.cambiar(lambda: hechos.append("cambio"))
    assert hechos == ["cambio"] and not c.tapando
    assert "No se pudo fotografiar" in caplog.text


# ---- La foto

def test_durante_el_cambio_el_area_esta_tapada_por_su_foto(area, fotos):
    c = cubierta_sin_ventana(area)
    vista = []
    c.cambiar(lambda: vista.append(c.tapando))
    assert vista == [True] and c.tapando
    x, y = area.winfo_rootx(), area.winfo_rooty()
    ancho, alto = area.winfo_width(), area.winfo_height()
    # La foto es del área, con todos los monitores (la ventana puede estar en otro), y se pone justo encima
    assert fotos == [{"bbox": (x, y, x + ancho, y + alto), "all_screens": True}]
    foto = c._mostrar_foto.call_args.args[0]
    assert c._mostrar_foto.call_args.args[1:] == (x, y, ancho, alto) and foto.size == (4, 4)
    c.quitar()


@pytest.fixture
def windows_simulado(raiz_tk, monkeypatch):
    """
    Anota las llamadas a Windows de la ventana de la foto (quitar la animación y pintar) sin hacerlas. De pintar_ya
    anota también el tamaño que tiene en ese momento el widget donde pinta: debe ser el de la foto.
    """
    llamadas = []

    def pintar_ya(hwnd, foto):
        widget = raiz_tk.nametowidget(raiz_tk.winfo_pathname(hwnd))
        llamadas.append(("pintar_ya", hwnd, foto, (widget.winfo_width(), widget.winfo_height())))

    monkeypatch.setattr(cubierta, "sin_animacion", lambda hwnd: llamadas.append(("sin_animacion", hwnd)))
    monkeypatch.setattr(cubierta, "pintar_ya", pintar_ya)
    return llamadas


def test_la_ventana_de_la_foto_no_tiene_bordes_cubre_el_area_y_ya_esta_pintada(raiz_tk, windows_simulado):
    foto = Image.new("RGB", (30, 20))
    ventana = Cubierta(raiz_tk)._mostrar_foto(foto, 5, 7, 30, 20)
    try:
        assert ventana.overrideredirect() and ventana.winfo_viewable()
        assert ventana.geometry().startswith("30x20")
        etiqueta = ventana.winfo_children()[0]
        assert etiqueta.imagen.width() == 30 and etiqueta.imagen.height() == 20
        # Sin el fundido de Windows y pintada ya en la etiqueta, que al pintarla ya mide lo que la foto (con pack
        # mediría 1×1 hasta que Tk atienda sus eventos), con la misma foto que Tk mostrará
        assert windows_simulado == [("sin_animacion", int(ventana.wm_frame(), 16)),
                                    ("pintar_ya", etiqueta.winfo_id(), foto, (30, 20))]
    finally:
        ventana.destroy()


def test_si_la_ventana_de_la_foto_falla_no_queda_suelta_y_el_cambio_se_hace(area, fotos, monkeypatch, caplog):
    def falla(hwnd):
        raise OSError("sin DWM")

    monkeypatch.setattr(cubierta, "sin_animacion", falla)
    antes = set(area.winfo_toplevel().winfo_children())
    hechos = []
    c = Cubierta(area)
    with caplog.at_level(logging.WARNING, logger=cubierta.__name__):
        c.cambiar(lambda: hechos.append("cambio"))
    assert hechos == ["cambio"] and not c.tapando
    sueltas = [w for w in set(area.winfo_toplevel().winfo_children()) - antes if isinstance(w, tk.Toplevel)]
    assert sueltas == [] and not any(isinstance(w, tk.Toplevel) for w in area.winfo_children())
    assert "No se pudo mostrar la foto" in caplog.text


def test_poner_la_foto_no_atiende_temporizadores_ni_clics(area, fotos, windows_simulado):
    # Si los atendiera, un clic o la precarga correrían en medio del cambio
    corridos = []
    tarea = area.after(0, lambda: corridos.append("temporizador"))
    area.event_generate("<<Prueba>>", when="tail")
    area.bind("<<Prueba>>", lambda _: corridos.append("evento"))
    vistos = []
    c = Cubierta(area)
    try:
        c.cambiar(lambda: vistos.append(list(corridos)))
        assert vistos == [[]] and c.tapando
    finally:
        c.quitar()
        area.after_cancel(tarea)


def test_un_cambio_mientras_tapa_usa_la_misma_foto(area, fotos):
    c = cubierta_sin_ventana(area)
    c.cambiar(lambda: None)
    c.cambiar(lambda: None)
    assert len(fotos) == 1 and c._mostrar_foto.call_count == 1
    c.quitar()


def test_si_el_cambio_falla_se_quita_la_foto_y_el_error_sube(area, fotos):
    c = cubierta_sin_ventana(area)

    def falla():
        raise ValueError("pantalla rota")

    with pytest.raises(ValueError, match="pantalla rota"):
        c.cambiar(falla)
    assert not c.tapando and c._tarea is None
    c._mostrar_foto.return_value.destroy.assert_called_once()


# ---- Cuándo se quita

def test_se_quita_tras_dos_revisiones_seguidas_sin_nada_por_pintar(area, fotos, monkeypatch):
    c = cubierta_sin_ventana(area)
    c.cambiar(lambda: None)
    pendientes(monkeypatch, True, False, True, False, False)
    estados = []
    for _ in range(5):
        revisar(c)
        estados.append(c.tapando)
    # Una revisión sin pendientes no basta (Tk podría estar dibujando); dos seguidas, sí
    assert estados == [True, True, True, True, False]
    assert c._tarea is None


def test_se_quita_al_llegar_al_limite_aunque_falte_pintar(area, fotos, monkeypatch):
    ahora = [100.0]
    c = cubierta_sin_ventana(area)
    c.reloj = lambda: ahora[0]
    c.cambiar(lambda: None)
    pendientes(monkeypatch, True, True)
    ahora[0] += Cubierta.MS_MAXIMO / 1000 - 0.01
    revisar(c)
    assert c.tapando
    ahora[0] += 0.01
    revisar(c)
    assert not c.tapando


def test_otro_cambio_renueva_el_limite(area, fotos, monkeypatch):
    ahora = [100.0]
    c = cubierta_sin_ventana(area)
    c.reloj = lambda: ahora[0]
    c.cambiar(lambda: None)
    ahora[0] += 1.0
    c.cambiar(lambda: None)
    pendientes(monkeypatch, True)
    ahora[0] += Cubierta.MS_MAXIMO / 1000 - 0.01  # desde el segundo cambio aún no se cumple
    revisar(c)
    assert c.tapando
    c.quitar()


def test_tras_el_cambio_queda_programada_una_revision(area, fotos):
    c = cubierta_sin_ventana(area)
    c.cambiar(lambda: None)
    programada = c._tarea
    assert programada in area.tk.call("after", "info")
    c.quitar()


def test_quitar_cancela_la_revision_y_cierra_la_foto(area, fotos):
    c = cubierta_sin_ventana(area)
    c.cambiar(lambda: None)
    programada = c._tarea
    c.quitar()
    assert c._tarea is None and not c.tapando
    assert programada not in area.tk.call("after", "info")
    c._mostrar_foto.return_value.destroy.assert_called_once()
    c.quitar()  # quitar dos veces no falla


def test_si_el_area_se_destruye_con_la_foto_puesta_la_revision_termina_sin_error(area, fotos, monkeypatch):
    c = Cubierta(area)
    ventana = MagicMock()
    ventana.winfo_exists.return_value = False  # se fue con el área
    monkeypatch.setattr(c, "_mostrar_foto", lambda *_: ventana)
    c.cambiar(lambda: None)
    area.destroy()
    errores = []
    c._raiz.tk.createcommand("bgerror", errores.append)  # errores de Tcl en tareas after (p. ej. «invalid command name»)
    try:
        time.sleep(2 * Cubierta.MS_ENTRE_REVISIONES / 1000)
        c._raiz.update()  # la revisión se dispara sola, como en la aplicación
    finally:
        c._raiz.tk.deletecommand("bgerror")
    assert errores == [] and not c.tapando and c._tarea is None
    ventana.destroy.assert_not_called()


@pytest.mark.skipif(sys.platform != "win32", reason="GetUpdateRect es de Windows")
def test_falta_pintar_ve_una_ventana_hija_por_pintar(raiz_tk):
    import ctypes

    ventana = tk.Toplevel(raiz_tk)
    ventana.overrideredirect(True)
    ventana.geometry("40x30+0+0")
    visible = tk.Frame(ventana, width=40, height=15)
    visible.pack()
    try:
        ventana.update()  # pintada: nada pendiente
        assert not cubierta.falta_pintar(ventana.winfo_id())
        ctypes.windll.user32.InvalidateRect(visible.winfo_id(), None, True)
        assert cubierta.falta_pintar(ventana.winfo_id())
        ventana.update()
        assert not cubierta.falta_pintar(ventana.winfo_id())
    finally:
        ventana.destroy()
