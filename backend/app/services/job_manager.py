"""
영상 분석 Job 상태 관리 (인메모리)
"""
import threading
import time
from typing import Dict, Any

_jobs: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()

# 모델(YOLO/VideoMAE/OCR)이 싱글턴이므로 동시 실행 불가 → 순차 처리
analysis_semaphore = threading.Semaphore(1)


def create_job(job_id: str, filename: str):
    with _lock:
        _jobs[job_id] = {
            "status":     "pending",
            "filename":   filename,
            "pct":        0,
            "step":       "대기 중",
            "start_time": None,
        }


def update_job(job_id: str, **kwargs):
    with _lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)


def get_jobs(job_ids: list) -> dict:
    now = time.time()
    with _lock:
        result = {}
        for jid in job_ids:
            if jid not in _jobs:
                continue
            job = dict(_jobs[jid])
            start = job.get("start_time")
            pct   = job.get("pct", 0)
            if start and pct > 3:
                elapsed  = now - start
                eta_sec  = int((elapsed / pct) * (100 - pct))
            else:
                eta_sec = None
            job["eta_sec"] = eta_sec
            result[jid] = job
        return result
