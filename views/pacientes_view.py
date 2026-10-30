"""
Pacientes (docs/diseno/BRIEF.md §5): consultar y corregir los datos de un paciente, admitirlo (abrir su episodio) e
identificar a los que llegaron sin identificar (NN).

- «Buscar»: el documento → la ficha, con «Editar datos» y «Abrir episodio». El documento no se edita: identifica a
  la persona. Si no hay nadie con ese documento, se ofrece registrarlo en Triaje.
- «Sin identificar (N)»: la lista de NN; al elegir uno se escribe su identidad real. Si ese documento ya es de otro
  paciente, no se identifica (se duplicaría la persona): se ofrece fusionar ambos registros, con confirmación.

Dar de baja y reactivar exigen el permiso de administración: no están en esta pantalla.
"""
import logging
from collections.abc import Callable

import customtkinter as ctk

from models.excepciones import SigtacError
from views import formato, tema
from views.componentes import (BotonPrimario, BotonSecundario, CamposDocumento, CamposPaciente, FichaPaciente,
                               Selector, TablaDatos, Tarjeta, campo_texto, confirmar, etiqueta_campo, marcar_error,
                               mostrar_error, mostrar_info)
from views.componentes.campos import sin_error
from views.componentes.documento import ETIQUETAS
from views.componentes.tabla import ALTO_FILA

logger = logging.getLogger(__name__)

AVISO_BUSCAR = "Escriba el documento y busque al paciente."
AVISO_IDENTIFICAR = "Si el documento ya es de un paciente registrado, se ofrece fusionarlos."
NO_ENCONTRADO = "No hay un paciente con ese documento."
DADO_DE_BAJA = "Está dado de baja: sus datos no se editan. Lo reactiva un administrador."
NADIE_SIN_IDENTIFICAR = "No hay pacientes sin identificar."
TEXTO_ELEGIR_NN = "Elija un paciente de la lista"   # el botón deshabilitado dice por qué no responde
TITULOS = {
    "buscar": ("Buscar paciente", "Por su documento de identidad"),
    "nn": ("Pacientes sin identificar", "Elija uno para registrar su identidad real"),
}


class PacientesView(ctk.CTkFrame):
    FILAS_LISTA = 5   # filas visibles de la lista de NN (más se desplazan dentro de la tabla)
    # «Registro» es el número del paciente en el sistema: dos NN del mismo sexo y edad aparente solo se distinguen
    # por él (el que se anota en la pulsera o la historia provisional)
    COLUMNAS_NN = (("Registro", 96), ("Paciente", 224), ("Seguro", 224))

    def __init__(self, padre, pacientes, al_registrar_en_triaje: Callable | None = None):
        """`al_registrar_en_triaje(tipo, numero)` abre Triaje con ese documento; None si el rol no tiene Triaje."""
        super().__init__(padre, fg_color="transparent")
        self._pacientes = pacientes
        self._al_registrar_en_triaje = al_registrar_en_triaje
        self._paciente = None              # el paciente de la ficha
        self._buscado = None               # (tipo, número) que se buscó: la ficha o «no encontrado» son de él
        self._documento_con_error = {}     # CamposDocumento → (tipo, número) rechazado por mal escrito

        # Como el formulario del triaje: se desplaza en vertical si no cabe (1093×614)
        self._contenido = contenido = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        contenido.pack(fill="both", expand=True)
        self._tarjeta = Tarjeta(contenido, *TITULOS["buscar"])
        self._tarjeta.pack(fill="x", padx=(0, tema.ESPACIO_MINIMO))
        self._modo = Selector(self._tarjeta.cabecera, [("buscar", "Buscar"), ("nn", "Sin identificar")],
                              self._cambiar_modo)
        self._modo.pack(side="right")
        cuerpo = ctk.CTkFrame(self._tarjeta, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=tema.ESPACIO_2, pady=(0, tema.ESPACIO_2))

        self._buscar = self._crear_buscar(cuerpo)
        self._nn = self._crear_sin_identificar(cuerpo)
        self._buscar.pack(fill="x")
        self._cargar_datos()
        self._tarea_foco = self.after_idle(self._documento.enfocar)

    # ---- Buscar

    def _crear_buscar(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        self._documento, self._aviso = self._fila_documento(marco, "Buscar", self.buscar)
        self._mostrar_aviso(self._aviso)

        self._no_encontrado = ctk.CTkFrame(marco, fg_color="transparent")
        ctk.CTkLabel(self._no_encontrado, text=NO_ENCONTRADO, font=tema.fuente("pequena"),
                     text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w").pack(anchor="w")
        if self._al_registrar_en_triaje is not None:
            BotonSecundario(self._no_encontrado, "Registrarlo en Triaje", self._ir_a_triaje).pack(
                anchor="w", pady=(tema.ESPACIO, 0))

        self._encontrado = ctk.CTkFrame(marco, fg_color="transparent")
        self._ficha = FichaPaciente(self._encontrado, ampliada=True)
        self._ficha.pack(fill="x")
        self._aviso_baja = ctk.CTkLabel(self._encontrado, text=DADO_DE_BAJA, font=tema.fuente("pequena"),
                                        text_color=tema.COLOR_TEXTO_SECUNDARIO, anchor="w")
        # Mientras se edita o se admite, estas dos se ocultan: a la vista queda solo el formulario abierto
        self._acciones_ficha = acciones = ctk.CTkFrame(self._encontrado, fg_color="transparent")
        acciones.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        self._boton_editar = BotonSecundario(acciones, "Editar datos", self.abrir_edicion)
        self._boton_editar.pack(side="left")
        self._boton_admitir = BotonSecundario(acciones, "Abrir episodio", self.abrir_admision)
        self._boton_admitir.pack(side="left", padx=(tema.ESPACIO, 0))

        # Editar datos: el documento queda fuera (no se edita)
        self._edicion = ctk.CTkFrame(self._encontrado, fg_color="transparent")
        self._datos = CamposPaciente(self._edicion)
        self._datos.pack(fill="x")
        for campo in self._datos.entradas:
            campo.bind("<Return>", self.guardar, add="+")
        self._acciones(self._edicion, "Guardar cambios", self.guardar, self.cancelar)

        # Abrir episodio: el motivo de consulta (el episodio empieza esperando triaje). Si falta, se explica bajo el
        # campo, como un documento mal escrito
        self._admision = ctk.CTkFrame(self._encontrado, fg_color="transparent")
        etiqueta_campo(self._admision, "Motivo de consulta").pack(anchor="w", pady=(0, tema.ESPACIO_MINIMO))
        self._motivo = campo_texto(self._admision, "Por qué acude a emergencia")
        self._motivo.pack(fill="x")
        self._aviso_motivo = ctk.CTkLabel(self._admision, text="", font=tema.fuente("pequena"),
                                          text_color=tema.COLOR_ERROR, anchor="w")
        self._motivo.bind("<Return>", self.abrir_episodio, add="+")
        self._motivo.bind("<KeyRelease>", lambda _e: self._motivo_corregido(), add="+")
        self._acciones(self._admision, "Abrir episodio", self.abrir_episodio, self.cancelar)
        return marco

    def buscar(self, _evento=None):
        tipo, numero = self._documento.valores()
        try:
            paciente = self._pacientes.buscar_por_documento(tipo.value, numero)
        except ValueError as error:
            self._documento_invalido(self._documento, self._aviso, error)
            return "break"
        except SigtacError as error:
            mostrar_error(self, error)  # la BD no respondió: no es culpa del documento
            return "break"
        self._documento_valido(self._documento, self._aviso)
        self._buscado = (tipo, numero.strip())
        self._paciente = paciente
        self.cerrar_formularios()
        if paciente is None:
            self._mostrar_resultado(self._no_encontrado)
        else:
            self._mostrar_ficha(paciente)
        return "break"

    def _mostrar_ficha(self, paciente):
        self._paciente = paciente
        self._ficha.mostrar(paciente)
        # Un paciente dado de baja no se edita ni se admite (RN-11; lo reactiva un administrador)
        estado = "normal" if paciente.activo else "disabled"
        self._boton_editar.configure(state=estado)
        self._boton_admitir.configure(state=estado)
        if paciente.activo:
            self._aviso_baja.pack_forget()
        else:
            self._aviso_baja.pack(anchor="w", pady=(tema.ESPACIO, 0), after=self._ficha)
        self._mostrar_resultado(self._encontrado)

    def _mostrar_resultado(self, cual):
        """Bajo el documento se ve una sola cosa: la indicación, «no hay nadie» o la ficha."""
        for parte in (self._aviso, self._no_encontrado, self._encontrado):
            parte.pack_forget()
        cual.pack(fill="x", pady=(tema.ESPACIO_2, 0))

    def _ir_a_triaje(self):
        """Lleva a Triaje el documento que se buscó (no lo que haya escrito ahora en el campo)."""
        self._al_registrar_en_triaje(*self._buscado)

    def abrir_edicion(self):
        """Muestra los datos de la ficha en los campos, listos para corregir."""
        self.cerrar_formularios()
        self._datos.fijar(self._paciente)
        self._acciones_ficha.pack_forget()
        self._edicion.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        self._mostrar_al_pie()
        self._datos.enfocar()

    def abrir_admision(self):
        self.cerrar_formularios()
        self._acciones_ficha.pack_forget()
        self._admision.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        self._mostrar_al_pie()
        self._motivo.focus_set()

    def _mostrar_al_pie(self):
        """Desplaza el contenido hasta el final, para que el formulario recién abierto y su botón queden a la vista."""
        self.update_idletasks()
        self._contenido._parent_canvas.yview_moveto(1.0)

    def cancelar(self):
        """«Cancelar»: cierra el formulario sin guardar y el foco vuelve al documento (no a un campo oculto)."""
        self.cerrar_formularios()
        self._documento.enfocar()

    def _motivo_corregido(self):
        sin_error(self._motivo)
        self._aviso_motivo.pack_forget()

    def cerrar_formularios(self):
        """Cierra la edición y la admisión sin guardar (los botones «Cancelar»); vuelven las acciones de la ficha."""
        self._edicion.pack_forget()
        self._admision.pack_forget()
        self._acciones_ficha.pack(fill="x", pady=(tema.ESPACIO_2, 0), after=self._ficha)
        self._datos.limpiar()
        self._motivo.delete(0, "end")
        self._motivo._activate_placeholder()
        self._motivo_corregido()

    def guardar(self, _evento=None):
        """Guarda los datos corregidos. El controlador no escribe nada si no cambió ningún dato."""
        try:
            datos = self._datos.valores()
            paciente = self._pacientes.actualizar_datos(self._paciente.id_paciente, **datos)
        except (SigtacError, ValueError) as error:
            mostrar_error(self, error)
            return "break"
        self.cancelar()
        self._mostrar_ficha(paciente)
        mostrar_info(self, "Datos del paciente guardados.")
        return "break"

    def abrir_episodio(self, _evento=None):
        """Registra la llegada del paciente: su episodio empieza esperando triaje."""
        try:
            self._pacientes.abrir_episodio(self._paciente.id_paciente, self._motivo.get())
        except ValueError as error:
            # El paciente sale de la ficha: el único dato que se escribe aquí es el motivo
            marcar_error(self._motivo)
            self._aviso_motivo.configure(text=str(error))
            self._aviso_motivo.pack(anchor="w", pady=(tema.ESPACIO, 0), after=self._motivo)
            return "break"
        except SigtacError as error:
            mostrar_error(self, error)
            return "break"
        nombre = self._ficha.nombre
        self.cancelar()
        mostrar_info(self, f"Episodio abierto: {nombre} espera triaje.")
        return "break"

    # ---- Sin identificar

    def _crear_sin_identificar(self, padre) -> ctk.CTkFrame:
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        lista = ctk.CTkFrame(marco, fg_color="transparent", height=ALTO_FILA * (self.FILAS_LISTA + 1))
        lista.pack_propagate(False)
        lista.pack(fill="x")
        self._tabla = TablaDatos(lista, self.COLUMNAS_NN, NADIE_SIN_IDENTIFICAR, al_seleccionar=self._nn_elegido)
        self._tabla.pack(fill="both", expand=True)

        # La identidad real del NN elegido
        self._identidad = ctk.CTkFrame(marco, fg_color="transparent")
        self._identidad.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        self._documento_nn, self._aviso_nn = self._fila_documento(self._identidad)
        self._mostrar_aviso(self._aviso_nn, AVISO_IDENTIFICAR)
        self._datos_nn = CamposPaciente(self._identidad, con_sexo_y_seguro=False)
        self._datos_nn.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        for campo in (self._documento_nn.campo_numero, *self._datos_nn.entradas):
            campo.bind("<Return>", self.identificar, add="+")
        self._boton_identificar = self._acciones(self._identidad, "Identificar", self.identificar)
        self._nn_elegido(None)
        return marco

    def _nn_elegido(self, id_paciente):
        if id_paciente is None:
            self._boton_identificar.configure(text=TEXTO_ELEGIR_NN, state="disabled")
        else:
            self._boton_identificar.configure(text="Identificar", state="normal")

    def identificar(self, _evento=None):
        """
        Registra la identidad real del NN elegido. Si el documento ya es de otro paciente, pregunta si fusionarlos:
        los episodios del NN pasan a ese paciente y el registro NN se da de baja (no se puede deshacer).
        """
        id_nn = self._tabla.seleccionado()
        if id_nn is None:
            return "break"
        tipo, numero = self._documento_nn.valores()
        try:
            existente = self._pacientes.buscar_por_documento(tipo.value, numero)
        except ValueError as error:
            self._documento_invalido(self._documento_nn, self._aviso_nn, error)
            return "break"
        except SigtacError as error:
            mostrar_error(self, error)
            return "break"
        self._documento_valido(self._documento_nn, self._aviso_nn, AVISO_IDENTIFICAR)
        try:
            if existente is not None:
                mensaje = self._fusionar(id_nn, existente, tipo, numero)
                if mensaje is None:
                    return "break"  # el usuario no confirmó
            else:
                datos = self._datos_nn.valores()
                paciente = self._pacientes.identificar(id_nn, tipo.value, numero, **datos)
                mensaje = f"Paciente identificado: {paciente.nombres} {paciente.apellidos}."
        except ValueError as error:
            mostrar_error(self, error)  # un dato mal escrito: la elección y lo escrito se conservan
            return "break"
        except SigtacError as error:
            mostrar_error(self, error)
            # Otro usuario pudo identificarlo mientras tanto: se recarga, y si sigue en la lista, sigue elegido
            self._recargar_nn()
            self._tabla.seleccionar(id_nn)
            self._nn_elegido(self._tabla.seleccionado())
            return "break"
        self._documento_nn.limpiar()
        self._datos_nn.limpiar()
        self._recargar_nn()
        mostrar_info(self, mensaje)
        return "break"

    def _fusionar(self, id_nn, existente, tipo, numero) -> str | None:
        nombre = f"{existente.nombres} {existente.apellidos}"
        pregunta = (f"{ETIQUETAS[tipo]} {numero} ya es de {nombre}.\n\n¿Fusionar el registro sin identificar con ese "
                    f"paciente? Sus episodios pasan a {nombre} y el registro sin identificar se da de baja. Los datos "
                    "escritos no se usan: valen los del paciente registrado. No se puede deshacer.")
        if not confirmar(self, pregunta):
            return None
        movidos = self._pacientes.fusionar(id_nn, existente.id_paciente)
        episodios = "1 episodio pasó" if movidos == 1 else f"{movidos} episodios pasaron"
        return f"Registros fusionados: {episodios} a {nombre}."

    # ---- Datos

    def _cargar_datos(self):
        """Los seguros y la lista de NN, al abrir. Si la BD falla, un solo aviso; la búsqueda sigue disponible."""
        try:
            seguros = self._pacientes.listar_seguros()
            nn = self._pacientes.listar_no_identificados()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudieron leer los datos de pacientes (%s).", type(error).__name__)
            mostrar_error(self, error)
            seguros, nn = [], []
        self._datos.cargar_seguros(seguros)
        self._mostrar_nn(nn)

    def _recargar_nn(self):
        try:
            nn = self._pacientes.listar_no_identificados()
        except (SigtacError, ValueError) as error:
            logger.warning("No se pudo actualizar la lista de NN (%s).", type(error).__name__)
            return
        self._mostrar_nn(nn)

    def _mostrar_nn(self, pacientes):
        self._tabla.cargar([(p.id_paciente, (p.id_paciente, formato.nombre_corto(p), p.nombre_seguro or ""))
                            for p in pacientes])
        self._modo.cambiar_texto("nn", f"Sin identificar ({len(pacientes)})")
        self._nn_elegido(None)

    def _cambiar_modo(self, modo: str):
        self._tarjeta.cambiar_textos(*TITULOS[modo])
        if modo == "nn":
            self._buscar.pack_forget()
            self._nn.pack(fill="x")
        else:
            self._nn.pack_forget()
            self._buscar.pack(fill="x")

    # ---- Piezas de la pantalla

    def _fila_documento(self, padre, texto_boton: str | None = None, accion=None):
        """El documento (y, si hay acción, su botón «Buscar» a la derecha) con la línea de aviso debajo."""
        fila = ctk.CTkFrame(padre, fg_color="transparent")
        fila.pack(fill="x")
        documento = CamposDocumento(fila)
        documento.pack(side="left", fill="x", expand=True)
        if accion is not None:
            BotonSecundario(fila, texto_boton, accion).pack(side="left", anchor="s", padx=(tema.ESPACIO, 0))
            documento.campo_numero.bind("<Return>", accion, add="+")
        aviso = ctk.CTkLabel(padre, text="", font=tema.fuente("pequena"), text_color=tema.COLOR_TEXTO_SECUNDARIO,
                             anchor="w", justify="left")
        documento.campo_numero.bind("<KeyRelease>", lambda _e: self._documento_editado(documento, aviso), add="+")
        return documento, aviso

    @staticmethod
    def _mostrar_aviso(aviso, texto: str = AVISO_BUSCAR, error: bool = False):
        aviso.configure(text=texto, text_color=tema.COLOR_ERROR if error else tema.COLOR_TEXTO_SECUNDARIO)
        aviso.pack(fill="x", pady=(tema.ESPACIO_2, 0))  # como el aviso bajo el documento del triaje

    def _documento_invalido(self, documento, aviso, error: ValueError):
        """Un documento mal escrito: borde rojo y la explicación bajo el campo, sin diálogo (como en el triaje)."""
        marcar_error(documento.campo_numero)
        self._documento_con_error[documento] = documento.valores()
        if aviso is self._aviso:
            self._mostrar_resultado(self._aviso)
        self._mostrar_aviso(aviso, str(error), error=True)

    def _documento_valido(self, documento, aviso, texto: str = AVISO_BUSCAR):
        marcar_error(documento.campo_numero, False)
        self._documento_con_error.pop(documento, None)
        aviso.configure(text=texto, text_color=tema.COLOR_TEXTO_SECUNDARIO)

    def _documento_editado(self, documento, aviso):
        """
        Al corregir un documento rechazado, el rojo y su explicación se van (soltar el Enter no lo corrige). Si se
        cambia el documento ya buscado, la ficha o «no encontrado» dejan de corresponderle y se retiran.
        """
        tipo, numero = documento.valores()
        rechazado = self._documento_con_error.get(documento)
        if rechazado is not None and (tipo, numero) != rechazado:
            texto = AVISO_BUSCAR if documento is self._documento else AVISO_IDENTIFICAR
            self._documento_valido(documento, aviso, texto)
        if documento is self._documento and self._buscado is not None and (tipo, numero.strip()) != self._buscado:
            self._buscado = self._paciente = None
            self.cerrar_formularios()
            self._mostrar_resultado(self._aviso)

    @staticmethod
    def _acciones(padre, texto: str, accion, cancelar=None) -> BotonPrimario:
        """La acción principal del formulario y, si se puede cancelar, «Cancelar» a su lado."""
        fila = ctk.CTkFrame(padre, fg_color="transparent")
        fila.pack(fill="x", pady=(tema.ESPACIO_2, 0))
        boton = BotonPrimario(fila, texto, accion)
        boton.pack(side="left")
        if cancelar is not None:
            BotonSecundario(fila, "Cancelar", cancelar).pack(side="left", padx=(tema.ESPACIO, 0))
        return boton

    def destroy(self):
        if self._tarea_foco is not None:
            self.after_cancel(self._tarea_foco)
            self._tarea_foco = None
        super().destroy()
