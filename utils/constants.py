import torch
import os


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMAGE_SIZE = (224, 224)
MAX_DEVIATION_PCT = 0.12          # Максимальное смещение центра сустава
CENTRAL_BLIND_ZONE_PCT = 0.10     # Слепая зона в центре

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".JPG", ".PNG", ".JPEG"}
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024

# Пути
TEMP_DIR = "temp"
SESSIONS_DIR = os.path.join(TEMP_DIR, "sessions")
RESULTS_DIR = "results"

# Таймауты и ограничения
MAX_SESSION_AGE_HOURS = 1
BATCH_MAX_FILES = 500
