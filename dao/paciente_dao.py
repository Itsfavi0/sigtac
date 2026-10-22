import logging

from dao.base_dao import BaseDAO
from models.documento import DocumentoIdentidad
from models.persona import Paciente

logger = logging.getLogger(__name__)


class PacienteDAO(BaseDAO):
    """
    DAO de la tabla paciente. Convierte filas en objetos Paciente y viceversa.

    Los errores de BD se propagan como PersistenciaError (ver BaseDAO); un documento repetido
    al crear lanza RegistroDuplicadoError.
    """

    # El código del tipo de documento y nombre_seguro no están en paciente: se obtienen con JOIN.
    # LEFT JOIN: un paciente sin identificar no tiene tipo de documento y también debe devolverse.
    _SELECT = """
        SELECT p.id_paciente, td.codigo AS tipo_documento, p.num_documento, p.nombres, p.apellidos,
               p.fecha_nac, p.sexo, p.id_seguro, s.nombre_seguro, p.estado_registro
        FROM paciente p
        LEFT JOIN tipo_documento td ON p.id_tipo_documento = td.id_tipo_documento
        JOIN seguro s ON p.id_seguro = s.id_seguro
    """

    @staticmethod
    def _a_paciente(fila: dict) -> Paciente:
        """Convierte una fila de la BD en un Paciente. El constructor valida los datos."""
        # El CHECK de la BD garantiza que tipo y número sean NULL a la vez (paciente sin identificar).
        documento = None
        if fila["num_documento"] is not None:
            documento = DocumentoIdentidad(fila["tipo_documento"], fila["num_documento"])
        return Paciente(
            fila["id_paciente"], documento, fila["nombres"], fila["apellidos"],
            fila["fecha_nac"], fila["sexo"], fila["id_seguro"],
            activo=bool(fila["estado_registro"]),  # MySQL devuelve BOOLEAN como 0/1
            nombre_seguro=fila["nombre_seguro"],
        )

    @staticmethod
    def buscar_por_id(id_paciente: int) -> Paciente | None:
        """Devuelve el paciente con ese id (activo o anulado), o None si no existe."""
        fila = PacienteDAO._consultar_uno(PacienteDAO._SELECT + " WHERE p.id_paciente = %s", (id_paciente,))
        return PacienteDAO._a_paciente(fila) if fila else None

    @staticmethod
    def buscar_por_documento(documento: DocumentoIdentidad) -> Paciente | None:
        """
        Devuelve el paciente con ese documento (tipo y número), o None si no existe.
        Incluye a los anulados: el documento es único también para ellos, así que el controlador
        necesita saber que existe (y reactivarlo) en lugar de intentar registrarlo de nuevo.
        """
        if not isinstance(documento, DocumentoIdentidad):
            raise ValueError("documento debe ser un DocumentoIdentidad.")
        fila = PacienteDAO._consultar_uno(
            PacienteDAO._SELECT + " WHERE td.codigo = %s AND p.num_documento = %s",
            (documento.tipo.value, documento.numero),
        )
        return PacienteDAO._a_paciente(fila) if fila else None

    @staticmethod
    def listar_no_identificados() -> list[Paciente]:
        """Pacientes activos que aún no tienen documento (NN), del más antiguo al más reciente."""
        filas = PacienteDAO._consultar_varios(
            PacienteDAO._SELECT + " WHERE p.num_documento IS NULL AND p.estado_registro = TRUE ORDER BY p.id_paciente"
        )
        return [PacienteDAO._a_paciente(fila) for fila in filas]

    @staticmethod
    def crear(paciente: Paciente) -> int:
        """Registra un paciente nuevo y devuelve su id. Lanza RegistroDuplicadoError si el documento ya existe."""
        if paciente.id_paciente is not None:
            raise ValueError("El paciente ya tiene id: para modificarlo use actualizar().")
        if not paciente.activo:
            raise ValueError("No se puede registrar un paciente anulado.")
        # El id del tipo de documento se obtiene a partir de su código con una subconsulta.
        # Un paciente sin identificar envía NULL en ambos: la subconsulta con codigo = NULL devuelve NULL.
        documento = paciente.documento
        tipo, numero = (documento.tipo.value, documento.numero) if documento else (None, None)
        id_nuevo = PacienteDAO._insertar(
            """
            INSERT INTO paciente (id_tipo_documento, num_documento, nombres, apellidos, fecha_nac, sexo, id_seguro)
            VALUES ((SELECT id_tipo_documento FROM tipo_documento WHERE codigo = %s), %s, %s, %s, %s, %s, %s)
            """,
            (tipo, numero, paciente.nombres, paciente.apellidos, paciente.fecha_nac,
             paciente.sexo, paciente.id_seguro),
        )
        logger.info("Paciente registrado (id_paciente=%s).", id_nuevo)
        return id_nuevo

    @staticmethod
    def actualizar(paciente: Paciente) -> bool:
        """
        Guarda los datos editables del paciente. Devuelve False si no existe.
        El documento no se modifica: identifica a la persona y la vincula con sus episodios.
        Para registrar el documento de un paciente sin identificar se usa identificar().
        """
        if paciente.id_paciente is None:
            raise ValueError("El paciente no tiene id: para registrarlo use crear().")
        filas = PacienteDAO._ejecutar(
            """
            UPDATE paciente
            SET nombres = %s, apellidos = %s, fecha_nac = %s, sexo = %s, id_seguro = %s
            WHERE id_paciente = %s
            """,
            (paciente.nombres, paciente.apellidos, paciente.fecha_nac, paciente.sexo,
             paciente.id_seguro, paciente.id_paciente),
        )
        return filas > 0

    @staticmethod
    def identificar(paciente: Paciente) -> bool:
        """
        Guarda la identidad real (documento, nombres, apellidos y fecha de nacimiento) de un paciente
        que ingresó sin identificar; antes se llama a paciente.identificar().
        Devuelve False si el paciente no existe o ya estaba identificado en la BD. Lanza
        RegistroDuplicadoError si el documento ya pertenece a otro paciente.
        """
        if paciente.id_paciente is None:
            raise ValueError("El paciente no tiene id: para registrarlo use crear().")
        if not paciente.identificado:
            raise ValueError("El paciente no tiene documento: llame antes a paciente.identificar().")
        # La condición num_documento IS NULL impide sobrescribir el documento de un paciente ya identificado.
        filas = PacienteDAO._ejecutar(
            """
            UPDATE paciente
            SET id_tipo_documento = (SELECT id_tipo_documento FROM tipo_documento WHERE codigo = %s),
                num_documento = %s, nombres = %s, apellidos = %s, fecha_nac = %s
            WHERE id_paciente = %s AND num_documento IS NULL
            """,
            (paciente.documento.tipo.value, paciente.documento.numero, paciente.nombres,
             paciente.apellidos, paciente.fecha_nac, paciente.id_paciente),
        )
        if filas:
            logger.info("Paciente identificado (id_paciente=%s).", paciente.id_paciente)
        return filas > 0

    @staticmethod
    def anular(id_paciente: int) -> bool:
        """RN-11: baja lógica (estado_registro = FALSE). Devuelve False si el paciente no existe."""
        filas = PacienteDAO._ejecutar(
            "UPDATE paciente SET estado_registro = FALSE WHERE id_paciente = %s",
            (id_paciente,),
        )
        if filas:
            logger.info("Paciente anulado (id_paciente=%s).", id_paciente)
        return filas > 0
