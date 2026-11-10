"""
Administración (permiso ADMINISTRACION): cuentas de usuario, bitácora de auditoría y baja o reactivación de pacientes.
Una tarjeta con «Cuentas (N) / Nueva cuenta (N) / Bitácora / Pacientes», como Gestión de camas.

- «Cuentas»: desactivar o activar, desbloquear, cambiar el rol y restablecer la clave de la cuenta elegida. Todo se
  deshace (activar ↔ desactivar), así que nada pide confirmación; ninguna acción es la principal.
- «Nueva cuenta»: un empleado activo sin cuenta, su rol y su clave.
- «Bitácora»: quién hizo qué y cuándo, en un período (CamposPeriodo, como Reportes) y con filtros por tabla y usuario.
- «Pacientes»: buscar por documento y dar de baja o reactivar (RN-11). Muestra solo nombre, documento y estado: el
  administrador no atiende pacientes. Un paciente sin identificar (NN) no tiene documento: no se busca aquí.

Las reglas (no modificarse a sí mismo, la política de claves, un paciente con episodio abierto) son de los
controladores; la pantalla muestra sus mensajes. Que las dos claves escritas coincidan sí es de la pantalla: es la
forma de escribir una clave sin verla.
"""
import hashlib
import logging
from collections import Counter
from collections.abc import Callable
from datetime import date, datetime

import customtkinter as ctk

from models.auditoria import AccionAuditoria
from models.excepciones import SigtacError
from models.permisos import Rol
from views import formato, tema
from views.componentes import (BotonPrimario, BotonSecundario, CamposDocumento, CamposPeriodo, Desplazable, Selector,
                               TablaDatos, Tarjeta, fila_acciones, lista_opciones, marcar_error, mostrar_error,
                               mostrar_info)
from views.componentes.campos import celda, campo_texto, leer_opcion, lista_en_rejilla
from views.componentes.documento import ETIQUETAS
from views.componentes.periodo import texto_periodo

logger = logging.getLogger(__name__)

TITULOS = {
    "cuentas": ("Cuentas de usuario", "Rol, acceso y clave de cada empleado"),
    "nueva": ("Nueva cuenta", "Empleados activos que aún no tienen cuenta"),
    "bitacora": ("Bitácora de auditoría", "Quién hizo qué y cuándo, de lo más reciente a lo más antiguo"),
    "pacientes": ("Baja y reactivación de pacientes", "Registros duplicados o dados de baja por error (RN-11)"),
}
SIN_CUENTAS = "No hay cuentas registradas."
SIN_EMPLEADOS = "Todos los empleados activos tienen cuenta."
SIN_REGISTROS = "No hay registros en este período."
ELIJA_CUENTA = "Elija una cuenta de la lista para cambiarla."
CUENTA_PROPIA = "Su cuenta: otro administrador puede desactivarla o cambiar su rol."
TEXTO_ELEGIR_EMPLEADO = "Elija un empleado de la lista"   # el botón deshabilitado dice por qué no responde
CLAVES_DISTINTAS = "Las dos claves no coinciden."
FALTA_ROL = "Elija el rol de la cuenta."
AVISO_BUSCAR = "Escriba el documento y busque al paciente."   # el mismo texto que Pacientes
NO_ENCONTRADO = "No hay un paciente con ese documento."
TODAS, TODOS = "Todas", "Todos"
LIMITE_BITACORA = 200  # el tope que pide la pantalla (AuditoriaDAO admite hasta 1000)
# Cómo se lee cada acción de la bitácora
ACCIONES = {AccionAuditoria.INSERT: "Creación", AccionAuditoria.UPDATE: "Cambio", AccionAuditoria.ANULAR: "Baja",
            AccionAuditoria.REACTIVAR: "Reactivación", AccionAuditoria.IDENTIFICAR: "Identificación",
            AccionAuditoria.FUSIONAR: "Fusión"}


def estado_cuenta(cuenta) -> str:
    """Desactivada pesa más que bloqueada: una cuenta desactivada no entra aunque se desbloquee."""
    if not cuenta.activo:
        return "Desactivada"
    return "Bloqueada" if cuenta.bloqueada else "Activa"


def nombres_de_cuentas(cuentas) -> dict[int, str]:
    """
    id_usuario → el nombre con que la pantalla nombra a cada cuenta (columna y filtro de la bitácora). Dos empleados
    con el mismo nombre se distinguen por el número de su cuenta.
    """
    repetidos = Counter(c.nombre_completo for c in cuentas)
    return {c.id_usuario: c.nombre_completo if repetidos[c.nombre_completo] == 1
            else f"{c.nombre_completo} (cuenta {c.id_usuario})" for c in cuentas}


# Las tablas cuyo nombre no se lee bien con solo cambiar «_» por un espacio (tildes y «de»)
NOMBRES_TABLA = {"area": "Área", "asignacion_cama": "Asignación de cama",
                 "episodio_emergencia": "Episodio de emergencia", "estado_cama": "Estado de cama",
                 "estado_episodio": "Estado de episodio",
                 "historial_estado_cama": "Historial de estados de cama", "nivel_triaje": "Nivel de triaje",
                 "sintoma": "Síntoma", "solicitud_limpieza": "Solicitud de limpieza", "tipo_cama": "Tipo de cama",
                 "tipo_documento": "Tipo de documento", "triaje_sintoma": "Síntomas del triaje"}


def texto_tabla(tabla: str) -> str:
    """«episodio_emergencia» → «Episodio de emergencia»; «signos_vitales» → «Signos vitales»."""
    return NOMBRES_TABLA.get(tabla, tabla.replace("_", " ").capitalize())


def texto_detalles(detalles: dict | None) -> str:
    """{"rol_anterior": "Médico", "activo": False} → «rol anterior: Médico · activo: no»."""
    if not detalles:
        return ""

    def valor(v):
        if isinstance(v, bool):
            return "sí" if v else "no"
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return str(v)

    return " · ".join(f"{clave.replace('_', ' ')}: {valor(v)}" for clave, v in detalles.items())


def fecha_hora(momento: datetime) -> str:
    return f"{formato.fecha_numerica(momento.date())} {formato.hora(momento)}"


class CamposClave:
    """
    La clave y su repetición, ocultas (como en el login), con el aviso del formulario debajo. Una clave rechazada (no
    coinciden o no cumple la política) queda marcada hasta que lo escrito cambia. De lo rechazado se guarda solo un
    resumen (SHA-256) para saber si cambió: la clave no queda en ningún atributo, mensaje ni registro.
    """

    def __init__(self, rejilla, fila: int, columna: int, aviso_padre):
        self.clave = campo_texto(celda(rejilla, "Clave", fila, columna), show="•")
        self.clave.pack(fill="x")
        self.repetir = campo_texto(celda(rejilla, "Repetir la clave", fila, columna + 1), show="•")
        self.repetir.pack(fill="x")
        # `antes`: el widget sobre el que se coloca el aviso (la fila de botones), si el formulario sigue debajo
        self.aviso = ctk.CTkLabel(aviso_padre, text="", font=tema.fuente("pequena"), text_color=tema.COLOR_ERROR,
                                  anchor="w", justify="left")
        self.antes = None
        self._rechazado = None
        for campo in self.entradas:
            campo.bind("<KeyRelease>", lambda _e: self._editada(), add="+")

    @property
    def entradas(self):
        return self.clave, self.repetir

    def leer(self) -> str:
        """La clave, si las dos coinciden. Si no, marca la repetición y lanza ValueError (sin la clave)."""
        if self.clave.get() != self.repetir.get():
            self.rechazar(CLAVES_DISTINTAS, self.repetir)
            raise ValueError(CLAVES_DISTINTAS)
        return self.clave.get()

    def rechazar(self, mensaje: str, campo=None):
        """Marca el campo culpable (la clave, si no se dice) y explica debajo por qué."""
        marcar_error(campo or self.clave)
        self._rechazado = self._resumen()
        self.avisar(mensaje)

    def avisar(self, mensaje: str):
        self.aviso.configure(text=mensaje)
        posicion = {} if self.antes is None else {"before": self.antes}
        self.aviso.pack(anchor="w", pady=(tema.ESPACIO, 0), **posicion)

    def ocultar_aviso(self):
        self.aviso.configure(text="")
        self.aviso.pack_forget()

    def limpiar(self):
        for campo in self.entradas:
            campo.delete(0, "end")
        self._quitar_rechazo()

    def _resumen(self) -> str:
        return hashlib.sha256("\0".join(c.get() for c in self.entradas).encode("utf-8")).hexdigest()

    def _editada(self):
        if self._rechazado is not None and self._resumen() != self._rechazado:
            self._quitar_rechazo()

    def _quitar_rechazo(self):
        self._rechazado = None
        for campo in self.entradas:
            marcar_error(campo, False)
        self.ocultar_aviso()


class AdminView(ctk.CTkFrame):
    FILAS_LISTA = 6        # filas visibles de cada lista (más se desplazan dentro de la tabla)
    FILAS_BITACORA = 8
    # Caben en la tarjeta a 1093×614 sin desplazamiento horizontal (brief, «Espacio útil»). El detalle completo del
    # registro elegido se lee bajo la tabla
    COLUMNAS_CUENTAS = (("Empleado", 224), ("Cargo", 176), ("Rol", 176), ("Estado", 112))
    COLUMNAS_EMPLEADOS = (("Empleado", 224), ("Cargo", 176))
    COLUMNAS_BITACORA = (("Fecha y hora", 128), ("Usuario", 176), ("Acción", 112), ("Tabla", 144),
                         ("Registro", 72), ("Detalle", 128))

    def __init__(self, padre, admin, pacientes, hoy: Callable[[], date] = date.today,
                 id_usuario_propio: int | None = None):
        """`id_usuario_propio`: la cuenta de la sesión, para no ofrecer lo que el controlador le va a rechazar."""
        super().__init__(padre, fg_color="transparent")
        self._admin, self._pacientes, self._hoy = admin, pacientes, hoy
        self._id_propio = id_usuario_propio
        self._cuentas = {}       # id_usuario → CuentaUsuario
        self._nombres = {}       # id_usuario → nombre en la bitácora y su filtro
        self._empleados = {}     # id_empleado → {"nombres", "apellidos", "nombre_cargo"}
        self._usuarios = {}      # texto del filtro → id_usuario
        self._tablas = {}        # texto del filtro → nombre de la tabla
        self._cuenta_mostrada = None  # id_usuario de la cuenta cuyos datos se muestran (para vaciar la clave al cambiar)
        self._paciente = None    # el paciente encontrado en «Pacientes»
        self._buscado = None     # (tipo, número) que se buscó: el resultado es de él
        self._documento_rechazado = None

        # Como las demás pantallas de trabajo: la tarjeta se desplaza en vertical si no cabe (1093×614)
        self._contenido = contenido = Desplazable(self)
        contenido.pack(fill="both", expand=True)
        self._tarjeta = Tarjeta(contenido, *TITULOS["cuentas"])
        self._tarjeta.pack(fill="x")
        self._modo = Selector(self._tarjeta.cabecera, [("cuentas", "Cuentas"), ("nueva", "Nueva cuenta"),
                                                       ("bitacora", "Bitácora"), ("pacientes", "Pacientes")],
                              self._cambiar_modo)
        self._modo.pack(side="right")
        cuerpo = ctk.CTkFrame(self._tarjeta, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))

        self._paneles = {"cuentas": self._crear_cuentas(cuerpo), "nueva": self._crear_nueva(cuerpo),
                         "bitacora": self._crear_bitacora(cuerpo), "pacientes": self._crear_pacientes(cuerpo)}
        self._paneles["cuentas"].pack(fill="x")
        self._cargar_datos()

    # ---- Cuentas

    def _crear_cuentas(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        self._tabla_cuentas = TablaDatos(marco, self.COLUMNAS_CUENTAS, SIN_CUENTAS,
                                         al_seleccionar=lambda _id: self._cuenta_elegida(), filas=self.FILAS_LISTA)
        self._tabla_cuentas.pack(fill="x")
        self._cuenta_titulo = ctk.CTkLabel(marco, text=ELIJA_CUENTA, font=tema.fuente("fuerte"),
                                           text_color=tema.COLOR_TEXTO, anchor="w")
        self._cuenta_titulo.pack(anchor="w", pady=(tema.ESPACIO_2, 0))

        fila = fila_acciones(marco)
        self._boton_acceso = BotonSecundario(fila, "Desactivar", self.cambiar_acceso, state="disabled")
        self._boton_acceso.pack(side="left")
        self._boton_desbloquear = BotonSecundario(fila, "Desbloquear", self.desbloquear, state="disabled")
        self._boton_desbloquear.pack(side="left", padx=(tema.ESPACIO, 0))

        # El rol y la clave en la rejilla de 3 del triaje; el botón de cada fila, junto a sus campos
        rejilla = ctk.CTkFrame(marco, fg_color="transparent")
        rejilla.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        rejilla.grid_columnconfigure((0, 1, 2), weight=1, uniform="cuenta")
        self._rol = lista_en_rejilla(rejilla, "Rol", [r.value for r in Rol], 0, 0)
        self._rol.configure(command=lambda _valor: self._actualizar_boton_rol())
        self._boton_rol = BotonSecundario(rejilla, "Cambiar rol", self.cambiar_rol, state="disabled")
        self._boton_rol.grid(row=0, column=1, sticky="sw", padx=(tema.ESPACIO, 0))
        self._clave_cuenta = CamposClave(rejilla, 1, 0, marco)
        self._boton_clave = BotonSecundario(rejilla, "Restablecer clave", self.restablecer_clave, state="disabled")
        self._boton_clave.grid(row=1, column=2, sticky="sw", padx=(tema.ESPACIO, 0))
        for campo in self._clave_cuenta.entradas:
            campo.bind("<Return>", self.restablecer_clave, add="+")
        return marco

    def _elegida(self):
        return self._cuentas.get(self._tabla_cuentas.seleccionado())

    def _cuenta_elegida(self):
        cuenta = self._elegida()
        nueva = None if cuenta is None else cuenta.id_usuario
        if nueva != self._cuenta_mostrada:
            # Una clave escrita para una cuenta no se aplica por error a otra
            self._clave_cuenta.limpiar()
            self._cuenta_mostrada = nueva
        for boton in (self._boton_acceso, self._boton_clave):
            boton.configure(state="normal" if cuenta is not None else "disabled")
        # La lista muestra el rol de la cuenta; sin cuenta, vacía y deshabilitada (se escribe habilitada)
        self._rol.configure(state="readonly")
        self._rol.set("" if cuenta is None else cuenta.rol.value)
        if cuenta is None:
            self._rol.configure(state="disabled")
            self._cuenta_titulo.configure(text=ELIJA_CUENTA)
            self._boton_acceso.configure(text="Desactivar")
            self._boton_desbloquear.configure(state="disabled")
        else:
            propia = cuenta.id_usuario == self._id_propio
            # La propia cuenta no se desactiva ni cambia de rol (lo decide AdminController): lo dice el título
            self._cuenta_titulo.configure(text=CUENTA_PROPIA if propia else f"Cuenta de {cuenta.nombre_completo}")
            self._boton_acceso.configure(text="Desactivar" if cuenta.activo else "Activar",
                                         state="disabled" if propia else "normal")
            # Desbloquear sirve también para borrar intentos fallidos que aún no llegan al bloqueo
            bloqueo = cuenta.bloqueada or cuenta.intentos_fallidos > 0
            self._boton_desbloquear.configure(state="normal" if bloqueo else "disabled")
        self._actualizar_boton_rol()

    def _actualizar_boton_rol(self):
        """«Cambiar rol» solo responde si el rol elegido en la lista es otro que el de la cuenta (y no es la propia)."""
        cuenta = self._elegida()
        distinto = cuenta is not None and self._rol.get() not in ("", cuenta.rol.value)
        propia = cuenta is not None and cuenta.id_usuario == self._id_propio
        self._boton_rol.configure(state="normal" if distinto and not propia else "disabled")

    def cambiar_acceso(self):
        """Desactiva la cuenta (deja de poder iniciar sesión) o la vuelve a activar."""
        cuenta = self._elegida()
        if cuenta is None:
            return
        quien = formato.abreviar(cuenta.nombres, cuenta.apellidos)
        if cuenta.activo:
            self._operar(lambda: self._admin.desactivar(cuenta.id_usuario),
                         f"Cuenta de {quien} desactivada: ya no puede iniciar sesión.")
        else:
            self._operar(lambda: self._admin.activar(cuenta.id_usuario),
                         f"Cuenta de {quien} activada: ya puede iniciar sesión.")

    def desbloquear(self):
        cuenta = self._elegida()
        if cuenta is not None:
            self._operar(lambda: self._admin.desbloquear(cuenta.id_usuario),
                         f"Cuenta de {formato.abreviar(cuenta.nombres, cuenta.apellidos)} desbloqueada.")

    def cambiar_rol(self):
        cuenta = self._elegida()
        if cuenta is not None:
            rol = self._rol.get()
            self._operar(lambda: self._admin.cambiar_rol(cuenta.id_usuario, rol),
                         f"{formato.abreviar(cuenta.nombres, cuenta.apellidos)} ahora tiene el rol {rol}.")

    def restablecer_clave(self, _evento=None):
        """La clave nueva (p. ej. si el empleado la olvidó). También quita el bloqueo por intentos fallidos."""
        cuenta = self._elegida()
        if cuenta is None:
            return "break"
        try:
            clave = self._clave_cuenta.leer()
            self._admin.restablecer_clave(cuenta.id_usuario, clave)
        except ValueError as error:
            if str(error) != CLAVES_DISTINTAS:
                self._clave_cuenta.rechazar(str(error))  # la política de claves
            return "break"
        except SigtacError as error:
            mostrar_error(self, error)
            self._recargar(conservar=True)
            return "break"
        self._clave_cuenta.limpiar()
        self._recargar(conservar=True)
        mostrar_info(self, f"Clave de {formato.abreviar(cuenta.nombres, cuenta.apellidos)} restablecida. "
                           "Entréguesela en persona.")
        return "break"

    # ---- Nueva cuenta

    def _crear_nueva(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        self._tabla_empleados = TablaDatos(marco, self.COLUMNAS_EMPLEADOS, SIN_EMPLEADOS,
                                           al_seleccionar=lambda _id: self._empleado_elegido(), filas=self.FILAS_LISTA)
        self._tabla_empleados.pack(fill="x")
        rejilla = ctk.CTkFrame(marco, fg_color="transparent")
        rejilla.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        rejilla.grid_columnconfigure((0, 1, 2), weight=1, uniform="nueva")
        # El rol empieza sin elegir: uno por omisión daría permisos que nadie decidió
        self._rol_nuevo = lista_en_rejilla(rejilla, "Rol", [r.value for r in Rol], 0, 0)
        self._rol_nuevo.configure(command=lambda _valor: self._rol_nuevo_elegido())
        self._clave_nueva = CamposClave(rejilla, 0, 1, marco)
        for campo in self._clave_nueva.entradas:
            campo.bind("<Return>", self.crear_cuenta, add="+")
        fila = fila_acciones(marco)
        self._clave_nueva.antes = fila  # el aviso, entre la rejilla y el botón
        self._boton_crear = BotonPrimario(fila, TEXTO_ELEGIR_EMPLEADO, self.crear_cuenta, state="disabled")
        self._boton_crear.pack(side="left")
        return marco

    def _empleado(self):
        return self._empleados.get(self._tabla_empleados.seleccionado())

    def _empleado_elegido(self):
        empleado = self._empleado()
        if empleado is None:
            self._boton_crear.configure(text=TEXTO_ELEGIR_EMPLEADO, state="disabled")
        else:
            nombre = formato.abreviar(empleado["nombres"], empleado["apellidos"])
            self._boton_crear.configure(text=f"Crear cuenta para {nombre}", state="normal")

    def _rol_nuevo_elegido(self):
        """Elegir el rol corrige la falta de rol: se van su borde rojo y su aviso."""
        marcar_error(self._rol_nuevo, False)
        if self._clave_nueva.aviso.cget("text") == FALTA_ROL:
            self._clave_nueva.ocultar_aviso()

    def crear_cuenta(self, _evento=None):
        id_empleado = self._tabla_empleados.seleccionado()
        if self._empleado() is None:
            return "break"
        try:
            rol = leer_opcion(self._rol_nuevo, {r.value: r for r in Rol}, FALTA_ROL)  # marca la lista
        except ValueError as error:
            self._clave_nueva.avisar(str(error))
            return "break"
        try:
            clave = self._clave_nueva.leer()
            cuenta = self._admin.crear_cuenta(id_empleado, rol, clave)
        except ValueError as error:
            if str(error) != CLAVES_DISTINTAS:
                self._clave_nueva.rechazar(str(error))  # la política de claves
            return "break"
        except SigtacError as error:
            mostrar_error(self, error)  # p. ej. otra PC ya le creó la cuenta: la lista recargada lo muestra
            self._recargar(conservar=True)
            return "break"
        self._clave_nueva.limpiar()
        self._rol_nuevo.set("")
        self._recargar()
        mostrar_info(self, f"Cuenta creada para {cuenta.nombre_completo} con el rol {cuenta.rol.value}. "
                           "Entréguele la clave en persona.")
        return "break"

    # ---- Bitácora

    def _crear_bitacora(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        # Los atajos en su fila (la cabecera ya tiene el selector de la pantalla); al abrir, hoy. Las fechas y los dos
        # filtros comparten la rejilla de 4
        self.periodo = CamposPeriodo(marco, lambda: self.ver_bitacora(), hoy=self._hoy, inicial="hoy", columnas=4)
        self.periodo.pack(fill="x")
        self._filtro_tabla = lista_opciones(celda(self.periodo.rejilla, "Tabla", 0, 2), [TODAS])
        self._filtro_tabla.pack(fill="x")
        self._filtro_usuario = lista_opciones(celda(self.periodo.rejilla, "Usuario", 0, 3), [TODOS])
        self._filtro_usuario.pack(fill="x")
        for campo in self.periodo.entradas:
            campo.bind("<Return>", self.ver_bitacora, add="+")
        fila = fila_acciones(marco)
        BotonPrimario(fila, "Ver bitácora", self.ver_bitacora).pack(side="left")
        self._registros = {}  # id_bitacora → registro, para mostrar el detalle completo del elegido
        self._tabla_bitacora = TablaDatos(marco, self.COLUMNAS_BITACORA, SIN_REGISTROS, filas=self.FILAS_BITACORA,
                                          al_seleccionar=self._registro_elegido)
        self._tabla_bitacora.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        self._resumen_bitacora = ctk.CTkLabel(marco, text="", font=tema.fuente("pequena"),
                                              text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        self._resumen_bitacora.pack(anchor="w", pady=(tema.ESPACIO, 0))
        # La columna «Detalle» corta los textos largos: el del registro elegido se lee completo aquí, partido al ancho
        # de la tabla (como los criterios del triaje). Solo ocupa lugar cuando tiene texto
        self._detalle_elegido = ctk.CTkLabel(marco, text="", font=tema.fuente("normal"), text_color=tema.COLOR_TEXTO,
                                             anchor="w", justify="left",
                                             wraplength=sum(ancho for _, ancho in self.COLUMNAS_BITACORA))
        return marco

    def _registro_elegido(self, id_bitacora):
        registro = self._registros.get(id_bitacora)
        detalle = texto_detalles(registro["detalles"]) if registro else ""
        if detalle:
            self._detalle_elegido.configure(text=f"Detalle: {detalle}")
            self._detalle_elegido.pack(anchor="w", pady=(tema.ESPACIO, 0))
        else:
            self._detalle_elegido.configure(text="")
            self._detalle_elegido.pack_forget()

    def ver_bitacora(self, _evento=None, avisar_error: bool = True):
        """Los registros del período y los filtros, del más reciente al más antiguo (como mucho LIMITE_BITACORA)."""
        try:
            desde, hasta = self.periodo.leer()
        except ValueError as error:
            if avisar_error:
                mostrar_error(self, error)
            return "break"
        try:
            registros = self._admin.bitacora(desde, hasta, tabla=self._tablas.get(self._filtro_tabla.get()),
                                             id_usuario=self._usuarios.get(self._filtro_usuario.get()),
                                             limite=LIMITE_BITACORA)
        except (SigtacError, ValueError) as error:
            if isinstance(error, ValueError):
                self.periodo.rechazar()  # la inicial después de la final, un año fuera de rango
            else:
                logger.warning("No se pudo leer la bitácora (%s).", type(error).__name__)
                if not self._registros:
                    self._tabla_bitacora.sin_lectura()  # no decir «no hay registros»
            if avisar_error:
                mostrar_error(self, error)
            return "break"
        self._mostrar_bitacora(registros, desde, hasta)
        return "break"

    def _mostrar_bitacora(self, registros, desde: date, hasta: date):
        self._registros = {r["id_bitacora"]: r for r in registros}
        self._registro_elegido(None)
        self._tabla_bitacora.cargar([(r["id_bitacora"], (
            fecha_hora(r["fecha_hora"]), self._nombres.get(r["id_usuario"], f"Cuenta {r['id_usuario']}"),
            ACCIONES.get(r["accion"], str(r["accion"])), texto_tabla(r["tabla_afectada"]),
            r["id_registro_afectado"], texto_detalles(r["detalles"]))) for r in registros])
        periodo = texto_periodo(desde, hasta)
        if len(registros) >= LIMITE_BITACORA:
            texto = (f"{periodo}: se muestran los {LIMITE_BITACORA} registros más recientes. Acote el período o los "
                     "filtros para ver los demás.")
        else:
            texto = f"{periodo}: {len(registros)} {'registro' if len(registros) == 1 else 'registros'}."
        self._resumen_bitacora.configure(text=texto)

    def _cargar_filtros(self, tablas: list[str]):
        """Las opciones de los filtros: las tablas auditables y las cuentas. Se conserva lo elegido si sigue."""
        self._tablas = {texto_tabla(t): t for t in tablas}
        self._usuarios = {nombre: id_usuario for id_usuario, nombre in self._nombres.items()}
        for lista, todas, opciones in ((self._filtro_tabla, TODAS, self._tablas),
                                       (self._filtro_usuario, TODOS, self._usuarios)):
            elegido = lista.get()
            lista.configure(values=[todas, *opciones])
            lista.set(elegido if elegido in opciones else todas)

    # ---- Pacientes

    def _crear_pacientes(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        fila = ctk.CTkFrame(marco, fg_color="transparent")
        fila.pack(fill="x")
        self._documento = CamposDocumento(fila)
        self._documento.pack(side="left", fill="x", expand=True)
        BotonSecundario(fila, "Buscar", self.buscar_paciente).pack(side="left", anchor="s", padx=(tema.ESPACIO, 0))
        self._documento.campo_numero.bind("<Return>", self.buscar_paciente, add="+")
        self._documento.campo_numero.bind("<KeyRelease>", lambda _e: self._documento_editado(), add="+")
        self._documento.al_cambiar_tipo(self._documento_editado)  # otro tipo también es otro documento
        self._aviso_paciente = ctk.CTkLabel(marco, text=AVISO_BUSCAR, font=tema.fuente("pequena"),
                                            text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w", justify="left")
        self._aviso_paciente.pack(fill="x", pady=(tema.ESPACIO_2, 0))

        self._encontrado = ctk.CTkFrame(marco, fg_color="transparent")
        self._nombre_paciente = ctk.CTkLabel(self._encontrado, text="", font=tema.fuente("fuerte"),
                                             text_color=tema.COLOR_TEXTO, anchor="w")
        self._nombre_paciente.pack(anchor="w")
        self._datos_paciente = ctk.CTkLabel(self._encontrado, text="", font=tema.fuente("pequena"),
                                            text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        self._datos_paciente.pack(anchor="w")
        fila = fila_acciones(self._encontrado)
        self._boton_paciente = BotonPrimario(fila, "Dar de baja", self.cambiar_paciente)
        self._boton_paciente.pack(side="left")
        return marco

    def buscar_paciente(self, _evento=None):
        tipo, numero = self._documento.valores()
        try:
            paciente = self._pacientes.buscar_para_administrar(tipo.value, numero)
        except ValueError as error:
            # Un documento mal escrito: borde rojo y la explicación debajo, sin diálogo (como en Pacientes)
            marcar_error(self._documento.campo_numero)
            self._documento_rechazado = (tipo, numero)
            self._buscado = None
            self._mostrar_paciente(None, str(error), error=True)
            return "break"
        except SigtacError as error:
            mostrar_error(self, error)  # la BD no respondió: no es culpa del documento
            return "break"
        marcar_error(self._documento.campo_numero, False)
        self._documento_rechazado = None
        self._buscado = (tipo, numero.strip())
        self._mostrar_paciente(paciente, NO_ENCONTRADO if paciente is None else "")
        return "break"

    def _mostrar_paciente(self, paciente, aviso: str, error: bool = False):
        self._paciente = paciente
        if paciente is None:
            self._encontrado.pack_forget()
            self._aviso_paciente.configure(text=aviso or AVISO_BUSCAR,
                                           text_color=tema.COLOR_ERROR if error else tema.COLOR_TEXTO_SECUNDARIO)
            self._aviso_paciente.pack(fill="x", pady=(tema.ESPACIO_2, 0))
            return
        self._aviso_paciente.pack_forget()
        documento = paciente.documento
        texto = formato.SIN_DOCUMENTO if documento is None else f"{ETIQUETAS[documento.tipo]} {documento.numero}"
        self._nombre_paciente.configure(text=f"{paciente.nombres} {paciente.apellidos}")
        self._datos_paciente.configure(text=f"{texto} · {'Activo' if paciente.activo else 'Dado de baja'}")
        self._boton_paciente.configure(text="Dar de baja" if paciente.activo else "Reactivar")
        self._encontrado.pack(fill="x", pady=(tema.ESPACIO_2, 0))

    def _documento_editado(self):
        """
        Al cambiar el documento (el número o el tipo): el rojo se va si cambió el rechazado, y el resultado de otro
        documento se retira. Soltar el Enter que buscó no cambia nada.
        """
        tipo, numero = self._documento.valores()
        if self._documento_rechazado is not None and (tipo, numero) != self._documento_rechazado:
            self._documento_rechazado = None
            marcar_error(self._documento.campo_numero, False)
            self._mostrar_paciente(None, AVISO_BUSCAR)
        if self._buscado is not None and (tipo, numero.strip()) != self._buscado:
            self._buscado = None
            self._mostrar_paciente(None, AVISO_BUSCAR)

    def cambiar_paciente(self):
        """Da de baja al paciente encontrado o, si ya lo estaba, lo reactiva. Después se relee como está ahora."""
        paciente = self._paciente
        if paciente is None:
            return
        # Sin «dado de baja» ni «reactivado» junto al nombre: no se sabe si es él o ella
        nombre = f"{paciente.nombres} {paciente.apellidos}"
        try:
            if paciente.activo:
                self._pacientes.dar_de_baja(paciente.id_paciente)
                mensaje = f"Se dio de baja a {nombre}. Se puede reactivar desde aquí."
            else:
                self._pacientes.reactivar(paciente.id_paciente)
                mensaje = f"Se reactivó a {nombre}."
        except (SigtacError, ValueError) as error:
            mostrar_error(self, error)  # p. ej. tiene un episodio abierto
            self._releer_paciente()     # otra PC pudo cambiarlo
            return
        self._releer_paciente()
        mostrar_info(self, mensaje)

    def _releer_paciente(self):
        """Vuelve a leer el paciente que se buscó (no lo escrito después), sin diálogo si falla."""
        if self._buscado is None:
            return
        tipo, numero = self._buscado
        try:
            paciente = self._pacientes.buscar_para_administrar(tipo.value, numero)
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudo releer al paciente (%s).", type(error).__name__)
            return
        self._mostrar_paciente(paciente, NO_ENCONTRADO if paciente is None else "")

    # ---- Datos

    def al_mostrar(self):
        """Al volver a Administración: relee cuentas y empleados, sin diálogo, y conserva lo elegido si sigue."""
        self._recargar(conservar=True)

    def _operar(self, operacion, exito: str):
        """
        Una operación sobre la cuenta elegida. Si falla (p. ej. es la propia cuenta), se avisa y se recarga conservando
        la elección; si sale bien, también se conserva (para seguir con la misma cuenta) y se avisa.
        """
        try:
            operacion()
        except (SigtacError, ValueError) as error:
            mostrar_error(self, error)
            self._recargar(conservar=True)
            return
        self._recargar(conservar=True)
        mostrar_info(self, exito)

    def _cargar_datos(self):
        """
        Cuentas, empleados sin cuenta, filtros y la bitácora de hoy, al abrir. Si la BD falla, un solo aviso y las
        tablas dicen que no se pudieron leer (no que están vacías).
        """
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron leer los datos de administración (%s).", type(error).__name__)
            mostrar_error(self, error)
            self._mostrar([], [], [])
            self._cuenta_elegida()
            self._empleado_elegido()
            for tabla in (self._tabla_cuentas, self._tabla_empleados, self._tabla_bitacora):
                tabla.sin_lectura()
            # Sin cifra: «(0)» diría que no hay, y no se sabe
            self._modo.cambiar_texto("cuentas", "Cuentas")
            self._modo.cambiar_texto("nueva", "Nueva cuenta")
            return
        self._mostrar(*datos)
        self._cuenta_elegida()
        self._empleado_elegido()
        self.ver_bitacora()  # las cuentas se leyeron: si solo falla la bitácora, es el único aviso

    def _recargar(self, conservar: bool = False):
        """Vuelve a leer, sin diálogo si falla. Con `conservar`, lo elegido que siga en su lista sigue elegido."""
        tablas = (self._tabla_cuentas, self._tabla_empleados)
        elegidos = [tabla.seleccionado() for tabla in tablas] if conservar else [None, None]
        try:
            datos = self._leer()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron actualizar los datos de administración (%s).", type(error).__name__)
            return
        self._mostrar(*datos)
        for tabla, elegido in zip(tablas, elegidos):
            if elegido is not None:
                tabla.seleccionar(elegido)
        self._cuenta_elegida()
        self._empleado_elegido()

    def _leer(self):
        return self._admin.listar_cuentas(), self._admin.listar_empleados_sin_cuenta(), \
            self._admin.listar_tablas_auditables()

    def _mostrar(self, cuentas, empleados, tablas):
        self._cuentas = {c.id_usuario: c for c in cuentas}
        self._nombres = nombres_de_cuentas(cuentas)
        self._tabla_cuentas.cargar([(c.id_usuario, (c.nombre_completo, c.cargo, c.rol.value, estado_cuenta(c)))
                                    for c in cuentas])
        self._empleados = {e["id_empleado"]: e for e in empleados}
        self._tabla_empleados.cargar([(e["id_empleado"], (f"{e['nombres']} {e['apellidos']}", e["nombre_cargo"]))
                                      for e in empleados])
        self._modo.cambiar_texto("cuentas", f"Cuentas ({len(cuentas)})")
        self._modo.cambiar_texto("nueva", f"Nueva cuenta ({len(empleados)})")
        self._cargar_filtros(tablas)
        # Los botones y la clave se actualizan después, con la elección ya repuesta (_recargar): hacerlo aquí, con las
        # tablas recién cargadas y sin elección, borraría la clave que se está escribiendo para la misma cuenta

    def _cambiar_modo(self, modo: str):
        self._tarjeta.cambiar_textos(*TITULOS[modo])
        for clave, panel in self._paneles.items():
            if clave != modo:
                panel.pack_forget()
        self._paneles[modo].pack(fill="x")
        self._contenido.reacomodar()
        if modo in ("cuentas", "nueva"):
            self._recargar(conservar=True)
        elif modo == "bitacora":
            self.ver_bitacora(avisar_error=False)  # lo recién hecho en las otras opciones ya aparece
        else:
            self._documento.enfocar()
