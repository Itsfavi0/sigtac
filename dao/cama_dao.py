import logging

from dao.base_dao import BaseDAO
from dao.transaccion import transaccion
from models.cama import Cama, CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.estados import EstadoCama
from models.excepciones import CamaNoDisponibleError

logger = logging.getLogger(__name__)


class CamaDAO(BaseDAO):
    """
    DAO de la tabla cama. Convierte cada fila en la subclase de Cama que corresponde a su tipo
    (fábrica simple), para que la compatibilidad con el nivel de triaje se decida por
    polimorfismo con cama.es_compatible(nivel), no en SQL.

    Solo trabaja con camas activas (estado_registro = TRUE): el modelo Cama no representa la baja.
    """

    # Fábrica: nombre del tipo en la tabla tipo_cama → subclase. Se usa el nombre (UNIQUE)
    # y no el id, porque los ids dependen del orden de inserción del seed.
    # tests/test_estados_vs_bd.py comprueba que coincida con seed.sql.
    CLASES_POR_TIPO = {
        "Cama de Trauma Shock": CamaTraumaShock,
        "Cama UCI con Ventilador": CamaUCI,
        "Cama de Observación con Monitor": CamaObservacion,
        "Cama de Hospitalización General": CamaHospitalizacion,
    }

    _SELECT = """
        SELECT c.id_cama, c.codigo, a.nombre_area, t.nombre_tipo_cama, e.nombre_estado_cama
        FROM cama c
        JOIN area a ON c.id_area = a.id_area
        JOIN tipo_cama t ON c.id_tipo_cama = t.id_tipo_cama
        JOIN estado_cama e ON c.id_estado_cama = e.id_estado_cama
        WHERE c.estado_registro = TRUE
    """
    _ORDEN = " ORDER BY a.nombre_area, c.codigo"

    @staticmethod
    def _a_cama(fila: dict) -> Cama:
        """Crea la subclase de Cama que corresponde al tipo de la fila."""
        clase = CamaDAO.CLASES_POR_TIPO.get(fila["nombre_tipo_cama"])
        if clase is None:
            raise ValueError("Tipo de cama sin clase asociada en CamaDAO.CLASES_POR_TIPO.")
        # EstadoCama(...) lanza ValueError si el estado de la BD no existe en el Enum
        return clase(fila["id_cama"], fila["codigo"], fila["nombre_area"], EstadoCama(fila["nombre_estado_cama"]))

    @staticmethod
    def buscar_por_id(id_cama: int) -> Cama | None:
        """Devuelve la cama activa con ese id, o None si no existe o está dada de baja."""
        fila = CamaDAO._consultar_uno(CamaDAO._SELECT + " AND c.id_cama = %s", (id_cama,))
        return CamaDAO._a_cama(fila) if fila else None

    @staticmethod
    def buscar_por_codigo(codigo: str) -> Cama | None:
        """Devuelve la cama activa con ese código (p. ej. 'UCI-01'), o None si no existe."""
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError("El código de cama es obligatorio.")
        fila = CamaDAO._consultar_uno(CamaDAO._SELECT + " AND c.codigo = %s", (codigo.strip(),))
        return CamaDAO._a_cama(fila) if fila else None

    @staticmethod
    def listar_activas() -> list[Cama]:
        """Todas las camas activas, en cualquier estado, ordenadas por área y código (mapa de camas)."""
        return [CamaDAO._a_cama(f) for f in CamaDAO._consultar_varios(CamaDAO._SELECT + CamaDAO._ORDEN)]

    @staticmethod
    def listar_disponibles() -> list[Cama]:
        """
        Camas activas en estado DISPONIBLE. El filtro por estado se hace en SQL; la
        compatibilidad con el nivel de triaje la decide el controlador con es_compatible().
        """
        filas = CamaDAO._consultar_varios(
            CamaDAO._SELECT + " AND e.nombre_estado_cama = %s" + CamaDAO._ORDEN,
            (EstadoCama.DISPONIBLE.value,),
        )
        return [CamaDAO._a_cama(f) for f in filas]

    @staticmethod
    def cambiar_estado(cama: Cama, estado_anterior: EstadoCama | str) -> None:
        """
        Guarda el estado actual de `cama` y lo registra en historial_estado_cama, en una transacción.

        La transición la valida antes el modelo (cama.reservar(), cama.dar_alta()...); este método
        solo la persiste:

            anterior = cama.estado
            cama.reservar()
            CamaDAO.cambiar_estado(cama, anterior)

        El UPDATE es condicional: solo cambia la cama si en la BD sigue en `estado_anterior`. Si otro
        usuario la cambió antes (o la cama no existe o está dada de baja) lanza CamaNoDisponibleError
        y no se guarda nada; el objeto `cama` queda desactualizado y conviene volver a consultarla.
        Se lanza una excepción en lugar de devolver False para que, dentro de la transacción de un
        controlador, se deshaga toda la operación.
        """
        if not isinstance(cama, Cama):
            raise ValueError("cama debe ser una Cama.")
        id_cama = cama.id_cama
        if isinstance(id_cama, bool) or not isinstance(id_cama, int) or id_cama <= 0:
            raise ValueError("La cama no tiene un id válido.")
        try:
            estado_anterior = EstadoCama(estado_anterior)
        except ValueError:
            raise ValueError("Estado anterior no reconocido.") from None
        estado_nuevo = cama.estado
        if estado_nuevo == estado_anterior:
            raise ValueError("La cama no cambió de estado.")

        # Los ids de estado se obtienen del catálogo por su nombre (el valor del Enum), con subconsultas.
        with transaccion():
            filas = CamaDAO._ejecutar(
                """
                UPDATE cama
                SET id_estado_cama = (SELECT id_estado_cama FROM estado_cama WHERE nombre_estado_cama = %s)
                WHERE id_cama = %s AND estado_registro = TRUE
                  AND id_estado_cama = (SELECT id_estado_cama FROM estado_cama WHERE nombre_estado_cama = %s)
                """,
                (estado_nuevo.value, id_cama, estado_anterior.value),
            )
            if filas == 0:
                logger.warning("Cambio de estado rechazado: la cama ya no está en %s (id_cama=%s).",
                               estado_anterior.value, id_cama)
                raise CamaNoDisponibleError(
                    f"La cama {cama.codigo} ya no está en estado {estado_anterior.value}: otro usuario la cambió."
                )
            CamaDAO._insertar(
                """
                INSERT INTO historial_estado_cama (id_cama, id_estado_cama)
                VALUES (%s, (SELECT id_estado_cama FROM estado_cama WHERE nombre_estado_cama = %s))
                """,
                (id_cama, estado_nuevo.value),
            )
        logger.info("Cama %s: %s -> %s.", id_cama, estado_anterior.value, estado_nuevo.value)
