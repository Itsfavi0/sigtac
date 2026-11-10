"""
Botones de la aplicación. El principal es la única acción en azul de una pantalla («Ingresar», «Confirmar nivel 3»);
el secundario, con borde y sin relleno, es para todo lo demás («Cerrar sesión», «Cancelar»).
"""
import customtkinter as ctk

from views import tema
from views.componentes.foco import marcar_foco_control


class BotonPrimario(ctk.CTkButton):
    """
    La acción principal. Deshabilitado se ve gris, con el texto secundario, para que no parezca disponible: quien lo
    presiona sin respuesta creería que la aplicación se colgó. Su texto dice qué falta («Complete los signos
    vitales»).
    """

    def __init__(self, padre, texto: str, comando, **opciones):
        super().__init__(padre, text=texto, command=comando, height=tema.ALTO_CONTROL, corner_radius=tema.RADIO_CONTROL,
                         font=tema.fuente("fuerte"), fg_color=tema.COLOR_PRIMARIO,
                         hover_color=tema.COLOR_PRIMARIO_HOVER, text_color=tema.COLOR_TEXTO_SOBRE_PRIMARIO,
                         text_color_disabled=tema.COLOR_TEXTO_DESHABILITADO, **opciones)
        self._pintar_estado()
        # Un borde azul no se vería sobre el azul: el foco se marca con el color del texto
        marcar_foco_control(self, self.invoke, color_foco=tema.COLOR_TEXTO)

    def configure(self, require_redraw=False, **opciones):
        super().configure(require_redraw=require_redraw, **opciones)
        if "state" in opciones:
            self._pintar_estado()

    def _pintar_estado(self):
        """El relleno según el estado: azul si responde, gris si está deshabilitado."""
        habilitado = self.cget("state") != "disabled"
        super().configure(fg_color=tema.COLOR_PRIMARIO if habilitado else tema.COLOR_FONDO_DESHABILITADO)

    @property
    def deshabilitado(self) -> bool:
        return self.cget("state") == "disabled"


class BotonSecundario(ctk.CTkButton):
    """Una acción secundaria: borde del color de los campos, sin relleno; al pasar el mouse toma el gris activo."""

    def __init__(self, padre, texto: str, comando, **opciones):
        super().__init__(padre, text=texto, command=comando, height=tema.ALTO_CONTROL, corner_radius=tema.RADIO_CONTROL,
                         font=tema.fuente("fuerte"), fg_color="transparent", hover_color=tema.COLOR_ACTIVO,
                         border_width=1, border_color=tema.COLOR_BORDE_CAMPO, text_color=tema.COLOR_TEXTO,
                         text_color_disabled=tema.COLOR_TEXTO_SECUNDARIO, **opciones)
        marcar_foco_control(self, self.invoke)
