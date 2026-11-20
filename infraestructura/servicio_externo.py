"""Une la API, el inspector y la base local. Si la API falla, usa el Plan B."""
from dominio.datos_externos import DeserializadorAPI, ErrorDeserializacion
from infraestructura import cache_local
from infraestructura.api_externa import ClienteAPI, ErrorApiExterna, registro

URL_BUSCAR_CIUDAD = "https://geocoding-api.open-meteo.com/v1/search"
URL_CLIMA = "https://api.open-meteo.com/v1/forecast"

cliente_clima = ClienteAPI("Servicio de clima")


def consultar_clima(ciudad):
    """Devuelve el clima y si viene del respaldo (True) o de internet (False)."""
    try:
        datos_ciudad = cliente_clima.obtener_json(
            URL_BUSCAR_CIUDAD, {"name": ciudad, "count": 1, "language": "es"})
        latitud, longitud, nombre = DeserializadorAPI.coordenadas(datos_ciudad)
        datos_clima = cliente_clima.obtener_json(URL_CLIMA, {
            "latitude": latitud, "longitude": longitud,
            "current": "temperature_2m,relative_humidity_2m,weather_code"})
        clima = DeserializadorAPI.clima(datos_clima, nombre or ciudad)
        cache_local.guardar_clima(clima, ciudad)  # Guarda una copia para el Plan B
        return clima, False
    except (ErrorApiExterna, ErrorDeserializacion) as error:
        # Plan B: la API falló, entonces buscamos la última copia guardada
        registro.warning("Clima de %s: se usa el respaldo local (%s)", ciudad, error)
        respaldo = cache_local.leer_clima(ciudad)
        if respaldo is None:
            raise ErrorApiExterna(f"{error} Tampoco hay datos guardados de esa ciudad.") from error
        return respaldo, True