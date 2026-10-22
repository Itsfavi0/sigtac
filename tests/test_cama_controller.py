from datetime import datetime

import pytest

from controllers import cama_controller
from controllers.cama_controller import CamaController
from models.asignacion import AsignacionCama, SolicitudLimpieza
from models.auditoria import AccionAuditoria
from models.cama import CamaObservacion, CamaTraumaShock, CamaUCI
from models.estados import EstadoCama, EstadoEpisodio
from models.excepciones import (CamaEstadoInvalidoError, CamaNoDisponibleError, ReglaNegocioError,
                                UsuarioSinPermisoError)
from models.permisos import Rol
from models.triaje import EpisodioEmergencia, Triaje

AHORA = datetime(2026, 10, 22, 9, 0)


def episodio(estado=EstadoEpisodio.EN_ESPERA, nivel=2, activo=True):
    triajes = (Triaje(1, nivel, 20, AHORA),) if nivel else ()
    return EpisodioEmergencia(7, 1, "Disnea", estado=estado, fecha_ingreso=AHORA, activo=activo, triajes=triajes)


def uci(estado=EstadoCama.DISPONIBLE):
    return CamaUCI(3, "UCI-01", "UCI", estado)


ASIGNACION = AsignacionCama(5, 7, 3, 20, AHORA)


@pytest.fixture
def datos(capa_datos):
    return capa_datos(cama_controller, "CamaDAO", "EpisodioDAO", "AsignacionDAO", "SolicitudLimpiezaDAO",
                      "AuditoriaDAO")


@pytest.fixture
def ctrl(sesion_de):
    return CamaController(sesion_de(Rol.MEDICO))


@pytest.fixture
def limpieza(sesion_de):
    return CamaController(sesion_de(Rol.LIMPIEZA, id_usuario=4, id_empleado=4))


# ---- Permisos

GESTION = [("camas_compatibles", (7,)), ("asignar", (7, 3)), ("ocupar", (3,)),
           ("cancelar_asignacion", (7,)), ("dar_alta", (7,))]
LIMPIEZA = [("solicitudes_limpieza", ()), ("confirmar_limpieza", (1,))]


@pytest.mark.parametrize("metodo, args", GESTION)
@pytest.mark.parametrize("rol", [Rol.ENFERMERO, Rol.LIMPIEZA, Rol.ADMINISTRADOR])
def test_solo_medico_y_jefe_gestionan_camas(datos, sesion_de, metodo, args, rol):
    with pytest.raises(UsuarioSinPermisoError):
        getattr(CamaController(sesion_de(rol)), metodo)(*args)
    assert datos.llamadas() == []


@pytest.mark.parametrize("metodo, args", LIMPIEZA)
@pytest.mark.parametrize("rol", [Rol.MEDICO, Rol.JEFE_GUARDIA, Rol.ENFERMERO])
def test_solo_limpieza_confirma_la_limpieza(datos, sesion_de, metodo, args, rol):  # RN-08
    with pytest.raises(UsuarioSinPermisoError):
        getattr(CamaController(sesion_de(rol)), metodo)(*args)
    assert datos.llamadas() == []


@pytest.mark.parametrize("rol", list(Rol))
def test_todos_ven_el_mapa_de_camas(datos, sesion_de, rol):
    datos["CamaDAO"].listar_activas.return_value = [uci()]
    assert CamaController(sesion_de(rol)).mapa_camas()[0].codigo == "UCI-01"


# ---- Consultas

def test_cola_de_espera_es_la_de_episodios_con_triaje(monkeypatch, sesion_de):
    pedidos = []
    monkeypatch.setattr(cama_controller, "armar_cola", lambda estado: pedidos.append(estado) or ["cola"])
    assert CamaController(sesion_de(Rol.ENFERMERO)).cola_de_espera() == ["cola"]
    assert pedidos == [EstadoEpisodio.EN_ESPERA]


def test_camas_compatibles_con_el_nivel_del_triaje(datos, ctrl):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(nivel=2)
    datos["CamaDAO"].listar_disponibles.return_value = [
        CamaTraumaShock(1, "TRA-02", "Trauma", EstadoCama.DISPONIBLE), uci(),
        CamaObservacion(6, "OBS-01", "Obs", EstadoCama.DISPONIBLE),
    ]
    assert [c.codigo for c in ctrl.camas_compatibles(7)] == ["UCI-01", "OBS-01"]


def test_camas_compatibles_sin_triaje(datos, ctrl):  # RN-01
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(EstadoEpisodio.EN_ESPERA_TRIAJE, nivel=None)
    with pytest.raises(ReglaNegocioError, match="RN-01"):
        ctrl.camas_compatibles(7)
    datos["CamaDAO"].listar_disponibles.assert_not_called()


@pytest.mark.parametrize("encontrado", [None, episodio(activo=False)])
def test_episodio_inexistente_o_anulado(datos, ctrl, encontrado):
    datos["EpisodioDAO"].buscar_por_id.return_value = encontrado
    with pytest.raises(ReglaNegocioError, match="no existe"):
        ctrl.camas_compatibles(7)


# ---- Asignar

def test_asignar_reserva_la_cama_y_audita(datos, ctrl):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio()
    datos["CamaDAO"].buscar_por_id.return_value = uci()
    datos["AsignacionDAO"].crear.return_value = 5
    assert ctrl.asignar(7, 3) == 5
    assert datos.llamadas() == [
        "inicio", "EpisodioDAO.buscar_por_id", "CamaDAO.buscar_por_id", "EpisodioDAO.cambiar_estado",
        "CamaDAO.cambiar_estado", "AsignacionDAO.crear", "AuditoriaDAO.registrar", "commit",
    ]
    ep, anterior_ep = datos["EpisodioDAO"].cambiar_estado.call_args.args
    cama, anterior_cama = datos["CamaDAO"].cambiar_estado.call_args.args
    assert (ep.estado, anterior_ep) == (EstadoEpisodio.EN_ATENCION, EstadoEpisodio.EN_ESPERA)
    assert (cama.estado, anterior_cama) == (EstadoCama.RESERVADA, EstadoCama.DISPONIBLE)
    datos["AsignacionDAO"].crear.assert_called_once_with(7, 3, 20)
    assert datos.auditoria().args == (10, "asignacion_cama", AccionAuditoria.INSERT, 5,
                                      {"id_episodio": 7, "id_cama": 3, "nivel": 2})


@pytest.mark.parametrize("ep, mensaje", [
    (episodio(EstadoEpisodio.EN_ESPERA_TRIAJE, nivel=None), "estado"),
    (episodio(EstadoEpisodio.EN_ATENCION), "estado"),
    (episodio(EstadoEpisodio.ALTA), "estado"),
])
def test_asignar_a_un_episodio_que_no_espera_cama(datos, ctrl, ep, mensaje):  # RN-01
    datos["EpisodioDAO"].buscar_por_id.return_value = ep
    datos["CamaDAO"].buscar_por_id.return_value = uci()
    with pytest.raises(ReglaNegocioError, match=mensaje):
        ctrl.asignar(7, 3)
    assert datos.escrituras() == [] and datos.llamadas()[-1] == "rollback"


def test_asignar_sin_triaje_activo(datos, ctrl):  # RN-01
    sin_triaje = episodio(nivel=3)
    sin_triaje.triajes[0].anular()
    datos["EpisodioDAO"].buscar_por_id.return_value = sin_triaje
    datos["CamaDAO"].buscar_por_id.return_value = uci()
    with pytest.raises(ReglaNegocioError, match="RN-01"):
        ctrl.asignar(7, 3)
    assert datos.escrituras() == []


def test_asignar_una_cama_incompatible_con_el_nivel(datos, ctrl):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(nivel=2)
    datos["CamaDAO"].buscar_por_id.return_value = CamaTraumaShock(2, "TRA-02", "Trauma", EstadoCama.DISPONIBLE)
    with pytest.raises(ReglaNegocioError, match="no es compatible"):
        ctrl.asignar(7, 2)
    assert datos.escrituras() == []


@pytest.mark.parametrize("estado", [EstadoCama.RESERVADA, EstadoCama.OCUPADA, EstadoCama.EN_LIMPIEZA,
                                    EstadoCama.FUERA_SERVICIO])
def test_asignar_una_cama_no_disponible(datos, ctrl, estado):  # RN-05
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio()
    datos["CamaDAO"].buscar_por_id.return_value = uci(estado)
    with pytest.raises(CamaEstadoInvalidoError):
        ctrl.asignar(7, 3)
    assert datos.escrituras() == []


def test_asignar_una_cama_inexistente(datos, ctrl):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio()
    datos["CamaDAO"].buscar_por_id.return_value = None
    with pytest.raises(CamaNoDisponibleError):
        ctrl.asignar(7, 99)


def test_si_otra_pc_tomo_la_cama_se_deshace_todo(datos, ctrl):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio()
    datos["CamaDAO"].buscar_por_id.return_value = uci()
    datos["CamaDAO"].cambiar_estado.side_effect = CamaNoDisponibleError("otro usuario la cambió")
    with pytest.raises(CamaNoDisponibleError):
        ctrl.asignar(7, 3)
    datos["AsignacionDAO"].crear.assert_not_called()
    datos["AuditoriaDAO"].registrar.assert_not_called()
    assert datos.llamadas()[-1] == "rollback"  # también se deshace el cambio de estado del episodio


# ---- Ocupar

def test_ocupar_una_cama_reservada(datos, ctrl):
    datos["CamaDAO"].buscar_por_id.return_value = uci(EstadoCama.RESERVADA)
    datos["AsignacionDAO"].buscar_vigente_por_cama.return_value = ASIGNACION
    ctrl.ocupar(3)
    cama, anterior = datos["CamaDAO"].cambiar_estado.call_args.args
    assert (cama.estado, anterior) == (EstadoCama.OCUPADA, EstadoCama.RESERVADA)
    assert datos.auditoria().args == (10, "cama", AccionAuditoria.UPDATE, 3,
                                      {"estado_anterior": "RESERVADA", "estado_nuevo": "OCUPADA"})
    assert datos.llamadas()[-1] == "commit"


def test_ocupar_sin_asignacion_vigente(datos, ctrl):
    datos["CamaDAO"].buscar_por_id.return_value = uci()
    datos["AsignacionDAO"].buscar_vigente_por_cama.return_value = None
    with pytest.raises(ReglaNegocioError, match="asignación vigente"):
        ctrl.ocupar(3)
    assert datos.escrituras() == []


def test_ocupar_una_cama_ya_ocupada(datos, ctrl):
    datos["CamaDAO"].buscar_por_id.return_value = uci(EstadoCama.OCUPADA)
    datos["AsignacionDAO"].buscar_vigente_por_cama.return_value = ASIGNACION
    with pytest.raises(CamaEstadoInvalidoError):
        ctrl.ocupar(3)


# ---- Cancelar asignación

def test_cancelar_una_reserva(datos, ctrl):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(EstadoEpisodio.EN_ATENCION)
    datos["AsignacionDAO"].buscar_vigente_por_episodio.return_value = ASIGNACION
    datos["CamaDAO"].buscar_por_id.return_value = uci(EstadoCama.RESERVADA)
    ctrl.cancelar_asignacion(7)
    assert datos.escrituras() == ["EpisodioDAO.cambiar_estado", "CamaDAO.cambiar_estado", "AsignacionDAO.anular",
                                  "AuditoriaDAO.registrar"]
    ep, _ = datos["EpisodioDAO"].cambiar_estado.call_args.args
    cama, _ = datos["CamaDAO"].cambiar_estado.call_args.args
    assert (ep.estado, cama.estado) == (EstadoEpisodio.EN_ESPERA, EstadoCama.DISPONIBLE)  # sin limpieza
    datos["AsignacionDAO"].anular.assert_called_once_with(5)
    assert datos.auditoria().args[:4] == (10, "asignacion_cama", AccionAuditoria.ANULAR, 5)


def test_no_se_cancela_una_cama_ya_ocupada(datos, ctrl):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(EstadoEpisodio.EN_ATENCION)
    datos["AsignacionDAO"].buscar_vigente_por_episodio.return_value = ASIGNACION
    datos["CamaDAO"].buscar_por_id.return_value = uci(EstadoCama.OCUPADA)
    with pytest.raises(CamaEstadoInvalidoError, match="no está reservada"):
        ctrl.cancelar_asignacion(7)
    assert datos.escrituras() == []


@pytest.mark.parametrize("metodo", ["cancelar_asignacion", "dar_alta"])
def test_sin_cama_asignada(datos, ctrl, metodo):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(EstadoEpisodio.EN_ATENCION)
    datos["AsignacionDAO"].buscar_vigente_por_episodio.return_value = None
    with pytest.raises(ReglaNegocioError, match="no tiene una cama"):
        getattr(ctrl, metodo)(7)


# ---- Dar de alta

def test_dar_alta_libera_la_cama_y_pide_limpieza(datos, ctrl):  # RN-07
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(EstadoEpisodio.EN_ATENCION)
    datos["AsignacionDAO"].buscar_vigente_por_episodio.return_value = ASIGNACION
    datos["CamaDAO"].buscar_por_id.return_value = uci(EstadoCama.OCUPADA)
    datos["SolicitudLimpiezaDAO"].crear.return_value = 12
    assert ctrl.dar_alta(7) == 12
    assert datos.escrituras() == ["EpisodioDAO.cambiar_estado", "CamaDAO.cambiar_estado", "AsignacionDAO.liberar",
                                  "SolicitudLimpiezaDAO.crear", "AuditoriaDAO.registrar"]
    ep, _ = datos["EpisodioDAO"].cambiar_estado.call_args.args
    cama, anterior = datos["CamaDAO"].cambiar_estado.call_args.args
    assert ep.estado == EstadoEpisodio.ALTA
    assert (cama.estado, anterior) == (EstadoCama.EN_LIMPIEZA, EstadoCama.OCUPADA)
    datos["AsignacionDAO"].liberar.assert_called_once_with(5)
    datos["SolicitudLimpiezaDAO"].crear.assert_called_once_with(3)
    assert datos.auditoria().args == (10, "episodio_emergencia", AccionAuditoria.UPDATE, 7, {
        "estado_anterior": "EN ATENCIÓN (CON CAMA)", "estado_nuevo": "ALTA MÉDICA",
        "id_cama": 3, "id_solicitud_limpieza": 12,
    })


def test_no_se_da_alta_si_el_paciente_no_llego_a_la_cama(datos, ctrl):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(EstadoEpisodio.EN_ATENCION)
    datos["AsignacionDAO"].buscar_vigente_por_episodio.return_value = ASIGNACION
    datos["CamaDAO"].buscar_por_id.return_value = uci(EstadoCama.RESERVADA)
    with pytest.raises(CamaEstadoInvalidoError, match="no está ocupada"):
        ctrl.dar_alta(7)
    assert datos.escrituras() == [] and datos.llamadas()[-1] == "rollback"


# ---- Limpieza

def test_bandeja_de_limpieza(datos, limpieza):
    datos["SolicitudLimpiezaDAO"].listar_pendientes.return_value = ["solicitud"]
    assert limpieza.solicitudes_limpieza() == ["solicitud"]


def test_confirmar_limpieza_devuelve_la_cama_a_disponible(datos, limpieza):  # RN-08
    datos["SolicitudLimpiezaDAO"].buscar_por_id.return_value = SolicitudLimpieza(1, 3, "UCI-01", AHORA)
    datos["CamaDAO"].buscar_por_id.return_value = uci(EstadoCama.EN_LIMPIEZA)
    limpieza.confirmar_limpieza(1)
    datos["SolicitudLimpiezaDAO"].atender.assert_called_once_with(1, 4)
    cama, anterior = datos["CamaDAO"].cambiar_estado.call_args.args
    assert (cama.estado, anterior) == (EstadoCama.DISPONIBLE, EstadoCama.EN_LIMPIEZA)
    assert datos.auditoria().args == (4, "solicitud_limpieza", AccionAuditoria.UPDATE, 1, {"id_cama": 3})
    assert datos.llamadas()[-1] == "commit"


@pytest.mark.parametrize("solicitud, mensaje", [
    (None, "no existe"),
    (SolicitudLimpieza(1, 3, "UCI-01", AHORA, id_empleado=4, fecha_atencion=AHORA), "ya fue atendida"),
])
def test_confirmar_una_solicitud_inexistente_o_atendida(datos, limpieza, solicitud, mensaje):
    datos["SolicitudLimpiezaDAO"].buscar_por_id.return_value = solicitud
    with pytest.raises(ReglaNegocioError, match=mensaje):
        limpieza.confirmar_limpieza(1)
    assert datos.escrituras() == []


def test_confirmar_limpieza_de_una_cama_que_no_esta_en_limpieza(datos, limpieza):
    datos["SolicitudLimpiezaDAO"].buscar_por_id.return_value = SolicitudLimpieza(1, 3, "UCI-01", AHORA)
    datos["CamaDAO"].buscar_por_id.return_value = uci(EstadoCama.DISPONIBLE)
    with pytest.raises(CamaEstadoInvalidoError):
        limpieza.confirmar_limpieza(1)
    datos["SolicitudLimpiezaDAO"].atender.assert_not_called()
