"""Campos del documento de identidad (tipo + número): login y pacientes los escriben igual."""
import customtkinter as ctk

from models.documento import TipoDocumento
from views import tema
from views.componentes.campos import campo_texto, etiqueta_campo, lista_opciones, mover_opcion

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
        # La lista empieza en DNI y se maneja con el teclado (ver lista_opciones)
        self._tipo = lista_opciones(self, list(ETIQUETAS.values()), width=200)
        self._tipo.grid(row=1, column=0, sticky="w", padx=(0, tema.ESPACIO))
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
        return mover_opcion(self._tipo, paso)

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
