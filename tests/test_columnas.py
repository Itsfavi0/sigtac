import customtkinter as ctk

from views import tema
from views.componentes import aviso_columna, dos_columnas, etiqueta_resumen, fila_acciones
from views.componentes.columnas import ANCHO_AVISO


def test_dos_columnas_con_una_linea_entre_ellas(raiz_tk):
    marco, izquierda, derecha = dos_columnas(raiz_tk)
    assert izquierda.grid_info()["column"] == 0 and derecha.grid_info()["column"] == 2
    # La derecha un poco más ancha (5 a 6), siempre en esa proporción
    assert marco.grid_columnconfigure(0)["weight"] == 5 and marco.grid_columnconfigure(2)["weight"] == 6
    assert marco.grid_columnconfigure(0)["uniform"] == marco.grid_columnconfigure(2)["uniform"] == "columnas"
    linea = next(h for h in marco.winfo_children() if h.grid_info()["column"] == 1)
    assert tuple(linea.cget("fg_color")) == tema.COLOR_DIVISOR and linea.cget("width") == 1


def test_etiqueta_del_resumen_gris_con_o_sin_punto(raiz_tk):
    padre = ctk.CTkFrame(raiz_tk)
    sin_punto = etiqueta_resumen(padre)
    con_punto = etiqueta_resumen(padre, tema.COLOR_NIVEL[1])
    assert tuple(sin_punto.master.cget("fg_color")) == tema.COLOR_ACTIVO
    assert len(sin_punto.master.winfo_children()) == 1
    punto = con_punto.master.winfo_children()[0]
    assert tuple(punto.cget("fg_color")) == tema.COLOR_NIVEL[1]
    # Una a continuación de la otra
    assert [h.pack_info()["side"] for h in padre.winfo_children()] == ["left", "left"]


def test_el_aviso_se_crea_sin_colocar_y_partido(raiz_tk):
    aviso = aviso_columna(raiz_tk, "Elija algo.")
    assert aviso.cget("text") == "Elija algo." and not aviso.winfo_manager()
    assert aviso.cget("wraplength") == ANCHO_AVISO and tuple(aviso.cget("text_color")) == tema.COLOR_TEXTO_SECUNDARIO


def margen(valor) -> tuple[int, int]:
    """Tk devuelve un margen como entero (igual a ambos lados) o como tupla, ya multiplicado por la escala."""
    texto = str(valor).replace("(", " ").replace(")", " ").replace(",", " ")
    numeros = tuple(int(float(n)) for n in texto.split())
    return numeros if len(numeros) == 2 else numeros * 2


def test_la_fila_de_acciones_queda_colocada_con_su_separacion(raiz_tk):
    escala = tema.escala(raiz_tk)  # CustomTkinter multiplica los márgenes por el zoom de la pantalla
    assert margen(fila_acciones(raiz_tk).pack_info()["pady"]) == (int(tema.ESPACIO_2 * escala), 0)
    assert margen(fila_acciones(raiz_tk, arriba=tema.ESPACIO).pack_info()["pady"]) == (int(tema.ESPACIO * escala), 0)
