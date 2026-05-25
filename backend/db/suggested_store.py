import logging
from datetime import datetime, timezone
from typing import Optional

from backend.db.supabase_client import get_client

logger = logging.getLogger(__name__)

_DB_COLUMNS = {
    "id", "source", "company", "role", "url", "snippet",
    "status", "suggested_at", "viewed_at", "created_at", "updated_at",
}

_CAMEL_TO_SNAKE = {
    "suggestedAt": "suggested_at",
    "viewedAt": "viewed_at",
    "createdAt": "created_at",
    "updatedAt": "updated_at",
}


def _to_db_row(data: dict) -> dict:
    row: dict = {}
    for key, value in data.items():
        db_key = _CAMEL_TO_SNAKE.get(key, key)
        if db_key in _DB_COLUMNS:
            row[db_key] = value
    return row


def _to_job_dict(row: dict) -> dict:
    job = dict(row)
    job.setdefault("suggestedAt", job.get("suggested_at"))
    job.setdefault("viewedAt", job.get("viewed_at"))
    job.setdefault("createdAt", job.get("created_at"))
    job.setdefault("updatedAt", job.get("updated_at"))
    return job


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_all(*, status: Optional[str] = None) -> list[dict]:
    try:
        query = get_client().table("suggested_jobs").select("*")
        if status:
            query = query.eq("status", status)
        result = query.order("suggested_at", desc=True).execute()
        return [_to_job_dict(row) for row in result.data]
    except Exception:
        logger.exception("[suggested_store] Failed to fetch suggested jobs")
        raise


def get_by_id(job_id: str) -> Optional[dict]:
    try:
        result = get_client().table("suggested_jobs").select("*").eq("id", job_id).execute()
        return _to_job_dict(result.data[0]) if result.data else None
    except Exception:
        logger.exception(f"[suggested_store] Failed to fetch job {job_id}")
        raise


def upsert(job: dict) -> dict:
    try:
        row = _to_db_row(job)
        now = _now_iso()
        row["updated_at"] = now
        row.setdefault("suggested_at", now)
        row.setdefault("status", "pending")

        if job.get("id"):
            existing = get_by_id(job["id"])
            if existing:
                result = (
                    get_client()
                    .table("suggested_jobs")
                    .update(row)
                    .eq("id", job["id"])
                    .execute()
                )
                return _to_job_dict(result.data[0])

        row.pop("id", None)
        result = get_client().table("suggested_jobs").insert(row).execute()
        return _to_job_dict(result.data[0])
    except Exception:
        logger.exception("[suggested_store] Failed to upsert job")
        raise


def reject(job_id: str) -> Optional[dict]:
    try:
        now = _now_iso()
        result = (
            get_client()
            .table("suggested_jobs")
            .update({"status": "rejected", "updated_at": now})
            .eq("id", job_id)
            .execute()
        )
        return _to_job_dict(result.data[0]) if result.data else None
    except Exception:
        logger.exception(f"[suggested_store] Failed to reject job {job_id}")
        raise


def mark_viewed(job_id: str) -> Optional[dict]:
    try:
        now = _now_iso()
        result = (
            get_client()
            .table("suggested_jobs")
            .update({"status": "viewed", "viewed_at": now, "updated_at": now})
            .eq("id", job_id)
            .execute()
        )
        return _to_job_dict(result.data[0]) if result.data else None
    except Exception:
        logger.exception(f"[suggested_store] Failed to mark job {job_id} viewed")
        raise
