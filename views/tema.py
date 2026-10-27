"""
Tema de la interfaz: el único lugar con los colores, las fuentes, los espacios y los tamaños de las vistas.

Una vista nunca escribe un color, un tamaño de letra ni un margen a mano: los toma de aquí. Así todas las
pantallas se ven iguales y un cambio de diseño se hace en un solo archivo. El diseño es el del Figma del equipo,
corregido (docs/diseno/): superficies planas de grises neutros, bordes de 1 px y color solo donde informa.

Cada color es un par (modo claro, modo oscuro). CustomTkinter dibuja el del modo activo, así que cambiar de modo
no exige tocar las vistas.
"""
import logging
from pathlib import Path

import customtkinter as ctk

from utils.colores import ESTADO_CAMA, NIVEL

logger = logging.getLogger(__name__)

# ---- Apariencia general (CustomTkinter)

MODO_APARIENCIA = "light"  # el claro es el predeterminado; el oscuro es opcional (turno de noche)
TEMA_DE_COLOR = "blue"     # tema incluido en CustomTkinter, para los widgets que no reciben color explícito

TITULO_VENTANA = "SIGTAC"
TAMANO_MINIMO = (960, 540)  # ancho, alto: una laptop de 1366×768 al 125 % deja unos 1093×560 útiles

# ---- Espaciado y medidas: todo es múltiplo de 4 píxeles

ESPACIO_MINIMO = 4   # entre un texto y su línea secundaria
ESPACIO = 8          # entre elementos de un mismo grupo (etiqueta y su campo, casillas)
ESPACIO_MEDIO = 12   # entre tarjetas de una fila
ESPACIO_2 = 16       # márgenes interiores de una tarjeta y entre secciones
ESPACIO_3 = 24       # bordes de la pantalla

RADIO_CONTROL = 6    # botones, campos, casillas de cama
RADIO_TARJETA = 8    # tarjetas y paneles
ALTO_CONTROL = 36    # botones y campos
ALTO_NAVEGACION = 40
ANCHO_BARRA = 200
ALTO_ENCABEZADO = 72

# ---- Colores: (claro, oscuro)

COLOR_FONDO = ("#F5F5F7", "#242424")
COLOR_BARRA = ("#FFFFFF", "#202020")
COLOR_SUPERFICIE = ("#FFFFFF", "#2B2B2B")      # tarjetas, paneles, tablas
COLOR_CASILLA = ("#FFFFFF", "#292929")         # fondo de una casilla de cama
COLOR_ACTIVO = ("#F0F0F2", "#2F2F2F")          # ítem activo, hover, píldoras
COLOR_BORDE = ("#D9D9DE", "#444444")           # tarjetas y paneles
COLOR_BORDE_CAMPO = ("#8E8E93", "#757575")     # campos y botones secundarios (3:1 como mínimo)
COLOR_DIVISOR = ("#E6E6EA", "#383838")         # líneas que separan zonas
COLOR_TEXTO = ("#1D1D1F", "#EEEEEE")
COLOR_ETIQUETA = ("#4A4A50", "#A5A5A5")        # etiquetas de campo y títulos de KPI
COLOR_TEXTO_SECUNDARIO = ("#5F6368", "#A3A3A3")
COLOR_PLACEHOLDER = ("#6B6B70", "#959595")
COLOR_PRIMARIO = ("#0A6CDE", "#0A6CDE")        # solo la acción principal y el ítem activo
COLOR_PRIMARIO_HOVER = ("#0A5CC0", "#0B5FC2")
COLOR_TEXTO_SOBRE_PRIMARIO = ("#FFFFFF", "#FFFFFF")
COLOR_ERROR = ("#C5221F", "#FF6B61")
COLOR_EXITO = ("#137333", "#34C759")           # «Actualizado», conexión correcta
COLOR_ALERTA_FONDO = ("#FDECEA", "#302525")    # bloque de una prioridad 1
COLOR_SIN_DATO = ("#E6E6EA", "#3A3A3A")        # etiqueta de nivel cuando aún no hay triaje

COLOR_NIVEL = NIVEL                # nivel de triaje → relleno de su etiqueta
COLOR_ESTADO_CAMA = ESTADO_CAMA    # EstadoCama → borde de la casilla

TEXTO_CLARO = "#FFFFFF"
TEXTO_OSCURO = "#1D1D1F"

# ---- Tipografía: Inter (la del Figma), incluida en views/assets/fonts con su licencia OFL

CARPETA_FUENTES = Path(__file__).resolve().parent / "assets" / "fonts"
ARCHIVOS_INTER = ("Inter-Regular.ttf", "Inter-Medium.ttf", "Inter-SemiBold.ttf", "Inter-Bold.ttf")

# Tk solo distingue normal y negrita; los pesos intermedios son familias aparte («Inter SemiBold»).
# Si Inter no se pudo cargar, cada familia tiene su equivalente de Windows.
_RESPALDO = {"Inter": "Segoe UI", "Inter Medium": "Segoe UI", "Inter SemiBold": "Segoe UI Semibold"}

# uso → (familia, tamaño en píxeles, peso). Nada baja de 12 px.
_FUENTES = {
    "cifra": ("Inter", 24, "bold"),            # el número de un KPI
    "titulo": ("Inter", 20, "bold"),           # título de la pantalla
    "subtitulo": ("Inter SemiBold", 15, "normal"),  # título de una tarjeta o sección
    "fuerte": ("Inter SemiBold", 13, "normal"),     # nombres, botones, ítem activo, título de un área
    "codigo": ("Inter", 13, "bold"),           # código de cama
    "normal": ("Inter", 13, "normal"),         # texto, campos y tablas
    "etiqueta": ("Inter Medium", 12, "normal"),     # etiquetas de campo y de KPI
    "pequena": ("Inter", 12, "normal"),        # textos secundarios, notas, estado de una cama
}

_inter_cargada = None  # se decide la primera vez que se pide una fuente


def cargar_fuentes() -> bool:
    """Registra los archivos de Inter en el proceso (una sola vez). Devuelve False si se usa el respaldo."""
    global _inter_cargada
    if _inter_cargada is None:
        archivos = [CARPETA_FUENTES / nombre for nombre in ARCHIVOS_INTER]
        _inter_cargada = all(a.is_file() and ctk.FontManager.load_font(str(a)) for a in archivos)
        if not _inter_cargada:
            logger.warning("No se pudo cargar la fuente Inter; se usa Segoe UI.")
    return _inter_cargada


def aplicar():
    """Configura CustomTkinter y carga las fuentes. Se llama una vez, desde main.py, antes de crear la ventana."""
    ctk.set_appearance_mode(MODO_APARIENCIA)
    ctk.set_default_color_theme(TEMA_DE_COLOR)
    cargar_fuentes()


def _familia(familia: str) -> str:
    return familia if cargar_fuentes() else _RESPALDO[familia]


def fuente(uso: str, tachada: bool = False) -> ctk.CTkFont:
    """
    Fuente para un uso del texto (ver _FUENTES). `tachada` sirve para una cama fuera de servicio.

    Es una función y no una constante porque Tk solo puede crear fuentes cuando la ventana ya existe.
    """
    try:
        familia, tamano, peso = _FUENTES[uso]
    except KeyError:
        raise ValueError(f"Uso de fuente desconocido: {uso!r}.") from None
    return ctk.CTkFont(family=_familia(familia), size=tamano, weight=peso, overstrike=tachada)


def escala(widget) -> float:
    """Escala de la interfaz (zoom de Windows, p. ej. 1.25 al 125 %) que CustomTkinter aplica a sus widgets."""
    return ctk.ScalingTracker.get_widget_scaling(widget)


def fuente_ttk(uso: str, widget) -> tuple:
    """
    La fuente de un uso para un widget ttk (que CustomTkinter no escala). Va en píxeles (tamaño negativo
    para Tk) y multiplicada por la escala: así una tabla ttk se lee del mismo tamaño que los CTkLabel.
    """
    familia, tamano, peso = _FUENTES[uso]
    return (_familia(familia), -round(tamano * escala(widget)), peso)


def modo_oscuro() -> bool:
    return ctk.get_appearance_mode() == "Dark"


def color_actual(par) -> str:
    """El color de un par (claro, oscuro) para el modo activo; para lo que CustomTkinter no pinta solo (ttk)."""
    return par[1] if modo_oscuro() else par[0]


def color_acento() -> str:
    """El color principal en el modo activo (fila elegida de una tabla ttk)."""
    return color_actual(COLOR_PRIMARIO)


def _luminancia(color_hex: str) -> float:
    """Luminancia relativa de un color #RRGGBB (0 = negro, 1 = blanco), según la fórmula de WCAG."""
    canales = [int(color_hex[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lineales = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lineales[0] + 0.7152 * lineales[1] + 0.0722 * lineales[2]


def _contraste(a: str, b: str) -> float:
    claro, oscuro = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def color_texto_sobre(fondo_hex: str) -> str:
    """
    El color de texto (claro u oscuro) que más contrasta con un fondo. Lo usan las piezas que pintan un
    fondo de color (la etiqueta de un nivel): el amarillo necesita texto oscuro; el rojo, blanco.
    """
    if not isinstance(fondo_hex, str) or len(fondo_hex) != 7 or not fondo_hex.startswith("#"):
        raise ValueError(f"Color no válido (se espera #RRGGBB): {fondo_hex!r}.")
    return max((TEXTO_CLARO, TEXTO_OSCURO), key=lambda texto: _contraste(fondo_hex, texto))


def texto_sobre(par) -> tuple:
    """color_texto_sobre para los dos tonos de un par (claro, oscuro)."""
    return tuple(color_texto_sobre(tono) for tono in par)
