import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
from math import ceil

import requests

from dominio.cotizacion_dolar import CotizacionDolar, DeserializadorCotizacion


URL_DOLAR = "https://cl.dolarapi.com/v1/cotizaciones/usd"
MAX_INTENTOS = 3
REGISTRO = logging.getLogger(__name__)


def segundos_retry_after(valor, espera_por_defecto):
    if not valor:
        return espera_por_defecto

    valor = valor.strip()
    try:
        if valor.isascii() and valor.isdigit():
            return int(valor)

        fecha = parsedate_to_datetime(valor)
        segundos = (fecha - datetime.now(timezone.utc)).total_seconds()
        return max(0, ceil(segundos))
    except (TypeError, ValueError, OverflowError):
        return espera_por_defecto


def leer_cotizacion(respuesta) -> CotizacionDolar:
    try:
        datos = respuesta.json(parse_float=Decimal)
    except requests.exceptions.JSONDecodeError as error:
        raise ValueError("DolarAPI entregó una respuesta JSON inválida.") from error

    return DeserializadorCotizacion.desde_json(datos)


def solicitar_respuesta():
    try:
        respuesta = requests.get(URL_DOLAR, timeout=10, allow_redirects=False)
    except requests.exceptions.SSLError as error:
        raise ConnectionError("No se pudo verificar la conexión segura con DolarAPI.") from error
    except (requests.Timeout, requests.ConnectionError):
        REGISTRO.warning("Fallo de red o tiempo de espera agotado.")
        return None
    except requests.RequestException as error:
        raise ConnectionError("No se pudo completar la consulta a DolarAPI.") from error

    REGISTRO.info("Respuesta HTTP %s.", respuesta.status_code)
    return respuesta


def calcular_espera(respuesta, intento):
    espera = 2 ** (intento - 1)

    if respuesta is None:
        return espera

    codigo = respuesta.status_code

    if codigo == 429:
        return segundos_retry_after(respuesta.headers.get("Retry-After"), espera)

    if 500 <= codigo <= 599:
        return espera

    raise ConnectionError(f"DolarAPI rechazó la consulta (HTTP {codigo}).")


def consultar_dolar() -> CotizacionDolar:
    for intento in range(1, MAX_INTENTOS + 1):
        REGISTRO.info("Consulta USD. Intento %s de %s.", intento, MAX_INTENTOS)

        respuesta = solicitar_respuesta()
        if respuesta is not None and respuesta.status_code == 200:
            return leer_cotizacion(respuesta)

        espera = calcular_espera(respuesta, intento)
        if intento < MAX_INTENTOS:
            REGISTRO.info("Próximo intento en %s segundos.", espera)
            time.sleep(espera)

    raise ConnectionError(f"No se obtuvo la cotización tras {MAX_INTENTOS} intentos.")