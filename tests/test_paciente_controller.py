from datetime import date

import pytest

from controllers import paciente_controller
from controllers.paciente_controller import PacienteController
from models.auditoria import AccionAuditoria
from models.documento import DocumentoIdentidad
from models.estados import EstadoEpisodio
from models.excepciones import RegistroDuplicadoError, ReglaNegocioError, UsuarioSinPermisoError
from models.permisos import Rol
from models.persona import Paciente
from models.triaje import EpisodioEmergencia

DNI = "70123456"
NACIMIENTO = date(1959, 5, 14)


def rosa(id_paciente=1, activo=True):
    return Paciente(id_paciente, DocumentoIdentidad("DNI", DNI), "Rosa", "Mendoza Flores", NACIMIENTO, "F", 1,
                    activo=activo, nombre_seguro="EsSalud")


def nn(id_paciente=5):
    p = Paciente.no_identificado("M", 45, 4)
    return Paciente(id_paciente, None, p.nombres, p.apellidos, p.fecha_nac, p.sexo, p.id_seguro)


def episodio(id_episodio=1, id_paciente=1, estado=EstadoEpisodio.EN_ESPERA_TRIAJE):
    return EpisodioEmergencia(id_episodio, id_paciente, "Dolor torácico", estado=estado)


@pytest.fixture
def datos(capa_datos):
    return capa_datos(paciente_controller, "PacienteDAO", "EpisodioDAO", "AuditoriaDAO")


@pytest.fixture
def ctrl(sesion_de):
    return PacienteController(sesion_de(Rol.ENFERMERO))


# ---- Permisos

OPERACIONES = [
    ("listar_seguros", ()),
    ("buscar_por_documento", ("DNI", DNI)),
    ("listar_no_identificados", ()),
    ("registrar", ("DNI", DNI, "Rosa", "Mendoza", NACIMIENTO, "F", 1)),
    ("registrar_no_identificado", ("M", 40, 4)),
    ("abrir_episodio", (1, "Dolor torácico")),
    ("identificar", (5, "DNI", DNI, "Rosa", "Mendoza", NACIMIENTO)),
    ("fusionar", (5, 1)),
]


@pytest.mark.parametrize("metodo, args", OPERACIONES)
@pytest.mark.parametrize("rol", [Rol.LIMPIEZA, Rol.ADMINISTRADOR])
def test_sin_permiso_de_pacientes_no_se_toca_la_bd(datos, sesion_de, metodo, args, rol):
    with pytest.raises(UsuarioSinPermisoError):
        getattr(PacienteController(sesion_de(rol)), metodo)(*args)
    assert datos.llamadas() == []


@pytest.mark.parametrize("metodo, args", OPERACIONES)
def test_con_la_sesion_cerrada_no_se_opera(datos, sesion_de, metodo, args):
    sesion = sesion_de(Rol.JEFE_GUARDIA)
    ctrl = PacienteController(sesion)
    sesion.cerrar()
    with pytest.raises(UsuarioSinPermisoError, match="sesión activa"):
        getattr(ctrl, metodo)(*args)
    assert datos.llamadas() == []


# ---- Consultas

def test_consultas(datos, ctrl):
    datos["PacienteDAO"].listar_seguros.return_value = [{"id_seguro": 1, "nombre_seguro": "EsSalud"}]
    datos["PacienteDAO"].buscar_por_documento.return_value = rosa()
    datos["PacienteDAO"].listar_no_identificados.return_value = [nn()]
    assert ctrl.listar_seguros()[0]["id_seguro"] == 1
    assert ctrl.buscar_por_documento("DNI", " 70123456 ").nombres == "Rosa"
    datos["PacienteDAO"].buscar_por_documento.assert_called_once_with(DocumentoIdentidad("DNI", DNI))
    assert not ctrl.listar_no_identificados()[0].identificado


def test_buscar_con_documento_invalido_no_consulta(datos, ctrl):
    with pytest.raises(ValueError):
        ctrl.buscar_por_documento("DNI", "123")
    assert datos.llamadas() == []


# ---- Registrar

def test_registrar_crea_y_audita_dentro_de_la_transaccion(datos, ctrl):
    datos["PacienteDAO"].buscar_por_documento.return_value = None
    datos["PacienteDAO"].crear.return_value = 7
    datos["PacienteDAO"].buscar_por_id.return_value = rosa(7)
    resultado = ctrl.registrar("DNI", DNI, "Rosa", "Mendoza Flores", NACIMIENTO, "F", 1)
    assert resultado.id_paciente == 7 and resultado.nombre_seguro == "EsSalud"
    assert datos.llamadas() == ["inicio", "PacienteDAO.buscar_por_documento", "PacienteDAO.crear",
                                "AuditoriaDAO.registrar", "PacienteDAO.buscar_por_id", "commit"]
    assert datos.auditoria().args == (10, "paciente", AccionAuditoria.INSERT, 7)
    creado = datos["PacienteDAO"].crear.call_args.args[0]
    assert creado.id_paciente is None and creado.documento == DocumentoIdentidad("DNI", DNI)


@pytest.mark.parametrize("existente, mensaje", [(rosa(), "Ya existe"), (rosa(activo=False), "dado de baja")])
def test_registrar_un_documento_existente(datos, ctrl, existente, mensaje):
    datos["PacienteDAO"].buscar_por_documento.return_value = existente
    with pytest.raises(ReglaNegocioError, match=mensaje):
        ctrl.registrar("DNI", DNI, "Rosa", "Mendoza Flores", NACIMIENTO, "F", 1)
    assert datos.escrituras() == []
    assert datos.llamadas()[-1] == "rollback"


@pytest.mark.parametrize("cambio", [{"sexo": "X"}, {"nombres": "  "}, {"num_documento": "12"}, {"id_seguro": None}])
def test_registrar_datos_invalidos_no_toca_la_bd(datos, ctrl, cambio):
    args = {"tipo_documento": "DNI", "num_documento": DNI, "nombres": "Rosa", "apellidos": "Mendoza",
            "fecha_nac": NACIMIENTO, "sexo": "F", "id_seguro": 1} | cambio
    with pytest.raises(ValueError):
        ctrl.registrar(**args)
    assert datos.llamadas() == []


def test_si_otra_pc_registra_el_mismo_documento_se_deshace_todo(datos, ctrl):
    datos["PacienteDAO"].buscar_por_documento.return_value = None
    datos["PacienteDAO"].crear.side_effect = RegistroDuplicadoError("Ya existe un registro con esos datos.")
    with pytest.raises(RegistroDuplicadoError):
        ctrl.registrar("DNI", DNI, "Rosa", "Mendoza Flores", NACIMIENTO, "F", 1)
    assert datos.llamadas()[-1] == "rollback"
    datos["AuditoriaDAO"].registrar.assert_not_called()


def test_registrar_no_identificado(datos, ctrl):
    datos["PacienteDAO"].crear.return_value = 8
    datos["PacienteDAO"].buscar_por_id.return_value = nn(8)
    assert ctrl.registrar_no_identificado("M", 45, 4).id_paciente == 8
    creado = datos["PacienteDAO"].crear.call_args.args[0]
    assert not creado.identificado and creado.nombres == Paciente.NOMBRE_NO_IDENTIFICADO
    assert datos.auditoria().args == (10, "paciente", AccionAuditoria.INSERT, 8)
    assert datos.llamadas()[0] == "inicio" and datos.llamadas()[-1] == "commit"


def test_registrar_no_identificado_con_edad_invalida(datos, ctrl):
    with pytest.raises(ValueError, match="edad"):
        ctrl.registrar_no_identificado("M", 200, 4)
    assert datos.llamadas() == []


# ---- Abrir episodio

def test_abrir_episodio_bloquea_al_paciente_y_audita(datos, ctrl):
    datos["PacienteDAO"].bloquear.return_value = True
    datos["EpisodioDAO"].listar_por_paciente.return_value = [episodio(3, estado=EstadoEpisodio.ALTA)]
    datos["EpisodioDAO"].crear.return_value = 9
    datos["EpisodioDAO"].buscar_por_id.return_value = episodio(9)
    assert ctrl.abrir_episodio(1, "Dolor torácico").id_episodio == 9
    assert datos.llamadas() == ["inicio", "PacienteDAO.bloquear", "EpisodioDAO.listar_por_paciente",
                                "EpisodioDAO.crear", "AuditoriaDAO.registrar", "EpisodioDAO.buscar_por_id", "commit"]
    nuevo = datos["EpisodioDAO"].crear.call_args.args[0]
    assert (nuevo.id_paciente, nuevo.estado) == (1, EstadoEpisodio.EN_ESPERA_TRIAJE)
    assert datos.auditoria().args == (10, "episodio_emergencia", AccionAuditoria.INSERT, 9)


@pytest.mark.parametrize("estado", [EstadoEpisodio.EN_ESPERA_TRIAJE, EstadoEpisodio.EN_ESPERA,
                                    EstadoEpisodio.EN_ATENCION])
def test_no_se_abren_dos_episodios_a_la_vez(datos, ctrl, estado):
    datos["PacienteDAO"].bloquear.return_value = True
    datos["EpisodioDAO"].listar_por_paciente.return_value = [episodio(3, estado=estado)]
    with pytest.raises(ReglaNegocioError, match="episodio abierto"):
        ctrl.abrir_episodio(1, "Dolor torácico")
    assert datos.escrituras() == [] and datos.llamadas()[-1] == "rollback"


def test_un_episodio_anulado_no_cuenta_como_abierto(datos, ctrl):
    anulado = episodio(3, estado=EstadoEpisodio.EN_ESPERA)
    anulado.anular()
    datos["PacienteDAO"].bloquear.return_value = True
    datos["EpisodioDAO"].listar_por_paciente.return_value = [anulado]
    datos["EpisodioDAO"].crear.return_value = 9
    ctrl.abrir_episodio(1, "Dolor torácico")
    datos["EpisodioDAO"].crear.assert_called_once()


def test_abrir_episodio_de_un_paciente_inexistente_o_anulado(datos, ctrl):
    datos["PacienteDAO"].bloquear.return_value = False
    with pytest.raises(ReglaNegocioError, match="no existe"):
        ctrl.abrir_episodio(1, "Dolor torácico")
    datos["EpisodioDAO"].crear.assert_not_called()


@pytest.mark.parametrize("motivo", ["", "   ", None])
def test_abrir_episodio_sin_motivo(datos, ctrl, motivo):
    with pytest.raises(ValueError, match="motivo"):
        ctrl.abrir_episodio(1, motivo)
    assert datos.llamadas() == []


# ---- Identificar

def test_identificar_un_nn(datos, ctrl):
    datos["PacienteDAO"].buscar_por_id.return_value = nn()
    datos["PacienteDAO"].buscar_por_documento.return_value = None
    datos["PacienteDAO"].identificar.return_value = True
    paciente = ctrl.identificar(5, "DNI", DNI, "Juan", "Quispe", date(1980, 3, 1))
    assert paciente.identificado and paciente.nombres == "Juan"
    assert datos.escrituras() == ["PacienteDAO.identificar", "AuditoriaDAO.registrar"]
    assert datos.auditoria().args == (10, "paciente", AccionAuditoria.IDENTIFICAR, 5)
    assert datos.llamadas()[-1] == "commit"


def test_identificar_con_un_documento_de_otro_paciente_pide_fusionar(datos, ctrl):
    datos["PacienteDAO"].buscar_por_id.return_value = nn()
    datos["PacienteDAO"].buscar_por_documento.return_value = rosa()
    with pytest.raises(ReglaNegocioError, match="fusione"):
        ctrl.identificar(5, "DNI", DNI, "Rosa", "Mendoza", NACIMIENTO)
    assert datos.escrituras() == []


def test_identificar_cuando_otro_usuario_llego_primero(datos, ctrl):
    datos["PacienteDAO"].buscar_por_id.return_value = nn()
    datos["PacienteDAO"].buscar_por_documento.return_value = None
    datos["PacienteDAO"].identificar.return_value = False
    with pytest.raises(ReglaNegocioError, match="Otro usuario"):
        ctrl.identificar(5, "DNI", DNI, "Juan", "Quispe", date(1980, 3, 1))
    datos["AuditoriaDAO"].registrar.assert_not_called()
    assert datos.llamadas()[-1] == "rollback"


@pytest.mark.parametrize("encontrado, error", [(None, ReglaNegocioError), (rosa(), ReglaNegocioError)])
def test_identificar_inexistente_o_ya_identificado(datos, ctrl, encontrado, error):
    datos["PacienteDAO"].buscar_por_id.return_value = encontrado
    datos["PacienteDAO"].buscar_por_documento.return_value = None
    with pytest.raises(error):
        ctrl.identificar(5, "DNI", "11112222", "Juan", "Quispe", date(1980, 3, 1))
    datos["PacienteDAO"].identificar.assert_not_called()


# ---- Fusionar

def test_fusionar_un_nn_con_un_paciente_registrado(datos, ctrl):
    datos["PacienteDAO"].buscar_por_id.side_effect = [nn(5), rosa(1)]
    datos["EpisodioDAO"].listar_por_paciente.side_effect = [[episodio(9, 5)], []]
    datos["PacienteDAO"].fusionar.return_value = 1
    assert ctrl.fusionar(5, 1) == 1
    nn_fusionado, destino = datos["PacienteDAO"].fusionar.call_args.args
    assert not nn_fusionado.activo and destino.id_paciente == 1
    assert datos.auditoria().args == (10, "paciente", AccionAuditoria.FUSIONAR, 5,
                                      {"id_destino": 1, "episodios_movidos": 1})
    assert datos.escrituras() == ["PacienteDAO.fusionar", "AuditoriaDAO.registrar"]


def test_no_se_fusionan_dos_pacientes_con_episodios_abiertos(datos, ctrl):
    datos["PacienteDAO"].buscar_por_id.side_effect = [nn(5), rosa(1)]
    datos["EpisodioDAO"].listar_por_paciente.side_effect = [[episodio(9, 5)], [episodio(4, 1)]]
    with pytest.raises(ReglaNegocioError, match="Ambos"):
        ctrl.fusionar(5, 1)
    datos["PacienteDAO"].fusionar.assert_not_called()


def test_fusionar_con_un_destino_no_identificado(datos, ctrl):
    datos["PacienteDAO"].buscar_por_id.side_effect = [nn(5), nn(6)]
    with pytest.raises(ReglaNegocioError, match="identificado"):
        ctrl.fusionar(5, 6)
    assert datos.escrituras() == []


def test_fusionar_un_paciente_inexistente(datos, ctrl):
    datos["PacienteDAO"].buscar_por_id.side_effect = [nn(5), None]
    with pytest.raises(ReglaNegocioError, match="no existe"):
        ctrl.fusionar(5, 99)
