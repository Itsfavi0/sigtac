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
    _SELECT = """
        SELECT p.id_paciente, td.codigo AS tipo_documento, p.num_documento, p.nombres, p.apellidos,
               p.fecha_nac, p.sexo, p.id_seguro, s.nombre_seguro, p.estado_registro
        FROM paciente p
        JOIN tipo_documento td ON p.id_tipo_documento = td.id_tipo_documento
        JOIN seguro s ON p.id_seguro = s.id_seguro
    """

    @staticmethod
    def _a_paciente(fila: dict) -> Paciente:
        """Convierte una fila de la BD en un Paciente. El constructor valida los datos."""
        return Paciente(
            fila["id_paciente"], DocumentoIdentidad(fila["tipo_documento"], fila["num_documento"]), fila["nombres"], fila["apellidos"],
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
    def crear(paciente: Paciente) -> int:
        """Registra un paciente nuevo y devuelve su id. Lanza RegistroDuplicadoError si el documento ya existe."""
        if paciente.id_paciente is not None:
            raise ValueError("El paciente ya tiene id: para modificarlo use actualizar().")
        if not paciente.activo:
            raise ValueError("No se puede registrar un paciente anulado.")
        # El id del tipo de documento se obtiene a partir de su código con una subconsulta.
        id_nuevo = PacienteDAO._insertar(
            """
            INSERT INTO paciente (id_tipo_documento, num_documento, nombres, apellidos, fecha_nac, sexo, id_seguro)
            VALUES ((SELECT id_tipo_documento FROM tipo_documento WHERE codigo = %s), %s, %s, %s, %s, %s, %s)
            """,
            (paciente.documento.tipo.value, paciente.documento.numero, paciente.nombres, paciente.apellidos, paciente.fecha_nac,
             paciente.sexo, paciente.id_seguro),
        )
        logger.info("Paciente registrado (id_paciente=%s).", id_nuevo)
        return id_nuevo

    @staticmethod
    def actualizar(paciente: Paciente) -> bool:
        """
        Guarda los datos editables del paciente. Devuelve False si no existe.
        El documento no se modifica: identifica a la persona y la vincula con sus episodios.
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
    def anular(id_paciente: int) -> bool:
        """RN-11: baja lógica (estado_registro = FALSE). Devuelve False si el paciente no existe."""
        filas = PacienteDAO._ejecutar(
            "UPDATE paciente SET estado_registro = FALSE WHERE id_paciente = %s",
            (id_paciente,),
        )
        if filas:
            logger.info("Paciente anulado (id_paciente=%s).", id_paciente)
        return filas > 0
