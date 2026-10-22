from abc import ABC, abstractmethod
from datetime import date, datetime

from models.documento import DocumentoIdentidad
from models.excepciones import ReglaNegocioError


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


def _validar_documento(valor) -> DocumentoIdentidad:
    # El formato del número lo valida DocumentoIdentidad al crearse; aquí solo se exige que lo sea.
    if not isinstance(valor, DocumentoIdentidad):
        raise ValueError("documento debe ser un DocumentoIdentidad.")
    return valor


def _validar_fecha_nac(valor) -> date:
    # datetime es subclase de date: se excluye para no mezclar fechas con horas.
    if not isinstance(valor, date) or isinstance(valor, datetime):
        raise ValueError("La fecha de nacimiento debe ser una fecha (date).")
    if valor > _hoy():
        raise ValueError("La fecha de nacimiento no puede ser futura.")
    return valor


#CLASE PADRE
class Persona(ABC):
    """Superclase abstracta que define los atributos comunes de la persona"""
    # Solo un paciente puede registrarse sin documento (paciente sin identificar, NN).
    _ADMITE_SIN_DOCUMENTO = False

    def __init__(self, documento: DocumentoIdentidad | None, nombres: str, apellidos: str, fecha_nac : date):
        if documento is None and not self._ADMITE_SIN_DOCUMENTO:
            raise ValueError("El documento es obligatorio.")
        self._documento = None if documento is None else _validar_documento(documento)
        self._nombres = _validar_texto(nombres, "nombres")
        self._apellidos = _validar_texto(apellidos, "apellidos")
        self._fecha_nac = _validar_fecha_nac(fecha_nac)

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
    """
    Paciente del servicio de emergencia.

    Puede registrarse sin documento (documento=None) cuando llega sin identificar, por ejemplo
    inconsciente y sin papeles. Mientras no se identifique, sus nombres y su fecha de nacimiento
    son provisionales (ver no_identificado); identificar() los reemplaza por los reales.
    """
    # Coinciden con CH_paciente_sexo en schema.sql
    SEXOS_VALIDOS = ("M", "F")
    _ADMITE_SIN_DOCUMENTO = True
    # Nombre provisional de un paciente sin identificar (como en los hospitales: "NN", sin nombre).
    NOMBRE_NO_IDENTIFICADO = "NN"
    EDAD_MAXIMA_ESTIMADA = 120

    def __init__(self, id_paciente : int | None, documento: DocumentoIdentidad | None, nombres: str, apellidos: str, fecha_nac : date,
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

    @property
    def identificado(self) -> bool:
        """False si el paciente aún no tiene documento (paciente NN)."""
        return self._documento is not None

    @classmethod
    def no_identificado(cls, sexo: str, edad_estimada: int, id_seguro: int) -> "Paciente":
        """
        Crea un paciente sin identificar (aún sin id de BD). Nombres y apellidos quedan como "NN" y la
        fecha de nacimiento se estima a partir de la edad aparente: el 1 de enero de (año actual - edad).
        """
        if isinstance(edad_estimada, bool) or not isinstance(edad_estimada, int) \
                or not 0 <= edad_estimada <= cls.EDAD_MAXIMA_ESTIMADA:
            raise ValueError(f"La edad estimada debe ser un entero entre 0 y {cls.EDAD_MAXIMA_ESTIMADA}.")
        fecha_estimada = date(_hoy().year - edad_estimada, 1, 1)
        return cls(None, None, cls.NOMBRE_NO_IDENTIFICADO, cls.NOMBRE_NO_IDENTIFICADO,
                   fecha_estimada, sexo, id_seguro)

    def identificar(self, documento: DocumentoIdentidad, nombres: str, apellidos: str, fecha_nac: date):
        """
        Registra la identidad real de un paciente que ingresó sin identificar. Solo se hace una vez:
        el documento de un paciente identificado no cambia.
        """
        if self.identificado:
            raise ReglaNegocioError("El paciente ya está identificado.")
        # Se valida todo antes de modificar: si un dato es inválido, el paciente queda como estaba.
        documento = _validar_documento(documento)
        nombres = _validar_texto(nombres, "nombres")
        apellidos = _validar_texto(apellidos, "apellidos")
        fecha_nac = _validar_fecha_nac(fecha_nac)
        self._documento, self._nombres, self._apellidos, self._fecha_nac = documento, nombres, apellidos, fecha_nac

    def obtener_resumen(self) -> str:
        seguro = self.nombre_seguro or f"id {self.id_seguro}"
        documento = self.documento or "SIN IDENTIFICAR"
        return f"PACIENTE: [{documento} - {self.apellidos}, {self.nombres}] | Sexo: {self.sexo} | Seguro: {seguro}"

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
