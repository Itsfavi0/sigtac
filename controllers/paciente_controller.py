from datetime import date

from controllers.auth_controller import Sesion, exigir_permiso
from dao.auditoria_dao import AuditoriaDAO
from dao.episodio_dao import EpisodioDAO
from dao.paciente_dao import PacienteDAO
from dao.transaccion import transaccion
from models.auditoria import AccionAuditoria
from models.documento import DocumentoIdentidad
from models.excepciones import ReglaNegocioError
from models.permisos import Permiso
from models.persona import Paciente
from models.triaje import EpisodioEmergencia


class PacienteController:
    """
    Admisión en emergencia: registrar pacientes (con documento o sin identificar, NN), abrir su
    episodio de emergencia, e identificar o fusionar a los pacientes NN.

    Cada operación que escribe lee los datos y los guarda dentro de la misma transacción, con su
    auditoría: o queda todo registrado, o nada.
    """

    def __init__(self, sesion: Sesion):
        self._sesion = sesion

    # ---- Consultas

    def listar_seguros(self) -> list[dict]:
        """Catálogo de seguros para el formulario de registro."""
        exigir_permiso(self._sesion, Permiso.PACIENTES)
        return PacienteDAO.listar_seguros()

    def buscar_por_documento(self, tipo_documento: str, num_documento: str) -> Paciente | None:
        """Busca al paciente por su documento (activo o dado de baja). ValueError si el documento es inválido."""
        exigir_permiso(self._sesion, Permiso.PACIENTES)
        return PacienteDAO.buscar_por_documento(DocumentoIdentidad(tipo_documento, num_documento))

    def listar_no_identificados(self) -> list[Paciente]:
        """Pacientes NN activos que aún esperan ser identificados."""
        exigir_permiso(self._sesion, Permiso.PACIENTES)
        return PacienteDAO.listar_no_identificados()

    # ---- Registro

    def registrar(self, tipo_documento: str, num_documento: str, nombres: str, apellidos: str,
                  fecha_nac: date, sexo: str, id_seguro: int) -> Paciente:
        """
        Registra un paciente con documento. Si el documento ya existe lanza ReglaNegocioError (el
        UNIQUE de la BD respalda la regla si dos PCs lo registran a la vez: RegistroDuplicadoError).
        """
        sesion = exigir_permiso(self._sesion, Permiso.PACIENTES)
        documento = DocumentoIdentidad(tipo_documento, num_documento)
        paciente = Paciente(None, documento, nombres, apellidos, fecha_nac, sexo, id_seguro)  # valida los datos
        with transaccion():
            existente = PacienteDAO.buscar_por_documento(documento)
            if existente is not None:
                if existente.activo:
                    raise ReglaNegocioError("Ya existe un paciente registrado con ese documento.")
                raise ReglaNegocioError("El paciente con ese documento está dado de baja: solicite su reactivación.")
            return self._crear(paciente, sesion)

    def registrar_no_identificado(self, sexo: str, edad_estimada: int, id_seguro: int) -> Paciente:
        """Registra un paciente que llega sin identificar (NN), con su sexo y una edad aparente."""
        sesion = exigir_permiso(self._sesion, Permiso.PACIENTES)
        paciente = Paciente.no_identificado(sexo, edad_estimada, id_seguro)
        with transaccion():
            return self._crear(paciente, sesion)

    @staticmethod
    def _crear(paciente: Paciente, sesion: Sesion) -> Paciente:
        id_paciente = PacienteDAO.crear(paciente)
        AuditoriaDAO.registrar(sesion.id_usuario, "paciente", AccionAuditoria.INSERT, id_paciente)
        # Se relee para devolver el paciente con su id y el nombre del seguro
        return PacienteDAO.buscar_por_id(id_paciente)

    # ---- Episodio de emergencia

    def abrir_episodio(self, id_paciente: int, motivo_consulta: str) -> EpisodioEmergencia:
        """
        Registra la llegada del paciente a emergencia: el episodio empieza EN ESPERA DE TRIAJE.

        Un paciente no puede tener dos episodios abiertos a la vez (sigue en emergencia). La fila del
        paciente se bloquea primero: si dos PCs lo admiten al mismo tiempo, la segunda espera y luego
        ve el episodio que abrió la primera.
        """
        sesion = exigir_permiso(self._sesion, Permiso.PACIENTES)
        if not isinstance(motivo_consulta, str) or not motivo_consulta.strip():
            raise ValueError("El motivo de consulta es obligatorio.")
        with transaccion():
            if not PacienteDAO.bloquear(id_paciente):
                raise ReglaNegocioError("El paciente no existe o está dado de baja.")
            abierto = self._episodio_abierto(id_paciente)
            if abierto is not None:
                raise ReglaNegocioError(
                    f"El paciente ya tiene un episodio abierto (n.º {abierto.id_episodio}, {abierto.estado})."
                )
            id_episodio = EpisodioDAO.crear(EpisodioEmergencia(None, id_paciente, motivo_consulta))
            AuditoriaDAO.registrar(sesion.id_usuario, "episodio_emergencia", AccionAuditoria.INSERT, id_episodio)
            return EpisodioDAO.buscar_por_id(id_episodio)

    @staticmethod
    def _episodio_abierto(id_paciente: int) -> EpisodioEmergencia | None:
        abiertos = [e for e in EpisodioDAO.listar_por_paciente(id_paciente) if not e.cerrado]
        return abiertos[0] if abiertos else None

    # ---- Pacientes sin identificar (NN)

    def identificar(self, id_paciente: int, tipo_documento: str, num_documento: str, nombres: str,
                    apellidos: str, fecha_nac: date) -> Paciente:
        """
        Registra la identidad real de un paciente NN. Si el documento ya pertenece a otro paciente,
        no se identifica (se duplicaría la persona): hay que fusionar ambos registros con fusionar().
        """
        sesion = exigir_permiso(self._sesion, Permiso.PACIENTES)
        documento = DocumentoIdentidad(tipo_documento, num_documento)
        with transaccion():
            paciente = self._cargar(id_paciente)
            if PacienteDAO.buscar_por_documento(documento) is not None:
                raise ReglaNegocioError(
                    "Ese documento ya pertenece a otro paciente registrado: fusione ambos registros."
                )
            paciente.identificar(documento, nombres, apellidos, fecha_nac)  # reglas y validaciones del modelo
            if not PacienteDAO.identificar(paciente):
                raise ReglaNegocioError("Otro usuario ya identificó o dio de baja a este paciente.")
            AuditoriaDAO.registrar(sesion.id_usuario, "paciente", AccionAuditoria.IDENTIFICAR, id_paciente)
        return paciente

    def fusionar(self, id_nn: int, id_destino: int) -> int:
        """
        El paciente NN resultó ser `id_destino`, ya registrado: sus episodios pasan al destino y el NN
        se da de baja. Devuelve cuántos episodios se movieron.

        Si los dos tienen un episodio abierto, no se fusionan: el destino quedaría con dos episodios
        abiertos a la vez. Antes hay que cerrar o anular uno de ellos.
        """
        sesion = exigir_permiso(self._sesion, Permiso.PACIENTES)
        with transaccion():
            nn, destino = self._cargar(id_nn), self._cargar(id_destino)
            nn.fusionar_en(destino)  # valida la regla y anula el NN en memoria
            if self._episodio_abierto(id_nn) is not None and self._episodio_abierto(id_destino) is not None:
                raise ReglaNegocioError("Ambos pacientes tienen un episodio abierto: cierre uno antes de fusionarlos.")
            movidos = PacienteDAO.fusionar(nn, destino)
            AuditoriaDAO.registrar(sesion.id_usuario, "paciente", AccionAuditoria.FUSIONAR, id_nn,
                                   {"id_destino": id_destino, "episodios_movidos": movidos})
        return movidos

    @staticmethod
    def _cargar(id_paciente: int) -> Paciente:
        paciente = PacienteDAO.buscar_por_id(id_paciente)
        if paciente is None:
            raise ReglaNegocioError("El paciente no existe.")
        return paciente
