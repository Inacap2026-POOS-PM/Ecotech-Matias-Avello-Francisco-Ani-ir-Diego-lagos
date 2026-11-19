import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from math import ceil

import requests


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


def solicitar_respuesta(url, servicio, parametros):
    try:
        respuesta = requests.get(
            url,
            params=parametros,
            timeout=10,
            allow_redirects=False
        )
    except requests.exceptions.SSLError as error:
        raise ConnectionError(
            f"No se pudo verificar la conexión segura con {servicio}."
        ) from error
    except (requests.Timeout, requests.ConnectionError):
        REGISTRO.warning("%s: fallo de red o tiempo de espera agotado.", servicio)
        return None
    except requests.RequestException as error:
        raise ConnectionError(
            f"No se pudo completar la consulta a {servicio}."
        ) from error

    REGISTRO.info("%s: respuesta HTTP %s.", servicio, respuesta.status_code)
    return respuesta


def calcular_espera(respuesta, intento, servicio):
    espera = 2 ** (intento - 1)

    if respuesta is None:
        return espera

    codigo = respuesta.status_code

    if codigo == 429:
        return segundos_retry_after(respuesta.headers.get("Retry-After"), espera)

    if 500 <= codigo <= 599:
        return espera

    raise ConnectionError(f"{servicio} rechazó la consulta (HTTP {codigo}).")


def leer_json(respuesta, servicio, parse_float):
    try:
        return respuesta.json(parse_float=parse_float)
    except requests.exceptions.JSONDecodeError as error:
        raise ValueError(f"{servicio} entregó una respuesta JSON inválida.") from error


def obtener_json(url, servicio, parametros=None, *, parse_float=float):
    for intento in range(1, MAX_INTENTOS + 1):
        REGISTRO.info("%s: intento %s de %s.", servicio, intento, MAX_INTENTOS)
        respuesta = solicitar_respuesta(url, servicio, parametros)

        if respuesta is not None and respuesta.status_code == 200:
            return leer_json(respuesta, servicio, parse_float)

        espera = calcular_espera(respuesta, intento, servicio)
        if intento < MAX_INTENTOS:
            REGISTRO.info("Próximo intento en %s segundos.", espera)
            time.sleep(espera)

    raise ConnectionError(
        f"No se obtuvieron datos de {servicio} tras {MAX_INTENTOS} intentos."
    )