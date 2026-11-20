import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dominio.cotizacion_dolar import DeserializadorCotizacion


RUTA_BD = Path(__file__).resolve().parent.parent / "cotizaciones.sqlite3"


def guardar_cotizacion(cotizacion):
    obtenido_en = datetime.now(timezone.utc).isoformat()

    try:
        with closing(sqlite3.connect(RUTA_BD)) as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS cotizacion (
                    moneda TEXT PRIMARY KEY,
                    venta TEXT NOT NULL,
                    fecha_actualizacion TEXT NOT NULL,
                    obtenido_en TEXT NOT NULL
                )
            """)

            conexion.execute("""
                INSERT INTO cotizacion (moneda, venta, fecha_actualizacion, obtenido_en)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(moneda) DO UPDATE SET
                    venta = excluded.venta,
                    fecha_actualizacion = excluded.fecha_actualizacion,
                    obtenido_en = excluded.obtenido_en
            """, (
                cotizacion.moneda,
                str(cotizacion.venta),
                cotizacion.fecha_actualizacion.isoformat(),
                obtenido_en
            ))

            conexion.commit()

    except sqlite3.Error as error:
        raise OSError("No se pudo guardar el respaldo local.") from error


def leer_respaldo():
    if not RUTA_BD.is_file():
        return None

    try:
        with closing(sqlite3.connect(RUTA_BD)) as conexion:
            fila = conexion.execute("""
                SELECT moneda, venta, fecha_actualizacion, obtenido_en
                FROM cotizacion
                WHERE moneda = ?
            """, ("USD",)).fetchone()

        if fila is None:
            return None

        moneda, venta, fecha, obtenido = fila
        cotizacion = DeserializadorCotizacion.desde_json({
            "moneda": moneda,
            "venta": Decimal(venta),
            "fechaActualizacion": fecha
        })

        obtenido_en = datetime.fromisoformat(obtenido)
        if obtenido_en.tzinfo is None:
            raise ValueError("Fecha de respaldo sin zona horaria.")

        return cotizacion, obtenido_en

    except (sqlite3.Error, ValueError, InvalidOperation, TypeError) as error:
        raise OSError("No se pudo leer el respaldo local.") from error