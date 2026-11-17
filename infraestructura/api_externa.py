from decimal import Decimal

import requests

from dominio.cotizacion_dolar import CotizacionDolar, DeserializadorCotizacion


URL_DOLAR = "https://cl.dolarapi.com/v1/cotizaciones/usd"


def consultar_dolar() -> CotizacionDolar:
    try:
        respuesta = requests.get(URL_DOLAR, timeout=10)
        respuesta.raise_for_status()
    except requests.Timeout as error:
        raise ConnectionError("DolarAPI no respondió a tiempo.") from error
    except requests.HTTPError as error:
        codigo = error.response.status_code
        raise ConnectionError(f"DolarAPI respondió con HTTP {codigo}.") from error
    except requests.RequestException as error:
        raise ConnectionError("No se pudo consultar DolarAPI.") from error

    try:
        datos = respuesta.json(parse_float=Decimal)
    except requests.exceptions.JSONDecodeError as error:
        raise ValueError("DolarAPI entregó una respuesta JSON inválida.") from error

    return DeserializadorCotizacion.desde_json(datos)