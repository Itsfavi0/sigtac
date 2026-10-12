import logging


def configurar_logging(nivel: int = logging.INFO) -> None:
    """
    Configura el logging de toda la aplicación. Debe llamarse una sola vez,
    desde el punto de entrada (main). Sin esto, los logger.info() no se muestran.
    """
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
