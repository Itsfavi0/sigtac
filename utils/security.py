import getpass

import bcrypt

# ==========================================
# MÓDULO DE SEGURIDAD
# ==========================================

def generar_hash(password_plano: str) -> str:
    """
    Toma una contraseña en texto plano, genera un 'salt' aleatorio
    y retorna el hash seguro usando bcrypt.
    """
    # Convertimos el string a bytes
    password_bytes = password_plano.encode('utf-8')

    # Generamos la sal y el hash
    sal = bcrypt.gensalt(rounds=12)  # 12 rondas es un buen equilibrio entre seguridad y velocidad
    hash_generado = bcrypt.hashpw(password_bytes, sal)

    # Retornamos el hash como string para guardarlo en MySQL (VARCHAR)
    return hash_generado.decode('utf-8')


def verificar_password(password_plano: str, hash_guardado: str) -> bool:
    """
    Compara la contraseña ingresada por el usuario en el login
    con el hash almacenado en la base de datos.
    """
    try:
        # Convertimos ambos a bytes para la validación
        password_bytes = password_plano.encode('utf-8')
        hash_bytes = hash_guardado.encode('utf-8')

        return bcrypt.checkpw(password_bytes, hash_bytes)
    except ValueError:
        # Si el hash_guardado no tiene el formato correcto de bcrypt, fallará de forma segura
        return False


# Hash bcrypt válido (mismo costo que los reales) que no corresponde a ninguna clave.
# Se calcula una vez al importar el módulo, para que el primer login fallido no tarde más.
_HASH_SENUELO = generar_hash("senuelo-no-corresponde-a-ningun-usuario")


def simular_verificacion(password_plano: str) -> None:
    """
    Ejecuta una verificación bcrypt contra un hash señuelo y descarta el resultado.

    Se usa cuando el login falla antes de comparar contra un hash real (usuario
    inexistente o desactivado), para que esas respuestas tarden lo mismo que una
    clave incorrecta y no se pueda deducir qué DNI existen midiendo tiempos.
    """
    verificar_password(password_plano, _HASH_SENUELO)


# ==========================================
# SCRIPT DE UTILIDAD
# ==========================================
if __name__ == "__main__":
    # Este bloque solo se ejecuta si corres este archivo directamente.
    # Genera un hash para pegarlo en seed.sql o en un alta de usuario.
    # La clave se pide sin mostrarla en pantalla ni dejarla en el historial del shell.
    print("--- GENERADOR DE HASH BCRYPT ---")
    clave = getpass.getpass("Clave a hashear: ")
    if clave != getpass.getpass("Repite la clave: "):
        raise SystemExit("Las claves no coinciden.")
    print(generar_hash(clave))
