from datetime import datetime

from dao.base_dao import BaseDAO
from models.estados import EstadoCama, EstadoEpisodio


class ReporteDAO(BaseDAO):
    """
    Consultas de agregación (COUNT, AVG) para los indicadores de la guardia. Solo lectura.

    Los cálculos que se resuelven mejor en la BD (contar y promediar miles de filas) se hacen aquí;
    los porcentajes y el formato los prepara ReporteController. Los períodos son [desde, hasta): el
    límite superior no se incluye.
    """

    @staticmethod
    def _validar_periodo(desde: datetime, hasta: datetime) -> tuple[datetime, datetime]:
        if not isinstance(desde, datetime) or not isinstance(hasta, datetime):
            raise ValueError("El período debe indicarse con fechas y horas (datetime).")
        if desde >= hasta:
            raise ValueError("El inicio del período debe ser anterior al final.")
        return desde, hasta

    @staticmethod
    def _promedio(fila: dict | None) -> float | None:
        # AVG devuelve Decimal, o NULL si no hubo filas
        return None if fila is None or fila["promedio"] is None else float(fila["promedio"])

    # ---- Estado actual

    @staticmethod
    def contar_camas_por_estado() -> dict[EstadoCama, int]:
        """Camas activas por estado; los estados sin camas aparecen con 0."""
        filas = ReporteDAO._consultar_varios(
            """
            SELECT e.nombre_estado_cama, COUNT(c.id_cama) AS total
            FROM estado_cama e
            LEFT JOIN cama c ON c.id_estado_cama = e.id_estado_cama AND c.estado_registro = TRUE
            GROUP BY e.id_estado_cama, e.nombre_estado_cama
            """
        )
        return {EstadoCama(f["nombre_estado_cama"]): int(f["total"]) for f in filas}

    @staticmethod
    def contar_episodios_por_estado() -> dict[EstadoEpisodio, int]:
        """Episodios activos (no anulados) por estado; los estados sin episodios aparecen con 0."""
        filas = ReporteDAO._consultar_varios(
            """
            SELECT e.nombre_estado_episodio, COUNT(ep.id_episodio) AS total
            FROM estado_episodio e
            LEFT JOIN episodio_emergencia ep ON ep.id_estado_ep = e.id_estado_ep AND ep.estado_registro = TRUE
            GROUP BY e.id_estado_ep, e.nombre_estado_episodio
            """
        )
        return {EstadoEpisodio(f["nombre_estado_episodio"]): int(f["total"]) for f in filas}

    # ---- Indicadores de un período

    @staticmethod
    def contar_ingresos(desde: datetime, hasta: datetime) -> int:
        """Episodios (no anulados) que ingresaron en el período."""
        fila = ReporteDAO._consultar_uno(
            """
            SELECT COUNT(*) AS total FROM episodio_emergencia
            WHERE estado_registro = TRUE AND fecha_ingreso >= %s AND fecha_ingreso < %s
            """,
            ReporteDAO._validar_periodo(desde, hasta),
        )
        return int(fila["total"])

    @staticmethod
    def contar_triajes_por_nivel(desde: datetime, hasta: datetime) -> dict[int, int]:
        """Triajes activos del período por nivel final (1 a 5); los niveles sin triajes aparecen con 0."""
        filas = ReporteDAO._consultar_varios(
            """
            SELECT n.numero, COUNT(t.id_triaje) AS total
            FROM nivel_triaje n
            LEFT JOIN triaje t ON t.id_nivel = n.id_nivel AND t.estado_registro = TRUE
                 AND t.fecha_hora >= %s AND t.fecha_hora < %s
            GROUP BY n.id_nivel, n.numero
            ORDER BY n.numero
            """,
            ReporteDAO._validar_periodo(desde, hasta),
        )
        return {int(f["numero"]): int(f["total"]) for f in filas}

    @staticmethod
    def contar_reclasificaciones(desde: datetime, hasta: datetime) -> tuple[int, int]:
        """(triajes activos del período, cuántos de ellos se reclasificaron: nivel final distinto del sugerido)."""
        fila = ReporteDAO._consultar_uno(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(id_nivel_sugerido IS NOT NULL AND id_nivel <> id_nivel_sugerido), 0) AS reclasificados
            FROM triaje
            WHERE estado_registro = TRUE AND fecha_hora >= %s AND fecha_hora < %s
            """,
            ReporteDAO._validar_periodo(desde, hasta),
        )
        return int(fila["total"]), int(fila["reclasificados"])

    @staticmethod
    def promedio_espera_triaje_min(desde: datetime, hasta: datetime) -> float | None:
        """Minutos promedio desde el ingreso hasta el primer triaje, de los episodios que ingresaron en el período."""
        return ReporteDAO._promedio(ReporteDAO._consultar_uno(
            """
            SELECT AVG(TIMESTAMPDIFF(MINUTE, ep.fecha_ingreso, t.primer_triaje)) AS promedio
            FROM episodio_emergencia ep
            JOIN (SELECT id_episodio, MIN(fecha_hora) AS primer_triaje
                  FROM triaje WHERE estado_registro = TRUE GROUP BY id_episodio) t
                 ON t.id_episodio = ep.id_episodio
            WHERE ep.estado_registro = TRUE AND ep.fecha_ingreso >= %s AND ep.fecha_ingreso < %s
            """,
            ReporteDAO._validar_periodo(desde, hasta),
        ))

    @staticmethod
    def promedio_espera_cama_min(desde: datetime, hasta: datetime) -> float | None:
        """
        Minutos promedio desde el ingreso hasta la asignación de cama, de las asignaciones del período.
        Las reservas canceladas (estado_registro = FALSE) no cuentan.
        """
        return ReporteDAO._promedio(ReporteDAO._consultar_uno(
            """
            SELECT AVG(TIMESTAMPDIFF(MINUTE, ep.fecha_ingreso, a.fecha_asignacion)) AS promedio
            FROM asignacion_cama a
            JOIN episodio_emergencia ep ON a.id_episodio = ep.id_episodio
            WHERE a.estado_registro = TRUE AND ep.estado_registro = TRUE
              AND a.fecha_asignacion >= %s AND a.fecha_asignacion < %s
            """,
            ReporteDAO._validar_periodo(desde, hasta),
        ))

    @staticmethod
    def promedio_estancia_min(desde: datetime, hasta: datetime) -> float | None:
        """Minutos promedio desde el ingreso hasta el alta, de los episodios dados de alta en el período."""
        return ReporteDAO._promedio(ReporteDAO._consultar_uno(
            """
            SELECT AVG(TIMESTAMPDIFF(MINUTE, fecha_ingreso, fecha_alta)) AS promedio
            FROM episodio_emergencia
            WHERE estado_registro = TRUE AND fecha_alta >= %s AND fecha_alta < %s
            """,
            ReporteDAO._validar_periodo(desde, hasta),
        ))
