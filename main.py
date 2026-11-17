import logging
from pathlib import Path

from presentacion.inicio import iniciar_programa


if __name__ == "__main__":
    logging.basicConfig(
        filename=Path(__file__).with_name("ecotech_api.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        encoding="utf-8"
    )
    iniciar_programa()