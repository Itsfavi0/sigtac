from abc import ABC, abstractmethod
from datetime import date

#CLASE PADRE
class Persona(ABC):
    """Superclase abstracta que define los atributos comunes de la persona"""
    def __init__(self, dni : str, nombres: str, apellidos: str, fecha_nac : date):
        self._dni = dni
        self._nombres = nombres
        self._apellidos = apellidos
        self._fecha_nac = fecha_nac

    @property
    def dni(self): return self._dni

    @property
    def nombres(self): return self._nombres

    @property
    def apellidos(self): return self._apellidos

    def calcular_edad(self) -> int:
        hoy = date.today()
        return hoy.year - self._fecha_nac.year - ((hoy.month, hoy.day) < (self._fecha_nac.month, self._fecha_nac.day))

    @abstractmethod
    def obtener_resumen(self) -> str:
        """Método abstracto abstracto, define como se resumen a sí mismas"""
        pass

#SUBCLASE: PACIENTE
class Paciente(Persona):
    def __init__(self, id_paciente : int, dni : str, nombres: str, apellidos: str, fecha_nac : date, seguro: str):
        super().__init__(dni, nombres, apellidos, fecha_nac)
        self._id_paciente = id_paciente
        self._seguro = seguro
        self._episodios = []

    @property
    def id_paciente(self): return self._id_paciente

    @property
    def seguro(self): return self._seguro
    
    def obtener_resumen(self) -> str:
        return  f"PACIENTE: [{self.dni} - {self.apellidos}, {self.nombres}, {self.seguro}] | Seguro: {self.seguro}]"

    def agregar_episodio(self, episodio):
        self._episodios.append(episodio)

class Empleado(Persona):
    """Clase abstracta que extiende a Persona para el personal del Hospital"""
    def __init__(self, id_empleado : int, dni : str, nombres: str, apellidos: str, fecha_nac : date, cargo : str, colegiatura = None):
        super().__init__(dni, nombres, apellidos, fecha_nac)
        self._id_empleado = id_empleado
        self._cargo = cargo
        self._colegiatura = colegiatura

    def obtener_resumen(self) -> str:
        base = f"EMPLEADO [{self._id_empleado}] - {self._apellidos}, {self.nombres} | Cargo: {self._cargo}"

        if self._colegiatura:
            base += f" | Registro: {self._colegiatura}"

        return base

    @abstractmethod
    def tiene_permiso(self, modulo: str) -> bool:
        """Determina si el empleado tiene acceso a cierta parte del sistema"""
        pass

#SUBCLASES DE EMPLEADO
class Enfermero(Empleado):
    def __init__(self, id_empleado : int, dni : str, nombres: str, apellidos: str, fecha_nac : date, cargo : str, colegiatura : str, area : str):
        super().__init__(id_empleado, dni, nombres, apellidos, fecha_nac, cargo, colegiatura)
        self._area = area

    def registrar_triaje(self):
        # Lógica futura para cerrar el episodio
        pass

    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in ['triaje', 'camas']

class Medico(Empleado):
    def __init__(self, id_empleado: int, dni: str, nombres: str, apellidos: str, fecha_nac: date, cargo: str, colegiatura: str, especialidad: str):
        super().__init__(id_empleado, dni, nombres, apellidos, fecha_nac, cargo, colegiatura)
        self._especialidad = especialidad

    def dar_alta(self, episodio):
        # Lógica futura para cerrar el episodio
        pass

    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in ['triaje', 'camas', 'historias_clinicas']


class PersonalLimpieza(Empleado):
    def __init__(self, id_empleado: int, dni: str, nombres: str, apellidos: str, fecha_nac: date, cargo: str, turno: str):
        # El personal de limpieza usualmente no tiene colegiatura
        super().__init__(id_empleado, dni, nombres, apellidos, fecha_nac, cargo, colegiatura=None)
        self._turno = turno

    def atender_solicitud(self, id_solicitud: int):
        # Lógica futura para liberar camas
        pass

    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in ['limpieza']

