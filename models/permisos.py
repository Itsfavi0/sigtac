from enum import StrEnum


class Rol(StrEnum):
    """Roles del sistema. Los valores coinciden con la tabla rol de la BD (nombre_rol)."""
    ADMINISTRADOR = "Administrador"
    JEFE_GUARDIA = "Jefe de Guardia"
    MEDICO = "Médico de Emergencia"
    ENFERMERO = "Enfermero de Triaje"
    LIMPIEZA = "Personal de Limpieza"


class Permiso(StrEnum):
    """Módulos o acciones del sistema que se autorizan por rol."""
    PACIENTES = "pacientes"            # registrar, identificar y fusionar pacientes NN
    TRIAJE = "triaje"                  # registrar y reclasificar triajes
    GESTION_CAMAS = "gestion_camas"    # asignar, cancelar reservas y dar de alta
    VER_CAMAS = "ver_camas"            # mapa de camas (solo lectura)
    LIMPIEZA = "limpieza"              # confirmar la limpieza de una cama (RN-08)
    REPORTES = "reportes"
    ADMINISTRACION = "administracion"  # usuarios y bitácora de auditoría


# Matriz de permisos: el permiso depende del ROL del usuario (usuario.id_rol), no del cargo ni de la
# subclase de Empleado: el cargo laboral y los permisos del software son conceptos distintos (por eso
# rol y cargo son tablas separadas). Es el único lugar donde se define quién puede hacer qué.
PERMISOS_POR_ROL = {
    Rol.ADMINISTRADOR: frozenset({Permiso.VER_CAMAS, Permiso.REPORTES, Permiso.ADMINISTRACION}),
    Rol.JEFE_GUARDIA: frozenset({Permiso.PACIENTES, Permiso.TRIAJE, Permiso.GESTION_CAMAS, Permiso.VER_CAMAS,
                                 Permiso.REPORTES}),
    Rol.MEDICO: frozenset({Permiso.PACIENTES, Permiso.TRIAJE, Permiso.GESTION_CAMAS, Permiso.VER_CAMAS}),
    Rol.ENFERMERO: frozenset({Permiso.PACIENTES, Permiso.TRIAJE, Permiso.VER_CAMAS}),
    Rol.LIMPIEZA: frozenset({Permiso.VER_CAMAS, Permiso.LIMPIEZA}),
}


def tiene_permiso(rol: Rol | str, permiso: Permiso | str) -> bool:
    """
    Indica si un rol tiene un permiso. `rol` puede ser el nombre_rol de la sesión (texto).

    Un rol desconocido no tiene ningún permiso (se deniega por defecto). Un permiso desconocido es un
    error de programación y lanza ValueError. Si el permiso falta, el controlador es quien lanza
    UsuarioSinPermisoError: el modelo solo responde la pregunta.
    """
    try:
        permiso = Permiso(permiso)
    except ValueError:
        raise ValueError("Permiso no reconocido.") from None
    try:
        rol = Rol(rol)
    except ValueError:
        return False
    return permiso in PERMISOS_POR_ROL[rol]
