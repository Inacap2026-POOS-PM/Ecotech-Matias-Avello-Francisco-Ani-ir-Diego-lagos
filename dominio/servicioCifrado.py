import os

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


class ServicioCifrado:
    def cifrar_contrasena(self, contrasena):
        if not isinstance(contrasena, str):
            raise TypeError("La contraseña debe ser una cadena.")

        derivador = Argon2id(
            salt=os.urandom(16),
            length=32,
            iterations=3,
            lanes=4,
            memory_cost=64 * 1024,
        )
        resumen = derivador.derive_phc_encoded(contrasena.encode("utf-8"))
        return resumen.encode("ascii")

    def validacion_cifrado(self, ingresada, token):
        if not isinstance(ingresada, str):
            raise TypeError("La contraseña debe ser una cadena.")
        if not isinstance(token, (bytes, bytearray, memoryview)):
            raise TypeError("El valor guardado debe recibirse como bytes.")

        try:
            resumen = bytes(token).decode("ascii")
            Argon2id.verify_phc_encoded(ingresada.encode("utf-8"), resumen)
        except (InvalidKey, UnicodeDecodeError):
            return False

        return True