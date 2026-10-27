"""
Mapa de camas como en el Figma: una columna por tipo de cama, separadas por líneas finas.

Cada vez que cambia el ancho se busca el menor número de filas en el que caben todas las columnas (`distribuir`),
y cada tipo recibe las columnas de casillas que necesita. Si aun así no cabe en el alto disponible (una laptop de
1366×768 al 125 %), el mapa se desplaza por dentro y muestra su barra; si cabe, la barra no aparece.
"""
import tkinter as tk
from collections.abc import Iterable, Sequence

import customtkinter as ctk

from models.cama import Cama, CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.estados import EstadoCama
from views import tema
from views.componentes.tarjetas import TarjetaCama

ORDEN_TIPOS = (CamaTraumaShock, CamaUCI, CamaObservacion, CamaHospitalizacion)  # de la más crítica a la general
SIN_CAMAS = "No hay camas registradas."


def distribuir(cantidades: Sequence[int], ancho_util: float, ancho_minimo: float,
               separacion: float) -> tuple[int, list[int]]:
    """
    El menor número de filas con el que todas las columnas de casillas caben en `ancho_util`, y cuántas columnas
    recibe cada grupo. Si ni con una columna por grupo caben, devuelve una columna por grupo (el mapa se desplaza).
    """
    if any(n <= 0 for n in cantidades):
        raise ValueError("Cada grupo debe tener al menos una cama.")
    if not cantidades:
        return 0, []
    for filas in range(1, max(cantidades) + 1):
        columnas = [-(-n // filas) for n in cantidades]  # división hacia arriba
        if sum(columnas) * (ancho_minimo + separacion) <= ancho_util:
            return filas, columnas
    return max(cantidades), [1] * len(cantidades)


class MatrizCamas(ctk.CTkFrame):
    ANCHO_MINIMO = 100   # cabe «F. de servicio» y el código a 13 px
    SEPARACION = tema.ESPACIO
    MARGEN = tema.ESPACIO_MEDIO
    ALTO_TITULO = 40     # nombre del tipo y «x de n libres»

    def __init__(self, padre):
        super().__init__(padre, fg_color=tema.COLOR_SUPERFICIE, corner_radius=0)
        self._lienzo = tk.Canvas(self, highlightthickness=0, borderwidth=0,
                                 background=tema.color_actual(tema.COLOR_SUPERFICIE))
        self._barra = ctk.CTkScrollbar(self, command=self._lienzo.yview)
        self._lienzo.configure(yscrollcommand=self._barra.set)
        self._lienzo.pack(side="left", fill="both", expand=True)
        self._interior = ctk.CTkFrame(self._lienzo, fg_color=tema.COLOR_SUPERFICIE, corner_radius=0)
        self._ventana = self._lienzo.create_window(0, 0, window=self._interior, anchor="nw")
        self._vacio = ctk.CTkLabel(self._interior, text=SIN_CAMAS, font=tema.fuente("normal"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO)
        self._grupos = []    # (marco del grupo, grilla, casillas)
        self._lineas = []
        self._clave = None
        self.filas, self.columnas, self.desplazable = 0, [], False
        self._lienzo.bind("<Configure>", self._reacomodar)
        self.bind("<Enter>", lambda _e: self._lienzo.bind_all("<MouseWheel>", self._rueda))
        self.bind("<Leave>", lambda _e: self._lienzo.unbind_all("<MouseWheel>"))
        self.cargar([])

    # ---- datos

    def cargar(self, camas: Iterable[Cama]):
        """Reemplaza las camas del mapa, agrupadas por tipo en el orden de ORDEN_TIPOS."""
        for marco, _, _ in self._grupos:
            marco.destroy()
        for linea in self._lineas:
            linea.destroy()
        self._grupos, self._lineas, self._clave = [], [], None
        camas = list(camas)
        for tipo in ORDEN_TIPOS:
            del_tipo = [c for c in camas if type(c) is tipo]
            if del_tipo:
                self._grupos.append(self._crear_grupo(tipo.NOMBRE_CORTO, del_tipo))
        self._lineas = [ctk.CTkFrame(self._interior, width=1, fg_color=tema.COLOR_DIVISOR, corner_radius=0)
                        for _ in self._grupos[1:]]
        if self._grupos:
            self._vacio.place_forget()
        else:
            self._vacio.place(relx=0.5, y=tema.ESPACIO_3, anchor="n")
        self._reacomodar()

    @property
    def cantidad_camas(self) -> int:
        return sum(len(casillas) for _, _, casillas in self._grupos)

    def _crear_grupo(self, nombre: str, camas: list[Cama]):
        marco = ctk.CTkFrame(self._interior, fg_color="transparent")
        titulo = ctk.CTkFrame(marco, fg_color="transparent", height=self.ALTO_TITULO)
        titulo.pack(fill="x", padx=self.MARGEN, pady=(self.MARGEN - 2, tema.ESPACIO_MINIMO))
        ctk.CTkLabel(titulo, text=nombre, font=tema.fuente("fuerte"), text_color=tema.COLOR_TEXTO,
                     height=17).pack(anchor="w")
        libres = sum(c.estado == EstadoCama.DISPONIBLE for c in camas)
        ctk.CTkLabel(titulo, text=f"{libres} de {len(camas)} libres", font=tema.fuente("pequena"),
                     text_color=tema.COLOR_TEXTO_SECUNDARIO, height=15).pack(anchor="w")
        grilla = ctk.CTkFrame(marco, fg_color="transparent")
        grilla.pack(fill="x", padx=(self.MARGEN, self.MARGEN - self.SEPARACION))
        casillas = [TarjetaCama(grilla, cama) for cama in camas]
        return marco, grilla, casillas

    # ---- disposición

    def _reacomodar(self, _evento=None):
        self.disponer(self._lienzo.winfo_width(), self._lienzo.winfo_height())

    def disponer(self, ancho_real: int, alto_real: int):
        """Reparte las camas para un lienzo de ese tamaño (en píxeles reales) y decide si hace falta desplazar."""
        escala = tema.escala(self)
        if not self._grupos or ancho_real <= 1:
            self._lienzo.itemconfigure(self._ventana, width=max(ancho_real, 1))
            return
        ancho = ancho_real / escala
        cantidades = [len(casillas) for _, _, casillas in self._grupos]
        filas, columnas = distribuir(cantidades, ancho - len(cantidades) * 2 * self.MARGEN,
                                     self.ANCHO_MINIMO, self.SEPARACION)
        clave = (round(ancho), round(alto_real / escala), tuple(columnas))
        if clave == self._clave:
            return
        self._clave = clave
        self.filas, self.columnas = filas, columnas

        # ancho de cada grupo: sus columnas más los márgenes; lo que sobra se reparte según las columnas
        base = [k * (self.ANCHO_MINIMO + self.SEPARACION) + 2 * self.MARGEN for k in columnas]
        sobra = max(0.0, ancho - sum(base))
        anchos = [b + sobra * k / sum(columnas) for b, k in zip(base, columnas)]
        x = 0.0
        for i, ((marco, grilla, casillas), w, k) in enumerate(zip(self._grupos, anchos, columnas)):
            if i:
                self._lineas[i - 1].place(relx=x / ancho, y=0, relheight=1)
            marco.place(relx=x / ancho, y=0, relwidth=w / ancho, relheight=1)
            for col in range(max(columnas) + 1):
                activa = col < k
                grilla.grid_columnconfigure(col, weight=1 if activa else 0, uniform="cama" if activa else "")
            for n, casilla in enumerate(casillas):
                casilla.grid(row=n // k, column=n % k, sticky="ew", padx=(0, self.SEPARACION),
                             pady=(0, self.SEPARACION))
            x += w

        filas_reales = max(-(-n // k) for n, k in zip(cantidades, columnas))
        alto = self.MARGEN + self.ALTO_TITULO + filas_reales * (TarjetaCama.ALTO + self.SEPARACION) + self.MARGEN
        self._interior.configure(height=alto)
        self._lienzo.itemconfigure(self._ventana, width=ancho_real, height=round(alto * escala))
        self._lienzo.configure(scrollregion=(0, 0, ancho_real, round(alto * escala)))
        self._mostrar_barra(alto * escala > alto_real + 1)

    def _mostrar_barra(self, mostrar: bool):
        self.desplazable = mostrar
        if mostrar and not self._barra.winfo_ismapped():
            self._barra.pack(side="right", fill="y", before=self._lienzo)
        elif not mostrar:
            self._barra.pack_forget()
            self._lienzo.yview_moveto(0)

    def _rueda(self, evento):
        if self.desplazable:
            self._lienzo.yview_scroll(-1 if evento.delta > 0 else 1, "units")

    def _set_appearance_mode(self, modo):
        # El lienzo es de Tk, no de CustomTkinter: su fondo se cambia a mano al pasar de claro a oscuro
        super()._set_appearance_mode(modo)
        self._lienzo.configure(background=tema.COLOR_SUPERFICIE[1 if str(modo).lower() == "dark" else 0])
