"""Dobles de prueba compartidos por las pruebas de los controladores."""
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from controllers.auth_controller import Sesion
from models.permisos import Rol


class CapaDatosFalsa:
    """
    Reemplaza, en el módulo de un controlador, los DAO indicados y transaccion() por dobles que
    anotan en un mismo registro el orden de todas las llamadas. Así una prueba comprueba qué se
    guardó y que se hizo dentro de la transacción (entre "inicio" y "commit"), sin MySQL.
    """

    def __init__(self, monkeypatch, modulo, *daos):
        self.registro = MagicMock()
        for nombre in daos:
            monkeypatch.setattr(modulo, nombre, getattr(self.registro, nombre))
        monkeypatch.setattr(modulo, "transaccion", self._transaccion)

    def __getitem__(self, nombre_dao):
        return getattr(self.registro, nombre_dao)

    @contextmanager
    def _transaccion(self):
        self.registro.inicio()
        try:
            yield
        except BaseException:
            self.registro.rollback()
            raise
        self.registro.commit()

    def llamadas(self) -> list[str]:
        """Nombres de las llamadas en orden, p. ej. ["inicio", "PacienteDAO.crear", "commit"]."""
        return [nombre for nombre, _, _ in self.registro.mock_calls if "()" not in nombre]

    def escrituras(self) -> list[str]:
        """Las llamadas que cambian datos (ni lecturas ni bloqueos), en orden."""
        lecturas = ("buscar", "listar", "bloquear")
        return [n for n in self.llamadas() if "." in n and not n.split(".")[1].startswith(lecturas)]

    def auditoria(self):
        """Argumentos de la (única) llamada a AuditoriaDAO.registrar."""
        return self.registro.AuditoriaDAO.registrar.call_args


@pytest.fixture
def capa_datos(monkeypatch):
    """Fábrica: capa_datos(modulo_del_controlador, "PacienteDAO", "AuditoriaDAO", ...)."""
    return lambda modulo, *daos: CapaDatosFalsa(monkeypatch, modulo, *daos)


def crear_sesion(rol=Rol.MEDICO, id_usuario=10, id_empleado=20) -> Sesion:
    return Sesion(id_usuario, id_empleado, rol, "Luis", "Ramos")


@pytest.fixture
def sesion_de():
    """Fábrica: sesion_de(Rol.ENFERMERO) crea una sesión activa de ese rol."""
    return crear_sesion
