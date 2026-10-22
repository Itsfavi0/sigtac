from dataclasses import dataclass

from dao.episodio_dao import EpisodioDAO
from dao.paciente_dao import PacienteDAO
from dao.transaccion import transaccion
from models.estados import EstadoEpisodio
from models.persona import Paciente
from models.triaje import EpisodioEmergencia, ordenar_por_prioridad


@dataclass(frozen=True)
class EntradaCola:
    """Un paciente en una cola de espera (de triaje o de cama), listo para mostrarse en la vista."""
    posicion: int  # 1 = el siguiente en ser atendido
    episodio: EpisodioEmergencia
    paciente: Paciente | None  # None solo si el paciente no se pudo leer (no debería ocurrir: FK)

    @property
    def nivel(self) -> int | None:
        return self.episodio.nivel_actual


def armar_cola(estado: EstadoEpisodio) -> list[EntradaCola]:
    """
    Episodios activos en `estado`, con su paciente, en orden de prioridad (ver ordenar_por_prioridad).
    Las lecturas van en una transacción para que episodios, historial y pacientes salgan de la misma
    foto de la BD aunque otra PC esté cambiando la cola en ese momento. El permiso lo comprueba el
    controlador que la llama.
    """
    with transaccion():
        episodios = EpisodioDAO.listar_por_estado(estado)
        pacientes = PacienteDAO.listar_por_estado_de_episodio(estado) if episodios else {}
    return [EntradaCola(posicion, episodio, pacientes.get(episodio.id_episodio))
            for posicion, episodio in enumerate(ordenar_por_prioridad(episodios), start=1)]
