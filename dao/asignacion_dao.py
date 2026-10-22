import logging

from dao.base_dao import BaseDAO
from models.asignacion import AsignacionCama
from models.excepciones import ReglaNegocioError

logger = logging.getLogger(__name__)


class AsignacionDAO(BaseDAO):
    """
    DAO de la tabla asignacion_cama. Se usa dentro de la transacción del controlador, junto con
    CamaDAO.cambiar_estado y EpisodioDAO.cambiar_estado:

        with transaccion():
            anterior_ep, anterior_cama = episodio.estado, cama.estado
            episodio.asignar_cama()   # RN-01
            cama.reservar()           # RN-05
            EpisodioDAO.cambiar_estado(episodio, anterior_ep)
            CamaDAO.cambiar_estado(cama, anterior_cama)
            AsignacionDAO.crear(episodio.id_episodio, cama.id_cama, id_empleado)
            AuditoriaDAO.registrar(...)

    Cada método es una sola sentencia, así que no abre transacción propia. Las asignaciones no se
    borran ni se editan: al dar de alta se liberan y quedan como historial.
    """

    _SELECT = """
        SELECT id_asignacion, id_episodio, id_cama, id_empleado, fecha_asignacion, fecha_liberacion
        FROM asignacion_cama
    """
    # Vigente = sin liberar y activa. Es la misma condición de las columnas generadas cama_vigente y
    # episodio_vigente, cuyo UNIQUE impide en la BD dos asignaciones vigentes de la misma cama (RN-05).
    _VIGENTE = " AND fecha_liberacion IS NULL AND estado_registro = TRUE"

    @staticmethod
    def _a_asignacion(fila: dict) -> AsignacionCama:
        return AsignacionCama(fila["id_asignacion"], fila["id_episodio"], fila["id_cama"], fila["id_empleado"],
                              fila["fecha_asignacion"], fila["fecha_liberacion"])

    @staticmethod
    def crear(id_episodio: int, id_cama: int, id_empleado: int) -> int:
        """
        Registra la asignación de una cama a un episodio y devuelve su id. La fecha la pone MySQL.
        Si la cama o el episodio ya tienen una asignación vigente, el UNIQUE de la BD lo impide y se
        lanza RegistroDuplicadoError (respaldo de RN-05 aunque falle la comprobación de estados).
        """
        AsignacionDAO._validar_id(id_episodio, "id_episodio")
        AsignacionDAO._validar_id(id_cama, "id_cama")
        AsignacionDAO._validar_id(id_empleado, "id_empleado")
        id_nuevo = AsignacionDAO._insertar(
            "INSERT INTO asignacion_cama (id_episodio, id_cama, id_empleado) VALUES (%s, %s, %s)",
            (id_episodio, id_cama, id_empleado),
        )
        logger.info("Cama asignada (id_asignacion=%s, id_episodio=%s, id_cama=%s).", id_nuevo, id_episodio, id_cama)
        return id_nuevo

    @staticmethod
    def buscar_vigente_por_episodio(id_episodio: int) -> AsignacionCama | None:
        """La asignación vigente del episodio (la cama que ocupa ahora), o None si no tiene."""
        AsignacionDAO._validar_id(id_episodio, "id_episodio")
        fila = AsignacionDAO._consultar_uno(
            AsignacionDAO._SELECT + " WHERE id_episodio = %s" + AsignacionDAO._VIGENTE, (id_episodio,)
        )
        return AsignacionDAO._a_asignacion(fila) if fila else None

    @staticmethod
    def buscar_vigente_por_cama(id_cama: int) -> AsignacionCama | None:
        """La asignación vigente de la cama (qué episodio la ocupa), o None si no tiene."""
        AsignacionDAO._validar_id(id_cama, "id_cama")
        fila = AsignacionDAO._consultar_uno(
            AsignacionDAO._SELECT + " WHERE id_cama = %s" + AsignacionDAO._VIGENTE, (id_cama,)
        )
        return AsignacionDAO._a_asignacion(fila) if fila else None

    @staticmethod
    def liberar(id_asignacion: int) -> None:
        """
        Cierra la asignación al dar de alta (RN-07): pone la fecha de liberación (reloj de MySQL).
        El UPDATE es condicional: si la asignación no existe o ya estaba liberada, lanza
        ReglaNegocioError para que se deshaga la transacción del controlador.
        """
        AsignacionDAO._validar_id(id_asignacion, "id_asignacion")
        filas = AsignacionDAO._ejecutar(
            "UPDATE asignacion_cama SET fecha_liberacion = NOW() WHERE id_asignacion = %s" + AsignacionDAO._VIGENTE,
            (id_asignacion,),
        )
        if filas == 0:
            logger.warning("Liberación rechazada: la asignación no está vigente (id_asignacion=%s).", id_asignacion)
            raise ReglaNegocioError("La asignación ya fue liberada o no existe.")
        logger.info("Asignación liberada (id_asignacion=%s).", id_asignacion)
