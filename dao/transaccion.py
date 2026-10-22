import logging
from contextlib import contextmanager

import mysql.connector

from dao.db_connection import ConexionBD
from models.excepciones import PersistenciaError

logger = logging.getLogger(__name__)


@contextmanager
def transaccion():
    """
    Agrupa varias escrituras en una sola unidad: o se guardan todas (COMMIT) o ninguna (ROLLBACK).

        with transaccion():
            CamaDAO.cambiar_estado(...)
            AsignacionDAO.crear(...)
            AuditoriaDAO.registrar(...)   # la auditoría va dentro: no queda un cambio sin auditar

    Cualquier excepción dentro del bloque deshace todo y se vuelve a lanzar.

    Si ya hay una transacción abierta, este bloque se une a ella en lugar de abrir otra: así un
    método DAO de varios pasos puede usar transaccion() y funcionar tanto solo como dentro de la
    transacción de un controlador. Por eso, dentro de una transacción, una excepción debe llegar
    hasta el bloque más externo: si se captura a mitad de camino, el resto se confirmaría igual.

    La conexión es compartida: hay una sola transacción a la vez.
    """
    bd = ConexionBD()
    if bd.en_transaccion:
        yield  # se une a la transacción abierta; la confirma o deshace el bloque externo
        return

    try:
        bd.iniciar_transaccion()  # ConexionBDError (sin conexión) se propaga tal cual
    except mysql.connector.Error as e:
        logger.error("ERROR DAO: no se pudo iniciar la transacción (errno=%s).", e.errno)
        raise PersistenciaError("No se pudo iniciar la operación en la base de datos.") from e

    exito = False
    try:
        yield
        exito = True
    finally:
        # try/finally en lugar de "except Exception": se deshace ante cualquier error sin capturarlo.
        if exito:
            _confirmar(bd)
        else:
            _deshacer(bd)


def _confirmar(bd: ConexionBD) -> None:
    try:
        bd.terminar_transaccion(confirmar=True)
    except mysql.connector.Error as e:
        logger.error("ERROR DAO: no se pudo confirmar la transacción (errno=%s).", e.errno)
        _deshacer(bd)
        raise PersistenciaError("No se pudo confirmar la operación en la base de datos.") from e
    logger.debug("Transacción confirmada.")


def _deshacer(bd: ConexionBD) -> None:
    try:
        bd.terminar_transaccion(confirmar=False)
    except mysql.connector.Error as e:
        # No se relanza: ocultaría el error original. Si la conexión se perdió, MySQL ya deshizo
        # la transacción al cerrarla.
        logger.error("ERROR DAO: no se pudo deshacer la transacción (errno=%s).", e.errno)
        return
    logger.warning("Transacción deshecha (ROLLBACK).")
