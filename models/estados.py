from enum import StrEnum


class EstadoCama(StrEnum):
    """Estados de una cama. Los valores coinciden con la tabla estado_cama de la BD."""
    DISPONIBLE = "DISPONIBLE"
    RESERVADA = "RESERVADA"
    OCUPADA = "OCUPADA"
    EN_LIMPIEZA = "EN LIMPIEZA"
    FUERA_SERVICIO = "FUERA DE SERVICIO"

    @property
    def texto(self) -> str:
        """Cómo se lee en pantalla y en el PDF: «En limpieza» (el valor es el de la BD, en mayúsculas)."""
        return self.value.capitalize()


class EstadoEpisodio(StrEnum):
    """Estados de un episodio de emergencia. Los valores coinciden con la tabla estado_episodio de la BD."""
    EN_ESPERA_TRIAJE = "EN ESPERA DE TRIAJE"
    EN_ESPERA = "EN ESPERA DE CAMA"
    EN_ATENCION = "EN ATENCIÓN (CON CAMA)"
    ALTA = "ALTA MÉDICA"
    REFERIDO = "REFERIDO"
    FUGADO = "FUGADO / ABANDONO"

    @property
    def texto(self) -> str:
        """Cómo se lee en pantalla y en el PDF: «En espera de cama»."""
        return self.value.capitalize()
