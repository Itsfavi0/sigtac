"""
Cómo se escribe un número decimal para el usuario: con coma, como en castellano («37,5»). Lo usan los criterios del
triaje (models/estrategias.py), las pantallas y el PDF, para que un mismo dato se lea igual en todos.
"""


def texto_decimal(valor, decimales: int | None = None) -> str:
    """
    37.5 → «37,5». Sin `decimales`, sin ceros de sobra (8.5, no 8.50; 39.0 → «39»), aunque llegue como
    Decimal; con ellos, siempre esa cantidad (45 → «45,0» con decimales=1).
    """
    texto = f"{float(valor):g}" if decimales is None else f"{float(valor):.{decimales}f}"
    return texto.replace(".", ",")
