"""
Controladores de demostración: los mismos métodos que los reales, con datos de ejemplo y sin MySQL.

Sirven para ver y revisar las pantallas (prototipo/ver.py) y para la demo sin base de datos. Los datos son
inventados: ningún nombre ni número corresponde a una persona real.
"""
from datetime import datetime, timedelta

from controllers.auth_controller import Sesion
from controllers.colas import EntradaCola
from controllers.reporte_controller import IndicadoresPeriodo
from controllers.triaje_controller import Sugerencia
from models.cama import CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.documento import DocumentoIdentidad
from models.estados import EstadoCama, EstadoEpisodio
from models.estrategias import ReglaManchester
from models.excepciones import ReglaNegocioError
from models.permisos import Rol
from models.persona import Paciente
from models.triaje import EpisodioEmergencia, SignosVitales, Sintoma, Triaje

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
# Registrada antes, sin episodio abierto: al buscar su DNI aparece su ficha
_REGISTRADO = (("DNI", "41234567"), "Carmen", "Rojas Llanos", "F")
# Pacientes que llegaron sin identificar: sexo, edad aparente y seguro
_SIN_IDENTIFICAR = (("M", 40, 4), ("F", 25, 2))

# Los catálogos de seed.sql
_SEGUROS = ({"id_seguro": 1, "nombre_seguro": "EsSalud"},
            {"id_seguro": 2, "nombre_seguro": "SIS (Seguro Integral de Salud)"},
            {"id_seguro": 3, "nombre_seguro": "Seguro Privado (EPS)"},
            {"id_seguro": 4, "nombre_seguro": "Particular / Sin Seguro"})
_SINTOMAS = (Sintoma(1, "Paro Cardiorrespiratorio", 10.0), Sintoma(2, "Dolor Torácico Opresivo", 8.5),
             Sintoma(3, "Dificultad Respiratoria Severa (Disnea)", 8.0), Sintoma(4, "Sangrado Activo Profuso", 7.5),
             Sintoma(5, "Alteración de la Conciencia (Glasgow < 8)", 9.0), Sintoma(6, "Fiebre Alta (> 39°C)", 4.0),
             Sintoma(7, "Dolor Abdominal Intenso", 5.0), Sintoma(8, "Vómitos Persistentes", 3.5),
             Sintoma(9, "Herida Superficial", 1.0), Sintoma(10, "Tos Leve", 0.5))


def sesion_demo(rol: Rol = Rol.JEFE_GUARDIA) -> Sesion:
    return Sesion(1, 1, rol, "Elena", "Ríos Paredes")


def _paciente(id_paciente, documento, nombres, apellidos, sexo):
    if documento is None:
        nn = Paciente.no_identificado(sexo, 40, 1)
        return Paciente(id_paciente, None, nn.nombres, nn.apellidos, nn.fecha_nac, sexo, 1)
    # SIS: el id y el nombre salen del mismo catálogo, para que la ficha y la edición digan lo mismo
    sis = _SEGUROS[1]
    return Paciente(id_paciente, DocumentoIdentidad(*documento), nombres, apellidos, datetime(1985, 3, 14).date(),
                    sexo, sis["id_seguro"], nombre_seguro=sis["nombre_seguro"])


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
    """
    La cola de triaje y el triaje, con la estrategia real (Manchester) y el catálogo de síntomas del seed. Recuerda
    lo que se registra mientras la ventana está abierta: un paciente triado sale de la cola.
    """

    def __init__(self, ahora=datetime.now):
        self._ahora = ahora
        self._estrategia = ReglaManchester()
        self._cola = None  # (episodio, paciente) en orden de llegada; se arma la primera vez
        self._id_triaje = 0

    def _entradas(self) -> list:
        if self._cola is None:
            ahora = self._ahora()
            self._cola = []
            for posicion, (doc, nombres, apellidos, sexo, motivo, minutos) in enumerate(_ESPERAN_TRIAJE, 1):
                episodio = EpisodioEmergencia(100 + posicion, 100 + posicion, motivo,
                                              fecha_ingreso=ahora - timedelta(minutes=minutos))
                self._cola.append((episodio, _paciente(100 + posicion, doc, nombres, apellidos, sexo)))
        return self._cola

    def cola_de_triaje(self):
        return [EntradaCola(posicion, episodio, paciente)
                for posicion, (episodio, paciente) in enumerate(self._entradas(), 1)]

    def agregar(self, episodio: EpisodioEmergencia, paciente: Paciente):
        """Lo que hace abrir un episodio: el paciente pasa a esperar triaje."""
        self._entradas().append((episodio, paciente))

    def en_cola(self, id_paciente: int) -> bool:
        return any(paciente.id_paciente == id_paciente for _, paciente in self._entradas())

    def pacientes_en_cola(self) -> list[Paciente]:
        return [paciente for _, paciente in self._entradas()]

    def cambiar_paciente(self, id_anterior: int, nuevo: Paciente) -> int:
        """Lo que hace una fusión: los episodios del NN pasan a `nuevo`. Devuelve cuántos se movieron."""
        entradas = self._entradas()
        movidos = 0
        for i, (episodio, paciente) in enumerate(entradas):
            if paciente.id_paciente == id_anterior:
                entradas[i] = (episodio, nuevo)
                movidos += 1
        return movidos

    def listar_sintomas(self):
        return list(_SINTOMAS)

    def sugerir(self, signos: dict, ids_sintomas):
        clasificacion = self._estrategia.evaluar(self._signos(signos), self._sintomas(ids_sintomas))
        return Sugerencia(clasificacion.nivel, self._estrategia.justificar(), clasificacion.criterios)

    def registrar(self, id_episodio: int, signos: dict, ids_sintomas, nivel_final=None, justificacion=None) -> int:
        sugerido = self._estrategia.clasificar(self._signos(signos), self._sintomas(ids_sintomas))
        triaje = Triaje(None, sugerido, 1, None)
        if nivel_final is not None and nivel_final != sugerido:
            triaje.reclasificar(nivel_final, justificacion)  # RN-10, con la regla real
        entradas = self._entradas()
        restantes = [(e, p) for e, p in entradas if e.id_episodio != id_episodio]
        if len(restantes) == len(entradas):
            raise ReglaNegocioError("El episodio no existe o ya fue triado.")
        entradas[:] = restantes
        self._id_triaje += 1
        return self._id_triaje

    @staticmethod
    def _signos(signos: dict) -> dict:
        return SignosVitales(**signos, id_si=None).a_diccionario()  # valida tipos y rangos, como el controlador

    @staticmethod
    def _sintomas(ids_sintomas) -> list:
        elegidos = set(ids_sintomas or [])
        return [s for s in _SINTOMAS if s.id_sintoma in elegidos]


class PacientesDemo:
    """Buscar, registrar y admitir pacientes; abrir un episodio lo agrega a la cola de `triaje`."""

    def __init__(self, triaje: TriajeDemo, ahora=datetime.now):
        self._triaje = triaje
        self._ahora = ahora
        self._pacientes = [_paciente(200, *_REGISTRADO)]
        self._siguiente = 300
        for i, (sexo, edad, id_seguro) in enumerate(_SIN_IDENTIFICAR):
            nn = Paciente.no_identificado(sexo, edad, id_seguro)
            self._reemplazar(Paciente(250 + i, None, nn.nombres, nn.apellidos, nn.fecha_nac, sexo, id_seguro))

    def listar_seguros(self):
        return [dict(seguro) for seguro in _SEGUROS]

    def buscar_por_documento(self, tipo_documento: str, num_documento: str):
        documento = DocumentoIdentidad(tipo_documento, num_documento)  # ValueError si no es válido
        conocidos = self._pacientes + self._triaje.pacientes_en_cola()
        return next((p for p in conocidos if p.documento == documento), None)

    def registrar(self, tipo_documento, num_documento, nombres, apellidos, fecha_nac, sexo, id_seguro):
        documento = DocumentoIdentidad(tipo_documento, num_documento)
        paciente = Paciente(None, documento, nombres, apellidos, fecha_nac, sexo, id_seguro)  # valida los datos
        if self.buscar_por_documento(tipo_documento, num_documento) is not None:
            raise ReglaNegocioError("Ya existe un paciente registrado con ese documento.")
        return self._guardar(paciente)

    def registrar_no_identificado(self, sexo: str, edad_estimada: int, id_seguro: int):
        return self._guardar(Paciente.no_identificado(sexo, edad_estimada, id_seguro))

    def abrir_episodio(self, id_paciente: int, motivo_consulta: str):
        if not isinstance(motivo_consulta, str) or not motivo_consulta.strip():
            raise ValueError("El motivo de consulta es obligatorio.")
        paciente = next((p for p in self._pacientes if p.id_paciente == id_paciente), None)
        if paciente is None:
            raise ReglaNegocioError("El paciente no existe o está dado de baja.")
        if self._triaje.en_cola(id_paciente):
            raise ReglaNegocioError("El paciente ya tiene un episodio abierto.")
        self._siguiente += 1
        episodio = EpisodioEmergencia(self._siguiente, id_paciente, motivo_consulta, fecha_ingreso=self._ahora())
        self._triaje.agregar(episodio, paciente)
        return episodio

    def listar_no_identificados(self):
        return [p for p in self._pacientes if not p.identificado and p.activo]

    def actualizar_datos(self, id_paciente, nombres, apellidos, fecha_nac, sexo, id_seguro):
        paciente = self._cargar(id_paciente)
        paciente.actualizar_datos(nombres, apellidos, fecha_nac, sexo, id_seguro)  # las reglas reales del modelo
        return self._reemplazar(paciente)

    def identificar(self, id_paciente, tipo_documento, num_documento, nombres, apellidos, fecha_nac):
        documento = DocumentoIdentidad(tipo_documento, num_documento)
        paciente = self._cargar(id_paciente)
        if self.buscar_por_documento(tipo_documento, num_documento) is not None:
            raise ReglaNegocioError("Ese documento ya pertenece a otro paciente registrado: fusione ambos registros.")
        paciente.identificar(documento, nombres, apellidos, fecha_nac)
        return self._reemplazar(paciente)

    def fusionar(self, id_nn: int, id_destino: int) -> int:
        """Los episodios del NN (aquí, su lugar en la cola de triaje) pasan al paciente registrado."""
        nn, destino = self._cargar(id_nn), self._cargar(id_destino)
        nn.fusionar_en(destino)  # valida y anula el NN
        if self._triaje.en_cola(id_nn) and self._triaje.en_cola(id_destino):
            raise ReglaNegocioError("Ambos pacientes tienen un episodio abierto: cierre uno antes de fusionarlos.")
        return self._triaje.cambiar_paciente(id_nn, destino)

    def _cargar(self, id_paciente: int) -> Paciente:
        conocidos = self._pacientes + self._triaje.pacientes_en_cola()
        paciente = next((p for p in conocidos if p.id_paciente == id_paciente), None)
        if paciente is None:
            raise ReglaNegocioError("El paciente no existe.")
        return paciente

    def _reemplazar(self, paciente: Paciente) -> Paciente:
        """Vuelve a armar el paciente con el nombre de su seguro, como lo relee el controlador real."""
        seguro = next(s["nombre_seguro"] for s in _SEGUROS if s["id_seguro"] == paciente.id_seguro)
        nuevo = Paciente(paciente.id_paciente, paciente.documento, paciente.nombres, paciente.apellidos,
                         paciente.fecha_nac, paciente.sexo, paciente.id_seguro, nombre_seguro=seguro)
        self._pacientes = [nuevo if p.id_paciente == nuevo.id_paciente else p for p in self._pacientes]
        if all(p.id_paciente != nuevo.id_paciente for p in self._pacientes):
            self._pacientes.append(nuevo)
        return nuevo

    def _guardar(self, paciente: Paciente) -> Paciente:
        self._siguiente += 1
        seguro = next(s["nombre_seguro"] for s in _SEGUROS if s["id_seguro"] == paciente.id_seguro)
        guardado = Paciente(self._siguiente, paciente.documento, paciente.nombres, paciente.apellidos,
                            paciente.fecha_nac, paciente.sexo, paciente.id_seguro, nombre_seguro=seguro)
        self._pacientes.append(guardado)
        return guardado


class ReportesDemo:
    def indicadores(self, desde, hasta):
        return IndicadoresPeriodo(desde, hasta, 42, {1: 3, 2: 6, 3: 15, 4: 9, 5: 3}, 12.5, 6.0, 8.0, 312.0)
