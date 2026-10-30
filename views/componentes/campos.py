"""
Campos de un formulario: la etiqueta, la caja donde se escribe, la lista de opciones y la casilla, iguales en todas
las pantallas (documento, contraseña, signos vitales, síntomas...). Cada campo lleva el foco visible de foco.py.
"""
from collections.abc import Callable, Sequence

import customtkinter as ctk

from views import tema
from views.componentes.foco import marcar_error, marcar_foco, marcar_foco_control

LADO_CASILLA = 20  # el cuadro de una casilla: más chico que un campo, alineado con la letra de 13 px
RADIO_CASILLA = 4  # proporcional a su lado, como RADIO_CONTROL lo es a un campo de 36


def etiqueta_campo(padre, texto: str) -> ctk.CTkLabel:
    """El nombre de un campo, encima de él («Documento de identidad», «Contraseña»)."""
    return ctk.CTkLabel(padre, text=texto, font=tema.fuente("etiqueta"), text_color=tema.COLOR_ETIQUETA, anchor="w")


def campo_texto(padre, placeholder: str | None = None, **opciones) -> ctk.CTkEntry:
    """
    Una caja de texto con el estilo del tema y el foco visible. `opciones` pasa lo propio de cada campo
    (p. ej. show="•" para una contraseña, o width).

    Sin placeholder se pasa None, no "": mientras CustomTkinter muestra un placeholder (aunque sea vacío) quita
    el `show`, y la contraseña quedaría sin ocultar hasta que el campo recibe el foco.
    """
    return marcar_foco(ctk.CTkEntry(
        padre, placeholder_text=placeholder, height=tema.ALTO_CONTROL, corner_radius=tema.RADIO_CONTROL,
        border_width=1, font=tema.fuente("normal"), fg_color=tema.COLOR_SUPERFICIE,
        border_color=tema.COLOR_BORDE_CAMPO, text_color=tema.COLOR_TEXTO,
        placeholder_text_color=tema.COLOR_PLACEHOLDER, **opciones))


def lista_opciones(padre, valores: Sequence[str], vacia: bool = False, **opciones) -> ctk.CTkComboBox:
    """
    Una lista de opciones de solo lectura (tipo de documento, sexo, seguro), empezando por la primera; con
    vacia=True empieza sin elegir, para un dato que no debe tomar un valor por omisión (el sexo de un paciente).
    `opciones` pasa lo propio de cada lista (width, command).

    Con el teclado: el foco se ve, ↑/↓ cambian la opción y espacio o Alt+↓ abren la lista. Es de solo lectura, así
    que sin esto no se podía elegir otra opción sin el mouse.
    """
    lista = ctk.CTkComboBox(
        padre, values=list(valores), state="readonly", height=tema.ALTO_CONTROL, corner_radius=tema.RADIO_CONTROL,
        border_width=1, font=tema.fuente("normal"), dropdown_font=tema.fuente("normal"),
        fg_color=tema.COLOR_SUPERFICIE, border_color=tema.COLOR_BORDE_CAMPO, button_color=tema.COLOR_BORDE_CAMPO,
        button_hover_color=tema.COLOR_TEXTO_SECUNDARIO, text_color=tema.COLOR_TEXTO,
        dropdown_fg_color=tema.COLOR_SUPERFICIE, dropdown_hover_color=tema.COLOR_ACTIVO,
        dropdown_text_color=tema.COLOR_TEXTO, **opciones)
    lista.set("" if vacia or not valores else valores[0])
    marcar_foco(lista)
    caja = lista._entry
    caja.bind("<Up>", lambda _e: mover_opcion(lista, -1), add="+")
    caja.bind("<Down>", lambda _e: mover_opcion(lista, 1), add="+")
    for tecla in ("<space>", "<Alt-Down>"):
        caja.bind(tecla, lambda _e: abrir_lista(lista), add="+")
    return lista


def mover_opcion(lista: ctk.CTkComboBox, paso: int) -> str:
    """
    Pasa a la opción anterior (-1) o a la siguiente (+1), sin dar la vuelta, y avisa como si se hubiera elegido con
    el mouse (`command`). Una lista deshabilitada no cambia.
    """
    if lista.cget("state") != "disabled":
        valores = list(lista.cget("values"))
        actual = valores.index(lista.get()) if lista.get() in valores else -1  # vacía: ↓ elige la primera
        nueva = valores[max(0, min(len(valores) - 1, actual + paso))]
        if nueva != lista.get():
            lista.set(nueva)
            comando = lista.cget("command")
            if comando is not None:
                comando(nueva)
    return "break"  # que Tk no haga además lo suyo con la tecla


def abrir_lista(lista: ctk.CTkComboBox) -> str:
    if lista.cget("state") != "disabled":
        lista._open_dropdown_menu()
    return "break"


# ---- Rejilla de campos: cada celda es una etiqueta con su campo debajo

def celda(padre, etiqueta: str, fila: int, columna: int) -> ctk.CTkFrame:
    """
    El lugar de un campo en una rejilla, con su etiqueta. Entre columnas, ESPACIO (como el tipo y el número del
    documento); entre filas, ESPACIO_2 arriba, así la última fila no suma margen al de la tarjeta.
    """
    marco = ctk.CTkFrame(padre, fg_color="transparent")
    marco.grid(row=fila, column=columna, sticky="ew", padx=(0 if columna == 0 else tema.ESPACIO, 0),
               pady=(0 if fila == 0 else tema.ESPACIO_2, 0))
    etiqueta_campo(marco, etiqueta).pack(anchor="w", pady=(0, tema.ESPACIO_MINIMO))
    return marco


def campo_en_rejilla(padre, etiqueta: str, fila: int, columna: int, placeholder: str | None = None) -> ctk.CTkEntry:
    campo = campo_texto(celda(padre, etiqueta, fila, columna), placeholder)
    campo.pack(fill="x")
    return campo


def lista_en_rejilla(padre, etiqueta: str, valores: Sequence[str], fila: int, columna: int) -> ctk.CTkComboBox:
    """Una lista de un dato del paciente: empieza sin elegir (un valor por omisión sería un dato falso)."""
    lista = lista_opciones(celda(padre, etiqueta, fila, columna), valores, vacia=True)
    lista.pack(fill="x")
    return lista


# ---- Leer lo escrito marcando el campo culpable

def leer_campo(campo: ctk.CTkEntry, leer: Callable[[str], object]):
    """Lee el texto de un campo con `leer`; si no se puede, el campo queda marcado y el ValueError sigue su camino."""
    try:
        valor = leer(campo.get())
    except ValueError:
        marcar_error(campo)
        raise
    marcar_error(campo, False)
    return valor


def leer_opcion(lista: ctk.CTkComboBox, valores: dict, mensaje: str):
    """El valor de la opción elegida (`valores`: texto → valor); sin elegir, marca la lista y lanza ValueError."""
    if lista.get() not in valores:
        marcar_error(lista)
        raise ValueError(mensaje)
    marcar_error(lista, False)
    return valores[lista.get()]


def limpiar_al_corregir(*campos):
    """
    Un campo marcado con error pierde el borde rojo en cuanto se corrige: al escribir en él o al elegir otra opción.
    Si no, quedaría rojo sin que nada diga por qué. A una lista le asigna su `command` (no debe tener otro).
    """
    for campo in campos:
        if isinstance(campo, ctk.CTkComboBox):
            campo.configure(command=lambda _valor, lista=campo: sin_error(lista))
        else:
            campo.bind("<KeyRelease>", lambda _e, caja=campo: sin_error(caja), add="+")


def sin_error(campo):
    """Quita el borde de error si el campo lo tiene (y deja el de foco si está enfocado)."""
    if getattr(campo, "_sigtac_error", False):
        marcar_error(campo, False)


def casilla(padre, texto: str, comando: Callable[[], None] | None = None) -> ctk.CTkCheckBox:
    """
    Una casilla para marcar (un síntoma). Se alcanza con Tab y se marca con espacio o Enter; el foco es un borde
    del color del texto, que se ve también sobre la casilla marcada (azul).
    """
    caja = ctk.CTkCheckBox(
        padre, text=texto, command=comando, font=tema.fuente("normal"), text_color=tema.COLOR_TEXTO,
        checkbox_width=LADO_CASILLA, checkbox_height=LADO_CASILLA, corner_radius=RADIO_CASILLA,
        border_width=1, border_color=tema.COLOR_BORDE_CAMPO, fg_color=tema.COLOR_PRIMARIO,
        hover_color=tema.COLOR_PRIMARIO_HOVER, checkmark_color=tema.COLOR_TEXTO_SOBRE_PRIMARIO)
    return marcar_foco_control(caja, caja.toggle, color_foco=tema.COLOR_TEXTO)
