"""
Limpieza: las camas dadas de alta que esperan limpieza, de la más antigua a la más reciente. El personal de limpieza
confirma cada una cuando la deja lista, y la cama vuelve a estar libre (RN-08). Solo ese rol puede hacerlo: al dar de
alta, la cama no queda libre sin esta confirmación (RN-07).

La lista se lee al abrir y después de cada confirmación, porque otra PC pudo confirmar la misma cama.
"""
import logging
from datetime import datetime

import customtkinter as ctk

from models.excepciones import SigtacError
from views import formato, tema
from views.componentes import BotonPrimario, Desplazable, TablaDatos, Tarjeta, mostrar_error, mostrar_info

logger = logging.getLogger(__name__)

NADA_POR_LIMPIAR = "No hay camas por limpiar."
TEXTO_ELEGIR = "Elija una cama de la lista"   # el botón deshabilitado dice por qué no responde


class LimpiezaView(ctk.CTkFrame):
    FILAS_LISTA = 8   # filas visibles (más se desplazan dentro de la tabla)
    COLUMNAS = (("Cama", 96), ("Tipo", 144), ("Área", 240), ("Desde", 80), ("Espera", 80))

    def __init__(self, padre, camas, reloj=datetime.now):
        super().__init__(padre, fg_color="transparent")
        self._camas, self._reloj = camas, reloj
        self._solicitudes = {}   # id_solicitud → SolicitudLimpieza

        # Como las demás pantallas de trabajo: la tarjeta se desplaza en vertical si no cabe (1093×614)
        contenido = Desplazable(self)
        contenido.pack(fill="both", expand=True)
        tarjeta = Tarjeta(contenido, "Camas por limpiar", "De la más antigua a la más reciente")
        tarjeta.pack(fill="x")
        cuerpo = ctk.CTkFrame(tarjeta, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))

        self._tabla = TablaDatos(cuerpo, self.COLUMNAS, NADA_POR_LIMPIAR,
                                 al_seleccionar=lambda _id: self._actualizar_boton(), filas=self.FILAS_LISTA)
        self._tabla.pack(fill="x")
        fila = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        self._boton = BotonPrimario(fila, TEXTO_ELEGIR, self.confirmar, state="disabled")
        self._boton.pack(side="left")
        self._cargar_datos()

    def _actualizar_boton(self):
        solicitud = self._solicitudes.get(self._tabla.seleccionado())
        if solicitud is None:
            self._boton.configure(text=TEXTO_ELEGIR, state="disabled")
        else:
            self._boton.configure(text=f"Confirmar limpieza de {solicitud.codigo_cama}", state="normal")

    def confirmar(self):
        """La cama elegida quedó limpia: vuelve a estar libre."""
        solicitud = self._solicitudes.get(self._tabla.seleccionado())
        if solicitud is None:
            return
        try:
            self._camas.confirmar_limpieza(solicitud.id_solicitud)
        except (SigtacError, ValueError) as error:
            mostrar_error(self, error)  # p. ej. otra PC ya la confirmó: se recarga y la lista lo muestra
            self._recargar()
            self._tabla.seleccionar(solicitud.id_solicitud)
            self._actualizar_boton()
            return
        self._recargar()
        mostrar_info(self, f"Cama {solicitud.codigo_cama} lista: vuelve a estar disponible.")

    # ---- Datos

    def al_mostrar(self):
        """Al volver a Limpieza: otra PC pudo dar de alta o confirmar camas."""
        self._recargar()

    def _cargar_datos(self):
        """Al abrir. Si la BD falla, un solo aviso y la lista vacía."""
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron leer las camas por limpiar (%s).", type(error).__name__)
            mostrar_error(self, error)
            self._mostrar([], {})
            self._tabla.sin_lectura()  # no «No hay camas por limpiar»: no se sabe
            return
        self._mostrar(*datos)

    def _recargar(self):
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudo actualizar la lista de limpieza (%s).", type(error).__name__)
            return
        self._mostrar(*datos)

    def _leer(self):
        """Las solicitudes pendientes y las camas (para decir de qué tipo y área es cada una)."""
        return self._camas.solicitudes_limpieza(), {c.id_cama: c for c in self._camas.mapa_camas()}

    def _mostrar(self, solicitudes, camas):
        ahora = self._reloj()
        self._solicitudes = {s.id_solicitud: s for s in solicitudes}
        filas = []
        for s in solicitudes:
            cama = camas.get(s.id_cama)
            filas.append((s.id_solicitud, (
                s.codigo_cama, type(cama).NOMBRE_CORTO if cama else "", cama.area if cama else "",
                formato.hora(s.fecha_solicitud),
                formato.texto_minutos(formato.minutos_desde(s.fecha_solicitud, ahora)))))
        self._tabla.cargar(filas)
        self._actualizar_boton()
