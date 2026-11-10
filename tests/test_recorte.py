import pytest

from views import tema
from views.componentes import EtiquetaRecortada
from views.componentes.recorte import PUNTOS, recortar


def medir(texto: str) -> int:
    """Cada letra mide 10 px: así se ve qué entra."""
    return len(texto) * 10


def test_si_cabe_queda_entero():
    assert recortar("Médico", medir, 60) == "Médico"
    assert recortar("", medir, 0) == ""


def test_si_no_cabe_termina_en_puntos_y_cabe():
    assert recortar("Médico de Emergencia", medir, 120) == "Médico de E" + PUNTOS  # 12 letras: justo 120 px
    texto = recortar("Médico de Emergencia", medir, 110)
    assert texto == "Médico de" + PUNTOS  # el corte cae en un espacio: sin el espacio antes de los puntos
    assert medir(texto) <= 110


@pytest.mark.parametrize("ancho", [5, 10])
def test_si_no_cabe_nada_quedan_los_puntos(ancho):
    assert recortar("Emergencia", medir, ancho) == PUNTOS


@pytest.mark.parametrize("ancho", range(10, 200, 7))
def test_siempre_lo_mas_largo_que_cabe(ancho):
    texto = "Hallado inconsciente en la vía pública"
    resultado = recortar(texto, medir, ancho)
    assert medir(resultado) <= ancho or resultado == PUNTOS
    if resultado.endswith(PUNTOS) and resultado != PUNTOS:
        prefijo = resultado[:-1]
        siguiente = texto[:len(prefijo) + 1].rstrip() + PUNTOS
        assert medir(siguiente) > ancho or len(siguiente) <= len(resultado)  # una letra más ya no entra


def test_la_etiqueta_muestra_lo_que_cabe_y_guarda_el_texto_completo(raiz_tk):
    etiqueta = EtiquetaRecortada(raiz_tk, "Médico de Emergencia", font=tema.fuente("pequena"))
    assert etiqueta.cget("text") == "Médico de Emergencia"  # sin ancho todavía (ventana oculta): entero
    etiqueta.ajustar(ancho=60)
    assert etiqueta.cget("text").endswith(PUNTOS) and etiqueta.completo == "Médico de Emergencia"
    etiqueta.ajustar(ancho=1000)
    assert etiqueta.cget("text") == "Médico de Emergencia"
    etiqueta.mostrar("Enfermero de Triaje")
    assert etiqueta.completo == "Enfermero de Triaje"
    etiqueta.destroy()
