from utils.security import generar_hash, simular_verificacion, verificar_password


def test_hash_tiene_formato_bcrypt():
    h = generar_hash("clave")
    assert h.startswith("$2b$12$")
    assert len(h) == 60


def test_verifica_clave_correcta_e_incorrecta():
    h = generar_hash("clave-correcta")
    assert verificar_password("clave-correcta", h)
    assert not verificar_password("clave-incorrecta", h)


def test_la_misma_clave_genera_hashes_distintos():  # sal aleatoria
    assert generar_hash("clave") != generar_hash("clave")


def test_acepta_caracteres_unicode():
    h = generar_hash("contraseña-ñandú-ü")
    assert verificar_password("contraseña-ñandú-ü", h)


def test_hash_con_formato_invalido_no_lanza_y_devuelve_false():
    assert verificar_password("clave", "esto-no-es-un-hash") is False
    assert verificar_password("clave", "") is False
    # el placeholder que tenía el seed (61 caracteres) no es un bcrypt válido
    assert verificar_password("clave", "$2b$12$EjemploHash1234567890123456789012345678901234567890123") is False


def test_simular_verificacion_no_devuelve_ni_lanza_nada():
    assert simular_verificacion("cualquier-clave") is None
