import logging

from dao.base_dao import BaseDAO
from dao.triaje_dao import TriajeDAO
from models.estados import EstadoEpisodio
from models.excepciones import ReglaNegocioError
from models.triaje import EpisodioEmergencia

logger = logging.getLogger(__name__)


class EpisodioDAO(BaseDAO):
    """
    DAO de la tabla episodio_emergencia. Un episodio es la visita de un paciente a emergencia;
    sus triajes y signos vitales los guarda TriajeDAO.
    """

    _SELECT = """
        SELECT ep.id_episodio, ep.id_paciente, ep.motivo_consulta, e.nombre_estado_episodio,
               ep.fecha_ingreso, ep.fecha_alta, ep.estado_registro
        FROM episodio_emergencia ep
        JOIN estado_episodio e ON ep.id_estado_ep = e.id_estado_ep
    """

    @staticmethod
    def _a_episodio(fila: dict) -> EpisodioEmergencia:
        """Convierte una fila en un EpisodioEmergencia (sin su historial de triajes ni signos)."""
        return EpisodioEmergencia(
            fila["id_episodio"], fila["id_paciente"], fila["motivo_consulta"],
            estado=EstadoEpisodio(fila["nombre_estado_episodio"]),  # ValueError si no existe en el Enum
            fecha_ingreso=fila["fecha_ingreso"], fecha_alta=fila["fecha_alta"],
            activo=bool(fila["estado_registro"]),  # MySQL devuelve BOOLEAN como 0/1
        )

    @staticmethod
    def crear(episodio: EpisodioEmergencia) -> int:
        """Registra la llegada de un paciente a emergencia y devuelve el id del episodio.
        La fecha de ingreso la pone MySQL."""
        if not isinstance(episodio, EpisodioEmergencia):
            raise ValueError("episodio debe ser un EpisodioEmergencia.")
        if episodio.id_episodio is not None:
            raise ValueError("El episodio ya tiene id: ya está registrado.")
        if not episodio.activo:
            raise ValueError("No se puede registrar un episodio anulado.")
        EpisodioDAO._validar_id(episodio.id_paciente, "id_paciente")
        if not isinstance(episodio.motivo_consulta, str) or not episodio.motivo_consulta.strip():
            raise ValueError("El motivo de consulta es obligatorio.")
        id_nuevo = EpisodioDAO._insertar(
            """
            INSERT INTO episodio_emergencia (id_paciente, motivo_consulta, id_estado_ep)
            VALUES (%s, %s, (SELECT id_estado_ep FROM estado_episodio WHERE nombre_estado_episodio = %s))
            """,
            (episodio.id_paciente, episodio.motivo_consulta.strip(), episodio.estado.value),
        )
        # El motivo de consulta es información clínica: no va al log.
        logger.info("Episodio registrado (id_episodio=%s, id_paciente=%s).", id_nuevo, episodio.id_paciente)
        return id_nuevo

    @staticmethod
    def buscar_por_id(id_episodio: int) -> EpisodioEmergencia | None:
        """
        Devuelve el episodio (activo o anulado) con su historial completo de signos vitales y triajes,
        o None si no existe. Así el modelo puede aplicar sus reglas (p. ej. RN-01 en asignar_cama).
        """
        EpisodioDAO._validar_id(id_episodio, "id_episodio")
        fila = EpisodioDAO._consultar_uno(EpisodioDAO._SELECT + " WHERE ep.id_episodio = %s", (id_episodio,))
        if not fila:
            return None
        episodio = EpisodioDAO._a_episodio(fila)
        for signos in TriajeDAO.listar_signos_por_episodio(id_episodio):
            episodio.agregar_signos_vitales(signos)
        for triaje in TriajeDAO.listar_por_episodio(id_episodio):
            # agregar_triaje solo cambia el estado si el episodio sigue EN ESPERA DE TRIAJE, lo que no
            # ocurre en un episodio guardado con triajes: el estado leído de la BD se conserva.
            episodio.agregar_triaje(triaje)
        return episodio

    @staticmethod
    def cambiar_estado(episodio: EpisodioEmergencia, estado_anterior: EstadoEpisodio | str) -> None:
        """
        Guarda el estado actual del episodio. La transición la decide antes el modelo
        (agregar_triaje, asignar_cama, dar_alta...); este método solo la persiste:

            anterior = episodio.estado
            episodio.asignar_cama()
            EpisodioDAO.cambiar_estado(episodio, anterior)

        El UPDATE es condicional, como en CamaDAO.cambiar_estado: si en la BD el episodio ya no está en
        `estado_anterior` (otro usuario lo cambió, no existe o está anulado), lanza ReglaNegocioError y
        no guarda nada. Al pasar a ALTA MÉDICA, la fecha de alta la pone MySQL.
        """
        if not isinstance(episodio, EpisodioEmergencia):
            raise ValueError("episodio debe ser un EpisodioEmergencia.")
        id_episodio = EpisodioDAO._validar_id(episodio.id_episodio, "id_episodio")
        try:
            estado_anterior = EstadoEpisodio(estado_anterior)
        except ValueError:
            raise ValueError("Estado anterior no reconocido.") from None
        estado_nuevo = episodio.estado
        if estado_nuevo == estado_anterior:
            raise ValueError("El episodio no cambió de estado.")

        # Una sola sentencia: no necesita transacción propia. Dentro de la de un controlador, la
        # excepción por 0 filas deshace también los pasos anteriores.
        # La fecha de alta se toma del reloj de MySQL (el mismo de fecha_ingreso), para que se cumpla
        # CH_episodio_fechas aunque el reloj de la PC esté desfasado.
        filas = EpisodioDAO._ejecutar(
            """
            UPDATE episodio_emergencia
            SET id_estado_ep = (SELECT id_estado_ep FROM estado_episodio WHERE nombre_estado_episodio = %s),
                fecha_alta = IF(%s, NOW(), fecha_alta)
            WHERE id_episodio = %s AND estado_registro = TRUE
              AND id_estado_ep = (SELECT id_estado_ep FROM estado_episodio WHERE nombre_estado_episodio = %s)
            """,
            (estado_nuevo.value, estado_nuevo is EstadoEpisodio.ALTA, id_episodio, estado_anterior.value),
        )
        if filas == 0:
            logger.warning("Cambio de estado rechazado: el episodio ya no está en %s (id_episodio=%s).",
                           estado_anterior.value, id_episodio)
            raise ReglaNegocioError(
                f"El episodio ya no está en estado {estado_anterior.value}: otro usuario lo cambió."
            )
        logger.info("Episodio %s: %s -> %s.", id_episodio, estado_anterior.value, estado_nuevo.value)
