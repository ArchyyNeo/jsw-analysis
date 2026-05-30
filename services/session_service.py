import os
import uuid
import shutil
import time
import streamlit as st
from utils.constants import SESSIONS_DIR, MAX_SESSION_AGE_HOURS


def get_session_id() -> str:
    """Возвращает или создаёт уникальный ID сессии пользователя"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def get_job_dir(job_id: str = None) -> tuple:
    """Создаёт и возвращает директорию для конкретного задания"""
    session_id = get_session_id()
    
    if job_id is None:
        job_id = f"job_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    
    job_dir = os.path.join(SESSIONS_DIR, session_id, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Создаём подпапки
    for subdir in ["input", "preprocessed", "masks", "results"]:
        os.makedirs(os.path.join(job_dir, subdir), exist_ok=True)
    
    return job_dir, job_id


def cleanup_old_sessions():
    """Очистка старых сессий (можно вызывать периодически)"""
    if not os.path.exists(SESSIONS_DIR):
        return
    
    now = time.time()
    for session_folder in os.listdir(SESSIONS_DIR):
        session_path = os.path.join(SESSIONS_DIR, session_folder)
        if os.path.isdir(session_path):
            try:
                mtime = os.path.getmtime(session_path)
                if (now - mtime) > (MAX_SESSION_AGE_HOURS * 3600):
                    shutil.rmtree(session_path, ignore_errors=True)
            except:
                pass
