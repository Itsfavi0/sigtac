import customtkinter as ctk
import pytest

from views import tema
from views.componentes import ListaSeleccion
from views.componentes.foco import GROSOR_FOCO
from views.componentes.tabla import SIN_LECTURA


class Elemento(ctk.CTkFrame):
    """Un elemento de prueba: un marco con su texto; `mostrar` cuenta los repintados."""

    def __init__(self, padre, dato):
        super().__init__(padre, height=20, border_width=1, border_color=tema.COLOR_BORDE)
        self.etiqueta = ctk.CTkLabel(self, text="")
        self.etiqueta.pack()
        self.repintados = 0
        self.mostrar(dato)

    def mostrar(self, dato):
        self.dato = dato
        self.repintados += 1
        self.etiqueta.configure(text=str(dato))


@pytest.fixture
def crear(raiz_tk):
    def crear(columnas=1, filas=None, reutilizar=True, **opciones):
        avisos = {"elegido": [], "activado": [], "creados": 0}

        def nuevo(padre, dato):
            avisos["creados"] += 1
            return Elemento(padre, dato)

        lista = ListaSeleccion(raiz_tk, nuevo, "No hay nada.", alto_elemento=20, columnas=columnas, filas=filas,
                               al_seleccionar=avisos["elegido"].append, al_activar=avisos["activado"].append,
                               actualizar=Elemento.mostrar if reutilizar else None, **opciones)
        lista.avisos = avisos
        return lista
    return crear


def datos(*ids):
    return [(i, f"dato {i}") for i in ids]


def turnos(raiz, cuantos: int = 10):
    """Deja correr los turnos de la carga de a pocos (cada uno se programa a 1 ms)."""
    for _ in range(cuantos):
        raiz.after(5)  # espera 5 ms sin procesar eventos
        raiz.update()


def marcado(elemento) -> bool:
    return elemento.cget("border_width") == GROSOR_FOCO and \
        tuple(elemento.cget("border_color")) == tema.COLOR_PRIMARIO_GRAFICO


# ---- Cargar

def test_sin_elementos_dice_el_texto_vacio_y_sin_lectura_no_que_no_hay(crear):
    lista = crear()
    assert lista.cantidad == 0 and lista._vacio.cget("text") == "No hay nada." and lista._vacio.winfo_manager()
    lista.sin_lectura()
    assert lista._vacio.cget("text") == SIN_LECTURA
    lista.cambiar_texto_vacio("Elija un paciente.")
    assert lista._vacio.cget("text") == "Elija un paciente."
    lista.cargar(datos(1))
    assert not lista._vacio.winfo_manager()


def test_los_elementos_se_reparten_en_columnas(crear):
    lista = crear(columnas=3)
    lista.cargar(datos(1, 2, 3, 4))
    posiciones = [(lista.elemento(i).grid_info()["row"], lista.elemento(i).grid_info()["column"]) for i in (1, 2, 3, 4)]
    assert posiciones == [(0, 0), (0, 1), (0, 2), (1, 0)]


def test_una_recarga_repinta_los_que_siguen_crea_los_nuevos_y_quita_los_que_no_estan(crear):
    lista = crear()
    lista.cargar(datos(1, 2))
    primero = lista.elemento(1)
    lista.cargar([(1, "otro"), (3, "dato 3")])
    assert lista.elemento(1) is primero and primero.dato == "otro" and primero.repintados == 2
    assert lista.avisos["creados"] == 3  # 1 y 2 al principio, 3 ahora
    assert lista._ids == [1, 3] and 2 not in lista._elementos


def test_sin_actualizar_una_recarga_rehace_todo(crear):
    lista = crear(reutilizar=False)
    lista.cargar(datos(1))
    primero = lista.elemento(1)
    lista.cargar(datos(1))
    assert not primero.winfo_exists() and lista.avisos["creados"] == 2


def test_una_recarga_quita_la_eleccion(crear):
    lista = crear()
    lista.cargar(datos(1, 2))
    lista.elegir(1)
    lista.cargar(datos(1, 2))
    assert lista.seleccionado() is None and not marcado(lista.elemento(1))


# ---- Elegir

def test_elegir_marca_el_elemento_y_avisa_una_vez(crear):
    lista = crear(fondo_elegido=tema.COLOR_ACTIVO)
    lista.cargar(datos(1, 2))
    lista.elegir(2)
    lista.elegir(2)  # el mismo: no vuelve a avisar
    assert lista.seleccionado() == 2 and lista.avisos["elegido"] == [2]
    assert marcado(lista.elemento(2)) and tuple(lista.elemento(2).cget("fg_color")) == tema.COLOR_ACTIVO
    lista.elegir(1)
    assert not marcado(lista.elemento(2)) and lista.elemento(2).cget("border_width") == 1  # recupera el suyo


def test_seleccionar_desde_el_codigo_no_avisa_y_un_id_que_no_esta_no_hace_nada(crear):
    lista = crear()
    lista.cargar(datos(1, 2))
    lista.seleccionar(2)
    lista.seleccionar(99)
    assert lista.seleccionado() == 2 and lista.avisos["elegido"] == []


def test_un_clic_elige(crear):
    lista = crear()
    lista.cargar(datos(1, 2))
    lista._clic(2)
    assert lista.seleccionado() == 2 and lista.avisos["elegido"] == [2]


@pytest.mark.parametrize("teclas, esperado", [
    ([("fila", 1)], 1),                    # sin elegido, la primera flecha elige el primero
    ([("fila", 1), ("fila", 1)], 4),       # abajo: una fila son 3 elementos
    ([("fila", 1), ("elemento", 1)], 2),   # a la derecha: el siguiente
    ([("fila", 1), ("fila", -1)], 1),      # límite: arriba del primero sigue el primero
    ([("fila", 1), ("fila", 1), ("fila", 1), ("fila", 1)], 5),  # límite: no pasa del último
])
def test_las_flechas_recorren_la_rejilla(crear, teclas, esperado):
    lista = crear(columnas=3)
    lista.cargar(datos(1, 2, 3, 4, 5))
    for unidad, paso in teclas:
        assert lista._mover(unidad, paso) == "break"
    assert lista.seleccionado() == esperado


def test_en_una_columna_los_lados_no_mueven(crear):
    lista = crear()
    lista.cargar(datos(1, 2))
    lista.elegir(1)
    lista._mover("elemento", 1)
    assert lista.seleccionado() == 1


def test_las_flechas_en_una_lista_vacia_no_fallan(crear):
    lista = crear()
    assert lista._mover("fila", 1) == "break" and lista.seleccionado() is None


def test_enter_activa_el_elegido_y_sin_elegido_no_hace_nada(crear):
    lista = crear()
    lista.cargar(datos(1, 2))
    assert lista._activar() is None and lista.avisos["activado"] == []
    lista.elegir(2)
    assert lista._activar() == "break" and lista.avisos["activado"] == [2]


# ---- De a pocos

def test_con_filas_crea_al_instante_solo_los_que_se_ven(crear, raiz_tk):
    lista = crear(filas=2)
    lista.cargar(datos(1, 2, 3, 4, 5))
    assert lista.avisos["creados"] == 2 and lista.cantidad == 5  # conoce los 5; crea 2
    turnos(raiz_tk)  # los turnos siguientes crean el resto
    assert lista.avisos["creados"] == 5


def test_elegir_uno_que_aun_no_existe_lo_crea_ya(crear):
    lista = crear(filas=1)
    lista.cargar(datos(1, 2, 3, 4))
    lista.elegir(3)
    assert lista.seleccionado() == 3 and marcado(lista.elemento(3))
    assert {1, 2, 3} <= set(lista._elementos)


def test_de_fondo_no_crea_ninguno_al_instante(crear, raiz_tk):
    lista = crear(filas=2)
    lista.cargar(datos(1, 2, 3), de_fondo=True)
    assert lista.avisos["creados"] == 0 and lista.cantidad == 3
    turnos(raiz_tk)
    assert lista.avisos["creados"] == 3


def test_una_recarga_cancela_la_carga_pendiente(crear, raiz_tk):
    lista = crear(filas=1)
    lista.cargar(datos(1, 2, 3))
    lista.cargar(datos(7))
    turnos(raiz_tk)
    assert lista._ids == [7] and set(lista._elementos) == {7}


def test_destruir_cancela_lo_pendiente(crear):
    lista = crear(filas=1)
    lista.cargar(datos(1, 2, 3))
    tarea = lista._tarea_carga
    assert tarea is not None
    lista.destroy()
    assert tarea not in lista.tk.call("after", "info")


# ---- Desplazamiento

def test_la_rueda_sigue_de_largo_si_la_lista_cabe(crear):
    lista = crear(filas=5)
    lista.cargar(datos(1))
    assert lista._rueda(type("Evento", (), {"delta": -120})()) is None  # la pantalla se desplaza, no la lista


def test_columnas_o_filas_invalidas(raiz_tk):
    with pytest.raises(ValueError):
        ListaSeleccion(raiz_tk, Elemento, "", alto_elemento=20, columnas=0)
    with pytest.raises(ValueError):
        ListaSeleccion(raiz_tk, Elemento, "", alto_elemento=20, filas=0)
