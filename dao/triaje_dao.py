import logging

from dao.base_dao import BaseDAO
from dao.transaccion import transaccion
from models.triaje import SignosVitales, Sintoma, Triaje

logger = logging.getLogger(__name__)


class TriajeDAO(BaseDAO):
    """
    DAO de las tablas signos_vitales, triaje y triaje_sintoma, y del catálogo sintoma.

    Un triaje no se edita una vez guardado (RN-09): una reevaluación posterior se registra como un
    triaje nuevo del mismo episodio. Por eso este DAO solo inserta y lee.
    """

    # Los niveles se guardan como FK a nivel_triaje: se buscan por su número (1-5), no por el id.
    _SELECT_TRIAJES = """
        SELECT t.id_triaje, nf.numero AS nivel_final, ns.numero AS nivel_sugerido, t.id_empleado,
               t.fecha_hora, t.justificacion, t.estado_registro
        FROM triaje t
        JOIN nivel_triaje nf ON t.id_nivel = nf.id_nivel
        LEFT JOIN nivel_triaje ns ON t.id_nivel_sugerido = ns.id_nivel
        WHERE t.id_episodio = %s
        ORDER BY t.fecha_hora, t.id_triaje
    """

    @staticmethod
    def _a_sintoma(fila: dict) -> Sintoma:
        # DECIMAL llega como Decimal: el modelo trabaja con float.
        return Sintoma(fila["id_sintoma"], fila["nombre_sintoma"], float(fila["peso_clinico"]))

    @staticmethod
    def _a_signos(fila: dict) -> SignosVitales:
        return SignosVitales(fila["pa_sis"], fila["pa_dia"], fila["fc"], fila["fr"], float(fila["temp"]),
                             fila["sato2"], id_si=fila["id_si"])

    @staticmethod
    def _a_triaje(fila: dict) -> Triaje:
        """
        Reconstruye un Triaje usando los métodos del modelo, para que sus reglas se vuelvan a aplicar:
        reclasificar() exige la justificación de RN-10 y anular() marca la baja lógica (RN-11).
        """
        # id_nivel_sugerido admite NULL en la BD (triaje sin sugerencia): entonces el sugerido es el final.
        sugerido = fila["nivel_sugerido"] if fila["nivel_sugerido"] is not None else fila["nivel_final"]
        triaje = Triaje(fila["id_triaje"], sugerido, fila["id_empleado"], fila["fecha_hora"])
        if fila["nivel_final"] != sugerido:
            triaje.reclasificar(fila["nivel_final"], fila["justificacion"])
        if not fila["estado_registro"]:
            triaje.anular()
        return triaje

    @staticmethod
    def listar_sintomas() -> list[Sintoma]:
        """Catálogo de síntomas (para el formulario de triaje), ordenado por nombre."""
        filas = TriajeDAO._consultar_varios(
            "SELECT id_sintoma, nombre_sintoma, peso_clinico FROM sintoma ORDER BY nombre_sintoma"
        )
        return [TriajeDAO._a_sintoma(fila) for fila in filas]

    @staticmethod
    def registrar(id_episodio: int, signos: SignosVitales, triaje: Triaje) -> int:
        """
        Guarda, en una transacción, los signos vitales medidos, el triaje y sus síntomas, y devuelve
        el id del triaje. La fecha y hora las pone MySQL.

        No cambia el estado del episodio: eso lo decide el modelo (EpisodioEmergencia.agregar_triaje)
        y lo guarda EpisodioDAO.cambiar_estado, dentro de la misma transacción del controlador.
        """
        TriajeDAO._validar_id(id_episodio, "id_episodio")
        if not isinstance(signos, SignosVitales):
            raise ValueError("signos debe ser un SignosVitales.")
        if not isinstance(triaje, Triaje):
            raise ValueError("triaje debe ser un Triaje.")
        if signos.id_si is not None or triaje.id_triaje is not None:
            raise ValueError("Los signos y el triaje ya tienen id: un triaje guardado no se vuelve a registrar (RN-09).")
        if not triaje.activo:
            raise ValueError("No se puede registrar un triaje anulado.")
        TriajeDAO._validar_id(triaje.id_empleado, "id_empleado")

        v = signos.a_diccionario()
        with transaccion():
            TriajeDAO._insertar(
                """
                INSERT INTO signos_vitales (id_episodio, pa_sis, pa_dia, fc, fr, temp, sato2)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (id_episodio, v["pa_sis"], v["pa_dia"], v["fc"], v["fr"], v["temp"], v["sato2"]),
            )
            id_triaje = TriajeDAO._insertar(
                """
                INSERT INTO triaje (id_episodio, id_nivel, id_nivel_sugerido, id_empleado, justificacion)
                VALUES (%s, (SELECT id_nivel FROM nivel_triaje WHERE numero = %s),
                        (SELECT id_nivel FROM nivel_triaje WHERE numero = %s), %s, %s)
                """,
                (id_episodio, triaje.nivel_final, triaje.nivel_sugerido, triaje.id_empleado, triaje.justificacion),
            )
            for sintoma in triaje.sintomas:
                TriajeDAO._ejecutar(
                    "INSERT INTO triaje_sintoma (id_triaje, id_sintoma) VALUES (%s, %s)",
                    (id_triaje, sintoma.id_sintoma),
                )
        # Solo ids y niveles: la justificación es texto clínico y no va al log.
        logger.info("Triaje registrado (id_triaje=%s, id_episodio=%s, nivel=%s, reclasificado=%s).",
                    id_triaje, id_episodio, triaje.nivel_final, triaje.es_reclasificacion)
        return id_triaje

    @staticmethod
    def listar_por_episodio(id_episodio: int) -> list[Triaje]:
        """Historial de triajes del episodio, con sus síntomas, del más antiguo al más reciente (RN-09).
        Incluye los anulados (activo=False)."""
        TriajeDAO._validar_id(id_episodio, "id_episodio")
        triajes = [TriajeDAO._a_triaje(fila)
                   for fila in TriajeDAO._consultar_varios(TriajeDAO._SELECT_TRIAJES, (id_episodio,))]
        if not triajes:
            return []
        # Una sola consulta para los síntomas de todos los triajes del episodio.
        por_id = {t.id_triaje: t for t in triajes}
        filas = TriajeDAO._consultar_varios(
            """
            SELECT ts.id_triaje, s.id_sintoma, s.nombre_sintoma, s.peso_clinico
            FROM triaje_sintoma ts
            JOIN sintoma s ON ts.id_sintoma = s.id_sintoma
            JOIN triaje t ON ts.id_triaje = t.id_triaje
            WHERE t.id_episodio = %s
            ORDER BY ts.id_triaje, s.id_sintoma
            """,
            (id_episodio,),
        )
        for fila in filas:
            por_id[fila["id_triaje"]].agregar_sintoma(TriajeDAO._a_sintoma(fila))
        return triajes

    @staticmethod
    def listar_signos_por_episodio(id_episodio: int) -> list[SignosVitales]:
        """Mediciones de signos vitales del episodio, de la más antigua a la más reciente."""
        TriajeDAO._validar_id(id_episodio, "id_episodio")
        filas = TriajeDAO._consultar_varios(
            """
            SELECT id_si, pa_sis, pa_dia, fc, fr, temp, sato2
            FROM signos_vitales
            WHERE id_episodio = %s
            ORDER BY fecha_hora, id_si
            """,
            (id_episodio,),
        )
        return [TriajeDAO._a_signos(fila) for fila in filas]
