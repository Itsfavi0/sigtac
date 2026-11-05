"""La marca SIGTAC: la misma en el inicio de sesión y en la barra lateral."""
import customtkinter as ctk

from views import tema
from views.componentes.iconos import LOGO, icono


class Marca(ctk.CTkFrame):
    """
    Como en el tablero aprobado: el logo (una línea de pulso en blanco sobre un cuadro azul) y a su lado «SIGTAC» con
    «Emergencia» debajo.
    """

    LADO_LOGO = 36     # el alto de las dos líneas de texto
    ALTO_NOMBRE = 20   # las líneas, ajustadas a su letra (15 y 12 px) para que juntas midan lo que el logo
    ALTO_SERVICIO = 16
    NOMBRE = "SIGTAC"
    SERVICIO = "Emergencia"

    def __init__(self, padre):
        super().__init__(padre, fg_color="transparent")
        logo = ctk.CTkFrame(self, width=self.LADO_LOGO, height=self.LADO_LOGO, corner_radius=tema.RADIO_TARJETA,
                            fg_color=tema.COLOR_PRIMARIO)
        logo.grid(row=0, column=0, rowspan=2, padx=(0, tema.ESPACIO_MEDIO))
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="", image=icono(LOGO, tema.COLOR_TEXTO_SOBRE_PRIMARIO), width=tema.LADO_ICONO,
                     height=tema.LADO_ICONO).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(self, text=self.NOMBRE, font=tema.fuente("subtitulo"), text_color=tema.COLOR_TEXTO, anchor="w",
                     height=self.ALTO_NOMBRE).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(self, text=self.SERVICIO, font=tema.fuente("pequena"), text_color=tema.COLOR_TEXTO_SECUNDARIO,
                     anchor="w", height=self.ALTO_SERVICIO).grid(row=1, column=1, sticky="w")
