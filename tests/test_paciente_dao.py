from datetime import date
from unittest.mock import MagicMock

import mysql.connector
import pytest
from mysql.connector import errorcode

from dao import base_dao
from dao.paciente_dao import PacienteDAO
from models.excepciones import ConexionBDError, PersistenciaError, RegistroDuplicadoError
from models.documento import DocumentoIdentidad, TipoDocumento
from models.persona import Paciente

DNI = "70123456"
DOCUMENTO = DocumentoIdentidad(TipoDocumento.DNI, DNI)


def fila(estado_registro=1, **cambios):
    datos = {
        "id_paciente": 1, "tipo_documento": "DNI", "num_documento": DNI, "nombres": "Rosa", "apellidos": "Mendoza Flores",
        "fecha_nac": date(1959, 5, 14), "sexo": "F", "id_seguro": 1,
        "nombre_seguro": "EsSalud", "estado_registro": estado_registro,
    }
    datos.update(cambios)
    return datos


def paciente(id_paciente=None, activo=True):
    return Paciente(id_paciente, DOCUMENTO, "Rosa", "Mendoza Flores", date(1959, 5, 14), "F", 1, activo=activo)


class BD:
    """Conexión simulada: el cursor devuelve lo indicado y recuerda cómo se usó."""

    def __init__(self, monkeypatch, row=None, rowcount=1, lastrowid=None, error_en_execute=None):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        self.cursor.rowcount = rowcount
        self.cursor.lastrowid = lastrowid
        if error_en_execute:
            self.cursor.execute.side_effect = error_en_execute
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        self.clase.return_value.obtener_conexion.return_value = conexion
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)

    @property
    def sql(self) -> str:
        return " ".join(self.cursor.execute.call_args.args[0].split())

    @property
    def params(self) -> tuple:
        return self.cursor.execute.call_args.args[1]


# ---- Lectura y mapeo fila → Paciente
def test_buscar_por_documento_devuelve_un_paciente(monkeypatch):
    bd = BD(monkeypatch, row=fila())
    p = PacienteDAO.buscar_por_documento(DOCUMENTO)
    assert isinstance(p, Paciente)
    assert (p.id_paciente, p.documento, p.sexo, p.id_seguro) == (1, DOCUMENTO, "F", 1)
    assert p.fecha_nac == date(1959, 5, 14)
    assert "WHERE td.codigo = %s AND p.num_documento = %s" in bd.sql
    assert bd.params == ("DNI", DNI)
    assert DNI not in bd.sql  # el dato viaja aparte, nunca dentro del SQL


def test_buscar_paciente_extranjero(monkeypatch):
    bd = BD(monkeypatch, row=fila(tipo_documento="CE", num_documento="001234567"))
    ce = DocumentoIdentidad(TipoDocumento.CARNE_EXTRANJERIA, "001234567")
    assert PacienteDAO.buscar_por_documento(ce).documento == ce
    assert bd.params == ("CE", "001234567")
    assert "JOIN tipo_documento" in bd.sql


def test_el_nombre_del_seguro_se_obtiene_con_join(monkeypatch):
    bd = BD(monkeypatch, row=fila())
    assert PacienteDAO.buscar_por_documento(DOCUMENTO).nombre_seguro == "EsSalud"
    assert "JOIN seguro" in bd.sql


@pytest.mark.parametrize("estado_registro, activo", [(1, True), (0, False)])
def test_estado_registro_se_convierte_a_bool(monkeypatch, estado_registro, activo):
    BD(monkeypatch, row=fila(estado_registro))
    assert PacienteDAO.buscar_por_id(1).activo is activo


def test_buscar_por_documento_incluye_a_los_anulados(monkeypatch):
    bd = BD(monkeypatch, row=fila(estado_registro=0))
    assert PacienteDAO.buscar_por_documento(DOCUMENTO) is not None
    assert "estado_registro = TRUE" not in bd.sql


def test_buscar_por_id(monkeypatch):
    bd = BD(monkeypatch, row=fila())
    assert PacienteDAO.buscar_por_id(1).id_paciente == 1
    assert "WHERE p.id_paciente = %s" in bd.sql and bd.params == (1,)


@pytest.mark.parametrize("metodo, argumento", [
    ("buscar_por_id", 99), ("buscar_por_documento", DocumentoIdentidad(TipoDocumento.DNI, "99999999")),
])
def test_inexistente_devuelve_none(monkeypatch, metodo, argumento):
    BD(monkeypatch, row=None)
    assert getattr(PacienteDAO, metodo)(argumento) is None


@pytest.mark.parametrize("documento", [DNI, None, ("DNI", DNI), "7012345' OR '1'='1"])
def test_buscar_sin_documento_identidad_se_rechaza_sin_consultar_la_bd(monkeypatch, documento):
    # El formato lo valida DocumentoIdentidad al crearse; el DAO solo exige recibir uno.
    bd = BD(monkeypatch, row=fila())
    with pytest.raises(ValueError):
        PacienteDAO.buscar_por_documento(documento)
    bd.clase.assert_not_called()


def test_fila_con_tipo_de_documento_desconocido_se_rechaza(monkeypatch):
    BD(monkeypatch, row=fila(tipo_documento="XX"))
    with pytest.raises(ValueError):
        PacienteDAO.buscar_por_id(1)


def test_fila_con_datos_invalidos_no_se_convierte_en_paciente(monkeypatch):
    # El constructor de Paciente es quien valida: el DAO no repite la regla
    BD(monkeypatch, row=fila(sexo="X"))
    with pytest.raises(ValueError):
        PacienteDAO.buscar_por_id(1)


# ---- crear
def test_crear_inserta_y_devuelve_el_id(monkeypatch):
    bd = BD(monkeypatch, lastrowid=7)
    assert PacienteDAO.crear(paciente()) == 7
    assert bd.sql.startswith("INSERT INTO paciente")
    assert "(SELECT id_tipo_documento FROM tipo_documento WHERE codigo = %s)" in bd.sql
    assert bd.params == ("DNI", DNI, "Rosa", "Mendoza Flores", date(1959, 5, 14), "F", 1)


def test_crear_paciente_extranjero(monkeypatch):
    bd = BD(monkeypatch, lastrowid=8)
    pasaporte = DocumentoIdentidad(TipoDocumento.PASAPORTE, "AB1234567")
    p = Paciente(None, pasaporte, "John", "Smith", date(1990, 1, 1), "M", 4)
    assert PacienteDAO.crear(p) == 8
    assert bd.params[:2] == ("PAS", "AB1234567")


def test_crear_con_documento_existente_lanza_registro_duplicado(monkeypatch):
    duplicado = mysql.connector.IntegrityError(msg="Duplicate entry", errno=errorcode.ER_DUP_ENTRY)
    BD(monkeypatch, error_en_execute=duplicado)
    with pytest.raises(RegistroDuplicadoError):
        PacienteDAO.crear(paciente())


def test_crear_con_seguro_inexistente_lanza_persistencia_error(monkeypatch):
    fk = mysql.connector.IntegrityError(msg="FK", errno=errorcode.ER_NO_REFERENCED_ROW_2)
    BD(monkeypatch, error_en_execute=fk)
    with pytest.raises(PersistenciaError):
        PacienteDAO.crear(paciente())


@pytest.mark.parametrize("p", [paciente(id_paciente=1), paciente(activo=False)])
def test_crear_rechaza_pacientes_con_id_o_anulados(monkeypatch, p):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        PacienteDAO.crear(p)
    bd.clase.assert_not_called()


# ---- actualizar
def test_actualizar_no_modifica_el_documento(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    assert PacienteDAO.actualizar(paciente(id_paciente=1)) is True
    set_clausula = bd.sql.split("SET")[1].split("WHERE")[0]
    assert "documento" not in set_clausula
    assert DNI not in bd.params
    assert bd.params[-1] == 1  # el WHERE usa el id


def test_actualizar_inexistente_devuelve_false(monkeypatch):
    BD(monkeypatch, rowcount=0)
    assert PacienteDAO.actualizar(paciente(id_paciente=99)) is False


def test_actualizar_sin_id_se_rechaza(monkeypatch):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        PacienteDAO.actualizar(paciente())
    bd.clase.assert_not_called()


# ---- Pacientes sin identificar (NN)
def fila_nn(**cambios):
    datos = dict(id_paciente=5, tipo_documento=None, num_documento=None, nombres="NN", apellidos="NN",
                 fecha_nac=date(1981, 1, 1), sexo="M", id_seguro=4)
    datos.update(cambios)
    return fila(**datos)


def test_fila_sin_documento_se_convierte_en_paciente_no_identificado(monkeypatch):
    bd = BD(monkeypatch, row=fila_nn())
    p = PacienteDAO.buscar_por_id(5)
    assert p.identificado is False and p.documento is None
    assert "LEFT JOIN tipo_documento" in bd.sql  # sin LEFT JOIN, el paciente NN no se encontraría


def test_crear_paciente_no_identificado_envia_null_en_el_documento(monkeypatch):
    bd = BD(monkeypatch, lastrowid=9)
    assert PacienteDAO.crear(Paciente.no_identificado("M", 45, 4)) == 9
    assert bd.params[:4] == (None, None, "NN", "NN")


def test_listar_no_identificados(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.fetchall.return_value = [fila_nn(), fila_nn(id_paciente=6)]
    pacientes = PacienteDAO.listar_no_identificados()
    assert [p.id_paciente for p in pacientes] == [5, 6]
    assert all(not p.identificado for p in pacientes)
    assert "WHERE p.num_documento IS NULL AND p.estado_registro = TRUE" in bd.sql


def test_listar_no_identificados_vacio(monkeypatch):
    bd = BD(monkeypatch)
    bd.cursor.fetchall.return_value = []
    assert PacienteDAO.listar_no_identificados() == []


def paciente_identificado():
    p = Paciente(5, None, "NN", "NN", date(1981, 1, 1), "M", 4)
    p.identificar(DocumentoIdentidad(TipoDocumento.PASAPORTE, "AB1234567"), "John", "Smith", date(1980, 3, 2))
    return p


def test_identificar_guarda_documento_y_datos_reales(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    assert PacienteDAO.identificar(paciente_identificado()) is True
    assert bd.sql.startswith("UPDATE paciente SET id_tipo_documento = (SELECT")
    assert "WHERE id_paciente = %s AND num_documento IS NULL" in bd.sql  # no sobrescribe un documento
    assert bd.params == ("PAS", "AB1234567", "John", "Smith", date(1980, 3, 2), 5)


def test_identificar_inexistente_o_ya_identificado_devuelve_false(monkeypatch):
    BD(monkeypatch, rowcount=0)
    assert PacienteDAO.identificar(paciente_identificado()) is False


def test_identificar_con_documento_de_otro_paciente_lanza_registro_duplicado(monkeypatch):
    duplicado = mysql.connector.IntegrityError(msg="Duplicate entry", errno=errorcode.ER_DUP_ENTRY)
    BD(monkeypatch, error_en_execute=duplicado)
    with pytest.raises(RegistroDuplicadoError):
        PacienteDAO.identificar(paciente_identificado())


@pytest.mark.parametrize("p", [
    Paciente.no_identificado("M", 45, 4),               # sin id
    Paciente(5, None, "NN", "NN", date(1981, 1, 1), "M", 4),  # sin documento
])
def test_identificar_rechaza_pacientes_sin_id_o_sin_documento(monkeypatch, p):
    bd = BD(monkeypatch)
    with pytest.raises(ValueError):
        PacienteDAO.identificar(p)
    bd.clase.assert_not_called()


def test_identificar_no_registra_datos_personales_en_el_log(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    BD(monkeypatch, rowcount=1)
    PacienteDAO.identificar(paciente_identificado())
    assert "AB1234567" not in caplog.text and "Smith" not in caplog.text
    assert "id_paciente=5" in caplog.text


# ---- anular (RN-11)
def test_anular_es_borrado_logico(monkeypatch):
    bd = BD(monkeypatch, rowcount=1)
    assert PacienteDAO.anular(1) is True
    assert bd.sql.startswith("UPDATE paciente SET estado_registro = FALSE")
    assert "DELETE" not in bd.sql.upper()
    assert bd.params == (1,)


def test_anular_inexistente_devuelve_false(monkeypatch):
    BD(monkeypatch, rowcount=0)
    assert PacienteDAO.anular(99) is False


# ---- Errores de infraestructura
def test_sin_conexion_se_propaga(monkeypatch):
    bd = BD(monkeypatch)
    bd.clase.return_value.obtener_conexion.side_effect = ConexionBDError("sin servidor")
    with pytest.raises(ConexionBDError):
        PacienteDAO.buscar_por_documento(DOCUMENTO)


# ---- Los logs no filtran datos personales
def test_los_logs_no_contienen_documento_ni_nombres(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    BD(monkeypatch, row=fila(), lastrowid=7)
    PacienteDAO.crear(paciente())
    PacienteDAO.buscar_por_documento(DOCUMENTO)
    PacienteDAO.anular(1)
    assert DNI not in caplog.text and "Rosa" not in caplog.text and "Mendoza" not in caplog.text
