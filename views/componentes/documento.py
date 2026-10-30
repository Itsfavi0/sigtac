"""Campos del documento de identidad (tipo + número): login y pacientes los escriben igual."""
import customtkinter as ctk

from models.documento import TipoDocumento
from views import tema
from views.componentes.campos import campo_texto, etiqueta_campo
from views.componentes.foco import marcar_foco

# Texto que ve el usuario para cada tipo (el valor del Enum es el código de la BD: DNI, CE, PAS, CPP)
ETIQUETAS = {
    TipoDocumento.DNI: "DNI",
    TipoDocumento.CARNE_EXTRANJERIA: "Carné de extranjería",
    TipoDocumento.PASAPORTE: "Pasaporte",
    TipoDocumento.PERMISO_PERMANENCIA: "Permiso temporal (CPP)",
}
_TIPO_POR_ETIQUETA = {etiqueta: tipo for tipo, etiqueta in ETIQUETAS.items()}


class CamposDocumento(ctk.CTkFrame):
    """
    Etiqueta «Documento de identidad», el tipo (lista) y el número.

    No valida el número: lo valida DocumentoIdentidad en el controlador, y su ValueError vuelve a la vista,
    que lo muestra con mostrar_error. Así el formato del DNI se define en un solo lugar.
    """

    def __init__(self, padre):
        super().__init__(padre, fg_color="transparent")
        etiqueta_campo(self, "Documento de identidad").grid(row=0, column=0, columnspan=2, sticky="w",
                                                            pady=(0, tema.ESPACIO_MINIMO))
        self._tipo = ctk.CTkComboBox(
            self, values=list(ETIQUETAS.values()), state="readonly", width=200, height=tema.ALTO_CONTROL,
            corner_radius=tema.RADIO_CONTROL, border_width=1, font=tema.fuente("normal"),
            dropdown_font=tema.fuente("normal"), fg_color=tema.COLOR_SUPERFICIE, border_color=tema.COLOR_BORDE_CAMPO,
            button_color=tema.COLOR_BORDE_CAMPO, button_hover_color=tema.COLOR_TEXTO_SECUNDARIO,
            text_color=tema.COLOR_TEXTO, dropdown_fg_color=tema.COLOR_SUPERFICIE,
            dropdown_hover_color=tema.COLOR_ACTIVO, dropdown_text_color=tema.COLOR_TEXTO)
        self._tipo.set(ETIQUETAS[TipoDocumento.DNI])
        self._tipo.grid(row=1, column=0, sticky="w", padx=(0, tema.ESPACIO))
        # Con el teclado: el foco se ve, ↑/↓ cambian el tipo y espacio o Alt+↓ abren la lista. La lista es de solo
        # lectura, así que sin esto no se podía elegir otro tipo sin el mouse.
        marcar_foco(self._tipo)
        caja = self._tipo._entry
        caja.bind("<Up>", lambda _e: self.cambiar_tipo(-1), add="+")
        caja.bind("<Down>", lambda _e: self.cambiar_tipo(1), add="+")
        for tecla in ("<space>", "<Alt-Down>"):
            caja.bind(tecla, lambda _e: self._abrir_lista(), add="+")
        self._numero = campo_texto(self, "Número")
        self._numero.grid(row=1, column=1, sticky="ew")
        self.grid_columnconfigure(1, weight=1)
        self._bloqueado = False

    def valores(self) -> tuple[TipoDocumento, str]:
        """El tipo elegido y el número tal como se escribió (el controlador lo normaliza y valida)."""
        return _TIPO_POR_ETIQUETA[self._tipo.get()], self._numero.get()

    def fijar(self, tipo: TipoDocumento, numero: str):
        """Pone un documento ya conocido (p. ej. el que se buscó antes de registrar al paciente)."""
        self._escribir(ETIQUETAS[TipoDocumento(tipo)], numero)

    def limpiar(self):
        self._escribir(ETIQUETAS[TipoDocumento.DNI], "")

    def cambiar_tipo(self, paso: int) -> str:
        """Pasa al tipo anterior (-1) o al siguiente (+1), sin dar la vuelta. Bloqueado no cambia nada."""
        if not self._bloqueado:
            etiquetas = list(ETIQUETAS.values())
            actual = etiquetas.index(self._tipo.get())
            self._tipo.set(etiquetas[max(0, min(len(etiquetas) - 1, actual + paso))])
        return "break"  # que Tk no haga además lo suyo con la tecla

    def _abrir_lista(self) -> str:
        if not self._bloqueado:
            self._tipo._open_dropdown_menu()
        return "break"

    def _escribir(self, etiqueta: str, numero: str):
        # Un campo deshabilitado no acepta texto: se habilita un momento y se deja como estaba
        bloqueado = self._bloqueado
        self.bloquear(False)
        self._tipo.set(etiqueta)
        self._numero.delete(0, "end")
        self._numero.insert(0, numero)
        self.bloquear(bloqueado)

    def bloquear(self, bloqueado: bool = True):
        """Al editar un paciente el documento no se modifica: los campos quedan solo para leer."""
        self._bloqueado = bloqueado
        self._tipo.configure(state="disabled" if bloqueado else "readonly")
        self._numero.configure(state="disabled" if bloqueado else "normal")

    def enfocar(self):
        self._numero.focus_set()

    @property
    def campo_numero(self) -> ctk.CTkEntry:
        """La caja del número, para que la pantalla le asocie teclas (Enter para la acción principal)."""
        return self._numero
