# Ecotech E3 · Diego Lagos

## Preparación
En la raíz del proyecto, con Python 3.10 o superior, crea el entorno con
`py -m venv .venv` e instala con `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
Copia .env.example como .env y configura una base individual de Supabase.
Conserva tu .env y clave_fernet.key si ya existen. En una base nueva aplica
ecotech_supabase.sql y después migraciones/002_rut.sql. En una base existente
de esta rama aplica solo la migración de RUT. Los empleados existentes pueden
completar el RUT al editarse. En una base sin cuentas, el administrador con acceso
PostgreSQL ejecuta crear_gerente_inicial.py. Si existen cuentas antiguas,
prueba migrar_cuentas.py sobre una copia con la clave Fernet original.
Ejecuta cada script con el Python del entorno. La configuración personal y la
base SQLite se generan en el equipo y se excluyen del ZIP.

## Demostración
1. Ejecutar main.py y entrar con una cuenta registrada. Gerente: opción 18.
   Empleado: opción 3. Ingresar moneda origen, destino y monto, por ejemplo USD, CLP y 2.
2. Comprobar tasa, fuente, fecha del proveedor, fecha de consulta y pago estimado.
   Las tasas son diarias y el cálculo muestra dos decimales. No ejecuta un pago.
3. Después de una consulta válida, desconectar la red y volver a consultar:
   aparece el respaldo y su antigüedad. Una combinación sin respaldo devuelve un aviso.
4. Cerrar, iniciar sin red y autenticarse en ese equipo dentro de las 24 horas
   del último acceso válido en línea. Solo se pueden consultar tasas guardadas.
5. Ejecutar `.\.venv\Scripts\python.exe -m unittest discover -s pruebas -v`.
   Las pruebas HTTP simulan respuestas; SQLite utiliza archivos temporales.
6. Verificar en la base individual el alta y edición de empleado con RUT, la
   migración de cuentas y los permisos de ambos roles antes de entregar por AAI.

Proveedor: https://www.exchangerate-api.com/docs/free
La modalidad Open Access requiere atribución, que se muestra en cada consulta.
Si Retry-After supera 15 segundos se abandona esa consulta y se ofrece el respaldo,
sin reintentar antes del plazo. El proveedor abierto no tiene token que renovar.
La extensión elegida implementa tipo de cambio. La guía sumativa también describe
clima; confirmar con el docente si se deben demostrar ambas funciones.
