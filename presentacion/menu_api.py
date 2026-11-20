"""Menú para consultar el clima de un proyecto."""
from infraestructura.api_externa import ErrorApiExterna
from infraestructura.servicio_externo import consultar_clima
from validaciones import validar_ciudad


def pedir_ciudad():
    while True:  # Repite hasta que el usuario escriba una ciudad válida
        try:
            return validar_ciudad(input("Ciudad del proyecto: "))
        except (ValueError, TypeError) as error:
            print("Dato invalido:", error)


def opcion_clima():
    ciudad = pedir_ciudad()
    try:
        clima, es_respaldo = consultar_clima(ciudad)
    except ErrorApiExterna as error:
        print("No se pudo consultar el clima:", error)
        return
    print(f"\nClima en {clima.ciudad}: {clima.estado}")
    print(f"  Temperatura: {clima.temperatura:.1f} °C | Humedad: {clima.humedad}%")
    if clima.apto_para_trabajo():
        print("  Recomendacion: se puede trabajar en terreno.")
    else:
        print("  Recomendacion: conviene reprogramar los trabajos en terreno.")
    if es_respaldo:
        print(f"  [Sin conexion] Datos guardados el {clima.obtenido_en:%d-%m-%Y %H:%M}.")
    else:
        print(f"  Datos en linea del {clima.obtenido_en:%d-%m-%Y %H:%M}.")