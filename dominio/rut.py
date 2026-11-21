import re


def validar_rut(rut):
    if not isinstance(rut, str):
        raise TypeError("El RUT debe ser texto.")
    formato = r"([0-9]{1,8}|[0-9]{1,2}(?:\.[0-9]{3}){1,2})-?([0-9K])"
    coincidencia = re.fullmatch(formato, rut.strip().upper())
    if coincidencia is None:
        raise ValueError("Formato de RUT invalido.")
    cuerpo = coincidencia[1].replace(".", "").lstrip("0")
    if not cuerpo or len(cuerpo) > 8:
        raise ValueError("Numero de RUT invalido.")
    suma = sum(int(digito) * (2 + indice % 6)
               for indice, digito in enumerate(reversed(cuerpo)))
    if coincidencia[2] != "0123456789K"[(11 - suma % 11) % 11]:
        raise ValueError("Digito verificador de RUT incorrecto.")
    return cuerpo + "-" + coincidencia[2]
