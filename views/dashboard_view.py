"""
Tablero de camas: la pantalla de inicio de todos los roles (diseño aprobado en docs/diseno/tablero_*.png).

Muestra 4 indicadores, la matriz de camas por tipo y quién espera cama. Solo lee: se actualiza al abrirse y cada
30 segundos. Si una actualización falla, conserva lo último que mostró y avisa a la ventana principal.
"""
import logging
from collections.abc import Callable
from datetime import date, datetime

import customtkinter as ctk

from models.estados import EstadoCama
from models.excepciones import SigtacError
from models.permisos import Permiso
from models.triaje import excede_plazo
from views import formato, tema
from views.componentes import InsigniaNivel, MatrizCamas, Tarjeta, TarjetaKPI, mostrar_error

logger = logging.getLogger(__name__)

NADIE_ESPERA = "Nadie espera cama."


class DashboardView(ctk.CTkFrame):
    TITULO = "Tablero de camas"
    SUBTITULO = "Estado de la guardia en este momento"
    INTERVALO_MS = 30_000
    FILAS_COLA = 3          # pacientes visibles en la cola; el resto se resume en una línea
    FILAS_COLA_BAJA = 2     # con poca altura la matriz tiene prioridad
    ALTO_BAJO = 700         # alto (lógico) de la vista por debajo del cual se usa FILAS_COLA_BAJA

    def __init__(self, padre, camas, sesion, reportes=None, triaje=None,
                 al_actualizar: Callable[[bool, datetime], None] | None = None, reloj=datetime.now):
        super().__init__(padre, fg_color="transparent")
        self._camas, self._sesion, self._reportes, self._triaje = camas, sesion, reportes, triaje
        self._al_actualizar = al_actualizar
        self._reloj = reloj
        self._cola = []
        self._filas_visibles = self.FILAS_COLA
        self._tarea = None
        self._construir()
        self.bind("<Configure>", self._ajustar_cola)
        self.refrescar(avisar_error=True)

    # ---- construcción

    def _construir(self):
        kpis = ctk.CTkFrame(self, fg_color="transparent")
        # Los márgenes exteriores los pone AppPrincipal: el tablero se alinea con el título del encabezado
        kpis.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        cuarto_titulo, cuarto_color = self._cuarto_indicador_titulo()
        datos = (("Camas libres", tema.COLOR_ESTADO_CAMA[EstadoCama.DISPONIBLE]),
                 ("En limpieza", tema.COLOR_ESTADO_CAMA[EstadoCama.EN_LIMPIEZA]),
                 ("Prioridad 1–2 sin cama", tema.COLOR_NIVEL[1]),
                 (cuarto_titulo, cuarto_color))
        self.kpis = []
        for i, (titulo, color) in enumerate(datos):
            tarjeta = TarjetaKPI(kpis, titulo, color)
            tarjeta.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else tema.ESPACIO_MEDIO, 0))
            kpis.grid_columnconfigure(i, weight=1, uniform="kpi")
            self.kpis.append(tarjeta)

        # La cola muestra nombres de pacientes: solo la ven los roles clínicos (permiso PACIENTES), no limpieza
        # ni administración, que no los necesitan para su trabajo (Ley 29733, datos personales de salud).
        self.muestra_cola = self._sesion.puede(Permiso.PACIENTES)
        if self.muestra_cola:
            tarjeta_cola = self._tarjeta(self, "Esperan cama", "Por prioridad y hora de llegada")
            tarjeta_cola.pack(side="bottom", fill="x")
            self._filas = ctk.CTkFrame(tarjeta_cola, fg_color="transparent")
            self._filas.pack(fill="x", padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO))

        mapa = self._tarjeta(self, "Matriz de camas", "Estado de cada cama por tipo", leyenda=True)
        mapa.pack(fill="both", expand=True, pady=tema.ESPACIO_MEDIO if self.muestra_cola else (tema.ESPACIO_MEDIO, 0))
        self.matriz = MatrizCamas(mapa)
        self.matriz.pack(fill="both", expand=True, padx=2, pady=(0, 2))

    def _tarjeta(self, padre, titulo, subtitulo, leyenda=False):
        tarjeta = Tarjeta(padre, titulo, subtitulo)
        if leyenda:
            caja = ctk.CTkFrame(tarjeta.cabecera, fg_color="transparent")
            caja.pack(side="right")
            for estado in EstadoCama:
                ctk.CTkFrame(caja, width=14, height=10, corner_radius=3, fg_color="transparent", border_width=1,
                             border_color=tema.COLOR_ESTADO_CAMA[estado]).pack(side="left", padx=(12, 5))
                ctk.CTkLabel(caja, text=estado.value.capitalize(), font=tema.fuente("pequena"),
                             text_color=tema.COLOR_TEXTO_SECUNDARIO).pack(side="left")
            ctk.CTkFrame(tarjeta, height=1, fg_color=tema.COLOR_DIVISOR, corner_radius=0).pack(fill="x", padx=1)
        return tarjeta

    def _cuarto_indicador_titulo(self):
        """El cuarto indicador depende del rol: la espera promedio pide REPORTES; si no, lo que el rol sí ve."""
        if self._reportes is not None and self._sesion.puede(Permiso.REPORTES):
            return "Espera de cama", tema.COLOR_PRIMARIO
        if self._triaje is not None and self._sesion.puede(Permiso.TRIAJE):
            return "Esperan triaje", tema.COLOR_PRIMARIO
        return "Fuera de servicio", tema.COLOR_ESTADO_CAMA[EstadoCama.FUERA_SERVICIO]

    # ---- datos

    def refrescar(self, avisar_error: bool = False):
        """Lee de nuevo camas y colas. Un error de una actualización automática no abre un diálogo cada 30 s."""
        try:
            camas = self._camas.mapa_camas()
            cola = self._camas.cola_de_espera()
            cuarto = self._cuarto_indicador_valor(camas)
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudo actualizar el tablero (%s).", type(error).__name__)
            if avisar_error:
                mostrar_error(self, error)
            self._avisar(False)
            self._programar()
            return
        self._mostrar_indicadores(camas, cola, cuarto)
        self.matriz.cargar(camas)
        self._cola = cola
        self._mostrar_cola()
        self._avisar(True)
        self._programar()

    def _cuarto_indicador_valor(self, camas):
        if self._reportes is not None and self._sesion.puede(Permiso.REPORTES):
            hoy = date.today()
            minutos = self._reportes.indicadores(hoy, hoy).espera_cama_min
            if minutos is None:
                return None, "sin datos de hoy"
            return formato.texto_minutos(round(minutos), con_cero=False), "hoy"
        if self._triaje is not None and self._sesion.puede(Permiso.TRIAJE):
            return str(len(self._triaje.cola_de_triaje())), "por evaluar"
        fuera = sum(c.estado == EstadoCama.FUERA_SERVICIO for c in camas)
        return str(fuera), "camas"

    def _mostrar_indicadores(self, camas, cola, cuarto):
        en_servicio = [c for c in camas if c.estado != EstadoCama.FUERA_SERVICIO]
        libres = sum(c.estado == EstadoCama.DISPONIBLE for c in camas)
        limpieza = sum(c.estado == EstadoCama.EN_LIMPIEZA for c in camas)
        urgentes = sum(entrada.nivel in (1, 2) for entrada in cola)
        disponible = formato.porcentaje(libres, len(en_servicio))
        self.kpis[0].mostrar(f"{libres} / {len(en_servicio)}", f"{disponible} disponible")
        self.kpis[1].mostrar(str(limpieza), "por confirmar")
        self.kpis[2].mostrar(str(urgentes), "requieren cama ya" if urgentes else "ninguno")
        self.kpis[3].mostrar(*cuarto)

    def _mostrar_cola(self):
        if not self.muestra_cola:
            return
        for hijo in self._filas.winfo_children():
            hijo.destroy()
        if not self._cola:
            ctk.CTkLabel(self._filas, text=NADIE_ESPERA, font=tema.fuente("normal"),
                         text_color=tema.COLOR_TEXTO_SECUNDARIO, height=40).pack(anchor="w")
            return
        ahora = self._reloj()
        for entrada in self._cola[:self._filas_visibles]:
            self._fila(entrada, ahora)
        restantes = len(self._cola) - self._filas_visibles
        if restantes > 0:
            ctk.CTkFrame(self._filas, height=1, fg_color=tema.COLOR_DIVISOR, corner_radius=0).pack(fill="x")
            texto = "1 paciente más en espera" if restantes == 1 else f"{restantes} pacientes más en espera"
            ctk.CTkLabel(self._filas, text=texto, font=tema.fuente("pequena"), text_color=tema.COLOR_TEXTO_SECUNDARIO,
                         height=28).pack(anchor="w")

    def _fila(self, entrada, ahora):
        ctk.CTkFrame(self._filas, height=1, fg_color=tema.COLOR_DIVISOR, corner_radius=0).pack(fill="x")
        fila = ctk.CTkFrame(self._filas, fg_color="transparent", height=48)
        fila.pack(fill="x")
        fila.grid_propagate(False)
        fila.grid_rowconfigure(0, weight=1)
        fila.grid_columnconfigure(1, minsize=230)
        fila.grid_columnconfigure(2, weight=1)
        nivel = entrada.nivel
        insignia = InsigniaNivel(fila)
        insignia.mostrar(nivel)
        insignia.grid(row=0, column=0, padx=(0, tema.ESPACIO_MEDIO))
        persona = ctk.CTkFrame(fila, fg_color="transparent")
        persona.grid(row=0, column=1, sticky="w", padx=(0, tema.ESPACIO_2))
        paciente = entrada.paciente
        ctk.CTkLabel(persona, text=formato.nombre_corto(paciente) if paciente else "Paciente sin datos",
                     font=tema.fuente("fuerte"), text_color=tema.COLOR_TEXTO, height=17).pack(anchor="w")
        ctk.CTkLabel(persona, text=formato.documento_enmascarado(paciente) if paciente else "",
                     font=tema.fuente("pequena"), text_color=tema.COLOR_TEXTO_SECUNDARIO, height=15).pack(anchor="w")
        ctk.CTkLabel(fila, text=entrada.episodio.motivo_consulta, font=tema.fuente("normal"),
                     text_color=tema.COLOR_TEXTO, anchor="w").grid(row=0, column=2, sticky="w")
        minutos = formato.minutos_desde(entrada.episodio.fecha_ingreso, ahora)
        tarde = nivel is not None and excede_plazo(nivel, minutos)
        ctk.CTkLabel(fila, text=formato.texto_minutos(minutos), width=80, anchor="e",
                     font=tema.fuente("fuerte" if tarde else "pequena"),
                     text_color=tema.COLOR_ERROR if tarde else tema.COLOR_TEXTO_SECUNDARIO).grid(
            row=0, column=3, padx=tema.ESPACIO_MEDIO)
        ctk.CTkLabel(fila, text=formato.texto_plazo(nivel) if nivel else "Sin triaje", width=112, height=26,
                     corner_radius=tema.RADIO_CONTROL, fg_color=tema.COLOR_ACTIVO, font=tema.fuente("etiqueta"),
                     text_color=tema.COLOR_ETIQUETA).grid(row=0, column=4)

    def _ajustar_cola(self, evento):
        visibles = self.FILAS_COLA_BAJA if evento.height / tema.escala(self) < self.ALTO_BAJO else self.FILAS_COLA
        if visibles != self._filas_visibles:
            self._filas_visibles = visibles
            self._mostrar_cola()

    # ---- ciclo de actualización

    def _avisar(self, correcto: bool):
        if self._al_actualizar is not None:
            self._al_actualizar(correcto, self._reloj())

    def _programar(self):
        if self._tarea is not None:
            self.after_cancel(self._tarea)
        self._tarea = self.after(self.INTERVALO_MS, self.refrescar)

    def destroy(self):
        if self._tarea is not None:
            self.after_cancel(self._tarea)
            self._tarea = None
        super().destroy()
