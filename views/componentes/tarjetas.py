"""Tarjetas: una sección con título (tablero, triaje), un indicador (KPI) y una casilla del mapa de camas."""
import customtkinter as ctk

from models.cama import Cama
from models.estados import EstadoCama
from views import formato, tema
from views.componentes.iconos import icono as imagen_icono

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
    Un indicador, como en el Figma: arriba un marcador del color del dato, con su ícono, y el título; abajo el valor
    grande y, a la derecha, una nota breve («42 % disponible»). El ícono va del color del marcador.
    """

    def __init__(self, padre, titulo: str, color=None, icono: str | None = None):
        super().__init__(padre, fg_color=tema.COLOR_SUPERFICIE, corner_radius=tema.RADIO_TARJETA, border_width=1,
                         border_color=tema.COLOR_BORDE)
        arriba = ctk.CTkFrame(self, fg_color="transparent")
        arriba.pack(fill="x", padx=tema.ESPACIO_2 - 2, pady=(tema.ESPACIO_MEDIO - 2, 0))
        color = color or tema.COLOR_BORDE_CAMPO
        marcador = ctk.CTkFrame(arriba, width=tema.LADO_MARCADOR_KPI, height=tema.LADO_MARCADOR_KPI,
                                corner_radius=tema.RADIO_CONTROL, fg_color="transparent", border_width=1,
                                border_color=color)
        marcador.pack(side="left")
        marcador.pack_propagate(False)
        self.icono = None
        if icono is not None:
            self.icono = icono
            # Del tamaño del ícono: una etiqueta mide 28 px por omisión y taparía el borde del marcador
            ctk.CTkLabel(marcador, text="", image=imagen_icono(icono, color, tema.LADO_ICONO_KPI),
                         width=tema.LADO_ICONO_KPI, height=tema.LADO_ICONO_KPI).place(relx=0.5, rely=0.5,
                                                                                    anchor="center")
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
    Una casilla del mapa: el código y el estado escritos, sobre un fondo teñido del color del estado y con una franja
    de ese color a la izquierda, para leer el mapa de un vistazo. Una cama fuera de servicio lleva el código tachado.
    El ancho lo decide la matriz que la contiene.
    """

    ALTO = 40
    ANCHO_FRANJA = 4
    X_FRANJA = 3   # dentro del borde, con 2 px de aire
    TEXTO_X = tema.ESPACIO + 5  # después de la franja, con el mismo aire que antes tenía el texto junto al borde

    def __init__(self, padre, cama: Cama):
        super().__init__(padre, height=self.ALTO, corner_radius=tema.RADIO_CONTROL, border_width=tema.GROSOR_BORDE)
        self.pack_propagate(False)
        self._cama = None
        self._franja = ctk.CTkFrame(self, width=self.ANCHO_FRANJA, corner_radius=self.ANCHO_FRANJA // 2)
        self._franja.place(x=self.X_FRANJA, rely=0.15, relheight=0.7)
        self._codigo = ctk.CTkLabel(self, text="", font=tema.fuente("codigo"), text_color=tema.COLOR_TEXTO, height=16)
        self._codigo.pack(anchor="w", padx=self.TEXTO_X, pady=(3, 0))
        self._estado = ctk.CTkLabel(self, text="", font=tema.fuente("pequena"), text_color=tema.COLOR_TEXTO,
                                    height=15)
        self._estado.pack(anchor="w", padx=self.TEXTO_X)
        self.mostrar(cama)

    def mostrar(self, cama: Cama):
        """
        Pinta la cama (otra, o la misma con otro estado) sin rehacer la casilla: el tablero se relee cada 30 s y así no
        reconstruye las casillas cada vez. Si la cama sigue igual, no repinta nada (cada repintado redibuja la casilla).
        """
        anterior, self._cama = self._cama, cama
        if anterior is not None and (anterior.codigo, anterior.estado) == (cama.codigo, cama.estado):
            return
        self.configure(fg_color=tema.COLOR_FONDO_ESTADO_CAMA[cama.estado],
                       border_color=tema.COLOR_BORDE_ESTADO_CAMA[cama.estado])
        self._franja.configure(fg_color=tema.COLOR_ESTADO_CAMA[cama.estado])
        fuera = cama.estado == EstadoCama.FUERA_SERVICIO
        self._codigo.configure(text=cama.codigo, font=tema.fuente("codigo", tachada=fuera))
        self._estado.configure(text=self.texto_estado(cama.estado))

    @staticmethod
    def texto_estado(estado: EstadoCama) -> str:
        """«Disponible», «En limpieza»... con la forma corta donde el término completo no cabe."""
        return TEXTO_CASILLA.get(estado, formato.texto_estado_cama(estado))

    @property
    def cama(self) -> Cama:
        return self._cama
