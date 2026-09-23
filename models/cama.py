from abc import ABC, abstractmethod

class CamaEstadoInvalidoError(Exception):
    """Excepción lanzada cuando se intenta un cambio de estado ilegal de la cama"""
    pass

#CLASE PADRE
class Cama(ABC):
    """"Superclase abstracta para el manejo de camas y sus estados"""
    ESTADO_DISPONIBLE = "DISPONIBLE"
    ESTADO_RESERVADA = "RESERVADA"
    ESTADO_OCUPADA = "OCUPADA"
    ESTADO_EN_LIMPIEZA = "EN LIMPIEZA"
    ESTADO_FUERA_SERVICIO = "FUERA DE SERVICIO"

    def __init__(self, id_cama, codigo, area, estado : str = ESTADO_DISPONIBLE):
        self._id_cama = id_cama
        self._codigo = codigo
        self._area = area
        self._estado = estado

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
        """Para casos de mantenimiento o daños físicos."""
        self._estado = self.ESTADO_FUERA_SERVICIO

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