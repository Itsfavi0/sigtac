from unittest.mock import MagicMock

import pytest
from mysql.connector import Error as DBError, IntegrityError, errorcode

from dao import base_dao, usuario_dao
from dao import transaccion as transaccion_mod
from dao.usuario_dao import UsuarioDAO
from models.excepciones import ConexionBDError, RegistroDuplicadoError, ReglaNegocioError
from models.permisos import Rol
from models.usuario import CuentaUsuario
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


# ---- Administración de cuentas
HASH = "$2b$12$abcdefghijklmnopqrstuv"


def fila_cuenta(**cambios):
    datos = {"id_usuario": 3, "id_empleado": 3, "nombres": "Ana", "apellidos": "Pérez",
             "nombre_cargo": "Licenciado(a) en Enfermería", "nombre_rol": "Enfermero de Triaje", "activo": 1,
             "intentos_fallidos": 0, "bloqueada": 0}
    datos.update(cambios)
    return datos


def cuenta(**cambios):
    return UsuarioDAO._a_cuenta(fila_cuenta(**cambios))


class BDCuentas:
    """Conexión simulada para las consultas de administración (filas, rowcount y lastrowid)."""

    def __init__(self, monkeypatch, row=None, rows=None, rowcount=1, lastrowid=None, error_en_execute=None):
        self.cursor = MagicMock()
        self.cursor.fetchone.return_value = row
        self.cursor.fetchall.return_value = rows or []
        self.cursor.rowcount = rowcount
        self.cursor.lastrowid = lastrowid
        if error_en_execute:
            self.cursor.execute.side_effect = error_en_execute
        conexion = MagicMock()
        conexion.cursor.return_value = self.cursor
        self.clase = MagicMock()
        self.clase.return_value.obtener_conexion.return_value = conexion
        self.clase.return_value.en_transaccion = False
        monkeypatch.setattr(base_dao, "ConexionBD", self.clase)
        monkeypatch.setattr(transaccion_mod, "ConexionBD", self.clase)

    @property
    def sql(self) -> str:
        return " ".join(self.cursor.execute.call_args.args[0].split())

    @property
    def params(self) -> tuple:
        return self.cursor.execute.call_args.args[1]


def test_a_cuenta_convierte_la_fila():
    c = cuenta(activo=0, bloqueada=1, intentos_fallidos=5)
    assert isinstance(c, CuentaUsuario)
    assert (c.rol, c.activo, c.bloqueada, c.intentos_fallidos) == (Rol.ENFERMERO, False, True, 5)


def test_a_cuenta_con_rol_desconocido():
    with pytest.raises(ValueError):
        cuenta(nombre_rol="Rol raro")


def test_listar_cuentas_no_lee_el_hash(monkeypatch):
    bd = BDCuentas(monkeypatch, rows=[fila_cuenta(), fila_cuenta(id_usuario=4)])
    assert [c.id_usuario for c in UsuarioDAO.listar_cuentas()] == [3, 4]
    assert "hash_clave" not in bd.sql
    assert "ORDER BY e.apellidos, e.nombres" in bd.sql


def test_buscar_cuenta(monkeypatch):
    bd = BDCuentas(monkeypatch, row=fila_cuenta())
    assert UsuarioDAO.buscar_cuenta(3).id_usuario == 3
    assert bd.sql.endswith("WHERE u.id_usuario = %s") and bd.params == (3,)


def test_buscar_cuenta_inexistente(monkeypatch):
    BDCuentas(monkeypatch, row=None)
    assert UsuarioDAO.buscar_cuenta(99) is None


def test_listar_empleados_sin_cuenta(monkeypatch):
    bd = BDCuentas(monkeypatch, rows=[{"id_empleado": 5}])
    assert UsuarioDAO.listar_empleados_sin_cuenta() == [{"id_empleado": 5}]
    assert "WHERE u.id_usuario IS NULL AND e.estado_registro = TRUE" in bd.sql


@pytest.mark.parametrize("row, esperado", [({"1": 1}, True), (None, False)])
def test_empleado_activo(monkeypatch, row, esperado):
    bd = BDCuentas(monkeypatch, row=row)
    assert UsuarioDAO.empleado_activo(3) is esperado
    assert "estado_registro = TRUE" in bd.sql


def test_crear_cuenta(monkeypatch):
    bd = BDCuentas(monkeypatch, lastrowid=7)
    assert UsuarioDAO.crear_cuenta(3, "Médico de Emergencia", HASH) == 7
    assert bd.sql == ("INSERT INTO usuario (id_empleado, id_rol, hash_clave) "
                      "VALUES (%s, (SELECT id_rol FROM rol WHERE nombre_rol = %s), %s)")
    assert bd.params == (3, "Médico de Emergencia", HASH)


@pytest.mark.parametrize("hash_clave", ["ClaveEnTextoPlano1", None, ""])
def test_crear_cuenta_rechaza_algo_que_no_es_un_hash(monkeypatch, hash_clave):
    bd = BDCuentas(monkeypatch)
    with pytest.raises(ValueError, match="hash"):
        UsuarioDAO.crear_cuenta(3, Rol.MEDICO, hash_clave)
    bd.clase.assert_not_called()


def test_crear_una_cuenta_duplicada(monkeypatch):
    BDCuentas(monkeypatch, error_en_execute=IntegrityError(errno=errorcode.ER_DUP_ENTRY))
    with pytest.raises(RegistroDuplicadoError):
        UsuarioDAO.crear_cuenta(3, Rol.MEDICO, HASH)


def test_cambiar_rol_es_condicional(monkeypatch):
    bd = BDCuentas(monkeypatch, rowcount=1)
    c = cuenta()
    c.cambiar_rol(Rol.MEDICO)
    UsuarioDAO.cambiar_rol(c, Rol.ENFERMERO)
    assert "WHERE id_usuario = %s AND id_rol = (SELECT id_rol FROM rol WHERE nombre_rol = %s)" in bd.sql
    assert bd.params == ("Médico de Emergencia", 3, "Enfermero de Triaje")


def test_cambiar_rol_si_otro_usuario_lo_cambio(monkeypatch):
    BDCuentas(monkeypatch, rowcount=0)
    c = cuenta()
    c.cambiar_rol(Rol.MEDICO)
    with pytest.raises(ReglaNegocioError, match="otro usuario"):
        UsuarioDAO.cambiar_rol(c, Rol.ENFERMERO)


def test_cambiar_rol_sin_cambio(monkeypatch):
    bd = BDCuentas(monkeypatch)
    with pytest.raises(ValueError):
        UsuarioDAO.cambiar_rol(cuenta(), Rol.ENFERMERO)
    bd.clase.assert_not_called()


@pytest.mark.parametrize("activo_final", [True, False])
def test_cambiar_activo_es_condicional(monkeypatch, activo_final):
    bd = BDCuentas(monkeypatch, rowcount=1)
    c = cuenta(activo=int(not activo_final))
    c.activar() if activo_final else c.desactivar()
    UsuarioDAO.cambiar_activo(c)
    assert bd.sql == "UPDATE usuario SET activo = %s WHERE id_usuario = %s AND activo = %s"
    assert bd.params == (activo_final, 3, not activo_final)


def test_cambiar_activo_si_otro_usuario_llego_antes(monkeypatch):
    BDCuentas(monkeypatch, rowcount=0)
    c = cuenta()
    c.desactivar()
    with pytest.raises(ReglaNegocioError):
        UsuarioDAO.cambiar_activo(c)


def test_restablecer_clave_quita_el_bloqueo(monkeypatch):
    bd = BDCuentas(monkeypatch, rowcount=1)
    UsuarioDAO.restablecer_clave(3, HASH)
    assert "SET hash_clave = %s, intentos_fallidos = 0, bloqueado_hasta = NULL" in bd.sql
    assert bd.params == (HASH, 3)


def test_restablecer_clave_rechaza_texto_plano(monkeypatch):
    bd = BDCuentas(monkeypatch)
    with pytest.raises(ValueError):
        UsuarioDAO.restablecer_clave(3, "NuevaClave1")
    bd.clase.assert_not_called()


@pytest.mark.parametrize("metodo, args", [("restablecer_clave", (99, HASH)), ("desbloquear", (99,))])
def test_cuenta_inexistente_lanza_regla_negocio_error(monkeypatch, metodo, args):
    BDCuentas(monkeypatch, rowcount=0)
    with pytest.raises(ReglaNegocioError, match="no existe"):
        getattr(UsuarioDAO, metodo)(*args)


def test_desbloquear(monkeypatch):
    bd = BDCuentas(monkeypatch, rowcount=1)
    UsuarioDAO.desbloquear(3)
    assert bd.sql == "UPDATE usuario SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id_usuario = %s"


def test_desbloquear_propaga_los_errores_de_bd(monkeypatch):
    # A diferencia del login, administrar una cuenta no oculta un fallo de la BD.
    BDCuentas(monkeypatch, error_en_execute=DBError(errno=2013))
    with pytest.raises(base_dao.PersistenciaError):
        UsuarioDAO.desbloquear(3)

