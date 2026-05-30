import os
import re


def extract_metadata(image_path: str):
    """Извлекает patient_id и сторону (L/R) из имени файла"""
    filename = os.path.basename(image_path)
    match = re.match(r"(\d+)([LR])", os.path.splitext(filename)[0], re.IGNORECASE)
    if match:
        return match.group(1), match.group(2).upper()
    return os.path.splitext(filename)[0], "R"


def is_valid_image_filename(filename: str) -> bool:
    """Проверяет, содержит ли имя файла L или R"""
    return bool(re.search(r"[LR]", os.path.splitext(filename)[0], re.IGNORECASE))


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()
