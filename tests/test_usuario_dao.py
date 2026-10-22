from unittest.mock import MagicMock

import pytest
from mysql.connector import Error as DBError

from dao import base_dao, usuario_dao
from dao.usuario_dao import UsuarioDAO
from models.excepciones import ConexionBDError
from utils.security import generar_hash

TIPO = "DNI"
DNI = "33333333"
CLAVE = "Clave#Prueba1"


@pytest.fixture(scope="module")
def hash_clave():
    return generar_hash(CLAVE)  # bcrypt es lento: se calcula una sola vez


def fila(hash_clave, activo=1, intentos=0, bloqueada=0, bloqueado_hasta=None):
    return {
        "id_empleado": 3, "tipo_documento": TIPO, "num_documento": DNI, "nombres": "Ana", "apellidos": "Pérez", "colegiatura": None,
        "cargo_nombre": "Licenciado(a) en Enfermería", "cargo_tipo": "Enfermería",
        "id_usuario": 3, "hash_clave": hash_clave, "activo": activo,
        "id_rol": 4, "nombre_rol": "Enfermero de Triaje",
        "intentos_fallidos": intentos, "bloqueado_hasta": bloqueado_hasta, "bloqueada": bloqueada,
    }


class BD:
    """Conexión simulada: devuelve la fila indicada y recuerda cómo se usó."""

    def __init__(self, monkeypatch, row=None, error_en_execute=None, error_de_conexion=None, errores_en_secuencia=None):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        if error_en_execute:
            self.cursor.execute.side_effect = error_en_execute
        if errores_en_secuencia:  # p. ej. [None, DBError(..)]: el 1.º execute (SELECT) funciona y el 2.º falla
            self.cursor.execute.side_effect = errores_en_secuencia
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        if error_de_conexion:
            self.clase.return_value.obtener_conexion.side_effect = error_de_conexion
        else:
            self.clase.return_value.obtener_conexion.return_value = conexion
        # La conexión se pide en BaseDAO: se reemplaza ahí
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)


@pytest.fixture
def senuelo(monkeypatch):
    """Espía la verificación señuelo para comprobar cuándo se usa."""
    espia = MagicMock()
    monkeypatch.setattr(usuario_dao, "simular_verificacion", espia)
    return espia


# ---- Login correcto
def test_login_correcto_devuelve_la_sesion_sin_el_hash(monkeypatch, senuelo, hash_clave):
    BD(monkeypatch, fila(hash_clave))
    sesion = UsuarioDAO.autenticar(TIPO, DNI, CLAVE)
    assert sesion["nombre_rol"] == "Enfermero de Triaje"
    assert sesion["id_empleado"] == 3
    assert not {"hash_clave", "intentos_fallidos", "bloqueado_hasta", "bloqueada"} & sesion.keys()
    senuelo.assert_not_called()


def test_el_documento_se_limpia_de_espacios(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave))
    assert UsuarioDAO.autenticar(TIPO, f"  {DNI}  ", CLAVE) is not None
    assert bd.cursor.execute.call_args.args[1] == (TIPO, DNI)


def test_login_de_empleado_con_carne_de_extranjeria(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, {**fila(hash_clave), "tipo_documento": "CE", "num_documento": "001234567"})
    sesion = UsuarioDAO.autenticar("CE", "001234567", CLAVE)
    assert sesion["num_documento"] == "001234567"
    assert bd.cursor.execute.call_args.args[1] == ("CE", "001234567")


def test_la_consulta_esta_parametrizada(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave))
    UsuarioDAO.autenticar(TIPO, DNI, CLAVE)
    consulta, parametros = bd.cursor.execute.call_args.args
    assert "%s" in consulta
    assert DNI not in consulta      # el dato viaja aparte, nunca dentro del SQL
    assert "WHERE td.codigo = %s AND e.num_documento = %s" in " ".join(consulta.split())
    assert parametros == (TIPO, DNI)


# ---- Fallos de autenticación
def test_clave_incorrecta(monkeypatch, senuelo, hash_clave):
    BD(monkeypatch, fila(hash_clave))
    assert UsuarioDAO.autenticar(TIPO, DNI, "otra-clave") is None


def test_usuario_inexistente_usa_el_senuelo(monkeypatch, senuelo):
    BD(monkeypatch, row=None)
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is None
    senuelo.assert_called_once_with(CLAVE)


def test_cuenta_desactivada_se_rechaza_aunque_la_clave_sea_correcta(monkeypatch, senuelo, hash_clave):
    BD(monkeypatch, fila(hash_clave, activo=0))
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is None
    senuelo.assert_called_once_with(CLAVE)


@pytest.mark.parametrize("hash_vacio", [None, ""])
def test_usuario_sin_hash_usa_el_senuelo(monkeypatch, senuelo, hash_vacio):
    BD(monkeypatch, fila(hash_vacio))
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is None
    senuelo.assert_called_once_with(CLAVE)


# ---- Validación de entradas: ni siquiera se consulta la BD
@pytest.mark.parametrize("tipo, dni, clave", [
    (TIPO, None, CLAVE), (TIPO, "", CLAVE), (TIPO, DNI, None), (TIPO, DNI, ""), (TIPO, 12345678, CLAVE),
    (TIPO, DNI, 123456),
    (None, DNI, CLAVE), ("", DNI, CLAVE), ("dni", DNI, CLAVE), ("XX", DNI, CLAVE),  # tipo desconocido
    (TIPO, "1234", CLAVE),               # muy corto
    (TIPO, "123456789", CLAVE),          # muy largo
    (TIPO, "abcdefgh", CLAVE),           # no numérico
    (TIPO, "1111111١", CLAVE),           # dígito árabe: \d lo aceptaría, [0-9] no
    (TIPO, "11111111; DROP TABLE usuario", CLAVE),
    (TIPO, "11111111\nINFO falso", CLAVE),
    ("PAS", "AB-123; --", CLAVE),        # documento extranjero con caracteres no permitidos
])
def test_entradas_invalidas_no_llegan_a_la_bd(monkeypatch, senuelo, tipo, dni, clave):
    bd = BD(monkeypatch, row=None)
    assert UsuarioDAO.autenticar(tipo, dni, clave) is None
    bd.clase.assert_not_called()


# ---- Errores de infraestructura
def test_sin_conexion_devuelve_none(monkeypatch, senuelo):
    BD(monkeypatch, error_de_conexion=ConexionBDError("sin servidor"))
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is None


def test_error_de_consulta_devuelve_none_y_cierra_el_cursor(monkeypatch, senuelo):
    bd = BD(monkeypatch, error_en_execute=DBError("boom"))
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is None
    bd.cursor.close.assert_called_once()


def test_el_cursor_se_cierra_tambien_en_un_login_correcto(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave))
    UsuarioDAO.autenticar(TIPO, DNI, CLAVE)
    bd.cursor.close.assert_called_once()


# ---- Los logs no filtran datos personales
def test_los_logs_no_contienen_documento_ni_nombres(monkeypatch, senuelo, hash_clave, caplog):
    caplog.set_level("DEBUG")
    BD(monkeypatch, fila(hash_clave))
    UsuarioDAO.autenticar(TIPO, DNI, CLAVE)
    UsuarioDAO.autenticar(TIPO, DNI, "mala")
    texto = caplog.text
    assert DNI not in texto and "Ana" not in texto and "Pérez" not in texto


# ---- Bloqueo temporal por intentos fallidos
def sentencias(bd):
    return [" ".join(c.args[0].split()) for c in bd.cursor.execute.call_args_list]


def test_clave_incorrecta_registra_el_intento_fallido(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave))
    assert UsuarioDAO.autenticar(TIPO, DNI, "otra-clave") is None
    assert len(sentencias(bd)) == 2
    assert sentencias(bd)[1].startswith("UPDATE usuario SET bloqueado_hasta = IF(intentos_fallidos + 1 >=")
    assert bd.cursor.execute.call_args_list[1].args[1] == (
        usuario_dao.MAX_INTENTOS_FALLIDOS, usuario_dao.MINUTOS_BLOQUEO, 3)


def test_cuenta_bloqueada_se_rechaza_aunque_la_clave_sea_correcta(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave, intentos=5, bloqueada=1, bloqueado_hasta="2099-01-01"))
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is None
    senuelo.assert_called_once_with(CLAVE)
    assert len(sentencias(bd)) == 1  # solo el SELECT: un intento bloqueado no suma ni reinicia nada


def test_login_correcto_tras_fallos_reinicia_el_contador(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave, intentos=3))
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is not None
    assert "intentos_fallidos = 0" in sentencias(bd)[1]


def test_login_correcto_sin_fallos_previos_no_escribe_en_la_bd(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave, intentos=0))
    UsuarioDAO.autenticar(TIPO, DNI, CLAVE)
    assert len(sentencias(bd)) == 1


def test_bloqueo_vencido_se_reinicia_antes_de_evaluar(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave, intentos=5, bloqueada=0, bloqueado_hasta="2020-01-01"))
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is not None
    reinicios = [q for q in sentencias(bd) if "intentos_fallidos = 0" in q]
    assert len(reinicios) == 1  # una sola vez, no dos


def test_bloqueo_vencido_y_clave_incorrecta_vuelve_a_contar_desde_cero(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, fila(hash_clave, intentos=5, bloqueada=0, bloqueado_hasta="2020-01-01"))
    UsuarioDAO.autenticar(TIPO, DNI, "mala")
    q = sentencias(bd)
    assert "intentos_fallidos = 0" in q[1] and q[2].startswith("UPDATE usuario SET bloqueado_hasta = IF(")


def test_usuario_inexistente_o_desactivado_no_escribe_en_la_bd(monkeypatch, senuelo, hash_clave):
    bd = BD(monkeypatch, row=None)
    UsuarioDAO.autenticar(TIPO, DNI, CLAVE)
    bd2 = BD(monkeypatch, fila(hash_clave, activo=0))
    UsuarioDAO.autenticar(TIPO, DNI, CLAVE)
    assert len(sentencias(bd)) == 1 and len(sentencias(bd2)) == 1


def test_si_falla_el_reinicio_el_login_correcto_igual_se_permite(monkeypatch, senuelo, hash_clave):
    BD(monkeypatch, fila(hash_clave, intentos=2), errores_en_secuencia=[None, DBError("sin permiso UPDATE")])
    assert UsuarioDAO.autenticar(TIPO, DNI, CLAVE) is not None


def test_si_falla_el_registro_del_fallo_se_deniega_igual(monkeypatch, senuelo, hash_clave):
    BD(monkeypatch, fila(hash_clave), errores_en_secuencia=[None, DBError("sin permiso UPDATE")])
    assert UsuarioDAO.autenticar(TIPO, DNI, "mala") is None
