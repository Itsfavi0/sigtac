"""
Ventana principal (docs/diseno/BRIEF.md §2 y el tablero aprobado): a la izquierda la barra lateral con la marca, el
menú de los módulos que el rol puede usar y, al pie, el usuario, el modo oscuro y «Cerrar sesión»; a la derecha el
encabezado del módulo (título, qué muestra, hora de actualización, fecha y reloj) y su contenido.

Cada pantalla se registra en PANTALLAS con una función crear(padre, sesion, principal) que devuelve su marco. Un
módulo sin pantalla todavía muestra un aviso: las pantallas de la Fase 6 se agregan una por una.
"""
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import customtkinter as ctk

from controllers.auth_controller import AuthController, Sesion
from controllers.cama_controller import CamaController
from controllers.paciente_controller import PacienteController
from controllers.reporte_controller import ReporteController
from controllers.triaje_controller import TriajeController
from models.permisos import Permiso
from views import formato, tema
from views.componentes import BotonSecundario, Marca
from views.componentes.foco import GROSOR_FOCO, fijar_borde, marcar_foco_control
from views.dashboard_view import DashboardView
from views.pacientes_view import PacientesView
from views.triage_view import TriageView


@dataclass(frozen=True)
class Modulo:
    clave: str
    nombre: str        # texto del menú y título del encabezado
    descripcion: str   # la línea bajo el título: qué muestra la pantalla
    permiso: Permiso   # sin él, el módulo no aparece en el menú


# En el orden del menú. Cola de espera, limpieza y reportes no se muestran hasta que tengan pantalla (brief §2).
MODULOS = (
    Modulo("tablero", "Tablero de camas", "Estado de la guardia en este momento", Permiso.VER_CAMAS),
    Modulo("triaje", "Triaje", "Registrar al paciente y clasificar su prioridad", Permiso.TRIAJE),
    Modulo("pacientes", "Pacientes", "Buscar, corregir e identificar pacientes", Permiso.PACIENTES),
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


# clave del módulo → crear(padre, sesion, principal). Cada pantalla de la Fase 6 se agrega aquí al crearse.
PANTALLAS: dict[str, Callable] = {"tablero": crear_tablero, "triaje": crear_triaje, "pacientes": crear_pacientes}

PUNTO = "●"  # delante de «Actualizado», como en el tablero aprobado
SIN_CONEXION = "Sin conexión"
TEXTO_PENDIENTE ="Esta pantalla se agrega en el siguiente paso de la Fase 6."
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

    def __init__(self, padre, auth: AuthController, sesion: Sesion, al_cerrar,
                 pantallas: dict[str, Callable] | None = None):
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
        self._tarea_reloj = None

        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._crear_barra().grid(row=0, column=0, sticky="ns")
        self._divisor(self, width=1).grid(row=0, column=1, sticky="ns")
        derecha = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        derecha.grid(row=0, column=2, sticky="nsew")
        self._crear_encabezado(derecha).pack(fill="x", padx=tema.ESPACIO_3)
        self._contenido = ctk.CTkFrame(derecha, fg_color="transparent", corner_radius=0)
        self._contenido.pack(fill="both", expand=True, padx=tema.ESPACIO_3, pady=(0, tema.ESPACIO_3))

        self._actualizar_reloj()
        if self._modulos:
            self.mostrar(self._modulos[0].clave)
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
        boton = ctk.CTkButton(
            fila, text=modulo.nombre, anchor="w", height=tema.ALTO_NAVEGACION, corner_radius=tema.RADIO_CONTROL,
            font=tema.fuente("normal"), fg_color="transparent", hover_color=tema.COLOR_ACTIVO,
            text_color=tema.COLOR_TEXTO, border_width=0, border_color=tema.COLOR_BORDE,
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
        """El aviso que reciben las pantallas que se actualizan solas (al_actualizar del tablero)."""
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
        """Cambia al módulo indicado, sin transición. Solo los módulos del menú (los que el rol puede usar)."""
        modulo = next((m for m in self._modulos if m.clave == clave), None)
        if modulo is None:
            raise ValueError(f"Módulo no disponible para este rol: {clave!r}.")
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
        else:
            self._colocar(crear(self._contenido, self._sesion, self))

    def _marcar_item(self, clave: str, activo: bool):
        boton, indicador = self._items[clave]
        boton.configure(fg_color=tema.COLOR_ACTIVO if activo else "transparent",
                        font=tema.fuente("fuerte" if activo else "normal"))
        fijar_borde(boton, 1 if activo else 0, tema.COLOR_BORDE)  # respeta el borde de foco si lo tiene
        indicador.configure(fg_color=tema.COLOR_PRIMARIO if activo else "transparent")

    def _mostrar_aviso(self, texto: str):
        self._colocar(ctk.CTkLabel(self._contenido, text=texto, font=tema.fuente("normal"),
                                   text_color=tema.COLOR_TEXTO_SECUNDARIO))

    def _colocar(self, pantalla):
        if self._pantalla is not None:
            self._pantalla.destroy()
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
        if self._tarea_reloj is not None:
            self.after_cancel(self._tarea_reloj)
            self._tarea_reloj = None
        super().destroy()
