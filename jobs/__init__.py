"""
Jobs модуль — отвечает за фоновую обработку задач (очередь, worker'ы).
Поддерживает многопользовательский режим.
"""

from .job_queue import job_queue, worker, active_jobs

__all__ = [
    "job_queue",
    "worker",
    "active_jobs",
]