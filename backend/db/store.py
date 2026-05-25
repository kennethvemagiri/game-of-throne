import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_BUNDLED_PATH = Path(__file__).resolve().parent.parent / "data" / "applications.json"
_TMP_PATH = Path("/tmp/got_data/applications.json")

ALLOWED_REVIEW_STATUSES = {
    "interview",
    "assessment",
    "recruiter_inbound",
    "acknowledged",
    "rejected",
    "applied",
}


def _data_path() -> Path:
    """Return a writable data path. On Vercel the bundled path is read-only,
    so we copy it to /tmp on first access and use that copy going forward."""
    if os.getenv("VERCEL") == "1":
        if not _TMP_PATH.exists():
            _TMP_PATH.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_BUNDLED_PATH, _TMP_PATH)
        return _TMP_PATH
    return _BUNDLED_PATH


def _read_all() -> list[dict]:
    path = _data_path()
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("applications", [])


def _write_all(applications: list[dict]) -> None:
    path = _data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(applications, f, indent=2)


def get_all(*, status: Optional[str] = None, needs_review: bool = False) -> list[dict]:
    apps = [a for a in _read_all() if a.get("status") != "archived"]
    if status:
        apps = [a for a in apps if a.get("status") == status]
    if needs_review:
        apps = [
            a
            for a in apps
            if a.get("status") == "needs_review" and (a.get("review") or {}).get("reviewed") is not True
        ]

    def sort_key(app: dict):
        return app.get("received_at") or app.get("receivedAt") or app.get("classified_at") or ""

    return sorted(apps, key=sort_key, reverse=True)


def get_by_id(app_id: str) -> Optional[dict]:
    return next((a for a in _read_all() if a.get("id") == app_id), None)


def upsert(application: dict) -> dict:
    apps = _read_all()
    now = datetime.now(timezone.utc).isoformat()
    index = next(
        (
            i
            for i, a in enumerate(apps)
            if a.get("id") == application.get("id")
            or a.get("email_id") == application.get("email_id")
            or a.get("emailId") == application.get("emailId")
        ),
        -1,
    )

    if index >= 0:
        apps[index] = {**apps[index], **application, "updated_at": now, "updatedAt": now}
        _write_all(apps)
        return apps[index]

    new_app = {
        "id": str(uuid.uuid4()),
        "review": {"reviewed": False, "reviewed_at": None, "reviewedAt": None},
        "created_at": now,
        "createdAt": now,
        **application,
        "updated_at": now,
        "updatedAt": now,
    }
    apps.append(new_app)
    _write_all(apps)
    return new_app


def assign_review(app_id: str, status: str) -> Optional[dict]:
    if status not in ALLOWED_REVIEW_STATUSES:
        raise ValueError("Invalid status")

    apps = _read_all()
    index = next((i for i, a in enumerate(apps) if a.get("id") == app_id), -1)
    if index < 0:
        return None

    now = datetime.now(timezone.utc).isoformat()
    apps[index] = {
        **apps[index],
        "status": status,
        "review": {"reviewed": True, "reviewed_at": now, "reviewedAt": now},
        "updated_at": now,
        "updatedAt": now,
    }
    _write_all(apps)
    return apps[index]


def archive(app_id: str) -> Optional[dict]:
    apps = _read_all()
    index = next((i for i, a in enumerate(apps) if a.get("id") == app_id), -1)
    if index < 0:
        return None

    now = datetime.now(timezone.utc).isoformat()
    apps[index] = {
        **apps[index],
        "status": "archived",
        "updated_at": now,
        "updatedAt": now,
    }
    _write_all(apps)
    return apps[index]


def get_stats() -> dict:
    apps = [a for a in _read_all() if a.get("status") != "archived"]
    counts: dict[str, int] = {}
    for app in apps:
        key = app.get("status", "unknown")
        counts[key] = counts.get(key, 0) + 1
    needs_review = sum(
        1
        for a in apps
        if a.get("status") == "needs_review" and (a.get("review") or {}).get("reviewed") is not True
    )
    return {"counts": counts, "needs_review": needs_review, "needsReview": needs_review, "total": len(apps)}
