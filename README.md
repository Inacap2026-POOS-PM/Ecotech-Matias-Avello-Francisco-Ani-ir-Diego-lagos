# EcoTech – Gestión de empleados y proyectos

EcoTech es una aplicación de consola en Python para una empresa dedicada al desarrollo de tecnologías sostenibles. Permite gestionar empleados, proyectos, departamentos y horas de trabajo. También permite consultar el clima de la ubicación de un proyecto y el valor del dólar en pesos chilenos.

Los datos de la empresa se guardan en PostgreSQL mediante Supabase. SQLite se utiliza para conservar las últimas consultas de las APIs y mostrarlas si el servicio externo falla.

## Instalación en Windows

Necesitas Python 3.10 o posterior, acceso al proyecto de Supabase y una terminal PowerShell. Abre en VS Code la carpeta que contiene `main.py`.

Si es la primera vez que ejecutas el proyecto en ese computador, ingresa estos comandos en orden:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En VS Code puedes seleccionar `.venv\Scripts\python.exe` desde **Python: Select Interpreter**.

## Configurar Supabase

1. Si estás preparando una base nueva, abre el editor SQL de tu proyecto de Supabase y ejecuta el contenido completo de `ecotech_supabase.sql`. Este script crea el esquema `ecotech`, sus tablas y restricciones.
2. Si ya utilizabas una versión anterior de EcoTech, comprueba que la base tenga la columna `rut`, su índice único y los campos de invitación. El script actualizado incluye esos cambios.
3. Si todavía no tienes un archivo `.env`, copia la plantilla desde PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Abre `.env` y completa los datos de conexión que aparecen en **Connect → Session pooler** de tu proyecto.

| Variable | Qué debes ingresar |
|---|---|
| `SUPABASE_DB_HOST` | Servidor del Session pooler. |
| `SUPABASE_DB_PORT` | Puerto indicado para la conexión. La plantilla usa `5432`. |
| `SUPABASE_DB_NAME` | Nombre de la base. La plantilla usa `postgres`. |
| `SUPABASE_DB_USER` | Usuario de PostgreSQL indicado por Supabase. |
| `SUPABASE_DB_PASSWORD` | Contraseña de PostgreSQL. Si la dejas vacía, EcoTech la solicita al iniciar. |
| `SUPABASE_SSLROOTCERT` | Déjala vacía para usar `supabase-ca.crt`, incluido en la raíz del proyecto. |

La conexión verifica el certificado y el nombre del servidor con `sslmode="verify-full"`. Guarda las credenciales reales en tu `.env` local. El archivo que se comparte en el repositorio es `.env.example`.

## Iniciar EcoTech

Desde la carpeta que contiene `main.py`, ejecuta:

```powershell
.\.venv\Scripts\python.exe main.py
```

Si ya tienes el entorno virtual activado, también puedes usar `python main.py`.

Al iniciar, EcoTech se conecta a Supabase, verifica las tablas y muestra **ECOTECH - ACCESO**. La contraseña de PostgreSQL permite conectar el programa a la base. El usuario y la contraseña de EcoTech determinan quién entra al sistema y qué menú puede utilizar.

## Primera cuenta y acceso de empleados

1. En una instalación nueva, selecciona **2. Crear primer gerente** y completa la ficha y las credenciales.
2. Inicia sesión como gerente. Para incorporar a un empleado, selecciona **1. Registrar trabajador** y asígnale el rol **Empleado**.
3. EcoTech muestra un código de invitación de un solo uso, válido por 24 horas. Entrega ese código al empleado en privado.
4. Desde la pantalla de acceso, el empleado selecciona **2. Crear cuenta de empleado con invitación**, ingresa el código y elige su propio nombre de usuario y contraseña.

| Rol | Funciones principales |
|---|---|
| Gerente | Gestionar empleados y cuentas, administrar proyectos y departamentos, registrar asignaciones y horas, consultar el historial, generar informes, consultar el clima y calcular un pago en pesos a partir de un monto en dólares. |
| Empleado | Consultar sus propios datos y horas de trabajo, revisar el clima de un proyecto y consultar el precio del dólar. |

## Validación de datos y contraseñas

- **RUT.** Se ingresa sin puntos y con guion, por ejemplo `12345678-5`. El programa comprueba el dígito verificador y la base impide registrar dos fichas con el mismo RUT.
- **Celular.** Se ingresa con `+569` seguido de ocho dígitos, por ejemplo `+56912345678`.
- **Correo.** El formulario del proyecto solicita una dirección terminada en `@gmail.com`.
- **Contraseñas.** EcoTech guarda un hash Argon2id con una sal aleatoria. Al iniciar sesión comprueba la contraseña contra ese hash. Si los datos son incorrectos, muestra un mensaje general. La versión actual funciona sin `clave_fernet.key`.

## Consultas de dólar y clima

| Consulta | Menú del gerente | Menú del empleado | Información que muestra |
|---|---:|---:|---|
| Dólar | 18 | 4 | DolarAPI entrega el precio de venta en CLP por USD y la fecha de actualización. El gerente también puede ingresar un monto en USD para calcular su equivalente en pesos. |
| Clima | 19 | 3 | Open-Meteo busca la ubicación por nombre. Si hay varias coincidencias, el usuario elige el lugar. Se muestran temperatura, humedad y estado del tiempo. |

Las peticiones tienen un tiempo de espera de 10 segundos. Ante fallos de red o errores del servidor, EcoTech realiza hasta tres intentos. Si recibe un código 429, utiliza el tiempo de espera indicado por `Retry-After` cuando está disponible.

Después de una consulta exitosa, el dólar se guarda en `cotizaciones.sqlite3` y el clima en `clima.sqlite3`. Si una consulta posterior falla durante la sesión, EcoTech busca un respaldo y muestra cuándo lo obtuvo y su antigüedad. Para el clima, el respaldo debe corresponder a la ubicación consultada. Si todavía no existe, la consola lo indica. El inicio de sesión requiere conexión a Supabase.

## Informes

Desde el menú del gerente se puede consultar el informe general en consola (**15**), guardarlo en Excel (**16**) o guardarlo en PDF (**17**). Los archivos se crean en `reportes/`, junto a `main.py`.

[Ver las instrucciones de exportación](COMO_EXPORTAR.md)

## Organización del proyecto

| Archivo o carpeta | Responsabilidad |
|---|---|
| `main.py` | Inicia la aplicación y configura el registro de las consultas a las APIs. |
| `presentacion/` | Inicio del programa, autenticación desde consola, menús, formularios y mensajes de error. |
| `dominio/` | Clases de empleados, cuentas, proyectos e informes, verificación de contraseñas y modelos de los datos externos. |
| `infraestructura/conexion.py` | Conexión segura a Supabase y comprobación de las tablas. |
| `infraestructura/repositorio.py` | Lectura y escritura de datos, cuentas, invitaciones e historial. |
| `infraestructura/apis/` | Consultas HTTP a DolarAPI y Open-Meteo. |
| `infraestructura/respaldo_dolar.py` y `respaldo_clima.py` | Guardado y recuperación de las consultas en SQLite. |
| `validaciones.py` | Reglas compartidas para validar los datos ingresados. |
| `ecotech_supabase.sql` | Creación y actualización del esquema de la base de datos. |
| `bitacora_ia.md` | Consultas realizadas durante el desarrollo, decisiones y resultados de las pruebas. |