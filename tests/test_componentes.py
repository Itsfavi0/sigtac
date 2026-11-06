from datetime import date
from pathlib import Path

import customtkinter as ctk
import pytest

from models.cama import CamaObservacion
from models.documento import TipoDocumento
from models.estados import EstadoCama
from models.excepciones import ReglaNegocioError
from views import tema
from views.componentes import (BotonPrimario, BotonSecundario, CamposDocumento, CamposPaciente, FichaPaciente,
                               InsigniaNivel, Marca, Selector,
                               TablaDatos, Tarjeta, TarjetaCama, TarjetaKPI, campo_texto, casilla, confirmar, errores,
                               etiqueta_campo, lista_opciones, marcar_error, marcar_foco, mostrar_error, mostrar_info,
                               pedir_ruta_pdf, texto_nivel)
from views.componentes.documento import ETIQUETAS
from views.componentes.periodo import CamposPeriodo, periodo_de, texto_periodo
from views.componentes.tabla import ALTO_FILA


def textos(widget) -> list[str]:
    """Textos de las etiquetas hijas de un widget, en orden."""
    return [hijo.cget("text") for hijo in widget.winfo_children() if isinstance(hijo, ctk.CTkLabel)]


# ---- errores.py

@pytest.fixture
def dialogos(monkeypatch):
    """Reemplaza los diálogos de messagebox (que bloquearían la prueba) y anota cómo se llamaron."""
    llamadas = []

    def registrar(tipo, respuesta=None):
        def dialogo(titulo, texto, parent=None):
            llamadas.append((tipo, titulo, texto, parent))
            return respuesta
        return dialogo

    monkeypatch.setattr(errores.messagebox, "showerror", registrar("error"))
    monkeypatch.setattr(errores.messagebox, "showinfo", registrar("info"))
    monkeypatch.setattr(errores.messagebox, "askyesno", registrar("pregunta", respuesta=True))
    return llamadas


def test_mostrar_error_usa_el_mensaje_del_error(dialogos):
    ventana = object()
    mostrar_error(ventana, ReglaNegocioError("El paciente ya tiene un episodio abierto."))
    assert dialogos == [("error", "SIGTAC", "El paciente ya tiene un episodio abierto.", ventana)]


def test_error_sin_mensaje(dialogos):
    mostrar_error(None, ValueError())
    assert dialogos[0][2] == errores.MENSAJE_SIN_TEXTO


def test_mostrar_info_y_confirmar(dialogos):
    mostrar_info(None, "Triaje registrado")
    assert confirmar(None, "¿Fusionar los pacientes?") is True
    assert [(tipo, texto) for tipo, _, texto, _ in dialogos] == [
        ("info", "Triaje registrado"), ("pregunta", "¿Fusionar los pacientes?")]


@pytest.mark.parametrize("elegida, esperada", [("C:/reportes/octubre.pdf", Path("C:/reportes/octubre.pdf")),
                                               ("", None)])  # "" = el usuario canceló
def test_pedir_ruta_pdf_propone_el_nombre_y_devuelve_la_ruta(monkeypatch, elegida, esperada):
    recibido = {}

    def guardar_como(**opciones):
        recibido.update(opciones)
        return elegida

    monkeypatch.setattr(errores.filedialog, "asksaveasfilename", guardar_como)
    ventana = object()
    assert pedir_ruta_pdf(ventana, "indicadores.pdf") == esperada
    assert recibido["parent"] is ventana and recibido["initialfile"] == "indicadores.pdf"
    assert recibido["defaultextension"] == ".pdf"


# ---- nivel.py

@pytest.mark.parametrize("nivel, texto", [
    (None, "Sin triaje"), (1, "1 · Rojo"), (2, "2 · Naranja"), (3, "3 · Amarillo"), (4, "4 · Verde"), (5, "5 · Azul"),
])
def test_texto_nivel(nivel, texto):
    assert texto_nivel(nivel) == texto


@pytest.mark.parametrize("nivel", [0, 6, "3"])
def test_texto_nivel_desconocido(nivel):
    with pytest.raises(ValueError, match="desconocido"):
        texto_nivel(nivel)


def test_insignia_sin_triaje(raiz_tk):
    insignia = InsigniaNivel(raiz_tk)
    assert insignia.nivel is None and insignia.texto == "–"
    assert tuple(insignia.cget("fg_color")) == tema.COLOR_SIN_DATO


@pytest.mark.parametrize("nivel", [1, 2, 3, 4, 5])
def test_insignia_con_el_numero_y_el_color_del_nivel(raiz_tk, nivel):
    insignia = InsigniaNivel(raiz_tk)
    insignia.mostrar(nivel)
    assert insignia.texto == str(nivel)  # el número: el nivel no depende solo del color
    assert tuple(insignia.cget("fg_color")) == tema.COLOR_NIVEL[nivel]
    assert tuple(insignia._numero.cget("text_color")) == tema.texto_sobre(tema.COLOR_NIVEL[nivel])


def test_insignia_con_nivel_invalido_no_cambia(raiz_tk):
    insignia = InsigniaNivel(raiz_tk)
    insignia.mostrar(2)
    with pytest.raises(ValueError):
        insignia.mostrar(9)
    assert insignia.nivel == 2 and insignia.texto == "2"


def test_insignia_grande_usa_letra_de_titulo(raiz_tk):
    assert InsigniaNivel(raiz_tk, lado=44)._numero.cget("font").cget("size") == 20


# ---- tarjetas.py

def test_tarjeta_kpi(raiz_tk):
    tarjeta = TarjetaKPI(raiz_tk, "Camas libres", color=tema.COLOR_ESTADO_CAMA[EstadoCama.DISPONIBLE])
    assert "Camas libres" in textos(tarjeta.winfo_children()[0])
    assert (tarjeta.valor, tarjeta.nota) == ("—", "")  # sin dato todavía
    tarjeta.mostrar("15 / 36", "42 % disponible")
    assert (tarjeta.valor, tarjeta.nota) == ("15 / 36", "42 % disponible")
    tarjeta.mostrar(None)
    assert (tarjeta.valor, tarjeta.nota) == ("—", "")


@pytest.mark.parametrize("estado", list(EstadoCama))
def test_tarjeta_cama_con_los_colores_de_su_estado(raiz_tk, estado):
    cama = CamaObservacion(7, "OBS-07", "Observación", estado)
    tarjeta = TarjetaCama(raiz_tk, cama)
    assert tuple(tarjeta.cget("fg_color")) == tema.COLOR_FONDO_ESTADO_CAMA[estado]
    assert tuple(tarjeta.cget("border_color")) == tema.COLOR_BORDE_ESTADO_CAMA[estado]
    assert tuple(tarjeta._franja.cget("fg_color")) == tema.COLOR_ESTADO_CAMA[estado]
    assert textos(tarjeta) == ["OBS-07", TarjetaCama.texto_estado(estado)]  # el estado va escrito
    assert tarjeta.cama is cama


def test_tarjeta_cama_con_detalle_lo_dice_en_lugar_del_estado(raiz_tk):
    # En una lista donde todas están disponibles, el tipo de cama dice más que el estado
    tarjeta = TarjetaCama(raiz_tk, CamaObservacion(7, "OBS-07", "Obs", EstadoCama.DISPONIBLE), detalle="Observación")
    assert textos(tarjeta) == ["OBS-07", "Observación"]


def test_tarjeta_cama_se_vuelve_a_pintar_sin_rehacerse(raiz_tk):
    tarjeta = TarjetaCama(raiz_tk, CamaObservacion(7, "OBS-07", "Obs", EstadoCama.DISPONIBLE))
    hijos = tarjeta.winfo_children()
    otra = CamaObservacion(7, "OBS-07", "Obs", EstadoCama.FUERA_SERVICIO)
    tarjeta.mostrar(otra)
    assert tarjeta.winfo_children() == hijos and tarjeta.cama is otra
    assert tuple(tarjeta.cget("fg_color")) == tema.COLOR_FONDO_ESTADO_CAMA[EstadoCama.FUERA_SERVICIO]
    assert textos(tarjeta) == ["OBS-07", "F. de servicio"] and tarjeta._codigo.cget("font").cget("overstrike")


def test_texto_del_estado_en_la_casilla():
    assert TarjetaCama.texto_estado(EstadoCama.EN_LIMPIEZA) == "En limpieza"
    assert TarjetaCama.texto_estado(EstadoCama.FUERA_SERVICIO) == "F. de servicio"  # la forma corta


def test_cama_fuera_de_servicio_con_codigo_tachado(raiz_tk):
    fuera = TarjetaCama(raiz_tk, CamaObservacion(1, "OBS-01", "Obs", EstadoCama.FUERA_SERVICIO))
    libre = TarjetaCama(raiz_tk, CamaObservacion(2, "OBS-02", "Obs", EstadoCama.DISPONIBLE))
    def codigo(tarjeta):
        return [h for h in tarjeta.winfo_children() if isinstance(h, ctk.CTkLabel)][0]
    assert codigo(fuera).cget("font").cget("overstrike")
    assert not codigo(libre).cget("font").cget("overstrike")


def test_alto_de_la_casilla_multiplo_de_4():
    assert TarjetaCama.ALTO % 4 == 0


# ---- foco.py

def test_el_foco_engrosa_el_borde_y_el_error_lo_mantiene(raiz_tk):
    from views.componentes.foco import al_entrar, al_salir
    campo = marcar_foco(ctk.CTkEntry(raiz_tk, border_width=1, border_color=tema.COLOR_BORDE_CAMPO))
    assert {"<FocusIn>", "<FocusOut>"} <= set(campo._entry.bind())  # CTkEntry recibe el foco en su Entry interno
    al_entrar(campo)
    assert campo.cget("border_width") == 2 and tuple(campo.cget("border_color")) == tema.COLOR_PRIMARIO_GRAFICO
    al_salir(campo)
    assert campo.cget("border_width") == 1 and tuple(campo.cget("border_color")) == tema.COLOR_BORDE_CAMPO
    marcar_error(campo)
    al_entrar(campo)
    assert tuple(campo.cget("border_color")) == tema.COLOR_ERROR  # el foco no tapa el error
    marcar_error(campo, False)
    assert campo.cget("border_width") == 1


# ---- documento.py

def test_hay_una_etiqueta_por_tipo_de_documento():
    assert set(ETIQUETAS) == set(TipoDocumento)
    assert len(set(ETIQUETAS.values())) == len(ETIQUETAS)  # sin etiquetas repetidas


def test_campos_documento_por_defecto_dni_vacio(raiz_tk):
    assert CamposDocumento(raiz_tk).valores() == (TipoDocumento.DNI, "")


def test_fijar_y_limpiar(raiz_tk):
    campos = CamposDocumento(raiz_tk)
    campos.fijar(TipoDocumento.PASAPORTE, "AB123456")
    assert campos.valores() == (TipoDocumento.PASAPORTE, "AB123456")
    campos.fijar("CE", "X1234567")  # también acepta el código de la BD
    assert campos.valores() == (TipoDocumento.CARNE_EXTRANJERIA, "X1234567")
    campos.limpiar()
    assert campos.valores() == (TipoDocumento.DNI, "")


def test_no_valida_el_numero(raiz_tk):
    # El formato lo valida DocumentoIdentidad en el controlador: aquí llega tal cual se escribió
    campos = CamposDocumento(raiz_tk)
    campos.fijar(TipoDocumento.DNI, " 123 ")
    assert campos.valores() == (TipoDocumento.DNI, " 123 ")


def test_avisa_al_cambiar_el_tipo(raiz_tk):
    from views.componentes.campos import mover_opcion
    campos = CamposDocumento(raiz_tk)
    avisos = []
    campos.al_cambiar_tipo(lambda: avisos.append(campos.valores()[0]))
    mover_opcion(campos._tipo, 1)  # ↓ en la lista, como el usuario
    assert avisos == [TipoDocumento.CARNE_EXTRANJERIA]


def test_bloquear_deja_los_campos_solo_para_leer(raiz_tk):
    campos = CamposDocumento(raiz_tk)
    campos.bloquear()
    campos.fijar(TipoDocumento.DNI, "45678912")  # se puede poner el documento aunque esté bloqueado
    assert campos.valores() == (TipoDocumento.DNI, "45678912")
    assert campos._numero.cget("state") == "disabled" and campos._tipo.cget("state") == "disabled"
    campos.bloquear(False)
    assert campos._numero.cget("state") == "normal" and campos._tipo.cget("state") == "readonly"


# ---- tabla.py

COLUMNAS = [("N.º", 40), ("Paciente", 200), ("Motivo", 240)]


def test_tabla_vacia_muestra_el_texto(raiz_tk):
    tabla = TablaDatos(raiz_tk, COLUMNAS, "No hay pacientes esperando triaje")
    assert tabla.cantidad == 0
    assert tabla._vacio.winfo_manager() == "place"
    assert tabla._vacio.cget("text") == "No hay pacientes esperando triaje"
    assert tabla.seleccionado() is None


def test_cargar_filas_oculta_el_texto_de_vacia(raiz_tk):
    tabla = TablaDatos(raiz_tk, COLUMNAS, "Vacía")
    tabla.cargar([(31, (1, "Ana Torres", "Dolor torácico")), (35, (2, "NN", None))])
    assert tabla.cantidad == 2
    assert tabla._vacio.winfo_manager() == ""
    filas = [tabla._arbol.item(iid, "values") for iid in tabla._arbol.get_children()]
    assert filas == [("1", "Ana Torres", "Dolor torácico"), ("2", "NN", "")]  # None se muestra vacío


def test_tabla_con_filas_mide_eso_mas_el_encabezado_aunque_tenga_mas(raiz_tk):
    marco = ctk.CTkFrame(raiz_tk)
    tabla = TablaDatos(marco, COLUMNAS, "Vacía", filas=3)
    tabla.pack(fill="x")
    assert tabla.cget("height") == ALTO_FILA * 4
    tabla.cargar([(i, (i, "Ana", "x")) for i in range(20)])  # las demás se desplazan por dentro
    raiz_tk.update()  # la ventana de las pruebas está oculta: se compara el alto pedido, no el dibujado
    assert tabla.winfo_reqheight() == round(ALTO_FILA * 4 * tema.escala(tabla))
    marco.destroy()


def test_tabla_con_menos_de_una_fila_es_un_error(raiz_tk):
    with pytest.raises(ValueError):
        TablaDatos(raiz_tk, COLUMNAS, "Vacía", filas=0)


def test_seleccionar_devuelve_el_id_y_avisa(raiz_tk):
    elegidos = []
    tabla = TablaDatos(raiz_tk, COLUMNAS, "Vacía", al_seleccionar=elegidos.append)
    tabla.cargar([(31, (1, "Ana", "x")), (35, (2, "Luis", "y"))])
    tabla.seleccionar(35)
    raiz_tk.update()  # el evento <<TreeviewSelect>> se procesa en el ciclo de Tk
    assert tabla.seleccionado() == 35
    assert elegidos == [35]


def test_seleccionar_un_id_que_no_esta_no_hace_nada(raiz_tk):
    tabla = TablaDatos(raiz_tk, COLUMNAS, "Vacía")
    tabla.cargar([(31, (1, "Ana", "x"))])
    tabla.seleccionar(99)
    assert tabla.seleccionado() is None


def test_recargar_borra_la_seleccion(raiz_tk):
    elegidos = []
    tabla = TablaDatos(raiz_tk, COLUMNAS, "Vacía", al_seleccionar=elegidos.append)
    tabla.cargar([(31, (1, "Ana", "x"))])
    tabla.seleccionar(31)
    raiz_tk.update()
    tabla.cargar([])
    raiz_tk.update()
    assert tabla.seleccionado() is None and tabla.cantidad == 0
    assert elegidos == [31, None]  # la vista se entera de que ya no hay fila elegida


@pytest.mark.parametrize("oscuro, i", [(False, 0), (True, 1)])
def test_la_tabla_toma_los_tonos_del_modo(raiz_tk, oscuro, i):
    from tkinter import ttk

    from views.componentes.tabla import ESTILO, _configurar_estilo
    TablaDatos(raiz_tk, COLUMNAS, "Vacía")
    _configurar_estilo(raiz_tk, oscuro=oscuro)
    estilo = ttk.Style(raiz_tk)
    assert estilo.lookup(ESTILO, "background") == tema.COLOR_SUPERFICIE[i]
    assert estilo.lookup(ESTILO, "foreground") == tema.COLOR_TEXTO[i]


# ---- botones.py

def test_boton_primario_azul_y_ejecuta_su_accion(raiz_tk):
    llamadas = []
    boton = BotonPrimario(raiz_tk, "Ingresar", lambda: llamadas.append("ok"))
    assert boton.cget("text") == "Ingresar"
    assert tuple(boton.cget("fg_color")) == tema.COLOR_PRIMARIO
    assert boton.cget("height") == tema.ALTO_CONTROL
    boton.invoke()
    assert llamadas == ["ok"]


def test_boton_primario_deshabilitado_conserva_el_texto_legible(raiz_tk):
    # El gris por defecto de CustomTkinter no se lee sobre el azul
    boton = BotonPrimario(raiz_tk, "Ingresar", None)
    assert tuple(boton.cget("text_color_disabled")) == tema.COLOR_TEXTO_SOBRE_PRIMARIO


def test_boton_deshabilitado_no_ejecuta_su_accion(raiz_tk):
    llamadas = []
    boton = BotonSecundario(raiz_tk, "Cerrar sesión", lambda: llamadas.append("ok"), state="disabled")
    boton.invoke()
    assert llamadas == []


def test_boton_secundario_con_borde_y_sin_relleno(raiz_tk):
    boton = BotonSecundario(raiz_tk, "Cerrar sesión", None)
    assert boton.cget("fg_color") == "transparent"
    assert boton.cget("border_width") == 1 and tuple(boton.cget("border_color")) == tema.COLOR_BORDE_CAMPO


# ---- marca.py

def test_marca_con_nombre_y_servicio(raiz_tk):
    assert textos(Marca(raiz_tk)) == ["SIGTAC", "Emergencia"]


def test_medidas_de_la_marca_multiplos_de_4():
    assert all(medida % 4 == 0 for medida in (Marca.LADO_LOGO, Marca.ALTO_NOMBRE, Marca.ALTO_SERVICIO))
    assert Marca.ALTO_NOMBRE + Marca.ALTO_SERVICIO == Marca.LADO_LOGO  # las dos líneas miden lo que el logo


# ---- campos.py

def test_campo_texto_con_el_estilo_del_tema_y_foco(raiz_tk):
    from views.componentes.foco import al_entrar
    campo = campo_texto(raiz_tk, "Número")
    assert campo.cget("placeholder_text") == "Número"
    assert campo.cget("height") == tema.ALTO_CONTROL
    assert tuple(campo.cget("border_color")) == tema.COLOR_BORDE_CAMPO
    al_entrar(campo)
    assert tuple(campo.cget("border_color")) == tema.COLOR_PRIMARIO_GRAFICO  # el foco se ve


def test_campo_texto_acepta_opciones_propias(raiz_tk):
    clave = campo_texto(raiz_tk, show="•")
    assert clave.cget("show") == "•"  # oculta desde el principio, no solo después de recibir el foco
    clave.insert(0, "secreta")
    assert clave.cget("show") == "•" and clave.get() == "secreta"


def test_etiqueta_campo(raiz_tk):
    etiqueta = etiqueta_campo(raiz_tk, "Contraseña")
    assert etiqueta.cget("text") == "Contraseña"
    assert tuple(etiqueta.cget("text_color")) == tema.COLOR_ETIQUETA



# ---- foco de botones e interruptores

def test_un_boton_acepta_el_foco_y_se_activa_con_enter_o_espacio(raiz_tk):
    llamadas = []
    boton = BotonSecundario(raiz_tk, "Cerrar sesión", lambda: llamadas.append("ok"))
    from views.componentes.foco import TECLAS_ACTIVAR, activar
    assert str(boton._canvas.cget("takefocus")) == "1"
    assert all(boton._canvas.bind(tecla) for tecla in TECLAS_ACTIVAR)  # Enter y espacio tienen acción
    # Tk no entrega teclas a una ventana oculta: se llama a lo que ejecutan
    activar(boton)
    assert llamadas == ["ok"]


@pytest.mark.parametrize("clase, color_foco", [
    (BotonSecundario, tema.COLOR_PRIMARIO_GRAFICO), (BotonPrimario, tema.COLOR_TEXTO),  # sobre el azul, el del texto
])
def test_el_foco_de_un_boton_se_ve_y_al_salir_vuelve_su_borde(raiz_tk, clase, color_foco):
    from views.componentes.foco import GROSOR_FOCO, al_entrar_control, al_salir_control
    boton = clase(raiz_tk, "Aceptar", None)
    borde = (boton.cget("border_width"), boton.cget("border_color"))
    al_entrar_control(boton)
    assert boton.cget("border_width") == GROSOR_FOCO and tuple(boton.cget("border_color")) == color_foco
    al_salir_control(boton)
    assert (boton.cget("border_width"), boton.cget("border_color")) == borde


def test_fijar_borde_con_foco_se_aplica_al_salir(raiz_tk):
    from views.componentes.foco import GROSOR_FOCO, al_entrar_control, al_salir_control, fijar_borde
    boton = BotonSecundario(raiz_tk, "Aceptar", None)
    al_entrar_control(boton)
    fijar_borde(boton, 0, tema.COLOR_BORDE)
    assert boton.cget("border_width") == GROSOR_FOCO  # mientras tiene el foco, se ve el foco
    al_salir_control(boton)
    assert boton.cget("border_width") == 0



def test_el_tipo_de_documento_se_elige_con_el_teclado(raiz_tk):
    campos = CamposDocumento(raiz_tk)
    caja = campos._tipo._entry
    assert all(caja.bind(tecla) for tecla in ("<Up>", "<Down>", "<space>", "<Alt-Down>"))
    # Tk no entrega teclas a una ventana oculta: se llama a lo que ejecutan ↓ y ↑
    assert campos.cambiar_tipo(1) == "break"
    assert campos.valores()[0] == TipoDocumento.CARNE_EXTRANJERIA
    campos.cambiar_tipo(-1)
    campos.cambiar_tipo(-1)  # en el primero no da la vuelta
    assert campos.valores()[0] == TipoDocumento.DNI


def test_el_tipo_bloqueado_no_cambia_con_el_teclado(raiz_tk):
    campos = CamposDocumento(raiz_tk)
    campos.bloquear()
    campos.cambiar_tipo(1)
    assert campos.valores()[0] == TipoDocumento.DNI


def test_el_tipo_de_documento_muestra_el_foco(raiz_tk):
    from views.componentes.foco import al_entrar
    campos = CamposDocumento(raiz_tk)
    al_entrar(campos._tipo)
    assert tuple(campos._tipo.cget("border_color")) == tema.COLOR_PRIMARIO_GRAFICO


# ---- Tarjeta (sección con título)

def test_tarjeta_con_titulo_subtitulo_y_lugar_en_la_cabecera(raiz_tk):
    tarjeta = Tarjeta(raiz_tk, "1. Paciente", "Búsquelo por su documento")
    assert (tarjeta.titulo, tarjeta.subtitulo) == ("1. Paciente", "Búsquelo por su documento")
    assert tuple(tarjeta.cget("fg_color")) == tema.COLOR_SUPERFICIE
    assert tuple(tarjeta.cget("border_color")) == tema.COLOR_BORDE and tarjeta.cget("border_width") == 1
    assert tarjeta.cget("corner_radius") == tema.RADIO_TARJETA
    ctk.CTkLabel(tarjeta.cabecera, text="extra").pack(side="right")  # la leyenda del mapa, un selector...


def test_tarjeta_acepta_opciones_propias(raiz_tk):
    assert Tarjeta(raiz_tk, "Clasificación", "", width=320).cget("width") == 320


# ---- lista_opciones

def test_lista_empieza_en_la_primera_o_vacia(raiz_tk):
    assert lista_opciones(raiz_tk, ["A", "B"]).get() == "A"
    assert lista_opciones(raiz_tk, ["A", "B"], vacia=True).get() == ""
    assert lista_opciones(raiz_tk, []).get() == ""


def test_lista_con_el_estilo_de_los_campos(raiz_tk):
    lista = lista_opciones(raiz_tk, ["A"])
    assert lista.cget("state") == "readonly" and lista.cget("height") == tema.ALTO_CONTROL
    assert tuple(lista.cget("border_color")) == tema.COLOR_BORDE_CAMPO


def test_lista_con_el_teclado_avisa_como_el_mouse(raiz_tk):
    from views.componentes.campos import mover_opcion
    elegidas = []
    lista = lista_opciones(raiz_tk, ["A", "B", "C"], vacia=True, command=elegidas.append)
    assert all(lista._entry.bind(tecla) for tecla in ("<Up>", "<Down>", "<space>", "<Alt-Down>"))
    assert mover_opcion(lista, 1) == "break"
    assert lista.get() == "A"  # vacía: ↓ elige la primera
    mover_opcion(lista, 1)
    mover_opcion(lista, 1)
    mover_opcion(lista, 1)  # en la última no da la vuelta ni vuelve a avisar
    assert lista.get() == "C" and elegidas == ["A", "B", "C"]


def test_lista_deshabilitada_no_cambia(raiz_tk):
    from views.componentes.campos import mover_opcion
    lista = lista_opciones(raiz_tk, ["A", "B"])
    lista.configure(state="disabled")
    mover_opcion(lista, 1)
    assert lista.get() == "A"


# ---- casilla

def test_ajustar_casilla_parte_el_texto_sin_contar_el_cuadro(raiz_tk):
    from views.componentes.campos import LADO_CASILLA, SEPARACION_CASILLA, ajustar_casilla
    caja = casilla(raiz_tk, "Alteración de la Conciencia (Glasgow < 8)")
    ajustar_casilla(caja, 200)
    cuadro = caja._apply_widget_scaling(LADO_CASILLA + SEPARACION_CASILLA)
    assert int(caja._text_label.cget("wraplength")) == 200 - cuadro
    ajustar_casilla(caja, 10)  # más angosta que el cuadro: no un ancho negativo (Tk lo leería como «sin límite»)
    assert int(caja._text_label.cget("wraplength")) == 1


def test_casilla_se_marca_con_el_teclado_y_avisa(raiz_tk):
    from views.componentes.foco import activar
    cambios = []
    caja = casilla(raiz_tk, "Tos leve", lambda: cambios.append(True))
    assert caja.cget("text") == "Tos leve" and caja.get() == 0
    assert str(caja._canvas.cget("takefocus")) == "1"
    activar(caja)  # lo que hacen espacio o Enter
    assert caja.get() == 1 and cambios == [True]


def test_el_foco_de_la_casilla_se_ve_tambien_marcada(raiz_tk):
    from views.componentes.foco import GROSOR_FOCO, al_entrar_control
    caja = casilla(raiz_tk, "Tos leve")
    caja.select()
    al_entrar_control(caja)
    # Con el color del texto: un borde azul no se vería sobre la casilla marcada (azul)
    assert caja.cget("border_width") == GROSOR_FOCO and tuple(caja.cget("border_color")) == tema.COLOR_TEXTO


# ---- Selector

def test_selector_empieza_en_la_primera_marcada_como_el_item_activo(raiz_tk):
    selector = Selector(raiz_tk, [("nuevo", "Nuevo"), ("cola", "En cola")])
    activo, otro = selector.botones["nuevo"], selector.botones["cola"]
    assert selector.valor == "nuevo"
    assert tuple(activo.cget("fg_color")) == tema.COLOR_ACTIVO and activo.cget("border_width") == 1
    assert otro.cget("fg_color") == "transparent" and otro.cget("border_width") == 0


def test_selector_avisa_solo_cuando_cambia(raiz_tk):
    cambios = []
    selector = Selector(raiz_tk, [("a", "A"), ("b", "B")], cambios.append)
    selector.botones["b"].invoke()
    selector.botones["b"].invoke()
    selector.elegir("a", avisar=False)
    assert cambios == ["b"] and selector.valor == "a"


def test_selector_se_maneja_con_el_teclado(raiz_tk):
    from views.componentes.foco import activar
    selector = Selector(raiz_tk, [("a", "A"), ("b", "B")])
    assert all(str(b._canvas.cget("takefocus")) == "1" for b in selector.botones.values())
    activar(selector.botones["b"])
    assert selector.valor == "b"


def test_selector_cambia_el_texto_de_una_opcion(raiz_tk):
    selector = Selector(raiz_tk, [("cola", "En cola")])
    selector.cambiar_texto("cola", "En cola (3)")
    assert selector.texto("cola") == "En cola (3)"


def test_selector_sin_eleccion_y_volver_a_elegir_la_misma_avisa(raiz_tk):
    # Un período escrito a mano no es ningún atajo; volver a pulsar el que estaba debe aplicarlo de nuevo
    cambios = []
    selector = Selector(raiz_tk, [("a", "A"), ("b", "B")], cambios.append)
    selector.quitar_eleccion()
    assert selector.valor is None
    assert all(b.cget("fg_color") == "transparent" and b.cget("border_width") == 0 for b in selector.botones.values())
    selector.botones["a"].invoke()
    assert cambios == ["a"] and selector.valor == "a"


def test_selector_de_repetir_avisa_tambien_la_misma_opcion(raiz_tk):
    cambios = []
    selector = Selector(raiz_tk, [("a", "A"), ("b", "B")], cambios.append, repetir=True)
    selector.botones["a"].invoke()
    selector.botones["a"].invoke()
    selector.elegir("a", avisar=False)
    assert cambios == ["a", "a"]


def test_selector_rechaza_opciones_invalidas(raiz_tk):
    with pytest.raises(ValueError):
        Selector(raiz_tk, [])
    with pytest.raises(ValueError, match="desconocida"):
        Selector(raiz_tk, [("a", "A")]).elegir("z")


# ---- marcar_error mientras se escribe

def test_quitar_el_error_a_un_campo_con_foco_deja_el_borde_de_foco(raiz_tk, monkeypatch):
    from views.componentes.foco import GROSOR_FOCO
    campo = campo_texto(raiz_tk)
    marcar_error(campo)
    # Tk no da el foco a una ventana oculta: se simula que el campo lo tiene
    monkeypatch.setattr(campo, "focus_get", lambda: campo._entry)
    marcar_error(campo, False)
    assert campo.cget("border_width") == GROSOR_FOCO and tuple(campo.cget("border_color")) == tema.COLOR_PRIMARIO_GRAFICO


# ---- Datos del paciente (CamposPaciente, FichaPaciente)

def _paciente(**cambios):
    from datetime import date
    from models.documento import DocumentoIdentidad
    from models.persona import Paciente
    datos = dict(id_paciente=7, documento=DocumentoIdentidad("DNI", "41234567"), nombres="Carmen",
                 apellidos="Rojas Llanos", fecha_nac=date(1985, 3, 14), sexo="F", id_seguro=2,
                 nombre_seguro="SIS")
    datos.update(cambios)
    return Paciente(**datos)


SEGUROS = [{"id_seguro": 1, "nombre_seguro": "EsSalud"}, {"id_seguro": 2, "nombre_seguro": "SIS"}]


def test_campos_paciente_empiezan_vacios_sin_sexo_ni_seguro_elegidos(raiz_tk):
    campos = CamposPaciente(raiz_tk)
    assert [c.get() for c in campos.entradas] == ["", "", ""]
    assert campos.sexo.get() == "" and campos.seguro.get() == ""
    assert campos.fecha_nac.cget("placeholder_text") == "dd/mm/aaaa"


def test_campos_paciente_fijar_y_leer(raiz_tk):
    from datetime import date
    campos = CamposPaciente(raiz_tk)
    campos.cargar_seguros(SEGUROS)
    campos.fijar(_paciente())
    assert campos.fecha_nac.get() == "14/03/1985" and campos.sexo.get() == "Mujer" and campos.seguro.get() == "SIS"
    assert campos.valores() == {"nombres": "Carmen", "apellidos": "Rojas Llanos", "fecha_nac": date(1985, 3, 14),
                                "sexo": "F", "id_seguro": 2}


@pytest.mark.parametrize("preparar, campo, mensaje", [
    (lambda c: c.fecha_nac.insert(0, "1985-03-14"), "fecha_nac", "La fecha de nacimiento debe tener la forma"),
    (lambda c: c.fecha_nac.insert(0, "14/03/1985"), "sexo", "Elija el sexo del paciente."),
    (lambda c: (c.fecha_nac.insert(0, "14/03/1985"), c.sexo.set("Varón")), "seguro", "Elija el seguro del paciente."),
])
def test_campos_paciente_marcan_el_campo_que_no_se_puede_leer(raiz_tk, preparar, campo, mensaje):
    campos = CamposPaciente(raiz_tk)
    campos.cargar_seguros(SEGUROS)
    preparar(campos)
    with pytest.raises(ValueError, match=mensaje):
        campos.valores()
    assert getattr(campos, campo)._sigtac_error
    campos.limpiar()
    assert not getattr(campos, campo)._sigtac_error and campos.fecha_nac.get() == ""


def test_campos_paciente_vacios_marcan_todos_a_la_vez(raiz_tk):
    # No solo el primero: así se ve de una vez todo lo que falta. El mensaje es el del primero (la fecha)
    campos = CamposPaciente(raiz_tk)
    campos.cargar_seguros(SEGUROS)
    with pytest.raises(ValueError, match="La fecha de nacimiento debe tener la forma"):
        campos.valores()
    assert campos.fecha_nac._sigtac_error and campos.sexo._sigtac_error and campos.seguro._sigtac_error


def test_leer_todos_hace_todas_las_lecturas_y_lanza_el_primer_error(raiz_tk):
    from views.componentes.campos import leer_todos
    hechas = []

    def lectura(clave, error=None):
        def leer():
            hechas.append(clave)
            if error:
                raise ValueError(error)
            return clave.upper()
        return leer

    assert leer_todos({"a": lectura("a"), "b": lectura("b")}) == {"a": "A", "b": "B"}
    hechas.clear()
    with pytest.raises(ValueError, match="^falta b$"):
        leer_todos({"a": lectura("a"), "b": lectura("b", "falta b"), "c": lectura("c", "falta c")})
    assert hechas == ["a", "b", "c"]  # la tercera se leyó (y marcó) aunque la segunda falló


def test_campos_paciente_sin_sexo_ni_seguro_al_identificar(raiz_tk):
    from datetime import date
    campos = CamposPaciente(raiz_tk, con_sexo_y_seguro=False)
    assert campos.sexo is None and campos.seguro is None
    campos.nombres.insert(0, "Lucía")
    campos.apellidos.insert(0, "Paredes")
    campos.fecha_nac.insert(0, "02/05/2000")
    assert campos.valores() == {"nombres": "Lucía", "apellidos": "Paredes", "fecha_nac": date(2000, 5, 2)}


def test_ficha_paciente(raiz_tk):
    ficha = FichaPaciente(raiz_tk)
    ficha.mostrar(_paciente())
    assert ficha.nombre == "Carmen Rojas Llanos" and ficha.datos.endswith("años · mujer · SIS")
    assert ficha._documento.winfo_manager() == ""  # la ficha corta no muestra el documento


def test_ficha_ampliada_con_documento_y_nacimiento_y_dado_de_baja(raiz_tk):
    ficha = FichaPaciente(raiz_tk, ampliada=True)
    ficha.mostrar(_paciente(activo=False))
    assert ficha.documento == "DNI 41234567 · nació el 14/03/1985"
    assert ficha.datos.endswith("· Dado de baja")


def test_celda_de_rejilla_con_los_espacios_del_tema(raiz_tk):
    from views.componentes.campos import celda

    def margen(valor) -> tuple[int, ...]:
        # Tk lo devuelve como entero o como tupla, ya multiplicado por la escala de la ventana
        texto = str(valor).replace("(", " ").replace(")", " ").replace(",", " ")
        numeros = tuple(int(float(n)) for n in texto.split())
        return numeros if len(numeros) == 2 else numeros * 2

    escala = tema.escala(raiz_tk)
    primera, segunda = celda(raiz_tk, "A", 0, 0), celda(raiz_tk, "B", 1, 1)
    # Primera fila y primera columna sin margen; después, ESPACIO entre columnas y ESPACIO_2 arriba
    assert margen(primera.grid_info()["padx"]) == (0, 0) and margen(primera.grid_info()["pady"]) == (0, 0)
    assert margen(segunda.grid_info()["padx"]) == (round(tema.ESPACIO * escala), 0)
    assert margen(segunda.grid_info()["pady"]) == (round(tema.ESPACIO_2 * escala), 0)


def test_leer_opcion_y_campo_marcan_y_desmarcan(raiz_tk):
    from views.componentes.campos import leer_campo, leer_opcion, limpiar_al_corregir, sin_error
    lista = lista_opciones(raiz_tk, ["A"], vacia=True)
    with pytest.raises(ValueError, match="Elija"):
        leer_opcion(lista, {"A": 1}, "Elija algo.")
    assert lista._sigtac_error
    lista.set("A")
    assert leer_opcion(lista, {"A": 1}, "Elija algo.") == 1 and not lista._sigtac_error
    campo = campo_texto(raiz_tk)
    campo.insert(0, "x")
    with pytest.raises(ValueError):
        leer_campo(campo, int)
    limpiar_al_corregir(campo)
    assert campo._entry.bind("<KeyRelease>")
    sin_error(campo)
    assert not campo._sigtac_error


# ---- periodo.py (CamposPeriodo)

HOY = date(2026, 10, 15)


@pytest.mark.parametrize("atajo, hoy, esperado", [
    ("hoy", HOY, (HOY, HOY)),
    ("semana", HOY, (date(2026, 10, 9), HOY)),                              # 7 días contando hoy
    ("semana", date(2027, 1, 3), (date(2026, 12, 28), date(2027, 1, 3))),  # cruza el año
    ("mes", HOY, (date(2026, 10, 1), HOY)),
    ("mes", date(2026, 11, 1), (date(2026, 11, 1), date(2026, 11, 1))),    # el día 1: solo ese día
])
def test_periodo_de_cada_atajo(atajo, hoy, esperado):
    assert periodo_de(atajo, hoy) == esperado


def test_atajo_desconocido():
    with pytest.raises(ValueError, match="desconocido"):
        periodo_de("año", HOY)


def test_texto_del_periodo():
    assert texto_periodo(date(2026, 10, 1), HOY) == "Del 01/10/2026 al 15/10/2026"
    assert texto_periodo(HOY, HOY) == "El 15/10/2026"


def crear_periodo(raiz, hoy=HOY, **opciones):
    pedidos = []
    periodo = CamposPeriodo(raiz, lambda: pedidos.append(periodo.leer()), hoy=lambda: hoy, **opciones)
    return periodo, pedidos


def escribir_fecha(periodo, campo, texto):
    campo.delete(0, "end")
    campo.insert(0, texto)
    periodo.fechas_editadas()


def test_periodo_empieza_en_el_atajo_inicial_sin_avisar(raiz_tk):
    periodo, pedidos = crear_periodo(raiz_tk, inicial="hoy")
    assert (periodo.desde.get(), periodo.hasta.get()) == ("15/10/2026", "15/10/2026")
    assert periodo.atajos.valor == "hoy" and pedidos == []
    assert periodo.leer() == (HOY, HOY)


def test_periodo_sin_cabecera_pone_los_atajos_en_su_fila(raiz_tk):
    periodo, _ = crear_periodo(raiz_tk)
    assert periodo.atajos.master is periodo
    tarjeta = Tarjeta(raiz_tk, "Período", "")
    con_cabecera, _ = crear_periodo(tarjeta, cabecera=tarjeta.cabecera)
    assert con_cabecera.atajos.master is tarjeta.cabecera


def test_un_atajo_rellena_y_avisa_aunque_ya_este_marcado(raiz_tk):
    periodo, pedidos = crear_periodo(raiz_tk)
    periodo.atajos.botones["semana"].invoke()
    periodo.atajos.botones["semana"].invoke()
    assert pedidos == [(date(2026, 10, 9), HOY)] * 2


def test_el_atajo_sigue_a_lo_escrito_y_el_marcado_va_primero(raiz_tk):
    periodo, _ = crear_periodo(raiz_tk, hoy=date(2026, 11, 1))  # el día 1, «Hoy» y «Este mes» coinciden
    assert periodo.atajos.valor == "mes"
    escribir_fecha(periodo, periodo.desde, "31/10/2026")
    assert periodo.atajos.valor is None
    escribir_fecha(periodo, periodo.desde, "01/11/2026")
    assert periodo.atajos.valor == "hoy"  # sin marcado, el primero que coincide


def test_una_fecha_mal_escrita_queda_marcada_hasta_que_cambia(raiz_tk):
    periodo, _ = crear_periodo(raiz_tk)
    escribir_fecha(periodo, periodo.hasta, "31/02/2026")
    with pytest.raises(ValueError, match="dd/mm/aaaa"):
        periodo.leer()
    periodo.fechas_editadas()  # soltar el Enter: el texto no cambió
    assert periodo.hasta._sigtac_error
    escribir_fecha(periodo, periodo.hasta, "28/02/2026")
    assert not periodo.hasta._sigtac_error


def test_dos_fechas_mal_escritas_quedan_marcadas_las_dos(raiz_tk):
    periodo, _ = crear_periodo(raiz_tk)
    escribir_fecha(periodo, periodo.desde, "1/10")
    escribir_fecha(periodo, periodo.hasta, "31/02/2026")
    with pytest.raises(ValueError, match="La fecha inicial"):
        periodo.leer()
    assert periodo.desde._sigtac_error and periodo.hasta._sigtac_error


def test_rechazar_marca_las_dos_y_al_corregir_se_van(raiz_tk):
    periodo, _ = crear_periodo(raiz_tk)
    periodo.rechazar()
    assert periodo.desde._sigtac_error and periodo.hasta._sigtac_error
    escribir_fecha(periodo, periodo.desde, "02/10/2026")
    assert not periodo.desde._sigtac_error and not periodo.hasta._sigtac_error


# ---- TablaDatos: barra, sin lectura, activar y borde

def test_la_barra_de_la_tabla_sigue_lo_que_tk_dice_que_se_ve(raiz_tk):
    # Tk avisa la fracción visible de las filas (yscrollcommand); la barra solo aparece si no se ve todo
    tabla = TablaDatos(raiz_tk, [("A", 80)], "Vacía", filas=2)
    assert "_desplazada" in str(tabla._arbol.cget("yscrollcommand"))  # Tk avisa a este método
    assert not tabla.muestra_barra
    for vista, barra in (((0.0, 0.6), True), ((0.4, 1.0), True), ((0.0, 1.0), False)):
        tabla._arbol.yview = lambda v=vista: v  # lo que Tk ve al terminar de acomodar
        tabla._desplazada(*map(str, vista))
        raiz_tk.update_idletasks()  # la decisión espera a que Tk termine
        assert tabla.muestra_barra is barra


def test_sin_lectura_dice_que_no_se_pudo_leer_hasta_la_proxima_carga(raiz_tk):
    from views.componentes.tabla import SIN_LECTURA
    tabla = TablaDatos(raiz_tk, [("A", 80)], "Nadie espera.", filas=2)
    tabla.cargar([(1, ("x",))])
    tabla.sin_lectura()
    assert tabla.cantidad == 0 and tabla._vacio.cget("text") == SIN_LECTURA
    tabla.cargar([])
    assert tabla._vacio.cget("text") == "Nadie espera."
    tabla.cambiar_texto_vacio("Elija un paciente.")
    tabla.sin_lectura()
    tabla.cargar([])
    assert tabla._vacio.cget("text") == "Elija un paciente."  # vuelve al último texto pedido


def test_enter_o_doble_clic_activan_la_fila_elegida(raiz_tk):
    activadas = []
    tabla = TablaDatos(raiz_tk, [("A", 80)], "Vacía", filas=2, al_activar=activadas.append)
    tabla.cargar([(7, ("x",))])
    assert tabla._activada(None) is None and activadas == []  # sin elección no hace nada
    tabla.seleccionar(7)
    assert tabla._activada(None) == "break" and activadas == [7]
    assert "_activada" in tabla._arbol.bind("<Return>") and "_doble_clic" in tabla._arbol.bind("<Double-1>")


def test_el_doble_clic_solo_activa_sobre_la_fila_elegida(raiz_tk, monkeypatch):
    from types import SimpleNamespace
    activadas = []
    tabla = TablaDatos(raiz_tk, [("A", 80)], "Vacía", filas=2, al_activar=activadas.append)
    tabla.cargar([(7, ("x",)), (8, ("y",))])
    tabla.seleccionar(7)
    elegida = tabla._arbol.selection()[0]
    otra = [iid for iid in tabla._arbol.get_children() if iid != elegida][0]
    clic = SimpleNamespace(x=10, y=10)
    for region, fila in (("heading", ""), ("nothing", ""), ("cell", otra)):  # encabezado, vacío, otra fila
        monkeypatch.setattr(tabla._arbol, "identify_region", lambda x, y, r=region: r)
        monkeypatch.setattr(tabla._arbol, "identify_row", lambda y, f=fila: f)
        assert tabla._doble_clic(clic) is None
    monkeypatch.setattr(tabla._arbol, "identify_region", lambda x, y: "cell")
    monkeypatch.setattr(tabla._arbol, "identify_row", lambda y: elegida)
    assert tabla._doble_clic(clic) == "break" and activadas == [7]


def test_sin_al_activar_enter_no_se_asocia(raiz_tk):
    tabla = TablaDatos(raiz_tk, [("A", 80)], "Vacía")
    assert not tabla._arbol.bind("<Return>")


@pytest.mark.parametrize("oscuro, i", [(False, 0), (True, 1)])
def test_el_borde_de_la_tabla_es_el_de_las_tarjetas(raiz_tk, oscuro, i):
    from tkinter import ttk
    from views.componentes.tabla import ESTILO, _configurar_estilo
    _configurar_estilo(raiz_tk, oscuro=oscuro)
    estilo = ttk.Style(raiz_tk)
    # «clam» pintaba un relieve blanco en modo oscuro: los tres tonos del borde son el de las tarjetas
    for opcion in ("bordercolor", "lightcolor", "darkcolor"):
        assert str(estilo.lookup(ESTILO, opcion)) == tema.COLOR_BORDE[i]


# ---- Desplazable

def test_desplazable_muestra_la_barra_solo_si_el_contenido_no_cabe(raiz_tk):
    from views.componentes import Desplazable
    contenido = Desplazable(raiz_tk)
    ctk.CTkFrame(contenido, height=300).pack()
    raiz_tk.update_idletasks()
    alto = contenido.winfo_reqheight()
    assert contenido.ajustar_barra(alto_visible=alto + 50) is False and not contenido.muestra_barra
    assert contenido.ajustar_barra(alto_visible=alto - 50) is True and contenido.muestra_barra
    contenido.mostrar_al_pie()  # no falla aunque la ventana esté oculta
    contenido.destroy()


@pytest.mark.parametrize("actual, y_conservar, y_abajo, esperado", [
    (0, 100, 380, 0),      # el pie ya se ve (380 + 10 = 390 < 400): no se mueve
    (0, 100, 390, 0),      # justo en el borde (390 + 10 = 400): tampoco
    (0, 100, 391, 1),      # un píxel más: baja solo ese píxel
    (0, 100, 450, 60),     # baja lo justo para ver el pie con su margen
    (0, 100, 490, 90),     # justo caben los dos con su aire (90 + 400 = 490 + 10)
    (0, 100, 495, 95),     # con aire no caben: cede el de arriba y se ven los dos (fila en 100, pie en 495)
    (0, 100, 500, 100),    # sin aire caben exacto: lo conservado queda en el borde de arriba
    (0, 100, 600, 100),    # ni así caben: gana lo que se conserva (el pie queda cortado)
    (200, 150, 300, 140),  # lo conservado quedó arriba de lo visible: sube hasta verlo, con su aire
    (0, 5, 30, 0),         # nunca por encima del inicio del contenido
])
def test_desplazamiento_justo(actual, y_conservar, y_abajo, esperado):
    from views.componentes.desplazable import desplazamiento_justo
    assert desplazamiento_justo(actual, 400, y_conservar, y_abajo, margen=10) == esperado


def test_mostrar_hasta_desplaza_lo_justo(raiz_tk, monkeypatch):
    from views.componentes import Desplazable
    from views.componentes import desplazable
    contenido = Desplazable(raiz_tk)
    ctk.CTkFrame(contenido, height=200).pack()
    marco = ctk.CTkFrame(contenido, fg_color="transparent")
    marco.pack()
    lista = ctk.CTkFrame(marco, height=100)
    lista.pack()
    boton = ctk.CTkButton(marco, text="Identificar")
    boton.pack()
    raiz_tk.update_idletasks()
    # El cálculo recibe la altura de cada widget medida desde el inicio del contenido, sumando la de su marco
    assert contenido._y_dentro(lista) == marco.winfo_y() + lista.winfo_y()
    pedidos, movimientos = [], []
    monkeypatch.setattr(desplazable, "desplazamiento_justo", lambda *a: pedidos.append(a) or 120)
    monkeypatch.setattr(contenido._parent_canvas, "yview_moveto", movimientos.append)
    contenido.mostrar_hasta(boton, conservar=lista)
    _, _, y_conservar, y_abajo, _ = pedidos[0]
    assert y_conservar == contenido._y_dentro(lista)
    assert y_abajo == contenido._y_dentro(boton) + boton.winfo_height()
    assert movimientos == [120 / contenido.winfo_reqheight()]
    contenido.mostrar_hasta(boton, conservar=lista, desde=40)  # p. ej. la fila elegida, 40 px dentro de la lista
    assert pedidos[1][2] == contenido._y_dentro(lista) + 40
    contenido.destroy()


def test_y_elegida_sin_fila_elegida_es_el_borde_de_la_tabla(raiz_tk):
    tabla = TablaDatos(raiz_tk, [("Nombre", 100)], "Vacía", filas=3)
    assert tabla.y_elegida() == 0
    tabla.cargar([(1, ["Ana"]), (2, ["Luis"])])
    tabla.seleccionar(2)
    assert tabla.y_elegida() >= 0  # con la ventana oculta Tk no la dibuja: queda el borde de la tabla
    tabla.destroy()


def test_mostrar_hasta_rechaza_un_widget_de_afuera(raiz_tk):
    from views.componentes import Desplazable
    contenido = Desplazable(raiz_tk)
    adentro = ctk.CTkFrame(contenido, height=50)
    adentro.pack()
    afuera = ctk.CTkFrame(raiz_tk)
    with pytest.raises(ValueError):
        contenido.mostrar_hasta(adentro, conservar=afuera)
    afuera.destroy()
    contenido.destroy()


def test_desplazable_avisa_solo_cuando_la_barra_cambia(raiz_tk):
    from views.componentes import Desplazable
    avisos = []
    contenido = Desplazable(raiz_tk, al_cambiar_barra=avisos.append)
    ctk.CTkFrame(contenido, height=300).pack()
    raiz_tk.update_idletasks()
    avisos.clear()  # el primer ajuste real (con la ventana oculta) ya avisó algo: se empieza de cero
    contenido._con_barra = None
    alto = contenido.winfo_reqheight()
    contenido.ajustar_barra(alto_visible=alto + 50)
    contenido.ajustar_barra(alto_visible=alto + 60)  # sigue sin barra: no avisa otra vez
    contenido.ajustar_barra(alto_visible=alto - 50)
    assert avisos == [False, True]
    contenido.destroy()


def test_reacomodar_vuelve_arriba_y_programa_la_revision(raiz_tk):
    from views.componentes import Desplazable
    contenido = Desplazable(raiz_tk)
    ctk.CTkFrame(contenido, height=300).pack()
    contenido._tarea and contenido.after_cancel(contenido._tarea)
    contenido._tarea = None
    contenido.reacomodar()
    assert contenido._tarea is not None and contenido._parent_canvas.yview()[0] == 0
    contenido.destroy()  # cancela la revisión pendiente sin error


# ---- iconos.py

def test_cada_icono_que_se_usa_existe_con_su_licencia():
    from views.componentes import iconos
    from views.app_principal import MODULOS
    assert {m.clave for m in MODULOS} == set(iconos.MENU)  # cada módulo del menú tiene su ícono
    usados = {*iconos.MENU.values(), iconos.LOGO, "bed", "spray", "first-aid-kit", "hourglass", "heartbeat",
              "bed-off", "users", "clock"}
    for nombre in usados:
        assert iconos.ruta(nombre).is_file()
    assert (iconos.CARPETA / "LICENSE-tabler-icons.txt").is_file()


def test_un_icono_desconocido_es_un_error():
    from views.componentes import iconos
    with pytest.raises(ValueError, match="desconocido"):
        iconos.ruta("no-existe")


def test_el_icono_se_pinta_del_color_de_cada_modo(raiz_tk):
    from views.componentes import iconos
    imagen = iconos.icono("bed", tema.COLOR_PRIMARIO, 16)
    assert imagen.cget("size") == (16, 16)
    claro, oscuro = imagen.cget("light_image"), imagen.cget("dark_image")
    # Donde el ícono es opaco, el color es el del modo; la forma (alfa) es la del PNG
    x, y = next((x, y) for x in range(claro.width) for y in range(claro.height) if claro.getpixel((x, y))[3] == 255)
    assert claro.getpixel((x, y))[:3] == tuple(int(tema.COLOR_PRIMARIO[0][i:i + 2], 16) for i in (1, 3, 5))
    assert oscuro.getchannel("A").tobytes() == claro.getchannel("A").tobytes()


def test_tarjeta_kpi_con_icono(raiz_tk):
    tarjeta = TarjetaKPI(raiz_tk, "Camas libres", tema.COLOR_ESTADO_CAMA[EstadoCama.DISPONIBLE], "bed")
    assert tarjeta.icono == "bed"
    assert TarjetaKPI(raiz_tk, "Sin ícono").icono is None
