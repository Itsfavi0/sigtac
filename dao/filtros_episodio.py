"""
Condiciones SQL fijas para cargar de una vez varios episodios y su historial (cola de espera,
episodios de un paciente). Las comparten EpisodioDAO, TriajeDAO y PacienteDAO, que usan el alias
`ep` para la tabla episodio_emergencia.

El nombre del filtro se valida contra esta lista blanca y el valor siempre viaja como parámetro
(%s): ningún dato del usuario se concatena al SQL.
"""

FILTROS_EPISODIO = {
    # Episodios activos en un estado (p. ej. la cola de espera de cama)
    "estado": "ep.estado_registro = TRUE AND ep.id_estado_ep = "
              "(SELECT id_estado_ep FROM estado_episodio WHERE nombre_estado_episodio = %s)",
    # Todos los episodios de un paciente (activos y anulados)
    "paciente": "ep.id_paciente = %s",
}


def condicion(filtro: str) -> str:
    """Devuelve la condición SQL del filtro, o lanza ValueError si no está en la lista blanca."""
    if filtro not in FILTROS_EPISODIO:
        raise ValueError("Filtro de episodios no reconocido.")
    return FILTROS_EPISODIO[filtro]
