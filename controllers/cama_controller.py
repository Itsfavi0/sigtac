from controllers.auth_controller import Sesion, exigir_permiso
from controllers.colas import EntradaCola, armar_cola
from dao.asignacion_dao import AsignacionDAO
from dao.auditoria_dao import AuditoriaDAO
from dao.cama_dao import CamaDAO
from dao.episodio_dao import EpisodioDAO
from dao.solicitud_limpieza_dao import SolicitudLimpiezaDAO
from dao.transaccion import transaccion
from models.asignacion import AsignacionCama, SolicitudLimpieza
from models.auditoria import AccionAuditoria
from models.cama import Cama
from models.estados import EstadoCama, EstadoEpisodio
from models.excepciones import CamaNoDisponibleError, ReglaNegocioError
from models.permisos import Permiso
from models.triaje import EpisodioEmergencia


class CamaController:
    """
    Gestión de camas: mapa y cola de espera (VER_CAMAS); asignar, ocupar, cancelar, dar de alta,
    referir, registrar una fuga y sacar o devolver una cama al servicio (GESTION_CAMAS); confirmar la
    limpieza (LIMPIEZA).

    Ciclo de una cama: DISPONIBLE → RESERVADA (asignar) → OCUPADA (el paciente llegó) → EN LIMPIEZA
    (alta, RN-07) → DISPONIBLE (limpieza confirmada, RN-08). Una reserva que no se usa vuelve a
    DISPONIBLE sin pasar por limpieza (cancelar). Fuera del ciclo: DISPONIBLE → FUERA DE SERVICIO
    (mantenimiento) → DISPONIBLE.

    Cada operación decide la transición en los modelos (Cama, EpisodioEmergencia) y la guarda en una
    transacción: los UPDATE condicionales de los DAO detectan si otra PC cambió la cama o el episodio
    entre la lectura y la escritura, y en ese caso se deshace todo.
    """

    def __init__(self, sesion: Sesion):
        self._sesion = sesion

    # ---- Consultas

    def mapa_camas(self) -> list[Cama]:
        """Todas las camas activas con su estado, ordenadas por área y código."""
        exigir_permiso(self._sesion, Permiso.VER_CAMAS)
        return CamaDAO.listar_activas()

    def cola_de_espera(self) -> list[EntradaCola]:
        """Pacientes con triaje que esperan cama, por prioridad (nivel y luego llegada)."""
        exigir_permiso(self._sesion, Permiso.VER_CAMAS)
        return armar_cola(EstadoEpisodio.EN_ESPERA)

    def camas_compatibles(self, id_episodio: int) -> list[Cama]:
        """
        Camas disponibles compatibles con el nivel de triaje actual del episodio (Cama.es_compatible).
        Lanza ReglaNegocioError si el episodio no tiene triaje (RN-01).
        """
        exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)
        episodio = self._cargar_episodio(id_episodio)
        nivel = self._exigir_nivel(episodio)
        return [cama for cama in CamaDAO.listar_disponibles() if cama.es_compatible(nivel)]

    def solicitudes_limpieza(self) -> list[SolicitudLimpieza]:
        """Bandeja del personal de limpieza: solicitudes pendientes, de la más antigua a la más reciente."""
        exigir_permiso(self._sesion, Permiso.LIMPIEZA)
        return SolicitudLimpiezaDAO.listar_pendientes()

    # ---- Ciclo de la cama

    def asignar(self, id_episodio: int, id_cama: int) -> int:
        """
        Reserva la cama para el episodio y devuelve el id de la asignación. Exige triaje activo
        (RN-01), cama disponible (RN-05) y compatible con el nivel del paciente.
        """
        sesion = exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)
        with transaccion():
            episodio = self._cargar_episodio(id_episodio)
            cama = self._cargar_cama(id_cama)
            anterior_ep, anterior_cama = episodio.estado, cama.estado
            episodio.asignar_cama()  # RN-01: en espera de cama y con triaje activo
            nivel = episodio.nivel_actual
            if not cama.es_compatible(nivel):
                raise ReglaNegocioError(f"La cama {cama.codigo} no es compatible con el nivel de triaje {nivel}.")
            cama.reservar()  # RN-05: solo una cama disponible
            EpisodioDAO.cambiar_estado(episodio, anterior_ep)
            CamaDAO.cambiar_estado(cama, anterior_cama)
            id_asignacion = AsignacionDAO.crear(id_episodio, id_cama, sesion.id_empleado)
            AuditoriaDAO.registrar(sesion.id_usuario, "asignacion_cama", AccionAuditoria.INSERT, id_asignacion,
                                   {"id_episodio": id_episodio, "id_cama": id_cama, "nivel": nivel})
        return id_asignacion

    def ocupar(self, id_cama: int) -> None:
        """El paciente llegó a la cama reservada: RESERVADA → OCUPADA."""
        sesion = exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)
        with transaccion():
            cama = self._cargar_cama(id_cama)
            if AsignacionDAO.buscar_vigente_por_cama(id_cama) is None:
                raise ReglaNegocioError(f"La cama {cama.codigo} no tiene una asignación vigente: asígnela antes.")
            anterior = cama.estado
            cama.ocupar()
            CamaDAO.cambiar_estado(cama, anterior)
            AuditoriaDAO.registrar(sesion.id_usuario, "cama", AccionAuditoria.UPDATE, id_cama,
                                   {"estado_anterior": anterior.value, "estado_nuevo": cama.estado.value})

    def cancelar_asignacion(self, id_episodio: int) -> None:
        """
        La cama reservada no llegó a usarse (asignación por error, el paciente necesita otra): la cama
        vuelve a DISPONIBLE sin limpieza, el episodio vuelve a la cola y la asignación se anula.
        Una cama ya ocupada no se cancela: se da de alta.
        """
        sesion = exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)
        with transaccion():
            episodio, asignacion, cama = self._cargar_asignacion(id_episodio)
            anterior_ep, anterior_cama = episodio.estado, cama.estado
            episodio.cancelar_asignacion()
            cama.cancelar_reserva()  # una cama OCUPADA lanza CamaEstadoInvalidoError
            EpisodioDAO.cambiar_estado(episodio, anterior_ep)
            CamaDAO.cambiar_estado(cama, anterior_cama)
            AsignacionDAO.anular(asignacion.id_asignacion)
            AuditoriaDAO.registrar(sesion.id_usuario, "asignacion_cama", AccionAuditoria.ANULAR,
                                   asignacion.id_asignacion, {"id_episodio": id_episodio, "id_cama": cama.id_cama})

    def dar_alta(self, id_episodio: int) -> int:
        """
        Alta médica: el episodio pasa a ALTA, la asignación se libera y la cama pasa a EN LIMPIEZA con
        una solicitud de limpieza (RN-07). Devuelve el id de la solicitud.
        """
        sesion = exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)
        with transaccion():
            episodio, asignacion, cama = self._cargar_asignacion(id_episodio)
            anterior_ep, anterior_cama = episodio.estado, cama.estado
            episodio.dar_alta()
            cama.dar_alta()  # RN-07; una cama solo reservada lanza CamaEstadoInvalidoError
            EpisodioDAO.cambiar_estado(episodio, anterior_ep)
            CamaDAO.cambiar_estado(cama, anterior_cama)
            AsignacionDAO.liberar(asignacion.id_asignacion)
            id_solicitud = SolicitudLimpiezaDAO.crear(cama.id_cama)
            AuditoriaDAO.registrar(sesion.id_usuario, "episodio_emergencia", AccionAuditoria.UPDATE, id_episodio, {
                "estado_anterior": anterior_ep.value, "estado_nuevo": episodio.estado.value,
                "id_cama": cama.id_cama, "id_solicitud_limpieza": id_solicitud,
            })
        return id_solicitud

    def referir(self, id_episodio: int) -> int | None:
        """
        El paciente se traslada a otro establecimiento: el episodio pasa a REFERIDO y, si tenía cama,
        se libera (ver _cerrar_episodio). Devuelve el id de la solicitud de limpieza, o None si no hizo falta.
        """
        return self._cerrar_episodio(id_episodio, EpisodioEmergencia.referir)

    def registrar_fuga(self, id_episodio: int) -> int | None:
        """
        El paciente se retiró sin alta médica: el episodio pasa a FUGADO / ABANDONO y, si tenía cama,
        se libera (ver _cerrar_episodio). Devuelve el id de la solicitud de limpieza, o None.
        """
        return self._cerrar_episodio(id_episodio, EpisodioEmergencia.registrar_fuga)

    def _cerrar_episodio(self, id_episodio: int, cerrar) -> int | None:
        """
        Cierra el episodio con `cerrar` (un método del modelo, que decide si se puede) y libera su cama:
        una cama solo reservada (el paciente no llegó a usarla) vuelve a DISPONIBLE y la asignación se
        anula, como al cancelar; una cama ocupada pasa a EN LIMPIEZA con su solicitud (RN-07), como en el alta.
        """
        sesion = exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)
        with transaccion():
            episodio = self._cargar_episodio(id_episodio)
            asignacion = AsignacionDAO.buscar_vigente_por_episodio(id_episodio)
            cama = self._cargar_cama(asignacion.id_cama) if asignacion else None
            anterior_ep = episodio.estado
            cerrar(episodio)
            detalles = {"estado_anterior": anterior_ep.value, "estado_nuevo": episodio.estado.value}
            EpisodioDAO.cambiar_estado(episodio, anterior_ep)
            id_solicitud = None
            if cama is not None:
                anterior_cama = cama.estado
                if anterior_cama == EstadoCama.RESERVADA:
                    cama.cancelar_reserva()
                    CamaDAO.cambiar_estado(cama, anterior_cama)
                    AsignacionDAO.anular(asignacion.id_asignacion)
                else:
                    cama.dar_alta()  # OCUPADA → EN LIMPIEZA (RN-07); otro estado lanza CamaEstadoInvalidoError
                    CamaDAO.cambiar_estado(cama, anterior_cama)
                    AsignacionDAO.liberar(asignacion.id_asignacion)
                    id_solicitud = SolicitudLimpiezaDAO.crear(cama.id_cama)
                detalles.update(id_cama=cama.id_cama, id_solicitud_limpieza=id_solicitud)
            AuditoriaDAO.registrar(sesion.id_usuario, "episodio_emergencia", AccionAuditoria.UPDATE, id_episodio,
                                   detalles)
        return id_solicitud

    def confirmar_limpieza(self, id_solicitud: int) -> None:
        """RN-08: el personal de limpieza confirma que la cama está lista: EN LIMPIEZA → DISPONIBLE."""
        sesion = exigir_permiso(self._sesion, Permiso.LIMPIEZA)
        with transaccion():
            solicitud = SolicitudLimpiezaDAO.buscar_por_id(id_solicitud)
            if solicitud is None:
                raise ReglaNegocioError("La solicitud de limpieza no existe.")
            if not solicitud.pendiente:
                raise ReglaNegocioError("La solicitud de limpieza ya fue atendida.")
            cama = self._cargar_cama(solicitud.id_cama)
            anterior = cama.estado
            cama.liberar_limpieza()
            SolicitudLimpiezaDAO.atender(id_solicitud, sesion.id_empleado)
            CamaDAO.cambiar_estado(cama, anterior)
            AuditoriaDAO.registrar(sesion.id_usuario, "solicitud_limpieza", AccionAuditoria.UPDATE, id_solicitud,
                                   {"id_cama": cama.id_cama})

    # ---- Mantenimiento

    MAX_MOTIVO = 200

    def poner_fuera_de_servicio(self, id_cama: int, motivo: str) -> None:
        """
        Saca la cama de circulación (equipo dañado, mantenimiento). El motivo es obligatorio y queda en
        la bitácora: debe describir la cama o el equipo, no al paciente.

        El modelo admite decretarlo desde cualquier estado, pero aquí se exige que la cama no tenga un
        paciente asignado ni una limpieza pendiente: si no, la asignación o la solicitud quedarían
        abiertas sobre una cama fuera de servicio. Primero se cancela la reserva, se da de alta o se
        confirma la limpieza.
        """
        sesion = exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)
        motivo = self._validar_motivo(motivo)
        with transaccion():
            cama = self._cargar_cama(id_cama)
            if cama.estado == EstadoCama.FUERA_SERVICIO:
                raise ReglaNegocioError(f"La cama {cama.codigo} ya está fuera de servicio.")
            if AsignacionDAO.buscar_vigente_por_cama(id_cama) is not None:
                raise ReglaNegocioError(
                    f"La cama {cama.codigo} tiene un paciente asignado: cancele la reserva o dé de alta antes."
                )
            if SolicitudLimpiezaDAO.buscar_pendiente_por_cama(id_cama) is not None:
                raise ReglaNegocioError(f"La cama {cama.codigo} tiene una limpieza pendiente: confírmela antes.")
            anterior = cama.estado
            cama.fuera_de_servicio()
            CamaDAO.cambiar_estado(cama, anterior)
            AuditoriaDAO.registrar(sesion.id_usuario, "cama", AccionAuditoria.UPDATE, id_cama, {
                "estado_anterior": anterior.value, "estado_nuevo": cama.estado.value, "motivo": motivo,
            })

    def volver_a_servicio(self, id_cama: int) -> None:
        """El mantenimiento terminó: FUERA DE SERVICIO → DISPONIBLE."""
        sesion = exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)
        with transaccion():
            cama = self._cargar_cama(id_cama)
            anterior = cama.estado
            cama.volver_a_servicio()  # CamaEstadoInvalidoError si no estaba fuera de servicio
            CamaDAO.cambiar_estado(cama, anterior)
            AuditoriaDAO.registrar(sesion.id_usuario, "cama", AccionAuditoria.UPDATE, id_cama,
                                   {"estado_anterior": anterior.value, "estado_nuevo": cama.estado.value})

    @classmethod
    def _validar_motivo(cls, motivo) -> str:
        if not isinstance(motivo, str) or not motivo.strip():
            raise ValueError("El motivo es obligatorio.")
        if len(motivo.strip()) > cls.MAX_MOTIVO:
            raise ValueError(f"El motivo no puede superar los {cls.MAX_MOTIVO} caracteres.")
        return motivo.strip()

    # ---- Ayudantes

    @staticmethod
    def _cargar_episodio(id_episodio: int) -> EpisodioEmergencia:
        episodio = EpisodioDAO.buscar_por_id(id_episodio)
        if episodio is None or not episodio.activo:
            raise ReglaNegocioError("El episodio no existe o está anulado.")
        return episodio

    @staticmethod
    def _cargar_cama(id_cama: int) -> Cama:
        cama = CamaDAO.buscar_por_id(id_cama)
        if cama is None:
            raise CamaNoDisponibleError("La cama no existe o está dada de baja.")
        return cama

    @classmethod
    def _cargar_asignacion(cls, id_episodio: int) -> tuple[EpisodioEmergencia, AsignacionCama, Cama]:
        """El episodio, su asignación vigente y la cama asignada."""
        episodio = cls._cargar_episodio(id_episodio)
        asignacion = AsignacionDAO.buscar_vigente_por_episodio(id_episodio)
        if asignacion is None:
            raise ReglaNegocioError("El episodio no tiene una cama asignada.")
        return episodio, asignacion, cls._cargar_cama(asignacion.id_cama)

    @staticmethod
    def _exigir_nivel(episodio: EpisodioEmergencia) -> int:
        nivel = episodio.nivel_actual
        if nivel is None:
            raise ReglaNegocioError("El episodio no tiene un triaje activo (RN-01).")
        return nivel
