"""
Abre la aplicación con los controladores de demostración (sin MySQL), para ver y revisar las pantallas.

    python -m prototipo.ver                                   # jefe de guardia, modo claro
    python -m prototipo.ver --rol "Personal de Limpieza" --modo oscuro --tamano 1093x614
    python -m prototipo.ver --captura docs/diseno/app.png     # guarda una captura y cierra

Los datos son inventados (prototipo/demo.py).
"""
import argparse
from functools import partial

import customtkinter as ctk

from controllers.auth_controller import AuthController
from models.permisos import Rol
from prototipo.demo import CamasDemo, ReportesDemo, TriajeDemo, sesion_demo
from views import tema
from views.app_principal import AppPrincipal, crear_tablero

# Las mismas pantallas que la aplicación, con los controladores de demostración
PANTALLAS_DEMO = {
    "tablero": partial(crear_tablero, camas=CamasDemo(), reportes=ReportesDemo(), triaje=TriajeDemo()),
}


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    argumentos.add_argument("--rol", default=Rol.JEFE_GUARDIA.value, choices=[r.value for r in Rol])
    argumentos.add_argument("--modo", default="claro", choices=["claro", "oscuro"])
    argumentos.add_argument("--tamano", default="1280x800", help="ancho x alto de la ventana (p. ej. 1093x614)")
    argumentos.add_argument("--captura", help="guarda una captura PNG de la ventana y la cierra")
    opciones = argumentos.parse_args()

    tema.aplicar()
    ctk.set_appearance_mode("dark" if opciones.modo == "oscuro" else "light")
    ventana = ctk.CTk(fg_color=tema.COLOR_FONDO)
    ventana.geometry(f"{opciones.tamano}+0+0")
    ventana.minsize(*tema.TAMANO_MINIMO)
    AppPrincipal(ventana, AuthController(), sesion_demo(Rol(opciones.rol)), al_cerrar=ventana.destroy,
                 pantallas=PANTALLAS_DEMO).pack(fill="both", expand=True)
    if opciones.captura:
        _capturar_y_cerrar(ventana, opciones.captura)
    ventana.mainloop()


def _capturar_y_cerrar(ventana, ruta):
    from PIL import ImageGrab  # Pillow viene con CustomTkinter

    ventana.attributes("-topmost", True)
    ventana.lift()

    def capturar():
        ventana.update()
        caja = (ventana.winfo_rootx(), ventana.winfo_rooty(), ventana.winfo_rootx() + ventana.winfo_width(),
                ventana.winfo_rooty() + ventana.winfo_height())
        ImageGrab.grab(bbox=caja).save(ruta)
        ventana.destroy()

    ventana.after(1500, capturar)


if __name__ == "__main__":
    main()
