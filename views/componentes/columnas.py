"""
Piezas de las pantallas de trabajo que eligen algo de una lista y actúan sobre ello (Gestión de camas, Limpieza):
las dos columnas, las etiquetas del resumen de arriba, el aviso de la columna derecha mientras no hay nada elegido y la
fila de sus botones.
"""
import customtkinter as ctk

from views import tema

ALTO_ETIQUETA = 28   # las etiquetas del resumen
LADO_PUNTO = 8       # el punto de color de una etiqueta del resumen
ANCHO_AVISO = 360    # el aviso de la columna derecha, partido para no pasar de ella


def dos_columnas(padre) -> tuple[ctk.CTkFrame, ctk.CTkFrame, ctk.CTkFrame]:
    """
    Lo que se elige a la izquierda; lo elegido y sus acciones a la derecha, separados por una línea. Devuelve el marco
    (para colocarlo) y las dos columnas.
    """
    marco = ctk.CTkFrame(padre, fg_color="transparent")
    marco.grid_columnconfigure(0, weight=5, uniform="columnas")
    marco.grid_columnconfigure(2, weight=6, uniform="columnas")
    izquierda = ctk.CTkFrame(marco, fg_color="transparent")
    izquierda.grid(row=0, column=0, sticky="nsew")
    ctk.CTkFrame(marco, width=1, fg_color=tema.COLOR_DIVISOR, corner_radius=0).grid(
        row=0, column=1, sticky="ns", padx=tema.ESPACIO_2)
    derecha = ctk.CTkFrame(marco, fg_color="transparent")
    derecha.grid(row=0, column=2, sticky="nsew")
    return marco, izquierda, derecha


def etiqueta_resumen(padre, color=None) -> ctk.CTkLabel:
    """
    Una etiqueta del resumen, gris como las del tablero («Plazo 10 min»), colocada a continuación de las anteriores. Con
    `color`, un punto de ese color delante. Devuelve el texto, que la pantalla llena con `configure(text=...)`.
    """
    marco = ctk.CTkFrame(padre, fg_color=tema.COLOR_ACTIVO, corner_radius=tema.RADIO_CONTROL)
    marco.pack(side="left", padx=(0, tema.ESPACIO))
    if color is not None:
        ctk.CTkFrame(marco, width=LADO_PUNTO, height=LADO_PUNTO, corner_radius=LADO_PUNTO // 2,
                     fg_color=color).pack(side="left", padx=(tema.ESPACIO_MEDIO, 0))
    texto = ctk.CTkLabel(marco, text="", font=tema.fuente("etiqueta"), text_color=tema.COLOR_ETIQUETA,
                         height=ALTO_ETIQUETA)
    texto.pack(side="left", padx=(tema.ESPACIO if color is not None else tema.ESPACIO_MEDIO, tema.ESPACIO_MEDIO))
    return texto


def aviso_columna(padre, texto: str) -> ctk.CTkLabel:
    """Lo que dice la columna derecha mientras no hay nada elegido. Se crea sin colocar: la pantalla decide cuándo."""
    return ctk.CTkLabel(padre, text=texto, font=tema.fuente("normal"), text_color=tema.COLOR_TEXTO_SECUNDARIO,
                        anchor="w", justify="left", wraplength=ANCHO_AVISO)


def fila_acciones(padre, arriba: int = tema.ESPACIO_2) -> ctk.CTkFrame:
    """Una fila para botones, ya colocada, separada `arriba` de lo anterior."""
    fila = ctk.CTkFrame(padre, fg_color="transparent")
    fila.pack(fill="x", pady=(arriba, 0))
    return fila
