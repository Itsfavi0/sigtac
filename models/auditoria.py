from enum import StrEnum


class AccionAuditoria(StrEnum):
    """
    Acciones que se registran en la bitácora de auditoría (columna bitacora_auditoria.accion).
    Un Enum evita que la misma acción quede escrita de varias formas ("update", "Actualizar"...),
    lo que impediría agruparlas en los reportes.
    """
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    ANULAR = "ANULAR"            # RN-11: baja lógica
    IDENTIFICAR = "IDENTIFICAR"  # paciente sin identificar (NN) que recibe su documento
