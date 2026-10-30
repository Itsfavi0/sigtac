"""
Controladores de demostración: los mismos métodos que los reales, con datos de ejemplo y sin MySQL.

Sirven para ver y revisar las pantallas (prototipo/ver.py) y para la demo sin base de datos. Los datos son
inventados: ningún nombre ni número corresponde a una persona real.
"""
from datetime import datetime, timedelta

from controllers.auth_controller import Sesion
from controllers.colas import EntradaCola
from controllers.reporte_controller import IndicadoresPeriodo
from models.cama import CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.documento import DocumentoIdentidad
from models.estados import EstadoCama, EstadoEpisodio
from models.permisos import Rol
from models.persona import Paciente
from models.triaje import EpisodioEmergencia, Triaje

D, O, L, R, F = (EstadoCama.DISPONIBLE, EstadoCama.OCUPADA, EstadoCama.EN_LIMPIEZA, EstadoCama.RESERVADA,
                 EstadoCama.FUERA_SERVICIO)

_CAMAS = (
    (CamaTraumaShock, "TS", "Trauma Shock", [O, O, D, R]),
    (CamaUCI, "UCI", "UCI", [O, O, D, R, O, D, L, F]),
    (CamaObservacion, "OBS", "Sala de Observación Adultos", [D, O, D, L, O, D, R, D, O, L, D, F, D, O]),
    (CamaHospitalizacion, "HOS", "Pabellón de Hospitalización A", [D, D, O, O, D, L, D, O, D, D]),
)

# nivel, documento, nombres, apellidos, sexo, motivo, minutos esperando
_ESPERAN_CAMA = (
    (1, ("DNI", "43215619"), "María", "Salazar Quispe", "F", "Dolor torácico agudo", 2),
    (2, ("DNI", "26874504"), "Jorge", "Mendoza Ríos", "M", "Dificultad respiratoria", 7),
    (3, ("CE", "00123452"), "Ana", "Torres Vega", "F", "Traumatismo en miembro inferior", 14),
    (3, None, None, None, "M", "Hallado inconsciente en la vía pública", 71),
)
_ESPERAN_TRIAJE = (
    (("DNI", "70112233"), "Rosa", "Huamán Paredes", "F", "Fiebre alta y vómitos", 5),
    (("DNI", "45566778"), "Luis", "Campos Díaz", "M", "Herida en la mano", 12),
)


def sesion_demo(rol: Rol = Rol.JEFE_GUARDIA) -> Sesion:
    return Sesion(1, 1, rol, "Elena", "Ríos Paredes")


def _paciente(id_paciente, documento, nombres, apellidos, sexo):
    if documento is None:
        nn = Paciente.no_identificado(sexo, 40, 1)
        return Paciente(id_paciente, None, nn.nombres, nn.apellidos, nn.fecha_nac, sexo, 1)
    return Paciente(id_paciente, DocumentoIdentidad(*documento), nombres, apellidos, datetime(1985, 3, 14).date(),
                    sexo, 1, nombre_seguro="SIS")


class CamasDemo:
    def __init__(self, ahora=datetime.now):
        self._ahora = ahora

    def mapa_camas(self):
        camas, id_cama = [], 1
        for clase, prefijo, area, estados in _CAMAS:
            for n, estado in enumerate(estados, start=1):
                camas.append(clase(id_cama, f"{prefijo}-{n:02d}", area, estado))
                id_cama += 1
        return camas

    def cola_de_espera(self):
        ahora = self._ahora()
        cola = []
        for posicion, (nivel, doc, nombres, apellidos, sexo, motivo, minutos) in enumerate(_ESPERAN_CAMA, 1):
            llegada = ahora - timedelta(minutes=minutos)
            triaje = Triaje(posicion, nivel, 1, llegada)
            episodio = EpisodioEmergencia(posicion, posicion, motivo, EstadoEpisodio.EN_ESPERA, fecha_ingreso=llegada,
                                          triajes=[triaje])
            cola.append(EntradaCola(posicion, episodio, _paciente(posicion, doc, nombres, apellidos, sexo)))
        return cola


class TriajeDemo:
    def __init__(self, ahora=datetime.now):
        self._ahora = ahora

    def cola_de_triaje(self):
        ahora = self._ahora()
        cola = []
        for posicion, (doc, nombres, apellidos, sexo, motivo, minutos) in enumerate(_ESPERAN_TRIAJE, 1):
            episodio = EpisodioEmergencia(100 + posicion, 100 + posicion, motivo,
                                          fecha_ingreso=ahora - timedelta(minutes=minutos))
            cola.append(EntradaCola(posicion, episodio, _paciente(100 + posicion, doc, nombres, apellidos, sexo)))
        return cola


class ReportesDemo:
    def indicadores(self, desde, hasta):
        return IndicadoresPeriodo(desde, hasta, 42, {1: 3, 2: 6, 3: 15, 4: 9, 5: 3}, 12.5, 6.0, 8.0, 312.0)
