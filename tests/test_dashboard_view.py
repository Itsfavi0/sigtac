from datetime import datetime
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from models.excepciones import PersistenciaError
from models.permisos import Rol
from prototipo.demo import CamasDemo, ReportesDemo, TriajeDemo
from views import dashboard_view, tema
from views.dashboard_view import NADIE_ESPERA, DashboardView

AHORA = datetime(2026, 10, 27, 10, 42)


def textos(widget) -> list[str]:
    """Todos los textos de las etiquetas dentro de un widget, en orden."""
    resultado = []
    for hijo in widget.winfo_children():
        if isinstance(hijo, ctk.CTkLabel):
            resultado.append(hijo.cget("text"))
        resultado.extend(textos(hijo))
    return resultado


@pytest.fixture
def errores(monkeypatch):
    llamadas = []
    monkeypatch.setattr(dashboard_view, "mostrar_error", lambda ventana, error: llamadas.append(error))
    return llamadas


@pytest.fixture
def crear(raiz_tk, sesion_de, errores):
    avisos = []

    def crear(rol=Rol.JEFE_GUARDIA, camas=None):
        vista = DashboardView(raiz_tk, camas or CamasDemo(lambda: AHORA), sesion_de(rol), ReportesDemo(),
                              TriajeDemo(lambda: AHORA), al_actualizar=lambda ok, momento: avisos.append(ok),
                              reloj=lambda: AHORA)
        vista.avisos = avisos
        return vista
    return crear


def test_indicadores_del_jefe_de_guardia(crear):
    vista = crear()
    assert [(k.valor, k.nota) for k in vista.kpis] == [
        ("15 / 34", "44 % disponible"),  # 34 en servicio: las 2 fuera de servicio no cuentan
        ("4", "por confirmar"), ("2", "requieren cama ya"), ("8 min", "hoy")]
    assert vista.avisos == [True]


@pytest.mark.parametrize("rol, titulo, valor", [
    (Rol.ADMINISTRADOR, "Espera de cama", "8 min"),
    (Rol.ENFERMERO, "Esperan triaje", "2"),
    (Rol.LIMPIEZA, "Fuera de servicio", "2"),
])
def test_el_cuarto_indicador_depende_del_rol(crear, rol, titulo, valor):
    vista = crear(rol)
    assert titulo in textos(vista.kpis[3]) and vista.kpis[3].valor == valor


def test_la_matriz_recibe_todas_las_camas(crear):
    assert crear().matriz.cantidad_camas == 36


def test_la_cola_muestra_tres_y_resume_el_resto(crear):
    vista = crear()
    visibles = textos(vista._filas)
    assert ["1", "M. Salazar", "DNI 43•••19", "Dolor torácico agudo", "02 min", "Inmediato"] == visibles[:6]
    assert "A. Torres" in visibles and "1 paciente más en espera" in visibles
    assert not any(t.startswith("NN") for t in visibles)  # el cuarto queda en el resumen


def test_la_espera_que_excede_el_plazo_se_marca(crear):
    vista = crear()
    etiquetas = [h for h in vista._filas.winfo_children() if isinstance(h, ctk.CTkFrame)]
    filas = [f for f in etiquetas if any(isinstance(n, ctk.CTkLabel) and "min" in n.cget("text")
                                         for n in f.winfo_children())]
    espera = {f.winfo_children()[3].cget("text"): tuple(f.winfo_children()[3].cget("text_color")) for f in filas}
    assert espera["02 min"] == tema.COLOR_ERROR            # nivel 1: inmediato, ya excede
    assert espera["07 min"] == tema.COLOR_TEXTO_SECUNDARIO  # nivel 2: plazo 10 min


def test_con_poca_altura_la_cola_muestra_dos(crear):
    vista = crear()
    evento = MagicMock(height=round(600 * tema.escala(vista)))
    vista._ajustar_cola(evento)
    assert "2 pacientes más en espera" in textos(vista._filas)


@pytest.mark.parametrize("rol", [Rol.LIMPIEZA, Rol.ADMINISTRADOR])
def test_limpieza_y_administracion_no_ven_la_cola(crear, rol):
    vista = crear(rol)
    assert vista.muestra_cola is False
    assert "Esperan cama" not in textos(vista)


def test_cola_vacia(crear):
    camas = CamasDemo(lambda: AHORA)
    camas.cola_de_espera = lambda: []
    vista = crear(camas=camas)
    assert NADIE_ESPERA in textos(vista._filas)
    assert vista.kpis[2].valor == "0" and vista.kpis[2].nota == "ninguno"


def test_si_falla_al_abrir_avisa_con_un_dialogo(crear, errores):
    camas = MagicMock()
    camas.mapa_camas.side_effect = PersistenciaError("No se pudo conectar a la base de datos.")
    vista = crear(camas=camas)
    assert len(errores) == 1 and vista.avisos == [False]


def test_si_falla_una_actualizacion_conserva_lo_anterior_sin_dialogo(crear, errores):
    vista = crear()
    vista._camas = MagicMock(**{"mapa_camas.side_effect": PersistenciaError("Sin conexión.")})
    vista.refrescar()  # actualización automática
    assert errores == [] and vista.avisos == [True, False]
    assert vista.kpis[0].valor == "15 / 34" and vista.matriz.cantidad_camas == 36


def test_programa_la_siguiente_actualizacion_y_la_cancela_al_cerrar(crear):
    vista = crear()
    assert vista._tarea is not None
    vista.destroy()
    assert vista._tarea is None
