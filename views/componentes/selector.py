"""
Selector de una opción entre pocas, siempre a la vista: «Nuevo / En cola (2)», «Con documento / Sin identificar».

La opción elegida se marca como el ítem activo del menú lateral (fondo activo, borde de 1 px y letra fuerte), así
la aplicación tiene una sola forma de decir «esto es lo elegido». Cada opción es un botón: se alcanza con Tab y se
elige con Enter o espacio.
"""
from collections.abc import Callable, Sequence

import customtkinter as ctk

from views import tema
from views.componentes.foco import fijar_borde, marcar_foco_control


class Selector(ctk.CTkFrame):
    """
    `opciones`: lista de (clave, texto). Empieza en la primera; quitar_eleccion() lo deja sin ninguna marcada.
    `al_cambiar(clave)` se llama cuando el usuario elige otra opción (no al elegirla desde el código con
    avisar=False). Con `repetir`, también cuando vuelve a elegir la que ya estaba (un atajo que se vuelve a pedir).
    """

    def __init__(self, padre, opciones: Sequence[tuple[str, str]], al_cambiar: Callable[[str], None] | None = None,
                 repetir: bool = False):
        super().__init__(padre, fg_color="transparent")
        if not opciones:
            raise ValueError("Un selector necesita al menos una opción.")
        self._al_cambiar = al_cambiar
        self._repetir = repetir
        self._botones = {}
        for i, (clave, texto) in enumerate(opciones):
            boton = ctk.CTkButton(
                self, text=texto, height=tema.ALTO_CONTROL, width=0, corner_radius=tema.RADIO_CONTROL,
                font=tema.fuente("normal"), fg_color="transparent", hover_color=tema.COLOR_ACTIVO,
                text_color=tema.COLOR_TEXTO, border_width=0, border_color=tema.COLOR_BORDE,
                command=lambda clave=clave: self.elegir(clave))
            marcar_foco_control(boton, boton.invoke)
            boton.pack(side="left", padx=(0 if i == 0 else tema.ESPACIO_MINIMO, 0))
            self._botones[clave] = boton
        self._valor = None
        self.elegir(opciones[0][0], avisar=False)

    def elegir(self, clave: str, avisar: bool = True):
        """Marca la opción `clave`. Si cambió (o el selector es de `repetir`) y `avisar`, llama a al_cambiar."""
        if clave not in self._botones:
            raise ValueError(f"Opción desconocida: {clave!r}.")
        cambio = clave != self._valor
        self._valor = clave
        for otra, boton in self._botones.items():
            activo = otra == clave
            boton.configure(fg_color=tema.COLOR_ACTIVO if activo else "transparent",
                            font=tema.fuente("fuerte" if activo else "normal"))
            fijar_borde(boton, 1 if activo else 0, tema.COLOR_BORDE)  # respeta el borde de foco si lo tiene
        if (cambio or self._repetir) and avisar and self._al_cambiar is not None:
            self._al_cambiar(clave)

    def quitar_eleccion(self):
        """
        Ninguna opción queda marcada (p. ej. un período escrito a mano que no es ningún atajo). Elegir después
        cualquiera, también la que estaba, avisa a al_cambiar.
        """
        self._valor = None
        for boton in self._botones.values():
            boton.configure(fg_color="transparent", font=tema.fuente("normal"))
            fijar_borde(boton, 0, tema.COLOR_BORDE)

    def cambiar_texto(self, clave: str, texto: str):
        """Cambia el texto de una opción (p. ej. «En cola (3)» cuando cambia la cola)."""
        self._botones[clave].configure(text=texto)

    def texto(self, clave: str) -> str:
        return self._botones[clave].cget("text")

    @property
    def valor(self) -> str | None:
        """La opción marcada, o None tras quitar_eleccion()."""
        return self._valor

    @property
    def botones(self) -> dict[str, ctk.CTkButton]:
        return dict(self._botones)
