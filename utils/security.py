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


# ==========================================
# SCRIPT DE UTILIDAD
# ==========================================
if __name__ == "__main__":
    # Este bloque solo se ejecuta si corres este archivo directamente.
    # Úsalo una sola vez para generar los hashes que pondrás en tu seed.sql
    print("--- GENERADOR DE HASH PARA SEED.SQL ---")
    claves_prueba = ["admin123", "123456", "enfermero2026"]

    for clave in claves_prueba:
        hash_result = generar_hash(clave)
        print(f"Clave: {clave} -> Hash: {hash_result}")