import os
import json
import pandas as pd
from datetime import datetime
from services.session_service import get_session_id


def save_result(job_id: str, metrics: dict, result_image_path: str = None):
    """Сохраняет результат анализа в JSON + создаёт запись"""
    session_id = get_session_id()
    result_dir = os.path.join("temp/sessions", session_id, job_id, "results")
    os.makedirs(result_dir, exist_ok=True)

    result_data = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "result_image": os.path.basename(result_image_path) if result_image_path else None
    }

    json_path = os.path.join(result_dir, f"{job_id}_result.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    return result_data


def get_result(job_id: str):
    """Получает результат по job_id"""
    session_id = get_session_id()
    json_path = os.path.join("temp/sessions", session_id, job_id, "results", f"{job_id}_result.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_user_results():
    """Возвращает список всех результатов текущего пользователя"""
    session_id = get_session_id()
    results = []
    session_dir = os.path.join("temp/sessions", session_id)
    
    if not os.path.exists(session_dir):
        return results

    for job_folder in os.listdir(session_dir):
        json_path = os.path.join(session_dir, job_folder, "results", f"{job_folder}_result.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(data)
            except:
                continue

    return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)