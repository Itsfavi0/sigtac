from datetime import datetime
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from controllers.auth_controller import AuthController, Sesion
from controllers.cama_controller import CamaController
from controllers.reporte_controller import ReporteController
from controllers.triaje_controller import TriajeController
from models.permisos import Permiso, Rol, tiene_permiso
from views import app_principal, formato, tema
from views.app_principal import (MODULOS, PANTALLAS, SIN_CONEXION, TEXTO_PENDIENTE, TEXTO_SIN_MODULOS, AppPrincipal,
                                 crear_tablero, iniciales)
from views.dashboard_view import DashboardView


def crear(raiz, sesion, pantallas=None):
    auth = MagicMock(spec=AuthController)
    al_cerrar = MagicMock()
    vista = AppPrincipal(raiz, auth, sesion, al_cerrar, pantallas={} if pantallas is None else pantallas)
    return vista, auth, al_cerrar


def textos_de(widget) -> list[str]:
    textos = []
    for hijo in widget.winfo_children():
        if isinstance(hijo, (ctk.CTkLabel, ctk.CTkButton)):
            textos.append(hijo.cget("text"))
        textos.extend(textos_de(hijo))
    return textos


# ---- Menú según el rol

@pytest.mark.parametrize("rol, esperados", [
    (Rol.ENFERMERO, ["tablero", "triaje", "pacientes"]),
    (Rol.MEDICO, ["tablero", "triaje", "pacientes"]),
    (Rol.JEFE_GUARDIA, ["tablero", "triaje", "pacientes"]),
    (Rol.LIMPIEZA, ["tablero"]),
    (Rol.ADMINISTRADOR, ["tablero"]),
])
def test_el_menu_muestra_solo_los_modulos_del_rol(raiz_tk, sesion_de, rol, esperados):
    vista, _, _ = crear(raiz_tk, sesion_de(rol))
    assert vista.modulos_visibles == esperados
    assert set(vista._items) == set(esperados)


def test_el_menu_sigue_la_matriz_de_permisos(raiz_tk, sesion_de):
    # La vista no decide quién ve qué: pregunta a la sesión, que usa models/permisos.py
    for rol in Rol:
        vista, _, _ = crear(raiz_tk, sesion_de(rol))
        assert vista.modulos_visibles == [m.clave for m in MODULOS if tiene_permiso(rol, m.permiso)]
        vista.destroy()


def test_un_rol_sin_modulos_ve_un_aviso(raiz_tk):
    vista, _, _ = crear(raiz_tk, Sesion(1, 2, "Rol inexistente", "Ana", "Pérez"))
    assert vista.modulos_visibles == [] and vista.modulo_actual is None
    assert TEXTO_SIN_MODULOS in textos_de(vista)


def test_no_se_ofrecen_modulos_sin_pantalla_en_este_alcance():
    assert [m.permiso for m in MODULOS] == [Permiso.VER_CAMAS, Permiso.TRIAJE, Permiso.PACIENTES]


# ---- Cambio de módulo

def test_empieza_en_el_tablero_con_su_encabezado(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.ENFERMERO))
    assert vista.modulo_actual == "tablero"
    assert vista._titulo.cget("text") == "Tablero de camas"
    assert vista._descripcion.cget("text") == MODULOS[0].descripcion


def test_el_item_activo_se_distingue(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.ENFERMERO))
    vista.mostrar("triaje")
    activo, indicador = vista._items["triaje"]
    inactivo, indicador_inactivo = vista._items["tablero"]
    assert tuple(activo.cget("fg_color")) == tema.COLOR_ACTIVO and activo.cget("border_width") == 1
    assert tuple(indicador.cget("fg_color")) == tema.COLOR_PRIMARIO
    assert inactivo.cget("fg_color") == "transparent" and inactivo.cget("border_width") == 0
    assert indicador_inactivo.cget("fg_color") == "transparent"


def test_un_clic_en_el_menu_cambia_de_modulo(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    vista._items["pacientes"][0].invoke()
    assert vista.modulo_actual == "pacientes" and vista._titulo.cget("text") == "Pacientes"


def test_un_modulo_sin_pantalla_muestra_el_aviso(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.ENFERMERO))
    assert vista._pantalla.cget("text") == TEXTO_PENDIENTE


def test_la_pantalla_registrada_se_crea_con_la_sesion_y_reemplaza_a_la_anterior(raiz_tk, sesion_de):
    creadas = []

    def crear_pantalla(padre, sesion, principal):
        marco = ctk.CTkFrame(padre)
        creadas.append((marco, sesion, principal))
        return marco

    sesion = sesion_de(Rol.ENFERMERO)
    vista, _, _ = crear(raiz_tk, sesion, pantallas={"tablero": crear_pantalla, "triaje": crear_pantalla})
    primera = vista._pantalla
    vista.mostrar("triaje")
    assert [(s, p) for _, s, p in creadas] == [(sesion, vista), (sesion, vista)]
    assert not primera.winfo_exists()  # la pantalla anterior se destruye
    assert vista._pantalla is creadas[1][0]


def test_no_se_puede_abrir_un_modulo_que_el_rol_no_tiene(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.LIMPIEZA))
    with pytest.raises(ValueError, match="no disponible"):
        vista.mostrar("triaje")
    assert vista.modulo_actual == "tablero"


# ---- Encabezado

def test_el_encabezado_muestra_la_fecha_y_el_reloj(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    assert vista._fecha.cget("text") == formato.fecha_corta(datetime.now().date())
    assert len(vista._reloj.cget("text")) == len("10:42:18")


def test_marcar_actualizado_y_se_borra_al_cambiar_de_modulo(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    vista.marcar_actualizado(datetime(2026, 10, 27, 10, 42, 18))
    assert vista._actualizado.cget("text") == "● Actualizado 10:42"  # con el punto verde del diseño
    vista.mostrar("triaje")
    assert vista._actualizado.cget("text") == ""  # la hora era de la pantalla anterior


def test_informar_actualizacion_correcta_y_sin_conexion(raiz_tk, sesion_de):
    # Es el al_actualizar del tablero: un fallo se ve en el encabezado, en rojo, sin abrir un diálogo
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    vista.informar_actualizacion(False, datetime(2026, 10, 27, 10, 42))
    assert vista._actualizado.cget("text") == f"● {SIN_CONEXION}"
    assert tuple(vista._actualizado.cget("text_color")) == tema.COLOR_ERROR
    vista.informar_actualizacion(True, datetime(2026, 10, 27, 10, 43))
    assert vista._actualizado.cget("text") == "● Actualizado 10:43"
    assert tuple(vista._actualizado.cget("text_color")) == tema.COLOR_EXITO


# ---- Pantallas registradas

def test_las_pantallas_hechas_estan_registradas():
    assert PANTALLAS == {"tablero": crear_tablero, "triaje": app_principal.crear_triaje,
                         "pacientes": app_principal.crear_pacientes}


def test_crear_tablero_usa_los_controladores_de_la_sesion(raiz_tk, sesion_de, monkeypatch):
    recibidos = {}

    class TableroFalso(ctk.CTkFrame):
        def __init__(self, padre, camas, sesion, reportes, triaje, al_actualizar):
            super().__init__(padre)
            recibidos.update(camas=camas, sesion=sesion, reportes=reportes, triaje=triaje, aviso=al_actualizar)

    monkeypatch.setattr(app_principal, "DashboardView", TableroFalso)
    sesion = sesion_de(Rol.JEFE_GUARDIA)
    vista, _, _ = crear(raiz_tk, sesion, pantallas={"tablero": crear_tablero})
    assert isinstance(vista._pantalla, TableroFalso)
    assert isinstance(recibidos["camas"], CamaController) and isinstance(recibidos["reportes"], ReporteController)
    assert isinstance(recibidos["triaje"], TriajeController) and recibidos["sesion"] is sesion
    assert recibidos["aviso"] == vista.informar_actualizacion


def test_crear_tablero_acepta_otros_controladores(raiz_tk, sesion_de):
    # Así el prototipo abre el tablero con los controladores de demostración, sin MySQL
    from prototipo.demo import CamasDemo, ReportesDemo, TriajeDemo
    sesion = sesion_de(Rol.JEFE_GUARDIA)
    vista, _, _ = crear(raiz_tk, sesion)
    tablero = crear_tablero(vista._contenido, sesion, vista, camas=CamasDemo(), reportes=ReportesDemo(),
                            triaje=TriajeDemo())
    assert isinstance(tablero, DashboardView)
    assert vista._actualizado.cget("text").startswith("● Actualizado")
    tablero.destroy()


def test_al_destruirse_se_detiene_el_reloj(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    tarea = vista._tarea_reloj
    vista.destroy()
    assert tarea not in raiz_tk.tk.call("after", "info")


# ---- Pie de la barra

def test_muestra_el_usuario_y_su_rol(raiz_tk):
    vista, _, _ = crear(raiz_tk, Sesion(1, 2, Rol.JEFE_GUARDIA, "Elena María", "Ríos Vega"))
    textos = textos_de(vista)
    assert "ER" in textos and "Elena Ríos" in textos and Rol.JEFE_GUARDIA.value in textos


def test_iniciales(sesion_de):
    assert iniciales(sesion_de(Rol.MEDICO)) == "LR"  # Luis Ramos


def test_cerrar_sesion(raiz_tk, sesion_de):
    vista, auth, al_cerrar = crear(raiz_tk, sesion_de(Rol.MEDICO))
    boton = next(w for w in vista.winfo_children()[0].winfo_children()
                 if isinstance(w, ctk.CTkButton) and w.cget("text") == "Cerrar sesión")
    boton.invoke()
    auth.cerrar_sesion.assert_called_once_with()
    al_cerrar.assert_called_once_with()


def test_el_interruptor_cambia_el_modo(raiz_tk, sesion_de, monkeypatch):
    modos = []
    monkeypatch.setattr(app_principal.ctk, "set_appearance_mode", modos.append)
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    oscuro = bool(vista._interruptor_modo.get())
    assert oscuro == tema.modo_oscuro()  # el interruptor arranca en el modo activo
    vista._interruptor_modo.toggle()
    vista._interruptor_modo.toggle()
    assert modos == (["light", "dark"] if oscuro else ["dark", "light"])


@pytest.mark.parametrize("modo, i", [("dark", 1), ("light", 0)])
def test_las_lineas_divisorias_toman_el_tono_del_modo(raiz_tk, sesion_de, modo, i):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    vista._set_appearance_mode(modo)
    assert len(vista._divisores) == 2  # entre la barra y el contenido, y sobre el usuario
    assert all(linea.cget("background") == tema.COLOR_DIVISOR[i] for linea in vista._divisores)


# ---- Teclado

def test_tab_recorre_la_barra_en_el_orden_de_lectura(raiz_tk, sesion_de):
    # Tk tabula en el orden de creación: el menú va antes que el pie aunque el pie se coloque primero
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    barra = vista.winfo_children()[0]
    controles = [w for w in barra.winfo_children() if isinstance(w, (ctk.CTkFrame, ctk.CTkSwitch, ctk.CTkButton))]
    menu = [vista._items[c][0].master for c in vista.modulos_visibles]
    salir = next(w for w in controles if isinstance(w, ctk.CTkButton) and w.cget("text") == "Cerrar sesión")
    orden = [controles.index(w) for w in (*menu, vista._interruptor_modo, salir)]
    assert orden == sorted(orden)


def test_el_menu_y_el_interruptor_aceptan_el_foco(raiz_tk, sesion_de):
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    for control in (*(boton for boton, _ in vista._items.values()), vista._interruptor_modo):
        assert str(control._canvas.cget("takefocus")) == "1"


def test_enter_en_un_item_del_menu_cambia_de_modulo(raiz_tk, sesion_de):
    from views.componentes.foco import activar, al_entrar_control, al_salir_control
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    boton = vista._items["triaje"][0]
    al_entrar_control(boton)
    activar(boton)  # lo que hace Enter (Tk no entrega teclas a una ventana oculta)
    assert vista.modulo_actual == "triaje"
    assert boton.cget("border_width") == 2  # el borde de foco se mantiene aunque el ítem pase a activo
    al_salir_control(boton)
    assert boton.cget("border_width") == 1  # al salir, el borde del ítem activo


def test_el_interruptor_se_mueve_con_el_teclado(raiz_tk, sesion_de, monkeypatch):
    from views.componentes.foco import activar
    modos = []
    monkeypatch.setattr(app_principal.ctk, "set_appearance_mode", modos.append)
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    activar(vista._interruptor_modo)
    assert len(modos) == 1



def test_el_circulo_del_interruptor_se_distingue_de_la_barra(raiz_tk, sesion_de, monkeypatch):
    # Apagado, blanco se perdería contra la barra blanca: es gris oscuro; encendido, blanco sobre el azul
    monkeypatch.setattr(app_principal.ctk, "set_appearance_mode", lambda modo: None)
    vista, _, _ = crear(raiz_tk, sesion_de(Rol.MEDICO))
    interruptor = vista._interruptor_modo
    if interruptor.get():
        interruptor.toggle()
    assert tuple(interruptor.cget("button_color")) == tema.COLOR_TEXTO_SECUNDARIO
    interruptor.toggle()
    assert tuple(interruptor.cget("button_color")) == tema.COLOR_TEXTO_SOBRE_PRIMARIO
