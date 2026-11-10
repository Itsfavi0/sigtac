"""
Ventana principal (docs/diseno/BRIEF.md §2 y el tablero aprobado): a la izquierda la barra lateral con la marca, el
menú de los módulos que el rol puede usar y, al pie, el usuario, el modo oscuro y «Cerrar sesión»; a la derecha el
encabezado del módulo (título, qué muestra, hora de actualización, fecha y reloj) y su contenido.

Cada pantalla se registra en PANTALLAS con una función crear(padre, sesion, principal) que devuelve su marco. Todos
los módulos tienen la suya (hay una prueba que lo exige); un módulo sin pantalla, como en las pruebas que pasan
`pantallas`, muestra un aviso.

Una pantalla se construye una sola vez por sesión: al cambiar de módulo se oculta, y al volver se muestra como quedó
(un triaje a medio escribir sigue ahí). Construir una tarda de 0,3 a 0,8 s; mostrarla ya construida, casi nada. Con
`precargar`, las del menú se construyen ocultas después de abrir la primera, una por vez. Una pantalla puede tener
`al_mostrar()` (al volver a ella: relee sus datos sin diálogo) y `al_ocultar()` (p. ej. detener una actualización
automática).
"""
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import customtkinter as ctk

from controllers.admin_controller import AdminController
from controllers.auth_controller import AuthController, Sesion
from controllers.cama_controller import CamaController
from controllers.paciente_controller import PacienteController
from controllers.reporte_controller import ReporteController
from controllers.triaje_controller import TriajeController
from models.permisos import Permiso
from views import formato, tema
from views.componentes import BotonSecundario, Cubierta, Marca
from views.componentes.foco import GROSOR_FOCO, fijar_borde, marcar_foco_control
from views.componentes.iconos import MENU, icono
from views.admin_view import AdminView
from views.camas_view import GestionCamasView
from views.dashboard_view import DashboardView
from views.limpieza_view import LimpiezaView
from views.pacientes_view import PacientesView
from views.reportes_view import ReportesView
from views.triage_view import TriageView


@dataclass(frozen=True)
class Modulo:
    clave: str
    nombre: str        # texto del menú y título del encabezado
    descripcion: str   # la línea bajo el título: qué muestra la pantalla
    permiso: Permiso   # sin él, el módulo no aparece en el menú


# En el orden del menú.
MODULOS = (
    Modulo("tablero", "Tablero de camas", "Estado de la guardia en este momento", Permiso.VER_CAMAS),
    Modulo("triaje", "Triaje", "Registrar al paciente y clasificar su prioridad", Permiso.TRIAJE),
    Modulo("camas", "Gestión de camas", "Asignar camas, dar de alta y mantenimiento", Permiso.GESTION_CAMAS),
    Modulo("pacientes", "Pacientes", "Buscar, corregir e identificar pacientes", Permiso.PACIENTES),
    Modulo("limpieza", "Limpieza", "Camas dadas de alta que esperan limpieza", Permiso.LIMPIEZA),
    Modulo("reportes", "Reportes", "Indicadores de un período y exportación a PDF", Permiso.REPORTES),
    Modulo("admin", "Administración", "Cuentas de usuario, bitácora y baja de pacientes", Permiso.ADMINISTRACION),
)

def crear_tablero(padre, sesion: Sesion, principal: "AppPrincipal", camas=None, reportes=None, triaje=None):
    """
    El tablero con los controladores reales de la sesión. El prototipo pasa los de demostración en camas,
    reportes y triaje (prototipo/ver.py).
    """
    return DashboardView(padre, camas or CamaController(sesion), sesion, reportes or ReporteController(sesion),
                         triaje or TriajeController(sesion), al_actualizar=principal.informar_actualizacion)


def crear_triaje(padre, sesion: Sesion, principal: "AppPrincipal", pacientes=None, triaje=None):
    """El triaje con los controladores reales de la sesión; el prototipo pasa los de demostración."""
    return TriageView(padre, pacientes or PacienteController(sesion), triaje or TriajeController(sesion))


def crear_pacientes(padre, sesion: Sesion, principal: "AppPrincipal", pacientes=None):
    """
    Pacientes con el controlador real; el prototipo pasa el de demostración. «Registrarlo en Triaje» abre Triaje
    con el documento ya buscado, si el rol lo tiene en el menú.
    """
    def registrar_en_triaje(tipo, numero):
        principal.mostrar("triaje")
        pantalla = principal.pantalla_actual
        if isinstance(pantalla, TriageView):  # sin pantalla registrada, Triaje muestra solo su aviso
            pantalla.buscar_documento(tipo, numero)

    return PacientesView(padre, pacientes or PacienteController(sesion),
                         registrar_en_triaje if "triaje" in principal.modulos_visibles else None)


def crear_camas(padre, sesion: Sesion, principal: "AppPrincipal", camas=None):
    """Gestión de camas con el controlador real; el prototipo pasa el de demostración."""
    return GestionCamasView(padre, camas or CamaController(sesion))


def crear_limpieza(padre, sesion: Sesion, principal: "AppPrincipal", camas=None):
    """Limpieza con el controlador real; el prototipo pasa el de demostración."""
    return LimpiezaView(padre, camas or CamaController(sesion))


def crear_reportes(padre, sesion: Sesion, principal: "AppPrincipal", reportes=None):
    """
    Reportes con el controlador real; el prototipo pasa el de demostración. Como el tablero, avisa al encabezado
    cuándo leyó los datos («Ahora en la guardia» es una foto de ese momento).
    """
    return ReportesView(padre, reportes or ReporteController(sesion), al_actualizar=principal.informar_actualizacion)


def crear_admin(padre, sesion: Sesion, principal: "AppPrincipal", admin=None, pacientes=None):
    """
    Administración con los controladores reales; el prototipo pasa los de demostración. Pacientes solo se usa para
    buscar, dar de baja y reactivar (permiso ADMINISTRACION).
    """
    return AdminView(padre, admin or AdminController(sesion), pacientes or PacienteController(sesion),
                     id_usuario_propio=sesion.id_usuario)


# clave del módulo → crear(padre, sesion, principal). Una pantalla nueva se agrega aquí y en PANTALLAS_DEMO.
PANTALLAS: dict[str, Callable] = {"tablero": crear_tablero, "triaje": crear_triaje, "camas": crear_camas,
                                  "pacientes": crear_pacientes, "limpieza": crear_limpieza,
                                  "reportes": crear_reportes, "admin": crear_admin}

PUNTO = "●"  # delante de «Actualizado», como en el tablero aprobado
SIN_CONEXION = "Sin conexión"
TEXTO_PENDIENTE = "Esta pantalla no está disponible."
TEXTO_SIN_MODULOS = "Su rol no tiene módulos disponibles. Consulte con el administrador."


def iniciales(sesion: Sesion) -> str:
    """Las iniciales del primer nombre y el primer apellido («Luis Ramos» → «LR»)."""
    partes = (sesion.nombres.split()[:1] + sesion.apellidos.split()[:1])
    return "".join(parte[0].upper() for parte in partes)


class AppPrincipal(ctk.CTkFrame):
    """
    El marco de la aplicación con sesión iniciada. No sabe qué se muestra al cerrar la sesión: llama a
    `al_cerrar()` y main.py vuelve al login.
    """

    MS_RELOJ = 1000
    MS_ANTES_DE_PRECARGAR = 500  # que la primera pantalla termine de dibujarse antes de construir las otras
    MS_ENTRE_PRECARGAS = 50      # entre una pantalla y la siguiente: deja pasar los clics del usuario

    def __init__(self, padre, auth: AuthController, sesion: Sesion, al_cerrar,
                 pantallas: dict[str, Callable] | None = None, precargar: bool = False):
        super().__init__(padre, fg_color=tema.COLOR_FONDO, corner_radius=0)
        self._auth = auth
        self._sesion = sesion
        self._al_cerrar = al_cerrar
        self._pantallas = PANTALLAS if pantallas is None else pantallas
        self._modulos = [m for m in MODULOS if sesion.puede(m.permiso)]
        self._items = {}        # clave → (botón, indicador)
        self._divisores = []
        self._actual = None
        self._pantalla = None
        self._guardadas = {}       # clave → pantalla ya construida: volver a ella no la reconstruye
        self._precargando = False  # se construye una pantalla oculta: su aviso de actualización no va al encabezado
        self._sin_conexion = False  # la última lectura falló: no se precarga (cada pantalla abriría un diálogo)
        self._tarea_reloj = None
        self._tarea_precarga = None

        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._crear_barra().grid(row=0, column=0, sticky="ns")
        self._divisor(self, width=1).grid(row=0, column=1, sticky="ns")
        derecha = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        derecha.grid(row=0, column=2, sticky="nsew")
        self._crear_encabezado(derecha).pack(fill="x", padx=tema.ESPACIO_3)
        self._contenido = ctk.CTkFrame(derecha, fg_color="transparent", corner_radius=0)
        self._contenido.pack(fill="both", expand=True, padx=tema.ESPACIO_3, pady=(0, tema.ESPACIO_3))
        # Tapa el encabezado y el contenido al cambiar de módulo (el título cambia junto con la pantalla); el menú
        # queda fuera y se marca al instante
        self._cubierta = Cubierta(derecha)

        self._actualizar_reloj()
        if self._modulos:
            self.mostrar(self._modulos[0].clave)
            if precargar:
                self._tarea_precarga = self.after(self.MS_ANTES_DE_PRECARGAR, self._precargar)
        else:
            self._mostrar_aviso(TEXTO_SIN_MODULOS)

    # ---- Barra lateral

    def _crear_barra(self) -> ctk.CTkFrame:
        # Los widgets se crean en el orden de lectura, que es el orden de Tab. Se colocan en otro: el pie antes que
        # el menú, para que en una ventana baja se recorte el menú y nunca «Cerrar sesión».
        barra = ctk.CTkFrame(self, width=tema.ANCHO_BARRA, fg_color=tema.COLOR_BARRA, corner_radius=0)
        barra.pack_propagate(False)
        marca = Marca(barra)
        titulo_menu = ctk.CTkLabel(barra, text="Menú principal", font=tema.fuente("etiqueta"),
                                   text_color=tema.COLOR_ETIQUETA, anchor="w")
        filas = [self._crear_item(barra, modulo) for modulo in self._modulos]
        divisor = self._divisor(barra, height=1)
        usuario = self._crear_usuario(barra)
        self._interruptor_modo = ctk.CTkSwitch(
            barra, text="Modo oscuro", command=self._cambiar_modo, font=tema.fuente("normal"),
            text_color=tema.COLOR_TEXTO, progress_color=tema.COLOR_PRIMARIO, fg_color=tema.COLOR_BORDE_CAMPO,
            border_width=0, border_color=tema.COLOR_BARRA)
        if tema.modo_oscuro():
            self._interruptor_modo.select()
        self._pintar_interruptor()
        marcar_foco_control(self._interruptor_modo, self._interruptor_modo.toggle)
        salir = BotonSecundario(barra, "Cerrar sesión", self.cerrar_sesion)

        marca.pack(anchor="w", padx=tema.ESPACIO_2, pady=(tema.ESPACIO_3, tema.ESPACIO_3))
        # El pie, de abajo hacia arriba
        salir.pack(side="bottom", fill="x", padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))
        self._interruptor_modo.pack(side="bottom", anchor="w", padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))
        usuario.pack(side="bottom", fill="x", padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))
        # La línea separa el pie del menú (en el diseño, ese lugar lo ocupaba la tarjeta «Conectado»)
        divisor.pack(side="bottom", fill="x", pady=(0, tema.ESPACIO_2))
        titulo_menu.pack(fill="x", padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO))
        for fila in filas:
            fila.pack(fill="x", pady=(0, tema.ESPACIO_MINIMO))
        return barra

    def _divisor(self, padre, **medidas) -> tk.Frame:
        """
        Una línea de 1 px entre zonas. Es un Frame de tkinter porque CustomTkinter no dibuja un CTkFrame tan
        delgado; como no entiende los pares (claro, oscuro), se repinta en _set_appearance_mode.
        """
        linea = tk.Frame(padre, background=tema.color_actual(tema.COLOR_DIVISOR), borderwidth=0,
                         highlightthickness=0, **medidas)
        self._divisores.append(linea)
        return linea

    def _crear_item(self, barra, modulo: Modulo) -> ctk.CTkFrame:
        fila = ctk.CTkFrame(barra, fg_color="transparent", corner_radius=0)
        # El ícono, a la izquierda del nombre, del color del texto secundario (azul en el ítem activo)
        boton = ctk.CTkButton(
            fila, text=modulo.nombre, anchor="w", height=tema.ALTO_NAVEGACION, corner_radius=tema.RADIO_CONTROL,
            font=tema.fuente("normal"), fg_color="transparent", hover_color=tema.COLOR_ACTIVO,
            text_color=tema.COLOR_TEXTO, border_width=0, border_color=tema.COLOR_BORDE,
            image=icono(MENU[modulo.clave], tema.COLOR_TEXTO_SECUNDARIO), compound="left",
            command=lambda: self.mostrar(modulo.clave))
        marcar_foco_control(boton, boton.invoke)
        # El alto explícito importa: un CTkFrame mide 200 px por defecto y estiraría la fila
        indicador = ctk.CTkFrame(fila, width=GROSOR_FOCO, height=tema.ALTO_NAVEGACION, corner_radius=0,
                                 fg_color="transparent")
        indicador.pack(side="right")
        boton.pack(side="left", fill="x", expand=True, padx=(tema.ESPACIO, tema.ESPACIO))
        self._items[modulo.clave] = (boton, indicador)
        return fila

    def _crear_usuario(self, barra) -> ctk.CTkFrame:
        usuario = ctk.CTkFrame(barra, fg_color="transparent")
        # La misma forma que la marca: un cuadro (aquí, círculo) y dos líneas que juntas miden lo mismo
        avatar = ctk.CTkFrame(usuario, width=Marca.LADO_LOGO, height=Marca.LADO_LOGO,
                              corner_radius=Marca.LADO_LOGO // 2, fg_color=tema.COLOR_ACTIVO)
        avatar.pack_propagate(False)
        avatar.grid(row=0, column=0, rowspan=2, padx=(0, tema.ESPACIO))
        ctk.CTkLabel(avatar, text=iniciales(self._sesion), font=tema.fuente("fuerte"),
                     text_color=tema.COLOR_TEXTO).place(relx=0.5, rely=0.5, anchor="center")
        nombre = f"{self._sesion.nombres.split()[0]} {self._sesion.apellidos.split()[0]}"
        ctk.CTkLabel(usuario, text=nombre, font=tema.fuente("fuerte"), text_color=tema.COLOR_TEXTO, anchor="w",
                     height=Marca.ALTO_NOMBRE).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(usuario, text=self._sesion.nombre_rol, font=tema.fuente("pequena"),
                     text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w", height=Marca.ALTO_SERVICIO).grid(
            row=1, column=1, sticky="w")
        return usuario

    # ---- Encabezado

    def _crear_encabezado(self, padre) -> ctk.CTkFrame:
        encabezado = ctk.CTkFrame(padre, height=tema.ALTO_ENCABEZADO, fg_color="transparent", corner_radius=0)
        encabezado.pack_propagate(False)
        textos = ctk.CTkFrame(encabezado, fg_color="transparent")
        textos.pack(side="left")
        self._titulo = ctk.CTkLabel(textos, text="", font=tema.fuente("titulo"), text_color=tema.COLOR_TEXTO,
                                    anchor="w")
        self._titulo.pack(anchor="w")
        self._descripcion = ctk.CTkLabel(textos, text="", font=tema.fuente("pequena"),
                                         text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        self._descripcion.pack(anchor="w")

        # A la derecha, de derecha a izquierda: reloj, fecha y la hora de la última actualización
        self._reloj = ctk.CTkLabel(encabezado, text="", font=tema.fuente("fuerte"), text_color=tema.COLOR_TEXTO)
        self._reloj.pack(side="right")
        self._fecha = ctk.CTkLabel(encabezado, text="", font=tema.fuente("normal"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO)
        self._fecha.pack(side="right", padx=tema.ESPACIO_2)
        self._actualizado = ctk.CTkLabel(encabezado, text="", font=tema.fuente("fuerte"),
                                         text_color=tema.COLOR_EXITO)
        self._actualizado.pack(side="right", padx=(0, tema.ESPACIO_2))
        return encabezado

    def marcar_actualizado(self, momento: datetime | None = None):
        """Lo llama la pantalla al cargar sus datos: «Actualizado 10:42» (brief §2: no «EN VIVO»)."""
        self._actualizado.configure(text=f"{PUNTO} Actualizado {formato.hora(momento or datetime.now())}",
                                    text_color=tema.COLOR_EXITO)

    def marcar_sin_conexion(self):
        """Lo llama la pantalla si no pudo leer sus datos: sigue mostrando lo último que leyó."""
        self._actualizado.configure(text=f"{PUNTO} {SIN_CONEXION}", text_color=tema.COLOR_ERROR)

    def informar_actualizacion(self, correcta: bool, momento: datetime):
        """
        El aviso que reciben las pantallas que se actualizan solas (al_actualizar del tablero y de reportes). El de
        una pantalla que se precarga no se muestra: el encabezado es de la pantalla visible.
        """
        self._sin_conexion = not correcta
        if self._precargando:
            return
        if correcta:
            self.marcar_actualizado(momento)
        else:
            self.marcar_sin_conexion()

    def _actualizar_reloj(self):
        ahora = datetime.now()
        self._fecha.configure(text=formato.fecha_corta(ahora.date()))
        self._reloj.configure(text=formato.hora(ahora, con_segundos=True))
        self._tarea_reloj = self.after(self.MS_RELOJ, self._actualizar_reloj)

    # ---- Módulos

    def mostrar(self, clave: str):
        """
        Cambia al módulo indicado, sin transición: la pantalla nueva aparece completa, de una vez (Cubierta). Solo los
        módulos del menú (los que el rol puede usar).
        """
        modulo = next((m for m in self._modulos if m.clave == clave), None)
        if modulo is None:
            raise ValueError(f"Módulo no disponible para este rol: {clave!r}.")
        self._cubierta.cambiar(lambda: self._abrir(modulo))

    def _abrir(self, modulo: Modulo):
        """
        El ítem del menú, el encabezado y la pantalla del módulo (la guardada con al_mostrar, una nueva o el aviso).
        Corre bajo la cubierta, que tapa encabezado y contenido: el menú, que queda fuera, se marca al instante.
        """
        clave = modulo.clave
        if self._actual is not None:
            self._marcar_item(self._actual, activo=False)
        self._actual = clave
        self._marcar_item(clave, activo=True)
        self._titulo.configure(text=modulo.nombre)
        self._descripcion.configure(text=modulo.descripcion)
        self._actualizado.configure(text="")
        crear = self._pantallas.get(clave)
        if crear is None:
            self._mostrar_aviso(TEXTO_PENDIENTE)
            return
        guardada = self._guardadas.get(clave)
        if guardada is None:
            self._colocar(self._guardar(clave, crear))
            return
        self._colocar(guardada)
        al_mostrar = getattr(guardada, "al_mostrar", None)
        if al_mostrar is not None:
            al_mostrar()  # se construyó antes: sus datos pueden haber cambiado

    def _guardar(self, clave: str, crear: Callable):
        pantalla = self._guardadas[clave] = crear(self._contenido, self._sesion, self)
        return pantalla

    def _precargar(self):
        """
        Construye, oculta, la siguiente pantalla del menú que aún no existe, y programa la que sigue. Una por vez:
        entre una y otra pasan los clics del usuario. Se detiene si la base de datos no respondió.
        """
        if self._tarea_precarga is not None:
            self.after_cancel(self._tarea_precarga)  # llamado antes de su hora: que no corra dos veces
            self._tarea_precarga = None
        pendiente = next((m.clave for m in self._modulos
                          if m.clave not in self._guardadas and m.clave in self._pantallas), None)
        if pendiente is None or self._sin_conexion:
            return
        foco = self.focus_get()
        self._precargando = True
        try:
            self._guardar(pendiente, self._pantallas[pendiente])
        finally:
            self._precargando = False
        if foco is not None:
            # Una pantalla pone el foco en su primer campo al construirse (after_idle); oculta, no debe quitárselo a
            # la visible. Este after_idle corre después del suyo
            self.after_idle(lambda: foco.winfo_exists() and foco.focus_set())
        self._tarea_precarga = self.after(self.MS_ENTRE_PRECARGAS, self._precargar)

    def _marcar_item(self, clave: str, activo: bool):
        boton, indicador = self._items[clave]
        color_icono = tema.COLOR_PRIMARIO_GRAFICO if activo else tema.COLOR_TEXTO_SECUNDARIO
        boton.configure(fg_color=tema.COLOR_ACTIVO if activo else "transparent",
                        font=tema.fuente("fuerte" if activo else "normal"), image=icono(MENU[clave], color_icono))
        fijar_borde(boton, 1 if activo else 0, tema.COLOR_BORDE)  # respeta el borde de foco si lo tiene
        indicador.configure(fg_color=tema.COLOR_PRIMARIO_GRAFICO if activo else "transparent")  # el azul del ícono

    def _mostrar_aviso(self, texto: str):
        self._colocar(ctk.CTkLabel(self._contenido, text=texto, font=tema.fuente("normal"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO))

    def _colocar(self, pantalla):
        """Muestra `pantalla`. La anterior se oculta si es de un módulo (se reutiliza) o se destruye si es un aviso."""
        anterior = self._pantalla
        if anterior is not None and anterior is not pantalla:
            if any(anterior is guardada for guardada in self._guardadas.values()):
                anterior.pack_forget()
                al_ocultar = getattr(anterior, "al_ocultar", None)
                if al_ocultar is not None:
                    al_ocultar()
            else:
                anterior.destroy()
        self._pantalla = pantalla
        pantalla.pack(fill="both", expand=True)

    @property
    def modulo_actual(self) -> str | None:
        return self._actual

    @property
    def pantalla_actual(self):
        """La pantalla que se muestra (para pasarle algo al abrirla desde otra, p. ej. un documento ya buscado)."""
        return self._pantalla

    @property
    def modulos_visibles(self) -> list[str]:
        return [m.clave for m in self._modulos]

    # ---- Pie de la barra

    def _cambiar_modo(self):
        self._pintar_interruptor()
        ctk.set_appearance_mode("dark" if self._interruptor_modo.get() else "light")

    def _pintar_interruptor(self):
        """
        Encendido, el círculo es blanco sobre el azul; apagado, gris oscuro, porque blanco se perdería contra la
        barra blanca. Apagado, al pasar el mouse se oscurece un poco.
        """
        if self._interruptor_modo.get():
            self._interruptor_modo.configure(button_color=tema.COLOR_TEXTO_SOBRE_PRIMARIO,
                                             button_hover_color=tema.COLOR_TEXTO_SOBRE_PRIMARIO)
        else:
            self._interruptor_modo.configure(button_color=tema.COLOR_TEXTO_SECUNDARIO,
                                             button_hover_color=tema.COLOR_ETIQUETA)

    def _set_appearance_mode(self, modo):
        super()._set_appearance_mode(modo)
        tono = tema.COLOR_DIVISOR[1 if str(modo).lower() == "dark" else 0]
        for linea in self._divisores:
            linea.configure(background=tono)

    def cerrar_sesion(self):
        self._auth.cerrar_sesion()
        self._al_cerrar()

    def destroy(self):
        self._cubierta.quitar()
        for tarea in (self._tarea_reloj, self._tarea_precarga):
            if tarea is not None:
                self.after_cancel(tarea)
        self._tarea_reloj = self._tarea_precarga = None
        super().destroy()
