from datetime import date

import pytest

from models.persona import Empleado, Enfermero, Medico, Paciente, PersonalLimpieza, Persona


def fijar_hoy(monkeypatch, hoy: date):
    """Hace que date.today() dentro de models.persona devuelva una fecha fija."""
    class FechaFija(date):
        @classmethod
        def today(cls):
            return hoy

    monkeypatch.setattr("models.persona.date", FechaFija)


def nuevo_paciente(activo=True, fecha_nac=date(1959, 5, 14)):
    return Paciente(1, "70123456", "Rosa", "Mendoza Flores", fecha_nac, "EsSalud", activo)


def nuevo_enfermero():
    return Enfermero(3, "33333333", "Ana", "Torres", date(1998, 7, 20),
                     "Licenciado(a) en Enfermería", "CEP-98765", "Triaje")


def nuevo_medico():
    return Medico(5, "55555555", "Luis", "Rojas", date(1985, 9, 30),
                  "Médico Internista", "CMP-67890", "Medicina Interna")


def nuevo_limpieza():
    return PersonalLimpieza(4, "44444444", "Juan", "Pérez", date(1999, 11, 5),
                            "Operario de Limpieza", "Mañana")


# ---- Clases abstractas
def test_persona_es_abstracta():
    with pytest.raises(TypeError):
        Persona("70123456", "Rosa", "Mendoza", date(1959, 5, 14))


def test_empleado_es_abstracto():
    with pytest.raises(TypeError):
        Empleado(1, "11111111", "Admin", "Sistema", date(1990, 1, 1), "Ingeniero de Sistemas")


# ---- Paciente
def test_paciente_expone_sus_datos():
    paciente = nuevo_paciente()
    assert paciente.id_paciente == 1
    assert paciente.dni == "70123456"
    assert paciente.nombres == "Rosa"
    assert paciente.apellidos == "Mendoza Flores"
    assert paciente.fecha_nac == date(1959, 5, 14)
    assert paciente.seguro == "EsSalud"
    assert isinstance(paciente, Persona)


def test_paciente_nuevo_esta_activo_por_defecto():
    assert nuevo_paciente().activo is True


def test_paciente_se_reconstruye_inactivo_desde_la_bd():
    # estado_registro = FALSE en la BD llega como activo=False
    assert nuevo_paciente(activo=False).activo is False


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


def test_resumen_de_paciente():
    assert nuevo_paciente().obtener_resumen() == (
        "PACIENTE: [70123456 - Mendoza Flores, Rosa] | Seguro: EsSalud"
    )


def test_los_atributos_son_de_solo_lectura():
    paciente = nuevo_paciente()
    with pytest.raises(AttributeError):
        paciente.dni = "00000000"
    with pytest.raises(AttributeError):
        paciente.activo = True


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


def test_calcular_edad_de_un_recien_nacido(monkeypatch):
    fijar_hoy(monkeypatch, date(2026, 10, 12))
    assert nuevo_paciente(fecha_nac=date(2026, 10, 12)).calcular_edad() == 0


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


# ---- Empleado y subclases
def test_empleado_expone_sus_datos():
    medico = nuevo_medico()
    assert medico.id_empleado == 5
    assert medico.cargo == "Médico Internista"
    assert medico.colegiatura == "CMP-67890"
    assert isinstance(medico, Empleado)
    assert isinstance(medico, Persona)


def test_resumen_de_empleado_con_colegiatura():
    assert nuevo_medico().obtener_resumen() == (
        "EMPLEADO [5] - Rojas, Luis | Cargo: Médico Internista | Registro: CMP-67890"
    )


def test_personal_de_limpieza_no_tiene_colegiatura():
    limpieza = nuevo_limpieza()
    assert limpieza.colegiatura is None
    assert limpieza.obtener_resumen() == "EMPLEADO [4] - Pérez, Juan | Cargo: Operario de Limpieza"


def test_resumen_es_polimorfico():
    personas = [nuevo_paciente(), nuevo_enfermero(), nuevo_medico(), nuevo_limpieza()]
    resumenes = [persona.obtener_resumen() for persona in personas]
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


@pytest.mark.parametrize("fabrica", [nuevo_enfermero, nuevo_medico, nuevo_limpieza])
def test_permiso_inexistente_se_rechaza(fabrica):
    assert fabrica().tiene_permiso("") is False
    assert fabrica().tiene_permiso("TRIAJE") is False  # distingue mayúsculas
