from datetime import date, datetime

import pytest

from models.persona import (
    Empleado, Enfermero, Medico, Paciente, PersonalLimpieza, Persona, es_dni_valido,
)


def fijar_hoy(monkeypatch, hoy: date):
    """Hace que la "fecha de hoy" de models.persona sea una fecha fija."""
    monkeypatch.setattr("models.persona._hoy", lambda: hoy)


def nuevo_paciente(**cambios):
    datos = dict(id_paciente=1, dni="70123456", nombres="Rosa", apellidos="Mendoza Flores",
                 fecha_nac=date(1959, 5, 14), sexo="F", id_seguro=1)
    datos.update(cambios)
    return Paciente(**datos)


def nuevo_enfermero(**cambios):
    datos = dict(id_empleado=3, dni="33333333", nombres="Ana", apellidos="Torres",
                 fecha_nac=date(1998, 7, 20), cargo="Licenciado(a) en Enfermería",
                 colegiatura="CEP-98765", area="Triaje")
    datos.update(cambios)
    return Enfermero(**datos)


def nuevo_medico(**cambios):
    datos = dict(id_empleado=5, dni="55555555", nombres="Luis", apellidos="Rojas",
                 fecha_nac=date(1985, 9, 30), cargo="Médico Internista",
                 colegiatura="CMP-67890", especialidad="Medicina Interna")
    datos.update(cambios)
    return Medico(**datos)


def nuevo_limpieza(**cambios):
    datos = dict(id_empleado=4, dni="44444444", nombres="Juan", apellidos="Pérez",
                 fecha_nac=date(1999, 11, 5), cargo="Operario de Limpieza", turno="MAÑANA")
    datos.update(cambios)
    return PersonalLimpieza(**datos)


FABRICAS = [nuevo_paciente, nuevo_enfermero, nuevo_medico, nuevo_limpieza]
FABRICAS_EMPLEADO = [nuevo_enfermero, nuevo_medico, nuevo_limpieza]


# ---- Clases abstractas
def test_persona_es_abstracta():
    with pytest.raises(TypeError):
        Persona("70123456", "Rosa", "Mendoza", date(1959, 5, 14))


def test_empleado_es_abstracto():
    with pytest.raises(TypeError):
        Empleado(1, "11111111", "Admin", "Sistema", date(1990, 1, 1), "Ingeniero de Sistemas")


# ---- Validaciones comunes de Persona (se prueban en todas las subclases)
@pytest.mark.parametrize("dni", [
    "1234567",     # 7 dígitos (límite inferior)
    "123456789",   # 9 dígitos (límite superior)
    "1234567A",    # contiene una letra
    " 12345678",   # espacios: el DNI debe llegar ya limpio
    "",
    None,
    12345678,      # número en lugar de texto
    "١٢٣٤٥٦٧٨",    # dígitos arábigos: \d los aceptaría, [0-9] no
])
@pytest.mark.parametrize("fabrica", FABRICAS)
def test_dni_invalido_se_rechaza(fabrica, dni):
    with pytest.raises(ValueError, match="DNI"):
        fabrica(dni=dni)


def test_el_mensaje_de_error_no_incluye_el_dni():
    # Los mensajes de error pueden acabar en un log: no deben llevar datos personales.
    with pytest.raises(ValueError) as error:
        nuevo_paciente(dni="1234567X")
    assert "1234567X" not in str(error.value)


@pytest.mark.parametrize("dni, esperado", [
    ("12345678", True), ("00000000", True), ("1234567", False), ("12345678 ", False), (None, False),
])
def test_es_dni_valido(dni, esperado):
    assert es_dni_valido(dni) is esperado


@pytest.mark.parametrize("campo", ["nombres", "apellidos"])
@pytest.mark.parametrize("valor", ["", "   ", None, 123])
@pytest.mark.parametrize("fabrica", FABRICAS)
def test_nombres_y_apellidos_obligatorios(fabrica, campo, valor):
    with pytest.raises(ValueError, match=campo):
        fabrica(**{campo: valor})


def test_nombres_y_apellidos_se_guardan_sin_espacios_en_los_extremos():
    paciente = nuevo_paciente(nombres="  Rosa ", apellidos=" Mendoza Flores  ")
    assert paciente.nombres == "Rosa"
    assert paciente.apellidos == "Mendoza Flores"


@pytest.mark.parametrize("fecha", ["1959-05-14", None, datetime(1959, 5, 14, 10, 30)])
def test_fecha_de_nacimiento_debe_ser_date(fecha):
    with pytest.raises(ValueError, match="fecha"):
        nuevo_paciente(fecha_nac=fecha)


def test_fecha_de_nacimiento_futura_se_rechaza(monkeypatch):
    fijar_hoy(monkeypatch, date(2026, 10, 12))
    with pytest.raises(ValueError, match="futura"):
        nuevo_paciente(fecha_nac=date(2026, 10, 13))  # un día después de hoy (límite)


def test_fecha_de_nacimiento_de_hoy_se_acepta(monkeypatch):
    fijar_hoy(monkeypatch, date(2026, 10, 12))
    assert nuevo_paciente(fecha_nac=date(2026, 10, 12)).calcular_edad() == 0


# ---- Paciente
def test_paciente_expone_sus_datos():
    paciente = nuevo_paciente(nombre_seguro="EsSalud")
    assert paciente.id_paciente == 1
    assert paciente.dni == "70123456"
    assert paciente.nombres == "Rosa"
    assert paciente.apellidos == "Mendoza Flores"
    assert paciente.fecha_nac == date(1959, 5, 14)
    assert paciente.sexo == "F"
    assert paciente.id_seguro == 1
    assert paciente.nombre_seguro == "EsSalud"
    assert isinstance(paciente, Persona)


def test_paciente_nuevo_sin_id_aun_no_guardado():
    # Un paciente recién registrado no tiene id hasta que el DAO lo inserta.
    assert nuevo_paciente(id_paciente=None).id_paciente is None


@pytest.mark.parametrize("sexo", ["M", "F"])
def test_sexo_valido(sexo):
    assert nuevo_paciente(sexo=sexo).sexo == sexo


@pytest.mark.parametrize("sexo", ["m", "f", "X", "", "MF", None])
def test_sexo_invalido_se_rechaza(sexo):  # coincide con CH_paciente_sexo de la BD
    with pytest.raises(ValueError, match="sexo"):
        nuevo_paciente(sexo=sexo)


@pytest.mark.parametrize("id_seguro", [None, 0, -1, "1", 1.5, True])
def test_id_seguro_invalido_se_rechaza(id_seguro):
    with pytest.raises(ValueError, match="id_seguro"):
        nuevo_paciente(id_seguro=id_seguro)


@pytest.mark.parametrize("id_paciente", [0, -1, "1", True])
def test_id_paciente_invalido_se_rechaza(id_paciente):
    with pytest.raises(ValueError, match="id_paciente"):
        nuevo_paciente(id_paciente=id_paciente)


def test_nombre_seguro_vacio_se_rechaza():
    with pytest.raises(ValueError, match="nombre_seguro"):
        nuevo_paciente(nombre_seguro="  ")


def test_paciente_nuevo_esta_activo_por_defecto():
    assert nuevo_paciente().activo is True


def test_paciente_se_reconstruye_inactivo_desde_la_bd():
    # estado_registro = FALSE en la BD llega como activo=False
    assert nuevo_paciente(activo=False).activo is False


@pytest.mark.parametrize("activo", [1, 0, "True", None])
def test_activo_debe_ser_booleano(activo):
    # El DAO debe convertir el 0/1 de MySQL a bool antes de crear el objeto.
    with pytest.raises(ValueError, match="activo"):
        nuevo_paciente(activo=activo)


def test_anular_paciente_es_baja_logica():  # RN-11
    paciente = nuevo_paciente()
    paciente.anular()
    assert paciente.activo is False
    # El objeto se conserva con todos sus datos: no hay borrado físico
    assert paciente.dni == "70123456"


def test_anular_dos_veces_no_falla():
    paciente = nuevo_paciente()
    paciente.anular()
    paciente.anular()
    assert paciente.activo is False


def test_resumen_de_paciente_con_nombre_de_seguro():
    assert nuevo_paciente(nombre_seguro="EsSalud").obtener_resumen() == (
        "PACIENTE: [70123456 - Mendoza Flores, Rosa] | Sexo: F | Seguro: EsSalud"
    )


def test_resumen_de_paciente_sin_nombre_de_seguro_muestra_el_id():
    assert nuevo_paciente().obtener_resumen().endswith("| Seguro: id 1")


def test_los_atributos_son_de_solo_lectura():
    paciente = nuevo_paciente()
    with pytest.raises(AttributeError):
        paciente.dni = "00000000"
    with pytest.raises(AttributeError):
        paciente.activo = True
    with pytest.raises(AttributeError):
        paciente.sexo = "M"


# ---- calcular_edad: valores límite alrededor del cumpleaños
@pytest.mark.parametrize("hoy, edad_esperada", [
    (date(2026, 5, 13), 66),  # un día antes del cumpleaños
    (date(2026, 5, 14), 67),  # el mismo día del cumpleaños
    (date(2026, 5, 15), 67),  # un día después
    (date(2026, 1, 1), 66),   # inicio del año, antes del cumpleaños
    (date(2026, 12, 31), 67), # fin del año, después del cumpleaños
])
def test_calcular_edad_alrededor_del_cumpleanos(monkeypatch, hoy, edad_esperada):
    fijar_hoy(monkeypatch, hoy)
    assert nuevo_paciente().calcular_edad() == edad_esperada


@pytest.mark.parametrize("hoy, edad_esperada", [
    (date(2025, 2, 28), 24),  # año no bisiesto: el 28 de febrero aún no cumple
    (date(2025, 3, 1), 25),   # cumple el 1 de marzo
    (date(2028, 2, 29), 28),  # año bisiesto: cumple el 29 de febrero
])
def test_calcular_edad_nacido_el_29_de_febrero(monkeypatch, hoy, edad_esperada):
    fijar_hoy(monkeypatch, hoy)
    assert nuevo_paciente(fecha_nac=date(2000, 2, 29)).calcular_edad() == edad_esperada


def test_calcular_edad_tambien_funciona_en_empleados(monkeypatch):
    fijar_hoy(monkeypatch, date(2026, 7, 20))
    assert nuevo_enfermero().calcular_edad() == 28


# ---- Empleado: datos comunes, validaciones y baja lógica
def test_empleado_expone_sus_datos():
    medico = nuevo_medico()
    assert medico.id_empleado == 5
    assert medico.cargo == "Médico Internista"
    assert medico.colegiatura == "CMP-67890"
    assert isinstance(medico, Empleado)
    assert isinstance(medico, Persona)


@pytest.mark.parametrize("fabrica", FABRICAS_EMPLEADO)
def test_empleado_sin_id_aun_no_guardado(fabrica):
    assert fabrica(id_empleado=None).id_empleado is None


@pytest.mark.parametrize("id_empleado", [0, -5, "3", False])
@pytest.mark.parametrize("fabrica", FABRICAS_EMPLEADO)
def test_id_empleado_invalido_se_rechaza(fabrica, id_empleado):
    with pytest.raises(ValueError, match="id_empleado"):
        fabrica(id_empleado=id_empleado)


@pytest.mark.parametrize("cargo", ["", "  ", None])
@pytest.mark.parametrize("fabrica", FABRICAS_EMPLEADO)
def test_cargo_obligatorio(fabrica, cargo):
    with pytest.raises(ValueError, match="cargo"):
        fabrica(cargo=cargo)


@pytest.mark.parametrize("fabrica", [nuevo_enfermero, nuevo_medico])
def test_colegiatura_es_opcional_pero_no_vacia(fabrica):
    assert fabrica(colegiatura=None).colegiatura is None
    with pytest.raises(ValueError, match="colegiatura"):
        fabrica(colegiatura="  ")


@pytest.mark.parametrize("fabrica", FABRICAS_EMPLEADO)
def test_empleado_nuevo_esta_activo_por_defecto(fabrica):
    assert fabrica().activo is True


@pytest.mark.parametrize("fabrica", FABRICAS_EMPLEADO)
def test_empleado_se_reconstruye_inactivo_desde_la_bd(fabrica):
    assert fabrica(activo=False).activo is False


@pytest.mark.parametrize("fabrica", FABRICAS_EMPLEADO)
def test_anular_empleado_es_baja_logica(fabrica):  # RN-11
    empleado = fabrica()
    empleado.anular()
    assert empleado.activo is False
    assert empleado.id_empleado is not None  # se conserva el registro


@pytest.mark.parametrize("fabrica", FABRICAS_EMPLEADO)
def test_activo_de_empleado_debe_ser_booleano(fabrica):
    with pytest.raises(ValueError, match="activo"):
        fabrica(activo=1)


# ---- Atributos propios de cada subclase
def test_enfermero_tiene_area():
    assert nuevo_enfermero().area == "Triaje"


@pytest.mark.parametrize("area", ["", "   ", None])
def test_area_de_enfermero_obligatoria(area):
    with pytest.raises(ValueError, match="area"):
        nuevo_enfermero(area=area)


def test_medico_tiene_especialidad():
    assert nuevo_medico().especialidad == "Medicina Interna"


@pytest.mark.parametrize("especialidad", ["", "   ", None])
def test_especialidad_de_medico_obligatoria(especialidad):
    with pytest.raises(ValueError, match="especialidad"):
        nuevo_medico(especialidad=especialidad)


@pytest.mark.parametrize("turno", ["MAÑANA", "TARDE", "NOCHE"])
def test_turnos_validos(turno):
    assert nuevo_limpieza(turno=turno).turno == turno


@pytest.mark.parametrize("turno", ["mañana", "MANANA", "MADRUGADA", "", None])
def test_turno_invalido_se_rechaza(turno):  # coincide con CH_empleado_turno de la BD
    with pytest.raises(ValueError, match="turno"):
        nuevo_limpieza(turno=turno)


def test_personal_de_limpieza_no_tiene_colegiatura():
    assert nuevo_limpieza().colegiatura is None


# ---- Resúmenes (polimorfismo)
def test_resumen_de_medico():
    assert nuevo_medico().obtener_resumen() == (
        "EMPLEADO [5] - Rojas, Luis | Cargo: Médico Internista | Registro: CMP-67890"
        " | Especialidad: Medicina Interna"
    )


def test_resumen_de_enfermero():
    assert nuevo_enfermero().obtener_resumen() == (
        "EMPLEADO [3] - Torres, Ana | Cargo: Licenciado(a) en Enfermería | Registro: CEP-98765"
        " | Área: Triaje"
    )


def test_resumen_de_personal_de_limpieza_sin_colegiatura():
    assert nuevo_limpieza().obtener_resumen() == (
        "EMPLEADO [4] - Pérez, Juan | Cargo: Operario de Limpieza | Turno: MAÑANA"
    )


def test_resumen_es_polimorfico():
    resumenes = [fabrica().obtener_resumen() for fabrica in FABRICAS]
    assert resumenes[0].startswith("PACIENTE:")
    assert all(resumen.startswith("EMPLEADO") for resumen in resumenes[1:])


# ---- Permisos por subclase
# Estas pruebas fijan el comportamiento actual de tiene_permiso(). Los permisos también
# existen en la tabla `rol`; cuál de las dos fuentes se conserva se decidirá en la Fase 4.
@pytest.mark.parametrize("fabrica, permitidos", [
    (nuevo_enfermero, {"triaje", "camas"}),
    (nuevo_medico, {"triaje", "camas", "historias_clinicas"}),
    (nuevo_limpieza, {"limpieza"}),
])
def test_permisos_por_tipo_de_empleado(fabrica, permitidos):
    empleado = fabrica()
    modulos = {"triaje", "camas", "historias_clinicas", "limpieza", "reportes", "usuarios"}
    for modulo in modulos:
        assert empleado.tiene_permiso(modulo) is (modulo in permitidos), modulo


@pytest.mark.parametrize("fabrica", FABRICAS_EMPLEADO)
def test_permiso_inexistente_se_rechaza(fabrica):
    assert fabrica().tiene_permiso("") is False
    assert fabrica().tiene_permiso("TRIAJE") is False  # distingue mayúsculas
