"""Garantiza que los Enum de Python y los catálogos del seed.sql no se desincronicen."""
import re
from pathlib import Path

import pytest

from models.estados import EstadoCama, EstadoEpisodio

SEED = (Path(__file__).resolve().parent.parent / "db_scripts" / "seed.sql").read_text(encoding="utf-8")


def nombres_en_seed(tabla):
    bloque = re.search(rf"INSERT INTO {tabla} \(.*?\) VALUES(.*?);", SEED, re.S).group(1)
    return set(re.findall(r"\(\d+, '([^']+)'\)", bloque))


@pytest.mark.parametrize("tabla, enum", [("estado_cama", EstadoCama), ("estado_episodio", EstadoEpisodio)])
def test_los_enum_coinciden_con_los_catalogos_de_la_bd(tabla, enum):
    assert {e.value for e in enum} == nombres_en_seed(tabla)
