import os
import cv2
import numpy as np
import tensorflow as tf
import keras_cv as kcv
from utils.constants import IMAGE_SIZE
from ultralytics import YOLO


# Глобальная загрузка YOLOv8n (один раз)
YOLO_AVAILABLE = False
yolo_model = None

try:
    yolo_model = YOLO("yolov8n.pt")
    YOLO_AVAILABLE = True
    print("[+] YOLOv8n успешно загружена")
except Exception as e:
    print(f"[-] YOLOv8n не загружена: {e}. Будет использоваться центральный кроп.")

normalize_pipeline = tf.keras.Sequential([
    kcv.layers.Equalization(value_range=(0, 255)),
    tf.keras.layers.Rescaling(1.0 / 255.0)
])


def crop_with_yolo(img_path: str, target_size=IMAGE_SIZE):
    """Умный кроп с YOLO + фолбэк на центр"""
    img = cv2.imread(img_path)
    if img is None:
        return None

    h, w = img.shape[:2]
    if h == target_size[0] and w == target_size[1]:
        return img

    if YOLO_AVAILABLE and yolo_model is not None:
        try:
            results = yolo_model(img, verbose=False)
            for r in results:
                person_boxes = [box for box in r.boxes if int(box.cls[0]) == 0]
                if person_boxes:
                    box = person_boxes[0]
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    bw, bh = x2 - x1, y2 - y1
                    box_size = int(max(bw, bh) * 1.1)

                    nx1 = max(0, cx - box_size // 2)
                    ny1 = max(0, cy - box_size // 2)
                    nx2 = min(w, nx1 + box_size)
                    ny2 = min(h, ny1 + box_size)

                    cropped = img[ny1:ny2, nx1:nx2]
                    return cv2.resize(cropped, target_size, interpolation=cv2.INTER_AREA)
        except:
            pass

    # Фолбэк — центральный квадрат
    crop_size = min(h, w)
    nx1 = (w - crop_size) // 2
    ny1 = (h - crop_size) // 2
    cropped = img[ny1:ny1 + crop_size, nx1:nx1 + crop_size]
    return cv2.resize(cropped, target_size, interpolation=cv2.INTER_AREA)


def save_preprocessed_image(input_image_path: str, output_image_path: str, image_size=IMAGE_SIZE):
    """Основная функция предобработки"""
    img_cropped = crop_with_yolo(input_image_path, image_size)
    if img_cropped is None:
        raise ValueError(f"Не удалось прочитать изображение: {input_image_path}")

    # Grayscale
    if len(img_cropped.shape) == 3:
        img_gray = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2GRAY)
    else:
        img_gray = img_cropped

    img_array = np.expand_dims(img_gray, axis=-1).astype(np.float32)

    # Нормализация в 8-bit
    img_8bit = cv2.normalize(img_array, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    if len(img_8bit.shape) == 2:
        img_8bit = np.expand_dims(img_8bit, axis=-1)

    # KerasCV пайплайн
    img_batch = tf.expand_dims(img_8bit, axis=0)
    processed = normalize_pipeline(img_batch)

    # Сохранение
    processed = tf.cast(processed[0] * 255.0, tf.uint8)
    encoded_img = tf.io.encode_png(processed)
    tf.io.write_file(output_image_path, encoded_img)
