import logging
import time
from random import SystemRandom
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime

import requests

from dominio.cotizacion import validar_moneda
from infraestructura.deserializador_cotizacion import DeserializadorCotizacion

LOG = logging.getLogger(__name__)
INTENTOS = 4
URL_BASE = "https://open.er-api.com/v6/latest/"
azar = SystemRandom()
MENSAJES_HTTP = {
    401: "El proveedor rechazó la autenticación (HTTP 401).",
    403: "El proveedor denegó el permiso de consulta (HTTP 403).",
    404: "El proveedor no encontró el recurso. Revise la moneda de origen (HTTP 404).",
}


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
                URL_BASE + base,
                timeout=10, allow_redirects=False
            ) as respuesta:
                estado = respuesta.status_code
                if estado == 200:
                    try:
                        datos = respuesta.json(parse_float=Decimal)
                        return DeserializadorCotizacion.desde_json(datos, base, destino)
                    except ValueError as error:
                        raise ServicioNoDisponible("Respuesta de cotizacion invalida.") from error
                if estado == 429:
                    espera = max(espera, espera_indicada(respuesta.headers.get("Retry-After"), espera))
                elif not 500 <= estado < 600:
                    raise ServicioNoDisponible(MENSAJES_HTTP.get(estado, f"Consulta rechazada por el proveedor (HTTP {estado})."))
                motivo = f"HTTP {estado}"
                mensaje_final = ("Se alcanzó el límite de consultas del proveedor (HTTP 429)."
                                 if estado == 429 else f"El proveedor tiene un problema temporal (HTTP {estado}).")
        except requests.exceptions.SSLError as error:
            raise ServicioNoDisponible("No se pudo verificar la conexion segura.") from error
        except requests.Timeout:
            motivo = "Timeout"
            mensaje_final = "El proveedor no respondió a tiempo."
        except requests.ConnectionError:
            motivo = "ConnectionError"
            mensaje_final = "No se pudo conectar con el proveedor. Revise su conexión a Internet."
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema,
                requests.exceptions.InvalidURL) as error:
            raise ServicioNoDisponible("La dirección de la API no es válida.") from error
        except requests.RequestException as error:
            raise ServicioNoDisponible("Fallo la comunicacion con el proveedor.") from error
        LOG.warning("Intento %d de %d: %s", intento, INTENTOS, motivo)
        if intento == INTENTOS or espera > 15:
            break
        demora = min(15, espera + azar.uniform(0, 0.5))
        LOG.info("Próximo intento en %.2f segundos", demora)
        time.sleep(demora)
    raise ServicioNoDisponible(mensaje_final)
