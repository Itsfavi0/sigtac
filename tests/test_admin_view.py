from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from models.auditoria import AccionAuditoria
from models.excepciones import ConexionBDError, RegistroDuplicadoError
from models.permisos import Rol
from prototipo.demo import AdminDemo, PacientesDemo, TriajeDemo
from views import admin_view
from views.admin_view import (AVISO_BUSCAR, CLAVES_DISTINTAS, ELIJA_CUENTA, FALTA_ROL, LIMITE_BITACORA, NO_ENCONTRADO,
                              SIN_LECTURA, TEXTO_ELEGIR_EMPLEADO, AdminView, estado_cuenta, nombres_de_cuentas,
                              texto_detalles, texto_tabla)
from views.componentes.campos import mover_opcion

HOY = date(2026, 11, 4)
AHORA = datetime(2026, 11, 4, 12, 0)
CLAVE = "Guardia2026"
REGISTRADO = ("DNI", "41234567")   # Carmen Rojas Llanos, sin episodio abierto
EN_COLA = ("DNI", "70112233")      # Rosa Huamán Paredes, espera triaje


@pytest.fixture
def dialogos(monkeypatch):
    anotados = {"error": [], "info": []}
    monkeypatch.setattr(admin_view, "mostrar_error", lambda ventana, error: anotados["error"].append(error))
    monkeypatch.setattr(admin_view, "mostrar_info", lambda ventana, texto: anotados["info"].append(texto))
    return anotados


@pytest.fixture
def crear(raiz_tk, dialogos):
    """La pantalla con los controladores de demostración envueltos en MagicMock(wraps=...): reglas reales."""
    def crear(admin=None, pacientes=None):
        demo = AdminDemo(ahora=lambda: AHORA)
        admin = admin or MagicMock(wraps=demo)
        pacientes = pacientes or MagicMock(wraps=PacientesDemo(TriajeDemo(ahora=lambda: AHORA),
                                                                al_auditar=demo.anotar))
        vista = AdminView(raiz_tk, admin, pacientes, hoy=lambda: HOY)
        vista.admin, vista.pacientes, vista.dialogos, vista.raiz = admin, pacientes, dialogos, raiz_tk
        return vista
    return crear


def filas(tabla) -> list[tuple]:
    return [tuple(tabla._arbol.item(iid, "values")) for iid in tabla._arbol.get_children()]


def fila_de(vista, nombre) -> tuple:
    return next(f for f in filas(vista._tabla_cuentas) if f[0] == nombre)


def elegir(vista, tabla, id_fila):
    tabla.seleccionar(id_fila)
    vista.raiz.update()


def escribir(campo, texto, soltar=None):
    """Escribe como el usuario: reemplaza el texto y, si se indica, avisa la tecla soltada."""
    campo.delete(0, "end")
    campo.insert(0, texto)
    if soltar is not None:
        soltar()


def marcado(campo) -> bool:
    return getattr(campo, "_sigtac_error", False)


# ---- Funciones de texto

@pytest.mark.parametrize("activo, bloqueada, texto", [(True, False, "Activa"), (True, True, "Bloqueada"),
                                                      (False, True, "Desactivada"), (False, False, "Desactivada")])
def test_estado_de_la_cuenta(activo, bloqueada, texto):
    assert estado_cuenta(MagicMock(activo=activo, bloqueada=bloqueada)) == texto


def test_textos_de_la_bitacora():
    assert texto_tabla("episodio_emergencia") == "Episodio emergencia"
    assert texto_detalles({"rol_anterior": "Médico", "activo": False, "campos": ["nombres", "sexo"]}) == (
        "rol anterior: Médico · activo: no · campos: nombres, sexo")
    assert texto_detalles(None) == "" and texto_detalles({}) == ""


def test_dos_cuentas_con_el_mismo_nombre_se_distinguen():
    cuentas = [MagicMock(id_usuario=2, nombre_completo="Luis Ramos Díaz"),
               MagicMock(id_usuario=9, nombre_completo="Luis Ramos Díaz"),
               MagicMock(id_usuario=3, nombre_completo="Ana Quispe Rojas")]
    assert nombres_de_cuentas(cuentas) == {2: "Luis Ramos Díaz (cuenta 2)", 9: "Luis Ramos Díaz (cuenta 9)",
                                           3: "Ana Quispe Rojas"}


# ---- Al abrir

def test_al_abrir_lista_las_cuentas_y_la_bitacora_de_hoy(crear):
    vista = crear()
    assert [f[0] for f in filas(vista._tabla_cuentas)][:2] == ["Rosa Díaz Vela", "Pedro Huamán Ccori"]
    assert fila_de(vista, "Ana Quispe Rojas") == ("Ana Quispe Rojas", "Enfermera", "Enfermero de Triaje", "Bloqueada")
    assert vista._modo.texto("cuentas") == "Cuentas (6)" and vista._modo.texto("nueva") == "Nueva cuenta (2)"
    assert vista._cuenta_titulo.cget("text") == ELIJA_CUENTA
    assert all(b.cget("state") == "disabled" for b in (vista._boton_acceso, vista._boton_desbloquear,
                                                        vista._boton_rol, vista._boton_clave))
    assert vista.periodo.atajos.valor == "hoy"
    vista.admin.bitacora.assert_called_once_with(HOY, HOY, tabla=None, id_usuario=None, limite=LIMITE_BITACORA)
    assert filas(vista._tabla_bitacora)[0][:5] == ("04/11/2026 11:48", "Rosa Díaz Vela", "Cambio", "Cama", "7")
    assert vista._resumen_bitacora.cget("text") == "El 04/11/2026: 4 registros."


def test_si_la_bd_falla_al_abrir_hay_un_solo_aviso(crear):
    admin = MagicMock()
    admin.listar_cuentas.side_effect = ConexionBDError("No hay conexión con la base de datos.")
    vista = crear(admin=admin)
    assert [str(e) for e in vista.dialogos["error"]] == ["No hay conexión con la base de datos."]
    assert vista._tabla_cuentas.cantidad == 0 and vista._modo.texto("cuentas") == "Cuentas (0)"
    # las tablas no dicen «no hay cuentas»: no se pudieron leer
    assert vista._tabla_cuentas._vacio.cget("text") == SIN_LECTURA
    assert vista._tabla_empleados._vacio.cget("text") == SIN_LECTURA
    admin.bitacora.assert_not_called()


def test_si_solo_falla_la_bitacora_al_abrir_es_el_unico_aviso(crear):
    admin = MagicMock(wraps=AdminDemo(ahora=lambda: AHORA))
    admin.bitacora.side_effect = ConexionBDError("No hay conexión con la base de datos.")
    vista = crear(admin=admin)
    assert len(vista.dialogos["error"]) == 1 and vista._tabla_cuentas.cantidad == 6
    assert vista._tabla_bitacora._vacio.cget("text") == SIN_LECTURA


# ---- Cuentas

def test_elegir_una_cuenta_bloqueada(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 3)
    assert vista._cuenta_titulo.cget("text") == "Cuenta de Ana Quispe Rojas"
    assert vista._boton_desbloquear.cget("state") == "normal" and vista._boton_acceso.cget("text") == "Desactivar"
    assert vista._rol.get() == Rol.ENFERMERO.value
    vista.desbloquear()
    vista.admin.desbloquear.assert_called_once_with(3)
    assert fila_de(vista, "Ana Quispe Rojas")[3] == "Activa"
    assert vista._tabla_cuentas.seleccionado() == 3  # sigue elegida para seguir con ella
    assert vista.dialogos["info"] == ["Cuenta de A. Quispe desbloqueada."]


def test_desbloquear_sirve_con_intentos_sin_bloqueo(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 4)  # 2 intentos fallidos, aún activa
    assert vista._boton_desbloquear.cget("state") == "normal"
    elegir(vista, vista._tabla_cuentas, 2)  # sin intentos
    assert vista._boton_desbloquear.cget("state") == "disabled"


def test_desactivar_y_activar_una_cuenta(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 2)
    vista.cambiar_acceso()
    vista.admin.desactivar.assert_called_once_with(2)
    assert fila_de(vista, "Luis Ramos Díaz")[3] == "Desactivada"
    assert vista._boton_acceso.cget("text") == "Activar"
    vista.cambiar_acceso()
    vista.admin.activar.assert_called_once_with(2)
    assert fila_de(vista, "Luis Ramos Díaz")[3] == "Activa"


def test_el_administrador_no_se_desactiva_a_si_mismo(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 1)
    vista.cambiar_acceso()
    assert "otro administrador" in str(vista.dialogos["error"][0])
    assert vista._tabla_cuentas.seleccionado() == 1 and fila_de(vista, "Elena Ríos Paredes")[3] == "Activa"


def test_cambiar_el_rol(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 2)
    vista._rol.set(Rol.JEFE_GUARDIA.value)
    vista.cambiar_rol()
    vista.admin.cambiar_rol.assert_called_once_with(2, Rol.JEFE_GUARDIA.value)
    assert fila_de(vista, "Luis Ramos Díaz")[2] == Rol.JEFE_GUARDIA.value
    assert vista.dialogos["info"] == [f"L. Ramos ahora tiene el rol {Rol.JEFE_GUARDIA.value}."]


def test_cambiar_rol_solo_responde_con_otro_rol(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 2)
    assert vista._boton_rol.cget("state") == "disabled"  # la lista muestra el rol que ya tiene
    mover_opcion(vista._rol, 1)  # ↓ en la lista, como el usuario
    assert vista._boton_rol.cget("state") == "normal"


def test_cambiar_al_mismo_rol_lo_rechaza_el_modelo(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 2)
    vista.cambiar_rol()
    assert "ya tiene el rol" in str(vista.dialogos["error"][0])


def test_el_administrador_no_cambia_su_propio_rol(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 1)
    vista._rol.set(Rol.MEDICO.value)
    vista.cambiar_rol()
    assert "otro administrador" in str(vista.dialogos["error"][0])
    assert fila_de(vista, "Elena Ríos Paredes")[2] == Rol.ADMINISTRADOR.value


def test_restablecer_con_claves_distintas_no_llama_al_controlador(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 3)
    campos = vista._clave_cuenta
    escribir(campos.clave, CLAVE)
    escribir(campos.repetir, "Guardia2027")
    vista.restablecer_clave()
    vista.admin.restablecer_clave.assert_not_called()
    assert marcado(campos.repetir) and campos.aviso.cget("text") == CLAVES_DISTINTAS
    assert vista.dialogos["error"] == []  # se explica bajo el campo, sin diálogo


def test_una_clave_debil_se_explica_y_la_marca_se_va_al_corregir(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 3)
    campos = vista._clave_cuenta
    escribir(campos.clave, "corta")
    escribir(campos.repetir, "corta")
    vista.restablecer_clave()
    assert marcado(campos.clave) and "8 caracteres" in campos.aviso.cget("text")
    campos._editada()  # soltar el Enter: el texto no cambió
    assert marcado(campos.clave)
    escribir(campos.clave, "cortas", soltar=campos._editada)
    assert not marcado(campos.clave) and campos.aviso.cget("text") == ""


def test_restablecer_la_clave_la_borra_y_quita_el_bloqueo(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 3)
    escribir(vista._clave_cuenta.clave, CLAVE)
    escribir(vista._clave_cuenta.repetir, CLAVE)
    assert vista.restablecer_clave() == "break"
    vista.admin.restablecer_clave.assert_called_once_with(3, CLAVE)
    assert vista._clave_cuenta.clave.get() == "" and vista._clave_cuenta.repetir.get() == ""
    assert fila_de(vista, "Ana Quispe Rojas")[3] == "Activa"
    assert vista.dialogos["info"] == ["Clave de A. Quispe restablecida. Entréguesela en persona."]


def test_la_clave_no_queda_guardada_ni_pasa_a_otra_cuenta(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 3)
    escribir(vista._clave_cuenta.clave, "corta")
    escribir(vista._clave_cuenta.repetir, "corta")
    vista.restablecer_clave()
    guardado = {k: v for k, v in vars(vista._clave_cuenta).items() if isinstance(v, (str, tuple))}
    assert "corta" not in repr(guardado)  # de lo rechazado solo queda un resumen
    elegir(vista, vista._tabla_cuentas, 2)
    assert vista._clave_cuenta.clave.get() == "" and vista._clave_cuenta.repetir.get() == ""
    assert not marcado(vista._clave_cuenta.clave)


def test_recargar_la_misma_cuenta_conserva_la_clave_que_se_escribe(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 3)
    escribir(vista._clave_cuenta.clave, CLAVE)
    vista.desbloquear()  # recarga conservando la elección
    vista._modo.elegir("nueva")
    vista._modo.elegir("cuentas")  # vuelve a recargar
    assert vista._tabla_cuentas.seleccionado() == 3 and vista._clave_cuenta.clave.get() == CLAVE


def test_la_clave_no_aparece_en_dialogos_ni_en_el_log(crear, caplog):
    vista = crear()
    vista.admin.restablecer_clave.side_effect = [ValueError("La clave debe combinar letras y números."),
                                                 ConexionBDError("No hay conexión con la base de datos.")]
    elegir(vista, vista._tabla_cuentas, 3)
    for clave in ("ClaveDebil", CLAVE):  # rechazada por la política y luego fallida en la BD
        escribir(vista._clave_cuenta.clave, clave)
        escribir(vista._clave_cuenta.repetir, clave)
        vista.restablecer_clave()
    textos = [str(e) for e in vista.dialogos["error"]] + vista.dialogos["info"]
    textos += [vista._clave_cuenta.aviso.cget("text"), caplog.text]
    assert not any(c in t for t in textos for c in ("ClaveDebil", CLAVE))
    assert [str(e) for e in vista.dialogos["error"]] == ["No hay conexión con la base de datos."]


def test_enter_en_las_claves_restablece(crear):
    vista = crear()
    for campo in vista._clave_cuenta.entradas:
        assert "restablecer_clave" in campo._entry.bind("<Return>")


# ---- Nueva cuenta

def test_sin_empleado_elegido_el_boton_dice_por_que(crear):
    vista = crear()
    assert vista._boton_crear.cget("text") == TEXTO_ELEGIR_EMPLEADO
    assert vista._boton_crear.cget("state") == "disabled"
    elegir(vista, vista._tabla_empleados, 7)
    assert vista._boton_crear.cget("text") == "Crear cuenta para C. Vega"


def test_sin_rol_se_pide_y_al_elegirlo_se_va_el_aviso(crear):
    vista = crear()
    elegir(vista, vista._tabla_empleados, 7)
    escribir(vista._clave_nueva.clave, CLAVE)
    escribir(vista._clave_nueva.repetir, CLAVE)
    vista.crear_cuenta()
    vista.admin.crear_cuenta.assert_not_called()
    assert marcado(vista._rol_nuevo) and vista._clave_nueva.aviso.cget("text") == FALTA_ROL
    mover_opcion(vista._rol_nuevo, 1)  # elegirlo como el usuario: avisa por el command de la lista
    assert vista._rol_nuevo.get() == list(Rol)[0].value
    assert not marcado(vista._rol_nuevo) and vista._clave_nueva.aviso.cget("text") == ""


def test_nueva_cuenta_con_claves_distintas_o_debiles(crear):
    vista = crear()
    elegir(vista, vista._tabla_empleados, 7)
    vista._rol_nuevo.set(Rol.ENFERMERO.value)
    escribir(vista._clave_nueva.clave, CLAVE)
    escribir(vista._clave_nueva.repetir, "otra")
    vista.crear_cuenta()
    assert marcado(vista._clave_nueva.repetir) and vista._clave_nueva.aviso.cget("text") == CLAVES_DISTINTAS
    vista.admin.crear_cuenta.assert_not_called()
    for campo in vista._clave_nueva.entradas:
        escribir(campo, "sinnumeros", soltar=vista._clave_nueva._editada)
    vista.crear_cuenta()
    assert marcado(vista._clave_nueva.clave) and "letras y números" in vista._clave_nueva.aviso.cget("text")
    assert vista._clave_nueva.aviso.winfo_manager() == "pack"
    vista.admin.crear_cuenta.assert_called_once()  # solo la segunda llegó al controlador (que la rechazó)
    assert vista.dialogos["error"] == []


def test_si_otra_pc_ya_le_creo_la_cuenta_se_avisa_y_se_recarga(crear):
    vista = crear()
    elegir(vista, vista._tabla_empleados, 7)
    vista._rol_nuevo.set(Rol.ENFERMERO.value)
    escribir(vista._clave_nueva.clave, CLAVE)
    escribir(vista._clave_nueva.repetir, CLAVE)
    vista.admin.crear_cuenta.side_effect = RegistroDuplicadoError("El empleado ya tiene una cuenta.")
    vista.crear_cuenta()
    assert [str(e) for e in vista.dialogos["error"]] == ["El empleado ya tiene una cuenta."]
    assert vista.admin.listar_cuentas.call_count == 2  # al abrir y al recargar


def test_crear_una_cuenta(crear):
    vista = crear()
    elegir(vista, vista._tabla_empleados, 7)
    vista._rol_nuevo.set(Rol.ENFERMERO.value)
    escribir(vista._clave_nueva.clave, CLAVE)
    escribir(vista._clave_nueva.repetir, CLAVE)
    vista.crear_cuenta()
    vista.admin.crear_cuenta.assert_called_once_with(7, Rol.ENFERMERO, CLAVE)
    assert fila_de(vista, "Carla Vega Torres")[2:] == (Rol.ENFERMERO.value, "Activa")
    assert vista._modo.texto("cuentas") == "Cuentas (7)" and vista._modo.texto("nueva") == "Nueva cuenta (1)"
    assert vista._clave_nueva.clave.get() == "" and vista._rol_nuevo.get() == ""
    assert vista.dialogos["info"][0].startswith("Cuenta creada para Carla Vega Torres")


# ---- Bitácora

def test_filtrar_la_bitacora_por_tabla_y_usuario(crear):
    vista = crear()
    vista._filtro_tabla.set("Usuario")
    vista.ver_bitacora()
    vista.admin.bitacora.assert_called_with(HOY, HOY, tabla="usuario", id_usuario=None, limite=LIMITE_BITACORA)
    assert [f[3] for f in filas(vista._tabla_bitacora)] == ["Usuario"]
    vista._filtro_tabla.set("Todas")
    vista._filtro_usuario.set("Rosa Díaz Vela")
    vista.ver_bitacora()
    assert {f[1] for f in filas(vista._tabla_bitacora)} == {"Rosa Díaz Vela"}


def test_lo_que_se_hace_en_la_pantalla_queda_en_la_bitacora(crear):
    vista = crear()
    elegir(vista, vista._tabla_cuentas, 2)
    vista.cambiar_acceso()
    vista.ver_bitacora()
    assert filas(vista._tabla_bitacora)[0][1:6] == ("Elena Ríos Paredes", "Cambio", "Usuario", "2", "activo: no")


def test_cambiar_de_opcion_relee_las_cuentas_y_la_bitacora(crear):
    vista = crear()
    vista.admin._mock_wraps.desactivar(2)  # lo hace otra PC
    vista._modo.elegir("nueva")
    vista._modo.elegir("cuentas")
    assert fila_de(vista, "Luis Ramos Díaz")[3] == "Desactivada"
    vista._modo.elegir("bitacora")
    assert filas(vista._tabla_bitacora)[0][4] == "2"


def test_al_abrir_pacientes_el_foco_va_al_documento(crear, monkeypatch):
    vista = crear()
    enfocados = []  # la ventana de pruebas está oculta y no recibe el foco: se anota el pedido, como en Pacientes
    monkeypatch.setattr(vista._documento, "enfocar", lambda: enfocados.append(True))
    vista._modo.elegir("pacientes")
    assert enfocados == [True]


def test_elegir_un_registro_muestra_su_detalle_completo(crear):
    vista = crear()
    elegir(vista, vista._tabla_bitacora, 4)
    assert vista._detalle_elegido.cget("text") == "Detalle: estado anterior: OCUPADA · estado nuevo: EN LIMPIEZA"
    assert vista._detalle_elegido.winfo_manager() == "pack"
    elegir(vista, vista._tabla_bitacora, 1)  # sin detalles: no ocupa lugar
    assert vista._detalle_elegido.cget("text") == "" and vista._detalle_elegido.winfo_manager() == ""


def test_un_periodo_rechazado_marca_las_dos_fechas(crear):  # valor límite: desde > hasta
    vista = crear()
    escribir(vista.periodo.desde, "05/11/2026", soltar=vista.periodo.fechas_editadas)
    vista.ver_bitacora()
    assert "posterior" in str(vista.dialogos["error"][0])
    assert marcado(vista.periodo.desde) and marcado(vista.periodo.hasta)


def test_al_llegar_al_tope_se_avisa(crear):
    admin = MagicMock(wraps=AdminDemo(ahora=lambda: AHORA))
    admin.bitacora.return_value = [
        {"id_bitacora": i, "id_usuario": 1, "tabla_afectada": "cama", "accion": AccionAuditoria.UPDATE,
         "id_registro_afectado": i, "fecha_hora": AHORA, "detalles": None} for i in range(LIMITE_BITACORA)]
    vista = crear(admin=admin)
    assert vista._resumen_bitacora.cget("text").startswith(
        f"El 04/11/2026: se muestran los {LIMITE_BITACORA} registros más recientes")


def test_un_atajo_consulta_la_bitacora(crear):
    vista = crear()
    vista.periodo.atajos.botones["semana"].invoke()
    vista.admin.bitacora.assert_called_with(date(2026, 10, 29), HOY, tabla=None, id_usuario=None,
                                            limite=LIMITE_BITACORA)


# ---- Pacientes

def buscar(vista, documento):
    vista._documento.fijar(*documento)
    return vista.buscar_paciente()


def test_buscar_muestra_solo_nombre_documento_y_estado(crear):
    vista = crear()
    assert buscar(vista, REGISTRADO) == "break"
    vista.pacientes.buscar_para_administrar.assert_called_once_with("DNI", "41234567")
    assert vista._nombre_paciente.cget("text") == "Carmen Rojas Llanos"
    assert vista._datos_paciente.cget("text") == "DNI 41234567 · Activo"
    assert vista._boton_paciente.cget("text") == "Dar de baja"
    assert vista._encontrado.winfo_manager() == "pack" and vista._aviso_paciente.winfo_manager() == ""


def test_dar_de_baja_y_reactivar(crear):
    vista = crear()
    buscar(vista, REGISTRADO)
    vista.cambiar_paciente()
    assert vista._datos_paciente.cget("text") == "DNI 41234567 · Dado de baja"
    assert vista._boton_paciente.cget("text") == "Reactivar"
    assert vista.dialogos["info"] == ["Carmen Rojas Llanos quedó dado de baja. Se puede reactivar desde aquí."]
    vista.cambiar_paciente()
    assert vista._datos_paciente.cget("text") == "DNI 41234567 · Activo"
    vista.ver_bitacora()
    assert [f[2] for f in filas(vista._tabla_bitacora)][:2] == ["Reactivación", "Baja"]


def test_un_paciente_con_episodio_abierto_no_se_da_de_baja(crear):
    vista = crear()
    buscar(vista, EN_COLA)
    vista.cambiar_paciente()
    assert "episodio abierto" in str(vista.dialogos["error"][0])
    assert vista._datos_paciente.cget("text").endswith("· Activo")


def test_no_encontrado_y_documento_mal_escrito(crear):
    vista = crear()
    buscar(vista, ("DNI", "12345678"))
    assert vista._aviso_paciente.cget("text") == NO_ENCONTRADO and vista._encontrado.winfo_manager() == ""
    buscar(vista, ("DNI", "123"))
    assert marcado(vista._documento.campo_numero) and vista.dialogos["error"] == []
    escribir(vista._documento.campo_numero, "1234", soltar=vista._documento_editado)
    assert not marcado(vista._documento.campo_numero) and vista._aviso_paciente.cget("text") == AVISO_BUSCAR


def test_cambiar_el_documento_retira_el_resultado(crear):
    vista = crear()
    buscar(vista, REGISTRADO)
    escribir(vista._documento.campo_numero, "4123456", soltar=vista._documento_editado)
    assert vista._paciente is None and vista._aviso_paciente.cget("text") == AVISO_BUSCAR


def test_si_la_bd_falla_al_buscar_no_es_culpa_del_documento(crear):
    vista = crear()
    vista.pacientes.buscar_para_administrar.side_effect = ConexionBDError("No hay conexión con la base de datos.")
    buscar(vista, REGISTRADO)
    assert len(vista.dialogos["error"]) == 1 and not marcado(vista._documento.campo_numero)


def test_si_la_bd_falla_al_dar_de_baja_hay_un_solo_aviso(crear):
    vista = crear()
    buscar(vista, REGISTRADO)
    error = ConexionBDError("No hay conexión con la base de datos.")
    vista.pacientes.dar_de_baja.side_effect = error
    vista.pacientes.buscar_para_administrar.side_effect = error  # tampoco se puede releer
    vista.cambiar_paciente()
    assert vista.dialogos["error"] == [error] and vista.dialogos["info"] == []


def test_un_documento_rechazado_y_luego_uno_valido_quita_el_rojo(crear):
    vista = crear()
    buscar(vista, ("DNI", "123"))
    buscar(vista, REGISTRADO)
    assert not marcado(vista._documento.campo_numero) and vista._paciente is not None
    vista._documento_editado()  # soltar el Enter que buscó: el resultado sigue
    assert vista._paciente is not None


def test_cambiar_el_tipo_retira_el_resultado(crear):
    vista = crear()
    buscar(vista, REGISTRADO)
    mover_opcion(vista._documento._tipo, 1)  # otro tipo con el mismo número es otro documento
    assert vista._paciente is None and vista._encontrado.winfo_manager() == ""


def test_tras_la_baja_se_relee_el_documento_buscado(crear):
    vista = crear()
    buscar(vista, REGISTRADO)
    vista.cambiar_paciente()
    vista.pacientes.buscar_para_administrar.assert_called_with("DNI", "41234567")
    assert vista._boton_paciente.cget("text") == "Reactivar"
