"""Guarda el último clima consultado en una base de datos local (SQLite) para el Plan B."""
import sqlite3
from datetime import datetime
from pathlib import Path

from dominio.datos_externos import Clima

# El archivo de la base queda en la raíz del proyecto (Git no lo sube por el .gitignore)
RUTA_BD = Path(__file__).resolve().parent.parent / "ecotech_local.sqlite3"


def conectar():
    conexion = sqlite3.connect(RUTA_BD)
    # Crea la tabla solo la primera vez; si ya existe no hace nada
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS clima (
            ciudad TEXT PRIMARY KEY,
            temperatura REAL NOT NULL,
            humedad INTEGER NOT NULL,
            estado TEXT NOT NULL,
            obtenido_en TEXT NOT NULL
        )""")
    return conexion


def guardar_clima(clima, ciudad_consultada):
    with conectar() as conexion:
        # Los ? se rellenan con los datos de la tupla: nunca se pega texto dentro del SQL
        # Si la ciudad ya existe, actualiza sus datos en vez de duplicarla
        conexion.execute("""
            INSERT INTO clima (ciudad, temperatura, humedad, estado, obtenido_en)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(ciudad) DO UPDATE SET
                temperatura = excluded.temperatura,
                humedad = excluded.humedad,
                estado = excluded.estado,
                obtenido_en = excluded.obtenido_en
        """, (ciudad_consultada.lower(), clima.temperatura, clima.humedad,
              clima.estado, clima.obtenido_en.isoformat(timespec="seconds")))


def leer_clima(ciudad):
    with conectar() as conexion:
        fila = conexion.execute(
            "SELECT ciudad, temperatura, humedad, estado, obtenido_en FROM clima WHERE ciudad = ?",
            (ciudad.lower(),)).fetchone()
    if fila is None:  # Nunca se ha guardado esa ciudad
        return None
    # Convierte la fila de la tabla de vuelta en un objeto Clima
    return Clima(ciudad.title(), fila[1], fila[2], fila[3], datetime.fromisoformat(fila[4]))