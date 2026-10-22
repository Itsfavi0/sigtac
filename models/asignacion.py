from dataclasses import dataclass
from datetime import datetime


def _validar_fechas(inicio: datetime, fin: datetime | None, nombre_fin: str):
    # Coincide con CH_asignacion_fechas y CH_limpieza_fechas de schema.sql
    if fin is not None and fin < inicio:
        raise ValueError(f"{nombre_fin} no puede ser anterior al inicio.")


@dataclass(frozen=True)
class AsignacionCama:
    """
    Registro inmutable de una cama asignada a un episodio. Las asignaciones no se editan: al dar
    de alta se libera (fecha_liberacion) y queda como historial.
    """
    id_asignacion: int
    id_episodio: int
    id_cama: int
    id_empleado: int
    fecha_asignacion: datetime
    fecha_liberacion: datetime | None = None

    def __post_init__(self):
        _validar_fechas(self.fecha_asignacion, self.fecha_liberacion, "fecha_liberacion")

    @property
    def vigente(self) -> bool:
        """RN-05: una cama solo tiene una asignación vigente (sin liberar) a la vez."""
        return self.fecha_liberacion is None


@dataclass(frozen=True)
class SolicitudLimpieza:
    """
    Registro inmutable de una solicitud de limpieza (RN-07: al dar de alta, la cama pasa a limpieza).
    Queda pendiente hasta que el personal de limpieza la atiende (RN-08).
    """
    id_solicitud: int
    id_cama: int
    codigo_cama: str
    fecha_solicitud: datetime
    id_empleado: int | None = None   # personal de limpieza que la atendió
    fecha_atencion: datetime | None = None

    def __post_init__(self):
        _validar_fechas(self.fecha_solicitud, self.fecha_atencion, "fecha_atencion")
        if self.fecha_atencion is not None and self.id_empleado is None:
            raise ValueError("Una solicitud atendida debe indicar qué empleado la atendió.")

    @property
    def pendiente(self) -> bool:
        return self.fecha_atencion is None
