import customtkinter as ctk
import pytest

from models.estados import EstadoCama
from models.triaje import COLOR_POR_NIVEL
from views import tema
from views.tema import _contraste, color_texto_sobre

MODOS = [(0, "claro"), (1, "oscuro")]
TEXTOS = {"texto": tema.COLOR_TEXTO, "etiqueta": tema.COLOR_ETIQUETA, "secundario": tema.COLOR_TEXTO_SECUNDARIO,
          "placeholder": tema.COLOR_PLACEHOLDER, "error": tema.COLOR_ERROR, "éxito": tema.COLOR_EXITO}
FONDOS = {"superficie": tema.COLOR_SUPERFICIE, "fondo": tema.COLOR_FONDO, "barra": tema.COLOR_BARRA}
PARES = [tema.COLOR_FONDO, tema.COLOR_BARRA, tema.COLOR_SUPERFICIE, tema.COLOR_CASILLA, tema.COLOR_ACTIVO,
         tema.COLOR_BORDE, tema.COLOR_BORDE_CAMPO, tema.COLOR_DIVISOR, *TEXTOS.values(), tema.COLOR_PRIMARIO,
         tema.COLOR_PRIMARIO_HOVER, tema.COLOR_ALERTA_FONDO, tema.COLOR_SIN_DATO, *tema.COLOR_NIVEL.values(),
         *tema.COLOR_ESTADO_CAMA.values()]


def test_hay_un_color_por_cada_estado_de_cama():
    assert set(tema.COLOR_ESTADO_CAMA) == set(EstadoCama)


def test_hay_un_color_por_cada_nivel_de_triaje():
    assert set(tema.COLOR_NIVEL) == set(COLOR_POR_NIVEL)


@pytest.mark.parametrize("par", PARES)
def test_cada_color_es_un_par_claro_oscuro(par):
    assert isinstance(par, tuple) and len(par) == 2
    for tono in par:
        color_texto_sobre(tono)  # valida el formato #RRGGBB


def test_el_espaciado_y_las_medidas_son_multiplos_de_4():
    medidas = (tema.ESPACIO_MINIMO, tema.ESPACIO, tema.ESPACIO_MEDIO, tema.ESPACIO_2, tema.ESPACIO_3,
               tema.ALTO_CONTROL, tema.ALTO_NAVEGACION, tema.ANCHO_BARRA, tema.ALTO_ENCABEZADO)
    assert all(m % 4 == 0 for m in medidas)


# ---- Contraste (WCAG: 4.5:1 para texto, 3:1 para bordes que indican algo), en los dos modos

@pytest.mark.parametrize("i, modo", MODOS)
@pytest.mark.parametrize("nombre_texto", TEXTOS)
@pytest.mark.parametrize("nombre_fondo", FONDOS)
def test_los_textos_se_leen_en_cada_fondo(i, modo, nombre_texto, nombre_fondo):
    assert _contraste(TEXTOS[nombre_texto][i], FONDOS[nombre_fondo][i]) >= 4.5


@pytest.mark.parametrize("i, modo", MODOS)
def test_el_borde_de_los_campos_se_ve(i, modo):
    assert _contraste(tema.COLOR_BORDE_CAMPO[i], tema.COLOR_SUPERFICIE[i]) >= 3


@pytest.mark.parametrize("i, modo", MODOS)
@pytest.mark.parametrize("estado", list(EstadoCama))
def test_el_borde_de_cada_estado_de_cama_se_ve(i, modo, estado):
    assert _contraste(tema.COLOR_ESTADO_CAMA[estado][i], tema.COLOR_CASILLA[i]) >= 3


@pytest.mark.parametrize("i, modo", MODOS)
@pytest.mark.parametrize("nivel", [1, 2, 3, 4, 5])
def test_el_numero_sobre_cada_nivel_se_lee(i, modo, nivel):
    fondo = tema.COLOR_NIVEL[nivel][i]
    assert _contraste(color_texto_sobre(fondo), fondo) >= 4.5


@pytest.mark.parametrize("i, modo", MODOS)
def test_el_texto_sobre_el_primario_y_sin_dato_se_lee(i, modo):
    assert _contraste(tema.COLOR_TEXTO_SOBRE_PRIMARIO[i], tema.COLOR_PRIMARIO[i]) >= 4.5
    assert _contraste(color_texto_sobre(tema.COLOR_SIN_DATO[i]), tema.COLOR_SIN_DATO[i]) >= 4.5


# ---- Funciones de color

@pytest.mark.parametrize("fondo, texto", [
    ("#FFFFFF", tema.TEXTO_OSCURO), ("#000000", tema.TEXTO_CLARO),
    ("#F9AB00", tema.TEXTO_OSCURO),  # amarillo: el blanco casi no se lee
    ("#D93025", tema.TEXTO_CLARO),   # rojo
])
def test_color_de_texto_sobre_un_fondo(fondo, texto):
    assert color_texto_sobre(fondo) == texto


def test_texto_sobre_un_par_da_un_par():
    assert tema.texto_sobre(("#FFFFFF", "#000000")) == (tema.TEXTO_OSCURO, tema.TEXTO_CLARO)


@pytest.mark.parametrize("fondo", ["rojo", "#FFF", "FFFFFF0", None, "#FFFFFFFF"])
def test_color_no_valido(fondo):
    with pytest.raises(ValueError, match="RRGGBB"):
        color_texto_sobre(fondo)


@pytest.mark.parametrize("modo, esperado", [("light", "#F5F5F7"), ("dark", "#242424")])
def test_color_actual_segun_el_modo(monkeypatch, modo, esperado):
    monkeypatch.setattr(ctk, "get_appearance_mode", lambda: modo.capitalize())
    assert tema.color_actual(tema.COLOR_FONDO) == esperado
    assert tema.color_acento() == tema.COLOR_PRIMARIO[modo == "dark"]


# ---- Fuentes

def test_inter_esta_incluida_con_su_licencia():
    for nombre in tema.ARCHIVOS_INTER:
        assert (tema.CARPETA_FUENTES / nombre).is_file()
    assert (tema.CARPETA_FUENTES / "LICENSE-Inter.txt").is_file()


def test_inter_se_carga():
    assert tema.cargar_fuentes() is True


@pytest.mark.parametrize("uso, familia, tamano, peso", [
    ("cifra", "Inter", 24, "bold"), ("titulo", "Inter", 20, "bold"), ("subtitulo", "Inter SemiBold", 15, "normal"),
    ("fuerte", "Inter SemiBold", 13, "normal"), ("codigo", "Inter", 13, "bold"), ("normal", "Inter", 13, "normal"),
    ("etiqueta", "Inter Medium", 12, "normal"), ("pequena", "Inter", 12, "normal"),
])
def test_fuentes(raiz_tk, uso, familia, tamano, peso):
    letra = tema.fuente(uso)
    assert isinstance(letra, ctk.CTkFont)
    assert (letra.cget("family"), letra.cget("size"), letra.cget("weight")) == (familia, tamano, peso)


def test_ninguna_letra_baja_de_12_px():
    assert min(tamano for _, tamano, _ in tema._FUENTES.values()) >= 12


def test_fuente_tachada(raiz_tk):
    assert tema.fuente("codigo", tachada=True).cget("overstrike")  # Tk lo devuelve como 1


def test_sin_inter_se_usa_segoe_ui(raiz_tk, monkeypatch):
    monkeypatch.setattr(tema, "_inter_cargada", False)
    assert tema.fuente("fuerte").cget("family") == "Segoe UI Semibold"
    assert tema.fuente("normal").cget("family") == "Segoe UI"


def test_uso_de_fuente_desconocido():
    with pytest.raises(ValueError, match="desconocido"):
        tema.fuente("enorme")


def test_aplicar_configura_customtkinter_y_carga_las_fuentes(monkeypatch):
    llamadas = []
    monkeypatch.setattr(ctk, "set_appearance_mode", lambda modo: llamadas.append(("modo", modo)))
    monkeypatch.setattr(ctk, "set_default_color_theme", lambda nombre: llamadas.append(("tema", nombre)))
    monkeypatch.setattr(tema, "cargar_fuentes", lambda: llamadas.append(("fuentes",)))
    tema.aplicar()
    assert llamadas == [("modo", "light"), ("tema", "blue"), ("fuentes",)]


def test_fuente_ttk_en_pixeles_y_escalada(raiz_tk, monkeypatch):
    # ttk no escala sus fuentes: se le pasan en píxeles (tamaño negativo en Tk) ya multiplicadas
    monkeypatch.setattr(tema, "escala", lambda widget: 1.25)
    assert tema.fuente_ttk("normal", raiz_tk) == ("Inter", -16, "normal")  # 13 × 1.25 = 16.25 → 16 px


def test_escala_es_la_de_customtkinter(raiz_tk):
    assert tema.escala(raiz_tk) == ctk.ScalingTracker.get_widget_scaling(raiz_tk)
