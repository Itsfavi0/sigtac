import pytest

from models.cama import CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.estados import EstadoCama
from views import tema
from views.componentes.matriz import SIN_CAMAS, MatrizCamas, distribuir

D, O = EstadoCama.DISPONIBLE, EstadoCama.OCUPADA


# ---- distribuir: el menor número de filas en el que caben todas las columnas

def test_todo_en_una_fila_si_alcanza_el_ancho():
    assert distribuir([2, 3], ancho_util=500, ancho_minimo=90, separacion=10) == (1, [2, 3])


def test_justo_en_el_limite_cabe():
    # 5 columnas × (90 + 10) = 500: cabe exacto
    assert distribuir([2, 3], 500, 90, 10) == (1, [2, 3])
    assert distribuir([2, 3], 499, 90, 10) == (2, [1, 2])


def test_busca_el_menor_numero_de_filas():
    # 36 camas como en la demo, con el ancho útil de 1280×800: 5 filas (1 + 2 + 3 + 2 columnas)
    assert distribuir([4, 8, 14, 10], 940, 100, 8) == (5, [1, 2, 3, 2])


def test_si_no_cabe_ni_una_columna_por_grupo_queda_una_por_grupo():
    assert distribuir([4, 8], 50, 100, 8) == (8, [1, 1])


def test_sin_grupos():
    assert distribuir([], 500, 100, 8) == (0, [])


def test_un_grupo_vacio_es_un_error():
    with pytest.raises(ValueError):
        distribuir([3, 0], 500, 100, 8)


# ---- MatrizCamas

def camas_demo():
    estados = [D, O, D, O]
    return ([CamaHospitalizacion(i, f"HOS-{i:02d}", "Hosp", estados[i % 4]) for i in range(1, 11)]
            + [CamaTraumaShock(i, f"TS-{i:02d}", "TS", O) for i in range(1, 5)]
            + [CamaObservacion(i, f"OBS-{i:02d}", "Obs", estados[i % 4]) for i in range(1, 15)]
            + [CamaUCI(i, f"UCI-{i:02d}", "UCI", D) for i in range(1, 9)])


def test_agrupa_por_tipo_de_la_mas_critica_a_la_general(raiz_tk):
    matriz = MatrizCamas(raiz_tk)
    matriz.cargar(camas_demo())
    titulos = [g[0].winfo_children()[0].winfo_children()[0].cget("text") for g in matriz._grupos]
    assert titulos == ["Trauma shock", "UCI", "Observación", "Hospitalización"]
    assert matriz.cantidad_camas == 36


def test_cuenta_las_libres_de_cada_tipo(raiz_tk):
    matriz = MatrizCamas(raiz_tk)
    matriz.cargar([CamaUCI(1, "UCI-01", "UCI", D), CamaUCI(2, "UCI-02", "UCI", O)])
    cabecera = matriz._grupos[0][0].winfo_children()[0]
    assert [h.cget("text") for h in cabecera.winfo_children()] == ["UCI", "1 de 2 libres"]


def test_sin_camas_muestra_el_aviso(raiz_tk):
    matriz = MatrizCamas(raiz_tk)
    matriz.cargar([])
    assert matriz.cantidad_camas == 0
    assert matriz._vacio.winfo_manager() == "place" and matriz._vacio.cget("text") == SIN_CAMAS


def test_recargar_reemplaza_las_camas(raiz_tk):
    matriz = MatrizCamas(raiz_tk)
    matriz.cargar(camas_demo())
    matriz.cargar([CamaUCI(1, "UCI-01", "UCI", D)])
    assert matriz.cantidad_camas == 1 and len(matriz._grupos) == 1 and matriz._lineas == []


def test_con_alto_suficiente_no_hay_barra(raiz_tk):
    matriz = MatrizCamas(raiz_tk)
    matriz.cargar(camas_demo())
    escala = tema.escala(matriz)
    matriz.disponer(round(1040 * escala), round(500 * escala))
    assert (matriz.filas, matriz.columnas) == (5, [1, 2, 3, 2])
    assert matriz.desplazable is False


def test_en_1093x614_la_matriz_se_desplaza(raiz_tk):
    # Laptop de 1366×768 al 125 %: la matriz recibe unos 850×150 y no le alcanza el alto
    matriz = MatrizCamas(raiz_tk)
    matriz.cargar(camas_demo())
    escala = tema.escala(matriz)
    matriz.disponer(round(850 * escala), round(150 * escala))
    assert matriz.filas > 2
    assert matriz.desplazable is True
    matriz.disponer(round(1040 * escala), round(500 * escala))  # al agrandar la ventana, la barra se va
    assert matriz.desplazable is False
