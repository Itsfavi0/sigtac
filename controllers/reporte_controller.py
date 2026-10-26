from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from controllers.auth_controller import Sesion, exigir_permiso
from dao.reporte_dao import ReporteDAO
from dao.transaccion import transaccion
from models.estados import EstadoCama, EstadoEpisodio
from models.permisos import Permiso
from models.triaje import EpisodioEmergencia
from utils import pdf_generator


@dataclass(frozen=True)
class EstadoGuardia:
    """Foto de la guardia en este momento."""
    camas_por_estado: dict[EstadoCama, int]
    porcentaje_ocupacion: float | None  # camas en uso / camas en servicio; None si no hay camas en servicio
    pacientes_por_estado: dict[EstadoEpisodio, int]  # solo los estados abiertos (pacientes en emergencia)

    @property
    def pacientes_en_emergencia(self) -> int:
        return sum(self.pacientes_por_estado.values())


@dataclass(frozen=True)
class IndicadoresPeriodo:
    """Indicadores de un período (días completos, ambos incluidos). Los promedios son en minutos."""
    desde: date
    hasta: date
    ingresos: int
    triajes_por_nivel: dict[int, int]
    porcentaje_reclasificacion: float | None  # None si no hubo triajes
    espera_triaje_min: float | None           # ingreso → primer triaje
    espera_cama_min: float | None             # ingreso → asignación de cama
    estancia_min: float | None                # ingreso → alta

    @property
    def total_triajes(self) -> int:
        return sum(self.triajes_por_nivel.values())


def _porcentaje(parte: int, total: int) -> float | None:
    return round(100 * parte / total, 1) if total else None


def _redondear(minutos: float | None) -> float | None:
    return None if minutos is None else round(minutos, 1)


class ReporteController:
    """Indicadores (KPI) para el jefe de guardia y el administrador. Permiso: REPORTES."""

    # Camas en uso: tienen un paciente asignado (aún no llegó o ya está en ella)
    CAMAS_EN_USO = (EstadoCama.RESERVADA, EstadoCama.OCUPADA)

    def __init__(self, sesion: Sesion):
        self._sesion = sesion

    def estado_actual(self) -> EstadoGuardia:
        """Camas por estado, porcentaje de ocupación y pacientes en emergencia por estado."""
        exigir_permiso(self._sesion, Permiso.REPORTES)
        with transaccion():  # las dos consultas ven la misma foto de la BD
            camas = ReporteDAO.contar_camas_por_estado()
            episodios = ReporteDAO.contar_episodios_por_estado()
        en_servicio = sum(camas.values()) - camas.get(EstadoCama.FUERA_SERVICIO, 0)
        en_uso = sum(camas.get(estado, 0) for estado in self.CAMAS_EN_USO)
        abiertos = {estado: total for estado, total in episodios.items()
                    if estado not in EpisodioEmergencia.ESTADOS_CERRADOS}
        return EstadoGuardia(camas, _porcentaje(en_uso, en_servicio), abiertos)

    def indicadores(self, desde: date, hasta: date) -> IndicadoresPeriodo:
        """Indicadores entre dos días, ambos incluidos (p. ej. del 1 al 31 de octubre)."""
        exigir_permiso(self._sesion, Permiso.REPORTES)
        for valor in (desde, hasta):
            # datetime es subclase de date: se exige un día, sin hora
            if not isinstance(valor, date) or isinstance(valor, datetime):
                raise ValueError("El período se indica con días (date), sin hora.")
        if desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la final.")
        inicio = datetime.combine(desde, time.min)
        fin = datetime.combine(hasta + timedelta(days=1), time.min)  # [inicio, fin): incluye todo el último día

        with transaccion():  # todas las consultas ven la misma foto de la BD
            ingresos = ReporteDAO.contar_ingresos(inicio, fin)
            por_nivel = ReporteDAO.contar_triajes_por_nivel(inicio, fin)
            total, reclasificados = ReporteDAO.contar_reclasificaciones(inicio, fin)
            espera_triaje = ReporteDAO.promedio_espera_triaje_min(inicio, fin)
            espera_cama = ReporteDAO.promedio_espera_cama_min(inicio, fin)
            estancia = ReporteDAO.promedio_estancia_min(inicio, fin)
        return IndicadoresPeriodo(desde, hasta, ingresos, por_nivel, _porcentaje(reclasificados, total),
                                  _redondear(espera_triaje), _redondear(espera_cama), _redondear(estancia))

    def exportar_pdf(self, desde: date, hasta: date, ruta: str | Path) -> Path:
        """
        Guarda en `ruta` un PDF con los indicadores del período y el estado actual de la guardia.
        Devuelve la ruta del archivo. Lanza ReporteError si no se puede escribir el archivo.
        """
        sesion = exigir_permiso(self._sesion, Permiso.REPORTES)
        ruta = pdf_generator.validar_ruta_pdf(ruta)  # antes de consultar: un error de la vista no toca la BD
        indicadores = self.indicadores(desde, hasta)
        estado = self.estado_actual()
        generado_por = f"{sesion.nombre_completo} ({sesion.nombre_rol})"
        return pdf_generator.guardar_reporte(ruta, indicadores, estado, datetime.now(), generado_por)
