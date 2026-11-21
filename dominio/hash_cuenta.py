import os

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


def crear_hash(contrasena):
    derivador = Argon2id(
        salt=os.urandom(16), length=32, iterations=3,
        lanes=4, memory_cost=64 * 1024
    )
    return derivador.derive_phc_encoded(contrasena.encode("utf-8")).encode("ascii")


def verificar_hash(contrasena, resumen):
    try:
        Argon2id.verify_phc_encoded(contrasena.encode("utf-8"), resumen.decode("ascii"))
    except InvalidKey:
        return False
    return True
