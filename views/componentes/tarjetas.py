"""Tarjetas del tablero: un indicador (KPI) y una casilla del mapa de camas."""
import customtkinter as ctk

from models.cama import Cama
from models.estados import EstadoCama
from views import tema

SIN_VALOR = "—"

# Texto del estado dentro de la casilla. «Fuera de servicio» no cabe en el ancho mínimo; la leyenda del mapa
# lleva el término completo.
TEXTO_CASILLA = {EstadoCama.FUERA_SERVICIO: "F. de servicio"}


class TarjetaKPI(ctk.CTkFrame):
    """
    Un indicador, como en el Figma: arriba un marcador del color del dato y el título; abajo el valor grande y,
    a la derecha, una nota breve («42 % disponible»). El marcador es el lugar del ícono cuando se agreguen.
    """

    def __init__(self, padre, titulo: str, color=None):
        super().__init__(padre, fg_color=tema.COLOR_SUPERFICIE, corner_radius=tema.RADIO_TARJETA, border_width=1,
                         border_color=tema.COLOR_BORDE)
        arriba = ctk.CTkFrame(self, fg_color="transparent")
        arriba.pack(fill="x", padx=tema.ESPACIO_2 - 2, pady=(tema.ESPACIO_MEDIO - 2, 0))
        ctk.CTkFrame(arriba, width=22, height=22, corner_radius=tema.RADIO_CONTROL, fg_color="transparent",
                     border_width=1, border_color=color or tema.COLOR_BORDE_CAMPO).pack(side="left")
        ctk.CTkLabel(arriba, text=titulo, font=tema.fuente("etiqueta"), text_color=tema.COLOR_ETIQUETA).pack(
            side="left", padx=tema.ESPACIO)
        abajo = ctk.CTkFrame(self, fg_color="transparent")
        abajo.pack(fill="x", padx=tema.ESPACIO_2 - 2, pady=(0, tema.ESPACIO))
        self._valor = ctk.CTkLabel(abajo, text=SIN_VALOR, font=tema.fuente("cifra"), text_color=tema.COLOR_TEXTO,
                                   height=30)
        self._valor.pack(side="left")
        self._nota = ctk.CTkLabel(abajo, text="", font=tema.fuente("pequena"),
                                  text_color=tema.COLOR_TEXTO_SECUNDARIO)
        self._nota.pack(side="right", anchor="s")

    def mostrar(self, valor: str | None, nota: str | None = None):
        """El valor ya formateado («15 / 36», «8 min»); None muestra «—» (no hay dato)."""
        self._valor.configure(text=SIN_VALOR if valor is None else valor)
        self._nota.configure(text=nota or "")

    @property
    def valor(self) -> str:
        return self._valor.cget("text")

    @property
    def nota(self) -> str:
        return self._nota.cget("text")


class TarjetaCama(ctk.CTkFrame):
    """
    Una casilla del mapa: el código y el estado escritos, con el borde del color del estado (como en el Figma).
    Una cama fuera de servicio lleva el código tachado. El ancho lo decide la matriz que la contiene.
    """

    ALTO = 40

    def __init__(self, padre, cama: Cama):
        super().__init__(padre, height=self.ALTO, corner_radius=tema.RADIO_CONTROL, fg_color=tema.COLOR_CASILLA,
                         border_width=1, border_color=tema.COLOR_ESTADO_CAMA[cama.estado])
        self.pack_propagate(False)
        self._cama = cama
        fuera = cama.estado == EstadoCama.FUERA_SERVICIO
        ctk.CTkLabel(self, text=cama.codigo, font=tema.fuente("codigo", tachada=fuera), text_color=tema.COLOR_TEXTO,
                     height=16).pack(anchor="w", padx=tema.ESPACIO + 1, pady=(3, 0))
        ctk.CTkLabel(self, text=self.texto_estado(cama.estado), font=tema.fuente("pequena"),
                     text_color=tema.COLOR_TEXTO_SECUNDARIO, height=15).pack(anchor="w", padx=tema.ESPACIO + 1)

    @staticmethod
    def texto_estado(estado: EstadoCama) -> str:
        """«Disponible», «En limpieza»... con la forma corta donde el término completo no cabe."""
        return TEXTO_CASILLA.get(estado, estado.value.capitalize())

    @property
    def cama(self) -> Cama:
        return self._cama
