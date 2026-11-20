from infraestructura.conexion import es_error_conexion


def mostrar_error_supabase(error, conexion=None):
    if es_error_conexion(error, conexion):
        raise ConnectionError(
            "Se perdio la conexion con Supabase. Revise la red y vuelva a iniciar el programa. "
            "Si fallo durante el guardado, consulte el registro antes de repetir la operacion."
        ) from error
    estado = error.sqlstate
    
    if estado == "23505":
        mensajes = {
            "idx_empleado_rut": "Ese RUT ya está registrado.",
            "cuenta_usuario_nombre_usuario_key": "Ese nombre de usuario ya está en uso.",
            "cuenta_usuario_id_empleado_key": "Ese empleado ya tiene una cuenta.",
        }
        print(mensajes.get(error.diag.constraint_name, "Ya existe un registro con esos datos."))
    elif estado in ("23503", "23001"):
        print("Revise los registros relacionados: el ID no existe o el registro todavia esta en uso.")
    elif estado in ("23514", "23502", "22001", "22003", "22007"):
        print("Un dato no cumple las restricciones de la base. Revise los valores ingresados.")
    elif estado in ("40P01", "40001", "55P03"):
        print("Otro cambio esta utilizando esos registros. Intente nuevamente.")
    elif estado in ("42P01", "42703", "3F000"):
        print("Falta el esquema de EcoTech. Ejecute ecotech_supabase.sql en el proyecto correcto.")
    elif estado == "42501":
        print("El usuario de la base no tiene permiso para realizar esta operacion.")
    elif estado and estado.startswith("28"):
        print("El usuario o la contrasena de la base son incorrectos.")
    elif estado and estado.startswith("08"):
        print("No se pudo mantener la conexion. Revise el servidor y la red.")
    else:
        print("No se pudo completar la operación en la base de datos.")
        
