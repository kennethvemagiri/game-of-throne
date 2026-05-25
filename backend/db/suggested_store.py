import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_BUNDLED_PATH = Path(__file__).resolve().parent.parent / "data" / "suggested_jobs.json"
_TMP_PATH = Path("/tmp/got_data/suggested_jobs.json")


def _data_path() -> Path:
    if os.getenv("VERCEL") == "1":
        if not _TMP_PATH.exists():
            _TMP_PATH.parent.mkdir(parents=True, exist_ok=True)
            if _BUNDLED_PATH.exists():
                shutil.copy2(_BUNDLED_PATH, _TMP_PATH)
            else:
                _TMP_PATH.write_text("[]", encoding="utf-8")
        return _TMP_PATH
    return _BUNDLED_PATH


def _read_all() -> list[dict]:
    path = _data_path()
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("suggestedJobs", [])


def _write_all(jobs: list[dict]) -> None:
    path = _data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)


def get_all(*, status: Optional[str] = None) -> list[dict]:
    jobs = _read_all()
    if status:
        jobs = [j for j in jobs if j.get("status") == status]

    def sort_key(job: dict):
        return job.get("suggestedAt") or job.get("suggested_at") or ""

    return sorted(jobs, key=sort_key, reverse=True)


def get_by_id(job_id: str) -> Optional[dict]:
    return next((j for j in _read_all() if j.get("id") == job_id), None)


def upsert(job: dict) -> dict:
    jobs = _read_all()
    now = datetime.now(timezone.utc).isoformat()
    index = next((i for i, j in enumerate(jobs) if j.get("id") == job.get("id")), -1)

    if index >= 0:
        jobs[index] = {**jobs[index], **job, "updatedAt": now}
        _write_all(jobs)
        return jobs[index]

    new_job = {
        "id": job.get("id") or f"sj-{uuid.uuid4().hex[:8]}",
        "status": "pending",
        "suggestedAt": now,
        **job,
        "updatedAt": now,
    }
    jobs.append(new_job)
    _write_all(jobs)
    return new_job


def reject(job_id: str) -> Optional[dict]:
    jobs = _read_all()
    index = next((i for i, j in enumerate(jobs) if j.get("id") == job_id), -1)
    if index < 0:
        return None

    now = datetime.now(timezone.utc).isoformat()
    jobs[index] = {**jobs[index], "status": "rejected", "updatedAt": now}
    _write_all(jobs)
    return jobs[index]


def mark_viewed(job_id: str) -> Optional[dict]:
    jobs = _read_all()
    index = next((i for i, j in enumerate(jobs) if j.get("id") == job_id), -1)
    if index < 0:
        return None

    now = datetime.now(timezone.utc).isoformat()
    jobs[index] = {**jobs[index], "status": "viewed", "viewedAt": now, "updatedAt": now}
    _write_all(jobs)
    return jobs[index]
