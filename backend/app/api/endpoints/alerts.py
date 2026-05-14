import os, sys, uuid, time, threading, tempfile
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from typing import List

router = APIRouter()

class TimestampUpdate(BaseModel):
    timestamp: str

class SituationUpdate(BaseModel):
    situation: str

@router.get("/events")
async def get_all_events(limit: int = 300):
    """모든 비디오 이벤트 조회 (Event History 용)"""
    from app.services.database import db_service
    return db_service.get_all_events(limit)

@router.get("/events/pending")
async def get_pending_events(limit: int = 100):
    """timestamp가 NULL인 처리대기 이벤트 조회"""
    from app.services.database import db_service
    return db_service.get_pending_events(limit)

@router.patch("/events/{event_id}/timestamp")
async def update_event_timestamp(event_id: str, body: TimestampUpdate):
    """이벤트 timestamp 수동 입력"""
    from app.services.database import db_service
    ok = db_service.update_event_timestamp(event_id, body.timestamp)
    if ok:
        return {"status": "success", "message": f"이벤트 {event_id} timestamp 업데이트 완료"}
    return {"status": "error", "message": "업데이트 실패"}

@router.post("/admin/fix-timestamps")
async def fix_timestamps():
    """기존 이벤트 타임스탬프 KST 보정 (최초 1회만 실행)"""
    from app.services.database import db_service
    from app.services.vector_db_service import vector_db_service
    result = db_service.fix_timestamps_kst()
    if result.get("status") == "success":
        vector_db_service.reload()
    return result

@router.patch("/events/{event_id}/situation")
async def resolve_event_conflict(event_id: str, body: SituationUpdate):
    """분류 충돌 이벤트의 상황을 사용자가 확정하고 처리대기에서 제거"""
    from app.services.database import db_service
    from app.services.vector_db_service import vector_db_service
    ok = db_service.resolve_event_conflict(event_id, body.situation)
    if ok:
        vector_db_service.reload()
        return {"status": "success", "message": f"이벤트 {event_id} 상황 확정 완료"}
    return {"status": "error", "message": "처리 실패"}

@router.post("/analyze")
async def start_analyze(files: List[UploadFile] = File(...)):
    """영상 파일을 받아 백그라운드에서 분석 시작, job_id 목록 반환"""
    from app.services.job_manager import create_job, update_job

    _BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    jobs_out = []
    for file in files:
        job_id  = str(uuid.uuid4())
        suffix  = os.path.splitext(file.filename or "video")[-1] or ".mp4"
        content = await file.read()

        # 임시 파일에 저장 (원본 파일명 유지)
        tmp_dir  = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, file.filename or f"upload{suffix}")
        with open(tmp_path, "wb") as f:
            f.write(content)

        create_job(job_id, file.filename or "unknown")
        jobs_out.append({"job_id": job_id, "filename": file.filename})

        def _run(jid=job_id, path=tmp_path, tdir=tmp_dir):
            import shutil, importlib.util
            from app.services.job_manager import analysis_semaphore
            update_job(jid, status="pending", step="대기 중 (이전 영상 분석 완료 후 시작)")
            analysis_semaphore.acquire()
            try:
                update_job(jid, status="running", start_time=time.time())
                spec = importlib.util.spec_from_file_location(
                    "makeJsonData",
                    os.path.join(_BACKEND, "makeData", "makeJsonData.py"),
                )
                mod = importlib.util.module_from_spec(spec)
                if mod.__name__ not in sys.modules:
                    sys.modules[mod.__name__] = mod
                    spec.loader.exec_module(mod)
                else:
                    mod = sys.modules[mod.__name__]
                mod.process_video(path, model_type="v8",
                                  progress_cb=lambda pct, step: update_job(jid, pct=pct, step=step))
                update_job(jid, status="done", pct=100, step="완료")
            except Exception as e:
                update_job(jid, status="error", step=str(e)[:120])
            finally:
                analysis_semaphore.release()
                shutil.rmtree(tdir, ignore_errors=True)

        threading.Thread(target=_run, daemon=True).start()

    return {"jobs": jobs_out}


@router.get("/analyze/status")
async def get_analyze_status(job_ids: str):
    """job_id 쉼표 목록으로 각 작업의 진행 상태 반환"""
    from app.services.job_manager import get_jobs
    return get_jobs(job_ids.split(","))


@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """이벤트 삭제 (관리자 전용)"""
    from app.services.database import db_service
    ok = db_service.delete_event(event_id)
    if ok:
        return {"status": "success", "message": f"이벤트 {event_id} 삭제 완료"}
    return {"status": "error", "message": "삭제 실패"}
