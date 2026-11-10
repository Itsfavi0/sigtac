"""
Gestión de camas: asignar una cama a quien la espera, seguir a los pacientes que ya tienen una y sacar o devolver
camas al servicio. El tablero solo muestra (brief §3); las acciones sobre las camas están aquí.

Arriba, un resumen (cuántos esperan, cuántos con prioridad 1–2, cuántas camas libres). Cada opción tiene dos
columnas: a la izquierda la lista para elegir, a la derecha lo elegido y sus acciones.

- «Esperan cama (N)»: la cola por prioridad, como en el tablero. Al elegir un paciente se ven sus datos y las camas
  libres compatibles con su nivel, como casillas (las decide el controlador con Cama.es_compatible); se reserva una
  (RN-01, RN-05).
- «Con cama (N)»: los pacientes con una cama reservada u ocupada. Una reservada: «Llegó a la cama» o «Cancelar
  reserva». Una ocupada: «Dar de alta», y la cama pasa a limpieza (RN-07). Referir y registrar una fuga cierran el
  episodio desde las dos. Como el alta, piden confirmación: no se deshacen.
- «Mantenimiento»: las camas libres o fuera de servicio, como casillas. Una libre sale de servicio con su motivo; una
  fuera de servicio vuelve.

Los datos se leen al abrir, al cambiar de opción y después de cada operación, porque otra PC pudo cambiarlos.
"""
import logging
from datetime import datetime

import customtkinter as ctk

from models.estados import EstadoCama
from models.excepciones import SigtacError
from models.triaje import excede_plazo
from views import formato, tema
from views.componentes import (BotonPrimario, BotonSecundario, Desplazable, InsigniaNivel, ListaSeleccion, Selector,
                               Tarjeta, TarjetaCama, aviso_columna, campo_texto, confirmar, dos_columnas,
                               etiqueta_campo, etiqueta_resumen, fila_acciones, marcar_error, mostrar_error,
                               mostrar_info, texto_nivel)
from views.componentes.campos import sin_error

logger = logging.getLogger(__name__)

NADIE_ESPERA = "Nadie espera cama."
NADIE_CON_CAMA = "Ninguna cama tiene un paciente asignado."
SIN_CAMAS_MANTENIMIENTO = "No hay camas disponibles ni fuera de servicio."
ELIJA_PACIENTE = "Elija un paciente de la cola para ver sus camas."
ELIJA_CON_CAMA = "Elija un paciente de la lista para ver su cama y sus acciones."
ELIJA_MANTENIMIENTO = "Elija una cama: una disponible sale de servicio con su motivo; una fuera de servicio vuelve."
SIN_LECTURA_COMPATIBLES = "No se pudieron leer sus camas compatibles. Elíjalo de nuevo."
SIN_DATOS = "Paciente sin datos"
NINGUN_PACIENTE = "Ningún paciente elegido"  # la ficha vacía: qué hacer ya lo dicen la lista y el botón
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
    """Lo que dice la lista de camas cuando ninguna libre sirve para ese nivel."""
    return f"No hay camas disponibles compatibles con el nivel {texto_nivel(nivel)}."


def destino_cama(queda_disponible: bool) -> str:
    """Qué pasa con la cama al cerrar el episodio: sin uso vuelve sin limpieza; usada, pasa a limpieza (RN-07)."""
    return "queda disponible" if queda_disponible else "pasa a limpieza"


def nombre(paciente) -> str:
    return formato.nombre_corto(paciente) if paciente else SIN_DATOS


def texto_resumen(cola, libres: int) -> tuple[str, str, str]:
    """Las tres etiquetas del resumen: «4 esperan cama», «2 con prioridad 1–2», «15 camas libres»."""
    esperan = "1 espera cama" if len(cola) == 1 else f"{len(cola)} esperan cama"
    urgentes = sum(entrada.nivel in (1, 2) for entrada in cola)
    camas = "1 cama libre" if libres == 1 else f"{libres} camas libres"
    return esperan, f"{urgentes} con prioridad 1–2", camas


class FichaElegido(ctk.CTkFrame):
    """El paciente elegido: su nivel en grande, su nombre, el nivel con su plazo, y su documento y motivo."""

    LADO_INSIGNIA = 48  # como el nivel sugerido en Triaje

    def __init__(self, padre):
        super().__init__(padre, fg_color="transparent")
        self._insignia = InsigniaNivel(self, lado=self.LADO_INSIGNIA)
        self._insignia.pack(side="left", padx=(0, tema.ESPACIO_MEDIO))
        textos = ctk.CTkFrame(self, fg_color="transparent")
        textos.pack(side="left", fill="x", expand=True)
        self._nombre = ctk.CTkLabel(textos, text="", font=tema.fuente("subtitulo"), text_color=tema.COLOR_TEXTO,
                                    anchor="w")
        self._nombre.pack(anchor="w")
        self._nivel = ctk.CTkLabel(textos, text="", font=tema.fuente("normal"), text_color=tema.COLOR_TEXTO,
                                   anchor="w")
        self._nivel.pack(anchor="w")
        self._datos = ctk.CTkLabel(textos, text="", font=tema.fuente("pequena"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        self._datos.pack(anchor="w")

    def mostrar_vacia(self, texto: str):
        """Sin paciente elegido, la ficha conserva su lugar (así la tarjeta no cambia de alto al elegir)."""
        self._insignia.mostrar(None)
        self._nombre.configure(text="")
        self._nivel.configure(text=texto)
        self._datos.configure(text="")

    def mostrar(self, paciente, episodio, nivel: int | None):
        self._insignia.mostrar(nivel)
        self._nombre.configure(text=nombre(paciente))
        self._nivel.configure(text="Sin triaje" if nivel is None else
                              f"Nivel {texto_nivel(nivel)} · {formato.texto_plazo(nivel)}")
        documento = formato.documento_enmascarado(paciente) if paciente else ""
        self._datos.configure(text=" · ".join(t for t in (documento, episodio.motivo_consulta) if t))

    @property
    def textos(self) -> tuple[str, str, str]:
        return self._nombre.cget("text"), self._nivel.cget("text"), self._datos.cget("text")


class FilaPaciente(ctk.CTkFrame):
    """
    Una fila de paciente, como en la cola del tablero: el cuadro de su nivel, dos renglones y, a la derecha, un dato.
    `mostrar` la repinta con datos nuevos (la lista la reutiliza al recargar).
    """

    ALTO = 52           # dos renglones y el cuadro de su nivel, con aire para el borde de la fila elegida
    ANCHO_ESPERA = 80   # la espera, alineada a la derecha como en el tablero
    LADO_INSIGNIA = 28

    def __init__(self, padre):
        super().__init__(padre, fg_color="transparent", corner_radius=tema.RADIO_CONTROL, height=self.ALTO,
                         border_width=0, border_color=tema.COLOR_BORDE)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._insignia = InsigniaNivel(self, lado=self.LADO_INSIGNIA)
        self._insignia.grid(row=0, column=0, padx=tema.ESPACIO_MEDIO)
        textos = ctk.CTkFrame(self, fg_color="transparent")
        textos.grid(row=0, column=1, sticky="w")
        self._principal = ctk.CTkLabel(textos, text="", font=tema.fuente("fuerte"), text_color=tema.COLOR_TEXTO,
                                       height=17, anchor="w")
        self._principal.pack(anchor="w")
        self._secundario = ctk.CTkLabel(textos, text="", font=tema.fuente("pequena"),
                                        text_color=tema.COLOR_TEXTO_SECUNDARIO, height=15, anchor="w")
        self._secundario.pack(anchor="w")
        self._mostrado = None  # lo que muestra: si una recarga trae lo mismo, no se repinta (cada repintado redibuja)

    def _pintar(self, nivel: int | None, principal: str, secundario: str, *dato) -> bool:
        """Pinta la fila si cambió lo que muestra; devuelve si la pintó."""
        if self._mostrado == (nivel, principal, secundario, *dato):
            return False
        self._mostrado = (nivel, principal, secundario, *dato)
        self._insignia.mostrar(nivel)
        self._principal.configure(text=principal)
        self._secundario.configure(text=secundario)
        return True

    @property
    def textos(self) -> tuple[str, ...]:
        return self._principal.cget("text"), self._secundario.cget("text")


class FilaCola(FilaPaciente):
    """Quien espera cama: nombre y motivo, y la espera (en rojo si pasó el plazo de su nivel)."""

    def __init__(self, padre, entrada, ahora: datetime):
        super().__init__(padre)
        self._espera = ctk.CTkLabel(self, text="", width=self.ANCHO_ESPERA, anchor="e")  # alineada, como en el tablero
        self._espera.grid(row=0, column=2, padx=tema.ESPACIO_MEDIO)
        self.mostrar(entrada, ahora)

    def mostrar(self, entrada, ahora: datetime):
        minutos = formato.minutos_desde(entrada.episodio.fecha_ingreso, ahora)
        tarde = entrada.nivel is not None and excede_plazo(entrada.nivel, minutos)
        if not self._pintar(entrada.nivel, nombre(entrada.paciente), entrada.episodio.motivo_consulta, minutos, tarde):
            return
        self._espera.configure(text=formato.texto_minutos(minutos), font=tema.fuente("fuerte" if tarde else "pequena"),
                               text_color=tema.COLOR_ERROR if tarde else tema.COLOR_TEXTO_SECUNDARIO)

    @property
    def textos(self) -> tuple[str, ...]:
        return *super().textos, self._espera.cget("text")


class FilaConCama(FilaPaciente):
    """Quien tiene cama: nombre, el estado de la cama desde cuándo, y su código con el tinte de su estado."""

    ALTO_CODIGO = 28

    def __init__(self, padre, en_cama):
        super().__init__(padre)
        self._codigo = ctk.CTkLabel(self, text="", font=tema.fuente("codigo"), text_color=tema.COLOR_TEXTO,
                                    corner_radius=tema.RADIO_CONTROL, height=self.ALTO_CODIGO)
        self._codigo.grid(row=0, column=2, padx=tema.ESPACIO_MEDIO)
        self.mostrar(en_cama)

    def mostrar(self, en_cama):
        estado = en_cama.cama.estado
        if not self._pintar(en_cama.nivel, nombre(en_cama.paciente),
                            f"{formato.texto_estado_cama(estado)} desde las {formato.hora(en_cama.fecha_asignacion)}",
                            en_cama.cama.codigo, estado):
            return
        self._codigo.configure(text=en_cama.cama.codigo, fg_color=tema.COLOR_FONDO_ESTADO_CAMA[estado])

    @property
    def textos(self) -> tuple[str, ...]:
        return self._codigo.cget("text"), *super().textos


class GestionCamasView(ctk.CTkFrame):
    FILAS_LISTA = 5          # filas visibles de cada lista de pacientes (más se desplazan dentro de la lista)
    # Filas de casillas compatibles visibles: con más, la columna derecha quedaría más alta que la cola
    FILAS_CAMAS = 2
    FILAS_MANTENIMIENTO = 4  # filas de casillas visibles en Mantenimiento
    COLUMNAS_CAMAS = 3       # casillas por fila: caben en una columna de la tarjeta a 1093×614
    ANCHO_CASILLA = 128      # la casilla de la cama del paciente, junto a su acción principal

    def __init__(self, padre, camas, reloj=datetime.now):
        super().__init__(padre, fg_color="transparent")
        self._camas, self._reloj = camas, reloj
        self._ahora = reloj()      # la hora con la que se calculan las esperas de la última lectura
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

        self._resumen = ctk.CTkFrame(cuerpo, fg_color="transparent")
        self._etiquetas_resumen = (etiqueta_resumen(self._resumen),
                                   etiqueta_resumen(self._resumen, tema.COLOR_NIVEL[1]),
                                   etiqueta_resumen(self._resumen, tema.COLOR_ESTADO_CAMA[EstadoCama.DISPONIBLE]))
        self._paneles = {"espera": self._crear_espera(cuerpo), "con_cama": self._crear_con_cama(cuerpo),
                         "mantenimiento": self._crear_mantenimiento(cuerpo)}
        self._paneles["espera"].pack(fill="x")
        self._cargar_datos()

    # ---- Esperan cama

    def _crear_espera(self, padre) -> ctk.CTkFrame:
        marco, izquierda, derecha = dos_columnas(padre)
        etiqueta_campo(izquierda, "Cola por prioridad").pack(anchor="w", pady=(0, tema.ESPACIO))
        self._lista_cola = self._lista_pacientes(
            izquierda, lambda padre_, entrada: FilaCola(padre_, entrada, self._ahora), NADIE_ESPERA,
            self._paciente_elegido, al_activar=lambda _id: self._lista_compatibles.enfocar())

        self._ficha_cola = FichaElegido(derecha)
        self._ficha_cola.pack(fill="x", pady=(0, tema.ESPACIO_2))
        self._titulo_compatibles = etiqueta_campo(derecha, "Camas compatibles")
        self._titulo_compatibles.pack(anchor="w", pady=(0, tema.ESPACIO))
        self._lista_compatibles = ListaSeleccion(
            derecha, lambda padre_, cama: TarjetaCama(padre_, cama, detalle=type(cama).NOMBRE_CORTO), ELIJA_PACIENTE,
            alto_elemento=TarjetaCama.ALTO, columnas=self.COLUMNAS_CAMAS, filas=self.FILAS_CAMAS,
            al_seleccionar=lambda _id: self._actualizar_asignar(), al_activar=lambda _id: self.asignar(),
            actualizar=TarjetaCama.mostrar)
        self._lista_compatibles.pack(fill="x")
        fila = fila_acciones(derecha)
        self._boton_asignar = BotonPrimario(fila, TEXTO_ELEGIR_PACIENTE, self.asignar, state="disabled")
        self._boton_asignar.pack(side="left")
        return marco

    def _paciente_elegido(self, id_episodio, recarga: bool = False):
        """
        Al elegir un paciente de la cola se ven sus datos y se leen sus camas compatibles; sin elección, la lista lo
        pide. Si el paciente es el que ya se muestra, no se vuelve a leer (así no se pierde la cama elegida). Durante
        una recarga (`recarga`) un error no abre un diálogo.
        """
        if id_episodio == self._paciente_mostrado and not recarga:
            self._actualizar_asignar()
            return
        self._compatibles = {}
        self._paciente_mostrado = id_episodio
        entrada = self._cola.get(id_episodio)
        if entrada is None:
            self._ficha_cola.mostrar_vacia(NINGUN_PACIENTE)
            self._titulo_compatibles.configure(text="Camas compatibles")
            self._lista_compatibles.cambiar_texto_vacio(ELIJA_PACIENTE)
        else:
            self._ficha_cola.mostrar(entrada.paciente, entrada.episodio, entrada.nivel)
            try:
                self._compatibles = {c.id_cama: c for c in self._camas.camas_compatibles(id_episodio)}
            except (SigtacError, ValueError) as error:
                logger.warning("No se pudieron leer las camas compatibles (%s).", type(error).__name__)
                if not recarga:
                    mostrar_error(self, error)  # p. ej. otra PC ya le asignó cama: se recarga la cola
                    self._recargar()
                    return
                self._lista_compatibles.cambiar_texto_vacio(SIN_LECTURA_COMPATIBLES)
                # Sin cifra: «(0)» diría que no hay ninguna, y no se sabe
                self._titulo_compatibles.configure(text=f"Camas compatibles con el nivel {texto_nivel(entrada.nivel)}")
            else:
                self._lista_compatibles.cambiar_texto_vacio(sin_compatibles(entrada.nivel))
                self._titulo_compatibles.configure(
                    text=f"Camas compatibles con el nivel {texto_nivel(entrada.nivel)} ({len(self._compatibles)})")
        self._lista_compatibles.cargar(self._compatibles.items())
        self._actualizar_asignar()

    def _actualizar_asignar(self):
        entrada = self._cola.get(self._lista_cola.seleccionado())
        cama = self._compatibles.get(self._lista_compatibles.seleccionado())
        if entrada is None:
            self._boton_asignar.configure(text=TEXTO_ELEGIR_PACIENTE, state="disabled")
        elif cama is None:
            self._boton_asignar.configure(text=TEXTO_ELEGIR_CAMA, state="disabled")
        else:
            self._boton_asignar.configure(text=f"Asignar {cama.codigo} a {nombre(entrada.paciente)}", state="normal")

    def asignar(self):
        """Reserva la cama elegida para el paciente elegido. Cuando llegue a ella, se marca en «Con cama»."""
        entrada = self._cola.get(self._lista_cola.seleccionado())
        cama = self._compatibles.get(self._lista_compatibles.seleccionado())
        if entrada is None or cama is None:
            return
        self._operar(lambda: self._camas.asignar(entrada.episodio.id_episodio, cama.id_cama),
                     f"Cama {cama.codigo} reservada para {nombre(entrada.paciente)}. Cuando llegue, márquelo en "
                     "«Con cama».")

    # ---- Con cama

    def _crear_con_cama(self, padre) -> ctk.CTkFrame:
        marco, izquierda, derecha = dos_columnas(padre)
        etiqueta_campo(izquierda, "Reservadas u ocupadas").pack(anchor="w", pady=(0, tema.ESPACIO))
        self._lista_con_cama = self._lista_pacientes(izquierda, FilaConCama, NADIE_CON_CAMA, self._con_cama_elegido)

        self._sin_con_cama = aviso_columna(derecha, ELIJA_CON_CAMA)
        self._detalle_con_cama = ctk.CTkFrame(derecha, fg_color="transparent")
        self._ficha_con_cama = FichaElegido(self._detalle_con_cama)
        self._ficha_con_cama.pack(fill="x")

        # La casilla de su cama, al lado de la acción principal: la columna no debe quedar más alta que la lista (si
        # la tarjeta crece al elegir, aparece la barra de la pantalla y todo se vuelve a acomodar)
        fila = fila_acciones(derecha)
        self._casilla_con_cama = None
        self._fila_cama = fila
        # El principal cambia con el estado de la cama: «Llegó a la cama» (reservada) o «Dar de alta» (ocupada)
        self._boton_cama = BotonPrimario(fila, TEXTO_ELEGIR_CON_CAMA, self._accion_principal, state="disabled")
        self._boton_cama.pack(side="left")
        otras = fila_acciones(derecha, arriba=tema.ESPACIO)
        self._boton_cancelar = BotonSecundario(otras, "Cancelar reserva", self.cancelar_reserva, state="disabled")
        self._boton_referir = BotonSecundario(otras, "Referir", self.referir, state="disabled")
        self._boton_fuga = BotonSecundario(otras, "Registrar fuga", self.registrar_fuga, state="disabled")
        for i, boton in enumerate((self._boton_cancelar, self._boton_referir, self._boton_fuga)):
            boton.pack(side="left", padx=(0 if i == 0 else tema.ESPACIO, 0))
        return marco

    def _elegido_con_cama(self):
        return self._con_cama.get(self._lista_con_cama.seleccionado())

    def _con_cama_elegido(self, _id_episodio=None):
        elegido = self._elegido_con_cama()
        if elegido is None:
            self._detalle_con_cama.pack_forget()
            self._sin_con_cama.pack(anchor="w", before=self._boton_cama.master)
            if self._casilla_con_cama is not None:
                self._casilla_con_cama.pack_forget()
            self._boton_cama.configure(text=TEXTO_ELEGIR_CON_CAMA, state="disabled")
        else:
            self._sin_con_cama.pack_forget()
            self._ficha_con_cama.mostrar(elegido.paciente, elegido.episodio, elegido.nivel)
            if self._casilla_con_cama is None:
                self._casilla_con_cama = TarjetaCama(self._fila_cama, elegido.cama)
                self._casilla_con_cama.configure(width=self.ANCHO_CASILLA)
            else:
                self._casilla_con_cama.mostrar(elegido.cama)
            self._casilla_con_cama.pack(side="left", padx=(0, tema.ESPACIO), before=self._boton_cama)
            self._detalle_con_cama.pack(fill="x", before=self._boton_cama.master)
        reservada = elegido is not None and elegido.cama.estado == EstadoCama.RESERVADA
        if elegido is not None:
            self._boton_cama.configure(text="Llegó a la cama" if reservada else "Dar de alta", state="normal")
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
        marco, izquierda, derecha = dos_columnas(padre)
        etiqueta_campo(izquierda, "Por tipo de cama").pack(anchor="w", pady=(0, tema.ESPACIO))
        self._lista_mantenimiento = ListaSeleccion(
            izquierda, TarjetaCama, SIN_CAMAS_MANTENIMIENTO, alto_elemento=TarjetaCama.ALTO,
            columnas=self.COLUMNAS_CAMAS, filas=self.FILAS_MANTENIMIENTO,
            al_seleccionar=self._cama_mantenimiento_elegida,
            al_activar=lambda _id: self._activar_mantenimiento(), actualizar=TarjetaCama.mostrar)
        self._lista_mantenimiento.pack(fill="x")

        self._sin_mantenimiento = aviso_columna(derecha, ELIJA_MANTENIMIENTO)
        self._detalle_mantenimiento = ctk.CTkFrame(derecha, fg_color="transparent")
        self._codigo_mantenimiento = ctk.CTkLabel(self._detalle_mantenimiento, text="", font=tema.fuente("subtitulo"),
                                                  text_color=tema.COLOR_TEXTO, anchor="w")
        self._codigo_mantenimiento.pack(anchor="w")
        self._datos_mantenimiento = ctk.CTkLabel(self._detalle_mantenimiento, text="", font=tema.fuente("pequena"),
                                                 text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        self._datos_mantenimiento.pack(anchor="w")

        # El motivo, solo para sacar de servicio una cama libre. Si falta, se explica bajo el campo
        self._con_motivo = ctk.CTkFrame(derecha, fg_color="transparent")
        etiqueta_campo(self._con_motivo, "Motivo").pack(anchor="w", pady=(tema.ESPACIO_2, tema.ESPACIO_MINIMO))
        self._motivo = campo_texto(self._con_motivo, "Qué falla en la cama o su equipo (sin datos del paciente)")
        self._motivo.pack(fill="x")
        self._aviso_motivo = ctk.CTkLabel(self._con_motivo, text="", font=tema.fuente("pequena"),
                                          text_color=tema.COLOR_ERROR, anchor="w")
        self._motivo.bind("<Return>", lambda _e: self.mantenimiento(), add="+")
        self._motivo.bind("<KeyRelease>", lambda _e: self._motivo_editado(), add="+")

        self._fila_mantenimiento = fila = fila_acciones(derecha)
        self._boton_mantenimiento = BotonPrimario(fila, TEXTO_ELEGIR_MANTENIMIENTO, self.mantenimiento,
                                                  state="disabled")
        self._boton_mantenimiento.pack(side="left")
        return marco

    def _cama_mantenimiento_elegida(self, _id_cama=None):
        cama = self._mantenimiento.get(self._lista_mantenimiento.seleccionado())
        libre = cama is not None and cama.estado == EstadoCama.DISPONIBLE
        self._con_motivo.pack_forget()  # se vuelve a colocar, si corresponde, debajo del detalle
        if cama is None:
            self._detalle_mantenimiento.pack_forget()
            self._sin_mantenimiento.pack(anchor="w", before=self._fila_mantenimiento)
            self._boton_mantenimiento.configure(text=TEXTO_ELEGIR_MANTENIMIENTO, state="disabled")
        else:
            self._sin_mantenimiento.pack_forget()
            self._codigo_mantenimiento.configure(text=cama.codigo)
            # Sin repetir el área si se llama como el tipo («UCI · UCI»)
            partes = dict.fromkeys((type(cama).NOMBRE_CORTO, cama.area, formato.texto_estado_cama(cama.estado)))
            self._datos_mantenimiento.configure(text=" · ".join(partes))
            self._detalle_mantenimiento.pack(fill="x", before=self._fila_mantenimiento)
            texto = f"Poner {cama.codigo} fuera de servicio" if libre else f"Volver {cama.codigo} a servicio"
            self._boton_mantenimiento.configure(text=texto, state="normal")
        # El motivo escrito se conserva aunque se oculte (p. ej. al recargar tras un error); se borra al guardarlo
        if libre:
            self._con_motivo.pack(fill="x", before=self._fila_mantenimiento)

    def _activar_mantenimiento(self):
        """Enter sobre una cama: si está libre, lleva al motivo (es obligatorio); si está fuera, la devuelve."""
        cama = self._mantenimiento.get(self._lista_mantenimiento.seleccionado())
        if cama is not None and cama.estado == EstadoCama.DISPONIBLE:
            self._motivo.focus_set()
        else:
            self.mantenimiento()

    def mantenimiento(self):
        """Saca de servicio la cama libre elegida (con su motivo) o devuelve al servicio la que estaba fuera."""
        cama = self._mantenimiento.get(self._lista_mantenimiento.seleccionado())
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
            for lista in (self._lista_cola, self._lista_con_cama, self._lista_mantenimiento):
                lista.sin_lectura()
            # Sin cifra: «(0)» o «0 esperan cama» dirían que nadie espera, y no se sabe
            self._modo.cambiar_texto("espera", "Esperan cama")
            self._modo.cambiar_texto("con_cama", "Con cama")
            self._resumen.pack_forget()
            self._mostrar_elecciones()
            return
        self._mostrar(*datos)
        self._mostrar_elecciones()

    def _recargar(self, conservar: bool = False):
        """Vuelve a leer todo, sin diálogo si falla. Con `conservar`, lo elegido que siga en su lista sigue elegido."""
        listas = (self._lista_cola, self._lista_con_cama, self._lista_mantenimiento)
        elegidos = [lista.seleccionado() for lista in listas] if conservar else [None] * len(listas)
        cama_elegida = self._lista_compatibles.seleccionado() if conservar else None
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron actualizar las camas (%s).", type(error).__name__)
            return
        self._mostrar(*datos)
        for lista, elegido in zip(listas, elegidos):
            if elegido is not None:
                lista.seleccionar(elegido)
        self._paciente_elegido(self._lista_cola.seleccionado(), recarga=True)
        if cama_elegida is not None:
            self._lista_compatibles.seleccionar(cama_elegida)  # si sigue libre y compatible
        self._actualizar_asignar()
        self._con_cama_elegido()
        self._cama_mantenimiento_elegida()

    def _leer(self):
        mantenimiento = [c for c in self._camas.mapa_camas()
                         if c.estado in (EstadoCama.DISPONIBLE, EstadoCama.FUERA_SERVICIO)]
        return self._camas.cola_de_espera(), self._camas.pacientes_con_cama(), mantenimiento

    def _mostrar(self, cola, con_cama, mantenimiento):
        self._ahora = self._reloj()
        self._cola = {e.episodio.id_episodio: e for e in cola}
        self._con_cama = {p.episodio.id_episodio: p for p in con_cama}
        self._mantenimiento = {c.id_cama: c for c in mantenimiento}
        self._pintar_listas()
        self._modo.cambiar_texto("espera", f"Esperan cama ({len(cola)})")
        self._modo.cambiar_texto("con_cama", f"Con cama ({len(con_cama)})")
        libres = sum(c.estado == EstadoCama.DISPONIBLE for c in mantenimiento)
        for etiqueta, texto in zip(self._etiquetas_resumen, texto_resumen(cola, libres)):
            etiqueta.configure(text=texto)
        self._resumen.pack(fill="x", pady=(0, tema.ESPACIO_2), before=self._paneles[self._modo.valor])

    def _mostrar_elecciones(self):
        """
        Lo de la derecha de cada opción según lo elegido en su lista. Las camas compatibles se releen del paciente que
        sigue elegido y la lista repinta las que ya tenía (vaciarla antes las rehacía todas en cada recarga).
        """
        self._paciente_elegido(self._lista_cola.seleccionado(), recarga=True)
        self._con_cama_elegido()
        self._cama_mantenimiento_elegida()

    def _pintar_listas(self):
        """
        Las tres listas, la de la opción visible al instante y las otras de fondo (de a pocos, con la ventana
        respondiendo): así, al abrir otra opción, sus filas ya existen. Las que no cambiaron no se repintan.
        """
        visible = self._modo.valor
        for modo, lista, datos in (("espera", self._lista_cola, self._cola),
                                   ("con_cama", self._lista_con_cama, self._con_cama),
                                   ("mantenimiento", self._lista_mantenimiento, self._mantenimiento)):
            lista.cargar(datos.items(), de_fondo=modo != visible)

    def _cambiar_modo(self, modo: str):
        self._tarjeta.cambiar_textos(*TITULOS[modo])
        for clave, panel in self._paneles.items():
            if clave != modo:
                panel.pack_forget()
        self._paneles[modo].pack(fill="x")
        self._contenido.reacomodar()
        self._recargar(conservar=True)

    # ---- Piezas de la pantalla

    def _lista_pacientes(self, padre, crear, texto_vacio: str, al_seleccionar, al_activar=None) -> ListaSeleccion:
        lista = ListaSeleccion(padre, crear, texto_vacio, alto_elemento=FilaPaciente.ALTO, filas=self.FILAS_LISTA,
                               separacion=tema.ESPACIO_MINIMO, al_seleccionar=al_seleccionar, al_activar=al_activar,
                               fondo_elegido=tema.COLOR_ACTIVO, actualizar=self._repintar_fila)
        lista.pack(fill="x")
        return lista

    def _repintar_fila(self, fila, dato):
        """Una recarga repinta las filas que siguen en la lista en vez de rehacerlas."""
        if isinstance(fila, FilaCola):
            fila.mostrar(dato, self._ahora)
        else:
            fila.mostrar(dato)
