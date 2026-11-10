"""
El contenido de una pantalla de trabajo, que se desplaza en vertical si no cabe (1093×614): un CTkScrollableFrame
cuya barra solo aparece cuando hace falta, como la de la matriz de camas y la de las tablas. Con la barra a la vista,
la separa del contenido ESPACIO_MINIMO; sin ella, el contenido llega al borde (no queda un margen vacío).

CustomTkinter no ofrece ocultar la barra ni desplazar desde el código: se usan sus atributos internos
(`_scrollbar`, `_parent_canvas`), aquí y en ningún otro lugar. Si una versión nueva los cambia, se corrige solo esto.
"""
import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from views import tema


def desplazamiento_justo(arriba_actual: float, alto_visible: int, y_conservar: int, y_abajo: int,
                         margen: int) -> float:
    """
    Dónde dejar el borde de arriba de lo visible (en píxeles desde el inicio del contenido) para ver `y_abajo` sin
    perder `y_conservar`, cada uno con `margen` de aire. Se mueve solo lo necesario. Si con el aire no caben los dos,
    cede primero el aire de `y_conservar` (los dos se siguen viendo); si ni así caben, gana `y_conservar`. Nunca
    queda por encima del inicio.
    """
    arriba = arriba_actual
    if y_abajo + margen > arriba + alto_visible:
        arriba = y_abajo + margen - alto_visible
    if y_conservar - margen < arriba:
        arriba = min(y_conservar, max(y_conservar - margen, y_abajo - alto_visible))
    return max(0, arriba)


class Desplazable(ctk.CTkScrollableFrame):
    """`al_cambiar_barra(visible)` avisa cuando la barra aparece o desaparece (p. ej. para ajustar un margen vecino)."""

    def __init__(self, padre, al_cambiar_barra: Callable[[bool], None] | None = None, **opciones):
        super().__init__(padre, fg_color="transparent", corner_radius=0, **opciones)
        self._al_cambiar_barra = al_cambiar_barra
        self._con_barra = None  # aún sin decidir: el primer ajuste avisa
        self._tarea = None
        # El contenido cambia de alto (paneles que se muestran u ocultan) y la ventana de tamaño
        self.bind("<Configure>", lambda _e: self._programar(), add="+")
        self._parent_canvas.bind("<Configure>", lambda _e: self._programar(), add="+")
        # Al pasar con Tab a un campo que quedó bajo el borde, se desplaza hasta él, para no escribir en un campo que
        # no se ve. <<TraverseIn>> lo genera Tk solo al recorrer con Tab (no con un clic, ni al volver a la ventana o
        # cerrar un diálogo, que no deben mover la vista), y llega a la ventana por el widget que recibe el foco
        self._ventana = self.winfo_toplevel()
        self._al_enfocar_id = self._ventana.bind("<<TraverseIn>>", self._al_enfocar, add="+")

    def _programar(self):
        """Una sola revisión cuando Tk termine de acomodar todo, no una por cada evento."""
        if self._tarea is None:
            self._tarea = self.after_idle(self.ajustar_barra)

    def reacomodar(self):
        """
        Para la pantalla que cambia de panel: vuelve arriba y revisa la barra. Si el contenido se acorta por debajo
        de lo que se estaba viendo, Tk no avisa con <Configure> (la parte visible quedó vacía); esto lo resuelve.
        """
        self._parent_canvas.yview_moveto(0)
        self._programar()

    def ajustar_barra(self, alto_visible: int | None = None) -> bool:
        """
        Muestra la barra si el contenido es más alto que lo visible; si cabe, la oculta y vuelve arriba. Devuelve si
        la barra quedó a la vista. `alto_visible` (en píxeles reales) es para las pruebas, sin ventana a la vista.
        """
        self._tarea = None
        visible = self._parent_canvas.winfo_height() if alto_visible is None else alto_visible
        if visible <= 1:
            # Aún sin acomodar (la pantalla se está construyendo): no se decide, lo hará el <Configure> de su tamaño
            # real. Una barra colocada y quitada antes de que la pantalla aparezca queda a la vista igual, sin lugar
            # (Tk la muestra al mostrar la pantalla), encima del borde de la tarjeta
            return self.muestra_barra
        hace_falta = self.winfo_reqheight() > visible + 1
        if hace_falta:
            self._scrollbar.grid(padx=(tema.ESPACIO_MINIMO, 0))  # CTkScrollbar.grid ya lo escala con el zoom
        else:
            self._scrollbar.grid_remove()
            self._parent_canvas.yview_moveto(0)
        if hace_falta != self._con_barra:
            self._con_barra = hace_falta
            if self._al_cambiar_barra is not None:
                self._al_cambiar_barra(hace_falta)
        return hace_falta

    @property
    def muestra_barra(self) -> bool:
        return bool(self._scrollbar.winfo_manager())

    def mostrar_al_pie(self):
        """Desplaza hasta el final: el formulario recién abierto y su botón quedan a la vista."""
        self.update_idletasks()
        self._parent_canvas.yview_moveto(1.0)

    def mostrar_hasta(self, abajo, conservar, desde: int = 0):
        """
        Desplaza lo justo para que el pie de `abajo` (p. ej. un botón) quede a la vista, sin que lo que está `desde`
        píxeles por debajo del borde de arriba de `conservar` (p. ej. la fila elegida de una lista) salga por arriba.
        Si no caben los dos, gana `conservar`. Los dos son widgets dentro de este contenido. Si ya se ven, no se mueve.
        """
        self.update_idletasks()
        alto_total = self.winfo_reqheight()
        if alto_total <= 0:
            return
        y_conservar = self._y_dentro(conservar) + desde
        y_abajo = self._y_dentro(abajo) + abajo.winfo_height()
        margen = round(tema.ESPACIO * tema.escala(self))
        arriba = desplazamiento_justo(self._parent_canvas.canvasy(0), self._parent_canvas.winfo_height(),
                                      y_conservar, y_abajo, margen)
        self._parent_canvas.yview_moveto(arriba / alto_total)

    def _al_enfocar(self, evento):
        """Si el widget que recibió el foco es de este contenido y se ve la pantalla, lo muestra entero."""
        widget = evento.widget
        if not isinstance(widget, tk.Misc) or not self.contiene(widget) or not self.winfo_viewable():
            return
        self.mostrar_hasta(widget, widget)

    def mostrar_foco(self):
        """
        Para el foco que pone el código (p. ej. al primer campo de un formulario que aparece): cuando Tk termine lo
        pendiente, muestra entero el widget que tenga el foco, si es de este contenido. Tab ya lo hace solo.
        """
        def mostrar():
            if not self.winfo_exists():
                return
            widget = self.focus_get()
            if widget is not None and self.contiene(widget) and self.winfo_viewable():
                self.mostrar_hasta(widget, widget)
        # En la ventana, no aquí: si este contenido se destruye antes, la tarea no falla («invalid command name»)
        self._ventana.after_idle(mostrar)

    def contiene(self, widget) -> bool:
        """Si `widget` está dentro de este contenido."""
        while widget is not None:
            if widget is self:
                return True
            widget = widget.master
        return False

    def _y_dentro(self, widget) -> int:
        """La altura de `widget` medida desde el borde de arriba de este contenido (suma la de cada contenedor)."""
        y = 0
        while widget is not None and widget is not self:
            y += widget.winfo_y()
            widget = widget.master
        if widget is None:
            raise ValueError("El widget no está dentro de este contenido.")
        return y

    def destroy(self):
        if self._tarea is not None:
            self.after_cancel(self._tarea)
            self._tarea = None
        if self._al_enfocar_id is not None and self._ventana.winfo_exists():
            self._ventana.unbind("<<TraverseIn>>", self._al_enfocar_id)  # solo el suyo: las demás pantallas siguen
            self._al_enfocar_id = None
        super().destroy()
