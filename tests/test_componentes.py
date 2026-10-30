import customtkinter as ctk
import pytest

from models.cama import CamaObservacion
from models.documento import TipoDocumento
from models.estados import EstadoCama
from models.excepciones import ReglaNegocioError
from views import tema
from views.componentes import (BotonPrimario, BotonSecundario, CamposDocumento, InsigniaNivel, Marca, TablaDatos,
                               TarjetaCama, TarjetaKPI, campo_texto, confirmar, errores, etiqueta_campo, marcar_error,
                               marcar_foco, mostrar_error, mostrar_info, texto_nivel)
from views.componentes.documento import ETIQUETAS


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
def test_tarjeta_cama_con_el_borde_de_su_estado(raiz_tk, estado):
    cama = CamaObservacion(7, "OBS-07", "Observación", estado)
    tarjeta = TarjetaCama(raiz_tk, cama)
    assert tuple(tarjeta.cget("border_color")) == tema.COLOR_ESTADO_CAMA[estado]
    assert textos(tarjeta) == ["OBS-07", TarjetaCama.texto_estado(estado)]  # el estado va escrito
    assert tarjeta.cama is cama


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
    assert campo.cget("border_width") == 2 and tuple(campo.cget("border_color")) == tema.COLOR_PRIMARIO
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
    assert tuple(campo.cget("border_color")) == tema.COLOR_PRIMARIO  # el foco se ve


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
    (BotonSecundario, tema.COLOR_PRIMARIO), (BotonPrimario, tema.COLOR_TEXTO),  # sobre el azul, el del texto
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
    assert tuple(campos._tipo.cget("border_color")) == tema.COLOR_PRIMARIO
