import pytest

from models.documento import DocumentoIdentidad, TipoDocumento

EXTRANJEROS = [TipoDocumento.CARNE_EXTRANJERIA, TipoDocumento.PASAPORTE, TipoDocumento.PERMISO_PERMANENCIA]


# ---- DNI: exactamente 8 dígitos
@pytest.mark.parametrize("numero", ["12345678", "00000000"])
def test_dni_valido(numero):
    documento = DocumentoIdentidad(TipoDocumento.DNI, numero)
    assert (documento.tipo, documento.numero) == (TipoDocumento.DNI, numero)


@pytest.mark.parametrize("numero", [
    "1234567",     # 7 dígitos (límite inferior)
    "123456789",   # 9 dígitos (límite superior)
    "1234567A",    # contiene una letra
    "1234 5678",   # espacio interno
    "",
    "١٢٣٤٥٦٧٨",    # dígitos arábigos: \d los aceptaría, [0-9] no
])
def test_dni_invalido_se_rechaza(numero):
    with pytest.raises(ValueError, match="DNI"):
        DocumentoIdentidad(TipoDocumento.DNI, numero)


# ---- Documentos extranjeros: de 6 a 12 letras o dígitos
@pytest.mark.parametrize("tipo", EXTRANJEROS)
@pytest.mark.parametrize("numero", ["123456", "AB1234", "001234567", "A12345678901"])
def test_documento_extranjero_valido(tipo, numero):
    assert DocumentoIdentidad(tipo, numero).numero == numero


@pytest.mark.parametrize("tipo", EXTRANJEROS)
@pytest.mark.parametrize("numero", [
    "12345",           # 5 caracteres (límite inferior)
    "A123456789012",   # 13 caracteres (límite superior)
    "AB-12345",        # guion
    "AB 12345",        # espacio interno
    "ÑA12345",         # letra fuera de A-Z
    "",
])
def test_documento_extranjero_invalido_se_rechaza(tipo, numero):
    with pytest.raises(ValueError, match="documento"):
        DocumentoIdentidad(tipo, numero)


# ---- Normalización
def test_el_numero_se_guarda_sin_espacios_en_los_extremos_y_en_mayusculas():
    assert DocumentoIdentidad(TipoDocumento.PASAPORTE, "  ab123456 ").numero == "AB123456"
    assert DocumentoIdentidad(TipoDocumento.DNI, " 12345678\n").numero == "12345678"


def test_el_tipo_se_acepta_como_texto():
    # Así llega desde la BD (tipo_documento.codigo) o desde un formulario
    assert DocumentoIdentidad("CE", "001234567").tipo is TipoDocumento.CARNE_EXTRANJERIA


@pytest.mark.parametrize("tipo", ["dni", "XX", "", None, 1])
def test_tipo_desconocido_se_rechaza(tipo):
    with pytest.raises(ValueError, match="Tipo de documento"):
        DocumentoIdentidad(tipo, "12345678")


@pytest.mark.parametrize("numero", [None, 12345678])
def test_el_numero_debe_ser_texto(numero):
    with pytest.raises(ValueError, match="texto"):
        DocumentoIdentidad(TipoDocumento.DNI, numero)


# ---- Objeto valor
def test_documentos_con_mismo_tipo_y_numero_son_iguales():
    a = DocumentoIdentidad(TipoDocumento.PASAPORTE, "ab123456")
    b = DocumentoIdentidad("PAS", "AB123456")
    assert a == b and hash(a) == hash(b)


def test_mismo_numero_con_distinto_tipo_son_documentos_distintos():
    assert DocumentoIdentidad(TipoDocumento.DNI, "12345678") != DocumentoIdentidad(TipoDocumento.PASAPORTE, "12345678")


def test_el_documento_es_de_solo_lectura():
    documento = DocumentoIdentidad(TipoDocumento.DNI, "12345678")
    with pytest.raises(AttributeError):
        documento.numero = "00000000"
    with pytest.raises(AttributeError):
        documento.otro_atributo = 1  # __slots__ impide añadir atributos


def test_str_muestra_tipo_y_numero():
    assert str(DocumentoIdentidad(TipoDocumento.CARNE_EXTRANJERIA, "001234567")) == "CE 001234567"


# ---- Datos personales fuera de mensajes de error y repr
def test_el_mensaje_de_error_no_incluye_el_numero():
    with pytest.raises(ValueError) as error:
        DocumentoIdentidad(TipoDocumento.DNI, "1234567X")
    assert "1234567X" not in str(error.value)


def test_repr_no_incluye_el_numero():
    assert "12345678" not in repr(DocumentoIdentidad(TipoDocumento.DNI, "12345678"))
