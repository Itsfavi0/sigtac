import logging

from dao.base_dao import BaseDAO
from models.asignacion import SolicitudLimpieza
from models.excepciones import ReglaNegocioError

logger = logging.getLogger(__name__)


class SolicitudLimpiezaDAO(BaseDAO):
    """
    DAO de la tabla solicitud_limpieza. Se usa dentro de la transacción del controlador:

    - Alta (RN-07): la cama pasa a EN LIMPIEZA y se crea una solicitud con crear().
    - Confirmación (RN-08): la cama vuelve a DISPONIBLE y la solicitud se cierra con atender().

    Solo hay una solicitud pendiente por cama porque el cambio de estado de la cama (UPDATE
    condicional de CamaDAO) deja pasar una sola transición a EN LIMPIEZA por ciclo.
    """

    _SELECT = """
        SELECT s.id_solicitud, s.id_cama, c.codigo, s.fecha_solicitud, s.id_empleado, s.fecha_atencion
        FROM solicitud_limpieza s
        JOIN cama c ON s.id_cama = c.id_cama
    """

    @staticmethod
    def _a_solicitud(fila: dict) -> SolicitudLimpieza:
        return SolicitudLimpieza(fila["id_solicitud"], fila["id_cama"], fila["codigo"], fila["fecha_solicitud"],
                                 fila["id_empleado"], fila["fecha_atencion"])

    @staticmethod
    def crear(id_cama: int) -> int:
        """Registra una solicitud de limpieza pendiente para la cama y devuelve su id. La fecha la pone MySQL."""
        SolicitudLimpiezaDAO._validar_id(id_cama, "id_cama")
        id_nuevo = SolicitudLimpiezaDAO._insertar(
            "INSERT INTO solicitud_limpieza (id_cama) VALUES (%s)", (id_cama,)
        )
        logger.info("Solicitud de limpieza creada (id_solicitud=%s, id_cama=%s).", id_nuevo, id_cama)
        return id_nuevo

    @staticmethod
    def buscar_por_id(id_solicitud: int) -> SolicitudLimpieza | None:
        """La solicitud con ese id (pendiente o atendida), o None si no existe."""
        SolicitudLimpiezaDAO._validar_id(id_solicitud, "id_solicitud")
        fila = SolicitudLimpiezaDAO._consultar_uno(
            SolicitudLimpiezaDAO._SELECT + " WHERE s.id_solicitud = %s", (id_solicitud,)
        )
        return SolicitudLimpiezaDAO._a_solicitud(fila) if fila else None

    @staticmethod
    def listar_pendientes() -> list[SolicitudLimpieza]:
        """Solicitudes sin atender, de la más antigua a la más reciente (bandeja del personal de limpieza)."""
        filas = SolicitudLimpiezaDAO._consultar_varios(
            SolicitudLimpiezaDAO._SELECT + " WHERE s.fecha_atencion IS NULL ORDER BY s.fecha_solicitud, s.id_solicitud"
        )
        return [SolicitudLimpiezaDAO._a_solicitud(fila) for fila in filas]

    @staticmethod
    def atender(id_solicitud: int, id_empleado: int) -> None:
        """
        Marca la solicitud como atendida por `id_empleado` (RN-08); la fecha la pone MySQL.
        El UPDATE es condicional: si no existe o ya fue atendida (p. ej. por otro compañero), lanza
        ReglaNegocioError para que se deshaga la transacción del controlador.
        """
        SolicitudLimpiezaDAO._validar_id(id_solicitud, "id_solicitud")
        SolicitudLimpiezaDAO._validar_id(id_empleado, "id_empleado")
        filas = SolicitudLimpiezaDAO._ejecutar(
            """
            UPDATE solicitud_limpieza SET id_empleado = %s, fecha_atencion = NOW()
            WHERE id_solicitud = %s AND fecha_atencion IS NULL
            """,
            (id_empleado, id_solicitud),
        )
        if filas == 0:
            logger.warning("Atención rechazada: la solicitud no está pendiente (id_solicitud=%s).", id_solicitud)
            raise ReglaNegocioError("La solicitud de limpieza ya fue atendida o no existe.")
        logger.info("Solicitud de limpieza atendida (id_solicitud=%s).", id_solicitud)
