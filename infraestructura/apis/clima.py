from dataclasses import dataclass

from dominio.clima import Clima, DeserializadorClima
from infraestructura.apis.cliente_http import obtener_json
from validaciones import validar_texto


URL_CLIMA = "https://api.open-meteo.com/v1/forecast"
URL_UBICACIONES = "https://geocoding-api.open-meteo.com/v1/search"


@dataclass(frozen=True)
class Ubicacion:
    nombre: str
    latitud: float
    longitud: float


def validar_coordenadas(latitud, longitud):
    if type(latitud) not in (int, float) or not -90 <= latitud <= 90:
        raise ValueError("La latitud debe ser un número entre -90 y 90.")

    if type(longitud) not in (int, float) or not -180 <= longitud <= 180:
        raise ValueError("La longitud debe ser un número entre -180 y 180.")


def leer_ubicacion(fila: dict) -> Ubicacion:
    if not isinstance(fila, dict) or not isinstance(fila.get("name"), str):
        raise ValueError("Open-Meteo entregó una ubicación sin nombre válido.")

    nombre = validar_texto(fila["name"], 200, "El nombre de la ubicación")
    partes = [nombre]

    for campo in ("admin2", "admin1", "country"):
        valor = fila.get(campo)
        if isinstance(valor, str) and valor.strip() and valor.strip() not in partes:
            partes.append(validar_texto(valor, 200, "La zona de la ubicación"))

    latitud = fila.get("latitude")
    longitud = fila.get("longitude")
    validar_coordenadas(latitud, longitud)

    return Ubicacion(", ".join(partes), latitud, longitud)


def buscar_ubicaciones(nombre: str) -> list[Ubicacion]:
    nombre = validar_texto(nombre, 150, "La ubicación")

    if len(nombre) < 2:
        raise ValueError("Escribe al menos dos caracteres de la ubicación.")

    parametros = {"name": nombre, "count": 10, "language": "es"}
    datos = obtener_json(URL_UBICACIONES, "Open-Meteo", parametros)

    if not isinstance(datos, dict) or not isinstance(datos.get("results", []), list):
        raise ValueError("Open-Meteo entregó una lista de ubicaciones inválida.")

    return [leer_ubicacion(fila) for fila in datos.get("results", [])]


def consultar_clima(latitud: float, longitud: float) -> Clima:
    validar_coordenadas(latitud, longitud)

    parametros = {
        "latitude": latitud,
        "longitude": longitud,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "temperature_unit": "celsius",
    }

    datos = obtener_json(URL_CLIMA, "Open-Meteo", parametros)
    return DeserializadorClima.desde_json(datos)