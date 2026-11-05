"""
Tabla de datos con selección de una fila: colas de espera, pacientes sin identificar...

CustomTkinter no trae una tabla, así que se usa el ttk.Treeview de Tkinter con el estilo del tema
(fuente, alto de fila, colores y borde), dentro de un CTkFrame con su barra de desplazamiento. La barra solo aparece
si las filas no caben.
"""
from collections.abc import Callable, Hashable, Iterable, Sequence
from tkinter import ttk

import customtkinter as ctk

from views import tema

ESTILO = "Sigtac.Treeview"
ALTO_FILA = 4 * tema.ESPACIO  # 32 px
SIN_LECTURA = "No se pudieron leer los datos."


def _configurar_estilo(widget, oscuro: bool | None = None):
    """
    Estilo ttk de todas las tablas (se registra en la ventana; repetirlo no cambia nada).

    ttk no entiende los pares (claro, oscuro) de CustomTkinter ni se escala solo: se le pasan los tonos del modo
    activo, y la fuente y el alto de fila multiplicados por la escala. El tema «clam» de ttk es el que permite
    pintar el encabezado; el predeterminado de Windows lo ignora. «clam» dibuja además un borde con relieve
    (lightcolor/darkcolor) que en modo oscuro quedaba blanco: se pinta con el color de borde de las tarjetas.
    """
    i = int(tema.modo_oscuro() if oscuro is None else oscuro)
    estilo = ttk.Style(widget)
    if estilo.theme_use() != "clam":
        estilo.theme_use("clam")
    fondo, texto, borde = tema.COLOR_SUPERFICIE[i], tema.COLOR_TEXTO[i], tema.COLOR_BORDE[i]
    estilo.configure(ESTILO, font=tema.fuente_ttk("normal", widget), rowheight=round(ALTO_FILA * tema.escala(widget)),
                     background=fondo, fieldbackground=fondo, foreground=texto, borderwidth=1, relief="solid",
                     bordercolor=borde, lightcolor=borde, darkcolor=borde)
    estilo.configure(f"{ESTILO}.Heading", font=tema.fuente_ttk("fuerte", widget), background=fondo,
                     foreground=tema.COLOR_ETIQUETA[i], relief="flat", borderwidth=0,
                     bordercolor=fondo, lightcolor=fondo, darkcolor=fondo)
    estilo.map(f"{ESTILO}.Heading", background=[("active", tema.COLOR_ACTIVO[i])])
    acento = tema.COLOR_PRIMARIO[i]
    estilo.map(ESTILO, background=[("selected", acento)], foreground=[("selected", tema.color_texto_sobre(acento))])


class TablaDatos(ctk.CTkFrame):
    """
    `columnas`: lista de (título, ancho en píxeles). Cada fila se carga como (id, valores): el id no se
    muestra, identifica la fila (p. ej. el id_episodio) y es lo que devuelve `seleccionado()`.
    `al_seleccionar(id)` se llama cuando el usuario elige una fila; `al_activar(id)`, cuando la abre con Enter o
    doble clic (p. ej. para pasar al paso siguiente).
    Con `filas`, la tabla mide eso más el encabezado y las demás filas se desplazan por dentro; sin él, toma el alto
    que le dé su contenedor (p. ej. con fill="both").
    """

    def __init__(self, padre, columnas: Sequence[tuple[str, int]], texto_vacio: str,
                 al_seleccionar: Callable[[Hashable], None] | None = None, filas: int | None = None,
                 al_activar: Callable[[Hashable], None] | None = None):
        if filas is not None and filas < 1:
            raise ValueError("Una tabla muestra al menos una fila.")
        alto = {} if filas is None else {"height": ALTO_FILA * (filas + 1)}
        super().__init__(padre, fg_color="transparent", **alto)
        if filas is not None:
            self.grid_propagate(False)  # el alto no depende de cuántas filas tenga cargadas
        _configurar_estilo(self)
        nombres = [f"c{i}" for i in range(len(columnas))]
        self._arbol = ttk.Treeview(self, columns=nombres, show="headings", selectmode="browse", style=ESTILO)
        for nombre, (titulo, ancho) in zip(nombres, columnas):
            ancho = round(ancho * tema.escala(self))  # como la fuente: ttk no escala solo
            self._arbol.heading(nombre, text=titulo, anchor="w")
            self._arbol.column(nombre, width=ancho, minwidth=ancho, anchor="w")
        self._barra = ctk.CTkScrollbar(self, command=self._arbol.yview)
        self._revision = None  # la revisión de la barra pendiente (after_idle)
        # Tk avisa qué fracción de las filas se ve: con eso se decide la barra, sin estimar altos de fila ni encabezado
        self._arbol.configure(yscrollcommand=self._desplazada)
        self._arbol.grid(row=0, column=0, sticky="nsew")
        self._barra.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # El fondo del texto es el de la tabla, sobre la que se coloca
        self._texto_vacio = texto_vacio
        self._vacio = ctk.CTkLabel(self, text=texto_vacio, font=tema.fuente("normal"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, fg_color=tema.COLOR_SUPERFICIE)
        self._ids = {}  # iid de la fila en el Treeview → id del dato
        self._al_seleccionar = al_seleccionar
        self._al_activar = al_activar
        self._arbol.bind("<<TreeviewSelect>>", self._seleccion_cambiada)
        if al_activar is not None:
            self._arbol.bind("<Return>", self._activada)
            self._arbol.bind("<Double-1>", self._doble_clic)
        self._barra.grid_remove()  # sin filas no hace falta; aparece cuando Tk avisa que no caben
        self.cargar([])

    def cargar(self, filas: Iterable[tuple[Hashable, Sequence]]):
        """Reemplaza las filas. Sin filas, muestra el texto de tabla vacía en lugar de la tabla en blanco."""
        self._arbol.delete(*self._arbol.get_children())
        self._ids.clear()
        for id_fila, valores in filas:
            iid = self._arbol.insert("", "end", values=["" if v is None else v for v in valores])
            self._ids[iid] = id_fila
        self._vacio.configure(text=self._texto_vacio)
        if self._ids:
            self._vacio.place_forget()
        else:
            # Centrado en la zona de filas: medio alto de fila más abajo, para no tapar el encabezado
            self._vacio.place(relx=0.5, rely=0.5, y=round(ALTO_FILA * tema.escala(self) / 2), anchor="center")

    def sin_lectura(self):
        """
        La carga falló: la tabla queda vacía y dice que no se pudieron leer los datos, no que no hay (p. ej. «Nadie
        espera cama» sería falso). La próxima carga vuelve al texto de tabla vacía.
        """
        self.cargar([])
        self._vacio.configure(text=SIN_LECTURA)

    def cambiar_texto_vacio(self, texto: str):
        """Para una tabla cuyo vacío significa cosas distintas («Elija un paciente…» / «No hay camas…»)."""
        self._texto_vacio = texto
        self._vacio.configure(text=texto)

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

    def y_elegida(self) -> int:
        """
        El borde de arriba de la fila elegida, medido desde el de la tabla (en píxeles reales), para desplazar la
        pantalla sin cortarla. Sin fila elegida, o si Tk aún no la dibujó, 0: el borde de la tabla.
        """
        seleccion = self._arbol.selection()
        caja = self._arbol.bbox(seleccion[0]) if seleccion else ""
        return self._arbol.winfo_y() + caja[1] if caja else 0

    @property
    def cantidad(self) -> int:
        return len(self._ids)

    @property
    def muestra_barra(self) -> bool:
        return bool(self._barra.winfo_manager())

    def _desplazada(self, primera: str, ultima: str):
        """
        Lo que Tk avisa al desplazar o cambiar las filas: la fracción visible. La barra solo aparece si no se ve todo
        (como en la matriz de camas); cambiar el ancho de la tabla no cambia cuántas filas caben, así que no hay
        idas y vueltas.
        """
        self._barra.set(primera, ultima)
        if self._revision is None:
            # Se decide cuando Tk termina de acomodar: al ocultar la barra la tabla se ensancha y Tk vuelve a avisar,
            # a veces con una fracción intermedia; lo que vale es la vista final
            self._revision = self.after_idle(self._ajustar_barra)

    def _ajustar_barra(self):
        self._revision = None
        primera, ultima = self._arbol.yview()
        if primera > 0 or ultima < 1:
            self._barra.grid()
        else:
            self._barra.grid_remove()

    def destroy(self):
        if self._revision is not None:
            self.after_cancel(self._revision)
            self._revision = None
        super().destroy()

    def _seleccion_cambiada(self, _evento):
        if self._al_seleccionar is not None:
            self._al_seleccionar(self.seleccionado())

    def _doble_clic(self, evento):
        """Solo un doble clic sobre la fila elegida la activa (no sobre el encabezado ni el espacio vacío)."""
        sobre_fila = self._arbol.identify_region(evento.x, evento.y) in ("cell", "tree")
        if sobre_fila and self._arbol.identify_row(evento.y) in self._arbol.selection():
            return self._activada(evento)
        return None

    def _activada(self, _evento):
        elegido = self.seleccionado()
        if elegido is not None:
            self._al_activar(elegido)
            return "break"
        return None

    def _set_appearance_mode(self, modo):
        # ttk no cambia solo de claro a oscuro: se vuelve a registrar el estilo con los tonos del modo nuevo
        super()._set_appearance_mode(modo)
        _configurar_estilo(self, oscuro=str(modo).lower() == "dark")
