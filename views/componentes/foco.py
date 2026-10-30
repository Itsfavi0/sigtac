"""
Foco visible para los campos, los botones y los interruptores. CustomTkinter no dibuja un anillo de foco: al
entrar a un campo con el teclado o el mouse, su borde pasa a 2 px del color principal, y al salir vuelve a 1 px del
color del campo. Los botones e interruptores, además, no aceptan el foco por sí solos (ver marcar_foco_control).
"""
from views import tema

GROSOR_FOCO = 2
TECLAS_ACTIVAR = ("<Return>", "<space>")


def al_entrar(campo):
    if not getattr(campo, "_sigtac_error", False):  # el foco no tapa un error
        campo.configure(border_width=GROSOR_FOCO, border_color=tema.COLOR_PRIMARIO)


def al_salir(campo):
    if not getattr(campo, "_sigtac_error", False):
        campo.configure(border_width=1, border_color=tema.COLOR_BORDE_CAMPO)


def marcar_foco(campo):
    """Aplica el borde de foco a un CTkEntry, CTkComboBox o CTkTextbox. Devuelve el mismo campo."""
    campo.bind("<FocusIn>", lambda _e: al_entrar(campo), add="+")
    campo.bind("<FocusOut>", lambda _e: al_salir(campo), add="+")
    return campo


def al_entrar_control(control):
    control._sigtac_enfocado = True
    control.configure(border_width=GROSOR_FOCO, border_color=control._sigtac_color_foco)


def al_salir_control(control):
    control._sigtac_enfocado = False
    control.configure(border_width=control._sigtac_borde[0], border_color=control._sigtac_borde[1])


def marcar_foco_control(control, accion, color_foco=None):
    """
    Hace que un botón o un interruptor de CustomTkinter se alcance con Tab y se active con Enter o espacio, como
    pide el brief. Esos widgets son un lienzo que Tk salta al tabular: aquí el lienzo acepta el foco, y al tenerlo
    el borde pasa a 2 px de `color_foco` (el principal; sobre un botón azul, el del texto). Devuelve el control.
    """
    control._sigtac_borde = (control.cget("border_width"), control.cget("border_color"))
    control._sigtac_color_foco = color_foco or tema.COLOR_PRIMARIO
    control._sigtac_enfocado = False
    control._sigtac_accion = accion
    lienzo = control._canvas
    lienzo.configure(takefocus=1)
    lienzo.bind("<FocusIn>", lambda _e: al_entrar_control(control), add="+")
    lienzo.bind("<FocusOut>", lambda _e: al_salir_control(control), add="+")
    for tecla in TECLAS_ACTIVAR:
        lienzo.bind(tecla, lambda _e: activar(control), add="+")
    return control


def activar(control):
    """Lo que hace Enter o espacio sobre un control con foco: su acción (pulsar el botón, mover el interruptor)."""
    control._sigtac_accion()


def fijar_borde(control, ancho: int, color):
    """Cambia el borde normal de un control con foco de teclado; si ahora tiene el foco, se aplica al salir."""
    control._sigtac_borde = (ancho, color)
    if not control._sigtac_enfocado:
        control.configure(border_width=ancho, border_color=color)


def marcar_error(campo, con_error: bool = True):
    """Borde de error (2 px, color de error) en un campo; con False vuelve al borde normal."""
    campo._sigtac_error = con_error
    if con_error:
        campo.configure(border_width=GROSOR_FOCO, border_color=tema.COLOR_ERROR)
    else:
        campo.configure(border_width=1, border_color=tema.COLOR_BORDE_CAMPO)
