"""
Íconos de la interfaz (Tabler Icons 2.47, licencia MIT: views/assets/icons/LICENSE-tabler-icons.txt).

Cada archivo es un PNG negro sobre fondo transparente; aquí se pinta con un color del tema, un tono para el modo
claro y otro para el oscuro, como los demás colores: CustomTkinter muestra el del modo activo. Un ícono siempre va
junto a un texto (el menú, el título de un indicador): no reemplaza la palabra.
"""
from functools import lru_cache
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from views import tema

CARPETA = Path(__file__).resolve().parent.parent / "assets" / "icons"

# Qué ícono lleva cada cosa (el nombre del archivo, sin .png)
MENU = {"tablero": "layout-dashboard", "triaje": "heartbeat", "camas": "bed", "pacientes": "users",
        "limpieza": "spray", "reportes": "chart-bar", "admin": "settings"}
LOGO = "activity"


def ruta(nombre: str) -> Path:
    archivo = CARPETA / f"{nombre}.png"
    if not archivo.is_file():
        raise ValueError(f"Ícono desconocido: {nombre!r}.")
    return archivo


@lru_cache(maxsize=None)
def _tenido(nombre: str, color_hex: str) -> Image.Image:
    """El ícono con su forma (el canal alfa del PNG) rellena de un color."""
    original = Image.open(ruta(nombre)).convert("RGBA")
    pintado = Image.new("RGBA", original.size, color_hex)
    pintado.putalpha(original.getchannel("A"))
    return pintado


@lru_cache(maxsize=None)
def icono(nombre: str, color: tuple[str, str], lado: int = tema.LADO_ICONO) -> ctk.CTkImage:
    """
    El ícono `nombre` del color `color` (claro, oscuro), de `lado` píxeles (CustomTkinter lo escala con el zoom).
    Se crea una vez por combinación: el menú lo pide de nuevo cada vez que cambia el ítem activo.
    """
    return ctk.CTkImage(light_image=_tenido(nombre, color[0]), dark_image=_tenido(nombre, color[1]),
                        size=(lado, lado))
