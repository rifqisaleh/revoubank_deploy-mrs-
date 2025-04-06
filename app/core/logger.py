import logging

logger = logging.getLogger("revoubank")
logger.setLevel(logging.INFO)  # ✅ Use the constant, not the function

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
