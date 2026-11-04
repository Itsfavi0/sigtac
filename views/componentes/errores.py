"""
Diálogos de la aplicación: la única forma en que una vista muestra un error, un aviso o una pregunta, o pide dónde
guardar un archivo.

Los controladores no capturan sus errores: llegan a la vista como SigtacError (regla de negocio, BD) o
ValueError (dato inválido), con un mensaje ya escrito para el usuario. La vista los captura y los muestra
aquí, nunca con un `except Exception`.
"""
from pathlib import Path
from tkinter import filedialog, messagebox

from models.excepciones import SigtacError

TITULO = "SIGTAC"
MENSAJE_SIN_TEXTO = "No se pudo completar la operación."


def mostrar_error(ventana, error: SigtacError | ValueError):
    """Muestra el mensaje de un error de la capa de control, encima de `ventana`."""
    messagebox.showerror(TITULO, str(error) or MENSAJE_SIN_TEXTO, parent=ventana)


def mostrar_info(ventana, texto: str):
    """Avisa que una operación terminó bien (p. ej. «Triaje registrado»)."""
    messagebox.showinfo(TITULO, texto, parent=ventana)


def confirmar(ventana, pregunta: str) -> bool:
    """Pide confirmación antes de una operación que no se puede deshacer (p. ej. fusionar pacientes)."""
    return messagebox.askyesno(TITULO, pregunta, parent=ventana)


def pedir_ruta_pdf(ventana, nombre_sugerido: str) -> Path | None:
    """
    El diálogo «Guardar como» de Windows para un PDF, con un nombre ya propuesto. Devuelve la ruta elegida, o None
    si el usuario cancela. No comprueba la ruta: eso lo hace el controlador al exportar.
    """
    ruta = filedialog.asksaveasfilename(parent=ventana, title=TITULO, initialfile=nombre_sugerido,
                                        defaultextension=".pdf", filetypes=[("Documento PDF", "*.pdf")])
    return Path(ruta) if ruta else None
