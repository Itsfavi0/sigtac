from dataclasses import dataclass
from datetime import datetime

from models.estados import EstadoEpisodio
from models.excepciones import NivelTriajeInvalidoError, ReglaNegocioError

# CATÁLOGO: SÍNTOMA
@dataclass(frozen=True)
class Sintoma:
    """Clase inmutable que representa un catálogo de síntomas con su peso clínico."""
    id_sintoma: int
    nombre: str
    peso_clinico: float

    def __post_init__(self):
        if self.peso_clinico < 0:
            raise ValueError("El peso clínico no puede ser negativo.")

# COMPONENTE: SIGNOS VITALES
class SignosVitales:
    """Objeto de valor que encapsula las mediciones de un momento dado."""

    # Rangos amplios, pensados solo para rechazar valores imposibles (errores de digitación),
    # no para decidir si un valor es clínicamente normal.
    RANGOS = {
        'pa_sis': (20, 300),
        'pa_dia': (0, 250),
        'fc': (0, 300),
        'fr': (0, 80),
        'temp': (25.0, 45.0),
        'sato2': (0, 100),
    }

    def __init__(self, pa_sis: int, pa_dia: int, fc: int, fr: int, temp: float, sato2: int, id_si: int):
        # Validaciones de integridad antes de instanciar
        valores = {'pa_sis': pa_sis, 'pa_dia': pa_dia, 'fc': fc, 'fr': fr, 'temp': temp, 'sato2': sato2}
        for nombre, valor in valores.items():
            minimo, maximo = self.RANGOS[nombre]
            if not (minimo <= valor <= maximo):
                raise ValueError(f"{nombre} fuera del rango admitido ({minimo}-{maximo}): {valor}")
        if pa_sis <= pa_dia:
            raise ValueError("La presión sistólica debe ser mayor a la diastólica.")

        self._id_si = id_si
        self._pa_sis = pa_sis
        self._pa_dia = pa_dia
        self._fc = fc
        self._fr = fr
        self._temp = temp
        self._sato2 = sato2

    @property
    def id_si(self): return self._id_si

    # Retornamos los datos como diccionario para que el Patrón Strategy los pueda leer fácilmente
    def a_diccionario(self) -> dict:
        return {
            'pa_sis': self._pa_sis,
            'pa_dia': self._pa_dia,
            'fc': self._fc,
            'fr': self._fr,
            'temp': self._temp,
            'sato2': self._sato2
        }

# TRANSACCIÓN: TRIAJE
class Triaje:
    def __init__(self, id_triaje: int, nivel_sugerido: int, id_empleado: int, fecha_hora: datetime):
        if nivel_sugerido not in range(1, 6):
            raise NivelTriajeInvalidoError("El nivel sugerido debe estar entre 1 (Rojo) y 5 (Azul).")

        self._id_triaje = id_triaje
        self._nivel_sugerido = nivel_sugerido
        self._nivel_final = nivel_sugerido  # Por defecto, el enfermero acepta la sugerencia
        self._id_empleado = id_empleado
        self._fecha_hora = fecha_hora or datetime.now()

        self._sintomas = []  # Composición: Relación de muchos a muchos
        self._justificacion = None  # Solo se llena si hay reclasificación
        self._activo = True  # Espejo de triaje.estado_registro (RN-11)

    @property
    def id_triaje(self): return self._id_triaje

    @property
    def id_empleado(self): return self._id_empleado

    @property
    def nivel_sugerido(self): return self._nivel_sugerido

    @property
    def nivel_final(self): return self._nivel_final

    @property
    def justificacion(self): return self._justificacion

    @property
    def fecha_hora(self): return self._fecha_hora

    @property
    def activo(self): return self._activo

    @property
    def es_reclasificacion(self) -> bool:
        return self._nivel_final != self._nivel_sugerido

    def agregar_sintoma(self, sintoma: Sintoma):
        self._sintomas.append(sintoma)

    def reclasificar(self, nuevo_nivel: int, justificacion: str):
        """
        RN-10: Toda reclasificación que difiera de la sugerencia
        exige una justificación escrita del profesional.

        Este método se usa antes de persistir el triaje (mientras el
        profesional confirma o corrige lo que propuso el sistema). Una
        reevaluación posterior del mismo episodio, horas después, no debe
        mutar este objeto ya guardado: debe crearse un Triaje nuevo y
        añadirse con EpisodioEmergencia.agregar_triaje(), preservando así
        el historial completo que exige RN-09.
        """
        if nuevo_nivel not in range(1, 6):
            raise NivelTriajeInvalidoError("El nivel de triaje debe estar entre 1 (Rojo) y 5 (Azul).")
        if not justificacion or len(justificacion.strip()) < 10:
            raise ValueError("Debe proporcionar una justificación médica válida (mínimo 10 caracteres).")

        self._nivel_final = nuevo_nivel
        self._justificacion = justificacion

    def anular(self):
        """RN-11: baja lógica; el triaje nunca se borra físicamente."""
        self._activo = False


#EPISODIO DE EMERGENCIA
class EpisodioEmergencia:
    """Clase principal que orquesta la visita del paciente."""

    ESTADO_EN_ESPERA_TRIAJE = EstadoEpisodio.EN_ESPERA_TRIAJE
    ESTADO_EN_ESPERA = EstadoEpisodio.EN_ESPERA
    ESTADO_EN_ATENCION = EstadoEpisodio.EN_ATENCION
    ESTADO_ALTA = EstadoEpisodio.ALTA

    def __init__(self, id_episodio: int, id_paciente: int, motivo_consulta: str, estado: str = ESTADO_EN_ESPERA_TRIAJE):
        self._id_episodio = id_episodio
        self._id_paciente = id_paciente
        self._motivo_consulta = motivo_consulta
        self._estado = EstadoEpisodio(estado)  # ValueError si el estado no existe
        self._fecha_ingreso = datetime.now()
        self._fecha_alta = None
        self._activo = True  # Espejo de episodio_emergencia.estado_registro (RN-11)

        # RN-09: Un episodio puede tener múltiples triajes (historial de reclasificaciones)
        self._historial_triajes = []
        self._signos_vitales = []

    @property
    def id_episodio(self): return self._id_episodio

    @property
    def id_paciente(self): return self._id_paciente

    @property
    def motivo_consulta(self): return self._motivo_consulta

    @property
    def estado(self): return self._estado

    @property
    def fecha_ingreso(self): return self._fecha_ingreso

    @property
    def fecha_alta(self): return self._fecha_alta

    @property
    def activo(self): return self._activo

    def agregar_triaje(self, triaje: Triaje):
        """Agrega un nuevo triaje a la lista, manteniendo el historial completo.

        RN-01: mientras no exista ningún triaje, el episodio permanece en
        EN_ESPERA_TRIAJE y no es elegible para asignación de cama. En cuanto
        se registra el primer triaje, pasa a EN_ESPERA (de cama).
        """
        self._historial_triajes.append(triaje)
        if self._estado == self.ESTADO_EN_ESPERA_TRIAJE:
            self._estado = self.ESTADO_EN_ESPERA

    def obtener_triaje_actual(self) -> Triaje | None:
        """Devuelve el triaje activo más reciente (los anulados no cuentan)."""
        activos = [t for t in self._historial_triajes if t.activo]
        return max(activos, key=lambda t: t.fecha_hora) if activos else None

    def agregar_signos_vitales(self, signos: SignosVitales):
        self._signos_vitales.append(signos)

    def asignar_cama(self):
        """RN-01: solo un episodio en espera de cama y con un triaje activo puede recibir cama."""
        if self._estado != self.ESTADO_EN_ESPERA:
            raise ReglaNegocioError(f"No se puede asignar cama a un episodio en estado {self._estado}.")
        if self.obtener_triaje_actual() is None:
            raise ReglaNegocioError("No se puede asignar cama sin un triaje activo (RN-01).")
        self._estado = self.ESTADO_EN_ATENCION

    def dar_alta(self):
        """Solo se da de alta a un paciente que está siendo atendido en una cama."""
        if self._estado != self.ESTADO_EN_ATENCION:
            raise ReglaNegocioError(f"No se puede dar de alta un episodio en estado {self._estado}.")
        self._estado = self.ESTADO_ALTA
        self._fecha_alta = datetime.now()

    def anular(self):
        """RN-11: baja lógica; el episodio nunca se borra físicamente."""
        self._activo = False