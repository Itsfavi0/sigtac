from abc import ABC, abstractmethod
from models.estados import EstadoCama
from models.excepciones import CamaEstadoInvalidoError

#CLASE PADRE
class Cama(ABC):
    """"Superclase abstracta para el manejo de camas y sus estados"""
    ESTADO_DISPONIBLE = EstadoCama.DISPONIBLE
    ESTADO_RESERVADA = EstadoCama.RESERVADA
    ESTADO_OCUPADA = EstadoCama.OCUPADA
    ESTADO_EN_LIMPIEZA = EstadoCama.EN_LIMPIEZA
    ESTADO_FUERA_SERVICIO = EstadoCama.FUERA_SERVICIO

    def __init__(self, id_cama, codigo, area, estado : str = ESTADO_DISPONIBLE):
        self._id_cama = id_cama
        self._codigo = codigo
        self._area = area
        self._estado = EstadoCama(estado)  # ValueError si el estado no existe

    @property
    def id_cama(self): return self._id_cama

    @property
    def codigo(self): return self._codigo

    @property
    def area(self): return self._area

    @property
    def estado(self): return self._estado

    def reservar(self):
        """RN-05: Solo se puede reservar si está disponible."""
        if self._estado != Cama.ESTADO_DISPONIBLE:
            raise CamaEstadoInvalidoError(f"No se puede reservar la cama {self.codigo} desde el estado {self._estado}")
        self._estado = Cama.ESTADO_RESERVADA

    def ocupar(self):
        """El paciente llegó físicamente a la cama."""
        if self._estado not in (self.ESTADO_DISPONIBLE, self.ESTADO_RESERVADA):
            raise CamaEstadoInvalidoError(f"No se puede ocupar la cama {self._codigo} desde el estado {self._estado}.")
        self._estado = self.ESTADO_OCUPADA

    def cancelar_reserva(self):
        """La reserva no llegó a usarse: la cama vuelve a estar disponible sin pasar por limpieza."""
        if self._estado != self.ESTADO_RESERVADA:
            raise CamaEstadoInvalidoError(f"La cama {self._codigo} no está reservada.")
        self._estado = self.ESTADO_DISPONIBLE

    def dar_alta(self):
        """RN-07: Al dar de alta, la cama no queda disponible, pasa a limpieza obligatoria."""
        if self._estado != self.ESTADO_OCUPADA:
            raise CamaEstadoInvalidoError(f"No se puede dar de alta la cama {self._codigo} porque no está ocupada.")
        self._estado = self.ESTADO_EN_LIMPIEZA

    def liberar_limpieza(self):
        """RN-08: Confirmación del personal de limpieza para volver a ponerla en circulación."""
        if self._estado != self.ESTADO_EN_LIMPIEZA:
            raise CamaEstadoInvalidoError(f"La cama {self._codigo} no está en limpieza.")
        self._estado = self.ESTADO_DISPONIBLE

    def fuera_de_servicio(self):
        """Para casos de mantenimiento o daños físicos.

        Deliberadamente, no valída el estado de origen: es una anulación
        administrativa (p. ej. un equipo que falla con el paciente aun
        dentro) y puede decretarse desde cualquier estado.
        """
        self._estado = self.ESTADO_FUERA_SERVICIO

    def volver_a_servicio(self):
        """Confirma que el mantenimiento terminó y la cama vuelve a circular."""
        if self._estado != self.ESTADO_FUERA_SERVICIO:
            raise CamaEstadoInvalidoError(f"La cama {self._codigo} no está fuera de servicio.")
        self._estado = self.ESTADO_DISPONIBLE

    @abstractmethod
    def es_compatible(self, nivel_triaje: int) -> bool:
        """
        Método abstracto. Cada tipo de cama definirá si es compatible
        con el nivel de urgencia (1=Rojo a 5=Azul).
        """
        pass

    def __str__(self):
        return f"[{self._codigo}] - {self.__class__.__name__} | Estado: {self._estado}"

#SUBCLASES DE CAMA
class CamaTraumaShock(Cama):
    """Cama de reanimación inmediata: solo para el nivel más crítico (Nivel I)."""

    def __init__(self, id_cama: int, codigo: str, area: str, estado: str, equipo_reanimacion: bool = True):
        super().__init__(id_cama, codigo, area, estado)
        self._equipo_reanimacion = equipo_reanimacion

    def es_compatible(self, nivel_triaje: int) -> bool:
        """Trauma Shock es estrictamente exclusiva del Nivel I (Rojo)."""
        return nivel_triaje == 1


class CamaUCI(Cama):
    def __init__(self, id_cama: int, codigo: str, area: str, estado: str, ventilador: bool = True):
        super().__init__(id_cama, codigo, area, estado)
        self._ventilador = ventilador # Atributo específico definido en el UML

    def es_compatible(self, nivel_triaje: int) -> bool:
        """UCI es compatible estrictamente con Nivel I (1) y Nivel II (2)"""
        return nivel_triaje in (1, 2)


class CamaObservacion(Cama):
    def __init__(self, id_cama: int, codigo: str, area: str, estado: str, monitor: bool = True):
        super().__init__(id_cama, codigo, area, estado)
        self._monitor = monitor

    def es_compatible(self, nivel_triaje: int) -> bool:
        """Observación es compatible con Niveles II (2), III (3) y IV (4)"""
        return nivel_triaje in (2, 3, 4)


class CamaHospitalizacion(Cama):
    def __init__(self, id_cama: int, codigo: str, area: str, estado: str, aislamiento: bool = False):
        super().__init__(id_cama, codigo, area, estado)
        self._aislamiento = aislamiento

    def es_compatible(self, nivel_triaje: int) -> bool:
        """Hospitalización general es para pacientes estables: Niveles III (3), IV (4) y V (5)"""
        return nivel_triaje in (3, 4, 5)