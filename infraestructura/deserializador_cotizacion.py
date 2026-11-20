from datetime import datetime, timezone
from decimal import Decimal

from dominio.cotizacion import Cotizacion, validar_moneda


class DeserializadorCotizacion:
    @staticmethod
    def desde_json(datos: dict, base: str, destino: str) -> Cotizacion:
        base = validar_moneda(base)
        destino = validar_moneda(destino)
        if not isinstance(datos, dict) or datos.get("result") != "success":
            raise ValueError("El proveedor no entrego una respuesta exitosa.")
        if datos.get("base_code") != base:
            raise ValueError("La moneda base recibida no coincide con la consulta.")

        tasas = datos.get("rates")
        if not isinstance(tasas, dict) or destino not in tasas:
            raise ValueError("No hay una tasa publicada para la moneda solicitada.")
        valor = tasas[destino]
        if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)):
            raise ValueError("La tasa recibida debe ser numerica.")

        marca = datos.get("time_last_update_unix")
        if type(marca) is not int or marca <= 0:
            raise ValueError("Fecha de publicacion invalida.")
        try:
            publicada = datetime.fromtimestamp(marca, tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as error:
            raise ValueError("Fecha de publicacion fuera de rango.") from error

        return Cotizacion(base, destino, Decimal(str(valor)), publicada, datetime.now(timezone.utc))
