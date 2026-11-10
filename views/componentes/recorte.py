"""
Texto que no cabe, terminado en «…». CustomTkinter corta el texto de una etiqueta en seco («Médico de Emergenci»), y
eso se lee como un error; con «…» se entiende que sigue.
"""
from collections.abc import Callable

import customtkinter as ctk

PUNTOS = "…"


def recortar(texto: str, medir: Callable[[str], int], ancho: int) -> str:
    """
    El texto entero si cabe en `ancho` píxeles; si no, lo más largo que quepa con «…» al final (sin espacio antes).
    `medir` da el ancho en píxeles de un texto con la fuente de la etiqueta.
    """
    if medir(texto) <= ancho:
        return texto
    bajo, alto = 0, len(texto)  # busca el prefijo más largo que cabe con los puntos
    while bajo < alto:
        medio = (bajo + alto + 1) // 2
        if medir(texto[:medio].rstrip() + PUNTOS) <= ancho:
            bajo = medio
        else:
            alto = medio - 1
    return texto[:bajo].rstrip() + PUNTOS


class EtiquetaRecortada(ctk.CTkLabel):
    """
    Una etiqueta de una línea que, si su texto no cabe en el ancho que le dan, lo muestra recortado con «…». Se coloca
    ocupando el ancho disponible (pack con fill="x", o grid con sticky="ew"): ese ancho decide cuánto se ve. El texto
    completo se cambia con `mostrar` y se lee con `completo`.
    """

    MARGEN = 6  # el relleno interno de la etiqueta de Tk a los dos lados

    def __init__(self, padre, texto: str = "", **opciones):
        super().__init__(padre, text=texto, **opciones)
        self._completo = texto
        self.bind("<Configure>", lambda _e: self.ajustar(), add="+")

    @property
    def completo(self) -> str:
        return self._completo

    def mostrar(self, texto: str):
        self._completo = texto
        self.ajustar()

    def ajustar(self, ancho: int | None = None):
        """Muestra lo que cabe en `ancho` píxeles (por omisión, el que tiene ahora). Sin ancho aún, el texto entero."""
        ancho = self.winfo_width() - self.MARGEN if ancho is None else ancho
        if ancho <= 1:
            texto = self._completo
        else:
            fuente = self._label.cget("font")
            texto = recortar(self._completo, lambda t: int(self.tk.call("font", "measure", fuente, t)), ancho)
        if texto != self.cget("text"):
            self.configure(text=texto)
