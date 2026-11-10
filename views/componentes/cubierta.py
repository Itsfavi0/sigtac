"""
Cambio de pantalla en un solo paso.

Tk dibuja cada widget directamente en la ventana, sin una imagen intermedia. Al cambiar de pantalla se ve el fondo
vacío y después los widgets apareciendo por partes: unos 250 ms, casi 1 s en el tablero. Tampoco sirve preparar la
pantalla nueva tapada dentro de la misma ventana, porque Windows no pinta lo que otra parte de la ventana tapa.

Cubierta lo resuelve con una foto. Antes del cambio fotografía el área y la pone encima, en una ventana aparte sin
bordes: debajo de otra ventana, Windows sí pinta. Hecho el cambio, pregunta a Windows cada 15 ms si a algún widget del
área le falta pintarse (GetUpdateRect) y quita la foto cuando ya no: la pantalla nueva aparece completa, de una vez.
Fuera de Windows, con la ventana oculta o si la foto falla, el cambio se hace sin foto, a la vista.
"""
import ctypes
import logging
import sys
import time
import tkinter as tk
from collections.abc import Callable

from PIL import ImageGrab, ImageTk

logger = logging.getLogger(__name__)

EN_WINDOWS = sys.platform == "win32"
DWMWA_TRANSITIONS_FORCEDISABLED = 3  # atributo de ventana de Windows: sin animaciones al mostrarla u ocultarla


class Cubierta:
    """Tapa un área con su propia foto mientras cambia lo que muestra. Una por área."""

    MS_ENTRE_REVISIONES = 15
    REVISIONES_SIN_PINTAR = 2  # seguidas: con una sola, Tk aún podría estar dibujando lo que Windows ya le pidió
    # La foto nunca tapa más que esto, aunque Windows siga pintando. Se mide con el reloj, no contando revisiones:
    # mientras Tk está ocupado (p. ej. precargando pantallas) las revisiones se atrasan
    MS_MAXIMO = 1500
    reloj = staticmethod(time.monotonic)  # segundos; las pruebas lo reemplazan

    def __init__(self, area: tk.Misc):
        self._area = area
        # Las revisiones se programan en la ventana raíz, que vive más que el área: si el área se destruye con una
        # revisión pendiente, la revisión lo nota y termina (programada en el área, fallaría: «invalid command name»)
        self._raiz = area.winfo_toplevel()
        self._ventana = None  # la ventana con la foto, mientras tapa
        self._tarea = None
        self._sin_pintar = 0
        self._limite = 0.0    # hora (del reloj) en que se quita de todos modos

    @property
    def tapando(self) -> bool:
        return self._ventana is not None

    def cambiar(self, cambio: Callable):
        """
        Ejecuta cambio() con el área tapada por su foto y devuelve lo que devuelva. El cambio ocurre ya (lo que se
        lea después de llamar, p. ej. la pantalla actual, es lo nuevo); solo la foto se queda hasta que el área termine
        de pintarse. Un cambio mientras ya tapa usa la misma foto. Si cambio() falla, la foto se quita y el error sube.

        La revisión se programa antes del cambio: si este abre un diálogo (p. ej. «sin conexión»), la foto se quita
        mientras el diálogo espera, y detrás se ve la pantalla nueva.
        """
        if self._ventana is None:
            self._tapar()
        if self._ventana is not None:
            self._sin_pintar = 0
            self._limite = self.reloj() + self.MS_MAXIMO / 1000
            if self._tarea is None:
                self._programar()
        terminado = False
        try:
            resultado = cambio()
            terminado = True
        finally:
            if not terminado:
                self.quitar()
        return resultado

    def quitar(self):
        """Quita la foto y cancela la revisión pendiente. Lo llama también quien destruye el área."""
        if self._tarea is not None:
            self._raiz.after_cancel(self._tarea)
            self._tarea = None
        if self._ventana is not None:
            if self._ventana.winfo_exists():
                self._ventana.destroy()
            self._ventana = None

    def _tapar(self):
        if not EN_WINDOWS or not self._area.winfo_viewable():
            return
        x, y = self._area.winfo_rootx(), self._area.winfo_rooty()
        ancho, alto = self._area.winfo_width(), self._area.winfo_height()
        try:
            # all_screens: si la ventana está en otro monitor, la foto también sale bien
            foto = ImageGrab.grab(bbox=(x, y, x + ancho, y + alto), all_screens=True)
        except OSError as error:
            logger.warning("No se pudo fotografiar la ventana (%s): el cambio de pantalla se verá por partes.",
                           type(error).__name__)
            return
        try:
            self._ventana = self._mostrar_foto(foto, x, y, ancho, alto)
        except (OSError, tk.TclError, ctypes.ArgumentError) as error:
            logger.warning("No se pudo mostrar la foto (%s): el cambio de pantalla se verá por partes.",
                           type(error).__name__)

    def _mostrar_foto(self, foto, x: int, y: int, ancho: int, alto: int) -> tk.Toplevel:
        """
        Una ventana sin bordes, justo encima del área, que solo muestra la foto, ya pintada al volver.

        Tk pintaría la foto recién al atender sus eventos, y para entonces el cambio ya se habría visto: por un
        instante, el área vacía. Atenderlos aquí (update()) correría también clics y temporizadores en medio del cambio
        (otro clic en el menú, la precarga con la sesión ya cerrada). Por eso la foto se pinta directamente con Windows
        (pintar_ya); cuando Tk la vuelva a pintar, pintará la misma imagen.
        """
        ventana = tk.Toplevel(self._area)
        lista = False
        try:
            ventana.withdraw()  # oculta hasta quitarle la animación de aparición
            ventana.overrideredirect(True)  # sin bordes ni barra de título
            ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
            imagen = ImageTk.PhotoImage(foto, master=ventana)
            etiqueta = tk.Label(ventana, image=imagen, borderwidth=0, highlightthickness=0)
            etiqueta.imagen = imagen  # tkinter no guarda la imagen: sin esta referencia se borraría
            # place con medidas fijas: la etiqueta toma su tamaño ya. Con pack lo tomaría al atender el evento de
            # tamaño de la ventana, que update_idletasks no atiende, y medría 1×1 al pintarla
            etiqueta.place(x=0, y=0, width=ancho, height=alto)
            ventana.update_idletasks()  # crea las ventanas de Windows (no atiende clics, teclas ni temporizadores)
            sin_animacion(int(ventana.wm_frame(), 16))
            ventana.deiconify()
            ventana.update_idletasks()  # la muestra
            pintar_ya(etiqueta.winfo_id(), foto)
            lista = True
        finally:
            if not lista:
                ventana.destroy()  # que no quede una ventana suelta encima del área
        return ventana

    def _programar(self):
        """
        La próxima revisión: dentro de 15 ms y, además, cuando Tk esté libre (after_idle: sin eventos en cola). Windows
        da por pintada una zona apenas Tk recibe el aviso, pero Tk la dibuja después, al atender sus eventos; revisar
        antes de eso, con Tk ocupado, daría por terminado un dibujo que no empezó.
        """
        self._tarea = self._raiz.after(self.MS_ENTRE_REVISIONES,
                                       lambda: setattr(self, "_tarea", self._raiz.after_idle(self._revisar)))

    def _revisar(self):
        self._tarea = None
        if not self._area.winfo_exists():  # destruida sin quitar(): la foto se fue con ella
            self.quitar()
            return
        # Lo que Tk dejó para «cuando esté libre» (acomodar, mostrar y dibujar widgets) se hace ya: así lo que falte
        # aparece como «por pintar». No atiende clics ni teclas
        self._area.update_idletasks()
        self._sin_pintar = 0 if falta_pintar(self._area.winfo_id()) else self._sin_pintar + 1
        if self._sin_pintar >= self.REVISIONES_SIN_PINTAR or self.reloj() >= self._limite:
            self.quitar()
        else:
            self._programar()


def sin_animacion(hwnd: int):
    """
    Quita a la ventana de Windows `hwnd` el fundido con que Windows muestra una ventana nueva: con él, el primer
    instante la foto aún es transparente y se ve el área vacía. Solo en Windows.
    """
    from ctypes import wintypes

    dwmapi = ctypes.WinDLL("dwmapi")  # propia: declarar los tipos no afecta a ctypes.windll
    dwmapi.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    desactivar = wintypes.BOOL(True)
    dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_TRANSITIONS_FORCEDISABLED, ctypes.byref(desactivar),
                                 ctypes.sizeof(desactivar))


def pintar_ya(hwnd: int, foto):
    """
    Pinta la foto (imagen de Pillow) en la ventana de Windows `hwnd` en este momento, sin esperar a Tk: copia sus
    píxeles al contexto de dibujo de la ventana con StretchDIBits. Solo en Windows.
    """
    from ctypes import wintypes

    class CabeceraBitmap(ctypes.Structure):  # BITMAPINFOHEADER de Windows
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD)]

    # Bibliotecas propias de esta función: declarar los tipos (los manejadores son de 64 bits) no afecta a ctypes.windll
    user32, gdi32 = ctypes.WinDLL("user32"), ctypes.WinDLL("gdi32")
    user32.GetDC.restype, user32.GetDC.argtypes = wintypes.HDC, [wintypes.HWND]
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    gdi32.StretchDIBits.argtypes = [wintypes.HDC] + [ctypes.c_int] * 8 + [ctypes.c_void_p, ctypes.c_void_p,
                                                                          wintypes.UINT, wintypes.DWORD]
    ancho, alto = foto.size
    pixeles = foto.convert("RGB").tobytes("raw", "BGRX")  # 4 bytes por píxel: filas sin relleno
    # Alto negativo: las filas van de arriba abajo, como en Pillow. 32 bits por píxel, sin compresión (BI_RGB = 0)
    cabecera = CabeceraBitmap(ctypes.sizeof(CabeceraBitmap), ancho, -alto, 1, 32, 0, 0, 0, 0, 0, 0)
    contexto = user32.GetDC(hwnd)
    try:
        gdi32.StretchDIBits(contexto, 0, 0, ancho, alto, 0, 0, ancho, alto, pixeles, ctypes.byref(cabecera),
                            0, 0x00CC0020)  # DIB_RGB_COLORS, SRCCOPY (copia tal cual)
    finally:
        user32.ReleaseDC(hwnd, contexto)


def falta_pintar(hwnd: int) -> bool:
    """
    True si a la ventana de Windows `hwnd` o a alguna de las suyas (cada widget de Tk es una) le queda una parte por
    pintar. GetUpdateRect lo dice sin pintar nada; EnumChildWindows recorre las ventanas hijas y se detiene en
    la primera pendiente. Solo en Windows (fuera de él, ctypes no tiene WinDLL).
    """
    from ctypes import wintypes

    al_recorrer = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32 = ctypes.WinDLL("user32")  # propia: declarar los tipos no afecta a ctypes.windll
    user32.GetUpdateRect.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.BOOL]
    user32.EnumChildWindows.argtypes = [wintypes.HWND, al_recorrer, wintypes.LPARAM]
    if user32.GetUpdateRect(hwnd, None, False):
        return True
    pendientes = []

    # No hace falta saltar las ocultas (p. ej. las pantallas precargadas): Windows no les guarda partes por pintar
    def revisar(hijo, _):
        if user32.GetUpdateRect(hijo, None, False):
            pendientes.append(hijo)
            return False  # detiene el recorrido
        return True

    user32.EnumChildWindows(hwnd, al_recorrer(revisar), 0)
    return bool(pendientes)
