"""
Reportes: los indicadores de un período y el estado de la guardia en este momento, para el jefe de guardia y el
administrador (permiso REPORTES). «Exportar PDF…» guarda el período que se ve en pantalla; «Ahora en la guardia» se
vuelve a leer al guardar.

- «Período» (CamposPeriodo): los atajos (Hoy / Últimos 7 días / Este mes) rellenan «Desde» y «Hasta», que también se
  escriben (dd/mm/aaaa). Al abrir se muestra el mes en curso.
- Los 4 indicadores del período: ingresos y los tiempos promedio desde el ingreso (hasta el triaje, hasta la cama y
  hasta el alta: la estancia). Encima, qué período muestran.
- «Triajes por nivel», con la reclasificación, y «Ahora en la guardia»: camas por estado, ocupación y pacientes.

Los cálculos los hace ReporteController; aquí solo se leen las fechas y se muestran los resultados. Una consulta que
falla conserva lo último que se mostró (la línea sobre los indicadores dice de qué período es) y avisa a la ventana
principal («Sin conexión»).
"""
import logging
from collections.abc import Callable
from datetime import date, datetime

import customtkinter as ctk

from models.estados import EstadoCama, EstadoEpisodio
from models.excepciones import PersistenciaError, SigtacError
from models.triaje import COLOR_POR_NIVEL
from views import formato, tema
from views.componentes import (BotonPrimario, BotonSecundario, CamposPeriodo, TablaDatos, Tarjeta, TarjetaKPI,
                               etiqueta_campo, mostrar_error, mostrar_info, pedir_ruta_pdf, texto_nivel)
from views.componentes.periodo import texto_periodo

logger = logging.getLogger(__name__)

AVISO_PROTOTIPO = "Prototipo académico: los indicadores no tienen validez clínica."
SIN_LECTURA = "No se pudieron leer los datos."
SIN_DATOS = "sin datos"
NIVELES = tuple(sorted(COLOR_POR_NIVEL))
# Los pacientes que siguen en emergencia, en el orden en que avanzan
PACIENTES = ((EstadoEpisodio.EN_ESPERA_TRIAJE, "esperan triaje"), (EstadoEpisodio.EN_ESPERA, "esperan cama"),
             (EstadoEpisodio.EN_ATENCION, "con cama"))


def nombre_archivo(desde: date, hasta: date) -> str:
    """El nombre que propone «Guardar como»: «sigtac_indicadores_2026-10-01_2026-10-31.pdf»."""
    return f"sigtac_indicadores_{desde.isoformat()}_{hasta.isoformat()}.pdf"


def texto_tiempo(minutos: float | None) -> str | None:
    """Un promedio en minutos como lo escribe el tablero («8 min», «5 h 12 min»); None si no hay dato."""
    return None if minutos is None else formato.texto_minutos(round(minutos), con_cero=False)


def cantidad(n: int, singular: str, plural: str) -> str:
    """«1 paciente», «21 pacientes»."""
    return f"{n} {singular if n == 1 else plural}"


class ReportesView(ctk.CTkFrame):
    FILAS_NIVELES = len(NIVELES)
    FILAS_CAMAS = len(EstadoCama)
    # Caben en media tarjeta a 1093×614 sin desplazamiento horizontal (brief, «Espacio útil»)
    COLUMNAS_NIVELES = (("Nivel", 128), ("Triajes", 80), ("Porcentaje", 96))
    COLUMNAS_CAMAS = (("Estado de la cama", 160), ("Camas", 80))

    def __init__(self, padre, reportes, al_actualizar: Callable[[bool, datetime], None] | None = None,
                 hoy: Callable[[], date] = date.today, reloj: Callable[[], datetime] = datetime.now):
        super().__init__(padre, fg_color="transparent")
        self._reportes, self._al_actualizar = reportes, al_actualizar
        self._hoy, self._reloj = hoy, reloj

        # Como las demás pantallas de trabajo: el contenido se desplaza en vertical si no cabe (1093×614)
        contenido = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        contenido.pack(fill="both", expand=True)
        self._crear_periodo(contenido).pack(fill="x", padx=(0, tema.ESPACIO_MINIMO))
        self._crear_indicadores(contenido).pack(fill="x", padx=(0, tema.ESPACIO_MINIMO))
        self._crear_detalle(contenido).pack(fill="x", padx=(0, tema.ESPACIO_MINIMO), pady=(tema.ESPACIO_MEDIO, 0))
        ctk.CTkLabel(contenido, text=AVISO_PROTOTIPO, font=tema.fuente("pequena"),
                     text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w").pack(anchor="w", pady=(tema.ESPACIO_MEDIO, 0))

        self._consultar(avisar_error=True)

    # ---- Período

    def _crear_periodo(self, padre) -> Tarjeta:
        tarjeta = Tarjeta(padre, "Período", "Días completos, ambos incluidos")
        cuerpo = ctk.CTkFrame(tarjeta, fg_color="transparent")
        cuerpo.pack(fill="x", padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))
        # Los atajos, a la derecha de la cabecera; al abrir, el mes en curso
        self.periodo = CamposPeriodo(cuerpo, lambda: self._consultar(avisar_error=True), hoy=self._hoy,
                                     cabecera=tarjeta.cabecera)
        self.periodo.pack(fill="x")
        for campo in self.periodo.entradas:
            campo.bind("<Return>", self.ver_indicadores, add="+")

        fila = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        BotonPrimario(fila, "Ver indicadores", self.ver_indicadores).pack(side="left")
        BotonSecundario(fila, "Exportar PDF…", self.exportar).pack(side="left", padx=(tema.ESPACIO, 0))
        return tarjeta

    # ---- Indicadores y detalle

    def _crear_indicadores(self, padre) -> ctk.CTkFrame:
        """Los 4 indicadores, con una línea encima que dice de qué período son (tras un fallo, del que se mostró)."""
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        self._periodo_mostrado = etiqueta_campo(marco, "")
        self._periodo_mostrado.pack(anchor="w", pady=(tema.ESPACIO_2, tema.ESPACIO_MINIMO))
        fila = ctk.CTkFrame(marco, fg_color="transparent")
        fila.pack(fill="x")
        titulos = ("Ingresos", "Espera de triaje", "Espera de cama", "Estancia")
        self.kpis = []
        for i, titulo in enumerate(titulos):
            # El marcador azul, como «Espera de cama» en el tablero: el mismo dato, el mismo marcador
            tarjeta = TarjetaKPI(fila, titulo, tema.COLOR_PRIMARIO)
            tarjeta.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else tema.ESPACIO_MEDIO, 0))
            fila.grid_columnconfigure(i, weight=1, uniform="kpi")
            self.kpis.append(tarjeta)
        return marco

    def _crear_detalle(self, padre) -> ctk.CTkFrame:
        """Las dos tarjetas lado a lado, del mismo ancho y alto, separadas como los indicadores."""
        fila = ctk.CTkFrame(padre, fg_color="transparent")
        fila.grid_columnconfigure((0, 1), weight=1, uniform="detalle")
        fila.grid_rowconfigure(0, weight=1)

        tarjeta_niveles = Tarjeta(fila, "Triajes por nivel", "Cuántos hubo de cada nivel en el período")
        tarjeta_niveles.grid(row=0, column=0, sticky="nsew")
        cuerpo = self._cuerpo(tarjeta_niveles)
        self._tabla_niveles = TablaDatos(cuerpo, self.COLUMNAS_NIVELES, SIN_LECTURA, filas=self.FILAS_NIVELES)
        self._tabla_niveles.pack(fill="x")
        self._reclasificacion = self._linea(cuerpo)

        tarjeta_guardia = Tarjeta(fila, "Ahora en la guardia", "Camas y pacientes en este momento")
        tarjeta_guardia.grid(row=0, column=1, sticky="nsew", padx=(tema.ESPACIO_MEDIO, 0))
        cuerpo = self._cuerpo(tarjeta_guardia)
        self._tabla_camas = TablaDatos(cuerpo, self.COLUMNAS_CAMAS, SIN_LECTURA, filas=self.FILAS_CAMAS)
        self._tabla_camas.pack(fill="x")
        self._ocupacion = self._linea(cuerpo)
        # En dos líneas: en media tarjeta a 1093×614, el detalle de los pacientes no cabe junto al total
        self._pacientes = ctk.CTkLabel(cuerpo, text="", font=tema.fuente("pequena"),
                                       text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w", justify="left")
        self._pacientes.pack(anchor="w", pady=(tema.ESPACIO_MINIMO, 0))
        return fila

    @staticmethod
    def _cuerpo(tarjeta: Tarjeta) -> ctk.CTkFrame:
        cuerpo = ctk.CTkFrame(tarjeta, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))
        return cuerpo

    @staticmethod
    def _linea(padre) -> ctk.CTkLabel:
        """La línea bajo una tabla con su dato principal («Reclasificados: 12 %», «Ocupación: 44 %»)."""
        linea = ctk.CTkLabel(padre, text="", font=tema.fuente("fuerte"), text_color=tema.COLOR_TEXTO, anchor="w")
        linea.pack(anchor="w", pady=(tema.ESPACIO_2, 0))
        return linea

    # ---- Acciones

    def ver_indicadores(self, _evento=None):
        """Lee el período escrito y muestra sus indicadores y el estado actual de la guardia."""
        self._consultar(avisar_error=True)
        return "break"  # que Enter no haga además lo suyo

    def exportar(self):
        """
        Muestra el período escrito (así la pantalla dice lo mismo que el PDF), pide dónde guardar el PDF y lo guarda.
        Si el período no se puede leer o la consulta falla, no se abre el diálogo.
        """
        periodo = self._consultar(avisar_error=True)
        if periodo is None:
            return
        ruta = pedir_ruta_pdf(self, nombre_archivo(*periodo))
        if ruta is None:
            return  # el usuario canceló
        try:
            guardado = self._reportes.exportar_pdf(*periodo, ruta)
        except (SigtacError, ValueError) as error:
            if isinstance(error, PersistenciaError):  # no un PDF abierto en otro programa (ReporteError)
                logger.warning("No se pudo exportar el reporte (%s).", type(error).__name__)
                self._avisar(False)
            mostrar_error(self, error)
            return
        mostrar_info(self, f"Reporte guardado en {guardado}.")

    # ---- Datos

    def _consultar(self, avisar_error: bool) -> tuple[date, date] | None:
        """
        Lee el período, consulta y muestra. Devuelve el período mostrado, o None si no se pudo: una fecha mal escrita
        queda marcada, y un período que el controlador rechaza marca las dos. Un fallo conserva lo último que se
        mostró. Con `avisar_error`, el error se muestra.
        """
        try:
            desde, hasta = self.periodo.leer()
        except ValueError as error:
            if avisar_error:
                mostrar_error(self, error)
            return None
        try:
            indicadores = self._reportes.indicadores(desde, hasta)
            estado = self._reportes.estado_actual()
        except (SigtacError, ValueError) as error:
            if isinstance(error, SigtacError):
                logger.warning("No se pudieron leer los indicadores (%s).", type(error).__name__)
                self._avisar(False)
            else:  # el período no vale como tal (la inicial después de la final, un año fuera de rango)
                self.periodo.rechazar()
            if avisar_error:
                mostrar_error(self, error)
            return None
        self._mostrar_indicadores(indicadores)
        self._mostrar_guardia(estado)
        self._avisar(True)
        return desde, hasta

    def _mostrar_indicadores(self, ind):
        self._periodo_mostrado.configure(
            text=f"{texto_periodo(ind.desde, ind.hasta)} · tiempos promedio desde el ingreso (la estancia, hasta el "
                 "alta)")
        # El valor y la nota comparten la línea: a 1093×614, «5 h 12 min» no deja lugar para una nota, y que son
        # promedios ya lo dice la línea de arriba
        self.kpis[0].mostrar(str(ind.ingresos), "paciente" if ind.ingresos == 1 else "pacientes")
        for tarjeta, minutos in zip(self.kpis[1:], (ind.espera_triaje_min, ind.espera_cama_min, ind.estancia_min)):
            tarjeta.mostrar(texto_tiempo(minutos), None if minutos is not None else SIN_DATOS)
        total = ind.total_triajes
        self._tabla_niveles.cargar([(n, (texto_nivel(n), ind.triajes_por_nivel.get(n, 0),
                                         formato.porcentaje(ind.triajes_por_nivel.get(n, 0), total)))
                                    for n in NIVELES])
        if ind.porcentaje_reclasificacion is None:
            texto = "Reclasificados: sin triajes en el período"
        else:
            porcentaje = formato.texto_porcentaje(ind.porcentaje_reclasificacion)
            texto = f"Reclasificados: {porcentaje} de {cantidad(total, 'triaje', 'triajes')}"
        self._reclasificacion.configure(text=texto)

    def _mostrar_guardia(self, estado):
        self._tabla_camas.cargar([(e, (e.value.capitalize(), estado.camas_por_estado.get(e, 0))) for e in EstadoCama])
        if estado.porcentaje_ocupacion is None:
            self._ocupacion.configure(text="Ocupación: sin camas en servicio")
        else:
            self._ocupacion.configure(text=f"Ocupación: {formato.texto_porcentaje(estado.porcentaje_ocupacion)}")
        detalle = " · ".join(f"{estado.pacientes_por_estado.get(e, 0)} {texto}" for e, texto in PACIENTES)
        total = cantidad(estado.pacientes_en_emergencia, "paciente en emergencia", "pacientes en emergencia")
        self._pacientes.configure(text=f"{total}\n{detalle}")

    def _avisar(self, correcto: bool):
        if self._al_actualizar is not None:
            self._al_actualizar(correcto, self._reloj())
