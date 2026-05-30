import threading
import queue
import time

job_queue = queue.Queue()
active_jobs = {}

def worker():
    while True:
        job = job_queue.get()
        if job is None:
            break
        try:
            # Здесь можно запускать process_single_image в фоне
            pass
        except:
            pass
        job_queue.task_done()

# Запуск worker
threading.Thread(target=worker, daemon=True).start()
