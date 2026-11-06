"""
Gestión de camas: asignar una cama a quien la espera, seguir a los pacientes que ya tienen una y sacar o devolver
camas al servicio. El tablero solo muestra (brief §3); las acciones sobre las camas están aquí.

- «Esperan cama (N)»: la cola por prioridad. Al elegir un paciente se ven las camas libres compatibles con su nivel
  (las decide el controlador con Cama.es_compatible) y se reserva una (RN-01, RN-05).
- «Con cama (N)»: las camas reservadas u ocupadas, con su paciente. Una reservada: «Llegó a la cama» o «Cancelar
  reserva». Una ocupada: «Dar de alta», y la cama pasa a limpieza (RN-07). Referir y registrar una fuga cierran el
  episodio desde las dos. Como el alta, piden confirmación: no se deshacen.
- «Mantenimiento»: las camas libres o fuera de servicio. Una libre sale de servicio con su motivo; una fuera de
  servicio vuelve.

Los datos se leen al abrir, al cambiar de opción y después de cada operación, porque otra PC pudo cambiarlos.
"""
import logging
from datetime import datetime

import customtkinter as ctk

from models.estados import EstadoCama
from models.excepciones import SigtacError
from views import formato, tema
from views.componentes import (BotonPrimario, BotonSecundario, Desplazable, Selector, TablaDatos, Tarjeta, campo_texto,
                               confirmar, etiqueta_campo, marcar_error, mostrar_error, mostrar_info, texto_nivel)
from views.componentes.campos import sin_error

logger = logging.getLogger(__name__)

NADIE_ESPERA = "Nadie espera cama."
NADIE_CON_CAMA = "Ninguna cama tiene un paciente asignado."
SIN_CAMAS_MANTENIMIENTO = "No hay camas disponibles ni fuera de servicio."
ELIJA_PACIENTE = "Elija un paciente de la cola para ver sus camas."
SIN_LECTURA_COMPATIBLES = "No se pudieron leer sus camas compatibles. Elíjalo de nuevo."
SIN_DATOS = "Paciente sin datos"
# El botón principal deshabilitado dice por qué no responde
TEXTO_ELEGIR_PACIENTE = "Elija un paciente de la cola"
TEXTO_ELEGIR_CAMA = "Elija una cama compatible"
TEXTO_ELEGIR_CON_CAMA = "Elija un paciente de la lista"
TEXTO_ELEGIR_MANTENIMIENTO = "Elija una cama de la lista"
TITULOS = {
    "espera": ("Asignar cama", "Elija un paciente y una cama disponible compatible con su nivel"),
    "con_cama": ("Pacientes con cama", "Llegada a la cama, alta y otros cierres del episodio"),
    "mantenimiento": ("Mantenimiento", "Camas disponibles o fuera de servicio"),
}


def sin_compatibles(nivel: int | None) -> str:
    """Lo que dice la tabla de camas cuando ninguna libre sirve para ese nivel."""
    return f"No hay camas disponibles compatibles con el nivel {texto_nivel(nivel)}."


def destino_cama(queda_disponible: bool) -> str:
    """Qué pasa con la cama al cerrar el episodio: sin uso vuelve sin limpieza; usada, pasa a limpieza (RN-07)."""
    return "queda disponible" if queda_disponible else "pasa a limpieza"


def nombre(paciente) -> str:
    return formato.nombre_corto(paciente) if paciente else SIN_DATOS


class GestionCamasView(ctk.CTkFrame):
    FILAS_LISTA = 5          # filas visibles de cada lista (más se desplazan dentro de la tabla)
    FILAS_COMPATIBLES = 3
    # Caben en la tarjeta a 1093×614 sin desplazamiento horizontal (brief, «Espacio útil»)
    COLUMNAS_COLA = (("Nivel", 112), ("Paciente", 200), ("Motivo", 240), ("Espera", 80))
    COLUMNAS_COMPATIBLES = (("Cama", 96), ("Tipo", 144), ("Área", 240))
    COLUMNAS_CON_CAMA = (("Cama", 96), ("Estado", 112), ("Nivel", 112), ("Paciente", 200), ("Desde", 80))
    COLUMNAS_MANTENIMIENTO = (("Cama", 96), ("Tipo", 144), ("Área", 240), ("Estado", 144))

    def __init__(self, padre, camas, reloj=datetime.now):
        super().__init__(padre, fg_color="transparent")
        self._camas, self._reloj = camas, reloj
        self._cola = {}            # id_episodio → EntradaCola
        self._compatibles = {}     # id_cama → Cama, del paciente elegido en la cola
        self._con_cama = {}        # id_episodio → PacienteEnCama
        self._mantenimiento = {}   # id_cama → Cama
        self._paciente_mostrado = None   # id_episodio cuyas camas compatibles se muestran
        self._motivo_rechazado = None    # el motivo tal como se rechazó: su aviso sigue hasta que cambie

        # Como Pacientes: la tarjeta se desplaza en vertical si no cabe (1093×614)
        self._contenido = contenido = Desplazable(self)
        contenido.pack(fill="both", expand=True)
        self._tarjeta = Tarjeta(contenido, *TITULOS["espera"])
        self._tarjeta.pack(fill="x")
        self._modo = Selector(self._tarjeta.cabecera, [("espera", "Esperan cama"), ("con_cama", "Con cama"),
                                                       ("mantenimiento", "Mantenimiento")], self._cambiar_modo)
        self._modo.pack(side="right")
        cuerpo = ctk.CTkFrame(self._tarjeta, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))

        self._paneles = {"espera": self._crear_espera(cuerpo), "con_cama": self._crear_con_cama(cuerpo),
                         "mantenimiento": self._crear_mantenimiento(cuerpo)}
        self._paneles["espera"].pack(fill="x")
        self._cargar_datos()

    # ---- Esperan cama

    def _crear_espera(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        self._tabla_cola = TablaDatos(marco, self.COLUMNAS_COLA, NADIE_ESPERA, al_seleccionar=self._paciente_elegido,
                                      filas=self.FILAS_LISTA)
        self._tabla_cola.pack(fill="x")
        etiqueta_campo(marco, "Camas compatibles").pack(anchor="w", pady=(tema.ESPACIO_2, tema.ESPACIO_MINIMO))
        self._tabla_compatibles = TablaDatos(marco, self.COLUMNAS_COMPATIBLES, ELIJA_PACIENTE,
                                             al_seleccionar=lambda _id: self._actualizar_asignar(),
                                             filas=self.FILAS_COMPATIBLES)
        self._tabla_compatibles.pack(fill="x")
        fila = self._fila_acciones(marco)
        self._boton_asignar = BotonPrimario(fila, TEXTO_ELEGIR_PACIENTE, self.asignar, state="disabled")
        self._boton_asignar.pack(side="left")
        return marco

    def _paciente_elegido(self, id_episodio, recarga: bool = False):
        """
        Al elegir un paciente de la cola se leen sus camas compatibles; sin elección, la tabla lo pide.

        ttk avisa la selección más tarde, también la que hace el código al recargar: si el paciente es el que ya se
        muestra, no se vuelve a leer (así no se pierde la cama elegida). Durante una recarga (`recarga`) un error no
        abre un diálogo.
        """
        if id_episodio == self._paciente_mostrado and not recarga:
            self._actualizar_asignar()
            return
        self._compatibles = {}
        self._paciente_mostrado = id_episodio
        entrada = self._cola.get(id_episodio)
        if entrada is None:
            self._tabla_compatibles.cambiar_texto_vacio(ELIJA_PACIENTE)
        else:
            try:
                self._compatibles = {c.id_cama: c for c in self._camas.camas_compatibles(id_episodio)}
            except (SigtacError, ValueError) as error:
                logger.warning("No se pudieron leer las camas compatibles (%s).", type(error).__name__)
                if not recarga:
                    mostrar_error(self, error)  # p. ej. otra PC ya le asignó cama: se recarga la cola
                    self._recargar()
                    return
                self._tabla_compatibles.cambiar_texto_vacio(SIN_LECTURA_COMPATIBLES)
            else:
                self._tabla_compatibles.cambiar_texto_vacio(sin_compatibles(entrada.nivel))
        self._tabla_compatibles.cargar([(c.id_cama, (c.codigo, type(c).NOMBRE_CORTO, c.area))
                                        for c in self._compatibles.values()])
        self._actualizar_asignar()

    def _actualizar_asignar(self):
        cama = self._compatibles.get(self._tabla_compatibles.seleccionado())
        if self._cola.get(self._tabla_cola.seleccionado()) is None:
            self._boton_asignar.configure(text=TEXTO_ELEGIR_PACIENTE, state="disabled")
        elif cama is None:
            self._boton_asignar.configure(text=TEXTO_ELEGIR_CAMA, state="disabled")
        else:
            self._boton_asignar.configure(text=f"Asignar cama {cama.codigo}", state="normal")

    def asignar(self):
        """Reserva la cama elegida para el paciente elegido. Cuando llegue a ella, se marca en «Con cama»."""
        entrada = self._cola.get(self._tabla_cola.seleccionado())
        cama = self._compatibles.get(self._tabla_compatibles.seleccionado())
        if entrada is None or cama is None:
            return
        self._operar(lambda: self._camas.asignar(entrada.episodio.id_episodio, cama.id_cama),
                     f"Cama {cama.codigo} reservada para {nombre(entrada.paciente)}. Cuando llegue, márquelo en "
                     "«Con cama».")

    # ---- Con cama

    def _crear_con_cama(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        self._tabla_con_cama = TablaDatos(marco, self.COLUMNAS_CON_CAMA, NADIE_CON_CAMA,
                                          al_seleccionar=self._con_cama_elegido, filas=self.FILAS_LISTA)
        self._tabla_con_cama.pack(fill="x")
        fila = self._fila_acciones(marco)
        # El principal cambia con el estado de la cama: «Llegó a la cama» (reservada) o «Dar de alta» (ocupada)
        self._boton_cama = BotonPrimario(fila, TEXTO_ELEGIR_CON_CAMA, self._accion_principal, state="disabled")
        self._boton_cama.pack(side="left")
        self._boton_cancelar = BotonSecundario(fila, "Cancelar reserva", self.cancelar_reserva, state="disabled")
        self._boton_referir = BotonSecundario(fila, "Referir", self.referir, state="disabled")
        self._boton_fuga = BotonSecundario(fila, "Registrar fuga", self.registrar_fuga, state="disabled")
        for boton in (self._boton_cancelar, self._boton_referir, self._boton_fuga):
            boton.pack(side="left", padx=(tema.ESPACIO, 0))
        return marco

    def _elegido_con_cama(self):
        return self._con_cama.get(self._tabla_con_cama.seleccionado())

    def _con_cama_elegido(self, _id_episodio=None):
        elegido = self._elegido_con_cama()
        if elegido is None:
            self._boton_cama.configure(text=TEXTO_ELEGIR_CON_CAMA, state="disabled")
        elif elegido.cama.estado == EstadoCama.RESERVADA:
            self._boton_cama.configure(text="Llegó a la cama", state="normal")
        else:
            self._boton_cama.configure(text="Dar de alta", state="normal")
        reservada = elegido is not None and elegido.cama.estado == EstadoCama.RESERVADA
        self._boton_cancelar.configure(state="normal" if reservada else "disabled")
        for boton in (self._boton_referir, self._boton_fuga):
            boton.configure(state="disabled" if elegido is None else "normal")

    def _accion_principal(self):
        elegido = self._elegido_con_cama()
        if elegido is None:
            return
        if elegido.cama.estado == EstadoCama.RESERVADA:
            self.ocupar()
        else:
            self.dar_alta()

    def ocupar(self):
        """El paciente llegó a la cama reservada: la cama queda ocupada."""
        elegido = self._elegido_con_cama()
        if elegido is not None:
            self._operar(lambda: self._camas.ocupar(elegido.cama.id_cama),
                         f"{nombre(elegido.paciente)} llegó a la cama {elegido.cama.codigo}: queda ocupada.")

    def cancelar_reserva(self):
        """La reserva no llegó a usarse: la cama queda libre (sin limpieza) y el paciente vuelve a la cola."""
        elegido = self._elegido_con_cama()
        if elegido is not None:
            self._operar(lambda: self._camas.cancelar_asignacion(elegido.episodio.id_episodio),
                         f"Reserva cancelada: la cama {elegido.cama.codigo} queda disponible y "
                         f"{nombre(elegido.paciente)} vuelve a esperar cama.")

    def dar_alta(self):
        elegido = self._elegido_con_cama()
        if elegido is None:
            return
        pregunta = (f"¿Dar de alta a {nombre(elegido.paciente)}?\n\nEl episodio se cierra y la cama "
                    f"{elegido.cama.codigo} pasa a limpieza. No se puede deshacer.")
        if confirmar(self, pregunta):
            self._operar(lambda: self._camas.dar_alta(elegido.episodio.id_episodio),
                         f"Alta registrada. La cama {elegido.cama.codigo} espera limpieza.")

    def referir(self):
        self._cerrar_episodio(self._camas.referir, "¿Referir a {nombre} a otro establecimiento?",
                              "Referencia registrada.")

    def registrar_fuga(self):
        self._cerrar_episodio(self._camas.registrar_fuga, "¿Registrar que {nombre} se retiró sin alta médica?",
                              "Fuga registrada.")

    def _cerrar_episodio(self, operacion, pregunta: str, exito: str):
        """
        Referir o registrar una fuga: cierran el episodio y liberan la cama. Una cama solo reservada queda disponible;
        una ocupada, como en el alta, pasa a limpieza (RN-07). La pregunta usa el estado recién leído (otra PC pudo
        marcar la llegada), y el aviso final, lo que hizo el controlador: el id de la limpieza pedida o None.
        """
        if self._elegido_con_cama() is None:
            return
        self._recargar(conservar=True)
        elegido = self._elegido_con_cama()
        if elegido is None:
            return  # otra PC ya cerró el episodio: la lista recargada ya no lo muestra
        codigo, quien = elegido.cama.codigo, nombre(elegido.paciente)
        texto = (f"{pregunta.format(nombre=quien)}\n\nEl episodio se cierra y la cama {codigo} "
                 f"{destino_cama(elegido.cama.estado == EstadoCama.RESERVADA)}. No se puede deshacer.")
        if confirmar(self, texto):
            self._operar(lambda: operacion(elegido.episodio.id_episodio),
                         lambda id_limpieza: f"{exito} La cama {codigo} {destino_cama(id_limpieza is None)}.")

    # ---- Mantenimiento

    def _crear_mantenimiento(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        self._tabla_mantenimiento = TablaDatos(marco, self.COLUMNAS_MANTENIMIENTO, SIN_CAMAS_MANTENIMIENTO,
                                               al_seleccionar=self._cama_mantenimiento_elegida,
                                               filas=self.FILAS_LISTA)
        self._tabla_mantenimiento.pack(fill="x")

        # El motivo, solo para sacar de servicio una cama libre. Si falta, se explica bajo el campo
        self._con_motivo = ctk.CTkFrame(marco, fg_color="transparent")
        etiqueta_campo(self._con_motivo, "Motivo").pack(anchor="w", pady=(tema.ESPACIO_2, tema.ESPACIO_MINIMO))
        self._motivo = campo_texto(self._con_motivo, "Qué falla en la cama o su equipo (sin datos del paciente)")
        self._motivo.pack(fill="x")
        self._aviso_motivo = ctk.CTkLabel(self._con_motivo, text="", font=tema.fuente("pequena"),
                                          text_color=tema.COLOR_ERROR, anchor="w")
        self._motivo.bind("<Return>", lambda _e: self.mantenimiento(), add="+")
        self._motivo.bind("<KeyRelease>", lambda _e: self._motivo_editado(), add="+")

        self._fila_mantenimiento = fila = self._fila_acciones(marco)
        self._boton_mantenimiento = BotonPrimario(fila, TEXTO_ELEGIR_MANTENIMIENTO, self.mantenimiento,
                                                  state="disabled")
        self._boton_mantenimiento.pack(side="left")
        return marco

    def _cama_mantenimiento_elegida(self, _id_cama=None):
        cama = self._mantenimiento.get(self._tabla_mantenimiento.seleccionado())
        libre = cama is not None and cama.estado == EstadoCama.DISPONIBLE
        if cama is None:
            self._boton_mantenimiento.configure(text=TEXTO_ELEGIR_MANTENIMIENTO, state="disabled")
        elif libre:
            self._boton_mantenimiento.configure(text=f"Poner {cama.codigo} fuera de servicio", state="normal")
        else:
            self._boton_mantenimiento.configure(text=f"Volver {cama.codigo} a servicio", state="normal")
        # El motivo escrito se conserva aunque se oculte (p. ej. al recargar tras un error); se borra al guardarlo
        if libre:
            self._con_motivo.pack(fill="x", before=self._fila_mantenimiento)
        else:
            self._con_motivo.pack_forget()

    def mantenimiento(self):
        """Saca de servicio la cama libre elegida (con su motivo) o devuelve al servicio la que estaba fuera."""
        cama = self._mantenimiento.get(self._tabla_mantenimiento.seleccionado())
        if cama is None:
            return "break"
        if cama.estado != EstadoCama.DISPONIBLE:
            self._operar(lambda: self._camas.volver_a_servicio(cama.id_cama),
                         f"La cama {cama.codigo} volvió a servicio: queda disponible.")
            return "break"
        try:
            self._camas.poner_fuera_de_servicio(cama.id_cama, self._motivo.get())
        except ValueError as error:
            # La cama sale de la lista: el único dato que se escribe aquí es el motivo
            marcar_error(self._motivo)
            self._motivo_rechazado = self._motivo.get()
            self._aviso_motivo.configure(text=str(error))
            self._aviso_motivo.pack(anchor="w", pady=(tema.ESPACIO, 0), after=self._motivo)
            return "break"
        except SigtacError as error:
            mostrar_error(self, error)
            self._recargar(conservar=True)
            return "break"
        self._limpiar_motivo()
        self._recargar()
        mostrar_info(self, f"La cama {cama.codigo} quedó fuera de servicio.")
        return "break"

    def _motivo_editado(self):
        """Al corregir el motivo rechazado se van el rojo y su aviso. Soltar el Enter que lo envió no lo corrige."""
        if self._motivo_rechazado is not None and self._motivo.get() != self._motivo_rechazado:
            self._motivo_corregido()

    def _motivo_corregido(self):
        self._motivo_rechazado = None
        sin_error(self._motivo)
        self._aviso_motivo.pack_forget()

    def _limpiar_motivo(self):
        self._motivo.delete(0, "end")
        self._motivo._activate_placeholder()
        self._motivo_corregido()

    # ---- Datos

    def al_mostrar(self):
        """Al volver a Gestión de camas: relee las listas, sin diálogo, y conserva lo elegido si sigue."""
        self._recargar(conservar=True)

    def _operar(self, operacion, exito):
        """
        Una operación del controlador. Si falla (p. ej. otra PC cambió la cama), se avisa y se recarga conservando la
        elección; si sale bien, se recarga sin elección y se avisa el resultado. `exito` es el texto, o una función que
        lo arma con lo que devolvió el controlador.
        """
        try:
            resultado = operacion()
        except (SigtacError, ValueError) as error:
            mostrar_error(self, error)
            self._recargar(conservar=True)
            return
        self._recargar()
        mostrar_info(self, exito(resultado) if callable(exito) else exito)

    def _cargar_datos(self):
        """La cola, las camas con paciente y las de mantenimiento, al abrir. Si la BD falla, un solo aviso."""
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron leer las camas (%s).", type(error).__name__)
            mostrar_error(self, error)
            self._mostrar([], [], [])
            # Las listas no dicen «Nadie espera cama»: no se pudieron leer
            for tabla in (self._tabla_cola, self._tabla_con_cama, self._tabla_mantenimiento):
                tabla.sin_lectura()
            # Sin cifra: «(0)» diría que nadie espera, y no se sabe
            self._modo.cambiar_texto("espera", "Esperan cama")
            self._modo.cambiar_texto("con_cama", "Con cama")
            return
        self._mostrar(*datos)

    def _recargar(self, conservar: bool = False):
        """Vuelve a leer todo, sin diálogo si falla. Con `conservar`, lo elegido que siga en su lista sigue elegido."""
        tablas = (self._tabla_cola, self._tabla_con_cama, self._tabla_mantenimiento)
        elegidos = [tabla.seleccionado() for tabla in tablas] if conservar else [None] * len(tablas)
        cama_elegida = self._tabla_compatibles.seleccionado() if conservar else None
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron actualizar las camas (%s).", type(error).__name__)
            return
        self._mostrar(*datos)
        for tabla, elegido in zip(tablas, elegidos):
            if elegido is not None:
                tabla.seleccionar(elegido)
        self._paciente_elegido(self._tabla_cola.seleccionado(), recarga=True)
        if cama_elegida is not None:
            self._tabla_compatibles.seleccionar(cama_elegida)  # si sigue libre y compatible
        self._actualizar_asignar()
        self._con_cama_elegido()
        self._cama_mantenimiento_elegida()

    def _leer(self):
        mantenimiento = [c for c in self._camas.mapa_camas()
                         if c.estado in (EstadoCama.DISPONIBLE, EstadoCama.FUERA_SERVICIO)]
        return self._camas.cola_de_espera(), self._camas.pacientes_con_cama(), mantenimiento

    def _mostrar(self, cola, con_cama, mantenimiento):
        ahora = self._reloj()
        self._cola = {e.episodio.id_episodio: e for e in cola}
        self._tabla_cola.cargar([(id_episodio, (
            texto_nivel(e.nivel), nombre(e.paciente), e.episodio.motivo_consulta,
            formato.texto_minutos(formato.minutos_desde(e.episodio.fecha_ingreso, ahora))))
            for id_episodio, e in self._cola.items()])
        self._con_cama = {p.episodio.id_episodio: p for p in con_cama}
        self._tabla_con_cama.cargar([(id_episodio, (
            p.cama.codigo, formato.texto_estado_cama(p.cama.estado), texto_nivel(p.nivel), nombre(p.paciente),
            formato.hora(p.fecha_asignacion))) for id_episodio, p in self._con_cama.items()])
        self._mantenimiento = {c.id_cama: c for c in mantenimiento}
        self._tabla_mantenimiento.cargar([
            (c.id_cama, (c.codigo, type(c).NOMBRE_CORTO, c.area, formato.texto_estado_cama(c.estado)))
            for c in mantenimiento])
        self._modo.cambiar_texto("espera", f"Esperan cama ({len(cola)})")
        self._modo.cambiar_texto("con_cama", f"Con cama ({len(con_cama)})")
        # Las tablas recargadas no tienen elección: se vacían las camas compatibles y se deshabilitan las acciones
        self._paciente_elegido(None, recarga=True)
        self._con_cama_elegido()
        self._cama_mantenimiento_elegida()

    def _cambiar_modo(self, modo: str):
        self._tarjeta.cambiar_textos(*TITULOS[modo])
        for clave, panel in self._paneles.items():
            if clave != modo:
                panel.pack_forget()
        self._paneles[modo].pack(fill="x")
        self._contenido.reacomodar()
        self._recargar(conservar=True)

    # ---- Piezas de la pantalla

    @staticmethod
    def _fila_acciones(padre) -> ctk.CTkFrame:
        fila = ctk.CTkFrame(padre, fg_color="transparent")
        fila.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        return fila
