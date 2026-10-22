from dataclasses import dataclass

from controllers.auth_controller import Sesion, exigir_permiso
from controllers.colas import EntradaCola, armar_cola
from dao.auditoria_dao import AuditoriaDAO
from dao.episodio_dao import EpisodioDAO
from dao.transaccion import transaccion
from dao.triaje_dao import TriajeDAO
from models.auditoria import AccionAuditoria
from models.estados import EstadoEpisodio
from models.estrategias import EstrategiaTriaje, ReglaManchester
from models.excepciones import ReglaNegocioError, SignosVitalesIncompletosError
from models.permisos import Permiso
from models.triaje import SignosVitales, Sintoma, Triaje


@dataclass(frozen=True)
class Sugerencia:
    """Nivel que propone la estrategia de triaje y el protocolo en que se basa (para mostrarlo al profesional)."""
    nivel: int
    protocolo: str


class TriajeController:
    """
    Triaje de un episodio: a partir de los signos vitales y los síntomas, la estrategia (patrón
    Strategy) sugiere un nivel; el profesional lo confirma o lo reclasifica con justificación (RN-10)
    y el triaje se agrega al historial del episodio (RN-09). Permiso: TRIAJE.

    La estrategia se recibe al crear el controlador (por defecto, Manchester): cambiar de protocolo
    no exige tocar este código.
    """

    # Claves que se esperan en el diccionario de signos vitales (las mismas que valida SignosVitales)
    SIGNOS = tuple(SignosVitales.RANGOS)

    def __init__(self, sesion: Sesion, estrategia: EstrategiaTriaje | None = None):
        estrategia = ReglaManchester() if estrategia is None else estrategia
        if not isinstance(estrategia, EstrategiaTriaje):
            raise ValueError("estrategia debe ser una EstrategiaTriaje.")
        self._sesion = sesion
        self._estrategia = estrategia

    # ---- Consultas

    def listar_sintomas(self) -> list[Sintoma]:
        """Catálogo de síntomas para el formulario."""
        exigir_permiso(self._sesion, Permiso.TRIAJE)
        return TriajeDAO.listar_sintomas()

    def cola_de_triaje(self) -> list[EntradaCola]:
        """Pacientes que esperan su primer triaje, por orden de llegada."""
        exigir_permiso(self._sesion, Permiso.TRIAJE)
        return armar_cola(EstadoEpisodio.EN_ESPERA_TRIAJE)

    def sugerir(self, signos: dict, ids_sintomas) -> Sugerencia:
        """Nivel que sugiere la estrategia, sin guardar nada (la vista lo muestra antes de confirmar)."""
        exigir_permiso(self._sesion, Permiso.TRIAJE)
        signos_vitales = self._crear_signos(signos)
        nivel = self._estrategia.clasificar(signos_vitales.a_diccionario(), self._buscar_sintomas(ids_sintomas))
        return Sugerencia(nivel, self._estrategia.justificar())

    # ---- Registro

    def registrar(self, id_episodio: int, signos: dict, ids_sintomas, nivel_final: int | None = None,
                  justificacion: str | None = None) -> int:
        """
        Registra un triaje en el episodio y devuelve su id.

        El nivel sugerido se vuelve a calcular aquí (no se recibe de la vista): así lo que queda como
        "sugerido" en la BD es siempre lo que dijo el algoritmo. Si `nivel_final` es distinto, es una
        reclasificación y exige justificación (RN-10); si es igual o None, se confirma la sugerencia
        y la justificación no se guarda.

        El primer triaje pasa el episodio de EN ESPERA DE TRIAJE a EN ESPERA DE CAMA. Un episodio
        cerrado no admite triajes. El episodio se bloquea al empezar: otra PC no puede darlo de alta
        mientras se registra.
        """
        sesion = exigir_permiso(self._sesion, Permiso.TRIAJE)
        signos_vitales = self._crear_signos(signos)
        sintomas = self._buscar_sintomas(ids_sintomas)
        sugerido = self._estrategia.clasificar(signos_vitales.a_diccionario(), sintomas)
        triaje = Triaje(None, sugerido, sesion.id_empleado, None)
        for sintoma in sintomas:
            triaje.agregar_sintoma(sintoma)
        if nivel_final is not None and nivel_final != sugerido:
            triaje.reclasificar(nivel_final, justificacion)  # RN-10

        with transaccion():
            if not EpisodioDAO.bloquear(id_episodio):
                raise ReglaNegocioError("El episodio no existe o está anulado.")
            episodio = EpisodioDAO.buscar_por_id(id_episodio)
            anterior = episodio.estado
            episodio.agregar_signos_vitales(signos_vitales)  # un episodio cerrado los rechaza
            episodio.agregar_triaje(triaje)
            id_triaje = TriajeDAO.registrar(id_episodio, signos_vitales, triaje)
            if episodio.estado != anterior:
                EpisodioDAO.cambiar_estado(episodio, anterior)
            AuditoriaDAO.registrar(sesion.id_usuario, "triaje", AccionAuditoria.INSERT, id_triaje, {
                "id_episodio": id_episodio, "nivel_sugerido": triaje.nivel_sugerido,
                "nivel_final": triaje.nivel_final, "reclasificado": triaje.es_reclasificacion,
                "protocolo": type(self._estrategia).__name__,
            })
        return id_triaje

    # ---- Ayudantes

    def _crear_signos(self, datos: dict) -> SignosVitales:
        """Convierte el diccionario del formulario en SignosVitales (el constructor valida tipos y rangos)."""
        if not isinstance(datos, dict):
            raise ValueError("Los signos vitales deben enviarse como diccionario.")
        desconocidos = sorted(str(clave) for clave in set(datos) - set(self.SIGNOS))
        if desconocidos:
            raise ValueError(f"Signos vitales no reconocidos: {', '.join(desconocidos)}.")
        faltantes = [s for s in self.SIGNOS if datos.get(s) is None]
        if faltantes:
            raise SignosVitalesIncompletosError(f"Faltan los signos vitales: {', '.join(faltantes)}.")
        return SignosVitales(**datos, id_si=None)

    @staticmethod
    def _buscar_sintomas(ids_sintomas) -> list[Sintoma]:
        """Convierte los ids elegidos en el formulario en Sintoma del catálogo."""
        ids = list(ids_sintomas or [])
        if len(ids) != len(set(ids)):
            raise ValueError("Hay síntomas repetidos.")
        if not ids:
            return []
        catalogo = {s.id_sintoma: s for s in TriajeDAO.listar_sintomas()}
        desconocidos = [i for i in ids if i not in catalogo]
        if desconocidos:
            raise ValueError("Síntoma no reconocido.")
        return [catalogo[i] for i in ids]
