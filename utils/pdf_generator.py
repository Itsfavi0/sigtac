"""
Reporte de indicadores en PDF (ReportLab).

Solo presenta: recibe los datos ya calculados por ReporteController (IndicadoresPeriodo y EstadoGuardia)
y no consulta la BD ni decide reglas de negocio. Las funciones filas_* y formatear_* arman el texto de
cada tabla y se prueban sin abrir el PDF.
"""
import logging
import math
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models.estados import EstadoCama, EstadoEpisodio
from models.excepciones import ReporteError
from models.triaje import COLOR_POR_NIVEL, EpisodioEmergencia

if TYPE_CHECKING:
    # Solo para las anotaciones: reporte_controller importa este módulo, y una importación real sería circular.
    from controllers.reporte_controller import EstadoGuardia, IndicadoresPeriodo

logger = logging.getLogger(__name__)

SIN_DATOS = "Sin datos"
NIVELES = tuple(sorted(COLOR_POR_NIVEL))

# Color de las barras de cada nivel (solo presentación; el nombre del color viene de COLOR_POR_NIVEL)
_RGB_POR_NIVEL = {1: "#C62828", 2: "#EF6C00", 3: "#F9A825", 4: "#2E7D32", 5: "#1565C0"}
_COLOR_ENCABEZADO = colors.HexColor("#1F3A5F")
_COLOR_FILA_TOTAL = colors.HexColor("#E8EEF5")

_NOTAS = (
    "Espera hasta el triaje: desde el ingreso hasta el primer triaje.",
    "Espera hasta la cama: desde el ingreso hasta la asignación de cama.",
    "Estancia: desde el ingreso hasta el alta médica (no incluye referidos ni fugas).",
    "Reclasificación: triajes cuyo nivel final difiere del sugerido por el algoritmo.",
    "Ocupación: camas reservadas u ocupadas sobre las camas en servicio.",
)


# ---- Formato de los valores

def formatear_minutos(minutos: float | None) -> str:
    """45.5 → '45.5 min'; 125 → '2 h 05 min'; None → 'Sin datos'."""
    if minutos is None:
        return SIN_DATOS
    if minutos < 60:
        return f"{minutos:.1f} min"
    horas, resto = divmod(round(minutos), 60)
    return f"{horas} h {resto:02d} min"


def formatear_porcentaje(porcentaje: float | None, si_no_hay: str = SIN_DATOS) -> str:
    return si_no_hay if porcentaje is None else f"{porcentaje:.1f} %"


def _formatear_fecha(dia) -> str:
    return dia.strftime("%d/%m/%Y")


# ---- Contenido de las tablas (lista de filas [etiqueta, valor])

def filas_indicadores(indicadores: "IndicadoresPeriodo") -> list[tuple[str, str]]:
    """Indicadores del período. Los niveles sin triajes aparecen con 0."""
    filas = [
        ("Ingresos a emergencia", str(indicadores.ingresos)),
        ("Triajes registrados", str(indicadores.total_triajes)),
    ]
    filas += [(f"   Nivel {n} ({COLOR_POR_NIVEL[n]})", str(indicadores.triajes_por_nivel.get(n, 0)))
              for n in NIVELES]
    filas += [
        ("Triajes reclasificados", formatear_porcentaje(indicadores.porcentaje_reclasificacion)),
        ("Espera promedio hasta el triaje", formatear_minutos(indicadores.espera_triaje_min)),
        ("Espera promedio hasta la cama", formatear_minutos(indicadores.espera_cama_min)),
        ("Estancia promedio", formatear_minutos(indicadores.estancia_min)),
    ]
    return filas


def filas_camas(estado: "EstadoGuardia") -> list[tuple[str, str]]:
    """Camas por estado (todos los estados, en el orden del Enum), el total y la ocupación."""
    filas = [(e.value.capitalize(), str(estado.camas_por_estado.get(e, 0))) for e in EstadoCama]
    filas.append(("Total de camas", str(sum(estado.camas_por_estado.values()))))
    filas.append(("Ocupación", formatear_porcentaje(estado.porcentaje_ocupacion, "Sin camas en servicio")))
    return filas


def filas_pacientes(estado: "EstadoGuardia") -> list[tuple[str, str]]:
    """Pacientes en emergencia por estado (solo los estados abiertos) y el total."""
    abiertos = [e for e in EstadoEpisodio if e not in EpisodioEmergencia.ESTADOS_CERRADOS]
    filas = [(e.value.capitalize(), str(estado.pacientes_por_estado.get(e, 0))) for e in abiertos]
    filas.append(("Pacientes en emergencia", str(estado.pacientes_en_emergencia)))
    return filas


# ---- Construcción del PDF

def _tabla(encabezado: tuple[str, str], filas: list[tuple[str, str]], filas_resaltadas: int = 0) -> Table:
    """Tabla de dos columnas con encabezado; las últimas `filas_resaltadas` filas son totales."""
    tabla = Table([encabezado, *filas], colWidths=(11 * cm, 5 * cm))
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), _COLOR_ENCABEZADO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B0BEC5")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if filas_resaltadas:
        estilo += [("BACKGROUND", (0, -filas_resaltadas), (-1, -1), _COLOR_FILA_TOTAL),
                   ("FONTNAME", (0, -filas_resaltadas), (-1, -1), "Helvetica-Bold")]
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _grafico_triajes(indicadores: "IndicadoresPeriodo") -> Drawing:
    """Barras con los triajes por nivel, cada una con el color de su nivel."""
    valores = [indicadores.triajes_por_nivel.get(n, 0) for n in NIVELES]
    maximo = max(valores)
    paso = max(1, math.ceil(maximo / 5))  # marcas enteras en el eje: no hay "medio triaje"

    grafico = VerticalBarChart()
    grafico.x, grafico.y = 1.2 * cm, 1 * cm
    grafico.width, grafico.height = 14.5 * cm, 4.5 * cm
    grafico.data = [valores]
    grafico.categoryAxis.categoryNames = [f"{n} - {COLOR_POR_NIVEL[n]}" for n in NIVELES]
    grafico.valueAxis.valueMin = 0
    grafico.valueAxis.valueMax = paso * math.ceil(maximo / paso) + paso  # aire sobre la barra más alta
    grafico.valueAxis.valueStep = paso
    grafico.barLabelFormat = "%d"
    grafico.barLabels.nudge = 7
    for etiquetas in (grafico.categoryAxis.labels, grafico.valueAxis.labels, grafico.barLabels):
        etiquetas.fontName, etiquetas.fontSize = "Helvetica", 8  # la misma letra que el resto del reporte
    for i, n in enumerate(NIVELES):
        grafico.bars[(0, i)].fillColor = colors.HexColor(_RGB_POR_NIVEL[n])

    dibujo = Drawing(16 * cm, 6 * cm)
    dibujo.add(grafico)
    return dibujo


def _pie_de_pagina(lienzo, documento):
    lienzo.saveState()
    lienzo.setFont("Helvetica", 8)
    lienzo.setFillColor(colors.grey)
    lienzo.drawString(documento.leftMargin, 1.2 * cm,
                      "SIGTAC - prototipo académico: los indicadores no tienen validez clínica.")
    lienzo.drawRightString(A4[0] - documento.rightMargin, 1.2 * cm, f"Página {documento.page}")
    lienzo.restoreState()


def construir_reporte(indicadores: "IndicadoresPeriodo", estado: "EstadoGuardia",
                      generado_en: datetime, generado_por: str) -> bytes:
    """Arma el PDF en memoria y devuelve sus bytes (no escribe ningún archivo)."""
    estilos = getSampleStyleSheet()
    nota = ParagraphStyle("Nota", parent=estilos["Normal"], fontSize=8, textColor=colors.HexColor("#455A64"))
    periodo = f"{_formatear_fecha(indicadores.desde)} al {_formatear_fecha(indicadores.hasta)}"

    contenido = [
        Paragraph("SIGTAC - Reporte de indicadores de emergencia", estilos["Title"]),
        Paragraph(f"<b>Período:</b> {periodo}", estilos["Normal"]),
        # escape(): el nombre va dentro de un Paragraph, que interpreta '<' y '&' como marcado
        Paragraph(f"<b>Generado:</b> {generado_en.strftime('%d/%m/%Y %H:%M')} por {escape(generado_por)}",
                  estilos["Normal"]),
        Spacer(1, 0.6 * cm),
        Paragraph("1. Indicadores del período", estilos["Heading2"]),
        _tabla(("Indicador", "Valor"), filas_indicadores(indicadores)),
    ]
    if indicadores.total_triajes:
        contenido += [Spacer(1, 0.4 * cm),
                      KeepTogether([Paragraph("Triajes por nivel", estilos["Heading3"]),
                                    _grafico_triajes(indicadores)])]
    # KeepTogether: si una tabla no cabe en lo que queda de la hoja, pasa entera a la siguiente
    contenido += [
        Spacer(1, 0.4 * cm),
        KeepTogether([Paragraph("2. Estado de la guardia al generar el reporte", estilos["Heading2"]),
                      _tabla(("Estado de la cama", "Camas"), filas_camas(estado), filas_resaltadas=2)]),
        Spacer(1, 0.4 * cm),
        KeepTogether(_tabla(("Estado del paciente", "Pacientes"), filas_pacientes(estado), filas_resaltadas=1)),
        Spacer(1, 0.6 * cm),
        KeepTogether([Paragraph(texto, nota) for texto in _NOTAS]),
    ]

    memoria = BytesIO()
    documento = SimpleDocTemplate(memoria, pagesize=A4, title=f"SIGTAC - Indicadores {periodo}",
                                  author="SIGTAC", leftMargin=2 * cm, rightMargin=2 * cm,
                                  topMargin=2 * cm, bottomMargin=2 * cm)
    documento.build(contenido, onFirstPage=_pie_de_pagina, onLaterPages=_pie_de_pagina)
    return memoria.getvalue()


def validar_ruta_pdf(ruta: str | Path) -> Path:
    """Comprueba que la ruta termine en .pdf (sin tocar el disco). Lanza ValueError si no."""
    if not isinstance(ruta, (str, Path)) or not str(ruta).strip():
        raise ValueError("Indica dónde guardar el reporte.")
    ruta = Path(ruta)
    if ruta.suffix.lower() != ".pdf":
        raise ValueError("El reporte debe guardarse con la extensión .pdf.")
    return ruta


def guardar_reporte(ruta: str | Path, indicadores: "IndicadoresPeriodo", estado: "EstadoGuardia",
                    generado_en: datetime, generado_por: str) -> Path:
    """
    Genera el PDF y lo guarda en `ruta` (si ya existe, lo reemplaza). Devuelve la ruta.

    El PDF se arma completo en memoria antes de escribir: si algo falla al armarlo, no queda un archivo
    a medias. Si no se puede escribir (carpeta inexistente, sin permisos o el PDF abierto en otro
    programa) lanza ReporteError, con un mensaje para mostrar al usuario.
    """
    ruta = validar_ruta_pdf(ruta)
    contenido = construir_reporte(indicadores, estado, generado_en, generado_por)
    try:
        ruta.write_bytes(contenido)
    except OSError as error:
        logger.warning("No se pudo guardar el reporte PDF: %s", error.strerror)
        raise ReporteError("No se pudo guardar el reporte. Comprueba que la carpeta exista y que el "
                           "archivo no esté abierto en otro programa.") from error
    logger.info("Reporte PDF guardado (período %s a %s).", indicadores.desde, indicadores.hasta)
    return ruta
