from dataclasses import dataclass
from math import isfinite


ESTADOS_TIEMPO = {
    0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado",
    3: "Cubierto", 45: "Niebla", 48: "Niebla con escarcha",
    51: "Llovizna leve", 53: "Llovizna moderada", 55: "Llovizna intensa",
    56: "Llovizna helada leve", 57: "Llovizna helada intensa",
    61: "Lluvia leve", 63: "Lluvia moderada", 65: "Lluvia intensa",
    66: "Lluvia helada leve", 67: "Lluvia helada intensa",
    71: "Nevada leve", 73: "Nevada moderada", 75: "Nevada intensa",
    77: "Nieve granulada", 80: "Chubascos leves", 81: "Chubascos moderados",
    82: "Chubascos fuertes", 85: "Chubascos de nieve leves",
    86: "Chubascos de nieve fuertes", 95: "Tormenta eléctrica",
    96: "Tormenta con granizo leve", 97: "Tormenta eléctrica fuerte",
    99: "Tormenta con granizo intenso",
}


@dataclass(frozen=True)
class Clima:
    temperatura_c: float
    humedad_porcentaje: int
    estado_tiempo: str


class DeserializadorClima:
    @staticmethod
    def desde_json(datos: dict) -> Clima:
        actual = datos.get("current") if isinstance(datos, dict) else None
        if not isinstance(actual, dict):
            raise ValueError("Faltan las condiciones actuales del clima.")

        temperatura = actual.get("temperature_2m")
        humedad = actual.get("relative_humidity_2m")
        codigo = actual.get("weather_code")

        if type(temperatura) not in (int, float):
            raise ValueError("La temperatura debe ser numérica.")
        try:
            temperatura = float(temperatura)
        except OverflowError as error:
            raise ValueError("La temperatura está fuera de rango.") from error
        if not isfinite(temperatura):
            raise ValueError("La temperatura debe ser finita.")

        if type(humedad) is not int or not 0 <= humedad <= 100:
            raise ValueError("La humedad debe ser un entero entre 0 y 100.")

        if type(codigo) is not int or codigo not in ESTADOS_TIEMPO:
            raise ValueError("El estado del tiempo no es válido.")

        return Clima(temperatura, humedad, ESTADOS_TIEMPO[codigo])