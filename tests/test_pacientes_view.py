from datetime import date, datetime
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from models.documento import TipoDocumento
from models.excepciones import ConexionBDError, PersistenciaError, ReglaNegocioError
from prototipo.demo import PacientesDemo, TriajeDemo
from views import pacientes_view, tema
from views.pacientes_view import (AVISO_BUSCAR, AVISO_IDENTIFICAR, DADO_DE_BAJA, NADIE_SIN_IDENTIFICAR,
                                  NO_ENCONTRADO, TEXTO_ELEGIR_NN, TITULOS, PacientesView)

AHORA = datetime(2026, 10, 30, 10, 0)


@pytest.fixture
def dialogos(monkeypatch):
    """Los diálogos de la pantalla, anotados en lugar de abrirse. `confirmar` responde lo que diga la prueba."""
    anotados = {"error": [], "info": [], "pregunta": [], "respuesta": True}
    monkeypatch.setattr(pacientes_view, "mostrar_error", lambda ventana, error: anotados["error"].append(error))
    monkeypatch.setattr(pacientes_view, "mostrar_info", lambda ventana, texto: anotados["info"].append(texto))

    def confirmar(ventana, pregunta):
        anotados["pregunta"].append(pregunta)
        return anotados["respuesta"]

    monkeypatch.setattr(pacientes_view, "confirmar", confirmar)
    return anotados


@pytest.fixture
def crear(raiz_tk, dialogos):
    """La pantalla con el controlador de demostración envuelto en MagicMock(wraps=...): reglas reales y llamadas anotadas."""
    def crear(pacientes=None, al_registrar_en_triaje=None):
        triaje = TriajeDemo(lambda: AHORA)
        pacientes = pacientes or MagicMock(wraps=PacientesDemo(triaje, lambda: AHORA))
        vista = PacientesView(raiz_tk, pacientes, al_registrar_en_triaje)
        vista.pacientes, vista.triaje, vista.dialogos = pacientes, triaje, dialogos
        return vista
    return crear


def escribir(campo, texto):
    campo.delete(0, "end")
    campo.insert(0, texto)


def buscar(vista, numero="41234567"):
    escribir(vista._documento.campo_numero, numero)
    vista.buscar()


def visible(widget) -> bool:
    return widget.winfo_manager() != ""


# ---- Al abrir

def test_al_abrir_muestra_buscar_y_cuenta_los_nn(crear):
    vista = crear()
    assert (vista._tarjeta.titulo, vista._tarjeta.subtitulo) == TITULOS["buscar"]
    assert vista._modo.texto("nn") == "Sin identificar (2)"
    assert vista._aviso.cget("text") == AVISO_BUSCAR and visible(vista._aviso)
    assert not visible(vista._encontrado) and not visible(vista._no_encontrado)


def test_si_la_bd_falla_al_abrir_hay_un_solo_aviso(crear):
    pacientes = MagicMock()
    pacientes.listar_no_identificados.side_effect = PersistenciaError("No se pudo leer la lista.")
    vista = crear(pacientes=pacientes)
    assert [str(e) for e in vista.dialogos["error"]] == ["No se pudo leer la lista."]
    assert vista._modo.texto("nn") == "Sin identificar (0)"


def test_destruir_cancela_el_foco_pendiente(crear):
    vista = crear()
    tarea = vista._tarea_foco
    vista.destroy()
    assert tarea not in vista.tk.call("after", "info")


# ---- Buscar

def test_buscar_muestra_la_ficha_ampliada(crear):
    vista = crear()
    buscar(vista)
    assert visible(vista._encontrado) and not visible(vista._aviso)
    assert vista._ficha.nombre == "Carmen Rojas Llanos"
    assert vista._ficha.documento.startswith("DNI 41234567 · nació el")
    assert vista._boton_editar.cget("state") == "normal" and not visible(vista._aviso_baja)


def test_sin_resultado_lo_dice_y_ofrece_registrarlo_en_triaje(crear):
    pedidos = []
    vista = crear(al_registrar_en_triaje=lambda tipo, numero: pedidos.append((tipo, numero)))
    buscar(vista, "48123456")
    assert visible(vista._no_encontrado)
    textos = [h.cget("text") for h in vista._no_encontrado.winfo_children()]
    assert NO_ENCONTRADO in textos and "Registrarlo en Triaje" in textos
    next(h for h in vista._no_encontrado.winfo_children() if isinstance(h, ctk.CTkButton)).invoke()
    assert pedidos == [(TipoDocumento.DNI, "48123456")]  # Triaje recibe el documento ya buscado


def test_sin_triaje_en_el_menu_no_se_ofrece_registrarlo(crear):
    vista = crear(al_registrar_en_triaje=None)
    buscar(vista, "48123456")
    assert not any(isinstance(h, ctk.CTkButton) for h in vista._no_encontrado.winfo_children())


def test_un_documento_invalido_se_marca_y_se_explica_sin_dialogo(crear):
    vista = crear()
    buscar(vista, "123")
    numero = vista._documento.campo_numero
    assert numero._sigtac_error and tuple(vista._aviso.cget("text_color")) == tema.COLOR_ERROR
    assert vista.dialogos["error"] == []
    vista._documento_editado(vista._documento, vista._aviso)  # soltar el Enter: el texto no cambió
    assert numero._sigtac_error
    escribir(numero, "1234")
    vista._documento_editado(vista._documento, vista._aviso)
    assert not numero._sigtac_error and vista._aviso.cget("text") == AVISO_BUSCAR


def test_sin_conexion_al_buscar_no_culpa_al_documento(crear):
    pacientes = MagicMock()
    pacientes.listar_seguros.return_value = []
    pacientes.listar_no_identificados.return_value = []
    pacientes.buscar_por_documento.side_effect = ConexionBDError("No hay conexión con la base de datos.")
    vista = crear(pacientes=pacientes)
    buscar(vista)
    assert [str(e) for e in vista.dialogos["error"]] == ["No hay conexión con la base de datos."]
    assert not getattr(vista._documento.campo_numero, "_sigtac_error", False)


def test_un_paciente_dado_de_baja_no_se_edita_ni_se_admite(crear):
    vista = crear()
    paciente = vista.pacientes.buscar_por_documento("DNI", "41234567")
    paciente.anular()
    buscar(vista)
    assert vista._boton_editar.cget("state") == "disabled" and vista._boton_admitir.cget("state") == "disabled"
    assert visible(vista._aviso_baja) and vista._aviso_baja.cget("text") == DADO_DE_BAJA


# ---- Editar datos

def test_editar_muestra_los_datos_y_oculta_las_otras_acciones(crear):
    vista = crear()
    buscar(vista)
    vista.abrir_edicion()
    assert visible(vista._edicion) and not visible(vista._acciones_ficha)
    assert vista._datos.nombres.get() == "Carmen" and vista._datos.fecha_nac.get() == "14/03/1985"
    assert vista._datos.sexo.get() == "Mujer" and vista._datos.seguro.get() == "SIS (Seguro Integral de Salud)"


def test_guardar_actualiza_y_refresca_la_ficha(crear):
    vista = crear()
    buscar(vista)
    vista.abrir_edicion()
    escribir(vista._datos.nombres, "Carmen Rosa")
    vista._datos.seguro.set("EsSalud")
    vista.guardar()
    vista.pacientes.actualizar_datos.assert_called_once_with(
        200, nombres="Carmen Rosa", apellidos="Rojas Llanos", fecha_nac=date(1985, 3, 14), sexo="F", id_seguro=1)
    assert vista._ficha.nombre == "Carmen Rosa Rojas Llanos" and vista._ficha.datos.endswith("EsSalud")
    assert not visible(vista._edicion) and visible(vista._acciones_ficha)
    assert vista.dialogos["info"] == ["Datos del paciente guardados."]


def test_una_fecha_mal_escrita_marca_su_campo_y_no_guarda(crear):
    vista = crear()
    buscar(vista)
    vista.abrir_edicion()
    escribir(vista._datos.fecha_nac, "1985-03-14")
    vista.guardar()
    assert vista._datos.fecha_nac._sigtac_error and len(vista.dialogos["error"]) == 1
    vista.pacientes.actualizar_datos.assert_not_called()
    assert visible(vista._edicion)  # el formulario conserva lo escrito


def test_cancelar_cierra_sin_guardar(crear):
    vista = crear()
    buscar(vista)
    vista.abrir_edicion()
    escribir(vista._datos.nombres, "Otra")
    vista.cerrar_formularios()
    assert not visible(vista._edicion) and vista._ficha.nombre == "Carmen Rojas Llanos"
    vista.pacientes.actualizar_datos.assert_not_called()


# ---- Abrir episodio

def test_abrir_episodio_lo_deja_esperando_triaje(crear):
    vista = crear()
    buscar(vista)
    vista.abrir_admision()
    assert visible(vista._admision) and not visible(vista._acciones_ficha)
    escribir(vista._motivo, "Dolor abdominal")
    vista.abrir_episodio()
    vista.pacientes.abrir_episodio.assert_called_once_with(200, "Dolor abdominal")
    assert vista.triaje.en_cola(200)
    assert vista.dialogos["info"] == ["Episodio abierto: Carmen Rojas Llanos espera triaje."]
    assert not visible(vista._admision)


def test_sin_motivo_se_marca_y_se_explica_bajo_el_campo(crear):
    vista = crear()
    buscar(vista)
    vista.abrir_admision()
    vista.abrir_episodio()
    assert vista._motivo._sigtac_error and vista.dialogos["error"] == []
    assert visible(vista._aviso_motivo) and vista._aviso_motivo.cget("text") == "El motivo de consulta es obligatorio."
    escribir(vista._motivo, "Dolor")
    vista._motivo_corregido()  # lo que hace soltar una tecla en el campo
    assert not vista._motivo._sigtac_error and not visible(vista._aviso_motivo)


def test_al_cancelar_o_terminar_el_foco_vuelve_al_documento(crear, monkeypatch):
    vista = crear()
    enfocados = []
    monkeypatch.setattr(vista._documento, "enfocar", lambda: enfocados.append(True))
    buscar(vista)
    vista.abrir_edicion()
    vista.cancelar()
    vista.abrir_admision()
    escribir(vista._motivo, "Dolor")
    vista.abrir_episodio()
    assert enfocados == [True, True]  # nunca queda en un campo oculto


def test_cambiar_el_documento_buscado_retira_la_ficha(crear):
    vista = crear()
    buscar(vista)
    vista.abrir_edicion()
    escribir(vista._documento.campo_numero, "4123456")
    vista._documento_editado(vista._documento, vista._aviso)
    assert not visible(vista._encontrado) and not visible(vista._edicion) and visible(vista._aviso)
    assert vista._paciente is None


def test_registrarlo_en_triaje_lleva_el_documento_buscado_no_el_escrito_despues(crear):
    pedidos = []
    vista = crear(al_registrar_en_triaje=lambda tipo, numero: pedidos.append(numero))
    buscar(vista, "48123456")
    vista._documento.campo_numero.insert("end", "9")  # sin soltar la tecla todavía: el aviso no cambió
    vista._ir_a_triaje()
    assert pedidos == ["48123456"]


def test_un_segundo_episodio_abierto_se_rechaza(crear):
    vista = crear()
    buscar(vista)
    vista.abrir_admision()
    escribir(vista._motivo, "Dolor")
    vista.abrir_episodio()
    vista.abrir_admision()
    escribir(vista._motivo, "Otra vez")
    vista.abrir_episodio()
    assert [str(e) for e in vista.dialogos["error"]] == ["El paciente ya tiene un episodio abierto."]


# ---- Sin identificar

def test_la_lista_de_nn_y_el_boton_que_dice_que_falta(crear):
    vista = crear()
    vista._modo.elegir("nn")
    assert (vista._tarjeta.titulo, vista._tarjeta.subtitulo) == TITULOS["nn"]
    assert visible(vista._nn) and not visible(vista._buscar) and vista._tabla.cantidad == 2
    assert vista._aviso_nn.cget("text") == AVISO_IDENTIFICAR
    assert (vista._boton_identificar.cget("text"), vista._boton_identificar.cget("state")) == (TEXTO_ELEGIR_NN,
                                                                                           "disabled")
    vista._tabla.seleccionar(250)
    vista._nn_elegido(250)
    assert (vista._boton_identificar.cget("text"), vista._boton_identificar.cget("state")) == ("Identificar",
                                                                                           "normal")


def test_sin_nn_lo_dice(crear):
    pacientes = MagicMock()
    pacientes.listar_seguros.return_value = []
    pacientes.listar_no_identificados.return_value = []
    vista = crear(pacientes=pacientes)
    assert vista._tabla._vacio.cget("text") == NADIE_SIN_IDENTIFICAR


def _elegir_nn(vista, id_nn=250, numero="48123456"):
    vista._modo.elegir("nn")
    vista._tabla.seleccionar(id_nn)
    escribir(vista._documento_nn.campo_numero, numero)
    escribir(vista._datos_nn.nombres, "Lucía")
    escribir(vista._datos_nn.apellidos, "Paredes Soto")
    escribir(vista._datos_nn.fecha_nac, "02/05/2000")


def test_identificar_un_nn(crear):
    vista = crear()
    _elegir_nn(vista)
    vista.identificar()
    vista.pacientes.identificar.assert_called_once_with(250, "DNI", "48123456", nombres="Lucía",
                                                         apellidos="Paredes Soto", fecha_nac=date(2000, 5, 2))
    assert vista.dialogos["info"] == ["Paciente identificado: Lucía Paredes Soto."]
    assert vista._tabla.cantidad == 1 and vista._modo.texto("nn") == "Sin identificar (1)"
    assert vista._documento_nn.valores()[1] == "" and vista._datos_nn.nombres.get() == ""


def test_si_el_documento_ya_existe_pregunta_y_fusiona(crear):
    vista = crear()
    vista.pacientes.abrir_episodio(250, "Hallado inconsciente")  # el NN tiene un episodio
    _elegir_nn(vista, numero="41234567")  # Carmen Rojas, ya registrada
    vista.identificar()
    assert len(vista.dialogos["pregunta"]) == 1 and "Carmen Rojas Llanos" in vista.dialogos["pregunta"][0]
    assert "No se puede deshacer" in vista.dialogos["pregunta"][0]
    assert "Los datos escritos no se usan" in vista.dialogos["pregunta"][0]
    vista.pacientes.identificar.assert_not_called()
    vista.pacientes.fusionar.assert_called_once_with(250, 200)
    assert vista.dialogos["info"] == ["Registros fusionados: 1 episodio pasó a Carmen Rojas Llanos."]
    assert vista._tabla.cantidad == 1 and vista.triaje.en_cola(200)


def test_si_no_se_confirma_la_fusion_no_se_hace_nada(crear):
    vista = crear()
    vista.dialogos["respuesta"] = False
    _elegir_nn(vista, numero="41234567")
    vista.identificar()
    vista.pacientes.fusionar.assert_not_called()
    assert vista.dialogos["info"] == [] and vista._tabla.cantidad == 2
    assert vista._documento_nn.valores()[1] == "41234567"  # se conserva lo escrito


def test_al_identificar_un_documento_invalido_se_marca(crear):
    vista = crear()
    _elegir_nn(vista, numero="123")
    vista.identificar()
    assert vista._documento_nn.campo_numero._sigtac_error
    assert tuple(vista._aviso_nn.cget("text_color")) == tema.COLOR_ERROR and vista.dialogos["error"] == []
    vista.pacientes.identificar.assert_not_called()


def test_al_identificar_una_fecha_mal_escrita_se_marca_y_el_nn_sigue_elegido(crear):
    vista = crear()
    _elegir_nn(vista)
    vista._nn_elegido(250)
    escribir(vista._datos_nn.fecha_nac, "31/02/1990")
    vista.identificar()
    assert vista._datos_nn.fecha_nac._sigtac_error and len(vista.dialogos["error"]) == 1
    vista.pacientes.identificar.assert_not_called()
    # Un dato mal escrito no recarga la lista: la elección y lo escrito se conservan
    assert vista._tabla.seleccionado() == 250 and vista._boton_identificar.cget("state") == "normal"
    assert vista._datos_nn.nombres.get() == "Lucía"


def test_si_otro_usuario_lo_identifico_antes_se_avisa_y_se_recarga(crear):
    vista = crear()
    _elegir_nn(vista)
    vista.pacientes.identificar.side_effect = ReglaNegocioError("Otro usuario ya identificó o dio de baja a este "
                                                                "paciente.")
    vista.identificar()
    assert len(vista.dialogos["error"]) == 1
    assert vista.pacientes.listar_no_identificados.call_count == 2  # al abrir y después del error
    assert vista._tabla.seleccionado() == 250  # sigue en la lista: sigue elegido


def test_sin_nn_elegido_identificar_no_hace_nada(crear):
    vista = crear()
    vista._modo.elegir("nn")
    assert vista.identificar() == "break"
    vista.pacientes.buscar_por_documento.assert_not_called()


# ---- Teclado

def test_enter_hace_la_accion_de_cada_formulario(crear):
    vista = crear()
    # CustomTkinter asocia las teclas a la caja de Tk que el campo lleva dentro
    assert vista._documento.campo_numero._entry.bind("<Return>")
    assert all(c._entry.bind("<Return>") for c in vista._datos.entradas)
    assert vista._motivo._entry.bind("<Return>")
    assert all(c._entry.bind("<Return>") for c in (vista._documento_nn.campo_numero, *vista._datos_nn.entradas))


# ---- En la ventana principal

def test_pacientes_registrada_y_triaje_recibe_el_documento(raiz_tk, sesion_de, monkeypatch):
    from controllers.auth_controller import AuthController
    from models.permisos import Rol
    from views import app_principal

    class TriajeFalso(ctk.CTkFrame):
        def __init__(self, padre, *_):
            super().__init__(padre)
            self.buscados = []

        def buscar_documento(self, tipo, numero):
            self.buscados.append((tipo, numero))

    monkeypatch.setattr(app_principal, "TriageView", TriajeFalso)
    pantallas = {"pacientes": lambda padre, sesion, principal: app_principal.crear_pacientes(
                     padre, sesion, principal, pacientes=MagicMock(wraps=PacientesDemo(TriajeDemo()))),
                 "triaje": lambda padre, sesion, principal: TriajeFalso(padre)}
    principal = app_principal.AppPrincipal(raiz_tk, MagicMock(spec=AuthController), sesion_de(Rol.ENFERMERO),
                                           MagicMock(), pantallas=pantallas)
    principal.mostrar("pacientes")
    vista = principal.pantalla_actual
    vista._al_registrar_en_triaje(TipoDocumento.DNI, "48123456")
    assert principal.modulo_actual == "triaje"
    assert principal.pantalla_actual.buscados == [(TipoDocumento.DNI, "48123456")]
    assert app_principal.PANTALLAS["pacientes"] is app_principal.crear_pacientes
