from pathlib import Path

from dotenv import load_dotenv

from infraestructura.repositorio import agregar_empleado
from presentacion.entradas import pedir_empleado, pedir_cuenta
from presentacion.inicio import conectar_con_reintentos, preparar_servicio_cifrado


def main():
    raiz = Path(__file__).resolve().parent
    load_dotenv(raiz / ".env")
    conexion = conectar_con_reintentos()
    if conexion is None:
        return
    try:
        servicio = preparar_servicio_cifrado(conexion, raiz)
        if servicio is None:
            return
        with conexion.transaction(), conexion.cursor() as cursor:
            cursor.execute("LOCK TABLE ecotech.cuenta_usuario IN SHARE ROW EXCLUSIVE MODE")
            cursor.execute("SELECT EXISTS (SELECT 1 FROM ecotech.cuenta_usuario)")
            if cursor.fetchone()[0]:
                print("Ya existen cuentas. Utilice el menu del gerente.")
                return
            empleado = pedir_empleado(None, conexion)
            if empleado.get_rol() != "Gerente":
                print("La primera cuenta debe corresponder a un gerente.")
                return
            empleado.asignar_cuenta(pedir_cuenta(empleado.get_correo(), servicio))
            agregar_empleado(conexion, empleado)
        print("Gerente inicial registrado.")
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
