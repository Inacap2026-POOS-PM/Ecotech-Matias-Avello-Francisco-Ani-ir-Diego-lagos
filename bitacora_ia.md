# Bitácora de uso de IA – EcoTech

**Estudiante:** Matías Avello  
**Evaluación:** E3 – Consumo de APIs, seguridad y persistencia  
**Herramienta utilizada:** ChatGPT

Usé la IA para revisar el checklist, comparar alternativas y probar casos difíciles de provocar manualmente, como una caída de la API. Las consultas de esta bitácora resumen lo que pregunté durante el desarrollo. En cada caso registro la sugerencia y el motivo de mi decisión.

## Consultas y decisiones

| Consulta que hice | Sugerencia de la IA | Mi decisión y motivo |
|---|---|---|
| ¿Cómo puedo implementar la API del dólar en EcoTech para consultar su valor en pesos chilenos? | Consultar DolarAPI con `requests` y extraer del JSON el precio de venta y la fecha de actualización. | **Acepto.** Así el gerente puede ingresar un monto en dólares, ver cuánto equivale en pesos chilenos y saber cuándo se actualizó la cotización. |
| ¿Qué pasa si el proyecto se realiza en otra ciudad? ¿Conviene pedir coordenadas? | Open-Meteo permite buscar una ubicación por nombre y usar sus coordenadas para consultar el clima. | **Modifico.** Dejé que la persona escriba la ciudad y elija entre las coincidencias. La aplicación usa las coordenadas del lugar seleccionado, así que el usuario no necesita conocerlas. |
| ¿Para qué usar SQLite si el sistema ya tiene Supabase? | Guardar localmente la última respuesta válida para consultarla cuando falle el servicio externo. | **Acepto.** Si falla la API, EcoTech puede mostrar un dato obtenido anteriormente. La consola indica que es un respaldo y muestra su antigüedad. En el clima también importa que el respaldo corresponda a la ubicación consultada. |
| ¿Hay que tratar igual un error 403 y uno 429? | Distinguir los códigos HTTP y limitar los reintentos. | **Acepto.** Repetir una consulta rechazada con 403 no corrige el problema. Ante un 429 se respeta `Retry-After` si está disponible. Para errores del servidor o de conexión se hacen hasta tres intentos y se registra cada uno. |
| ¿Puede el empleado consultar el dólar y el clima? | Habilitar ambas consultas para usuarios autenticados y comprobar el rol antes de ejecutar las funciones del gerente. | **Modifico.** Dejé las dos consultas disponibles para gerente y empleado. El cálculo de un pago en pesos a partir de un monto en dólares quedó en el menú del gerente. |
| Si olvido una contraseña, ¿conviene que el dueño de la base pueda verla? | Usar Argon2id con una sal aleatoria y migrar las cuentas antiguas cuando su titular inicie sesión correctamente. | **Descarto la idea de mostrar contraseñas.** Para comprobar el acceso basta con verificar la contraseña ingresada contra su hash. Además, elegí un mensaje general para que la consola no revele cuál de las credenciales falló. |
| ¿Cómo hago para que el gerente se dé cuenta si está ingresando a un empleado que ya estaba registrado? | Usar el RUT para detectar una ficha repetida y mostrar un aviso en la consola. | **Acepto.** Dos empleados pueden llamarse igual, así que preferí usar el RUT. Si el gerente repite uno, aparece el mensaje «Ese RUT ya está registrado» y puede revisar la ficha que ya existe. |

## Auditoría de las cinco señales del checklist

La revisión del código publicado se hizo sobre la rama `Matias_Avello_Ecotech_ev3`, commit `07e4f80`. Los cambios posteriores del inicio de sesión se comprobaron también en mi copia de trabajo.

| Señal revisada | Resultado |
|---|---|
| SQL construido con f-strings | En el código revisado no se encontraron f-strings que incorporen datos del usuario al SQL. PostgreSQL recibe los valores mediante `%s` y SQLite mediante parámetros. En las consultas reutilizadas para varias entidades, los nombres de tablas y columnas se toman de la configuración del proyecto y se componen con `psycopg.sql.Identifier`. |
| Verificación TLS desactivada | No se encontró `verify=False`. Las consultas web mantienen la verificación del certificado y la conexión a Supabase usa `sslmode="verify-full"`. |
| Errores ocultos | No se encontró `except Exception: pass`. Durante la revisión sí se detectó que un error de base de datos sin tratamiento específico podía mostrar una traza. Se ajustó `mostrar_error_supabase` para que ese caso tenga un mensaje general. |
| Peticiones sin tiempo de espera | Las dos llamadas a `requests.get`, en `infraestructura/apis/dolar.py` y `infraestructura/apis/cliente_http.py`, tienen `timeout=10`. La búsqueda de ciudades y la consulta del clima usan el cliente HTTP. |
| Dependencias de `requirements.txt` | Se comprobó en PyPI la existencia de `psycopg` con el extra `binary`, `python-dotenv`, `cryptography`, `cffi`, `openpyxl`, `reportlab` y `requests`. |

## Pruebas y resultados

**Pruebas que comprobé en mi entorno**

- **Cotización real.** Abrí la URL de DolarAPI en el navegador y vi los datos en JSON. En la consola comprobé que el precio de venta y la fecha se mostraban en una tabla. Así entendí que la hora de actualización corresponde al dato publicado por la API.
- **Migración de cuentas.** Ejecuté en Supabase la consulta que cuenta las credenciales pendientes de migrar. El resultado pasó de `2` a `1` y finalmente a `0`.
- **Inicio de sesión.** Probé mi usuario con una contraseña incorrecta y apareció el mensaje general de datos incorrectos. Volví a ingresar con la contraseña correcta y pude entrar al sistema.
- **Consulta del dólar sin internet.** Primero consulté el dólar con internet. Después apagué el Wi‑Fi y volví a elegir la misma opción. Tras tres intentos, el programa me avisó que no pudo obtener la cotización y mostró el valor que había guardado un minuto antes: 1.016,40 pesos por dólar. En la consola apareció como «COTIZACIÓN DE RESPALDO», así que pude reconocer que estaba viendo el último dato guardado.

**Pruebas realizadas con apoyo de IA en una copia del proyecto**

- Se ejecutaron 39 secuencias HTTP simuladas para el dólar, la búsqueda de ubicaciones y el clima. Se comprobaron respuestas exitosas, errores 4xx y 5xx, `Retry-After`, fallos de conexión y el límite de reintentos.
- Se simuló la caída de los servicios después de guardar una consulta válida. Tanto el dólar como el clima recuperaron datos de SQLite y mostraron la antigüedad del respaldo.
- En PostgreSQL local se probaron los cambios del RUT: guardar y recuperar una ficha, cargar una ficha antigua con RUT vacío y rechazar un RUT duplicado con el mensaje correspondiente.