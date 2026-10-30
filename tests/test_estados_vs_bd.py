"""Garantiza que los valores fijos de Python y los de la BD (seed.sql y CHECK de schema.sql) no se desincronicen."""
import re
from pathlib import Path

import pytest

from dao.auditoria_dao import AuditoriaDAO
from dao.cama_dao import CamaDAO
from models.auditoria import AccionAuditoria
from models.documento import TipoDocumento
from models.estados import EstadoCama, EstadoEpisodio
from models.permisos import Rol
from models.persona import Paciente, PersonalLimpieza
from models.triaje import COLOR_POR_NIVEL, TIEMPO_MAXIMO_POR_NIVEL, Triaje

DB_SCRIPTS = Path(__file__).resolve().parent.parent / "db_scripts"
SEED = (DB_SCRIPTS / "seed.sql").read_text(encoding="utf-8")
SCHEMA = (DB_SCRIPTS / "schema.sql").read_text(encoding="utf-8")


def nombres_en_seed(tabla):
    bloque = re.search(rf"INSERT INTO {tabla} \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    return set(re.findall(r"\(\d+, '([^']+)'\)", bloque))


@pytest.mark.parametrize("tabla, enum", [
    ("estado_cama", EstadoCama), ("estado_episodio", EstadoEpisodio), ("rol", Rol),
])
def test_los_enum_coinciden_con_los_catalogos_de_la_bd(tabla, enum):
    assert {e.value for e in enum} == nombres_en_seed(tabla)


def valores_del_check(nombre_check):
    """Valores permitidos por un CHECK (... IN ('A', 'B')) de schema.sql."""
    linea = re.search(rf"CONSTRAINT {nombre_check} CHECK (.*)", SCHEMA).group(1)
    lista = re.search(r"IN \((.*?)\)", linea).group(1)
    return set(re.findall(r"'([^']+)'", lista))


@pytest.mark.parametrize("nombre_check, valores", [
    ("CH_paciente_sexo", Paciente.SEXOS_VALIDOS),
    ("CH_empleado_turno", PersonalLimpieza.TURNOS_VALIDOS),
])
def test_valores_validos_coinciden_con_los_check_de_la_bd(nombre_check, valores):
    assert set(valores) == valores_del_check(nombre_check)


def test_la_fabrica_de_camas_cubre_los_tipos_de_la_bd():
    bloque = re.search(r"INSERT INTO tipo_cama \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    tipos_en_seed = set(re.findall(r"\(\d+, '([^']+)', \d+\)", bloque))
    assert tipos_en_seed  # la expresión regular encontró filas
    assert set(CamaDAO.CLASES_POR_TIPO) == tipos_en_seed


def test_los_niveles_de_triaje_del_seed_son_los_del_modelo():
    # TriajeDAO busca el nivel por su número (nivel_triaje.numero); Triaje acepta del 1 al 5.
    bloque = re.search(r"INSERT INTO nivel_triaje \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    numeros = {int(n) for n in re.findall(r"\(\d+, (\d+), '[^']+', \d+\)", bloque)}
    assert numeros == set(range(1, 6))


def test_los_colores_de_los_niveles_coinciden_con_el_seed():
    # El reporte PDF y las vistas muestran el color de cada nivel con COLOR_POR_NIVEL.
    bloque = re.search(r"INSERT INTO nivel_triaje \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    colores = {int(n): color for n, color in re.findall(r"\(\d+, (\d+), '([^']+)', \d+\)", bloque)}
    assert COLOR_POR_NIVEL == colores


def test_los_plazos_de_los_niveles_coinciden_con_el_seed():
    bloque = re.search(r"INSERT INTO nivel_triaje \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    plazos = {int(n): int(m) for n, m in re.findall(r"\(\d+, (\d+), '[^']+', (\d+)\)", bloque)}
    assert TIEMPO_MAXIMO_POR_NIVEL == plazos


def test_el_minimo_de_la_justificacion_coincide_con_el_check():
    # RN-10: la vista muestra el mínimo con Triaje.MIN_JUSTIFICACION; la BD lo exige con CH_triaje_rn10.
    check = re.search(r"CONSTRAINT CH_triaje_rn10 CHECK (.*)", SCHEMA).group(1)
    assert int(re.search(r"CHAR_LENGTH\(TRIM\(justificacion\)\) >= (\d+)", check).group(1)) == Triaje.MIN_JUSTIFICACION


def test_las_tablas_auditables_son_todas_las_del_esquema_salvo_la_bitacora():
    tablas = set(re.findall(r"CREATE TABLE (\w+)", SCHEMA))
    assert "paciente" in tablas  # la expresión regular encontró tablas
    assert AuditoriaDAO.TABLAS_AUDITABLES == tablas - {"bitacora_auditoria"}


def test_las_acciones_del_seed_existen_en_el_enum():
    bloque = re.search(r"INSERT INTO bitacora_auditoria \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    acciones = set(re.findall(r"\(\d+, \d+, '[^']+', '([^']+)'", bloque))
    assert acciones  # la expresión regular encontró filas
    assert acciones <= {a.value for a in AccionAuditoria}


def test_el_seed_tiene_un_paciente_sin_identificar_con_el_nombre_del_modelo():
    nn = Paciente.NOMBRE_NO_IDENTIFICADO
    assert f"NULL, NULL, '{nn}', '{nn}'," in SEED


def test_los_tipos_de_documento_coinciden_con_la_bd():
    bloque = re.search(r"INSERT INTO tipo_documento \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    codigos_en_seed = set(re.findall(r"\(\d+, '([^']+)', '[^']+'\)", bloque))
    assert codigos_en_seed  # la expresión regular encontró filas
    assert {t.value for t in TipoDocumento} == codigos_en_seed
