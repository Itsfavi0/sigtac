"""
Diálogos de la aplicación: la única forma en que una vista muestra un error, un aviso o una pregunta, o pide dónde
guardar un archivo.

Los controladores no capturan sus errores: llegan a la vista como SigtacError (regla de negocio, BD) o
ValueError (dato inválido), con un mensaje ya escrito para el usuario. La vista los captura y los muestra
aquí, nunca con un `except Exception`.

Lo que salió bien se avisa de dos formas:
- `avisar_exito`, para las operaciones de todos los días (triar, asignar, dar de alta, confirmar una limpieza): un
  aviso que no bloquea, en el encabezado de la ventana principal. Un diálogo en cada una costaría un clic más cada
  vez y taparía el resultado.
- `mostrar_info`, un diálogo, para lo poco frecuente que hay que leer entero (la clave que se entrega en persona, la
  ruta del PDF guardado).
"""
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox

from models.excepciones import SigtacError

TITULO = "SIGTAC"
MENSAJE_SIN_TEXTO = "No se pudo completar la operación."

_avisadores: dict[str, Callable[[str], None]] = {}  # ventana raíz (su nombre en Tk) → cómo avisa sin bloquear


def mostrar_error(ventana, error: SigtacError | ValueError):
    """Muestra el mensaje de un error de la capa de control, encima de `ventana`."""
    messagebox.showerror(TITULO, str(error) or MENSAJE_SIN_TEXTO, parent=ventana)


def mostrar_info(ventana, texto: str):
    """Un diálogo con algo que hay que leer entero (p. ej. «Entréguele la clave en persona»)."""
    messagebox.showinfo(TITULO, texto, parent=ventana)


def registrar_avisos(ventana, avisar: Callable[[str], None]):
    """
    La ventana principal se registra para mostrar los avisos de `avisar_exito` sin diálogo. Se guarda por ventana
    raíz: todas las pantallas de esa ventana avisan ahí.
    """
    _avisadores[str(ventana.winfo_toplevel())] = avisar


def quitar_avisos(ventana, avisar: Callable[[str], None]):
    """
    La ventana principal deja de recibir los avisos (al cerrar sesión). Solo si sigue registrada ella: la nueva pudo
    registrarse antes de que se destruya la anterior.
    """
    clave = str(ventana.winfo_toplevel())
    if _avisadores.get(clave) == avisar:
        del _avisadores[clave]


def avisar_exito(ventana, texto: str):
    """
    Avisa que una operación terminó bien (p. ej. «Triaje registrado»), sin bloquear: en el encabezado de la ventana
    principal. Sin ventana principal registrada (p. ej. una pantalla abierta sola), con un diálogo.
    """
    avisar = _avisadores.get(str(ventana.winfo_toplevel())) if hasattr(ventana, "winfo_toplevel") else None
    if avisar is None:
        mostrar_info(ventana, texto)
    else:
        avisar(texto)


def confirmar(ventana, pregunta: str) -> bool:
    """
    Pide confirmación antes de una operación que no se puede deshacer (p. ej. dar de alta, fusionar pacientes). El
    botón elegido de entrada es «No»: un Enter apurado no la confirma.
    """
    return messagebox.askyesno(TITULO, pregunta, parent=ventana, default=messagebox.NO)


def pedir_ruta_pdf(ventana, nombre_sugerido: str) -> Path | None:
    """
    El diálogo «Guardar como» de Windows para un PDF, con un nombre ya propuesto. Devuelve la ruta elegida, o None
    si el usuario cancela. No comprueba la ruta: eso lo hace el controlador al exportar.
    """
    ruta = filedialog.asksaveasfilename(parent=ventana, title=TITULO, initialfile=nombre_sugerido,
                                        defaultextension=".pdf", filetypes=[("Documento PDF", "*.pdf")])
    return Path(ruta) if ruta else None
