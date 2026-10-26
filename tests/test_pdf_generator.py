from datetime import date, datetime
from pathlib import Path

import pytest
from reportlab import rl_config

from controllers.reporte_controller import EstadoGuardia, IndicadoresPeriodo
from models.estados import EstadoCama, EstadoEpisodio
from models.excepciones import ReporteError
from utils import pdf_generator
from utils.pdf_generator import (construir_reporte, filas_camas, filas_indicadores, filas_pacientes,
                                 formatear_minutos, formatear_porcentaje, guardar_reporte, validar_ruta_pdf)

C, E = EstadoCama, EstadoEpisodio
GENERADO_EN = datetime(2026, 10, 26, 14, 30)


def indicadores(**cambios):
    datos = dict(desde=date(2026, 10, 1), hasta=date(2026, 10, 31), ingresos=42,
                 triajes_por_nivel={1: 2, 2: 5, 3: 14, 4: 9, 5: 3}, porcentaje_reclasificacion=12.1,
                 espera_triaje_min=8.4, espera_cama_min=47.0, estancia_min=312.6)
    return IndicadoresPeriodo(**{**datos, **cambios})


def estado(**cambios):
    datos = dict(camas_por_estado={C.DISPONIBLE: 4, C.RESERVADA: 1, C.OCUPADA: 2, C.EN_LIMPIEZA: 1,
                                   C.FUERA_SERVICIO: 2},
                 porcentaje_ocupacion=37.5,
                 pacientes_por_estado={E.EN_ESPERA_TRIAJE: 1, E.EN_ESPERA: 3, E.EN_ATENCION: 2})
    return EstadoGuardia(**{**datos, **cambios})


def vacios():
    """Un período sin actividad y una guardia sin camas: todos los promedios son None."""
    return (indicadores(ingresos=0, triajes_por_nivel={}, porcentaje_reclasificacion=None,
                        espera_triaje_min=None, espera_cama_min=None, estancia_min=None),
            estado(camas_por_estado={}, porcentaje_ocupacion=None, pacientes_por_estado={}))


# ---- Formato de los valores

@pytest.mark.parametrize("minutos, texto", [
    (None, "Sin datos"),
    (0, "0.0 min"),
    (8.4, "8.4 min"),
    (59.9, "59.9 min"),        # límite: todavía en minutos
    (60, "1 h 00 min"),        # límite: desde una hora se muestran horas
    (125.4, "2 h 05 min"),
    (312.6, "5 h 13 min"),     # los minutos se redondean
    (1440, "24 h 00 min"),
])
def test_formatear_minutos(minutos, texto):
    assert formatear_minutos(minutos) == texto


@pytest.mark.parametrize("porcentaje, texto", [(None, "Sin datos"), (0.0, "0.0 %"), (37.5, "37.5 %"),
                                               (100.0, "100.0 %")])
def test_formatear_porcentaje(porcentaje, texto):
    assert formatear_porcentaje(porcentaje) == texto


def test_porcentaje_sin_datos_con_otro_texto():
    assert formatear_porcentaje(None, "Sin camas en servicio") == "Sin camas en servicio"


# ---- Contenido de las tablas

def test_filas_de_indicadores():
    assert filas_indicadores(indicadores()) == [
        ("Ingresos a emergencia", "42"),
        ("Triajes registrados", "33"),
        ("   Nivel 1 (Rojo)", "2"),
        ("   Nivel 2 (Naranja)", "5"),
        ("   Nivel 3 (Amarillo)", "14"),
        ("   Nivel 4 (Verde)", "9"),
        ("   Nivel 5 (Azul)", "3"),
        ("Triajes reclasificados", "12.1 %"),
        ("Espera promedio hasta el triaje", "8.4 min"),
        ("Espera promedio hasta la cama", "47.0 min"),
        ("Estancia promedio", "5 h 13 min"),
    ]


def test_los_niveles_sin_triajes_aparecen_con_cero():
    filas = dict(filas_indicadores(indicadores(triajes_por_nivel={3: 4})))
    assert filas["   Nivel 1 (Rojo)"] == "0" and filas["   Nivel 3 (Amarillo)"] == "4"
    assert filas["Triajes registrados"] == "4"


def test_periodo_sin_actividad_muestra_sin_datos():
    ind, _ = vacios()
    filas = dict(filas_indicadores(ind))
    assert filas["Ingresos a emergencia"] == "0"
    assert [filas[k] for k in ("Triajes reclasificados", "Espera promedio hasta el triaje",
                               "Espera promedio hasta la cama", "Estancia promedio")] == ["Sin datos"] * 4


def test_filas_de_camas_en_el_orden_del_enum_con_total_y_ocupacion():
    assert filas_camas(estado()) == [
        ("Disponible", "4"), ("Reservada", "1"), ("Ocupada", "2"), ("En limpieza", "1"),
        ("Fuera de servicio", "2"), ("Total de camas", "10"), ("Ocupación", "37.5 %"),
    ]


def test_sin_camas_en_servicio():
    _, est = vacios()
    filas = dict(filas_camas(est))
    assert filas["Disponible"] == "0" and filas["Total de camas"] == "0"
    assert filas["Ocupación"] == "Sin camas en servicio"


def test_filas_de_pacientes_solo_estados_abiertos():
    assert filas_pacientes(estado()) == [
        ("En espera de triaje", "1"), ("En espera de cama", "3"), ("En atención (con cama)", "2"),
        ("Pacientes en emergencia", "6"),
    ]


# ---- PDF

@pytest.fixture
def sin_compresion(monkeypatch):
    """Escribe el texto del PDF sin comprimir, para poder buscarlo en los bytes."""
    monkeypatch.setattr(rl_config, "pageCompression", 0)


def test_construye_un_pdf_con_los_valores(sin_compresion):
    pdf = construir_reporte(indicadores(), estado(), GENERADO_EN, "Luis Ramos (JEFE DE GUARDIA)")
    assert pdf.startswith(b"%PDF-")
    for texto in (b"01/10/2026 al 31/10/2026", b"26/10/2026 14:30", b"Luis Ramos", b"JEFE DE GUARDIA",
                  b"Ingresos a emergencia", b"5 h 13 min", b"37.5 %", b"Triajes por nivel"):
        assert texto in pdf, texto


def test_sin_triajes_no_hay_grafico(sin_compresion):
    pdf = construir_reporte(*vacios(), GENERADO_EN, "Ana Torres")
    assert pdf.startswith(b"%PDF-")
    assert b"Sin camas en servicio" in pdf
    assert b"Triajes por nivel" not in pdf


def test_el_nombre_con_caracteres_de_marcado_no_rompe_el_pdf(sin_compresion):
    # Paragraph interpreta '<' y '&' como marcado: sin escape(), esto lanzaría un error al armar el PDF
    pdf = construir_reporte(indicadores(), estado(), GENERADO_EN, "Ana <b> & Cía")
    assert pdf.startswith(b"%PDF-")


def test_un_solo_nivel_con_muchos_triajes():
    pdf = construir_reporte(indicadores(triajes_por_nivel={1: 997}), estado(), GENERADO_EN, "Ana")
    assert pdf.startswith(b"%PDF-")


# ---- Ruta y guardado

@pytest.mark.parametrize("ruta", ["reporte.pdf", "reporte.PDF", Path("carpeta") / "octubre.pdf"])
def test_ruta_valida(ruta):
    assert validar_ruta_pdf(ruta) == Path(ruta)


@pytest.mark.parametrize("ruta, mensaje", [
    ("", "dónde"), ("   ", "dónde"), (None, "dónde"), (42, "dónde"),
    ("reporte", ".pdf"), ("reporte.txt", ".pdf"), ("reporte.pdf.txt", ".pdf"),
])
def test_ruta_invalida(ruta, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        validar_ruta_pdf(ruta)


def test_guardar_escribe_el_archivo(tmp_path):
    ruta = guardar_reporte(tmp_path / "octubre.pdf", indicadores(), estado(), GENERADO_EN, "Ana")
    assert ruta == tmp_path / "octubre.pdf"
    assert ruta.read_bytes().startswith(b"%PDF-")


def test_guardar_reemplaza_un_archivo_existente(tmp_path):
    ruta = tmp_path / "octubre.pdf"
    ruta.write_bytes(b"viejo")
    guardar_reporte(ruta, indicadores(), estado(), GENERADO_EN, "Ana")
    assert ruta.read_bytes().startswith(b"%PDF-")


def test_extension_invalida_no_escribe_nada(tmp_path):
    with pytest.raises(ValueError):
        guardar_reporte(tmp_path / "octubre.txt", indicadores(), estado(), GENERADO_EN, "Ana")
    assert list(tmp_path.iterdir()) == []


def test_carpeta_inexistente_lanza_reporte_error(tmp_path):
    with pytest.raises(ReporteError, match="carpeta"):
        guardar_reporte(tmp_path / "no_existe" / "octubre.pdf", indicadores(), estado(), GENERADO_EN, "Ana")


def test_archivo_abierto_en_otro_programa_lanza_reporte_error(tmp_path, monkeypatch):
    # En Windows, escribir sobre un PDF abierto en un visor da PermissionError
    def bloqueado(self, contenido):
        raise PermissionError(13, "Permission denied")
    monkeypatch.setattr(Path, "write_bytes", bloqueado)
    with pytest.raises(ReporteError, match="abierto en otro programa") as error:
        guardar_reporte(tmp_path / "octubre.pdf", indicadores(), estado(), GENERADO_EN, "Ana")
    assert isinstance(error.value.__cause__, PermissionError)


def test_si_falla_al_armar_el_pdf_no_queda_un_archivo_a_medias(tmp_path, monkeypatch):
    def falla(*args):
        raise RuntimeError("fallo de ReportLab")
    monkeypatch.setattr(pdf_generator, "construir_reporte", falla)
    with pytest.raises(RuntimeError):
        guardar_reporte(tmp_path / "octubre.pdf", indicadores(), estado(), GENERADO_EN, "Ana")
    assert list(tmp_path.iterdir()) == []
