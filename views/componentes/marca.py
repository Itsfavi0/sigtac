"""La marca SIGTAC: la misma en el inicio de sesión y en la barra lateral."""
import customtkinter as ctk

from views import tema


class Marca(ctk.CTkFrame):
    """
    Como en el tablero aprobado: un cuadro de color (el lugar del logo, cuando exista) y a su lado «SIGTAC» con
    «Emergencia» debajo.
    """

    LADO_LOGO = 36     # el alto de las dos líneas de texto
    ALTO_NOMBRE = 20   # las líneas, ajustadas a su letra (15 y 12 px) para que juntas midan lo que el logo
    ALTO_SERVICIO = 16
    NOMBRE = "SIGTAC"
    SERVICIO = "Emergencia"

    def __init__(self, padre):
        super().__init__(padre, fg_color="transparent")
        ctk.CTkFrame(self, width=self.LADO_LOGO, height=self.LADO_LOGO, corner_radius=tema.RADIO_TARJETA,
                     fg_color=tema.COLOR_PRIMARIO).grid(row=0, column=0, rowspan=2, padx=(0, tema.ESPACIO_MEDIO))
        ctk.CTkLabel(self, text=self.NOMBRE, font=tema.fuente("subtitulo"), text_color=tema.COLOR_TEXTO, anchor="w",
                     height=self.ALTO_NOMBRE).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(self, text=self.SERVICIO, font=tema.fuente("pequena"), text_color=tema.COLOR_TEXTO_SECUNDARIO,
                     anchor="w", height=self.ALTO_SERVICIO).grid(row=1, column=1, sticky="w")
