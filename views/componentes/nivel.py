"""Nivel de triaje: el cuadro relleno con su número (cola, sugerencia, ficha) y su texto («3 · Amarillo»)."""
import customtkinter as ctk

from models.triaje import COLOR_POR_NIVEL
from views import tema

SIN_TRIAJE = "Sin triaje"
SIN_NIVEL = "–"


def texto_nivel(nivel: int | None) -> str:
    """3 → «3 · Amarillo»; None (aún sin triaje) → «Sin triaje»."""
    if nivel is None:
        return SIN_TRIAJE
    if nivel not in COLOR_POR_NIVEL:
        raise ValueError(f"Nivel de triaje desconocido: {nivel!r}.")
    return f"{nivel} · {COLOR_POR_NIVEL[nivel]}"


class InsigniaNivel(ctk.CTkFrame):
    """
    Cuadro del color del nivel con su número, en el tono del modo activo. Sin triaje es gris con un guion.
    Va siempre acompañado de texto (nombre del paciente, «Nivel 1 · Rojo»...): el número no depende del color.
    """

    def __init__(self, padre, lado: int = 24):
        super().__init__(padre, width=lado, height=lado, corner_radius=tema.RADIO_CONTROL - 1)
        self.pack_propagate(False)
        uso = "fuerte" if lado < 40 else "titulo"
        self._numero = ctk.CTkLabel(self, text="", font=tema.fuente(uso))
        self._numero.pack(expand=True)
        self._nivel = None
        self.mostrar(None)

    def mostrar(self, nivel: int | None):
        texto_nivel(nivel)  # valida el nivel antes de pintar nada
        fondo = tema.COLOR_SIN_DATO if nivel is None else tema.COLOR_NIVEL[nivel]
        self.configure(fg_color=fondo)
        self._numero.configure(text=SIN_NIVEL if nivel is None else str(nivel), text_color=tema.texto_sobre(fondo))
        self._nivel = nivel

    @property
    def nivel(self) -> int | None:
        return self._nivel

    @property
    def texto(self) -> str:
        return self._numero.cget("text")
