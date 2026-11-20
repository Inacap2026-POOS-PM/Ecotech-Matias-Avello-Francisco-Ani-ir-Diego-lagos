from presentacion.cotizaciones import consultar_pago
from infraestructura.acceso_local import recordar, olvidar, verificar
from infraestructura.conexion_local import ErrorBaseLocal
from infraestructura.repositorio import comprobar_acceso
from presentacion.entradas import pedir_dato
from validaciones import validar_contrasena, validar_nombre_usuario


def pedir_credenciales():
    usuario = pedir_dato("Nombre de usuario: ", validar_nombre_usuario, revisar_formato=True)
    clave = pedir_dato("Contraseña: ", validar_contrasena, ocultar=True)
    return usuario, clave


def iniciar_sesion(conexion, servicio, menu_gerente, menu_empleado):
    usuario, clave = pedir_credenciales()
    sesion = comprobar_acceso(conexion, usuario, clave, servicio)
    if not sesion or sesion["rol"] not in ("Gerente", "Empleado"):
        print("Acceso rechazado.")
        try:
            olvidar(usuario)
        except (ErrorBaseLocal, ValueError):
            print("No se pudo actualizar el permiso local de este equipo.")
        return
    try:
        recordar(usuario, clave)
    except (ErrorBaseLocal, ValueError):
        print("Acceso en línea autorizado. No se pudo preparar el acceso local.")
    if sesion["rol"] == "Gerente":
        menu_gerente(conexion, servicio, sesion)
    else:
        menu_empleado(conexion, sesion)


def iniciar_sesion_local():
    usuario, clave = pedir_credenciales()
    try:
        permitido = verificar(usuario, clave)
    except (ErrorBaseLocal, ValueError):
        print("No se pudo verificar la cuenta en este equipo.")
        return
    if not permitido:
        print("Acceso local rechazado. Verifique sus credenciales o vuelva a conectarse.")
        return
    print("Sesión local de solo lectura:", usuario)
    while True:
        opcion = input("1. Consultar cotizacion guardada | 0. Cerrar sesion: ").strip()
        if opcion == "0":
            return
        if opcion == "1":
            consultar_pago({"rol": "Local", "nombre_usuario": usuario})
        else:
            print("Opcion invalida.")

