"""
Colores de los niveles de triaje y de los estados de cama, compartidos por las vistas (views/tema.py) y el reporte
PDF (utils/pdf_generator.py).

Cada color es un par (modo claro, modo oscuro): CustomTkinter dibuja el del modo activo y el PDF, que se imprime
sobre blanco, usa el claro. Solo presentación: el nombre de cada color de triaje (Rojo, Naranja...) es un dato del
dominio y vive en models/triaje.py (COLOR_POR_NIVEL).
"""
from models.estados import EstadoCama

# Relleno de la etiqueta de cada nivel de triaje (1 = el más urgente)
NIVEL = {
    1: ("#D93025", "#FF453A"),
    2: ("#E8710A", "#FF9F0A"),
    3: ("#F9AB00", "#FFD60A"),
    4: ("#188038", "#30D158"),
    5: ("#1967D2", "#0A84FF"),
}

# Borde de cada estado de cama en la matriz (el estado también va escrito en la casilla: nunca solo color)
ESTADO_CAMA = {
    EstadoCama.DISPONIBLE: ("#1E8E3E", "#34C759"),
    EstadoCama.RESERVADA: ("#7B4FD6", "#BF8CFF"),
    EstadoCama.OCUPADA: ("#D93025", "#FF453A"),
    EstadoCama.EN_LIMPIEZA: ("#B26A00", "#FFD60A"),
    EstadoCama.FUERA_SERVICIO: ("#8E8E93", "#8E8E93"),
}
