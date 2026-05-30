import os
import streamlit as st
from core.model_loader import load_model
from core.preprocess import save_preprocessed_image
from core.inference import run_inference_on_single_file
from core.visualization import visualize_professional_jsw
from services.session_service import get_job_dir


def process_single_image(uploaded_file) -> dict:
    """Основная функция обработки одного изображения"""
    
    job_dir, job_id = get_job_dir()
    
    # Пути
    input_path = os.path.join(job_dir, "input", uploaded_file.name)
    preprocessed_path = os.path.join(job_dir, "preprocessed", uploaded_file.name)
    mask_dir = os.path.join(job_dir, "masks")
    result_path = os.path.join(job_dir, "results", f"result_{uploaded_file.name}")

    try:
        # 1. Сохраняем исходный файл
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 2. Предобработка
        save_preprocessed_image(input_path, preprocessed_path)

        # 3. Инференс
        model = load_model()
        run_inference_on_single_file(model, preprocessed_path, mask_dir)

        mask_path = os.path.join(mask_dir, uploaded_file.name)

        # 4. Визуализация и расчёт метрик
        success, metrics = visualize_professional_jsw(
            mask_path, 
            preprocessed_path, 
            result_path
        )

        return {
            "success": success,
            "metrics": metrics,
            "result_image_path": result_path if success else None,
            "job_id": job_id,
            "input_filename": uploaded_file.name
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "job_id": job_id
        }