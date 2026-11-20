from contextlib import nullcontext
from decimal import Decimal
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from infraestructura import servicios_externos as api
from presentacion.cotizaciones import consultar_pago


def respuesta(estado, espera=None):
    r = Mock(status_code=estado, headers={"Retry-After": espera} if espera else {})
    r.json.return_value = dict(result="success", base_code="USD",
                               rates={"CLP": Decimal("950.25")}, time_last_update_unix=1795046551)
    return nullcontext(r)


class PruebasE3(unittest.TestCase):
    def test_estados_definitivos(self):
        for estado in (301, 400, 401, 403, 404):
            with self.subTest(estado=estado), patch.object(api.requests, "get", return_value=respuesta(estado)) as get:
                with self.assertRaises(api.ServicioNoDisponible):
                    api.consultar_api("USD", "CLP")
                self.assertEqual(get.call_count, 1)

    @patch.object(api.time, "sleep")
    def test_reintentos(self, dormir):
        for falla in (api.requests.Timeout(), api.requests.ConnectionError()):
            dormir.reset_mock()
            with patch.object(api.requests, "get", side_effect=falla) as get:
                with self.assertRaises(api.ServicioNoDisponible):
                    api.consultar_api("USD", "CLP")
                self.assertEqual(get.call_count, 4)
                self.assertEqual([x.args[0] for x in dormir.call_args_list], [1, 2, 4])

    @patch.object(api.time, "sleep")
    def test_cuota_y_servidor(self, dormir):
        with patch.object(api.requests, "get", side_effect=[respuesta(429, "3"), respuesta(503), respuesta(200)]) as get:
            self.assertEqual(api.consultar_api("USD", "CLP").tasa, Decimal("950.25"))
            self.assertEqual([x.args[0] for x in dormir.call_args_list], [3, 2])
            self.assertEqual(get.call_args.kwargs["timeout"], (3, 10))
        with patch.object(api.requests, "get", return_value=respuesta(429, "120")) as get:
            with self.assertRaises(api.ServicioNoDisponible):
                api.consultar_api("USD", "CLP")
            self.assertEqual(get.call_count, 1)

    def test_pago_y_respaldo(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"ECOTECH_SQLITE_PATH": str(Path(d)/"e3.db")}):
            for rol, evento, esperado in (
                ("Gerente", respuesta(200), "1900.50"),
                ("Empleado", respuesta(404), "1900.50"),
                ("Local", None, "1900.50"),
            ):
                with patch.object(api.requests, "get", return_value=evento) as get, patch("builtins.input", side_effect=["USD","CLP","2"]), patch("builtins.print") as salida:
                    consultar_pago({"rol":rol})
                    self.assertIn(esperado, str(salida.call_args_list))
                    if rol == "Local":
                        get.assert_not_called()
            with patch("builtins.input", side_effect=["CLP","EUR","2"]), patch("builtins.print") as salida:
                consultar_pago({"rol":"Local"})
                self.assertIn("No hay cotizacion", str(salida.call_args_list))
        with self.assertRaises(PermissionError):
            consultar_pago(None)
