"""Garantiza que los valores fijos de Python y los de la BD (seed.sql y CHECK de schema.sql) no se desincronicen."""
import re
from pathlib import Path

import pytest

from dao.cama_dao import CamaDAO
from models.documento import TipoDocumento
from models.estados import EstadoCama, EstadoEpisodio
from models.persona import Paciente, PersonalLimpieza

DB_SCRIPTS = Path(__file__).resolve().parent.parent / "db_scripts"
SEED = (DB_SCRIPTS / "seed.sql").read_text(encoding="utf-8")
SCHEMA = (DB_SCRIPTS / "schema.sql").read_text(encoding="utf-8")


def nombres_en_seed(tabla):
    bloque = re.search(rf"INSERT INTO {tabla} \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    return set(re.findall(r"\(\d+, '([^']+)'\)", bloque))


@pytest.mark.parametrize("tabla, enum", [("estado_cama", EstadoCama), ("estado_episodio", EstadoEpisodio)])
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


def test_el_seed_tiene_un_paciente_sin_identificar_con_el_nombre_del_modelo():
    nn = Paciente.NOMBRE_NO_IDENTIFICADO
    assert f"NULL, NULL, '{nn}', '{nn}'," in SEED


def test_los_tipos_de_documento_coinciden_con_la_bd():
    bloque = re.search(r"INSERT INTO tipo_documento \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    codigos_en_seed = set(re.findall(r"\(\d+, '([^']+)', '[^']+'\)", bloque))
    assert codigos_en_seed  # la expresión regular encontró filas
    assert {t.value for t in TipoDocumento} == codigos_en_seed
