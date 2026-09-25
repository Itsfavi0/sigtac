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
    """Se lanza cuando el orquestador intenta asignar una cama que ya fue tomada por otro usuario."""
    pass

class UsuarioSinPermisoError(SigtacError):
    """Se lanza cuando un empleado intenta realizar una acción fuera de los permisos de su rol."""
    pass

class NivelTriajeInvalidoError(SigtacError):
    """Se lanza cuando un algoritmo o usuario sugiere un nivel de triaje fuera del rango (1-5)."""
    pass

class ReglaNegocioError(SigtacError):
    """Se lanza cuando se viola una regla fundamental (ej. intentar dar de alta a un paciente que no tiene cama)."""
    pass