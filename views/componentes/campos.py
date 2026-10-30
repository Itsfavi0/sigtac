"""
Campos de texto: la etiqueta y la caja donde se escribe, iguales en todas las pantallas (documento, contraseña,
signos vitales...). Cada caja lleva el borde de foco de foco.py.
"""
import customtkinter as ctk

from views import tema
from views.componentes.foco import marcar_foco


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
