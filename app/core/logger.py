import logging
from flask import current_app

logger = logging.getLogger("revoubank")

# We'll set this level dynamically later inside create_app()
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
