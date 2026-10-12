from enum import StrEnum


class EstadoCama(StrEnum):
    """Estados de una cama. Los valores coinciden con la tabla estado_cama de la BD."""
    DISPONIBLE = "DISPONIBLE"
    RESERVADA = "RESERVADA"
    OCUPADA = "OCUPADA"
    EN_LIMPIEZA = "EN LIMPIEZA"
    FUERA_SERVICIO = "FUERA DE SERVICIO"


class EstadoEpisodio(StrEnum):
    """Estados de un episodio de emergencia. Los valores coinciden con la tabla estado_episodio de la BD."""
    EN_ESPERA_TRIAJE = "EN ESPERA DE TRIAJE"
    EN_ESPERA = "EN ESPERA DE CAMA"
    EN_ATENCION = "EN ATENCIÓN (CON CAMA)"
    ALTA = "ALTA MÉDICA"
    REFERIDO = "REFERIDO"
    FUGADO = "FUGADO / ABANDONO"
