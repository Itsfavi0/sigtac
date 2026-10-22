from datetime import datetime, timedelta

import pytest

from controllers import colas
from controllers.colas import EntradaCola, armar_cola
from models.estados import EstadoEpisodio
from models.persona import Paciente
from models.triaje import EpisodioEmergencia, Triaje

AHORA = datetime(2026, 10, 22, 9, 0)


def en_espera(id_episodio, nivel, minutos):
    return EpisodioEmergencia(id_episodio, id_episodio, "Motivo", estado=EstadoEpisodio.EN_ESPERA,
                              fecha_ingreso=AHORA - timedelta(minutes=minutos),
                              triajes=(Triaje(id_episodio, nivel, 3, AHORA),))


@pytest.fixture
def datos(capa_datos):
    return capa_datos(colas, "EpisodioDAO", "PacienteDAO")


def test_la_cola_sale_en_orden_de_prioridad_con_su_paciente(datos):
    nn = Paciente.no_identificado("F", 30, 4)
    datos["EpisodioDAO"].listar_por_estado.return_value = [en_espera(1, 3, 50), en_espera(2, 1, 5), en_espera(3, 3, 80)]
    datos["PacienteDAO"].listar_por_estado_de_episodio.return_value = {1: nn, 2: nn, 3: nn}
    cola = armar_cola(EstadoEpisodio.EN_ESPERA)
    assert [(e.posicion, e.episodio.id_episodio, e.nivel) for e in cola] == [(1, 2, 1), (2, 3, 3), (3, 1, 3)]
    assert all(e.paciente is nn for e in cola)
    # una sola transacción: todas las lecturas ven la misma foto de la BD
    assert datos.llamadas() == ["inicio", "EpisodioDAO.listar_por_estado",
                                "PacienteDAO.listar_por_estado_de_episodio", "commit"]
    datos["EpisodioDAO"].listar_por_estado.assert_called_once_with(EstadoEpisodio.EN_ESPERA)


def test_una_cola_vacia_no_busca_pacientes(datos):
    datos["EpisodioDAO"].listar_por_estado.return_value = []
    assert armar_cola(EstadoEpisodio.EN_ESPERA_TRIAJE) == []
    datos["PacienteDAO"].listar_por_estado_de_episodio.assert_not_called()


def test_la_entrada_es_inmutable():
    entrada = EntradaCola(1, en_espera(1, 2, 5), None)
    assert entrada.nivel == 2
    with pytest.raises(AttributeError):
        entrada.posicion = 2
