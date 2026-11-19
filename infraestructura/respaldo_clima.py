import sqlite3
from contextlib import closing
from math import isfinite
from datetime import datetime, timezone
from pathlib import Path

from dominio.clima import Clima
from infraestructura.apis.clima import Ubicacion


RUTA_BD = Path(__file__).resolve().parent.parent / "clima.sqlite3"


def guardar_clima(busqueda: str, lugar: Ubicacion, clima: Clima):
    obtenido_en = datetime.now(timezone.utc).isoformat()

    try:
        with closing(sqlite3.connect(RUTA_BD)) as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS clima (
                    busqueda TEXT NOT NULL,
                    ubicacion TEXT NOT NULL,
                    latitud REAL NOT NULL,
                    longitud REAL NOT NULL,
                    temperatura REAL NOT NULL,
                    humedad INTEGER NOT NULL CHECK (humedad BETWEEN 0 AND 100),
                    estado TEXT NOT NULL,
                    obtenido_en TEXT NOT NULL,
                    PRIMARY KEY (busqueda, latitud, longitud)
                )
            """)

            conexion.execute("""
                INSERT INTO clima (
                    busqueda, ubicacion, latitud, longitud,
                    temperatura, humedad, estado, obtenido_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (busqueda, latitud, longitud) DO UPDATE SET
                    ubicacion = excluded.ubicacion,
                    temperatura = excluded.temperatura,
                    humedad = excluded.humedad,
                    estado = excluded.estado,
                    obtenido_en = excluded.obtenido_en
                WHERE excluded.obtenido_en >= clima.obtenido_en
            """, (
                busqueda.strip().casefold(), lugar.nombre,
                lugar.latitud, lugar.longitud,
                clima.temperatura_c, clima.humedad_porcentaje,
                clima.estado_tiempo, obtenido_en
            ))

            conexion.commit()

    except sqlite3.Error as error:
        raise OSError("No se pudo guardar el respaldo local del clima.") from error


def leer_respaldos_clima(busqueda, lugar=None):
    if not RUTA_BD.is_file():
        return {}

    parametros = {
        "texto": busqueda.strip().casefold(),
        "lat": lugar.latitud if lugar else None,
        "lon": lugar.longitud if lugar else None,
    }

    try:
        with closing(sqlite3.connect(RUTA_BD)) as conexion:
            cursor = conexion.execute("""
                SELECT ubicacion, latitud, longitud, temperatura,
                       humedad, estado, obtenido_en
                FROM clima
                WHERE (:lat IS NULL AND busqueda = :texto)
                   OR (latitud = :lat AND longitud = :lon)
                ORDER BY obtenido_en DESC
            """, parametros)

            filas = cursor.fetchall() if lugar is None else cursor.fetchmany(1)

        respaldos = {}
        for nombre, lat, lon, temp, humedad, estado, obtenido in filas:
            fecha = datetime.fromisoformat(obtenido)
            if (
                fecha.tzinfo is None
                or not isfinite(temp)
                or not isinstance(humedad, int)
                or not 0 <= humedad <= 100
            ):
                raise ValueError("Respaldo inválido.")

            ubicacion = Ubicacion(nombre, lat, lon)
            respaldos[ubicacion] = (Clima(temp, humedad, estado), fecha)

        return respaldos

    except (sqlite3.Error, TypeError, ValueError) as error:
        raise OSError("No se pudo leer el respaldo local del clima.") from error