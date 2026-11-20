from datetime import datetime, timezone
from decimal import Decimal, DecimalException

from dominio.cotizacion import validar_moneda
from infraestructura.conexion_local import ErrorBaseLocal
from infraestructura.cotizaciones_locales import guardar, recuperar
from infraestructura.servicios_externos import ServicioNoDisponible, consultar_api
from validaciones import validar_dinero


def consultar_pago(sesion, local=False):
    if not sesion or sesion.get("rol") not in ("Gerente", "Empleado", "Local"):
        raise PermissionError("Se requiere iniciar sesion.")
    local = local or sesion["rol"] == "Local"
    try:
        base = validar_moneda(input("Moneda del pago (ej. USD): "))
        destino = validar_moneda(input("Moneda de destino (ej. CLP): "))
        monto = validar_dinero(input("Monto del pago: "), "El monto")
        q = None
        if not local:
            try:
                q = consultar_api(base, destino)
            except ServicioNoDisponible as error:
                print(error)
            else:
                try:
                    guardar(q)
                except ErrorBaseLocal:
                    print("Cotizacion recibida. No se pudo guardar el respaldo.")
        if q is None:
            q = recuperar(base, destino)
            if q is None:
                print("No hay cotizacion guardada para estas monedas.")
                return
            edad = datetime.now(timezone.utc) - q.obtenido_en
            print("Respaldo local. Antiguedad:", str(edad).split(".")[0])
        print("Fuente: ExchangeRate-API (https://www.exchangerate-api.com)")
        print("Publicado:", q.publicada_en, "| Obtenido:", q.obtenido_en)
        print("1", base, "=", q.tasa, destino)
        print("Pago estimado:", (monto * q.tasa).quantize(Decimal("0.01")), destino)
    except (ValueError, DecimalException, ErrorBaseLocal) as error:
        print("No se pudo completar la consulta:", error)
