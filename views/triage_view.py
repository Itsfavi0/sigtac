"""
Triaje, en un solo flujo (docs/diseno/BRIEF.md §4): se elige o se registra al paciente, se toman sus signos vitales
y sus síntomas, y se confirma o se reclasifica el nivel que sugiere el sistema.

A la izquierda, el formulario en tres pasos; a la derecha, el panel de clasificación, siempre a la vista. La
sugerencia se calcula sola en cuanto los 6 signos son válidos, y se recalcula con cada cambio.

Al confirmar, la pantalla llama en orden a registrar o buscar al paciente → abrir su episodio → registrar el triaje.
Son operaciones separadas: si falla el triaje, el paciente ya quedó en «En cola», y la pantalla recuerda lo que ya
se hizo para que el reintento no lo repita.
"""
import logging
from datetime import datetime

import customtkinter as ctk

from models.excepciones import SigtacError
from models.triaje import SignosVitales, Triaje
from views import formato, tema
from views.componentes import (BotonPrimario, BotonSecundario, CamposDocumento, CamposPaciente, FichaPaciente,
                               InsigniaNivel, Selector, TablaDatos, Tarjeta, campo_texto, casilla, etiqueta_campo,
                               lista_opciones, marcar_error, marcar_foco, mostrar_error, mostrar_info, texto_nivel)
from views.componentes.campos import (campo_en_rejilla, leer_campo, leer_opcion, limpiar_al_corregir, lista_en_rejilla,
                                      sin_error)
from views.componentes.paciente import SEXOS
from views.componentes.tabla import ALTO_FILA

logger = logging.getLogger(__name__)

# Los 6 signos, en el orden del formulario: clave del controlador → (nombre, unidad, admite decimales).
# Los rangos admitidos no se escriben aquí: se leen de SignosVitales.RANGOS (el modelo los valida).
SIGNOS = {
    "pa_sis": ("PA sistólica", "mmHg", False),
    "pa_dia": ("PA diastólica", "mmHg", False),
    "fc": ("FC", "lpm", False),
    "fr": ("FR", "rpm", False),
    "temp": ("Temperatura", "°C", True),
    "sato2": ("SatO₂", "%", False),
}
NIVELES = (1, 2, 3, 4, 5)

SIN_SUGERENCIA = "Complete los signos vitales para ver la sugerencia."
NADIE_ESPERA_TRIAJE = "Nadie espera triaje."
AVISO_BUSCAR = "Busque el documento. Si el paciente no está registrado, aquí mismo se registra."
NO_REGISTRADO = "No hay un paciente con ese documento: complete sus datos para registrarlo."
TEXTO_CONFIRMAR = "Confirmar nivel"
TEXTO_SIN_SIGNOS = "Complete los signos vitales"   # el botón deshabilitado dice por qué no responde
TEXTO_RECLASIFICAR = "Reclasificar"
TEXTO_CANCELAR_RECLASIFICACION = "Cancelar reclasificación"


def rango_admitido(clave: str) -> str:
    """«20–300»: el rango que el modelo admite para ese signo (SignosVitales.RANGOS)."""
    minimo, maximo = SignosVitales.RANGOS[clave]
    return f"{minimo:g}–{maximo:g}"


def texto_faltan(faltan: int) -> str:
    """Lo que dice el botón mientras la justificación no llega al mínimo de RN-10."""
    return f"Faltan {faltan} caracteres (mínimo {Triaje.MIN_JUSTIFICACION})"


class TriageView(ctk.CTkFrame):
    ANCHO_PANEL = 320      # el panel de clasificación, fijo; el formulario toma el resto
    LADO_INSIGNIA = 48     # el nivel sugerido, lo más visible del panel
    ESPERA_MS = 300        # pausa al escribir antes de recalcular la sugerencia
    FILAS_COLA = 5         # filas visibles de la cola de triaje (más se desplazan dentro de la tabla)
    # Columnas de la cola: caben en el formulario a 1093×614 sin desplazamiento horizontal (brief, «Espacio útil»)
    COLUMNAS_COLA = (("Llegada", 64), ("Paciente", 144), ("Motivo", 160), ("Espera", 72))

    def __init__(self, padre, pacientes, triaje, reloj=datetime.now):
        super().__init__(padre, fg_color="transparent")
        self._pacientes, self._triaje, self._reloj = pacientes, triaje, reloj
        self._sugerencia = None
        self._reclasificando = False
        self._buscado = None       # (tipo, número) del documento buscado, para saber si se editó después
        self._documento_con_error = None  # (tipo, número) del documento rechazado por mal escrito
        self._paciente = None      # el paciente buscado o ya registrado en este intento
        self._id_episodio = None   # el episodio ya abierto en este intento, si el triaje falló después
        self._seguros = {}         # nombre del seguro → id_seguro
        self._casillas = {}        # id_sintoma → casilla
        self._tarea = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # El formulario se desplaza en vertical si no cabe (1093×614); el panel no se mueve. Entre los dos queda la
        # barra de desplazamiento, con ESPACIO_MINIMO a cada lado.
        self._formulario = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self._formulario.grid(row=0, column=0, sticky="nsew", padx=(0, tema.ESPACIO_MINIMO))
        self._crear_paso_paciente()
        self._crear_paso_signos()
        self._crear_paso_sintomas()
        self._crear_panel().grid(row=0, column=1, sticky="ns")

        self._cargar_datos()
        self._mostrar_sugerencia(None)
        self._tarea_foco = self.after_idle(self._documento.enfocar)

    # ---- Paso 1: el paciente

    def _crear_paso_paciente(self):
        tarjeta = self._seccion("1. Paciente", "Búsquelo por su documento o elíjalo de la cola")
        self._modo = Selector(tarjeta.cabecera, [("nuevo", "Nuevo"), ("cola", "En cola")], self._cambiar_modo)
        self._modo.pack(side="right")
        cuerpo = self._cuerpo(tarjeta)

        self._nuevo = ctk.CTkFrame(cuerpo, fg_color="transparent")
        self._identidad = Selector(self._nuevo, [("documento", "Con documento"), ("nn", "Sin identificar")],
                                   self._cambiar_identidad)
        self._identidad.pack(anchor="w", pady=(0, tema.ESPACIO_2))
        self._identificacion = ctk.CTkFrame(self._nuevo, fg_color="transparent")
        self._identificacion.pack(fill="x")
        self._con_documento = self._crear_con_documento(self._identificacion)
        self._sin_documento = self._crear_sin_documento(self._identificacion)
        self._con_documento.pack(fill="x")
        self._motivo = self._campo(self._nuevo, "Motivo de consulta", "Por qué acude a emergencia")
        self._enter_confirma(self._motivo)

        self._en_cola = ctk.CTkFrame(cuerpo, fg_color="transparent", height=ALTO_FILA * (self.FILAS_COLA + 1))
        self._en_cola.pack_propagate(False)
        self._tabla = TablaDatos(self._en_cola, self.COLUMNAS_COLA, NADIE_ESPERA_TRIAJE)
        self._tabla.pack(fill="both", expand=True)
        self._nuevo.pack(fill="x")

    def _crear_con_documento(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        fila = ctk.CTkFrame(marco, fg_color="transparent")
        fila.pack(fill="x")
        self._documento = CamposDocumento(fila)
        self._documento.pack(side="left", fill="x", expand=True)
        BotonSecundario(fila, "Buscar", self.buscar).pack(side="left", anchor="s", padx=(tema.ESPACIO, 0))
        self._documento.campo_numero.bind("<Return>", self.buscar, add="+")
        self._documento.campo_numero.bind("<KeyRelease>", self._documento_editado, add="+")

        self._resultado = ctk.CTkFrame(marco, fg_color="transparent")
        self._resultado.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        # Bajo el documento: la indicación, o por qué no se pudo buscar (en el color de error)
        self._aviso = ctk.CTkLabel(self._resultado, text=AVISO_BUSCAR, font=tema.fuente("pequena"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w", justify="left")
        self._ficha = FichaPaciente(self._resultado)

        self._registro = ctk.CTkFrame(self._resultado, fg_color="transparent")
        ctk.CTkLabel(self._registro, text=NO_REGISTRADO, font=tema.fuente("pequena"),
                     text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w").pack(anchor="w")
        self._datos = CamposPaciente(self._registro)
        self._datos.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        for campo in self._datos.entradas:
            self._enter_confirma(campo)
        self._mostrar_aviso()
        return marco

    def _crear_sin_documento(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        self._sexo_nn = lista_en_rejilla(marco, "Sexo", list(SEXOS), 0, 0)
        self._edad_nn = campo_en_rejilla(marco, "Edad aparente (años)", 0, 1)
        self._seguro_nn = lista_en_rejilla(marco, "Seguro", [], 0, 2)
        marco.grid_columnconfigure((0, 1, 2), weight=1, uniform="nn")
        self._enter_confirma(self._edad_nn)
        limpiar_al_corregir(self._sexo_nn, self._edad_nn, self._seguro_nn)
        return marco

    def _limpiar_errores_paciente(self):
        """Al cambiar de modo, los campos del paciente que quedan ocultos o vuelven a usarse no conservan el rojo."""
        for campo in (self._documento.campo_numero, self._sexo_nn, self._edad_nn, self._seguro_nn):
            sin_error(campo)
        self._datos.limpiar_errores()
        self._documento_con_error = None

    def _cambiar_modo(self, modo: str):
        self._olvidar_intento()
        self._limpiar_errores_paciente()
        self._mostrar_aviso()
        if modo == "cola":
            self._nuevo.pack_forget()
            self._en_cola.pack(fill="x")
        else:
            self._en_cola.pack_forget()
            self._nuevo.pack(fill="x")

    def _cambiar_identidad(self, identidad: str):
        self._olvidar_intento()
        self._limpiar_errores_paciente()
        self._mostrar_aviso()
        self._con_documento.pack_forget()
        self._sin_documento.pack_forget()
        (self._sin_documento if identidad == "nn" else self._con_documento).pack(fill="x")

    def buscar_documento(self, tipo, numero: str):
        """Empieza un triaje nuevo con ese documento ya buscado (lo usa Pacientes: «Registrarlo en Triaje»)."""
        self._modo.elegir("nuevo")
        self._identidad.elegir("documento")
        self._documento.fijar(tipo, numero)
        self.buscar()

    def buscar(self, _evento=None):
        """Busca el documento: si el paciente existe muestra su ficha; si no, los campos para registrarlo."""
        tipo, numero = self._documento.valores()
        try:
            paciente = self._pacientes.buscar_por_documento(tipo.value, numero)
        except ValueError as error:
            # El documento está mal escrito: se señala junto al campo, sin diálogo (como un signo inválido)
            marcar_error(self._documento.campo_numero)
            self._documento_con_error = (tipo, numero)
            self._mostrar_aviso(str(error), error=True)
            return "break"
        except SigtacError as error:
            # La BD no respondió: no es culpa del documento, que queda como estaba
            mostrar_error(self, error)
            return "break"
        marcar_error(self._documento.campo_numero, False)
        self._documento_con_error = None
        self._olvidar_intento()
        self._buscado = (tipo, numero.strip())
        self._paciente = paciente
        if paciente is None:
            self._mostrar_resultado(self._registro)
            self._datos.enfocar()
        else:
            self._ficha.mostrar(paciente)
            self._mostrar_resultado(self._ficha)
        return "break"

    def _mostrar_aviso(self, texto: str = AVISO_BUSCAR, error: bool = False):
        self._aviso.configure(text=texto, text_color=tema.COLOR_ERROR if error else tema.COLOR_TEXTO_SECUNDARIO)
        self._mostrar_resultado(self._aviso)

    def _mostrar_resultado(self, cual):
        for parte in (self._aviso, self._ficha, self._registro):
            parte.pack_forget()
        cual.pack(fill="x")

    def _documento_editado(self, _evento=None):
        """
        Si el documento cambió después de buscarlo, la ficha o el registro ya no le corresponden; y si estaba marcado
        como inválido, el rojo y su explicación se van. Se compara el texto: soltar el Enter que buscó no lo cambia.
        """
        if self._documento_con_error is not None and self._documento.valores() != self._documento_con_error:
            self._documento_con_error = None
            marcar_error(self._documento.campo_numero, False)
            self._mostrar_aviso()
        if self._buscado is not None:
            tipo, numero = self._documento.valores()
            if (tipo, numero.strip()) != self._buscado:
                self._olvidar_intento()
                self._mostrar_aviso()

    def _olvidar_intento(self):
        self._buscado = self._paciente = self._id_episodio = None

    # ---- Paso 2: signos vitales

    def _crear_paso_signos(self):
        tarjeta = self._seccion("2. Signos vitales", "Los 6 son obligatorios; la sugerencia se calcula sola")
        cuerpo = self._cuerpo(tarjeta)
        self._campos_signos = {}
        for i, (clave, (nombre, unidad, _decimales)) in enumerate(SIGNOS.items()):
            campo = campo_en_rejilla(cuerpo, f"{nombre} ({unidad})", i // 3, i % 3, rango_admitido(clave))
            campo.bind("<KeyRelease>", self._programar_sugerencia, add="+")
            self._enter_confirma(campo)
            self._campos_signos[clave] = campo
        cuerpo.grid_columnconfigure((0, 1, 2), weight=1, uniform="signos")
        # El primer signo que no se puede usar, escrito junto a los campos (no solo el borde rojo)
        self._aviso_signos = ctk.CTkLabel(cuerpo, text="", font=tema.fuente("pequena"), text_color=tema.COLOR_ERROR,
                                          anchor="w")
        self._aviso_signos.grid(row=2, column=0, columnspan=3, sticky="w", pady=(tema.ESPACIO, 0))
        self._aviso_signos.grid_remove()  # solo ocupa lugar cuando hay algo que decir

    def leer_signos(self) -> dict | None:
        """
        Los 6 signos como números, o None si falta alguno o alguno no se puede usar. Cada campo inválido queda con
        el borde de error, y el primero se explica bajo los campos. Un campo vacío no es un error: aún no se midió.
        """
        signos, problema = {}, None
        for clave, campo in self._campos_signos.items():
            nombre, _unidad, decimales = SIGNOS[clave]
            texto = campo.get()
            if not texto.strip():
                marcar_error(campo, False)
                continue
            try:
                valor = formato.leer_numero(texto, nombre, decimales)
                minimo, maximo = SignosVitales.RANGOS[clave]
                if not minimo <= valor <= maximo:
                    raise ValueError(f"{nombre} fuera del rango admitido ({rango_admitido(clave)}).")
            except ValueError as error:
                marcar_error(campo)
                problema = problema or str(error)
                continue
            marcar_error(campo, False)
            signos[clave] = valor
        self._avisar_signos(problema)
        return signos if len(signos) == len(SIGNOS) else None

    def _avisar_signos(self, problema: str | None):
        self._aviso_signos.configure(text=problema or "")
        if problema:
            self._aviso_signos.grid()
        else:
            self._aviso_signos.grid_remove()

    # ---- Paso 3: síntomas

    def _crear_paso_sintomas(self):
        tarjeta = self._seccion("3. Síntomas", "Marque los que presenta")
        self._lista_sintomas = self._cuerpo(tarjeta)
        self._lista_sintomas.grid_columnconfigure((0, 1), weight=1, uniform="sintomas")

    def _mostrar_sintomas(self, sintomas):
        for i, sintoma in enumerate(sintomas):
            caja = casilla(self._lista_sintomas, sintoma.nombre, self._programar_sugerencia)
            caja.grid(row=i // 2, column=i % 2, sticky="w", pady=(0 if i < 2 else tema.ESPACIO, 0))
            self._casillas[sintoma.id_sintoma] = caja
        if not sintomas:
            ctk.CTkLabel(self._lista_sintomas, text="No hay síntomas en el catálogo.", font=tema.fuente("normal"),
                         text_color=tema.COLOR_TEXTO_SECUNDARIO).grid(row=0, column=0, sticky="w")

    def sintomas_elegidos(self) -> list[int]:
        return [id_sintoma for id_sintoma, caja in self._casillas.items() if caja.get()]

    # ---- Panel de clasificación

    def _crear_panel(self) -> Tarjeta:
        panel = Tarjeta(self, "Clasificación", "El sistema sugiere; usted decide", width=self.ANCHO_PANEL)
        panel.pack_propagate(False)
        ancho_texto = self.ANCHO_PANEL - 2 * tema.ESPACIO_2

        # Se crea en el orden de lectura (que es el orden de Tab): el contenido y después las acciones. Se coloca en
        # otro: las acciones primero, al pie, para que en una ventana baja se recorte el contenido y no los botones.
        cuerpo = ctk.CTkFrame(panel, fg_color="transparent")
        self._vacio = ctk.CTkLabel(cuerpo, text=SIN_SUGERENCIA, font=tema.fuente("normal"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, wraplength=ancho_texto, justify="left",
                                   anchor="w")
        self._detalle = ctk.CTkFrame(cuerpo, fg_color="transparent")
        nivel = ctk.CTkFrame(self._detalle, fg_color="transparent")
        nivel.pack(fill="x", pady=(0, tema.ESPACIO_2))
        self._insignia = InsigniaNivel(nivel, lado=self.LADO_INSIGNIA)
        self._insignia.pack(side="left", padx=(0, tema.ESPACIO_MEDIO))
        textos = ctk.CTkFrame(nivel, fg_color="transparent")
        textos.pack(side="left")
        self._texto_nivel = ctk.CTkLabel(textos, text="", font=tema.fuente("subtitulo"), text_color=tema.COLOR_TEXTO,
                                         anchor="w")
        self._texto_nivel.pack(anchor="w")
        self._plazo = ctk.CTkLabel(textos, text="", font=tema.fuente("pequena"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        self._plazo.pack(anchor="w")
        etiqueta_campo(self._detalle, "Criterios").pack(anchor="w", pady=(0, tema.ESPACIO_MINIMO))
        self._criterios = ctk.CTkFrame(self._detalle, fg_color="transparent")
        self._criterios.pack(fill="x")
        self._protocolo = ctk.CTkLabel(self._detalle, text="", font=tema.fuente("pequena"),
                                       text_color=tema.COLOR_TEXTO_SECUNDARIO, wraplength=ancho_texto,
                                       justify="left", anchor="w")
        self._protocolo.pack(anchor="w", pady=(tema.ESPACIO, 0))

        # Reclasificar (RN-10): el nivel final y la justificación, solo cuando se pide. Lo que falta para el mínimo
        # lo dice el botón principal, que siempre está a la vista.
        self._reclasificacion = ctk.CTkFrame(self._detalle, fg_color="transparent")
        etiqueta_campo(self._reclasificacion, "Nivel final").pack(anchor="w", pady=(0, tema.ESPACIO_MINIMO))
        self._nivel_final = lista_opciones(self._reclasificacion, [texto_nivel(n) for n in NIVELES],
                                           command=lambda _valor: self._actualizar_acciones())
        self._nivel_final.pack(fill="x", pady=(0, tema.ESPACIO_2))
        etiqueta_campo(self._reclasificacion, "Justificación").pack(anchor="w", pady=(0, tema.ESPACIO_MINIMO))
        self._justificacion = marcar_foco(ctk.CTkTextbox(
            self._reclasificacion, height=tema.ALTO_CONTROL * 2, corner_radius=tema.RADIO_CONTROL, border_width=1,
            font=tema.fuente("normal"), fg_color=tema.COLOR_SUPERFICIE, border_color=tema.COLOR_BORDE_CAMPO,
            text_color=tema.COLOR_TEXTO, wrap="word"))
        self._justificacion.pack(fill="x")
        self._justificacion.bind("<KeyRelease>", lambda _e: self._actualizar_acciones(), add="+")
        # En un cuadro de texto Tab escribiría un tabulador: aquí pasa al control siguiente, como en los campos
        caja = self._justificacion._textbox
        caja.bind("<Tab>", lambda _e: self._enfocar(caja.tk_focusNext()), add="+")
        caja.bind("<Shift-Tab>", lambda _e: self._enfocar(caja.tk_focusPrev()), add="+")

        acciones = ctk.CTkFrame(panel, fg_color="transparent")
        self._boton_confirmar = BotonPrimario(acciones, TEXTO_CONFIRMAR, self.confirmar)
        self._boton_confirmar.pack(fill="x")
        self._boton_reclasificar = BotonSecundario(acciones, TEXTO_RECLASIFICAR, self.alternar_reclasificacion)
        self._boton_reclasificar.pack(fill="x", pady=(tema.ESPACIO, 0))
        acciones.pack(side="bottom", fill="x", padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))
        cuerpo.pack(fill="both", expand=True, padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))
        return panel

    @staticmethod
    def _enfocar(widget) -> str:
        if widget is not None:
            widget.focus_set()
        return "break"

    def _programar_sugerencia(self, _evento=None):
        """Recalcula después de una pausa al escribir, no en cada tecla."""
        if self._tarea is not None:
            self.after_cancel(self._tarea)
        self._tarea = self.after(self.ESPERA_MS, self.calcular_sugerencia)

    def calcular_sugerencia(self):
        if self._tarea is not None:
            self.after_cancel(self._tarea)
            self._tarea = None
        signos = self.leer_signos()
        if signos is None:
            self._mostrar_sugerencia(None)
            return
        try:
            sugerencia = self._triaje.sugerir(signos, self.sintomas_elegidos())
        except (SigtacError, ValueError) as error:
            # Se recalcula con cada pausa al escribir: un error se lee en el panel, no en un diálogo tras otro
            logger.warning("No se pudo calcular la sugerencia (%s).", type(error).__name__)
            self._mostrar_sugerencia(None, aviso=str(error))
            return
        self._mostrar_sugerencia(sugerencia)

    def _mostrar_sugerencia(self, sugerencia, aviso: str | None = None):
        """
        Sin sugerencia (falta un signo, o uno es inválido mientras se corrige) se oculta el detalle, pero una
        reclasificación abierta y su justificación se conservan: vuelven a verse con la sugerencia.
        """
        self._sugerencia = sugerencia
        if sugerencia is None:
            self._detalle.pack_forget()
            self._vacio.configure(text=aviso or SIN_SUGERENCIA,
                                  text_color=tema.COLOR_ERROR if aviso else tema.COLOR_TEXTO_SECUNDARIO)
            self._vacio.pack(fill="x")
        else:
            self._vacio.pack_forget()
            self._insignia.mostrar(sugerencia.nivel)
            self._texto_nivel.configure(text=f"Nivel {texto_nivel(sugerencia.nivel)}")
            self._plazo.configure(text=formato.texto_plazo(sugerencia.nivel))
            for hijo in self._criterios.winfo_children():
                hijo.destroy()
            for criterio in sugerencia.criterios:
                ctk.CTkLabel(self._criterios, text=f"• {criterio}", font=tema.fuente("normal"),
                             text_color=tema.COLOR_TEXTO, anchor="w", justify="left",
                             wraplength=self.ANCHO_PANEL - 2 * tema.ESPACIO_2).pack(anchor="w")
            self._protocolo.configure(text=sugerencia.protocolo)
            self._detalle.pack(fill="x")
        self._actualizar_acciones()

    def alternar_reclasificacion(self):
        """Abre o cierra la elección del nivel final y la justificación. Cerrarla vuelve a la sugerencia."""
        if not self._reclasificando and self._sugerencia is None:
            return
        self._reclasificando = not self._reclasificando
        if self._reclasificando:
            self._nivel_final.set(texto_nivel(self._sugerencia.nivel))
            self._protocolo.pack_forget()  # deja lugar a la justificación; los criterios siguen a la vista
            self._reclasificacion.pack(fill="x", pady=(tema.ESPACIO_2, 0))
            self._nivel_final.focus_set()
        else:
            self._reclasificacion.pack_forget()
            self._justificacion.delete("1.0", "end")
            self._protocolo.pack(anchor="w", pady=(tema.ESPACIO, 0))
        self._actualizar_acciones()

    def nivel_final(self) -> int | None:
        """El nivel elegido al reclasificar; None si no se está reclasificando."""
        if not self._reclasificando:
            return None
        return next(n for n in NIVELES if texto_nivel(n) == self._nivel_final.get())

    def _texto_justificacion(self) -> str:
        return self._justificacion.get("1.0", "end").strip()

    def _actualizar_acciones(self):
        """
        El botón principal dice qué va a registrar («Confirmar nivel 2»). Deshabilitado dice por qué: faltan los
        signos, o faltan caracteres de la justificación (RN-10). Así no parece activo sin responder.
        """
        hay_sugerencia = self._sugerencia is not None
        self._boton_reclasificar.configure(
            text=TEXTO_CANCELAR_RECLASIFICACION if self._reclasificando else TEXTO_RECLASIFICAR,
            state="normal" if hay_sugerencia else "disabled")
        if not hay_sugerencia:
            self._boton_confirmar.configure(text=TEXTO_SIN_SIGNOS, state="disabled")
            return
        nivel = self.nivel_final() or self._sugerencia.nivel
        faltan = Triaje.MIN_JUSTIFICACION - len(self._texto_justificacion())
        if nivel != self._sugerencia.nivel and faltan > 0:
            self._boton_confirmar.configure(text=texto_faltan(faltan), state="disabled")
        else:
            self._boton_confirmar.configure(text=f"{TEXTO_CONFIRMAR} {nivel}", state="normal")

    # ---- Registrar

    def confirmar(self, _evento=None):
        """Registra el triaje con el nivel que muestra el botón principal (también con Enter en los campos)."""
        if self._tarea is not None:
            # Un cambio todavía sin recalcular (Enter justo después de escribir): primero se recalcula, para que
            # el nivel del botón y del aviso sea el que el controlador va a guardar
            self.calcular_sugerencia()
        if self._boton_confirmar.cget("state") == "disabled":
            return "break"
        signos = self.leer_signos()
        sugerido = self._sugerencia.nivel
        nivel_final = self.nivel_final()
        justificacion = self._texto_justificacion() if nivel_final not in (None, sugerido) else None
        try:
            id_episodio = self._episodio_a_triar()
            self._triaje.registrar(id_episodio, signos, self.sintomas_elegidos(), nivel_final, justificacion)
        except (SigtacError, ValueError) as error:
            mostrar_error(self, error)
            self._recargar_cola()  # si el episodio llegó a abrirse, ya aparece «En cola»
            return "break"
        mostrar_info(self, f"Triaje registrado: nivel {texto_nivel(nivel_final or sugerido)}. "
                           "El paciente pasa a la cola de cama.")
        self.limpiar()
        self._recargar_cola()
        return "break"

    def _episodio_a_triar(self) -> int:
        """El id del episodio: el elegido en la cola, o el que se abre ahora (registrando al paciente si hace falta)."""
        if self._modo.valor == "cola":
            id_episodio = self._tabla.seleccionado()
            if id_episodio is None:
                raise ValueError("Elija en la cola al paciente que va a triar.")
            return id_episodio
        if self._id_episodio is None:
            paciente = self._paciente_a_admitir()
            self._id_episodio = self._pacientes.abrir_episodio(paciente.id_paciente, self._motivo.get()).id_episodio
        return self._id_episodio

    def _paciente_a_admitir(self):
        """El paciente buscado, o el que se registra ahora. Un dato que no se puede leer marca su campo."""
        if self._paciente is not None:
            return self._paciente
        if self._identidad.valor == "nn":
            sexo = leer_opcion(self._sexo_nn, SEXOS, "Elija el sexo del paciente.")
            edad = leer_campo(self._edad_nn, lambda texto: formato.leer_numero(texto, "La edad aparente"))
            seguro = leer_opcion(self._seguro_nn, self._seguros, "Elija el seguro del paciente.")
            self._paciente = self._pacientes.registrar_no_identificado(sexo, edad, seguro)
            return self._paciente
        tipo, numero = self._documento.valores()
        if self._buscado != (tipo, numero.strip()):
            marcar_error(self._documento.campo_numero)
            raise ValueError("Busque el documento del paciente antes de confirmar.")
        datos = self._datos.valores()
        self._paciente = self._pacientes.registrar(tipo.value, numero, datos["nombres"], datos["apellidos"],
                                                   datos["fecha_nac"], datos["sexo"], datos["id_seguro"])
        return self._paciente

    def limpiar(self):
        """Deja la pantalla lista para el siguiente paciente (después de registrar)."""
        self._olvidar_intento()
        self._documento.limpiar()
        self._limpiar_errores_paciente()
        self._mostrar_aviso()
        self._datos.limpiar()
        for campo in (self._edad_nn, self._motivo, *self._campos_signos.values()):
            campo.delete(0, "end")
            campo._activate_placeholder()  # CustomTkinter solo lo vuelve a mostrar al perder el foco
            marcar_error(campo, False)
        for lista in (self._sexo_nn, self._seguro_nn):
            lista.set("")
            marcar_error(lista, False)
        for caja in self._casillas.values():
            caja.deselect()
        if self._reclasificando:
            self.alternar_reclasificacion()
        self._avisar_signos(None)
        self._mostrar_sugerencia(None)
        self._documento.enfocar()

    # ---- Datos

    def _cargar_datos(self):
        """Seguros, síntomas y la cola, al abrir. Si la BD falla, un solo aviso; el formulario queda usable."""
        try:
            seguros = self._pacientes.listar_seguros()
            sintomas = self._triaje.listar_sintomas()
            cola = self._triaje.cola_de_triaje()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron leer los datos del triaje (%s).", type(error).__name__)
            mostrar_error(self, error)
            seguros, sintomas, cola = [], [], []
        self._seguros = {s["nombre_seguro"]: s["id_seguro"] for s in seguros}
        self._datos.cargar_seguros(seguros)
        self._seguro_nn.configure(values=list(self._seguros))
        self._mostrar_sintomas(sintomas)
        self._mostrar_cola(cola)

    def _recargar_cola(self):
        try:
            cola = self._triaje.cola_de_triaje()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudo actualizar la cola de triaje (%s).", type(error).__name__)
            return
        self._mostrar_cola(cola)

    def _mostrar_cola(self, cola):
        ahora = self._reloj()
        filas = []
        for entrada in cola:
            episodio, paciente = entrada.episodio, entrada.paciente
            filas.append((episodio.id_episodio, (
                formato.hora(episodio.fecha_ingreso),
                formato.nombre_corto(paciente) if paciente else "Paciente sin datos",
                episodio.motivo_consulta,
                formato.texto_minutos(formato.minutos_desde(episodio.fecha_ingreso, ahora)))))
        self._tabla.cargar(filas)
        self._modo.cambiar_texto("cola", f"En cola ({len(filas)})")

    # ---- Piezas de la pantalla

    def _seccion(self, titulo: str, subtitulo: str) -> Tarjeta:
        tarjeta = Tarjeta(self._formulario, titulo, subtitulo)
        # A la derecha deja lugar a la barra de desplazamiento del formulario
        tarjeta.pack(fill="x", padx=(0, tema.ESPACIO_MINIMO), pady=(0, tema.ESPACIO_MEDIO))
        return tarjeta

    @staticmethod
    def _cuerpo(tarjeta) -> ctk.CTkFrame:
        cuerpo = ctk.CTkFrame(tarjeta, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))
        return cuerpo

    def _enter_confirma(self, campo):
        campo.bind("<Return>", self.confirmar, add="+")

    @staticmethod
    def _campo(padre, etiqueta: str, placeholder: str | None = None) -> ctk.CTkEntry:
        etiqueta_campo(padre, etiqueta).pack(anchor="w", pady=(tema.ESPACIO_2, tema.ESPACIO_MINIMO))
        campo = campo_texto(padre, placeholder)
        campo.pack(fill="x")
        return campo

    def destroy(self):
        for tarea in (self._tarea, self._tarea_foco):
            if tarea is not None:
                self.after_cancel(tarea)
        self._tarea = self._tarea_foco = None
        super().destroy()
