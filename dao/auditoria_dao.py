import json
import logging

from dao.base_dao import BaseDAO
from models.auditoria import AccionAuditoria

logger = logging.getLogger(__name__)


class AuditoriaDAO(BaseDAO):
    """
    DAO de la tabla bitacora_auditoria. Los controladores llaman a registrar() después de cada
    operación sensible (la auditoría es explícita, no automática).

    La bitácora es de solo inserción: este DAO no tiene métodos para modificar ni borrar registros,
    porque una auditoría que se puede editar no sirve como evidencia.
    """

    # Tablas que se pueden auditar: todas las del esquema salvo la propia bitácora.
    # El nombre viaja como parámetro (no hay riesgo de inyección); la lista evita registros que
    # apunten a una tabla inexistente. tests/test_estados_vs_bd.py la compara con schema.sql.
    TABLAS_AUDITABLES = frozenset({
        "rol", "cargo", "seguro", "tipo_documento", "estado_episodio", "estado_cama", "area",
        "tipo_cama", "nivel_triaje", "sintoma", "empleado", "usuario", "paciente", "cama",
        "episodio_emergencia", "signos_vitales", "triaje", "triaje_sintoma", "asignacion_cama",
        "solicitud_limpieza", "historial_estado_cama",
    })

    @staticmethod
    def _validar_tabla(tabla: str) -> str:
        if tabla not in AuditoriaDAO.TABLAS_AUDITABLES:
            raise ValueError("Tabla no auditable.")
        return tabla

    @staticmethod
    def _a_registro(fila: dict) -> dict:
        """Convierte una fila de la bitácora en un diccionario, con los detalles ya decodificados."""
        detalles = fila["detalles_json"]
        if isinstance(detalles, (bytes, bytearray)):  # según la versión del conector, JSON llega como bytes
            detalles = detalles.decode("utf-8")
        return {
            "id_bitacora": fila["id_bitacora"],
            "id_usuario": fila["id_usuario"],
            "tabla_afectada": fila["tabla_afectada"],
            "accion": AccionAuditoria(fila["accion"]),
            "id_registro_afectado": fila["id_registro_afectado"],
            "fecha_hora": fila["fecha_hora"],
            "detalles": None if detalles is None else json.loads(detalles),
        }

    @staticmethod
    def registrar(id_usuario: int, tabla: str, accion: AccionAuditoria | str, id_registro: int,
                  detalles: dict | None = None) -> int:
        """
        Registra una operación en la bitácora y devuelve el id del registro.

        `detalles` es opcional y se guarda como JSON. No debe contener datos personales (documentos,
        nombres, claves): solo ids y valores no sensibles, p. ej. {"nivel_anterior": 3, "nivel_nuevo": 2}.
        La fecha y hora las pone MySQL.
        """
        AuditoriaDAO._validar_id(id_usuario, "id_usuario")
        AuditoriaDAO._validar_tabla(tabla)
        try:
            accion = AccionAuditoria(accion)
        except ValueError:
            raise ValueError("Acción de auditoría no reconocida.") from None
        AuditoriaDAO._validar_id(id_registro, "id_registro")
        detalles_json = None
        if detalles is not None:
            if not isinstance(detalles, dict):
                raise ValueError("detalles debe ser un diccionario.")
            try:
                detalles_json = json.dumps(detalles, ensure_ascii=False)
            except TypeError:
                raise ValueError("detalles solo puede contener valores convertibles a JSON.") from None

        id_nuevo = AuditoriaDAO._insertar(
            """
            INSERT INTO bitacora_auditoria (id_usuario, tabla_afectada, accion, id_registro_afectado, detalles_json)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id_usuario, tabla, accion.value, id_registro, detalles_json),
        )
        logger.info("Auditoría registrada (id_bitacora=%s, tabla=%s, accion=%s).", id_nuevo, tabla, accion.value)
        return id_nuevo

    @staticmethod
    def listar_por_registro(tabla: str, id_registro: int) -> list[dict]:
        """Historial de auditoría de un registro (p. ej. un paciente), del más antiguo al más reciente."""
        AuditoriaDAO._validar_tabla(tabla)
        AuditoriaDAO._validar_id(id_registro, "id_registro")
        filas = AuditoriaDAO._consultar_varios(
            """
            SELECT id_bitacora, id_usuario, tabla_afectada, accion, id_registro_afectado, fecha_hora, detalles_json
            FROM bitacora_auditoria
            WHERE tabla_afectada = %s AND id_registro_afectado = %s
            ORDER BY fecha_hora, id_bitacora
            """,
            (tabla, id_registro),
        )
        return [AuditoriaDAO._a_registro(fila) for fila in filas]
