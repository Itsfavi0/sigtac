"""
Una lista de elementos que se eligen con un clic o con el teclado: las filas de una cola, las casillas de cama.

TablaDatos muestra texto en columnas; esta lista muestra lo que dibuje la pantalla (un cuadro de nivel, una casilla de
cama), en una o más columnas. Se usa casi igual: `cargar([(id, dato)])`, `seleccionado()`, `seleccionar(id)`,
`sin_lectura()` y `cambiar_texto_vacio()`. A diferencia de la tabla, `seleccionar` y `cargar` no avisan con
`al_seleccionar`: solo lo hace lo que elige el usuario (un clic, las flechas o `elegir`), y la pantalla llama a sus
manejadores después de recargar.

Con el teclado es un solo lugar de Tab: al tenerlo, la lista muestra el borde de foco; las flechas cambian el elegido
(arriba y abajo, de una fila a otra; a los lados, en una rejilla) y Enter lo activa. Con `filas`, mide eso y lo demás
se desplaza por dentro, con la rueda o al elegir con las flechas.

Dibujar un elemento de CustomTkinter es caro (de 60 a 100 ms una fila o una casilla de cama). Por eso:
- con `actualizar`, una recarga repinta los elementos que siguen en la lista y solo crea los nuevos;
- con `filas`, se crean al instante los que se ven, y los demás de a pocos (LOTE por turno), con la ventana
  respondiendo entre turno y turno. Elegir uno que aún no existe (p. ej. bajando con las flechas) lo crea ya.
"""
import tkinter as tk
from collections.abc import Callable, Hashable, Iterable

import customtkinter as ctk

from views import tema
from views.componentes.foco import GROSOR_FOCO
from views.componentes.tabla import SIN_LECTURA

# Tecla → cuánto se mueve el elegido, en filas (arriba/abajo) o en elementos (a los lados)
TECLAS = {"<Up>": ("fila", -1), "<Down>": ("fila", 1), "<Left>": ("elemento", -1), "<Right>": ("elemento", 1)}


class ListaSeleccion(ctk.CTkFrame):
    """
    `crear(padre, dato)` dibuja un elemento y devuelve su marco (un CTkFrame); `actualizar(elemento, dato)` lo
    repinta con el dato nuevo del mismo id. Al elegir un elemento, la lista le pone el borde del azul de foco y, si se
    da `fondo_elegido`, ese fondo; al dejarlo, le devuelve los suyos. `al_seleccionar(id)` se llama cuando el usuario
    elige uno; `al_activar(id)`, con Enter o doble clic.
    """

    MARGEN = GROSOR_FOCO + 2  # entre el borde de foco de la lista y sus elementos
    LOTE = 2                  # elementos que se crean por turno al completar una lista que no se ve entera

    def __init__(self, padre, crear: Callable[[ctk.CTkFrame, object], ctk.CTkFrame], texto_vacio: str, *,
                 alto_elemento: int, columnas: int = 1, filas: int | None = None, separacion: int = tema.ESPACIO,
                 al_seleccionar: Callable[[Hashable], None] | None = None,
                 al_activar: Callable[[Hashable], None] | None = None, fondo_elegido=None,
                 actualizar: Callable[[ctk.CTkFrame, object], None] | None = None):
        if columnas < 1 or (filas is not None and filas < 1):
            raise ValueError("Una lista muestra al menos una columna y una fila.")
        super().__init__(padre, fg_color="transparent", corner_radius=tema.RADIO_CONTROL, border_width=0,
                         border_color=tema.COLOR_PRIMARIO_GRAFICO)
        self._crear, self._actualizar, self._texto_vacio = crear, actualizar, texto_vacio
        self._alto, self._columnas, self._filas, self._separacion = alto_elemento, columnas, filas, separacion
        self._al_seleccionar, self._al_activar, self._fondo_elegido = al_seleccionar, al_activar, fondo_elegido
        self._ids = []            # en el orden en que se muestran
        self._elementos = {}      # id → marco del elemento
        self._originales = {}     # id → (ancho de borde, color de borde, fondo) del elemento sin elegir
        self._pendientes = []     # (posición, id, dato) de los que aún no se crearon, en orden
        self._tarea_carga = self._tarea_vista = None
        self._elegido = None

        margen = round(self.MARGEN * tema.escala(self))  # el lienzo es de Tk: no escala solo
        self._lienzo = tk.Canvas(self, highlightthickness=0, borderwidth=0, takefocus=1,
                                 background=tema.color_actual(tema.COLOR_SUPERFICIE))
        # Del alto de un elemento: se estira hasta el de la lista (fill="y"). Con los 200 px que CustomTkinter le da
        # por omisión, al aparecer estiraría la lista a 200 px aunque pidiera 2 filas (88 px)
        self._barra = ctk.CTkScrollbar(self, command=self._lienzo.yview, height=alto_elemento)
        # CTkScrollbar redibuja toda la ventana cada vez que se mueve (update_idletasks): la barra se actualiza una
        # sola vez, cuando Tk termina de acomodar, y no con cada cambio
        self._lienzo.configure(yscrollcommand=self._desplazada)
        self._pendiente, self._fraccion = None, ("0", "1")
        self._lienzo.pack(side="left", fill="both", expand=True, padx=margen, pady=margen)
        self._interior = ctk.CTkFrame(self._lienzo, fg_color=tema.COLOR_SUPERFICIE, corner_radius=0)
        self._ventana = self._lienzo.create_window(0, 0, window=self._interior, anchor="nw")
        for columna in range(columnas):
            self._interior.grid_columnconfigure(columna, weight=1, uniform="elemento")
        self._vacio = ctk.CTkLabel(self._interior, text=texto_vacio, font=tema.fuente("normal"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, height=alto_elemento)
        if filas is not None:
            self._lienzo.configure(height=round((filas * alto_elemento + (filas - 1) * separacion) * tema.escala(self)))

        self._lienzo.bind("<Configure>", self._ancho_cambiado)
        self._interior.bind("<Configure>", lambda _e: self._contenido_cambiado(), add="+")
        self._lienzo.bind("<FocusIn>", lambda _e: self.configure(border_width=GROSOR_FOCO))
        self._lienzo.bind("<FocusOut>", lambda _e: self.configure(border_width=0))
        for tecla, (unidad, paso) in TECLAS.items():
            self._lienzo.bind(tecla, lambda _e, u=unidad, p=paso: self._mover(u, p))
        self._lienzo.bind("<Return>", lambda _e: self._activar())
        self._lienzo.bind("<MouseWheel>", self._rueda)
        self.cargar([])

    # ---- Datos

    def cargar(self, datos: Iterable[tuple[Hashable, object]], de_fondo: bool = False):
        """
        Reemplaza los elementos, sin elegido. Con `actualizar`, el de un id que ya estaba se repinta en lugar de
        rehacerse. Sin elementos, muestra el texto de lista vacía. Con `de_fondo` (una lista que no se ve, p. ej. en
        otra pestaña), todos los nuevos se crean de a pocos, ninguno al instante.
        """
        if self._tarea_carga is not None:
            self.after_cancel(self._tarea_carga)
            self._tarea_carga = None
        if self._elegido is not None:
            self._desmarcar(self._elegido)
        datos = list(datos)
        anteriores, self._elementos, self._originales = self._elementos, {}, {}
        self._ids, self._pendientes, self._elegido = [id_dato for id_dato, _ in datos], [], None
        visibles = 0 if de_fondo else len(datos) if self._filas is None else self._filas * self._columnas
        for posicion, (id_dato, dato) in enumerate(datos):
            elemento = anteriores.pop(id_dato, None) if self._actualizar is not None else None
            if elemento is not None:
                self._actualizar(elemento, dato)
                self._colocar(posicion, id_dato, elemento)
            elif posicion < visibles:
                self._colocar(posicion, id_dato, self._nuevo(id_dato, dato))
            else:
                self._pendientes.append((posicion, id_dato, dato))
        for sobrante in anteriores.values():
            sobrante.destroy()
        if self._pendientes:
            self._tarea_carga = self.after(1, self._crear_pendientes)
        self._vacio.configure(text=self._texto_vacio)
        if self._ids:
            self._vacio.grid_forget()
        else:
            self._vacio.grid(row=0, column=0, columnspan=self._columnas, sticky="ew")
        self._lienzo.yview_moveto(0)

    def sin_lectura(self):
        """La carga falló: la lista queda vacía y dice que no se pudieron leer los datos, no que no hay."""
        self.cargar([])
        self._vacio.configure(text=SIN_LECTURA)

    def cambiar_texto_vacio(self, texto: str):
        """Para una lista cuyo vacío significa cosas distintas («Elija un paciente…» / «No hay camas…»)."""
        self._texto_vacio = texto
        self._vacio.configure(text=texto)

    def seleccionado(self) -> Hashable | None:
        """El id del elemento elegido, o None si no hay ninguno."""
        return self._elegido

    def seleccionar(self, id_dato: Hashable):
        """Elige ese elemento desde el código (p. ej. para mantenerlo al recargar), sin avisar. Si no está, nada."""
        if id_dato in self._ids:
            self._asegurar(id_dato)
            self._marcar(id_dato)

    def elegir(self, id_dato: Hashable):
        """Lo que hace el usuario con un clic o las flechas: elige ese elemento y avisa con `al_seleccionar`."""
        if id_dato in self._ids and id_dato != self._elegido:
            self._asegurar(id_dato)
            self._marcar(id_dato)
            if self._al_seleccionar is not None:
                self._al_seleccionar(id_dato)

    def elemento(self, id_dato: Hashable) -> ctk.CTkFrame:
        self._asegurar(id_dato)
        return self._elementos[id_dato]

    def enfocar(self):
        self._lienzo.focus_set()

    @property
    def cantidad(self) -> int:
        return len(self._ids)

    @property
    def muestra_barra(self) -> bool:
        return bool(self._barra.winfo_manager())

    # ---- Crear los elementos

    def _nuevo(self, id_dato: Hashable, dato) -> ctk.CTkFrame:
        elemento = self._crear(self._interior, dato)
        self._vincular(elemento, id_dato)
        return elemento

    def _margenes_columna(self, columna: int) -> tuple[int, int]:
        """
        Los márgenes (izquierdo, derecho) de un elemento de esa columna: entre dos vecinos suman la separación, en los
        bordes no hay, y todos los elementos quedan del mismo ancho (las celdas son iguales). Si la separación quedara
        entera a la derecha de cada uno, el último sería esa separación más ancho que los demás.
        """
        paso = self._separacion / self._columnas
        izquierdo = columna * paso
        derecho = (self._columnas - 1 - columna) * paso
        return round(izquierdo), round(derecho)

    def _colocar(self, posicion: int, id_dato: Hashable, elemento: ctk.CTkFrame):
        fila, columna = divmod(posicion, self._columnas)
        elemento.grid(row=fila, column=columna, sticky="ew", padx=self._margenes_columna(columna),
                      pady=(0 if fila == 0 else self._separacion, 0))
        self._elementos[id_dato] = elemento
        # Sus colores sin elegir, leídos después de pintarlo (una casilla cambia con el estado de su cama)
        self._originales[id_dato] = (elemento.cget("border_width"), elemento.cget("border_color"),
                                     elemento.cget("fg_color"))

    def _crear_siguiente(self):
        posicion, id_dato, dato = self._pendientes.pop(0)
        self._colocar(posicion, id_dato, self._nuevo(id_dato, dato))

    def _crear_pendientes(self):
        """Un turno: crea LOTE de los que faltan y deja el resto para el siguiente."""
        self._tarea_carga = None
        for _ in range(min(self.LOTE, len(self._pendientes))):
            self._crear_siguiente()
        if self._pendientes:
            self._tarea_carga = self.after(1, self._crear_pendientes)

    def _asegurar(self, id_dato: Hashable):
        """Si ese elemento aún no se creó, crea ya los que faltan hasta él."""
        while id_dato not in self._elementos and self._pendientes:
            self._crear_siguiente()

    # ---- Elegir

    def _marcar(self, id_dato: Hashable):
        anterior, self._elegido = self._elegido, id_dato
        if anterior is not None and anterior in self._elementos:
            self._desmarcar(anterior)
        fondo = {} if self._fondo_elegido is None else {"fg_color": self._fondo_elegido}
        self._elementos[id_dato].configure(border_width=GROSOR_FOCO, border_color=tema.COLOR_PRIMARIO_GRAFICO, **fondo)
        # Cuando Tk termine de ubicar los elementos: antes, sus posiciones pueden ser las viejas (o ninguna)
        if self._tarea_vista is None and self._filas is not None:
            self._tarea_vista = self.after_idle(self._mostrar_elegido)

    def _desmarcar(self, id_dato: Hashable):
        ancho, color, fondo = self._originales[id_dato]
        self._elementos[id_dato].configure(border_width=ancho, border_color=color, fg_color=fondo)

    def _vincular(self, widget, id_dato: Hashable):
        """Un clic sobre el elemento o cualquier parte suya lo elige y lleva el foco a la lista."""
        widget.bind("<Button-1>", lambda _e: self._clic(id_dato), add="+")
        widget.bind("<Double-Button-1>", lambda _e: self._activar(), add="+")
        widget.bind("<MouseWheel>", self._rueda, add="+")
        if isinstance(widget, (ctk.CTkFrame, ctk.CTkLabel)):
            widget.configure(cursor="hand2")
        for hijo in widget.winfo_children():
            # Los widgets de CustomTkinter ya vinculan sus piezas internas (su lienzo, su texto): no se repite
            if isinstance(hijo, ctk.CTkBaseClass) or not isinstance(widget, ctk.CTkBaseClass):
                self._vincular(hijo, id_dato)

    def _clic(self, id_dato: Hashable):
        self._lienzo.focus_set()
        self.elegir(id_dato)

    def _mover(self, unidad: str, paso: int) -> str:
        if not self._ids:
            return "break"
        if unidad == "elemento" and self._columnas == 1:
            return "break"  # en una sola columna, los lados no mueven
        if self._elegido is None:
            indice = 0
        else:
            salto = paso * (self._columnas if unidad == "fila" else 1)
            indice = max(0, min(len(self._ids) - 1, self._ids.index(self._elegido) + salto))
        self.elegir(self._ids[indice])
        return "break"  # que Tk no haga además lo suyo con la tecla

    def _activar(self) -> str | None:
        if self._elegido is not None and self._al_activar is not None:
            self._al_activar(self._elegido)
            return "break"
        return None

    # ---- Desplazamiento

    def _ancho_cambiado(self, evento):
        self._lienzo.itemconfigure(self._ventana, width=evento.width)

    def _contenido_cambiado(self):
        alto = self._interior.winfo_reqheight()
        self._lienzo.configure(scrollregion=(0, 0, self._lienzo.winfo_width(), alto))
        if self._filas is None:
            self._lienzo.configure(height=alto)
            return
        if alto > self._lienzo.winfo_reqheight() + 1:
            if not self._barra.winfo_manager():
                self._barra.pack(side="right", fill="y", before=self._lienzo)
        elif self._barra.winfo_manager():
            self._barra.pack_forget()
            self._lienzo.yview_moveto(0)

    def _mostrar_elegido(self):
        """Desplaza lo justo para que se vea el elegido (al recorrer con las flechas una lista que no cabe)."""
        self._tarea_vista = None
        if self._elegido not in self._elementos or not self._lienzo.winfo_ismapped():
            return  # una lista oculta (otra pestaña) no tiene alto todavía: se mide al verse
        self._interior.update_idletasks()  # que las posiciones y el alto sean los de ahora
        elemento = self._elementos[self._elegido]
        total = max(1, self._interior.winfo_reqheight())
        self._lienzo.configure(scrollregion=(0, 0, self._lienzo.winfo_width(), total))
        arriba = self._lienzo.yview()[0] * total
        visible = self._lienzo.winfo_height()
        y, alto = elemento.winfo_y(), elemento.winfo_reqheight()
        if y < arriba:
            self._lienzo.yview_moveto(y / total)
        elif y + alto > arriba + visible:
            self._lienzo.yview_moveto((y + alto - visible) / total)

    def _desplazada(self, primera: str, ultima: str):
        self._fraccion = (primera, ultima)
        if self._pendiente is None:
            self._pendiente = self.after_idle(self._mover_barra)

    def _mover_barra(self):
        """Solo si cambió: Tk avisa la misma fracción cada vez que acomoda la ventana, y set la redibuja entera."""
        self._pendiente = None
        fraccion = tuple(float(valor) for valor in self._fraccion)
        if self._barra.winfo_manager() and fraccion != self._barra.get():
            self._barra.set(*fraccion)

    def destroy(self):
        for tarea in (self._pendiente, self._tarea_carga, self._tarea_vista):
            if tarea is not None:
                self.after_cancel(tarea)
        self._pendiente = self._tarea_carga = self._tarea_vista = None
        super().destroy()

    def _rueda(self, evento) -> str | None:
        """La rueda desplaza la lista si no cabe; si cabe, sigue de largo y desplaza la pantalla."""
        if not self.muestra_barra:
            return None
        self._lienzo.yview_scroll(-1 if evento.delta > 0 else 1, "units")
        return "break"

    def _set_appearance_mode(self, modo):
        # El lienzo es de Tk, no de CustomTkinter: su fondo se cambia a mano al pasar de claro a oscuro
        super()._set_appearance_mode(modo)
        self._lienzo.configure(background=tema.COLOR_SUPERFICIE[1 if str(modo).lower() == "dark" else 0])
