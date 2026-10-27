"""
Foco visible para los campos. CustomTkinter no dibuja un anillo de foco: al entrar a un campo con el teclado o
el mouse, su borde pasa a 2 px del color principal, y al salir vuelve a 1 px del color del campo.
"""
from views import tema

GROSOR_FOCO = 2


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


def marcar_error(campo, con_error: bool = True):
    """Borde de error (2 px, color de error) en un campo; con False vuelve al borde normal."""
    campo._sigtac_error = con_error
    if con_error:
        campo.configure(border_width=GROSOR_FOCO, border_color=tema.COLOR_ERROR)
    else:
        campo.configure(border_width=1, border_color=tema.COLOR_BORDE_CAMPO)
