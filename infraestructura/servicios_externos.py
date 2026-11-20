import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime

import requests

from dominio.cotizacion import validar_moneda
from infraestructura.deserializador_cotizacion import DeserializadorCotizacion

LOG = logging.getLogger(__name__)
INTENTOS = 4


class ServicioNoDisponible(RuntimeError):
    pass


def espera_indicada(valor, defecto):
    if not valor:
        return defecto
    try:
        if valor.isascii() and valor.isdecimal():
            return int(valor)
        fecha = parsedate_to_datetime(valor)
        return max(0, (fecha - datetime.now(timezone.utc)).total_seconds())
    except (ValueError, TypeError, OverflowError):
        return defecto


def consultar_api(base, destino):
    base, destino = validar_moneda(base), validar_moneda(destino)
    for intento in range(1, INTENTOS + 1):
        espera = 2 ** (intento - 1)
        LOG.info("Consulta de cotizacion, intento %d", intento)
        try:
            with requests.get(
                "https://open.er-api.com/v6/latest/" + base,
                timeout=(3, 10), allow_redirects=False
            ) as respuesta:
                estado = respuesta.status_code
                if estado == 200:
                    try:
                        datos = respuesta.json(parse_float=Decimal)
                        return DeserializadorCotizacion.desde_json(datos, base, destino)
                    except ValueError as error:
                        raise ServicioNoDisponible("Respuesta de cotizacion invalida.") from error
                if estado == 429:
                    espera = espera_indicada(respuesta.headers.get("Retry-After"), espera)
                elif not 500 <= estado < 600:
                    raise ServicioNoDisponible(f"Consulta rechazada por el proveedor (HTTP {estado}).")
                motivo = f"HTTP {estado}"
        except requests.exceptions.SSLError as error:
            raise ServicioNoDisponible("No se pudo verificar la conexion segura.") from error
        except (requests.Timeout, requests.ConnectionError) as error:
            motivo = type(error).__name__
        except requests.RequestException as error:
            raise ServicioNoDisponible("Fallo la comunicacion con el proveedor.") from error
        LOG.warning("Intento %d de %d: %s", intento, INTENTOS, motivo)
        if intento == INTENTOS or espera > 15:
            break
        time.sleep(espera)
    raise ServicioNoDisponible("El proveedor no esta disponible en este momento.")
