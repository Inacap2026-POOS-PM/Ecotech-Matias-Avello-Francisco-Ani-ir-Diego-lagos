import time

from dominio.hash_cuenta import crear_hash, verificar_hash
from infraestructura.conexion_local import abrir_base_local

VIGENCIA = 24 * 60 * 60


def preparar(conexion):
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS acceso_local (
            usuario TEXT PRIMARY KEY,
            resumen BLOB NOT NULL,
            validado_en INTEGER NOT NULL
        )
    """)


def recordar(usuario, contrasena):
    resumen = crear_hash(contrasena)
    with abrir_base_local() as conexion:
        preparar(conexion)
        conexion.execute("""
            INSERT INTO acceso_local (usuario, resumen, validado_en) VALUES (?, ?, ?)
            ON CONFLICT(usuario) DO UPDATE SET
                resumen = excluded.resumen, validado_en = excluded.validado_en
        """, (usuario, resumen, int(time.time())))


def olvidar(usuario):
    with abrir_base_local() as conexion:
        preparar(conexion)
        conexion.execute("DELETE FROM acceso_local WHERE usuario = ?", (usuario,))


def verificar(usuario, contrasena):
    with abrir_base_local() as conexion:
        preparar(conexion)
        fila = conexion.execute(
            "SELECT resumen, validado_en FROM acceso_local WHERE usuario = ?", (usuario,)
        ).fetchone()
    return (fila is not None
            and 0 <= time.time() - fila["validado_en"] < VIGENCIA
            and verificar_hash(contrasena, fila["resumen"]))
