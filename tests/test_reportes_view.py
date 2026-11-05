from datetime import date, datetime
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from controllers.reporte_controller import EstadoGuardia, IndicadoresPeriodo
from models.estados import EstadoCama, EstadoEpisodio
from models.excepciones import ConexionBDError, ReporteError
from prototipo.demo import ReportesDemo
from views import reportes_view, tema
from views.reportes_view import SIN_LECTURA, ReportesView, nombre_archivo

HOY = date(2026, 10, 15)
AHORA = datetime(2026, 10, 15, 10, 42)
NOTA = " · tiempos promedio desde el ingreso (la estancia, hasta el alta)"


@pytest.fixture
def dialogos(monkeypatch):
    anotados = {"error": [], "info": [], "ruta": []}
    monkeypatch.setattr(reportes_view, "mostrar_error", lambda ventana, error: anotados["error"].append(error))
    monkeypatch.setattr(reportes_view, "mostrar_info", lambda ventana, texto: anotados["info"].append(texto))
    return anotados


@pytest.fixture
def crear(raiz_tk, dialogos):
    """La pantalla con el controlador de demostración envuelto en MagicMock(wraps=...): datos reales y llamadas anotadas."""
    def crear(reportes=None, hoy=HOY):
        reportes = reportes or MagicMock(wraps=ReportesDemo())
        avisos = []
        vista = ReportesView(raiz_tk, reportes, al_actualizar=lambda correcto, momento: avisos.append(correcto),
                             hoy=lambda: hoy, reloj=lambda: AHORA)
        vista.reportes, vista.dialogos, vista.avisos = reportes, dialogos, avisos
        return vista
    return crear


def filas(tabla) -> list[tuple]:
    return [tuple(tabla._arbol.item(iid, "values")) for iid in tabla._arbol.get_children()]


def escribir(vista, campo, texto):
    """Escribe en Desde o Hasta como el usuario: reemplaza el texto y suelta una tecla."""
    caja = getattr(vista.periodo, campo)
    caja.delete(0, "end")
    caja.insert(0, texto)
    vista.periodo.fechas_editadas()


def kpis(vista) -> list[tuple[str, str]]:
    return [(tarjeta.valor, tarjeta.nota) for tarjeta in vista.kpis]


def marcado(campo) -> bool:
    return getattr(campo, "_sigtac_error", False)


# ---- Funciones puras

def test_nombre_del_archivo_propuesto():
    assert nombre_archivo(date(2026, 10, 1), date(2026, 10, 31)) == "sigtac_indicadores_2026-10-01_2026-10-31.pdf"


# ---- Al abrir

def test_al_abrir_muestra_el_mes_en_curso(crear):
    vista = crear()
    assert (vista.periodo.desde.get(), vista.periodo.hasta.get()) == ("01/10/2026", "15/10/2026")
    assert vista.periodo.atajos.valor == "mes"
    vista.reportes.indicadores.assert_called_once_with(date(2026, 10, 1), HOY)
    assert vista._periodo_mostrado.cget("text") == "Del 01/10/2026 al 15/10/2026" + NOTA
    # 15 días de la demo: 14 ingresos y 12 triajes por día
    assert kpis(vista) == [("210", "pacientes"), ("6 min", ""), ("8 min", ""), ("5 h 12 min", "")]
    assert filas(vista._tabla_niveles)[0] == ("1 · Rojo", "15", "8 %")
    assert len(filas(vista._tabla_niveles)) == 5
    assert vista._reclasificacion.cget("text") == "Reclasificados: 12 % de 180 triajes"
    assert vista.avisos == [True] and vista.dialogos["error"] == []


def test_los_indicadores_llevan_el_marcador_azul_del_tablero(crear):
    vista = crear()
    def marcos(widget):
        return [hijo for hijo in widget.winfo_children() if isinstance(hijo, ctk.CTkFrame)]

    marcadores = [marcos(marcos(tarjeta)[0])[0] for tarjeta in vista.kpis]  # la fila de arriba, su primer cuadro
    assert all(tuple(m.cget("border_color")) == tema.COLOR_PRIMARIO_GRAFICO for m in marcadores)


def test_ahora_en_la_guardia(crear):
    vista = crear()
    assert filas(vista._tabla_camas) == [("Disponible", "15"), ("Reservada", "2"), ("Ocupada", "12"),
                                         ("En limpieza", "4"), ("Fuera de servicio", "3")]
    assert vista._ocupacion.cget("text") == "Ocupación: 34 %"
    assert vista._pacientes.cget("text") == ("21 pacientes en emergencia\n"
                                             "3 esperan triaje · 4 esperan cama · 14 con cama")


def test_el_dia_1_al_abrir_queda_marcado_este_mes(crear):  # «Hoy» y «Este mes» son el mismo período
    vista = crear(hoy=date(2026, 11, 1))
    assert vista.periodo.atajos.valor == "mes"
    vista.periodo.atajos.botones["hoy"].invoke()
    assert vista.periodo.atajos.valor == "hoy"


def test_si_la_bd_falla_al_abrir_hay_un_solo_aviso(crear):
    reportes = MagicMock()
    reportes.indicadores.side_effect = ConexionBDError("No hay conexión con la base de datos.")
    vista = crear(reportes=reportes)
    assert [str(e) for e in vista.dialogos["error"]] == ["No hay conexión con la base de datos."]
    assert kpis(vista) == [("—", "")] * 4
    assert vista._periodo_mostrado.cget("text") == ""
    assert vista._tabla_niveles.cantidad == 0 and vista._tabla_niveles._vacio.cget("text") == SIN_LECTURA
    assert vista._tabla_camas.cantidad == 0
    assert vista.avisos == [False]  # el encabezado dice «Sin conexión»


# ---- Sin datos y singular (valores límite)

def test_un_periodo_sin_datos_muestra_guiones(crear):
    reportes = MagicMock()
    reportes.indicadores.return_value = IndicadoresPeriodo(HOY, HOY, 0, {}, None, None, None, None)
    reportes.estado_actual.return_value = EstadoGuardia({EstadoCama.FUERA_SERVICIO: 2}, None, {})
    vista = crear(reportes=reportes)
    assert vista._periodo_mostrado.cget("text") == "El 15/10/2026" + NOTA
    assert kpis(vista) == [("0", "pacientes")] + [("—", "sin datos")] * 3
    assert filas(vista._tabla_niveles)[0] == ("1 · Rojo", "0", "—")
    assert vista._reclasificacion.cget("text") == "Reclasificados: sin triajes en el período"
    assert vista._ocupacion.cget("text") == "Ocupación: sin camas en servicio"
    assert vista._pacientes.cget("text") == ("0 pacientes en emergencia\n"
                                             "0 esperan triaje · 0 esperan cama · 0 con cama")


def test_uno_en_singular(crear):
    reportes = MagicMock()
    reportes.indicadores.return_value = IndicadoresPeriodo(HOY, HOY, 1, {3: 1}, 0.0, 5.0, None, None)
    reportes.estado_actual.return_value = EstadoGuardia({}, 0.0, {EstadoEpisodio.EN_ESPERA: 1})
    vista = crear(reportes=reportes)
    assert kpis(vista)[0] == ("1", "paciente")
    assert vista._reclasificacion.cget("text") == "Reclasificados: 0 % de 1 triaje"
    assert vista._pacientes.cget("text").startswith("1 paciente en emergencia\n")


# ---- Elegir el período

def test_un_atajo_rellena_las_fechas_y_consulta(crear):
    vista = crear()
    vista.periodo.atajos.botones["hoy"].invoke()
    assert (vista.periodo.desde.get(), vista.periodo.hasta.get()) == ("15/10/2026", "15/10/2026")
    vista.reportes.indicadores.assert_called_with(HOY, HOY)
    assert kpis(vista)[0] == ("14", "pacientes")


def test_pulsar_el_atajo_marcado_vuelve_a_pedirlo(crear):
    vista = crear()
    vista.periodo.atajos.botones["mes"].invoke()
    assert vista.reportes.indicadores.call_count == 2


def test_al_escribir_el_atajo_sigue_a_las_fechas(crear):
    vista = crear()
    escribir(vista, "desde", "01/09/2026")
    assert vista.periodo.atajos.valor is None  # aún sin consultar: «Este mes» ya no corresponde
    escribir(vista, "desde", "09/10/2026")
    assert vista.periodo.atajos.valor == "semana"
    escribir(vista, "desde", "09/10/20")  # a medio escribir
    assert vista.periodo.atajos.valor is None and not marcado(vista.periodo.desde)


def test_tras_escribir_otro_periodo_el_mes_vuelve_con_su_atajo(crear):
    vista = crear()
    escribir(vista, "desde", "01/09/2026")
    vista.periodo.atajos.botones["mes"].invoke()
    assert vista.periodo.desde.get() == "01/10/2026"
    vista.reportes.indicadores.assert_called_with(date(2026, 10, 1), HOY)
    assert vista.periodo.atajos.valor == "mes"


def test_un_periodo_escrito_se_consulta(crear):
    vista = crear()
    escribir(vista, "desde", "01/09/2026")
    assert vista.ver_indicadores() == "break"
    vista.reportes.indicadores.assert_called_with(date(2026, 9, 1), HOY)
    assert vista._periodo_mostrado.cget("text").startswith("Del 01/09/2026 al 15/10/2026")


def test_enter_en_las_dos_fechas_consulta(crear):
    vista = crear()
    for campo in (vista.periodo.desde, vista.periodo.hasta):
        assert "ver_indicadores" in campo._entry.bind("<Return>")


@pytest.mark.parametrize("campo, texto", [("desde", "1/13/2026"), ("desde", "31/02/2026"), ("hasta", "ayer"),
                                          ("hasta", "")])
def test_una_fecha_mal_escrita_marca_su_campo_y_no_consulta(crear, campo, texto):
    vista = crear()
    escribir(vista, campo, texto)
    vista.ver_indicadores()
    assert marcado(getattr(vista.periodo, campo))
    assert "dd/mm/aaaa" in str(vista.dialogos["error"][0])
    assert vista.reportes.indicadores.call_count == 1  # solo al abrir


def test_la_marca_se_va_al_corregir_no_al_soltar_enter(crear):
    vista = crear()
    escribir(vista, "hasta", "ayer")
    vista.ver_indicadores()
    vista.periodo.fechas_editadas()  # soltar el Enter: el texto no cambió
    assert marcado(vista.periodo.hasta)
    escribir(vista, "hasta", "15/10/2026")
    assert not marcado(vista.periodo.hasta)


def test_un_periodo_rechazado_marca_las_dos_fechas_y_conserva_lo_mostrado(crear):  # valor límite: desde > hasta
    reportes = MagicMock(wraps=ReportesDemo())
    vista = crear(reportes=reportes)
    reportes.indicadores.side_effect = ValueError("La fecha inicial no puede ser posterior a la final.")
    escribir(vista, "desde", "16/10/2026")
    vista.ver_indicadores()
    assert [str(e) for e in vista.dialogos["error"]] == ["La fecha inicial no puede ser posterior a la final."]
    assert marcado(vista.periodo.desde) and marcado(vista.periodo.hasta)
    assert vista._periodo_mostrado.cget("text").startswith("Del 01/10/2026 al 15/10/2026")
    assert vista.avisos == [True]  # no es un problema de conexión
    escribir(vista, "desde", "14/10/2026")  # al corregir una, el período cambió: se van las dos marcas
    assert not marcado(vista.periodo.desde) and not marcado(vista.periodo.hasta)


def test_si_la_bd_falla_despues_conserva_lo_ultimo_y_dice_de_que_periodo_es(crear):
    vista = crear()
    vista.reportes.estado_actual.side_effect = ConexionBDError("No hay conexión con la base de datos.")
    vista.periodo.atajos.botones["hoy"].invoke()
    assert kpis(vista)[0] == ("210", "pacientes")
    assert vista._periodo_mostrado.cget("text").startswith("Del 01/10/2026 al 15/10/2026")  # no el de «Hoy»
    assert vista.avisos == [True, False]
    assert len(vista.dialogos["error"]) == 1


# ---- Exportar

@pytest.fixture
def guardar_como(monkeypatch, dialogos):
    """Reemplaza el diálogo «Guardar como»: devuelve la ruta indicada (None = cancelar) y anota el nombre propuesto."""
    def fijar(ruta):
        def pedir(ventana, nombre):
            dialogos["ruta"].append(nombre)
            return ruta
        monkeypatch.setattr(reportes_view, "pedir_ruta_pdf", pedir)
    return fijar


def test_exportar_guarda_el_pdf_del_periodo_mostrado(crear, guardar_como, tmp_path):
    vista = crear()
    escribir(vista, "desde", "01/09/2026")
    destino = tmp_path / "septiembre.pdf"
    guardar_como(destino)
    vista.exportar()
    assert vista.dialogos["ruta"] == ["sigtac_indicadores_2026-09-01_2026-10-15.pdf"]
    vista.reportes.exportar_pdf.assert_called_once_with(date(2026, 9, 1), HOY, destino)
    assert destino.read_bytes().startswith(b"%PDF")
    assert vista.dialogos["info"] == [f"Reporte guardado en {destino}."]
    # la pantalla dice lo mismo que el PDF
    assert vista._periodo_mostrado.cget("text").startswith("Del 01/09/2026 al 15/10/2026")


def test_cancelar_el_dialogo_no_exporta(crear, guardar_como):
    vista = crear()
    guardar_como(None)
    vista.exportar()
    vista.reportes.exportar_pdf.assert_not_called()
    assert vista.dialogos["info"] == [] and vista.dialogos["error"] == []


def test_con_una_fecha_mal_escrita_no_se_abre_el_dialogo(crear, guardar_como, tmp_path):
    vista = crear()
    guardar_como(tmp_path / "x.pdf")
    escribir(vista, "desde", "ayer")
    vista.exportar()
    assert vista.dialogos["ruta"] == []
    vista.reportes.exportar_pdf.assert_not_called()


def test_una_ruta_sin_pdf_se_rechaza(crear, guardar_como, tmp_path):
    vista = crear()
    guardar_como(tmp_path / "reporte.txt")
    vista.exportar()
    assert "pdf" in str(vista.dialogos["error"][0])
    assert not (tmp_path / "reporte.txt").exists() and vista.dialogos["info"] == []


def test_si_no_se_puede_guardar_se_avisa_sin_decir_sin_conexion(crear, guardar_como, tmp_path):
    vista = crear()
    guardar_como(tmp_path / "abierto.pdf")
    vista.reportes.exportar_pdf.side_effect = ReporteError("Cierre el PDF si está abierto en otro programa.")
    vista.exportar()
    assert [str(e) for e in vista.dialogos["error"]] == ["Cierre el PDF si está abierto en otro programa."]
    assert vista.dialogos["info"] == [] and False not in vista.avisos


def test_si_la_bd_falla_al_exportar_el_encabezado_lo_dice(crear, guardar_como, tmp_path):
    vista = crear()
    guardar_como(tmp_path / "x.pdf")
    vista.reportes.exportar_pdf.side_effect = ConexionBDError("No hay conexión con la base de datos.")
    vista.exportar()
    assert vista.avisos[-1] is False and len(vista.dialogos["error"]) == 1
