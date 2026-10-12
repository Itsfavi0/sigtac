import logging

from dao.base_dao import BaseDAO
from models.persona import Paciente, es_dni_valido

logger = logging.getLogger(__name__)


class PacienteDAO(BaseDAO):
    """
    DAO de la tabla paciente. Convierte filas en objetos Paciente y viceversa.

    Los errores de BD se propagan como PersistenciaError (ver BaseDAO); un DNI repetido
    al crear lanza RegistroDuplicadoError.
    """

    # nombre_seguro no está en paciente: se obtiene con un JOIN para mostrarlo.
    _SELECT = """
        SELECT p.id_paciente, p.dni, p.nombres, p.apellidos, p.fecha_nac, p.sexo,
               p.id_seguro, s.nombre_seguro, p.estado_registro
        FROM paciente p
        JOIN seguro s ON p.id_seguro = s.id_seguro
    """

    @staticmethod
    def _a_paciente(fila: dict) -> Paciente:
        """Convierte una fila de la BD en un Paciente. El constructor valida los datos."""
        return Paciente(
            fila["id_paciente"], fila["dni"], fila["nombres"], fila["apellidos"],
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
    def buscar_por_dni(dni: str) -> Paciente | None:
        """
        Devuelve el paciente con ese DNI, o None si no existe.
        Incluye a los anulados: el DNI es único también para ellos, así que el controlador
        necesita saber que existe (y reactivarlo) en lugar de intentar registrarlo de nuevo.
        """
        if not es_dni_valido(dni):
            raise ValueError("El DNI debe tener exactamente 8 dígitos.")
        fila = PacienteDAO._consultar_uno(PacienteDAO._SELECT + " WHERE p.dni = %s", (dni,))
        return PacienteDAO._a_paciente(fila) if fila else None

    @staticmethod
    def crear(paciente: Paciente) -> int:
        """Registra un paciente nuevo y devuelve su id. Lanza RegistroDuplicadoError si el DNI ya existe."""
        if paciente.id_paciente is not None:
            raise ValueError("El paciente ya tiene id: para modificarlo use actualizar().")
        if not paciente.activo:
            raise ValueError("No se puede registrar un paciente anulado.")
        id_nuevo = PacienteDAO._insertar(
            """
            INSERT INTO paciente (dni, nombres, apellidos, fecha_nac, sexo, id_seguro)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (paciente.dni, paciente.nombres, paciente.apellidos, paciente.fecha_nac,
             paciente.sexo, paciente.id_seguro),
        )
        logger.info("Paciente registrado (id_paciente=%s).", id_nuevo)
        return id_nuevo

    @staticmethod
    def actualizar(paciente: Paciente) -> bool:
        """
        Guarda los datos editables del paciente. Devuelve False si no existe.
        El DNI no se modifica: identifica a la persona y la vincula con sus episodios.
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
