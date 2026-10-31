"""
Controladores de demostración: los mismos métodos que los reales, con datos de ejemplo y sin MySQL.

Sirven para ver y revisar las pantallas (prototipo/ver.py) y para la demo sin base de datos. Los datos son
inventados: ningún nombre ni número corresponde a una persona real.
"""
from datetime import datetime, timedelta

from controllers.auth_controller import Sesion
from controllers.cama_controller import CamaController, PacienteEnCama
from controllers.colas import EntradaCola
from controllers.reporte_controller import IndicadoresPeriodo
from controllers.triaje_controller import Sugerencia
from models.cama import CamaHospitalizacion, CamaObservacion, CamaTraumaShock, CamaUCI
from models.documento import DocumentoIdentidad
from models.estados import EstadoCama, EstadoEpisodio
from models.estrategias import ReglaManchester
from models.asignacion import SolicitudLimpieza
from models.excepciones import CamaNoDisponibleError, ReglaNegocioError
from models.permisos import Rol
from models.persona import Paciente
from models.triaje import EpisodioEmergencia, SignosVitales, Sintoma, Triaje, ordenar_por_prioridad

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
# Pacientes de las camas reservadas u ocupadas al abrir la demo: nombre y sexo, apellidos y motivo, combinados por
# turno. El nivel es uno compatible con su tipo de cama.
_NOMBRES = (("Pedro", "M"), ("Lucía", "F"), ("Raúl", "M"), ("Sofía", "F"), ("Miguel", "M"), ("Elsa", "F"),
            ("Víctor", "M"))
_APELLIDOS = ("Gómez Vargas", "Flores Ccama", "Castillo León", "Rojas Mamani", "Paredes Soto")
_MOTIVOS = ("Dolor abdominal", "Crisis asmática", "Fractura de cadera", "Neumonía", "Deshidratación",
            "Cefalea intensa")
_NIVEL_POR_TIPO = {CamaTraumaShock: 1, CamaUCI: 2, CamaObservacion: 3, CamaHospitalizacion: 4}
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
    """
    El ciclo de las camas con las reglas reales de los modelos (Cama, EpisodioEmergencia): asignar, ocupar, cancelar,
    dar de alta, referir, registrar una fuga, confirmar la limpieza y el mantenimiento. Recuerda lo que se hace
    mientras la ventana está abierta. Un paciente triado en TriajeDemo pasa a esperar cama aquí (esperar_cama).

    Cada operación comprueba primero lo que puede fallar sin cambiar nada (la cama), y solo después cambia el
    episodio: así un error no deja la demo a medias, como la transacción del controlador real.
    """

    def __init__(self, ahora=datetime.now):
        self._ahora = ahora
        ahora = ahora()
        self._camas, self._con_cama, self._limpieza = [], {}, []  # _con_cama: id_cama → (episodio, paciente, desde)
        self._siguiente = 400            # ids de los episodios en cama y de las asignaciones
        self._siguiente_solicitud = 0
        for clase, prefijo, area, estados in _CAMAS:
            for n, estado in enumerate(estados, start=1):
                cama = clase(len(self._camas) + 1, f"{prefijo}-{n:02d}", area, estado)
                self._camas.append(cama)
                if estado in (O, R):
                    self._con_cama[cama.id_cama] = self._paciente_en_cama(cama, ahora)
                elif estado == L:
                    self._pedir_limpieza(cama, ahora - timedelta(minutes=15 * (len(self._limpieza) + 1)))
        self._cola = []  # (episodio, paciente) que esperan cama
        for posicion, (nivel, doc, nombres, apellidos, sexo, motivo, minutos) in enumerate(_ESPERAN_CAMA, 1):
            llegada = ahora - timedelta(minutes=minutos)
            episodio = EpisodioEmergencia(posicion, posicion, motivo, EstadoEpisodio.EN_ESPERA, fecha_ingreso=llegada,
                                          triajes=[Triaje(posicion, nivel, 1, llegada)])
            self._cola.append((episodio, _paciente(posicion, doc, nombres, apellidos, sexo)))

    def _paciente_en_cama(self, cama, ahora):
        """Un paciente inventado, de un nivel compatible con la cama, que llegó hace un rato."""
        self._siguiente += 1
        n = self._siguiente - 400
        nombre, sexo = _NOMBRES[n % len(_NOMBRES)]
        llegada = ahora - timedelta(minutes=20 + 11 * n)
        episodio = EpisodioEmergencia(self._siguiente, self._siguiente, _MOTIVOS[n % len(_MOTIVOS)],
                                      EstadoEpisodio.EN_ATENCION, fecha_ingreso=llegada,
                                      triajes=[Triaje(self._siguiente, _NIVEL_POR_TIPO[type(cama)], 1, llegada)])
        paciente = _paciente(self._siguiente, ("DNI", f"{60000000 + n:08d}"), nombre,
                             _APELLIDOS[n % len(_APELLIDOS)], sexo)
        return episodio, paciente, llegada + timedelta(minutes=10)

    # ---- Consultas

    def mapa_camas(self):
        return list(self._camas)

    def cola_de_espera(self):
        pacientes = {episodio.id_episodio: paciente for episodio, paciente in self._cola}
        return [EntradaCola(posicion, episodio, pacientes[episodio.id_episodio])
                for posicion, episodio in enumerate(ordenar_por_prioridad([e for e, _ in self._cola]), start=1)]

    def pacientes_con_cama(self):
        return [PacienteEnCama(cama, *self._con_cama[cama.id_cama]) for cama in self._camas
                if cama.id_cama in self._con_cama]

    def camas_compatibles(self, id_episodio: int):
        episodio, _ = self._en_cola(id_episodio)
        return [cama for cama in self._camas
                if cama.estado == D and cama.es_compatible(episodio.nivel_actual)]

    def solicitudes_limpieza(self):
        return list(self._limpieza)

    def esperar_cama(self, episodio: EpisodioEmergencia, paciente: Paciente):
        """Lo que hace el primer triaje: el paciente pasa a la cola de cama."""
        self._cola.append((episodio, paciente))

    # ---- Ciclo de la cama

    def asignar(self, id_episodio: int, id_cama: int) -> int:
        episodio, paciente = self._en_cola(id_episodio)
        cama = self._cama(id_cama)
        if not cama.es_compatible(episodio.nivel_actual):
            raise ReglaNegocioError(f"La cama {cama.codigo} no es compatible con el nivel de triaje "
                                    f"{episodio.nivel_actual}.")
        cama.reservar()  # RN-05
        episodio.asignar_cama()  # RN-01
        self._cola.remove((episodio, paciente))
        self._con_cama[id_cama] = (episodio, paciente, self._ahora())
        self._siguiente += 1
        return self._siguiente

    def ocupar(self, id_cama: int):
        cama = self._cama(id_cama)
        if id_cama not in self._con_cama:
            raise ReglaNegocioError(f"La cama {cama.codigo} no tiene una asignación vigente: asígnela antes.")
        cama.ocupar()

    def cancelar_asignacion(self, id_episodio: int):
        cama, (episodio, paciente, _) = self._con_su_cama(id_episodio)
        cama.cancelar_reserva()  # una cama ocupada no se cancela: se da de alta
        episodio.cancelar_asignacion()
        del self._con_cama[cama.id_cama]
        self._cola.append((episodio, paciente))

    def dar_alta(self, id_episodio: int) -> int:
        cama, (episodio, _, _) = self._con_su_cama(id_episodio)
        cama.dar_alta()  # RN-07; una cama solo reservada no se da de alta
        episodio.dar_alta()
        del self._con_cama[cama.id_cama]
        return self._pedir_limpieza(cama)

    def referir(self, id_episodio: int):
        return self._cerrar_episodio(id_episodio, EpisodioEmergencia.referir)

    def registrar_fuga(self, id_episodio: int):
        return self._cerrar_episodio(id_episodio, EpisodioEmergencia.registrar_fuga)

    def _cerrar_episodio(self, id_episodio: int, cerrar):
        """Como el controlador: cierra el episodio y libera su cama, si tenía (reservada → libre; ocupada → limpieza)."""
        en_cola = next(((e, p) for e, p in self._cola if e.id_episodio == id_episodio), None)
        if en_cola is not None:
            cerrar(en_cola[0])
            self._cola.remove(en_cola)
            return None
        cama, (episodio, _, _) = self._con_su_cama(id_episodio)
        cerrar(episodio)
        del self._con_cama[cama.id_cama]
        if cama.estado == R:
            cama.cancelar_reserva()
            return None
        cama.dar_alta()
        return self._pedir_limpieza(cama)

    def confirmar_limpieza(self, id_solicitud: int):
        solicitud = next((s for s in self._limpieza if s.id_solicitud == id_solicitud), None)
        if solicitud is None:
            raise ReglaNegocioError("La solicitud de limpieza ya fue atendida.")
        self._cama(solicitud.id_cama).liberar_limpieza()  # RN-08
        self._limpieza.remove(solicitud)

    # ---- Mantenimiento

    def poner_fuera_de_servicio(self, id_cama: int, motivo: str):
        motivo = CamaController.validar_motivo(motivo)
        cama = self._cama(id_cama)
        if cama.estado == F:
            raise ReglaNegocioError(f"La cama {cama.codigo} ya está fuera de servicio.")
        if id_cama in self._con_cama:
            raise ReglaNegocioError(f"La cama {cama.codigo} tiene un paciente asignado: cancele la reserva o dé de "
                                    "alta antes.")
        if any(s.id_cama == id_cama for s in self._limpieza):
            raise ReglaNegocioError(f"La cama {cama.codigo} tiene una limpieza pendiente: confírmela antes.")
        cama.fuera_de_servicio()

    def volver_a_servicio(self, id_cama: int):
        self._cama(id_cama).volver_a_servicio()

    # ---- Ayudantes

    def _cama(self, id_cama: int):
        cama = next((c for c in self._camas if c.id_cama == id_cama), None)
        if cama is None:
            raise CamaNoDisponibleError("La cama no existe o está dada de baja.")
        return cama

    def _en_cola(self, id_episodio: int):
        en_cola = next(((e, p) for e, p in self._cola if e.id_episodio == id_episodio), None)
        if en_cola is None:
            raise ReglaNegocioError("No se puede asignar cama: el episodio ya no espera cama.")
        return en_cola

    def _con_su_cama(self, id_episodio: int):
        for id_cama, datos in self._con_cama.items():
            if datos[0].id_episodio == id_episodio:
                return self._cama(id_cama), datos
        raise ReglaNegocioError("El episodio no tiene una cama asignada.")

    def _pedir_limpieza(self, cama, desde: datetime | None = None) -> int:
        self._siguiente_solicitud += 1
        self._limpieza.append(SolicitudLimpieza(self._siguiente_solicitud, cama.id_cama, cama.codigo,
                                                desde or self._ahora()))
        return self._siguiente_solicitud


class TriajeDemo:
    """
    La cola de triaje y el triaje, con la estrategia real (Manchester) y el catálogo de síntomas del seed. Recuerda
    lo que se registra mientras la ventana está abierta: un paciente triado sale de la cola y, si hay
    `al_triar(episodio, paciente)` (p. ej. CamasDemo.esperar_cama), pasa a esperar cama.
    """

    def __init__(self, ahora=datetime.now, al_triar=None):
        self._ahora = ahora
        self._al_triar = al_triar
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
        triaje = Triaje(self._id_triaje + 1, sugerido, 1, self._ahora())
        if nivel_final is not None and nivel_final != sugerido:
            triaje.reclasificar(nivel_final, justificacion)  # RN-10, con la regla real
        entradas = self._entradas()
        triado = next(((e, p) for e, p in entradas if e.id_episodio == id_episodio), None)
        if triado is None:
            raise ReglaNegocioError("El episodio no existe o ya fue triado.")
        episodio, paciente = triado
        episodio.agregar_triaje(triaje)  # pasa a esperar cama, como en el modelo real
        entradas.remove(triado)
        self._id_triaje += 1
        if self._al_triar is not None:
            self._al_triar(episodio, paciente)
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
