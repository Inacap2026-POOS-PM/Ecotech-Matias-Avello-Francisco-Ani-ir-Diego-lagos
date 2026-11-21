import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


def validar_moneda(codigo: str) -> str:
    if not isinstance(codigo, str) or not re.fullmatch("[A-Za-z]{3}", codigo.strip()):
        raise ValueError("Ingrese un codigo de moneda de tres letras.")
    return codigo.strip().upper()


@dataclass(frozen=True)
class Cotizacion:
    base: str
    destino: str
    tasa: Decimal
    publicada_en: datetime
    obtenido_en: datetime

    def __post_init__(self):
        for campo in ("base", "destino"):
            object.__setattr__(self, campo, validar_moneda(getattr(self, campo)))
        if not isinstance(self.tasa, Decimal) or not self.tasa.is_finite() or self.tasa <= 0:
            raise ValueError("La tasa debe ser un decimal positivo y finito.")
        if self.base == self.destino and self.tasa != 1:
            raise ValueError("La tasa entre la misma moneda debe ser uno.")
        for fecha in (self.publicada_en, self.obtenido_en):
            if not isinstance(fecha, datetime) or fecha.utcoffset() is None:
                raise ValueError("Las fechas deben incluir zona horaria.")
