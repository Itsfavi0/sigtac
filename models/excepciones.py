# ==========================================
# EXCEPCIONES DEL DOMINIO (SIGTAC)
# ==========================================

class SigtacError(Exception):
    """Clase base para todas las excepciones personalizadas del sistema."""
    pass

class CamaEstadoInvalidoError(SigtacError):
    """Se lanza cuando se intenta una transición de estado no permitida en una cama."""
    pass

class CamaNoDisponibleError(SigtacError):
    """
    Se lanza cuando la cama ya no está en el estado esperado en la BD (otro usuario la tomó o la
    cambió antes) o ya no existe.
    """
    pass

class AutenticacionError(SigtacError):
    """
    Se lanza cuando el inicio de sesión falla. El mensaje es siempre el mismo (no dice si el documento
    no existe, la clave es incorrecta o la cuenta está bloqueada) para no dar pistas a un atacante.
    """
    pass

class UsuarioSinPermisoError(SigtacError):
    """
    Se lanza cuando un empleado intenta realizar una acción fuera de los permisos de su rol, o cuando no
    hay una sesión activa.
    """
    pass

class NivelTriajeInvalidoError(SigtacError):
    """Se lanza cuando un algoritmo o usuario sugiere un nivel de triaje fuera del rango (1-5)."""
    pass

class ReglaNegocioError(SigtacError):
    """Se lanza cuando se viola una regla fundamental (ej. intentar dar de alta a un paciente que no tiene cama)."""
    pass

class SignosVitalesIncompletosError(SigtacError):
    """Se lanza cuando falta un signo vital que el algoritmo de triaje necesita para clasificar."""
    pass

class ReporteError(SigtacError):
    """Se lanza cuando no se pudo guardar un reporte (p. ej. el PDF está abierto en otro programa)."""
    pass

class PersistenciaError(SigtacError):
    """Se lanza cuando una operación sobre la base de datos no se pudo completar."""
    pass

class ConexionBDError(PersistenciaError):
    """Se lanza cuando falta configuración (.env) o no se puede conectar a la base de datos."""
    pass

class RegistroDuplicadoError(PersistenciaError):
    """Se lanza cuando se intenta guardar un registro que viola una restricción de unicidad (p. ej. documento de identidad repetido)."""
    pass
