import logging

from .constants import DEBUG

logger = logging.Logger(__name__)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
