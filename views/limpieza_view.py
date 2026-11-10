"""
Limpieza: las camas dadas de alta que esperan limpieza, de la más antigua a la más reciente. El personal de limpieza
confirma cada una cuando la deja lista, y la cama vuelve a estar libre (RN-08). Solo ese rol puede hacerlo: al dar de
alta, la cama no queda libre sin esta confirmación (RN-07).

Como Mantenimiento en Gestión de camas: arriba, un resumen (cuántas esperan y cuánto la más antigua); a la izquierda
las camas como casillas, con su tipo; a la derecha la cama elegida y la confirmación, que se hace solo con el botón.

La lista se lee al abrir, al volver a la pantalla y después de cada confirmación, porque otra PC pudo confirmar la
misma cama.
"""
import logging
from datetime import datetime

import customtkinter as ctk

from models.estados import EstadoCama
from models.excepciones import SigtacError
from views import formato, tema
from views.componentes import (BotonPrimario, Desplazable, ListaSeleccion, Tarjeta, TarjetaCama, avisar_exito,
                               aviso_columna, dos_columnas, etiqueta_campo, etiqueta_resumen, fila_acciones,
                               mostrar_error)

logger = logging.getLogger(__name__)

NADA_POR_LIMPIAR = "No hay camas por limpiar."
ELIJA_CAMA = "Elija una cama: al confirmar su limpieza, vuelve a estar disponible."
TEXTO_ELEGIR = "Elija una cama de la lista"   # el botón deshabilitado dice por qué no responde


def texto_espera(desde: datetime, ahora: datetime) -> str:
    """Cuánto lleva esperando, en texto corrido: «7 min», «1 h 05 min» (sin el cero que alinea columnas)."""
    return formato.texto_minutos(formato.minutos_desde(desde, ahora), con_cero=False)


def texto_resumen(solicitudes, ahora: datetime) -> tuple[str, str | None]:
    """
    Las etiquetas del resumen: «3 camas por limpiar» y «La más antigua: 45 min». Sin camas, la segunda no va (None):
    la cifra ya lo dice, y la lista también.
    """
    cantidad = "1 cama por limpiar" if len(solicitudes) == 1 else f"{len(solicitudes)} camas por limpiar"
    if not solicitudes:
        return cantidad, None
    return cantidad, f"La más antigua: {texto_espera(min(s.fecha_solicitud for s in solicitudes), ahora)}"


class LimpiezaView(ctk.CTkFrame):
    COLUMNAS_CAMAS = 3   # casillas por fila, como en Gestión de camas
    FILAS_CAMAS = 4      # filas de casillas visibles (más se desplazan dentro de la lista)

    def __init__(self, padre, camas, reloj=datetime.now):
        super().__init__(padre, fg_color="transparent")
        self._camas, self._reloj = camas, reloj
        self._ahora = reloj()
        self._solicitudes = {}   # id_solicitud → SolicitudLimpieza, de las que se muestran
        self._camas_de = {}      # id_solicitud → su Cama (lo que muestra cada casilla)

        # Como las demás pantallas de trabajo: la tarjeta se desplaza en vertical si no cabe (1093×614)
        contenido = Desplazable(self)
        contenido.pack(fill="both", expand=True)
        tarjeta = Tarjeta(contenido, "Camas por limpiar", "De la más antigua a la más reciente")
        tarjeta.pack(fill="x")
        cuerpo = ctk.CTkFrame(tarjeta, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))

        self._resumen = ctk.CTkFrame(cuerpo, fg_color="transparent")
        self._etiquetas_resumen = (
            etiqueta_resumen(self._resumen, tema.COLOR_ESTADO_CAMA[EstadoCama.EN_LIMPIEZA]),
            etiqueta_resumen(self._resumen))
        self._columnas, izquierda, derecha = dos_columnas(cuerpo)
        self._columnas.pack(fill="x")

        etiqueta_campo(izquierda, "Por limpiar").pack(anchor="w", pady=(0, tema.ESPACIO))
        self._lista = ListaSeleccion(
            izquierda, lambda padre_, cama: TarjetaCama(padre_, cama, detalle=type(cama).NOMBRE_CORTO),
            NADA_POR_LIMPIAR, alto_elemento=TarjetaCama.ALTO, columnas=self.COLUMNAS_CAMAS, filas=self.FILAS_CAMAS,
            al_seleccionar=lambda _id: self._cama_elegida(), actualizar=TarjetaCama.mostrar)
        # Sin al_activar: Enter y el doble clic solo eligen. Confirmar la cama equivocada la mostraría disponible
        # estando sucia, y se la podrían asignar al siguiente paciente; se confirma solo con el botón, que la nombra
        self._lista.pack(fill="x")

        self._sin_eleccion = aviso_columna(derecha, ELIJA_CAMA)
        self._detalle = ctk.CTkFrame(derecha, fg_color="transparent")
        self._codigo = ctk.CTkLabel(self._detalle, text="", font=tema.fuente("subtitulo"), text_color=tema.COLOR_TEXTO,
                                    anchor="w")
        self._codigo.pack(anchor="w")
        self._datos = ctk.CTkLabel(self._detalle, text="", font=tema.fuente("pequena"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        self._datos.pack(anchor="w")
        self._desde = ctk.CTkLabel(self._detalle, text="", font=tema.fuente("pequena"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        self._desde.pack(anchor="w")
        self._fila = fila_acciones(derecha)
        self._boton = BotonPrimario(self._fila, TEXTO_ELEGIR, self.confirmar, state="disabled")
        self._boton.pack(side="left")
        self._cargar_datos()

    def _elegida(self):
        """(solicitud, cama) de la casilla elegida, o None."""
        id_solicitud = self._lista.seleccionado()
        if id_solicitud not in self._solicitudes:
            return None
        return self._solicitudes[id_solicitud], self._camas_de[id_solicitud]

    def _cama_elegida(self):
        """A la derecha, la cama elegida y su confirmación; sin elección, qué hacer."""
        elegida = self._elegida()
        if elegida is None:
            self._detalle.pack_forget()
            self._sin_eleccion.pack(anchor="w", before=self._fila)
            self._boton.configure(text=TEXTO_ELEGIR, state="disabled")
            return
        solicitud, cama = elegida
        self._sin_eleccion.pack_forget()
        self._codigo.configure(text=cama.codigo)
        self._datos.configure(text=" · ".join(dict.fromkeys((type(cama).NOMBRE_CORTO, cama.area))))  # sin «UCI · UCI»
        self._desde.configure(text=f"En limpieza desde las {formato.hora(solicitud.fecha_solicitud)} "
                                   f"({texto_espera(solicitud.fecha_solicitud, self._ahora)})")
        self._detalle.pack(fill="x", before=self._fila)
        self._boton.configure(text=f"Confirmar limpieza de {cama.codigo}", state="normal")

    def confirmar(self):
        """La cama elegida quedó limpia: vuelve a estar libre."""
        elegida = self._elegida()
        if elegida is None:
            return
        solicitud, cama = elegida
        try:
            self._camas.confirmar_limpieza(solicitud.id_solicitud)
        except (SigtacError, ValueError) as error:
            mostrar_error(self, error)  # p. ej. otra PC ya la confirmó: se recarga y la lista lo muestra
            self._recargar(conservar=True)
            return
        self._recargar()
        avisar_exito(self, f"Cama {cama.codigo} lista: vuelve a estar disponible.")

    # ---- Datos

    def al_mostrar(self):
        """Al volver a Limpieza: otra PC pudo dar de alta o confirmar camas. Lo elegido sigue si sigue en la lista."""
        self._recargar(conservar=True)

    def _cargar_datos(self):
        """Al abrir. Si la BD falla, un solo aviso; la lista dice que no se pudo leer y no hay resumen."""
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron leer las camas por limpiar (%s).", type(error).__name__)
            mostrar_error(self, error)
            self._lista.sin_lectura()  # no «No hay camas por limpiar»: no se sabe
            self._cama_elegida()
            return
        self._mostrar(*datos)

    def _recargar(self, conservar: bool = False):
        """Vuelve a leer, sin diálogo si falla. Con `conservar`, la cama elegida sigue elegida si sigue en la lista."""
        elegida = self._lista.seleccionado() if conservar else None
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudo actualizar la lista de limpieza (%s).", type(error).__name__)
            return
        self._mostrar(*datos)
        if elegida is not None:
            self._lista.seleccionar(elegida)
            self._cama_elegida()

    def _leer(self):
        """Las solicitudes pendientes y las camas (cada casilla muestra su cama: código, tipo y área)."""
        return self._camas.solicitudes_limpieza(), {c.id_cama: c for c in self._camas.mapa_camas()}

    def _mostrar(self, solicitudes, camas):
        self._ahora = self._reloj()
        self._solicitudes, self._camas_de = {}, {}
        for s in solicitudes:
            cama = camas.get(s.id_cama)
            if cama is None:
                # El mapa solo trae camas activas: una dada de baja mientras esperaba limpieza no se muestra
                logger.warning("Solicitud de limpieza %s sin su cama en el mapa.", s.id_solicitud)
                continue
            self._solicitudes[s.id_solicitud], self._camas_de[s.id_solicitud] = s, cama
        self._lista.cargar(self._camas_de.items())
        # El resumen cuenta las que se muestran: si no, diría «4» con 3 casillas
        cantidad, mas_antigua = texto_resumen(list(self._solicitudes.values()), self._ahora)
        self._etiquetas_resumen[0].configure(text=cantidad)
        segunda = self._etiquetas_resumen[1]
        if mas_antigua is None:
            segunda.master.pack_forget()
        else:
            segunda.configure(text=mas_antigua)
            segunda.master.pack(side="left", padx=(0, tema.ESPACIO))  # como la colocó etiqueta_resumen
        self._resumen.pack(fill="x", pady=(0, tema.ESPACIO_2), before=self._columnas)
        self._cama_elegida()
