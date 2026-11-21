import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_BASE_PREDETERMINADA = Path("datos") / "ecotech.sqlite3"
TIEMPO_ESPERA_BASE = 10


class ErrorBaseLocal(RuntimeError):
    """No se pudo acceder a la base local o completar una operacion."""


def obtener_ruta_base_local():
    configurada = os.getenv("ECOTECH_SQLITE_PATH", "").strip()
    ruta = Path(configurada or RUTA_BASE_PREDETERMINADA).expanduser()
    if not ruta.is_absolute():
        ruta = CARPETA_PROYECTO / ruta
    if ruta.suffix.lower() not in (".db", ".sqlite", ".sqlite3"):
        raise ValueError(
            "ECOTECH_SQLITE_PATH debe indicar un archivo .db, .sqlite o .sqlite3."
        )
    return ruta.resolve()


def preparar_archivo_base_local(ruta):
    ruta.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        descriptor = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if not ruta.is_file():
            raise ValueError("La ruta de la base local debe ser un archivo.")
    else:
        os.close(descriptor)


@contextmanager
def abrir_base_local():
    """Abre una transaccion local y cierra siempre su conexion.

    Confirma los cambios al terminar correctamente y los revierte si falla
    la operacion. El inicio de la aplicacion debe cargar el archivo .env.
    Los repositorios deben pasar los valores mediante parametros SQL.
    """
    conexion = None
    try:
        ruta = obtener_ruta_base_local()
        preparar_archivo_base_local(ruta)
        conexion = sqlite3.connect(
            str(ruta),
            timeout=TIEMPO_ESPERA_BASE,
            isolation_level="DEFERRED"
        )
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        # BEGIN incluye tambien las operaciones de esquema en la transaccion.
        conexion.execute("BEGIN")
        with conexion:
            yield conexion
    except sqlite3.Error as error:
        raise ErrorBaseLocal(
            "No se pudo completar la operacion en la base local. "
            "Revise que el archivo sea valido y no este ocupado por otro programa."
        ) from error
    except OSError as error:
        raise ErrorBaseLocal(
            "No se pudo acceder al archivo de la base local. "
            "Revise los permisos y el espacio disponible."
        ) from error
    finally:
        if conexion is not None:
            conexion.close()
