import os
from pathlib import Path

from dotenv import load_dotenv

from dominio.hash_cuenta import crear_hash
from dominio.servicioCifrado import ServicioCifrado
from presentacion.inicio import conectar_con_reintentos


def convertir(token, servicio):
    token = bytes(token)
    if token.startswith(b"$argon2id$"):
        return token
    contenido = servicio.descifrar(token)
    if contenido.startswith(servicio.MARCADOR_HASH):
        return contenido[len(servicio.MARCADOR_HASH):].encode("ascii")
    return crear_hash(contenido)


def migrar(conexion, servicio):
    cambios = 0
    with conexion.transaction(), conexion.cursor() as cursor:
        cursor.execute(
            "SELECT id_cuenta, contrasena_cifrada FROM ecotech.cuenta_usuario "
            "ORDER BY id_cuenta FOR UPDATE"
        )
        for identificador, token in cursor.fetchall():
            try:
                resumen = convertir(token, servicio)
            except ValueError as error:
                raise ValueError(
                    f"Revise la clave original o restablezca la cuenta {identificador}."
                ) from error
            if resumen != bytes(token):
                cursor.execute(
                    "UPDATE ecotech.cuenta_usuario SET contrasena_cifrada = %s "
                    "WHERE id_cuenta = %s", (resumen, identificador)
                )
                cambios += 1
    return cambios


def main():
    raiz = Path(__file__).resolve().parent
    load_dotenv(raiz / ".env")
    ruta = raiz / (os.getenv("ECOTECH_FERNET_KEY_FILE") or "clave_fernet.key")
    if not ruta.is_file():
        print("Falta la clave Fernet original. Restaurela antes de migrar.")
        return
    servicio = ServicioCifrado(ruta)
    conexion = conectar_con_reintentos()
    if conexion is None:
        return
    try:
        print("Base conectada:", conexion.info.host, conexion.info.dbname)
        if input("Escriba MIGRAR para actualizar las cuentas: ") == "MIGRAR":
            print("Cuentas actualizadas:", migrar(conexion, servicio))
    except ValueError as error:
        print("Migracion cancelada:", error)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
