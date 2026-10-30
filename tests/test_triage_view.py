from datetime import date, datetime
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from controllers.triaje_controller import TriajeController
from models.excepciones import PersistenciaError, ReglaNegocioError
from models.triaje import SignosVitales, Triaje
from prototipo.demo import PacientesDemo, TriajeDemo
from views import tema, triage_view
from views.componentes.campos import sin_error
from views.componentes.nivel import texto_nivel
from models.excepciones import ConexionBDError
from views.triage_view import (AVISO_BUSCAR, NADIE_ESPERA_TRIAJE, NO_REGISTRADO, SIGNOS, SIN_SUGERENCIA,
                               TEXTO_SIN_SIGNOS, TriageView, rango_admitido, texto_faltan)

AHORA = datetime(2026, 10, 30, 10, 0)
NORMALES = {"pa_sis": "120", "pa_dia": "80", "fc": "80", "fr": "16", "temp": "36,8", "sato2": "98"}
JUSTIFICACION = "Saturación en ascenso tras oxígeno"


@pytest.fixture
def dialogos(monkeypatch):
    """Los diálogos de la pantalla, anotados en lugar de abrirse (bloquearían la prueba)."""
    anotados = {"error": [], "info": []}
    monkeypatch.setattr(triage_view, "mostrar_error", lambda ventana, error: anotados["error"].append(error))
    monkeypatch.setattr(triage_view, "mostrar_info", lambda ventana, texto: anotados["info"].append(texto))
    return anotados


@pytest.fixture
def crear(raiz_tk, dialogos):
    """
    La pantalla con los controladores de demostración envueltos en MagicMock(wraps=...): se comportan como los
    reales (la estrategia Manchester, el catálogo del seed) y además anotan cada llamada.
    """
    def crear(pacientes=None, triaje=None):
        triaje_demo = TriajeDemo(lambda: AHORA)
        triaje = triaje or MagicMock(wraps=triaje_demo)
        pacientes = pacientes or MagicMock(wraps=PacientesDemo(triaje_demo, lambda: AHORA))
        vista = TriageView(raiz_tk, pacientes, triaje, reloj=lambda: AHORA)
        vista.pacientes, vista.triaje, vista.dialogos = pacientes, triaje, dialogos
        return vista
    return crear


def escribir(campo, texto):
    campo.delete(0, "end")
    campo.insert(0, texto)


def escribir_signos(vista, **cambios):
    for clave, valor in {**NORMALES, **cambios}.items():
        escribir(vista._campos_signos[clave], valor)
    vista.calcular_sugerencia()


def con_paciente_registrado(vista):
    escribir(vista._documento.campo_numero, "41234567")  # Carmen Rojas, registrada sin episodio abierto
    vista.buscar()
    escribir(vista._motivo, "Dolor en el pecho")


def boton(vista):
    return vista._boton_confirmar.cget("text"), vista._boton_confirmar.cget("state")


# ---- Al abrir

def test_al_abrir_no_hay_sugerencia_y_el_boton_dice_por_que(crear):
    vista = crear()
    assert vista._vacio.cget("text") == SIN_SUGERENCIA
    # Deshabilitado, el botón azul se ve igual: su texto dice qué falta
    assert boton(vista) == (TEXTO_SIN_SIGNOS, "disabled")
    assert vista._boton_reclasificar.cget("state") == "disabled"


def test_al_abrir_carga_seguros_sintomas_y_la_cola(crear):
    vista = crear()
    assert len(vista._casillas) == 10 and len(vista._seguros) == 4
    assert vista._tabla.cantidad == 2 and vista._modo.texto("cola") == "En cola (2)"
    assert vista.dialogos["error"] == []


def test_si_la_bd_falla_al_abrir_hay_un_solo_aviso_y_la_pantalla_se_usa(crear):
    triaje = MagicMock()
    triaje.listar_sintomas.side_effect = PersistenciaError("No se pudo leer el catálogo.")
    vista = crear(triaje=triaje)
    assert [str(e) for e in vista.dialogos["error"]] == ["No se pudo leer el catálogo."]
    assert vista._tabla.cantidad == 0 and vista._modo.texto("cola") == "En cola (0)"


def test_la_cola_vacia_lo_dice(crear):
    triaje = MagicMock()
    triaje.listar_sintomas.return_value = []
    triaje.cola_de_triaje.return_value = []
    vista = crear(triaje=triaje)
    assert vista._tabla._vacio.cget("text") == NADIE_ESPERA_TRIAJE


# ---- Signos vitales

def test_los_signos_son_los_del_controlador_con_los_rangos_del_modelo():
    # La vista no inventa rangos: los lee de SignosVitales.RANGOS
    assert set(SIGNOS) == set(TriajeController.SIGNOS) == set(SignosVitales.RANGOS)
    assert rango_admitido("pa_sis") == "20–300" and rango_admitido("temp") == "25–45"


def test_cada_signo_muestra_su_rango_como_ayuda(crear):
    vista = crear()
    assert vista._campos_signos["sato2"].cget("placeholder_text") == "0–100"


def test_con_los_6_signos_aparece_la_sugerencia_con_sus_criterios(crear):
    vista = crear()
    escribir_signos(vista, sato2="88")
    assert vista._insignia.nivel == 1 and vista._texto_nivel.cget("text") == f"Nivel {texto_nivel(1)}"
    assert vista._plazo.cget("text") == "Inmediato"
    criterios = [hijo.cget("text") for hijo in vista._criterios.winfo_children()]
    assert criterios == ["• SatO₂ 88 % < 90 %"]
    assert boton(vista) == ("Confirmar nivel 1", "normal")


def test_los_sintomas_marcados_cambian_la_sugerencia(crear):
    vista = crear()
    escribir_signos(vista)
    assert vista._insignia.nivel == 5
    vista._casillas[2].select()  # dolor torácico opresivo (8.5): nivel 2
    vista.calcular_sugerencia()
    assert vista._insignia.nivel == 2
    vista.triaje.sugerir.assert_called_with(vista.leer_signos(), [2])


def test_la_temperatura_acepta_coma_o_punto(crear):
    vista = crear()
    escribir_signos(vista, temp="37.5")
    assert vista.leer_signos()["temp"] == 37.5
    escribir_signos(vista, temp="37,5")
    assert vista.leer_signos()["temp"] == 37.5


def test_un_signo_vacio_no_es_un_error_pero_no_hay_sugerencia(crear):
    vista = crear()
    escribir_signos(vista, fr="")
    assert vista.leer_signos() is None and vista._sugerencia is None
    assert not getattr(vista._campos_signos["fr"], "_sigtac_error", False)
    vista.triaje.sugerir.assert_not_called()


@pytest.mark.parametrize("clave, valor, aviso", [
    ("pa_sis", "301", "PA sistólica fuera del rango admitido (20–300)."),
    ("pa_sis", "19", "PA sistólica fuera del rango admitido (20–300)."),
    ("fc", "9x", "FC debe ser un número entero."),
    ("sato2", "97,5", "SatO₂ debe ser un número entero."),
])
def test_un_signo_invalido_se_marca_y_se_explica_junto_a_los_campos(crear, clave, valor, aviso):
    vista = crear()
    escribir_signos(vista, **{clave: valor})
    campo = vista._campos_signos[clave]
    assert campo._sigtac_error and tuple(campo.cget("border_color")) == tema.COLOR_ERROR
    assert vista._aviso_signos.cget("text") == aviso and vista._aviso_signos.winfo_manager() == "grid"
    assert vista._sugerencia is None
    assert vista.dialogos["error"] == []  # no es un diálogo: se ve junto al campo


@pytest.mark.parametrize("valor", ["20", "300"])
def test_los_limites_del_rango_se_aceptan(crear, valor):
    vista = crear()
    escribir_signos(vista, pa_sis=valor)
    assert vista.leer_signos()["pa_sis"] == int(valor)


def test_al_corregir_el_signo_se_quita_el_error(crear):
    vista = crear()
    escribir_signos(vista, fc="9x")
    escribir_signos(vista, fc="90")
    assert not vista._campos_signos["fc"]._sigtac_error
    assert vista._aviso_signos.cget("text") == "" and vista._aviso_signos.winfo_manager() == ""


def test_si_falla_la_sugerencia_se_lee_en_el_panel_sin_dialogos(crear):
    triaje = MagicMock(wraps=TriajeDemo(lambda: AHORA))
    triaje.sugerir.side_effect = PersistenciaError("No se pudo leer el catálogo de síntomas.")
    vista = crear(triaje=triaje)
    escribir_signos(vista)
    assert vista._vacio.cget("text") == "No se pudo leer el catálogo de síntomas."
    assert tuple(vista._vacio.cget("text_color")) == tema.COLOR_ERROR
    assert vista.dialogos["error"] == [] and boton(vista)[1] == "disabled"


def test_escribir_programa_el_calculo_y_destruir_lo_cancela(crear):
    vista = crear()
    vista._programar_sugerencia()
    tarea = vista._tarea
    assert tarea is not None
    vista.destroy()
    assert tarea not in vista.tk.call("after", "info")


# ---- Paso 1: el paciente

def test_buscar_un_paciente_registrado_muestra_su_ficha(crear):
    vista = crear()
    con_paciente_registrado(vista)
    assert vista._ficha.winfo_manager() == "pack" and vista._registro.winfo_manager() == ""
    assert vista._ficha.nombre == "Carmen Rojas Llanos"
    assert vista._ficha.datos.endswith("mujer · SIS (Seguro Integral de Salud)")


def test_buscar_un_documento_nuevo_abre_el_registro(crear):
    vista = crear()
    escribir(vista._documento.campo_numero, "48123456")
    vista.buscar()
    assert vista._registro.winfo_manager() == "pack"
    assert NO_REGISTRADO in [h.cget("text") for h in vista._registro.winfo_children() if isinstance(h, ctk.CTkLabel)]
    # El sexo y el seguro no toman un valor por omisión
    assert vista._datos.sexo.get() == "" and vista._datos.seguro.get() == ""


def test_un_documento_invalido_se_marca_y_se_explica_bajo_el_campo(crear):
    vista = crear()
    escribir(vista._documento.campo_numero, "123")
    vista.buscar()
    assert vista._documento.campo_numero._sigtac_error
    assert vista._aviso.winfo_manager() == "pack" and vista._aviso.cget("text") != AVISO_BUSCAR
    assert tuple(vista._aviso.cget("text_color")) == tema.COLOR_ERROR
    assert vista.dialogos["error"] == []  # como un signo inválido: junto al campo, sin diálogo
    escribir(vista._documento.campo_numero, "41234567")
    vista.buscar()
    assert not vista._documento.campo_numero._sigtac_error


def test_al_corregir_el_documento_el_rojo_y_su_explicacion_se_van(crear):
    vista = crear()
    numero = vista._documento.campo_numero
    escribir(numero, "123")
    vista.buscar()
    vista._documento_editado()  # soltar el Enter que buscó: el texto no cambió, el error sigue
    assert numero._sigtac_error and tuple(vista._aviso.cget("text_color")) == tema.COLOR_ERROR
    escribir(numero, "1234")
    vista._documento_editado()
    assert not numero._sigtac_error
    assert vista._aviso.cget("text") == AVISO_BUSCAR
    assert tuple(vista._aviso.cget("text_color")) == tema.COLOR_TEXTO_SECUNDARIO


@pytest.mark.parametrize("cambiar", [lambda v: v._identidad.elegir("documento"), lambda v: v._modo.elegir("cola")])
def test_al_cambiar_de_modo_no_queda_un_borde_rojo_sin_explicacion(crear, cambiar):
    vista = crear()
    escribir(vista._documento.campo_numero, "123")
    vista.buscar()
    escribir(vista._motivo, "Dolor")
    escribir_signos(vista)
    vista._identidad.elegir("nn", avisar=False)  # sin limpiar todavía: confirmar marca sexo, edad...
    vista.confirmar()
    assert vista._sexo_nn._sigtac_error
    cambiar(vista)
    for campo in (vista._documento.campo_numero, vista._sexo_nn, vista._edad_nn, vista._seguro_nn):
        assert not getattr(campo, "_sigtac_error", False)
    assert vista._aviso.cget("text") == AVISO_BUSCAR


def test_un_campo_marcado_pierde_el_rojo_al_corregirlo(crear):
    from views.componentes.campos import mover_opcion
    vista = crear()
    vista._identidad.elegir("nn")
    escribir(vista._edad_nn, "unos 30")
    escribir(vista._motivo, "Dolor")
    escribir_signos(vista)
    vista.confirmar()  # falta el sexo: lo marca
    assert vista._sexo_nn._sigtac_error
    mover_opcion(vista._sexo_nn, 1)  # elegir una opción (↓, o el mouse: el mismo command)
    assert not vista._sexo_nn._sigtac_error
    vista.confirmar()  # ahora la edad no se puede leer
    assert vista._edad_nn._sigtac_error
    escribir(vista._edad_nn, "30")
    # Tk no entrega teclas a una ventana oculta: se comprueba la asociación y se ejecuta lo que hace la tecla
    assert vista._edad_nn._entry.bind("<KeyRelease>")
    sin_error(vista._edad_nn)
    assert not vista._edad_nn._sigtac_error


def test_sin_conexion_al_buscar_avisa_sin_culpar_al_documento(crear):
    pacientes = MagicMock()
    pacientes.listar_seguros.return_value = []
    pacientes.buscar_por_documento.side_effect = ConexionBDError("No hay conexión con la base de datos.")
    vista = crear(pacientes=pacientes)
    escribir(vista._documento.campo_numero, "41234567")
    vista.buscar()
    assert [str(e) for e in vista.dialogos["error"]] == ["No hay conexión con la base de datos."]
    assert not getattr(vista._documento.campo_numero, "_sigtac_error", False)


def test_cambiar_el_documento_despues_de_buscar_olvida_la_ficha(crear):
    vista = crear()
    con_paciente_registrado(vista)
    escribir(vista._documento.campo_numero, "4123456")
    vista._documento_editado()
    assert vista._aviso.winfo_manager() == "pack" and vista._paciente is None


def test_cambiar_a_la_cola_y_a_sin_identificar(crear):
    vista = crear()
    vista._modo.elegir("cola")
    assert vista._en_cola.winfo_manager() == "pack" and vista._nuevo.winfo_manager() == ""
    vista._modo.elegir("nuevo")
    vista._identidad.elegir("nn")
    assert vista._sin_documento.winfo_manager() == "pack" and vista._con_documento.winfo_manager() == ""


def test_cambiar_de_modo_no_deja_a_la_vista_una_ficha_olvidada(crear):
    vista = crear()
    con_paciente_registrado(vista)
    vista._identidad.elegir("nn")
    vista._identidad.elegir("documento")
    assert vista._aviso.winfo_manager() == "pack" and vista._ficha.winfo_manager() == ""


def test_la_cola_cabe_en_el_formulario_a_1093x614():
    # Formulario a 1093×614: 1093 - barra 200 - 1 - márgenes 2×24 - panel 320 - barra de desplazamiento y sus
    # márgenes (~24) - interior de la tarjeta 2×16 ≈ 468; las columnas no pueden pasar de ahí (sin scroll horizontal)
    assert sum(ancho for _, ancho in TriageView.COLUMNAS_COLA) <= 468
    assert all(ancho % 4 == 0 for _, ancho in TriageView.COLUMNAS_COLA)


# ---- Reclasificar (RN-10)

def test_reclasificar_pide_justificacion_con_el_minimo_del_modelo(crear):
    vista = crear()
    escribir_signos(vista, sato2="88")
    vista.alternar_reclasificacion()
    assert vista._reclasificacion.winfo_manager() == "pack" and vista._nivel_final.get() == texto_nivel(1)
    assert boton(vista) == ("Confirmar nivel 1", "normal")  # mismo nivel: no hace falta justificar
    vista._nivel_final.set(texto_nivel(2))
    vista._actualizar_acciones()
    minimo = Triaje.MIN_JUSTIFICACION
    # Lo que falta lo dice el botón, que siempre está a la vista (también a 1093×614)
    assert boton(vista) == (f"Faltan {minimo} caracteres (mínimo {minimo})", "disabled")
    vista._justificacion.insert("1.0", "x" * (minimo - 1))
    vista._actualizar_acciones()
    assert boton(vista) == (texto_faltan(1), "disabled")
    vista._justificacion.insert("end", "x")
    vista._actualizar_acciones()
    assert boton(vista) == ("Confirmar nivel 2", "normal")


def test_en_la_justificacion_tab_pasa_al_control_siguiente(crear):
    vista = crear()
    caja = vista._justificacion._textbox
    assert caja.bind("<Tab>") and caja.bind("<Shift-Tab>")


def test_el_panel_se_recorre_en_el_orden_de_lectura(crear):
    # Tk tabula en el orden de creación: el contenido (nivel final, justificación) antes que los botones del pie
    vista = crear()
    orden = [str(w) for w in (vista._nivel_final, vista._justificacion, vista._boton_confirmar,
                              vista._boton_reclasificar)]
    creados = [str(w) for w in _descendientes(vista) if str(w) in orden]
    assert creados == orden


def _descendientes(widget):
    for hijo in widget.winfo_children():
        yield hijo
        yield from _descendientes(hijo)


def test_cancelar_la_reclasificacion_vuelve_a_la_sugerencia(crear):
    vista = crear()
    escribir_signos(vista, sato2="88")
    vista.alternar_reclasificacion()
    vista._nivel_final.set(texto_nivel(3))
    vista._justificacion.insert("1.0", JUSTIFICACION)
    vista.alternar_reclasificacion()
    assert vista._reclasificacion.winfo_manager() == "" and vista._texto_justificacion() == ""
    assert boton(vista) == ("Confirmar nivel 1", "normal")
    assert vista._boton_reclasificar.cget("text") == "Reclasificar"


def test_sin_sugerencia_no_se_puede_reclasificar(crear):
    vista = crear()
    vista.alternar_reclasificacion()
    assert not vista._reclasificando


def test_si_un_signo_se_borra_para_corregirlo_la_justificacion_se_conserva(crear):
    vista = crear()
    escribir_signos(vista)
    vista.alternar_reclasificacion()
    vista._nivel_final.set(texto_nivel(3))
    vista._justificacion.insert("1.0", JUSTIFICACION)
    escribir_signos(vista, fc="")
    assert boton(vista) == (TEXTO_SIN_SIGNOS, "disabled")
    escribir_signos(vista, fc="85")
    assert vista._reclasificando and vista._texto_justificacion() == JUSTIFICACION
    assert vista.nivel_final() == 3 and boton(vista) == ("Confirmar nivel 3", "normal")


# ---- Confirmar

def test_confirmar_un_paciente_registrado_abre_su_episodio_y_registra_el_triaje(crear):
    vista = crear()
    con_paciente_registrado(vista)
    escribir_signos(vista, sato2="88")
    vista._casillas[2].select()
    vista.calcular_sugerencia()
    vista.confirmar()
    vista.pacientes.registrar.assert_not_called()
    vista.pacientes.abrir_episodio.assert_called_once_with(200, "Dolor en el pecho")
    # El episodio que se acaba de abrir (el primero que crea la demostración) es el que se tría
    vista.triaje.registrar.assert_called_once_with(
        301, {"pa_sis": 120, "pa_dia": 80, "fc": 80, "fr": 16, "temp": 36.8, "sato2": 88}, [2], None, None)
    assert vista.dialogos["info"] == [f"Triaje registrado: nivel {texto_nivel(1)}. El paciente pasa a la cola de cama."]


def test_despues_de_registrar_el_formulario_queda_limpio(crear):
    vista = crear()
    con_paciente_registrado(vista)
    escribir_signos(vista)
    vista._casillas[9].select()
    vista.confirmar()
    assert vista._documento.valores()[1] == "" and vista._motivo.get() == ""
    assert all(campo.get() == "" for campo in vista._campos_signos.values())
    assert vista.sintomas_elegidos() == [] and vista._sugerencia is None
    assert vista._aviso.winfo_manager() == "pack" and vista._paciente is None


def test_confirmar_un_paciente_nuevo_lo_registra_primero(crear):
    vista = crear()
    escribir(vista._documento.campo_numero, "48123456")
    vista.buscar()
    escribir(vista._datos.nombres, "Pedro")
    escribir(vista._datos.apellidos, "Quispe Mamani")
    escribir(vista._datos.fecha_nac, "14/03/1985")
    vista._datos.sexo.set("Varón")
    vista._datos.seguro.set("EsSalud")
    escribir(vista._motivo, "Caída de altura")
    escribir_signos(vista)
    vista.confirmar()
    vista.pacientes.registrar.assert_called_once_with("DNI", "48123456", "Pedro", "Quispe Mamani", date(1985, 3, 14),
                                                      "M", 1)
    assert vista.triaje.registrar.call_count == 1 and vista.dialogos["error"] == []


def test_confirmar_sin_identificar(crear):
    vista = crear()
    vista._identidad.elegir("nn")
    vista._sexo_nn.set("Mujer")
    escribir(vista._edad_nn, "30")
    vista._seguro_nn.set("Particular / Sin Seguro")
    escribir(vista._motivo, "Hallada inconsciente")
    escribir_signos(vista)
    vista.confirmar()
    vista.pacientes.registrar_no_identificado.assert_called_once_with("F", 30, 4)
    assert vista.triaje.registrar.call_count == 1


def _nuevo_sin_fecha(vista):
    escribir(vista._documento.campo_numero, "48123456")
    vista.buscar()
    escribir(vista._datos.fecha_nac, "1985-03-14")


@pytest.mark.parametrize("preparar, mensaje, campo", [
    (lambda v: None, "Busque el documento del paciente antes de confirmar.", lambda v: v._documento.campo_numero),
    (lambda v: (v._identidad.elegir("nn"), escribir(v._edad_nn, "30")), "Elija el sexo del paciente.",
     lambda v: v._sexo_nn),
    (lambda v: (v._identidad.elegir("nn"), v._sexo_nn.set("Mujer"), escribir(v._edad_nn, "unos 30")),
     "La edad aparente debe ser un número entero.", lambda v: v._edad_nn),
    (_nuevo_sin_fecha, "La fecha de nacimiento debe tener la forma dd/mm/aaaa", lambda v: v._datos.fecha_nac),
])
def test_los_datos_que_faltan_se_avisan_y_marcan_su_campo_antes_de_escribir(crear, preparar, mensaje, campo):
    vista = crear()
    preparar(vista)
    escribir(vista._motivo, "Dolor")
    escribir_signos(vista)
    vista.confirmar()
    assert len(vista.dialogos["error"]) == 1 and str(vista.dialogos["error"][0]).startswith(mensaje)
    assert campo(vista)._sigtac_error
    vista.pacientes.registrar.assert_not_called()
    vista.pacientes.abrir_episodio.assert_not_called()
    vista.triaje.registrar.assert_not_called()
    assert vista.leer_signos() is not None  # el formulario conserva lo escrito


def test_confirmar_desde_la_cola_usa_el_episodio_elegido(crear):
    vista = crear()
    vista._modo.elegir("cola")
    vista._tabla.seleccionar(102)
    escribir_signos(vista)
    vista.confirmar()
    vista.pacientes.abrir_episodio.assert_not_called()
    assert vista.triaje.registrar.call_args.args[0] == 102
    assert vista._tabla.cantidad == 1 and vista._modo.texto("cola") == "En cola (1)"


def test_confirmar_desde_la_cola_sin_elegir_avisa(crear):
    vista = crear()
    vista._modo.elegir("cola")
    escribir_signos(vista)
    vista.confirmar()
    assert [str(e) for e in vista.dialogos["error"]] == ["Elija en la cola al paciente que va a triar."]
    vista.triaje.registrar.assert_not_called()


def test_reclasificar_registra_el_nivel_final_con_su_justificacion(crear):
    vista = crear()
    con_paciente_registrado(vista)
    escribir_signos(vista, sato2="88")
    vista.alternar_reclasificacion()
    vista._nivel_final.set(texto_nivel(2))
    vista._justificacion.insert("1.0", JUSTIFICACION)
    vista._actualizar_acciones()
    vista.confirmar()
    args = vista.triaje.registrar.call_args.args
    assert args[3:] == (2, JUSTIFICACION)
    assert vista.dialogos["info"][0].startswith(f"Triaje registrado: nivel {texto_nivel(2)}.")


def test_si_falla_el_triaje_el_reintento_no_vuelve_a_abrir_el_episodio(crear):
    vista = crear()
    con_paciente_registrado(vista)
    escribir_signos(vista)
    registrar = vista.triaje.registrar
    registrar.side_effect = [ReglaNegocioError("Otro usuario cerró el episodio."), 1]
    vista.confirmar()
    assert [str(e) for e in vista.dialogos["error"]] == ["Otro usuario cerró el episodio."]
    assert vista._modo.texto("cola") == "En cola (3)"  # el episodio ya abierto aparece en la cola
    assert vista._motivo.get() == "Dolor en el pecho"  # el formulario conserva lo escrito
    vista.confirmar()
    assert vista.pacientes.abrir_episodio.call_count == 1 and registrar.call_count == 2
    assert len(vista.dialogos["info"]) == 1


def test_si_falla_abrir_el_episodio_el_reintento_no_vuelve_a_registrar_al_paciente(crear):
    vista = crear()
    escribir(vista._documento.campo_numero, "48123456")
    vista.buscar()
    escribir(vista._datos.nombres, "Pedro")
    escribir(vista._datos.apellidos, "Quispe")
    escribir(vista._datos.fecha_nac, "14/03/1985")
    vista._datos.sexo.set("Varón")
    vista._datos.seguro.set("EsSalud")
    escribir_signos(vista)  # sin motivo de consulta
    vista.confirmar()
    assert [str(e) for e in vista.dialogos["error"]] == ["El motivo de consulta es obligatorio."]
    escribir(vista._motivo, "Caída")
    vista.confirmar()
    assert vista.pacientes.registrar.call_count == 1 and vista.triaje.registrar.call_count == 1


def test_enter_justo_despues_de_escribir_registra_el_nivel_recalculado(crear):
    vista = crear()
    con_paciente_registrado(vista)
    escribir_signos(vista)  # nivel 5
    escribir(vista._campos_signos["sato2"], "85")
    vista._programar_sugerencia()  # la pausa de 300 ms todavía no pasó
    vista.confirmar()
    # El aviso dice el nivel que el controlador guarda (1), no el que mostraba el botón antes de la pausa (5)
    assert vista.dialogos["info"][0].startswith(f"Triaje registrado: nivel {texto_nivel(1)}.")
    assert vista._tarea is None


def test_sin_sugerencia_confirmar_no_hace_nada(crear):
    vista = crear()
    con_paciente_registrado(vista)
    assert vista.confirmar() == "break"
    vista.pacientes.abrir_episodio.assert_not_called()


def test_enter_en_un_signo_o_en_el_motivo_confirma(crear):
    vista = crear()
    # CustomTkinter asocia las teclas a la caja de Tk que el campo lleva dentro
    assert vista._campos_signos["sato2"]._entry.bind("<Return>") and vista._motivo._entry.bind("<Return>")
    assert vista._documento.campo_numero._entry.bind("<Return>")  # en el documento, Enter busca


def test_destruir_la_pantalla_cancela_el_foco_pendiente(crear):
    vista = crear()
    tarea = vista._tarea_foco
    vista.destroy()
    assert tarea not in vista.tk.call("after", "info")


# ---- En la ventana principal

def test_el_triaje_esta_registrado_con_los_controladores_de_la_sesion(raiz_tk, sesion_de, monkeypatch):
    from controllers.paciente_controller import PacienteController
    from models.permisos import Rol
    from views import app_principal
    recibidos = {}

    class TriajeFalso(ctk.CTkFrame):
        def __init__(self, padre, pacientes, triaje):
            super().__init__(padre)
            recibidos.update(pacientes=pacientes, triaje=triaje)

    monkeypatch.setattr(app_principal, "TriageView", TriajeFalso)
    assert app_principal.PANTALLAS["triaje"] is app_principal.crear_triaje
    app_principal.crear_triaje(raiz_tk, sesion_de(Rol.ENFERMERO), None)
    assert isinstance(recibidos["pacientes"], PacienteController)
    assert isinstance(recibidos["triaje"], TriajeController)
