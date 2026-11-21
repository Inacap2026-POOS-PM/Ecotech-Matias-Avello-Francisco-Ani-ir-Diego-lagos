import logging

from presentacion.inicio import iniciar_programa


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    iniciar_programa()
