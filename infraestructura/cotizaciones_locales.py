from datetime import datetime
from decimal import Decimal

from dominio.cotizacion import Cotizacion
from infraestructura.conexion_local import abrir_base_local


def preparar(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS cotizacion (
            base TEXT NOT NULL, destino TEXT NOT NULL, tasa TEXT NOT NULL,
            publicada_en TEXT NOT NULL, obtenido_en TEXT NOT NULL,
            PRIMARY KEY (base, destino)
        )
    """)


def guardar(q):
    with abrir_base_local() as c:
        preparar(c)
        c.execute("""
            INSERT INTO cotizacion VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(base, destino) DO UPDATE SET tasa=excluded.tasa,
                publicada_en=excluded.publicada_en, obtenido_en=excluded.obtenido_en
            WHERE excluded.publicada_en >= cotizacion.publicada_en
        """, (q.base, q.destino, str(q.tasa), q.publicada_en.isoformat(), q.obtenido_en.isoformat()))


def recuperar(base, destino):
    with abrir_base_local() as c:
        preparar(c)
        fila = c.execute("""
            SELECT tasa, publicada_en, obtenido_en FROM cotizacion
            WHERE base=? AND destino=?
        """, (base, destino)).fetchone()
    if fila:
        return Cotizacion(base, destino, Decimal(fila["tasa"]),
                          datetime.fromisoformat(fila["publicada_en"]),
                          datetime.fromisoformat(fila["obtenido_en"]))
    return None
