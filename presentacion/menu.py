import json
from infraestructura.apis.dolar import consultar_dolar
from infraestructura.apis.clima import buscar_ubicaciones, consultar_clima
from psycopg.errors import UniqueViolation
from datetime import datetime, timezone
from infraestructura.respaldo_dolar import guardar_cotizacion, leer_respaldo
from infraestructura.respaldo_clima import guardar_clima, leer_respaldos_clima
from psycopg import (
    IntegrityError, DataError, OperationalError, InterfaceError, ProgrammingError
)
from dominio import (
    Tiempo,
    Empleado
)
from validaciones import (
    validar_fecha,
    validar_descripcion,
    validar_id,
    validar_horas_adicionales,
    validar_nombre_usuario,
    validar_contrasena
)
from infraestructura.repositorio import (
    agregar_empleado,
    consultar_empleados,
    buscar_empleado,
    crear_ficha_con_invitacion,
    contacto_pendiente_invitacion,
    actualizar_empleado,
    activar_cuenta_empleado,
    eliminar_empleado,
    consultar_cuentas,
    registrar_empleado_invitado,
    generar_invitacion,
    sesion_vigente,
    agregar_cuenta,
    actualizar_cuenta,
    eliminar_cuenta,
    comprobar_acceso,
    primer_administrador_pendiente,
    crear_primer_administrador,
    consultar_datos_empleado,
    consultar_horas_empleado,
    buscar_registro,
    objeto_desde_fila,
    consultar_registros,
    validar_rol_trabajador,
    guardar_registro,
    cambiar_rol_trabajador,
    eliminar_registro,
    consultar_proyectos,
    generar_invitacion,
    consultar_departamentos,
    consultar_asignaciones,
    registrar_horas_asignacion,
    consultar_historial,
    consultar_detalle_historial,
    guardar_tiempo
)
from infraestructura.conexion import (
    configuracion_entidad
)
from dominio.informe import (
    Informes
)
from presentacion.entradas import (
    pedir_id,
    pedir_dato,
    pedir_contrasena,
    pedir_empleado,
    pedir_datos_contrato,
    pedir_datos_contacto,
    pedir_nombre_nuevo,
    pedir_credenciales_nuevas,
    pedir_cuenta,
    pedir_id_vinculado,
    pedir_registro
)
from presentacion.errores import (
    mostrar_error_supabase
)


REGISTRO_NO_EXISTE = "No existe ese registro."
ELIMINACION_CANCELADA = "Eliminación cancelada."
EMPLEADO_NO_EXISTE = "No existe un empleado con ese ID."


def mostrar_historial(conexion):
    entidad = input("Entidad: EMPLEADO, CUENTA_USUARIO, PROYECTO, DEPARTAMENTO o ASIGNACION (Enter para todas): ").strip().upper()
    entrada = input("ID del registro de esa entidad (Enter para todos): ").strip()
    id_registro = validar_id(entrada) if entrada else None
    entrada = input("ID del empleado (Enter para todos): ").strip()
    id_empleado = int(entrada) if entrada else None
    operacion = input(
        "Operación: AGREGAR, ACTUALIZAR o ELIMINAR (Enter para todas): "
    ).strip().upper()
    texto = input("Buscar nombre, usuario u otro texto (Enter para todos): ").strip()
    entrada = input("Cantidad de resultados, 1 a 200 [20]: ").strip()
    limite = int(entrada) if entrada else 20
    registros = consultar_historial(
        conexion, id_empleado, operacion or None, texto, limite, entidad or None, id_registro
    )
    if not registros:
        print("No hay cambios que coincidan con la búsqueda.")
        return
    for fila in registros:
        print(
            'Historial {} | {} | {} | {} {} | Empleado {} | Base de datos: {}'.format(fila['id_historial'], fila['fecha'], fila['operacion'], fila['entidad'], fila['id_registro'], fila['id_empleado'], fila['usuario_mysql'])
        )
        print(" ", fila["detalle"])
    entrada = input("ID del historial para ver antes/después (Enter para volver): ").strip()
    if not entrada:
        return
    id_historial = int(entrada)
    if id_historial <= 0:
        raise ValueError("El ID debe ser mayor que cero.")
    fila = consultar_detalle_historial(conexion, id_historial)
    if fila is None:
        print("No existe ese registro de historial.")
        return
    print('\nHistorial {}: {}'.format(fila['id_historial'], fila['detalle']))
    for campo, titulo in (
        ("datos_anteriores", "ANTES"), ("datos_nuevos", "DESPUÉS")
    ):
        print(titulo + ":")
        if fila[campo] is None:
            print("No corresponde.")
        else:
            print(json.dumps(json.loads(fila[campo]), ensure_ascii=False, indent=2))


def pedir_y_guardar_tiempo(conexion):
    id_empleado = pedir_id_vinculado(conexion, "EMPLEADO")
    id_proyecto = pedir_id_vinculado(conexion, "PROYECTO")
    fecha = pedir_dato("Fecha del trabajo (AAAA-MM-DD): ", validar_fecha)
    horas = pedir_dato("Horas trabajadas (entero mayor que cero): ", validar_horas_adicionales)
    descripcion = pedir_dato("Descripción de las tareas: ", validar_descripcion)
    tiempo = Tiempo(fecha, horas, descripcion, id_empleado, id_proyecto)
    id_registro = guardar_tiempo(conexion, tiempo)
    print("Registro de tiempo guardado en Supabase. ID:", id_registro)


def crear_informe_desde_supabase(conexion):
    return Informes(
        consultar_empleados(conexion), consultar_proyectos(conexion),
        consultar_departamentos(conexion), consultar_asignaciones(conexion)
    )


def mostrar_informes_desde_supabase(conexion):
    informe = crear_informe_desde_supabase(conexion)
    print("\nINFORME GENERAL DE ECOTECH")
    informe.generar_informes()


def exportar_informe_desde_supabase(conexion, formato):
    informe = crear_informe_desde_supabase(conexion)
    if formato == "excel":
        ruta = informe.exportar_excel()
    elif formato == "pdf":
        ruta = informe.exportar_pdf()
    else:
        raise ValueError("Formato no reconocido.")
    print("Informe guardado en:", ruta)
    return ruta

def ejecutar_accion(acciones, opcion, mensaje_invalido):
    seleccion = acciones.get(opcion)
    if seleccion is None:
        print(mensaje_invalido)
        return
    funcion, argumentos = seleccion
    funcion(*argumentos)


def agregar_registro_desde_menu(conexion, entidad):
    registro = pedir_registro(conexion, entidad)
    id_nuevo = guardar_registro(conexion, entidad, registro)
    print("Registro guardado en Supabase; cambio registrado. ID:", id_nuevo)


def listar_registros_desde_menu(conexion, entidad):
    registros = consultar_registros(conexion, entidad)
    if not registros:
        print("No hay registros de esta entidad.")
    for registro in registros:
        print(registro)


def actualizar_registro_desde_menu(conexion, entidad):
    id_registro = pedir_id("ID del registro a actualizar: ")
    if buscar_registro(conexion, entidad, id_registro) is None:
        print(REGISTRO_NO_EXISTE)
        return
    registro = pedir_registro(conexion, entidad, id_registro)
    if guardar_registro(conexion, entidad, registro, actualizar=True):
        print("Registro actualizado en Supabase; cambio registrado.")
    else:
        print("El registro ya no existe.")


def eliminar_registro_desde_menu(conexion, entidad):
    id_registro = pedir_id("ID del registro a eliminar: ")
    confirmar = input("¿Eliminar este registro? (s/n): ").strip().lower()
    if confirmar != "s":
        print(ELIMINACION_CANCELADA)
        return
    if eliminar_registro(conexion, entidad, id_registro):
        print("Registro eliminado de Supabase; historial conservado.")
    else:
        print(REGISTRO_NO_EXISTE)


def buscar_registro_desde_menu(conexion, entidad):
    id_registro = pedir_id("ID del registro a buscar: ")
    fila = buscar_registro(conexion, entidad, id_registro)
    if fila is None:
        print(REGISTRO_NO_EXISTE)
    else:
        print(objeto_desde_fila(entidad, fila))


def sumar_horas_desde_menu(conexion):
    id_asignacion = pedir_id("ID de la asignación: ")
    horas = pedir_dato("Horas adicionales: ", validar_horas_adicionales)
    total = registrar_horas_asignacion(conexion, id_asignacion, horas)
    if total is None:
        print("No existe esa asignación.")
    else:
        print('Horas guardadas en Base de datos: {}. Cambio registrado.'.format(total))

def exigir_sesion(sesion):
    if sesion is None or sesion.get("rol") not in ("Gerente", "Empleado"):
        raise PermissionError("Inicia sesión con una cuenta de EcoTech.")

def exigir_gerente(sesion):
    if sesion is None or sesion.get("rol") != "Gerente":
        raise PermissionError(
            "No tienes permisos para realizar esta operación."

        )

def menu_entidad(conexion, entidad, sesion):
    exigir_gerente(sesion)

    configuracion_entidad(entidad)
    acciones = {
        "1": (agregar_registro_desde_menu, (conexion, entidad)),
        "2": (listar_registros_desde_menu, (conexion, entidad)),
        "3": (actualizar_registro_desde_menu, (conexion, entidad)),
        "4": (eliminar_registro_desde_menu, (conexion, entidad)),
        "5": (buscar_registro_desde_menu, (conexion, entidad)),
    }
    if entidad == "ASIGNACION":
        
        acciones["6"] = (sumar_horas_desde_menu, (conexion,))
        acciones["7"] = (pedir_y_guardar_tiempo, (conexion,))
    
    while True:
        print("\nGESTIÓN DE " + entidad)
        print("1. Agregar")
        print("2. Consultar todos")
        print("3. Actualizar por ID")
        print("4. Eliminar por ID")
        print("5. Buscar por ID")
        if entidad == "ASIGNACION":
            print("6. Sumar horas trabajadas")
            print("7. Registrar tiempo de trabajo")
        
        print("0. Volver al menú principal")
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "0":
            return
        try:
            ejecutar_accion(acciones, opcion, "Opción inválida. Elija una de las opciones mostradas.")
        except ValueError as error:
            print("Dato inválido:", error)
        except (IntegrityError, DataError, OperationalError, InterfaceError, ProgrammingError) as error:
            mostrar_error_supabase(error, conexion)


def mostrar_invitacion(id_empleado, codigo):
    print(f"Ficha de empleado {id_empleado}. Código de invitación: {codigo}")
    print("Entrégalo en privado al empleado. Vence en 24 horas.")


def agregar_empleado_desde_menu(conexion, servicio):
    empleado = pedir_empleado(None, conexion)

    if empleado.get_rol() == "Empleado":
        id_empleado, codigo = registrar_empleado_invitado(conexion, empleado)
        mostrar_invitacion(id_empleado, codigo)
        return

    cuenta = pedir_cuenta(empleado.get_correo(), servicio)
    empleado.asignar_cuenta(cuenta)
    id_gerente = agregar_empleado(conexion, empleado)
    print("Gerente y cuenta guardados. ID:", id_gerente)


def listar_empleados_desde_menu(conexion):
    empleados = consultar_empleados(conexion)
    if not empleados:
        print("No hay empleados registrados.")
    for empleado in empleados:
        print(empleado)


def actualizar_empleado_desde_menu(conexion):
    id_empleado = pedir_id("ID del trabajador a actualizar: ")
    ficha = buscar_empleado(conexion, id_empleado)

    if ficha is None:
        print(EMPLEADO_NO_EXISTE)
        return

    nombre, rut, fecha_contrato, salario = pedir_datos_contrato()

    direccion = telefono = correo = None
    if ficha["correo"] is not None:
        direccion, telefono, correo = pedir_datos_contacto()

    empleado = Empleado(
        id_empleado, nombre, direccion, telefono, correo,
        fecha_contrato, salario, ficha["rol"], rut=rut,
    )

    if actualizar_empleado(conexion, empleado):
        print("Ficha guardada.")
    else:
        print(EMPLEADO_NO_EXISTE)


def cambiar_rol_desde_menu(conexion):
    id_empleado = pedir_id("ID del trabajador: ")
    rol = pedir_dato("Nuevo rol (Empleado/Gerente): ", validar_rol_trabajador)

    if cambiar_rol_trabajador(conexion, id_empleado, rol):
        print("Rol actualizado a", rol)
    else:
        print("El trabajador ya tiene ese rol.")


def renovar_invitacion_desde_menu(conexion):
    id_empleado = pedir_id("ID del empleado: ")
    codigo = generar_invitacion(conexion, id_empleado)
    mostrar_invitacion(id_empleado, codigo)


def eliminar_empleado_desde_menu(conexion):
    id_empleado = pedir_id("ID del empleado a eliminar: ")
    confirmar = input("Se eliminará también su cuenta. ¿Continuar? (s/n): ")
    if confirmar.strip().lower() != "s":
        print(ELIMINACION_CANCELADA)
        return
    if eliminar_empleado(conexion, id_empleado):
        print("Empleado y cuenta eliminados de Supabase; historial conservado.")
    else:
        print(EMPLEADO_NO_EXISTE)


def guardar_cuenta_desde_menu(conexion, servicio, actualizar=False):
    id_empleado = pedir_id("ID del empleado: ")
    empleado = buscar_empleado(conexion, id_empleado)
    if empleado is None:
        print(EMPLEADO_NO_EXISTE)
        return
    
    if not actualizar and empleado["rol"] == "Empleado":
        codigo = generar_invitacion(conexion, id_empleado)
        mostrar_invitacion(id_empleado, codigo)
        return
    
    cuenta = pedir_cuenta(empleado["correo"], servicio)
    if actualizar:
        if actualizar_cuenta(conexion, id_empleado, cuenta):
            print("Cuenta actualizada en Supabase; cambio registrado.")
        else:
            print("No existe una cuenta para ese empleado.")
        return
    id_cuenta = agregar_cuenta(conexion, id_empleado, cuenta)
    if id_cuenta is None:
        print(EMPLEADO_NO_EXISTE)
    else:
        print("Cuenta guardada en Supabase. ID de cuenta:", id_cuenta)


MENSAJE_ACCESO_INVALIDO = (
    "Los datos ingresados no son correctos. Verifícalos e inténtalo de nuevo."
)


def autenticar_cuenta(conexion, servicio):
    nombre = input("Nombre de usuario: ").strip()
    contrasena = pedir_contrasena("Contraseña: ")

    if not contrasena.strip():
        return None

    try:
        nombre = validar_nombre_usuario(nombre, revisar_formato=True)
        validar_contrasena(contrasena)
    except ValueError:
        return None

    return comprobar_acceso(conexion, nombre, contrasena, servicio)


def comprobar_acceso_desde_menu(conexion, servicio):
    if autenticar_cuenta(conexion, servicio):
        print("Acceso autorizado.")
    else:
        print(MENSAJE_ACCESO_INVALIDO)


def listar_cuentas_desde_menu(conexion):
    cuentas = consultar_cuentas(conexion)
    if not cuentas:
        print("No hay cuentas registradas.")
    for cuenta in cuentas:
        print(
            'Cuenta {} | Empleado {}: {} | Usuario: {} | {}'.format(
                cuenta['id_cuenta'], cuenta['id_empleado'], cuenta['empleado'],
                cuenta['nombre_usuario'], cuenta['correo']
            )
        )


def eliminar_cuenta_desde_menu(conexion):
    id_cuenta = pedir_id("ID de la cuenta a eliminar (opción 7): ")
    confirmar = input("El empleado se conservará. ¿Eliminar cuenta? (s/n): ")
    if confirmar.strip().lower() != "s":
        print(ELIMINACION_CANCELADA)
        return
    if eliminar_cuenta(conexion, id_cuenta):
        print("Cuenta eliminada de Supabase; empleado e historial conservados.")
    else:
        print("No existe una cuenta con ese ID.")


def ejecutar_opcion_menu(opcion, conexion, sesion):
    exigir_gerente(sesion)

    acciones = {
        "1": (listar_empleados_desde_menu, (conexion,)),
        "2": (menu_entidad, (conexion, "PROYECTO", sesion)),
        "3": (menu_entidad, (conexion, "DEPARTAMENTO", sesion)),
        "4": (menu_entidad, (conexion, "ASIGNACION", sesion)),
        "5": (mostrar_informes_desde_supabase, (conexion,)),
        "6": (exportar_informe_desde_supabase, (conexion, "excel")),
        "7": (exportar_informe_desde_supabase, (conexion, "pdf")),
        "8": (consultar_dolar_desde_menu, (sesion,)),
        "9": (consultar_clima_desde_menu, (sesion,)),
    }
    
    try:
        ejecutar_accion(acciones, opcion, "Opción inválida. Elige una opción del 0 al 9.")
    except ValueError as error:
        print("Dato inválido:", error)
    except ConnectionError:
        raise
    except PermissionError as error:
        print("No se pudo guardar el informe por falta de permisos:", error)
    except FileNotFoundError as error:
        print("No se encontro el archivo o la carpeta:", error)
    except OSError as error:
        print("No se pudo guardar el archivo:", error)
    except ModuleNotFoundError:
        print("Falta una biblioteca. Instale las dependencias de requirements.txt.")
    except (IntegrityError, DataError, OperationalError, InterfaceError, ProgrammingError) as error:
        mostrar_error_supabase(error, conexion)

def menu_empleado(conexion, sesion):
    
    exigir_sesion(sesion)
    id_empleado = sesion["id_empleado"]

    while True:
        print("\nECOTECH - MENÚ DEL EMPLEADO")
        print("Usuario:", sesion["nombre_usuario"])
        print("1. Consultar mis datos")
        print("2. Consultar mis horas de trabajo")
        print("3. Consultar clima del proyecto")
        print("4. Consultar precio del dólar")
        print("0. Cerrar sesión")

        opcion = input("Seleccione una opción: ").strip()
        
        if opcion != "0" and not sesion_vigente(conexion, sesion):
            print("La cuenta o el rol cambió. Vuelve a iniciar sesión.")
            return

        try:
            if opcion == "1":
                empleado = consultar_datos_empleado(
                    conexion, id_empleado
                )

                if empleado is None:
                    print("No se encontraron tus datos.")
                    continue

                print("\nMIS DATOS")
                print("ID:", empleado["id_empleado"])
                print("Nombre:", empleado["nombre"])
                print("Dirección:", empleado["direccion"])
                print("Teléfono:", empleado["telefono"])
                print("Correo:", empleado["correo"])
                print("Fecha de inicio:", empleado["fecha_inicio"])
                print("Salario:", empleado["salario"])
                print("Rol:", empleado["rol"])

            elif opcion == "2":
                registros = consultar_horas_empleado(
                    conexion, id_empleado
                )

                print("\nMIS HORAS DE TRABAJO")

                if not registros:
                    print("Todavía no tienes horas registradas.")
                    continue

                for registro in registros:
                    print("--------------------------------")
                    print("Fecha:", registro["fecha"])
                    print("Proyecto:", registro["nombre_proyecto"] or "Sin vincular")
                    print("Horas:", registro["horas_trabajadas"])
                    print("Tareas:", registro["tareas_realizadas"])

            elif opcion == "3":
                consultar_clima_desde_menu(sesion)

            elif opcion == "4":
                consultar_dolar_desde_menu(sesion)
            
            elif opcion == "0":
                print("Sesión finalizada.")
                return

            else:
                print("Opción inválida.")

        except ValueError as error:
            print("Dato inválido:", error)

def registrar_primer_administrador(conexion, servicio):
    print("\nECOTECH - REGISTRO DEL PRIMER ADMINISTRADOR")

    empleado = pedir_empleado(None, conexion, rol_fijo="Administrador")
    cuenta = pedir_cuenta(empleado.get_correo(), servicio)
    empleado.asignar_cuenta(cuenta)

    if crear_primer_administrador(conexion, empleado):
        print("Cuenta de administrador creada. Ya puedes iniciar sesión.")
    else:
        print("El registro de la primera cuenta ya está cerrado.")


def registrar_trabajador_con_codigo(conexion, sesion):
    exigir_administrador(sesion)
    nombre, rut, fecha_contrato, salario = pedir_datos_contrato()

    id_empleado, codigo = crear_ficha_con_invitacion(
        conexion, nombre, rut, fecha_contrato, salario
    )
    mostrar_invitacion(id_empleado, codigo)


def registrar_cuenta_empleado(conexion, servicio):
    while True:
        codigo = input("Código de invitación (Enter para volver): ").strip()
        if not codigo:
            return

        pendiente = contacto_pendiente_invitacion(conexion, codigo)
        if pendiente is not None:
            break

        print("El código es incorrecto, venció o ya fue utilizado.")

    nombre, contrasena = pedir_credenciales_nuevas(conexion)
    contacto = pedir_datos_contacto() if pendiente else None

    while True:
        try:
            activar_cuenta_empleado(
                conexion, codigo, nombre, contrasena, servicio,
                contacto=contacto,
            )
            print("Cuenta creada. Ya puedes iniciar sesión.")
            return
        except UniqueViolation as error:
            if error.diag.constraint_name != "cuenta_usuario_nombre_usuario_key":
                raise
            print("Ese nombre de usuario ya está en uso. Elige otro.")
            nombre = pedir_nombre_nuevo(conexion)


def menu(conexion, servicio):
    while True:
        alta_disponible = primer_administrador_pendiente(conexion)

        print("\nECOTECH - ACCESO")
        print("1. Iniciar sesión")
        if alta_disponible:
            print("2. Crear primer administrador")
        else:
            print("2. Crear cuenta de empleado con invitación")
        print("0. Salir")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "0":
            return

        if opcion == "1":
            iniciar_sesion(conexion, servicio)
        elif opcion == "2":
            try:
                if alta_disponible:
                    registrar_primer_administrador(conexion, servicio)
                else:
                    registrar_cuenta_empleado(conexion, servicio)
            except ValueError as error:
                print(error)
            except (IntegrityError, DataError) as error:
                mostrar_error_supabase(error, conexion)
        else:
            print("Opción inválida.")

def exigir_administrador(sesion):
    if sesion is None or sesion.get("rol") != "Administrador":
        raise PermissionError("Esta opción requiere una cuenta de administrador.")


def menu_administrador(conexion, sesion):
    exigir_administrador(sesion)

    acciones = {
        "1": (registrar_trabajador_con_codigo, (conexion, sesion)),
        "2": (listar_empleados_desde_menu, (conexion,)),
        "3": (actualizar_empleado_desde_menu, (conexion,)),
        "4": (cambiar_rol_desde_menu, (conexion,)),
        "5": (listar_cuentas_desde_menu, (conexion,)),
        "6": (renovar_invitacion_desde_menu, (conexion,)),
        "7": (eliminar_cuenta_desde_menu, (conexion,)),
        "8": (eliminar_empleado_desde_menu, (conexion,)),
        "9": (mostrar_historial, (conexion,)),
    }

    while True:
        print("\nECOTECH - MENÚ DEL ADMINISTRADOR")
        print("1. Registrar trabajador y generar invitación")
        print("2. Consultar trabajadores")
        print("3. Actualizar ficha de trabajador")
        print("4. Cambiar rol de trabajador")
        print("5. Consultar cuentas de usuario")
        print("6. Renovar código de invitación")
        print("7. Eliminar solo la cuenta de usuario")
        print("8. Eliminar ficha del trabajador y su cuenta")
        print("9. Consultar historial de cambios")
        print("0. Cerrar sesión")

        opcion = input("Seleccione una opción: ").strip()
        
        if opcion != "0" and not sesion_vigente(conexion, sesion):
            print("La cuenta o el rol cambió. Vuelve a iniciar sesión.")
            return
        if opcion == "0":
            return

        try:
            if not sesion_vigente(conexion, sesion):
                print("La cuenta o el rol cambió. Vuelve a iniciar sesión.")
                return

            ejecutar_accion(acciones, opcion, "Opción inválida.")

        except ValueError as error:
            print(error)
        except (IntegrityError, DataError, OperationalError,
                InterfaceError, ProgrammingError) as error:
            mostrar_error_supabase(error, conexion)

def iniciar_sesion(conexion, servicio):
    print("\nECOTECH - INICIO DE SESIÓN")

    sesion = autenticar_cuenta(conexion, servicio)

    if sesion is None:
        print(MENSAJE_ACCESO_INVALIDO)
        return


    print("\nBienvenido a EcoTech.")

    if sesion["rol"] == "Gerente":
        print("Acceso autorizado como Gerente.")
        menu_gerente(conexion, sesion)

    elif sesion["rol"] == "Empleado":
        print("Acceso autorizado como Empleado.")
        menu_empleado(conexion, sesion)

    elif sesion["rol"] == "Administrador":
        print("Acceso autorizado como Administrador.")
        menu_administrador(conexion, sesion)

    else:
        print("El rol de esta cuenta no está autorizado.")

def menu_gerente(conexion, sesion):
    exigir_gerente(sesion)

    while True:
        print("\nECOTECH - MENÚ DEL GERENTE")
        print("1. Consultar trabajadores")
        print("2. Gestionar proyectos")
        print("3. Gestionar departamentos")
        print("4. Gestionar asignaciones y horas")
        print("5. Consultar informe general")
        print("6. Exportar informe a Excel")
        print("7. Exportar informe a PDF")
        print("8. Consultar dólar y calcular pago en pesos")
        print("9. Consultar clima del proyecto")
        print("0. Cerrar sesión")

        opcion = input("Seleccione una opción: ").strip()
        if opcion != "0" and not sesion_vigente(conexion, sesion):
            print("La cuenta o el rol cambió. Vuelve a iniciar sesión.")
            return
        
        if opcion == "0":
            return

        ejecutar_opcion_menu(opcion, conexion, sesion)

def mostrar_cotizacion_dolar(cotizacion):
    precio = f"{cotizacion.venta:.2f}".replace(".", ",")
    fecha = cotizacion.fecha_actualizacion.astimezone().strftime("%d/%m/%Y %H:%M:%S")

    encabezado = f"{'Moneda':<6} | {'Venta (CLP por USD)':>18} | Actualización (hora local)"
    print(encabezado)
    print("-" * len(encabezado))
    print(f"{cotizacion.moneda:<6} | {precio:>18} | {fecha}")

def consultar_dolar_desde_menu(sesion):
    exigir_sesion(sesion)

    try:
        cotizacion = consultar_dolar()
    except (ConnectionError, ValueError) as error:
        print(error)
        cotizacion = mostrar_respaldo_dolar()
        if cotizacion is None:
            return
    else:
        mostrar_cotizacion_dolar(cotizacion)
        try:
            guardar_cotizacion(cotizacion)
        except OSError as error:
            print(error)

    if sesion["rol"] == "Gerente":
        solicitar_monto_usd(cotizacion)


def mostrar_respaldo_dolar():
    try:
        respaldo = leer_respaldo()
    except OSError as error:
        print(error)
        return

    if respaldo is None:
        print("Todavía no hay una cotización guardada en este equipo.")
        return

    cotizacion, obtenido_en = respaldo
    antiguedad = datetime.now(timezone.utc) - obtenido_en
    minutos = max(0, int(antiguedad.total_seconds() // 60))
    fecha_local = obtenido_en.astimezone().strftime("%d/%m/%Y %H:%M:%S")

    print(f"COTIZACIÓN DE RESPALDO | Obtenida el {fecha_local} | Antigüedad: {minutos} min")
    mostrar_cotizacion_dolar(cotizacion)
    return cotizacion

def solicitar_monto_usd(cotizacion):
    while True:
        entrada = input("Monto en USD sin separador de miles (Enter para volver): ").strip()
        if not entrada:
            return

        try:
            total = cotizacion.calcular_pago_clp(entrada.replace(",", "."))
        except ValueError as error:
            print(error)
            continue

        pesos = f"{total:,.0f}".replace(",", ".")
        print(f"Pago estimado: {pesos} CLP")
        return

def elegir_ubicacion(lugares):
    if len(lugares) == 1:
        return lugares[0]

    opciones = {str(i): lugar for i, lugar in enumerate(lugares, start=1)}

    for numero, lugar in opciones.items():
        print(f"{numero}. {lugar.nombre}")

    while True:
        numero = input("Elige la ubicación (0 para volver): ").strip()

        if numero == "0":
            return None
        if numero in opciones:
            return opciones[numero]

        print("Elige uno de los números de la lista.")

def recuperar_clima(nombre, lugar):
    try:
        respaldos = leer_respaldos_clima(nombre, lugar)
    except OSError as error:
        print(error)
        return None

    if not respaldos:
        print("Todavía no hay clima guardado para esa ubicación.")
        return None

    if len(respaldos) > 1:
        print("Elige una de las ubicaciones guardadas:")

    elegido = elegir_ubicacion(list(respaldos))
    if elegido is None:
        return None

    clima, fecha = respaldos[elegido]
    antiguedad = datetime.now(timezone.utc) - fecha
    minutos = max(0, int(antiguedad.total_seconds() // 60))
    hora_local = fecha.astimezone().strftime("%d/%m/%Y %H:%M")

    print(f"CLIMA DE RESPALDO | Obtenido el {hora_local} | Antigüedad: {minutos} min")
    return elegido, clima


def consultar_clima_desde_menu(sesion):
    exigir_sesion(sesion)

    nombre = input("Ciudad o localidad del proyecto (Enter para volver): ").strip()
    if not nombre:
        return

    lugar = None
    
    try:
        lugares = buscar_ubicaciones(nombre)
        if not lugares:
            print("No se encontró la ubicación. Prueba con otra ciudad o localidad.")
            return

        lugar = elegir_ubicacion(lugares)
        if lugar is None:
            return

        clima = consultar_clima(lugar.latitud, lugar.longitud)

    except (ConnectionError, ValueError) as error:
        print(error)
        respaldo = recuperar_clima(nombre, lugar)
        if respaldo is None:
            return

        lugar, clima = respaldo

    else:
        try:
            guardar_clima(nombre, lugar, clima)
        except OSError as error:
            print(error)
    
    temperatura = f"{clima.temperatura_c:.1f} °C".replace(".", ",")
    humedad = f"{clima.humedad_porcentaje} %"
    encabezado = f"{'Temperatura':>12} | {'Humedad':>8} | Estado del tiempo"

    print(f"Ubicación: {lugar.nombre}")
    print(encabezado)
    print("-" * len(encabezado))
    print(f"{temperatura:>12} | {humedad:>8} | {clima.estado_tiempo}")