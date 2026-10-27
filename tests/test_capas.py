"""Comprueba la regla de capas para las vistas: views → controllers, nunca directo a dao/ ni a MySQL."""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVOS_DE_PRESENTACION = sorted((RAIZ / "views").rglob("*.py")) + [RAIZ / "main.py"]
IMPORTACION_PROHIBIDA = re.compile(r"^\s*(from|import)\s+(dao|mysql)\b", re.M)


def test_hay_archivos_de_presentacion():
    assert any(p.name == "tema.py" for p in ARCHIVOS_DE_PRESENTACION)  # la búsqueda encuentra las vistas


@pytest.mark.parametrize("archivo", ARCHIVOS_DE_PRESENTACION, ids=lambda p: p.relative_to(RAIZ).as_posix())
def test_las_vistas_no_importan_dao_ni_mysql(archivo):
    assert not IMPORTACION_PROHIBIDA.search(archivo.read_text(encoding="utf-8"))
