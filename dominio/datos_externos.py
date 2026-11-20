"""Clase Clima y el inspector que revisa los datos que llegan de la API."""
from dataclasses import dataclass
from datetime import datetime

# Traductor: la API entrega un número y aquí lo pasamos a palabras
DESCRIPCION_CLIMA = {
    0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
    45: "Niebla", 48: "Niebla con escarcha", 51: "Llovizna debil", 53: "Llovizna",
    55: "Llovizna intensa", 61: "Lluvia debil", 63: "Lluvia", 65: "Lluvia intensa",
    71: "Nieve debil", 73: "Nieve", 75: "Nieve intensa", 80: "Chubascos debiles",
    81: "Chubascos", 82: "Chubascos violentos", 95: "Tormenta",
}


class ErrorDeserializacion(ValueError):
    """Error cuando los datos de la API llegan incompletos o con valores raros."""


@dataclass(frozen=True)  # Crea el constructor solo y no deja cambiar los datos después
class Clima:
    ciudad: str
    temperatura: float
    humedad: int
    estado: str
    obtenido_en: datetime

    def apto_para_trabajo(self):
        # Revisa si el estado del cielo tiene alguna de estas palabras
        lluvia = any(palabra in self.estado for palabra in ("Lluvia", "Chubasco", "Tormenta", "Nieve"))
        return not lluvia and -5 <= self.temperatura <= 35


class DeserializadorAPI:
    """Inspector: revisa los datos de la API y solo si están bien crea el objeto Clima."""

    @staticmethod
    def _numero(datos, clave):
        valor = datos.get(clave)
        # True/False no cuentan como número, y si no es int o float se rechaza
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ErrorDeserializacion(f"El campo {clave} no es numerico.")
        return valor

    @classmethod
    def coordenadas(cls, json_geo):
        resultados = json_geo.get("results") if isinstance(json_geo, dict) else None
        if not resultados:  # Si la lista viene vacía, la ciudad no existe
            raise ErrorDeserializacion("No se encontro la ciudad indicada.")
        primero = resultados[0]
        # Devuelve 3 cosas: latitud, longitud y nombre
        return cls._numero(primero, "latitude"), cls._numero(primero, "longitude"), str(primero.get("name", ""))

    @classmethod
    def clima(cls, json_clima, ciudad):
        actual = json_clima.get("current") if isinstance(json_clima, dict) else None
        if not isinstance(actual, dict):
            raise ErrorDeserializacion("La respuesta del clima no trae datos actuales.")
        temperatura = float(cls._numero(actual, "temperature_2m"))
        humedad = int(cls._numero(actual, "relative_humidity_2m"))
        codigo = int(cls._numero(actual, "weather_code"))
        # Revisa que los valores sean posibles (no existen 500 grados ni 150% de humedad)
        if not -90 <= temperatura <= 60 or not 0 <= humedad <= 100:
            raise ErrorDeserializacion("Los valores del clima estan fuera de rango.")
        return Clima(ciudad, temperatura, humedad,
                     DESCRIPCION_CLIMA.get(codigo, "Desconocido"), datetime.now())