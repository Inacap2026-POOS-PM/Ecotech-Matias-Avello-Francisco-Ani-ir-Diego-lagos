# Bitácora de IA · E3

Evidencia del desarrollo asistido. Las decisiones siguientes describen propuestas
y ajustes realizados durante el chat. La explicación individual y las pruebas
que Diego realice deben añadirse con sus propios resultados.

| Petición del chat | Propuesta y componente | Decisión y fundamento |
|---|---|---|
| «elige un api que sea gratis que no me cause gastos» | ExchangeRate-API Free con clave inicialmente; cliente servicios_externos.py | Modifico a Open Access sin cuenta. Permite mostrar tasas y atribución sin facturación. |
| «pon una base local» | Guardar en Supabase o SQLite | Descarto depender de Supabase para el respaldo porque también necesita red. Acepto SQLite y consultas parametrizadas. |
| Diseñar login sin Internet | Guardar verificador local tras login correcto | Acepto Argon2id, vigencia de 24 horas y modo solo lectura. Una cuenta revocada fuera de línea no puede revalidarse hasta reconectar. |
| Conservar cuentas antiguas | Reutilizar Fernet para contraseñas nuevas | Descarto almacenamiento reversible. Conservo hashes existentes y convierto credenciales antiguas en una transacción. |
| «diferencias entre gerente y usuario» | Mostrar menús distintos | Modifico el control para comprobar el rol también al ejecutar operaciones y limitar las consultas personales al ID de sesión. |
| «genera las ultimas partes altiro» | Cliente, respaldo e integración | Acepto separar transporte, deserialización y persistencia. Decimal conserva la precisión del JSON. El respaldo se usa cuando la consulta falla. |

## Cinco señales revisadas
- SQL: el historial concatenaba cláusulas constantes. Se sustituyó por una consulta fija con filtros parametrizados. Los identificadores genéricos existentes pasan por una lista permitida y psycopg.sql.Identifier.
- TLS: el cliente conserva verificación y trata un error de certificado como definitivo.
- Excepciones: se distinguen TLS, red, timeout, respuesta inválida y error de base. El cliente informa el fallo antes de usar respaldo.
- Timeout: el GET usa límites explícitos de conexión y lectura. Los reintentos tienen tope y se registran sin claves ni datos de empleados.
- Paquetes: el requirements original decía request. Se corrigió a requests, verificado en PyPI durante la parte 1. sqlite3 viene con el intérprete utilizado.

## Evidencia de comprobación
Cuatro pruebas automatizadas cubrieron estados definitivos, red y timeout, 429 y
503, y conversión con respaldo local y sin sesión. Se ejecutaron con respuestas
HTTP simuladas y SQLite temporal. En el entorno de revisión se utilizó Requests
incluido en pip porque el entorno no tenía instalada la dependencia independiente.
Pendientes: conexión en vivo desde main.py con requirements instalado, migración
PostgreSQL y demostración individual con ambos roles. No se atribuyen a Diego
pruebas, decisiones personales ni resultados que aún no haya realizado.

## Revisión de la Clase 13 · 20 de noviembre de 2026

Petición de Diego: «vuelves a analizarlas y realiza cambios que diga». Se revisaron los 17 HTML de *Cuando la red falla*. Estas son las decisiones de la revisión técnica.

| Señal o sugerencia | Decisión y fundamento |
|---|---|
| SQL con valores interpolados | Acepto mantener parámetros para los valores y la lista permitida de identificadores en el repositorio. |
| Desactivar la comprobación de certificados | Descarto esa opción. El cliente conserva la verificación TLS y comunica el fallo de certificado. |
| Silenciar excepciones | Modifico los mensajes para distinguir URL inválida, falta de permiso, recurso inexistente, cuota agotada, timeout y fallo de conexión. La consola informa el motivo antes de consultar SQLite. |
| Peticiones sin timeout y reintentos simultáneos | Acepto mantener el timeout de 10 segundos y cuatro intentos como máximo. A la espera de 1, 2 y 4 segundos se añaden hasta 0,5 segundos aleatorios. El cliente respeta Retry-After y registra la demora. |
| Dependencias inventadas | Conservo Requests, verificado en PyPI durante la integración. La variación de espera usa la biblioteca estándar de Python. |

Verificación local: pasaron cinco pruebas. La nueva usa una URL sin esquema desde la consulta de un empleado con SQLite temporal. Requests rechaza la dirección, la aplicación lo explica e indica que no hay cotización guardada. La prueba comprueba que no hubo espera de reintento. Las pruebas de red caída, 429 y 503 simulan los fallos.
