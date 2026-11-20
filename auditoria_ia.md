# Auditoría y bitácora de IA – Francisco Aniñir (EcoTech ES3)

Herramientas de IA usadas: Claude y Copilot (VS Code).
Parte desarrollada: consumo de la API de clima (Open-Meteo) para planificar proyectos.

## 1. Auditoría de 5 señales críticas

| # | Señal | Cómo lo revisé | Resultado |
|---|-------|----------------|-----------|
| 1 | SQL dinámico (f-strings) | Revisé `cache_local.py` | OK: todas las consultas usan `?` (parametrizadas) |
| 2 | `verify=False` (TLS desactivado) | Busqué `verify=False` con Ctrl+Shift+F | OK: no existe, `requests` verifica HTTPS |
| 3 | `except Exception: pass` | Busqué `except Exception` | OK: cada error se captura por su tipo y se avisa |
| 4 | Peticiones sin `timeout` | Revisé `requests.get` en `api_externa.py` | OK: usa `timeout=(3, 10)` |
| 5 | Librerías inexistentes | Revisé `requirements.txt` en pypi.org | OK: todas existen; agregué `requests==2.32.5` |

## 2. Bitácora de IA

| # | Lo que pedí | Lo que sugirió la IA | Decisión | Por qué |
|---|-------------|----------------------|----------|---------|
| 1 | Cliente para llamar a la API con reintentos | Clase `ClienteAPI` con timeout, 4 intentos y backoff | Modifico | Dejé 3 intentos (1 + 2 reintentos), renombré el error a `ErrorApiExterna` y escribí mis propios comentarios |
| 2 | Carpeta para guardar el registro (log) | Otra IA (Copilot) usó `.parent` y `mkdir(parents=True)` | Modifico | Con un solo `.parent` la carpeta quedaba dentro de `infraestructura`; usé `.parent.parent` para dejarla en la raíz y acepté `parents=True` |
| 3 | Ruta del archivo de registro | Ruta terminada en `.log` usada como carpeta y `hasHandlers()` | Modifico | Creaba una carpeta con nombre de archivo y no se podía escribir; separé carpeta (`registro`) y archivo (`api_externa.log`). Cambié `hasHandlers()` por `registro.handlers` |
| 4 | Revisar mi código pegado | Detectó la sangría mal puesta | Modifico | El `try` quedó dentro de `if self.token:` y la petición nunca se hacía; corregí la sangría |
| 5 | Considerar la nieve en el clima | Mantener la nieve en la lista | Acepto | Aunque donde vivo no nieva, los proyectos pueden estar en otras ciudades |
| 6 | Pylance ofreció revisión estricta de tipos | Activar la comprobación de tipos | Descarto | Llenaba de advertencias el código de todo el grupo; la validación ya la hace `DeserializadorAPI` |
| 7 | Guardar el clima localmente | `cache_local.py` con SQLite y consultas `?` | Acepto | Evita inyección SQL y no necesita internet ni claves |
| 8 | Qué hacer si la API falla | Plan B: usar la última copia guardada mostrando su fecha | Acepto | El programa no se cae y el usuario sabe que el dato es antiguo |
| 9 | Validar la ciudad | `validar_ciudad`: largo de 2 a 60 y solo letras | Acepto | Rechaza números y textos peligrosos antes de usarlos |
| 10 | Parte de monedas (pagos internacionales) | Segunda API para tipo de cambio | Descarto por ahora | Por tiempo prioricé dejar el clima completo y probado; `ClienteAPI` se puede reintentar |