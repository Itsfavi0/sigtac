"""
Un período de días completos (p. ej. del 1 al 31 de octubre, ambos incluidos), como lo piden los indicadores
(ReporteController) y la bitácora (AdminController). Se valida aquí una sola vez y se convierte en el rango
[desde 00:00, hasta + 1 día 00:00) con que consultan los DAO.
"""
from datetime import date, datetime, time, timedelta

# El rango de DATETIME de MySQL (años 1000 a 9999). Al último día se le suma uno para incluirlo completo, así que el
# 31/12/9999 no cabría (Python lanzaría OverflowError, que las vistas no esperan)
ANIO_MINIMO, ANIO_MAXIMO = 1000, 9998


def rango_de_dias(desde: date, hasta: date) -> tuple[datetime, datetime]:
    """El rango [inicio, fin) que cubre los dos días completos. ValueError si el período no es válido."""
    for valor in (desde, hasta):
        # datetime es subclase de date: se exige un día, sin hora
        if not isinstance(valor, date) or isinstance(valor, datetime):
            raise ValueError("El período se indica con días (date), sin hora.")
    if desde > hasta:
        raise ValueError("La fecha inicial no puede ser posterior a la final.")
    if desde.year < ANIO_MINIMO or hasta.year > ANIO_MAXIMO:
        raise ValueError(f"El período debe estar entre los años {ANIO_MINIMO} y {ANIO_MAXIMO}.")
    return datetime.combine(desde, time.min), datetime.combine(hasta + timedelta(days=1), time.min)
