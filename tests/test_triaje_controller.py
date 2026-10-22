from datetime import datetime

import pytest

from controllers import triaje_controller
from controllers.triaje_controller import Sugerencia, TriajeController
from models.auditoria import AccionAuditoria
from models.estados import EstadoEpisodio
from models.estrategias import EstrategiaTriaje, ReglaManchester, ReglaMINSA
from models.excepciones import (NivelTriajeInvalidoError, PersistenciaError, ReglaNegocioError,
                                SignosVitalesIncompletosError, UsuarioSinPermisoError)
from models.permisos import Rol
from models.triaje import EpisodioEmergencia, Sintoma, Triaje

AHORA = datetime(2026, 10, 22, 9, 0)
SIGNOS = {"pa_sis": 120, "pa_dia": 80, "fc": 85, "fr": 18, "temp": 37.0, "sato2": 97}
TORACICO = Sintoma(2, "Dolor Torácico Opresivo", 8.5)
TOS = Sintoma(10, "Tos Leve", 0.5)
JUSTIFICACION = "Antecedente de infarto hace un mes; se prioriza."


class EstrategiaFija(EstrategiaTriaje):
    """Estrategia de prueba: siempre sugiere el mismo nivel."""

    def __init__(self, nivel=3):
        self.nivel = nivel

    def clasificar(self, signos_vitales, sintomas):
        return self.nivel

    def justificar(self):
        return "Protocolo de prueba."


def episodio(estado=EstadoEpisodio.EN_ESPERA_TRIAJE, con_triaje=False):
    triajes = (Triaje(1, 4, 20, AHORA),) if con_triaje else ()
    return EpisodioEmergencia(7, 1, "Dolor torácico", estado=estado, fecha_ingreso=AHORA, triajes=triajes)


@pytest.fixture
def datos(capa_datos):
    d = capa_datos(triaje_controller, "EpisodioDAO", "TriajeDAO", "AuditoriaDAO")
    d["TriajeDAO"].listar_sintomas.return_value = [TORACICO, TOS]
    d["TriajeDAO"].registrar.return_value = 40
    d["EpisodioDAO"].bloquear.return_value = True
    d["EpisodioDAO"].buscar_por_id.return_value = episodio()
    return d


@pytest.fixture
def ctrl(sesion_de):
    return TriajeController(sesion_de(Rol.ENFERMERO), EstrategiaFija(3))


def triaje_guardado(datos) -> Triaje:
    id_episodio, _, triaje = datos["TriajeDAO"].registrar.call_args.args
    assert id_episodio == 7
    return triaje


# ---- Construcción y permisos

def test_la_estrategia_por_defecto_es_manchester(sesion_de):
    assert isinstance(TriajeController(sesion_de())._estrategia, ReglaManchester)


@pytest.mark.parametrize("estrategia", ["Manchester", ReglaMINSA, object()])
def test_la_estrategia_debe_ser_una_estrategia_de_triaje(sesion_de, estrategia):
    with pytest.raises(ValueError, match="EstrategiaTriaje"):
        TriajeController(sesion_de(), estrategia)


OPERACIONES = [
    ("listar_sintomas", ()),
    ("cola_de_triaje", ()),
    ("sugerir", (SIGNOS, [2])),
    ("registrar", (7, SIGNOS, [2])),
]


@pytest.mark.parametrize("metodo, args", OPERACIONES)
@pytest.mark.parametrize("rol", [Rol.LIMPIEZA, Rol.ADMINISTRADOR])
def test_sin_permiso_de_triaje_no_se_toca_la_bd(datos, sesion_de, monkeypatch, metodo, args, rol):
    monkeypatch.setattr(triaje_controller, "armar_cola", lambda estado: pytest.fail("no debe consultar"))
    with pytest.raises(UsuarioSinPermisoError):
        getattr(TriajeController(sesion_de(rol), EstrategiaFija()), metodo)(*args)
    assert datos.llamadas() == []


# ---- Consultas

def test_listar_sintomas(datos, ctrl):
    assert ctrl.listar_sintomas() == [TORACICO, TOS]


def test_cola_de_triaje_es_la_de_episodios_sin_triaje(monkeypatch, ctrl):
    pedidos = []
    monkeypatch.setattr(triaje_controller, "armar_cola", lambda estado: pedidos.append(estado) or ["cola"])
    assert ctrl.cola_de_triaje() == ["cola"]
    assert pedidos == [EstadoEpisodio.EN_ESPERA_TRIAJE]


def test_sugerir_usa_la_estrategia_y_no_guarda_nada(datos, sesion_de):
    ctrl = TriajeController(sesion_de(Rol.ENFERMERO), ReglaManchester())
    sugerencia = ctrl.sugerir(SIGNOS, [2])  # dolor torácico (8.5) → Manchester nivel 2
    assert sugerencia == Sugerencia(2, ReglaManchester().justificar())
    assert datos.llamadas() == ["TriajeDAO.listar_sintomas"]


def test_sugerir_sin_sintomas_no_consulta_el_catalogo(datos, ctrl):
    assert ctrl.sugerir(SIGNOS, []).nivel == 3
    assert datos.llamadas() == []


# ---- Validación de los datos del formulario (antes de tocar la BD)

@pytest.mark.parametrize("signos, error, mensaje", [
    ({k: v for k, v in SIGNOS.items() if k != "sato2"}, SignosVitalesIncompletosError, "sato2"),
    (SIGNOS | {"fc": None}, SignosVitalesIncompletosError, "fc"),
    (SIGNOS | {"glucosa": 90}, ValueError, "glucosa"),
    (SIGNOS | {"fc": "85"}, ValueError, "fc debe ser un número"),
    (SIGNOS | {"pa_sis": 70, "pa_dia": 80}, ValueError, "sistólica"),
    ([120, 80], ValueError, "diccionario"),
])
def test_signos_invalidos(datos, ctrl, signos, error, mensaje):
    with pytest.raises(error, match=mensaje):
        ctrl.registrar(7, signos, [])
    assert datos.llamadas() == []


@pytest.mark.parametrize("ids, mensaje", [([2, 2], "repetidos"), ([2, 99], "no reconocido")])
def test_sintomas_invalidos(datos, ctrl, ids, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        ctrl.registrar(7, SIGNOS, ids)
    assert datos.escrituras() == [] and "inicio" not in datos.llamadas()


# ---- Registrar

def test_primer_triaje_pasa_el_episodio_a_espera_de_cama(datos, ctrl):
    assert ctrl.registrar(7, SIGNOS, [2, 10]) == 40
    assert datos.llamadas() == [
        "TriajeDAO.listar_sintomas", "inicio", "EpisodioDAO.bloquear", "EpisodioDAO.buscar_por_id",
        "TriajeDAO.registrar", "EpisodioDAO.cambiar_estado", "AuditoriaDAO.registrar", "commit",
    ]
    triaje = triaje_guardado(datos)
    assert (triaje.nivel_sugerido, triaje.nivel_final, triaje.id_empleado) == (3, 3, 20)
    assert [s.id_sintoma for s in triaje.sintomas] == [2, 10] and triaje.justificacion is None
    guardado, anterior = datos["EpisodioDAO"].cambiar_estado.call_args.args
    assert (guardado.estado, anterior) == (EstadoEpisodio.EN_ESPERA, EstadoEpisodio.EN_ESPERA_TRIAJE)
    assert datos.auditoria().args == (10, "triaje", AccionAuditoria.INSERT, 40, {
        "id_episodio": 7, "nivel_sugerido": 3, "nivel_final": 3, "reclasificado": False,
        "protocolo": "EstrategiaFija",
    })


@pytest.mark.parametrize("estado", [EstadoEpisodio.EN_ESPERA, EstadoEpisodio.EN_ATENCION])
def test_una_reevaluacion_no_cambia_el_estado(datos, ctrl, estado):  # RN-09
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(estado, con_triaje=True)
    ctrl.registrar(7, SIGNOS, [])
    datos["EpisodioDAO"].cambiar_estado.assert_not_called()
    assert datos.llamadas()[-1] == "commit"


def test_reclasificar_con_justificacion(datos, ctrl):  # RN-10
    ctrl.registrar(7, SIGNOS, [2], nivel_final=1, justificacion=JUSTIFICACION)
    triaje = triaje_guardado(datos)
    assert (triaje.nivel_sugerido, triaje.nivel_final, triaje.justificacion) == (3, 1, JUSTIFICACION)
    detalles = datos.auditoria().args[4]
    assert detalles["reclasificado"] is True and detalles["nivel_final"] == 1
    assert JUSTIFICACION not in str(detalles)  # el texto clínico no va a la bitácora


@pytest.mark.parametrize("justificacion", [None, "", "corto"])
def test_reclasificar_sin_justificacion_suficiente_no_toca_la_bd(datos, ctrl, justificacion):
    with pytest.raises(ValueError, match="justificación"):
        ctrl.registrar(7, SIGNOS, [], nivel_final=1, justificacion=justificacion)
    assert datos.llamadas() == []


def test_confirmar_el_mismo_nivel_no_es_reclasificacion(datos, ctrl):
    ctrl.registrar(7, SIGNOS, [], nivel_final=3, justificacion=JUSTIFICACION)
    triaje = triaje_guardado(datos)
    assert not triaje.es_reclasificacion and triaje.justificacion is None


@pytest.mark.parametrize("nivel", [0, 6, "2"])
def test_reclasificar_a_un_nivel_invalido(datos, ctrl, nivel):
    with pytest.raises(NivelTriajeInvalidoError):
        ctrl.registrar(7, SIGNOS, [], nivel_final=nivel, justificacion=JUSTIFICACION)
    assert datos.llamadas() == []


def test_episodio_inexistente_o_anulado(datos, ctrl):
    datos["EpisodioDAO"].bloquear.return_value = False
    with pytest.raises(ReglaNegocioError, match="no existe"):
        ctrl.registrar(7, SIGNOS, [])
    datos["TriajeDAO"].registrar.assert_not_called()
    assert datos.llamadas()[-1] == "rollback"


@pytest.mark.parametrize("estado", [EstadoEpisodio.ALTA, EstadoEpisodio.REFERIDO, EstadoEpisodio.FUGADO])
def test_un_episodio_cerrado_no_admite_triajes(datos, ctrl, estado):
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(estado, con_triaje=True)
    with pytest.raises(ReglaNegocioError):
        ctrl.registrar(7, SIGNOS, [])
    assert datos.escrituras() == [] and datos.llamadas()[-1] == "rollback"


def test_si_falla_la_bd_se_deshace_y_no_se_audita(datos, ctrl):
    datos["TriajeDAO"].registrar.side_effect = PersistenciaError("No se pudo completar la operación.")
    with pytest.raises(PersistenciaError):
        ctrl.registrar(7, SIGNOS, [])
    datos["AuditoriaDAO"].registrar.assert_not_called()
    assert datos.llamadas()[-1] == "rollback"


def test_la_auditoria_registra_el_protocolo_usado(datos, sesion_de):
    TriajeController(sesion_de(Rol.MEDICO), ReglaMINSA()).registrar(7, SIGNOS, [])
    assert datos.auditoria().args[4]["protocolo"] == "ReglaMINSA"
