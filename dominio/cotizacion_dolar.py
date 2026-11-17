from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CotizacionDolar:
    moneda: str
    venta: Decimal
    fecha_actualizacion: datetime


class DeserializadorCotizacion:
    @staticmethod
    def desde_json(datos: dict) -> CotizacionDolar:
        if not isinstance(datos, dict) or datos.get("moneda") != "USD":
            raise ValueError("Se esperaba una cotización en USD.")

        precio = datos.get("venta")
        if isinstance(precio, bool) or not isinstance(precio, (int, float, Decimal)):
            raise ValueError("El precio de venta debe ser numérico.")

        venta = Decimal(str(precio))
        if not venta.is_finite() or venta <= 0:
            raise ValueError("El precio de venta debe ser positivo y finito.")

        texto_fecha = datos.get("fechaActualizacion")
        if not isinstance(texto_fecha, str):
            raise ValueError("Falta la fecha de actualización.")

        # La API utiliza Z para indicar que la hora está en UTC.
        if texto_fecha.endswith("Z"):
            texto_fecha = texto_fecha[:-1] + "+00:00"

        try:
            fecha = datetime.fromisoformat(texto_fecha)
        except ValueError as error:
            raise ValueError("La fecha de actualización no es válida.") from error

        if fecha.tzinfo is None:
            raise ValueError("La fecha debe indicar su zona horaria.")

        return CotizacionDolar(datos["moneda"], venta, fecha)