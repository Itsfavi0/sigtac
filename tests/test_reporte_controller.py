from datetime import date, datetime

import pytest

from controllers import reporte_controller
from controllers.reporte_controller import ReporteController
from models.estados import EstadoCama, EstadoEpisodio
from models.excepciones import ReporteError, UsuarioSinPermisoError
from models.permisos import Rol

C, E = EstadoCama, EstadoEpisodio


@pytest.fixture
def datos(capa_datos):
    return capa_datos(reporte_controller, "ReporteDAO")


@pytest.fixture
def ctrl(sesion_de):
    return ReporteController(sesion_de(Rol.JEFE_GUARDIA))


@pytest.mark.parametrize("metodo, args", [("estado_actual", ()), ("indicadores", (date(2026, 10, 1), date(2026, 10, 31)))])
@pytest.mark.parametrize("rol", [Rol.MEDICO, Rol.ENFERMERO, Rol.LIMPIEZA])
def test_sin_permiso_de_reportes(datos, sesion_de, metodo, args, rol):
    with pytest.raises(UsuarioSinPermisoError):
        getattr(ReporteController(sesion_de(rol)), metodo)(*args)
    assert datos.llamadas() == []


@pytest.mark.parametrize("rol", [Rol.JEFE_GUARDIA, Rol.ADMINISTRADOR])
def test_jefe_y_administrador_ven_los_reportes(datos, sesion_de, rol):
    datos["ReporteDAO"].contar_camas_por_estado.return_value = {}
    datos["ReporteDAO"].contar_episodios_por_estado.return_value = {}
    ReporteController(sesion_de(rol)).estado_actual()


# ---- Estado actual

def test_ocupacion_y_pacientes_en_emergencia(datos, ctrl):
    datos["ReporteDAO"].contar_camas_por_estado.return_value = {
        C.DISPONIBLE: 4, C.RESERVADA: 1, C.OCUPADA: 2, C.EN_LIMPIEZA: 1, C.FUERA_SERVICIO: 2}
    datos["ReporteDAO"].contar_episodios_por_estado.return_value = {
        E.EN_ESPERA_TRIAJE: 1, E.EN_ESPERA: 3, E.EN_ATENCION: 2, E.ALTA: 40, E.REFERIDO: 2, E.FUGADO: 1}
    estado = ctrl.estado_actual()
    assert estado.porcentaje_ocupacion == 37.5  # (1 reservada + 2 ocupadas) / (10 - 2 fuera de servicio)
    assert estado.pacientes_por_estado == {E.EN_ESPERA_TRIAJE: 1, E.EN_ESPERA: 3, E.EN_ATENCION: 2}
    assert estado.pacientes_en_emergencia == 6
    assert estado.camas_por_estado[C.FUERA_SERVICIO] == 2
    assert datos.llamadas() == ["inicio", "ReporteDAO.contar_camas_por_estado",
                                "ReporteDAO.contar_episodios_por_estado", "commit"]


def test_sin_camas_en_servicio_la_ocupacion_es_none(datos, ctrl):
    datos["ReporteDAO"].contar_camas_por_estado.return_value = {C.DISPONIBLE: 0, C.FUERA_SERVICIO: 3}
    datos["ReporteDAO"].contar_episodios_por_estado.return_value = {}
    assert ctrl.estado_actual().porcentaje_ocupacion is None


# ---- Indicadores de un período

def preparar(datos, total=8, reclasificados=2, promedios=(12.34, 95.0, None)):
    r = datos["ReporteDAO"]
    r.contar_ingresos.return_value = 10
    r.contar_triajes_por_nivel.return_value = {1: 1, 2: 2, 3: 4, 4: 1, 5: 0}
    r.contar_reclasificaciones.return_value = (total, reclasificados)
    r.promedio_espera_triaje_min.return_value, r.promedio_espera_cama_min.return_value, \
        r.promedio_estancia_min.return_value = promedios


def test_indicadores_del_periodo(datos, ctrl):
    preparar(datos)
    ind = ctrl.indicadores(date(2026, 10, 1), date(2026, 10, 31))
    assert (ind.ingresos, ind.total_triajes, ind.porcentaje_reclasificacion) == (10, 8, 25.0)
    assert (ind.espera_triaje_min, ind.espera_cama_min, ind.estancia_min) == (12.3, 95.0, None)
    # el último día se incluye completo: [1 oct 00:00, 1 nov 00:00)
    datos["ReporteDAO"].contar_ingresos.assert_called_once_with(datetime(2026, 10, 1), datetime(2026, 11, 1))
    assert datos.llamadas()[0] == "inicio" and datos.llamadas()[-1] == "commit"


def test_un_solo_dia(datos, ctrl):
    preparar(datos)
    ctrl.indicadores(date(2026, 10, 22), date(2026, 10, 22))
    datos["ReporteDAO"].contar_triajes_por_nivel.assert_called_once_with(datetime(2026, 10, 22), datetime(2026, 10, 23))


def test_sin_triajes_el_porcentaje_es_none(datos, ctrl):
    preparar(datos, total=0, reclasificados=0)
    assert ctrl.indicadores(date(2026, 10, 1), date(2026, 10, 1)).porcentaje_reclasificacion is None


@pytest.mark.parametrize("desde, hasta, mensaje", [
    (date(2026, 10, 31), date(2026, 10, 1), "posterior"),
    (datetime(2026, 10, 1, 8), date(2026, 10, 31), "date"),
    ("2026-10-01", date(2026, 10, 31), "date"),
    (date(2026, 10, 1), None, "date"),
])
def test_periodo_invalido_no_consulta(datos, ctrl, desde, hasta, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        ctrl.indicadores(desde, hasta)
    assert datos.llamadas() == []


# ---- Exportar a PDF

def preparar_estado(datos):
    datos["ReporteDAO"].contar_camas_por_estado.return_value = {C.DISPONIBLE: 3, C.OCUPADA: 1}
    datos["ReporteDAO"].contar_episodios_por_estado.return_value = {E.EN_ESPERA: 2}


def test_exportar_pdf(datos, ctrl, tmp_path):
    preparar(datos)
    preparar_estado(datos)
    ruta = ctrl.exportar_pdf(date(2026, 10, 1), date(2026, 10, 31), tmp_path / "octubre.pdf")
    assert ruta == tmp_path / "octubre.pdf"
    assert ruta.read_bytes().startswith(b"%PDF-")
    # dos lecturas (indicadores y estado actual), cada una en su transacción
    assert datos.llamadas().count("inicio") == 2 and datos.llamadas().count("commit") == 2


def test_exportar_pdf_entrega_los_datos_y_quien_lo_genera(datos, ctrl, monkeypatch, tmp_path):
    preparar(datos)
    preparar_estado(datos)
    recibido = {}
    monkeypatch.setattr(reporte_controller.pdf_generator, "guardar_reporte",
                        lambda ruta, ind, est, en, por: recibido.update(ind=ind, est=est, en=en, por=por) or ruta)
    ctrl.exportar_pdf(date(2026, 10, 1), date(2026, 10, 31), tmp_path / "octubre.pdf")
    assert recibido["ind"].ingresos == 10 and recibido["ind"].desde == date(2026, 10, 1)
    assert recibido["est"].porcentaje_ocupacion == 25.0
    assert recibido["por"] == f"Luis Ramos ({Rol.JEFE_GUARDIA})"
    assert isinstance(recibido["en"], datetime)


@pytest.mark.parametrize("rol", [Rol.MEDICO, Rol.ENFERMERO, Rol.LIMPIEZA])
def test_exportar_pdf_sin_permiso(datos, sesion_de, tmp_path, rol):
    with pytest.raises(UsuarioSinPermisoError):
        ReporteController(sesion_de(rol)).exportar_pdf(date(2026, 10, 1), date(2026, 10, 31),
                                                       tmp_path / "octubre.pdf")
    assert datos.llamadas() == []
    assert list(tmp_path.iterdir()) == []


def test_exportar_pdf_con_ruta_invalida_no_consulta(datos, ctrl, tmp_path):
    with pytest.raises(ValueError, match=".pdf"):
        ctrl.exportar_pdf(date(2026, 10, 1), date(2026, 10, 31), tmp_path / "octubre.txt")
    assert datos.llamadas() == []


def test_exportar_pdf_con_periodo_invalido_no_consulta(datos, ctrl, tmp_path):
    with pytest.raises(ValueError, match="posterior"):
        ctrl.exportar_pdf(date(2026, 10, 31), date(2026, 10, 1), tmp_path / "octubre.pdf")
    assert datos.llamadas() == []
    assert list(tmp_path.iterdir()) == []


def test_exportar_pdf_si_no_se_puede_escribir(datos, ctrl, tmp_path):
    preparar(datos)
    preparar_estado(datos)
    with pytest.raises(ReporteError):
        ctrl.exportar_pdf(date(2026, 10, 1), date(2026, 10, 31), tmp_path / "no_existe" / "octubre.pdf")
