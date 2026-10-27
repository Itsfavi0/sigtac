"""
Tabla de datos con selección de una fila: colas de espera, pacientes sin identificar...

CustomTkinter no trae una tabla, así que se usa el ttk.Treeview de Tkinter con el estilo del tema
(fuente, alto de fila y color de selección), dentro de un CTkFrame con su barra de desplazamiento.
"""
from collections.abc import Callable, Hashable, Iterable, Sequence
from tkinter import ttk

import customtkinter as ctk

from views import tema

ESTILO = "Sigtac.Treeview"
ALTO_FILA = 4 * tema.ESPACIO  # 32 px


def _configurar_estilo(widget, oscuro: bool | None = None):
    """
    Estilo ttk de todas las tablas (se registra en la ventana; repetirlo no cambia nada).

    ttk no entiende los pares (claro, oscuro) de CustomTkinter ni se escala solo: se le pasan los tonos del modo
    activo, y la fuente y el alto de fila multiplicados por la escala. El tema «clam» de ttk es el que permite
    pintar el encabezado; el predeterminado de Windows lo ignora.
    """
    i = int(tema.modo_oscuro() if oscuro is None else oscuro)
    estilo = ttk.Style(widget)
    if estilo.theme_use() != "clam":
        estilo.theme_use("clam")
    fondo, texto = tema.COLOR_SUPERFICIE[i], tema.COLOR_TEXTO[i]
    estilo.configure(ESTILO, font=tema.fuente_ttk("normal", widget), rowheight=round(ALTO_FILA * tema.escala(widget)),
                     background=fondo, fieldbackground=fondo, foreground=texto, borderwidth=0, relief="flat")
    estilo.configure(f"{ESTILO}.Heading", font=tema.fuente_ttk("fuerte", widget), background=fondo,
                     foreground=tema.COLOR_ETIQUETA[i], relief="flat", borderwidth=0)
    estilo.map(f"{ESTILO}.Heading", background=[("active", tema.COLOR_ACTIVO[i])])
    acento = tema.COLOR_PRIMARIO[i]
    estilo.map(ESTILO, background=[("selected", acento)], foreground=[("selected", tema.color_texto_sobre(acento))])


class TablaDatos(ctk.CTkFrame):
    """
    `columnas`: lista de (título, ancho en píxeles). Cada fila se carga como (id, valores): el id no se
    muestra, identifica la fila (p. ej. el id_episodio) y es lo que devuelve `seleccionado()`.
    `al_seleccionar(id)` se llama cuando el usuario elige una fila.
    """

    def __init__(self, padre, columnas: Sequence[tuple[str, int]], texto_vacio: str,
                 al_seleccionar: Callable[[Hashable], None] | None = None):
        super().__init__(padre, fg_color="transparent")
        _configurar_estilo(self)
        nombres = [f"c{i}" for i in range(len(columnas))]
        self._arbol = ttk.Treeview(self, columns=nombres, show="headings", selectmode="browse", style=ESTILO)
        for nombre, (titulo, ancho) in zip(nombres, columnas):
            ancho = round(ancho * tema.escala(self))  # como la fuente: ttk no escala solo
            self._arbol.heading(nombre, text=titulo, anchor="w")
            self._arbol.column(nombre, width=ancho, minwidth=ancho, anchor="w")
        barra = ctk.CTkScrollbar(self, command=self._arbol.yview)
        self._arbol.configure(yscrollcommand=barra.set)
        self._arbol.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # El fondo del texto es el de la tabla, sobre la que se coloca
        self._vacio = ctk.CTkLabel(self, text=texto_vacio, font=tema.fuente("normal"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, fg_color=tema.COLOR_SUPERFICIE)
        self._ids = {}  # iid de la fila en el Treeview → id del dato
        self._al_seleccionar = al_seleccionar
        self._arbol.bind("<<TreeviewSelect>>", self._seleccion_cambiada)
        self.cargar([])

    def cargar(self, filas: Iterable[tuple[Hashable, Sequence]]):
        """Reemplaza las filas. Sin filas, muestra el texto de tabla vacía en lugar de la tabla en blanco."""
        self._arbol.delete(*self._arbol.get_children())
        self._ids.clear()
        for id_fila, valores in filas:
            iid = self._arbol.insert("", "end", values=["" if v is None else v for v in valores])
            self._ids[iid] = id_fila
        if self._ids:
            self._vacio.place_forget()
        else:
            # Centrado en la zona de filas: medio alto de fila más abajo, para no tapar el encabezado
            self._vacio.place(relx=0.5, rely=0.5, y=round(ALTO_FILA * tema.escala(self) / 2), anchor="center")

    def seleccionado(self) -> Hashable | None:
        """El id de la fila elegida, o None si no hay ninguna."""
        seleccion = self._arbol.selection()
        return self._ids[seleccion[0]] if seleccion else None

    def seleccionar(self, id_fila: Hashable):
        """Elige la fila con ese id (p. ej. para mantener la selección al recargar). Si no está, no hace nada."""
        for iid, valor in self._ids.items():
            if valor == id_fila:
                self._arbol.selection_set(iid)
                self._arbol.see(iid)
                return

    @property
    def cantidad(self) -> int:
        return len(self._ids)

    def _seleccion_cambiada(self, _evento):
        if self._al_seleccionar is not None:
            self._al_seleccionar(self.seleccionado())

    def _set_appearance_mode(self, modo):
        # ttk no cambia solo de claro a oscuro: se vuelve a registrar el estilo con los tonos del modo nuevo
        super()._set_appearance_mode(modo)
        _configurar_estilo(self, oscuro=str(modo).lower() == "dark")
