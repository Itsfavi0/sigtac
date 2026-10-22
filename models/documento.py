import re
from enum import StrEnum


class TipoDocumento(StrEnum):
    """Tipos de documento de identidad. Los valores coinciden con tipo_documento.codigo de la BD."""
    DNI = "DNI"
    CARNE_EXTRANJERIA = "CE"
    PASAPORTE = "PAS"
    PERMISO_PERMANENCIA = "CPP"


# Formato de cada tipo. Es la única definición del formato en el proyecto.
# El DNI peruano es exacto (8 dígitos). Para los documentos extranjeros se acepta un formato
# permisivo (letras y dígitos), porque varía según el país emisor y la fecha de emisión.
_FORMATO_EXTRANJERO = re.compile(r"[A-Z0-9]{6,12}")
_FORMATOS = {
    TipoDocumento.DNI: re.compile(r"[0-9]{8}"),
    TipoDocumento.CARNE_EXTRANJERIA: _FORMATO_EXTRANJERO,
    TipoDocumento.PASAPORTE: _FORMATO_EXTRANJERO,
    TipoDocumento.PERMISO_PERMANENCIA: _FORMATO_EXTRANJERO,
}


class DocumentoIdentidad:
    """
    Documento de identidad de una persona: tipo + número.

    Es un objeto valor: no cambia después de creado y dos documentos son iguales si tienen
    el mismo tipo y número. El número se normaliza (sin espacios en los extremos y en
    mayúsculas) antes de validarlo.
    """
    __slots__ = ("_tipo", "_numero")

    def __init__(self, tipo: TipoDocumento | str, numero: str):
        try:
            tipo = TipoDocumento(tipo)
        except ValueError:
            raise ValueError("Tipo de documento no reconocido.") from None
        if not isinstance(numero, str):
            raise ValueError("El número de documento debe ser texto.")
        numero = numero.strip().upper()
        # Los mensajes de error no incluyen el número: es un dato personal y podría terminar en un log.
        if _FORMATOS[tipo].fullmatch(numero) is None:
            if tipo is TipoDocumento.DNI:
                raise ValueError("El DNI debe tener exactamente 8 dígitos.")
            raise ValueError("El número de documento debe tener entre 6 y 12 letras o dígitos.")
        self._tipo = tipo
        self._numero = numero

    @property
    def tipo(self) -> TipoDocumento: return self._tipo

    @property
    def numero(self) -> str: return self._numero

    def __eq__(self, otro):
        if not isinstance(otro, DocumentoIdentidad):
            return NotImplemented
        return (self._tipo, self._numero) == (otro._tipo, otro._numero)

    def __hash__(self):
        return hash((self._tipo, self._numero))

    def __str__(self):
        return f"{self._tipo.value} {self._numero}"

    def __repr__(self):
        # Sin el número: un repr puede acabar en un log o en un mensaje de error.
        return f"DocumentoIdentidad({self._tipo.value}, ***)"
