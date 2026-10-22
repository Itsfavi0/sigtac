from abc import ABC, abstractmethod
from datetime import date, datetime

from models.documento import DocumentoIdentidad


def _hoy() -> date:
    """Fecha actual. Está separada para que las pruebas puedan fijarla."""
    return date.today()


def _validar_id(valor, nombre: str):
    """Un id es un entero positivo, o None si el objeto aún no se ha guardado en la BD."""
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(f"{nombre} debe ser un entero positivo.")
    return valor


def _validar_texto(valor, nombre: str) -> str:
    """Texto obligatorio: no vacío ni compuesto solo de espacios. Se guarda sin espacios en los extremos."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nombre} es obligatorio.")
    return valor.strip()


def _validar_activo(valor) -> bool:
    if not isinstance(valor, bool):
        raise ValueError("activo debe ser True o False.")
    return valor


#CLASE PADRE
class Persona(ABC):
    """Superclase abstracta que define los atributos comunes de la persona"""
    def __init__(self, documento: DocumentoIdentidad, nombres: str, apellidos: str, fecha_nac : date):
        # El formato del número lo valida DocumentoIdentidad al crearse; aquí solo se exige que lo sea.
        if not isinstance(documento, DocumentoIdentidad):
            raise ValueError("documento debe ser un DocumentoIdentidad.")
        # datetime es subclase de date: se excluye para no mezclar fechas con horas.
        if not isinstance(fecha_nac, date) or isinstance(fecha_nac, datetime):
            raise ValueError("La fecha de nacimiento debe ser una fecha (date).")
        if fecha_nac > _hoy():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        self._documento = documento
        self._nombres = _validar_texto(nombres, "nombres")
        self._apellidos = _validar_texto(apellidos, "apellidos")
        self._fecha_nac = fecha_nac

    @property
    def documento(self): return self._documento

    @property
    def nombres(self): return self._nombres

    @property
    def apellidos(self): return self._apellidos

    @property
    def fecha_nac(self): return self._fecha_nac

    def calcular_edad(self) -> int:
        hoy = _hoy()
        return hoy.year - self._fecha_nac.year - ((hoy.month, hoy.day) < (self._fecha_nac.month, self._fecha_nac.day))

    @abstractmethod
    def obtener_resumen(self) -> str:
        """Método abstracto abstracto, define como se resumen a sí mismas"""
        pass

#SUBCLASE: PACIENTE
class Paciente(Persona):
    # Coinciden con CH_paciente_sexo en schema.sql
    SEXOS_VALIDOS = ("M", "F")

    def __init__(self, id_paciente : int | None, documento: DocumentoIdentidad, nombres: str, apellidos: str, fecha_nac : date,
                 sexo: str, id_seguro: int, activo: bool = True, nombre_seguro: str | None = None):
        super().__init__(documento, nombres, apellidos, fecha_nac)
        if sexo not in self.SEXOS_VALIDOS:
            raise ValueError("El sexo debe ser 'M' o 'F'.")
        if id_seguro is None:
            raise ValueError("id_seguro es obligatorio.")
        self._id_paciente = _validar_id(id_paciente, "id_paciente")
        self._sexo = sexo
        # id_seguro es la FK a la tabla seguro; nombre_seguro es opcional y solo sirve
        # para mostrarlo (el DAO lo obtiene con un JOIN).
        self._id_seguro = _validar_id(id_seguro, "id_seguro")
        self._nombre_seguro = None if nombre_seguro is None else _validar_texto(nombre_seguro, "nombre_seguro")
        self._episodios = []
        # Espejo de paciente.estado_registro en la BD (RN-11: no se elimina
        # físicamente, solo se anula lógicamente conservando el registro).
        self._activo = _validar_activo(activo)

    @property
    def id_paciente(self): return self._id_paciente

    @property
    def sexo(self): return self._sexo

    @property
    def id_seguro(self): return self._id_seguro

    @property
    def nombre_seguro(self): return self._nombre_seguro

    @property
    def activo(self): return self._activo

    def obtener_resumen(self) -> str:
        seguro = self.nombre_seguro or f"id {self.id_seguro}"
        return f"PACIENTE: [{self.documento} - {self.apellidos}, {self.nombres}] | Sexo: {self.sexo} | Seguro: {seguro}"

    def agregar_episodio(self, episodio):
        self._episodios.append(episodio)

    def anular(self):
        """RN-11: baja lógica. El registro se conserva, solo deja de estar activo."""
        self._activo = False

class Empleado(Persona):
    """Clase abstracta que extiende a Persona para el personal del Hospital"""
    def __init__(self, id_empleado : int | None, documento: DocumentoIdentidad, nombres: str, apellidos: str, fecha_nac : date,
                 cargo : str, colegiatura: str | None = None, activo: bool = True):
        super().__init__(documento, nombres, apellidos, fecha_nac)
        self._id_empleado = _validar_id(id_empleado, "id_empleado")
        self._cargo = _validar_texto(cargo, "cargo")
        self._colegiatura = None if colegiatura is None else _validar_texto(colegiatura, "colegiatura")
        # Espejo de empleado.estado_registro en la BD (RN-11: baja lógica).
        self._activo = _validar_activo(activo)

    @property
    def id_empleado(self): return self._id_empleado

    @property
    def cargo(self): return self._cargo

    @property
    def colegiatura(self): return self._colegiatura

    @property
    def activo(self): return self._activo

    def anular(self):
        """RN-11: baja lógica. El empleado se conserva (y su historial de auditoría), solo deja de estar activo."""
        self._activo = False

    def obtener_resumen(self) -> str:
        base = f"EMPLEADO [{self.id_empleado}] - {self.apellidos}, {self.nombres} | Cargo: {self.cargo}"

        if self.colegiatura:
            base += f" | Registro: {self.colegiatura}"

        return base

    @abstractmethod
    def tiene_permiso(self, modulo: str) -> bool:
        """Determina si el empleado tiene acceso a cierta parte del sistema"""
        pass

#SUBCLASES DE EMPLEADO
class Enfermero(Empleado):
    def __init__(self, id_empleado : int | None, documento: DocumentoIdentidad, nombres: str, apellidos: str, fecha_nac : date,
                 cargo : str, colegiatura : str | None, area : str, activo: bool = True):
        super().__init__(id_empleado, documento, nombres, apellidos, fecha_nac, cargo, colegiatura, activo)
        # Nombre del área asignada (tabla area, mediante empleado.id_area).
        self._area = _validar_texto(area, "area")

    @property
    def area(self): return self._area

    def obtener_resumen(self) -> str:
        return f"{super().obtener_resumen()} | Área: {self.area}"

    def registrar_triaje(self):
        # Lógica futura para registrar el triaje
        pass

    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in ['triaje', 'camas']

class Medico(Empleado):
    def __init__(self, id_empleado: int | None, documento: DocumentoIdentidad, nombres: str, apellidos: str, fecha_nac: date,
                 cargo: str, colegiatura: str | None, especialidad: str, activo: bool = True):
        super().__init__(id_empleado, documento, nombres, apellidos, fecha_nac, cargo, colegiatura, activo)
        self._especialidad = _validar_texto(especialidad, "especialidad")

    @property
    def especialidad(self): return self._especialidad

    def obtener_resumen(self) -> str:
        return f"{super().obtener_resumen()} | Especialidad: {self.especialidad}"

    def dar_alta(self, episodio):
        # Lógica futura para cerrar el episodio
        pass

    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in ['triaje', 'camas', 'historias_clinicas']


class PersonalLimpieza(Empleado):
    # Coinciden con CH_empleado_turno en schema.sql
    TURNOS_VALIDOS = ("MAÑANA", "TARDE", "NOCHE")

    def __init__(self, id_empleado: int | None, documento: DocumentoIdentidad, nombres: str, apellidos: str, fecha_nac: date,
                 cargo: str, turno: str, activo: bool = True):
        # El personal de limpieza usualmente no tiene colegiatura
        super().__init__(id_empleado, documento, nombres, apellidos, fecha_nac, cargo, colegiatura=None, activo=activo)
        if turno not in self.TURNOS_VALIDOS:
            raise ValueError(f"El turno debe ser uno de: {', '.join(self.TURNOS_VALIDOS)}.")
        self._turno = turno

    @property
    def turno(self): return self._turno

    def obtener_resumen(self) -> str:
        return f"{super().obtener_resumen()} | Turno: {self.turno}"

    def atender_solicitud(self, id_solicitud: int):
        # Lógica futura para liberar camas
        pass

    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in ['limpieza']
