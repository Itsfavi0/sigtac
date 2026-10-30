"""
Cómo se escriben en pantalla los datos del modelo (nombres, documentos, tiempos y fechas) y cómo se leen los números
y las fechas que escribe el usuario.

Son funciones puras (sin widgets) para probarlas sin ventana. No contienen reglas de negocio: el plazo de cada
nivel y si se excede vienen de models/triaje.py; aquí solo se decide cómo se lee.
"""
from datetime import date, datetime

from models.persona import Paciente
from models.triaje import TIEMPO_MAXIMO_POR_NIVEL

SIN_DOCUMENTO = "Sin documento"
SEXO = {"M": "varón", "F": "mujer"}
_DIAS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def nombre_corto(paciente: Paciente) -> str:
    """«María Salazar Quispe» → «M. Salazar»; un NN → «NN · varón, ~40 años» (lo que se sabe de él)."""
    if not paciente.identificado:
        return f"NN · {SEXO[paciente.sexo]}, ~{paciente.calcular_edad()} años"
    return f"{paciente.nombres.strip()[0]}. {paciente.apellidos.split()[0]}"


def documento_enmascarado(paciente: Paciente) -> str:
    """«DNI 43•••19»: tipo, dos primeros y dos últimos caracteres. La pantalla puede verla cualquiera."""
    documento = paciente.documento
    if documento is None:
        return SIN_DOCUMENTO
    numero = documento.numero
    return f"{documento.tipo.value} {numero[:2]}•••{numero[-2:]}"


def minutos_desde(inicio: datetime, ahora: datetime) -> int:
    """Minutos completos transcurridos (nunca negativos, aunque los relojes de dos PCs difieran)."""
    return max(0, int((ahora - inicio).total_seconds() // 60))


def texto_minutos(minutos: int, con_cero: bool = True) -> str:
    """7 → «07 min» (alinea en columnas; con con_cero=False, «7 min»); 75 → «1 h 15 min»."""
    if minutos < 60:
        return f"{minutos:02d} min" if con_cero else f"{minutos} min"
    horas, resto = divmod(minutos, 60)
    return f"{horas} h {resto:02d} min"


def texto_plazo(nivel: int) -> str:
    """El tiempo máximo de espera del nivel: «Inmediato» o «Plazo 10 min»."""
    maximo = TIEMPO_MAXIMO_POR_NIVEL[nivel]
    return "Inmediato" if maximo == 0 else f"Plazo {maximo} min"


def fecha_corta(dia: date) -> str:
    """«Lun, 27 oct 2026», sin depender de la configuración regional de Windows."""
    return f"{_DIAS[dia.weekday()]}, {dia.day} {_MESES[dia.month - 1]} {dia.year}"


def fecha_numerica(dia: date) -> str:
    """«14/03/1985»: la forma en que se escribe una fecha en un campo (la que lee leer_fecha)."""
    return dia.strftime("%d/%m/%Y")


def hora(momento: datetime, con_segundos: bool = False) -> str:
    return momento.strftime("%H:%M:%S" if con_segundos else "%H:%M")


def porcentaje(parte: int, total: int) -> str:
    """«42 %»; sin total, «—»."""
    return f"{round(100 * parte / total)} %" if total else "—"


# ---- Lo que escribe el usuario: texto → dato. Un texto que no se puede leer es un ValueError con su mensaje.

def leer_numero(texto: str, nombre: str, decimales: bool = False) -> int | float:
    """
    «120» → 120; con decimales, «37,5» o «37.5» → 37.5 (en Perú se escriben las dos). Si no es un número, el
    ValueError dice qué campo es («Temperatura debe ser un número.»). No decide rangos: eso es del modelo.
    """
    limpio = texto.strip().replace(",", ".") if decimales else texto.strip()
    try:
        return float(limpio) if decimales else int(limpio)
    except ValueError:
        tipo = "un número" if decimales else "un número entero"
        raise ValueError(f"{nombre} debe ser {tipo}.") from None


def leer_fecha(texto: str, nombre: str) -> date:
    """«14/03/1985» → date(1985, 3, 14). Otra forma, o una fecha que no existe, es un ValueError."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ValueError(f"{nombre} debe tener la forma dd/mm/aaaa (por ejemplo, 14/03/1985).") from None
