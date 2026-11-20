import logging
import time
from pathlib import Path

import requests

carpeta_registro = Path(__file__).resolve().parent.parent / "registro"
carpeta_registro.mkdir(parents=True, exist_ok=True)

registro = logging.getLogger("ecotech.api_externa")
if not registro.handlers:
    manejador = logging.FileHandler(carpeta_registro / "api_externa.log", encoding="utf-8")
    manejador.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    registro.addHandler(manejador)
    registro.setLevel(logging.INFO)

TIEMPO_ESPERA = (3, 10)  # Timeout: 3 s para conectar y 10 s para recibir la respuesta
MAX_INTENTOS = 3  # Número de intentos 1 y se puede reintentar 2 veces más, total 3 intentos
ESPERA_INICIAL = 1  # Segundos que espera antes de reintentar. Cada vez espera el doble: 1 s, luego 2 s


class ErrorApiExterna(Exception):
    """Error cuando la API falla. Muestra un mensaje seguro al usuario."""


class ClienteAPI:
    def __init__(self, nombre_servicio, renovar_token=None):
        self.nombre_servicio = nombre_servicio
        self.renovar_token = renovar_token
        self.token = None

    def obtener_json(self, url, parametros=None):
        espera = ESPERA_INICIAL
        token_renovado = False
        for intento in range(1, MAX_INTENTOS + 1):
            cabeceras = {"accept": "application/json"}
            if self.token:
                cabeceras["Authorization"] = "Bearer " + self.token

            try:
                respuesta = requests.get(url, params=parametros, headers=cabeceras, timeout=TIEMPO_ESPERA)

            except (requests.Timeout, requests.ConnectionError) as error:
                registro.warning("%s intento %d/%d: fallo de red (%s)", self.nombre_servicio,
                                 intento, MAX_INTENTOS, type(error).__name__)

            else:
                codigo_estado = respuesta.status_code
                registro.info("%s intento %d/%d: HTTP %d",
                              self.nombre_servicio, intento, MAX_INTENTOS, codigo_estado)

                if codigo_estado == 200:
                    try:
                        return respuesta.json()
                    except ValueError as error:
                        raise ErrorApiExterna(f"{self.nombre_servicio} respondio con datos invalidos.") from error

                if codigo_estado == 401 and self.renovar_token and not token_renovado:
                    self.token = self.renovar_token()
                    token_renovado = True
                    continue  # Reintentar inmediatamente con el nuevo token

                if codigo_estado == 429:
                    espera_429 = self._leer_retry_after(respuesta, espera)
                    registro.warning("%s limite de consultas alcanzado: espera %ss",
                                     self.nombre_servicio, espera_429)
                    if intento < MAX_INTENTOS:
                        time.sleep(espera_429)
                        continue  # Reintentar después de esperar

                if 400 <= codigo_estado < 500:
                    raise ErrorApiExterna(self.mensaje_error(codigo_estado))

            if intento < MAX_INTENTOS:
                registro.info("%s reintentando en %ss", self.nombre_servicio, espera)
                time.sleep(espera)
                espera *= 2  # Doble del tiempo de espera para el siguiente intento

        raise ErrorApiExterna(f"{self.nombre_servicio} no responde. Por favor, intente nuevamente más tarde.")

    @staticmethod
    def _leer_retry_after(respuesta, espera_por_defecto):
        valor = respuesta.headers.get("Retry-After", "")
        if valor.isdigit():
            return min(int(valor), 60)  # Limitar a 60 segundos
        return espera_por_defecto

    def mensaje_error(self, codigo_estado):
        mensajes = {
            400: "Solicitud incorrecta. Por favor, verifique los parámetros.",
            401: "No autorizado. Por favor, verifique sus credenciales.",
            403: "Prohibido. No tiene permiso para acceder a este recurso.",
            404: "Recurso no encontrado. Por favor, verifique la URL.",
        }
        return f"{self.nombre_servicio} error {codigo_estado}: {mensajes.get(codigo_estado, 'la consulta fue rechazada.')}"                      