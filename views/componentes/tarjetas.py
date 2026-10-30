"""Tarjetas: una sección con título (tablero, triaje), un indicador (KPI) y una casilla del mapa de camas."""
import customtkinter as ctk

from models.cama import Cama
from models.estados import EstadoCama
from views import tema

SIN_VALOR = "—"

# Texto del estado dentro de la casilla. «Fuera de servicio» no cabe en el ancho mínimo; la leyenda del mapa
# lleva el término completo.
TEXTO_CASILLA = {EstadoCama.FUERA_SERVICIO: "F. de servicio"}


class Tarjeta(ctk.CTkFrame):
    """
    Una sección de una pantalla: el recuadro con su título y una línea que dice qué contiene («Matriz de camas»,
    «1. Paciente»). El contenido se coloca en la misma tarjeta, debajo de la cabecera. A la derecha de la cabecera
    queda lugar para algo propio de la sección (`cabecera`): la leyenda del mapa, un selector.
    """

    ALTO_TITULO = 20      # las dos líneas ajustadas a su letra (15 y 12 px), como la marca
    ALTO_SUBTITULO = 16

    def __init__(self, padre, titulo: str, subtitulo: str, **opciones):
        # `opciones` pasa lo propio de cada tarjeta (p. ej. width para un panel de ancho fijo)
        super().__init__(padre, fg_color=tema.COLOR_SUPERFICIE, corner_radius=tema.RADIO_TARJETA, border_width=1,
                         border_color=tema.COLOR_BORDE, **opciones)
        self.cabecera = ctk.CTkFrame(self, fg_color="transparent")
        self.cabecera.pack(fill="x", padx=tema.ESPACIO_2, pady=(tema.ESPACIO_MEDIO, tema.ESPACIO))
        textos = ctk.CTkFrame(self.cabecera, fg_color="transparent")
        textos.pack(side="left")
        self._titulo = ctk.CTkLabel(textos, text=titulo, font=tema.fuente("subtitulo"), text_color=tema.COLOR_TEXTO,
                                    height=self.ALTO_TITULO)
        self._titulo.pack(anchor="w")
        self._subtitulo = ctk.CTkLabel(textos, text=subtitulo, font=tema.fuente("pequena"),
                                       text_color=tema.COLOR_TEXTO_SECUNDARIO, height=self.ALTO_SUBTITULO)
        self._subtitulo.pack(anchor="w")

    def cambiar_textos(self, titulo: str, subtitulo: str):
        """Para una tarjeta que cambia de contenido (p. ej. «Buscar paciente» / «Pacientes sin identificar»)."""
        self._titulo.configure(text=titulo)
        self._subtitulo.configure(text=subtitulo)

    @property
    def titulo(self) -> str:
        return self._titulo.cget("text")

    @property
    def subtitulo(self) -> str:
        return self._subtitulo.cget("text")


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
