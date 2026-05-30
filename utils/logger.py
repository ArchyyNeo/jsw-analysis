import logging
import os
from datetime import datetime


os.makedirs("logs", exist_ok=True)

log_file = os.path.join(
    "logs",
    f"{datetime.now():%Y-%m-%d}.log"
)

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("jsw")
