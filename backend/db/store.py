import logging
from datetime import datetime, timezone
from typing import Optional

from backend.db.supabase_client import get_client

logger = logging.getLogger(__name__)

ALLOWED_REVIEW_STATUSES = {
    "interview",
    "assessment",
    "recruiter_inbound",
    "acknowledged",
    "rejected",
    "applied",
}

_DB_COLUMNS = {
    "id", "email_id", "company", "role", "status", "suggested_status",
    "confidence", "subject", "snippet", "received_at", "classified_at",
    "reviewed", "reviewed_at", "created_at", "updated_at",
}

_CAMEL_TO_SNAKE = {
    "emailId": "email_id",
    "suggestedStatus": "suggested_status",
    "receivedAt": "received_at",
    "classifiedAt": "classified_at",
    "createdAt": "created_at",
    "updatedAt": "updated_at",
    "reviewedAt": "reviewed_at",
}


def _to_db_row(data: dict) -> dict:
    """Convert an application dict (camelCase) to a flat DB row (snake_case)."""
    row: dict = {}
    review = data.get("review")

    for key, value in data.items():
        if key == "review":
            continue
        db_key = _CAMEL_TO_SNAKE.get(key, key)
        if db_key in _DB_COLUMNS:
            row[db_key] = value

    if isinstance(review, dict):
        if "reviewed" in review:
            row["reviewed"] = review["reviewed"]
        rev_at = review.get("reviewedAt") or review.get("reviewed_at")
        if rev_at is not None:
            row["reviewed_at"] = rev_at

    return row


def _to_app_dict(row: dict) -> dict:
    """Convert a DB row to the dict shape the rest of the app expects."""
    app = dict(row)

    app.setdefault("emailId", app.get("email_id"))
    app.setdefault("suggestedStatus", app.get("suggested_status"))
    app.setdefault("receivedAt", app.get("received_at"))
    app.setdefault("classifiedAt", app.get("classified_at"))
    app.setdefault("createdAt", app.get("created_at"))
    app.setdefault("updatedAt", app.get("updated_at"))

    app["review"] = {
        "reviewed": app.get("reviewed", False),
        "reviewed_at": app.get("reviewed_at"),
        "reviewedAt": app.get("reviewed_at"),
    }

    return app


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_all(*, status: Optional[str] = None, needs_review: bool = False) -> list[dict]:
    try:
        query = get_client().table("applications").select("*").neq("status", "archived")

        if status:
            query = query.eq("status", status)
        if needs_review:
            query = query.eq("status", "needs_review").eq("reviewed", False)

        result = query.order("received_at", desc=True).execute()
        return [_to_app_dict(row) for row in result.data]
    except Exception:
        logger.exception("[store] Failed to fetch applications")
        raise


def get_by_id(app_id: str) -> Optional[dict]:
    try:
        result = get_client().table("applications").select("*").eq("id", app_id).execute()
        return _to_app_dict(result.data[0]) if result.data else None
    except Exception:
        logger.exception(f"[store] Failed to fetch application {app_id}")
        raise


def upsert(application: dict) -> dict:
    try:
        row = _to_db_row(application)
        row["updated_at"] = _now_iso()
        row.setdefault("created_at", _now_iso())

        result = (
            get_client()
            .table("applications")
            .upsert(row, on_conflict="email_id")
            .execute()
        )
        return _to_app_dict(result.data[0])
    except Exception:
        logger.exception("[store] Failed to upsert application")
        raise


def assign_review(app_id: str, status: str) -> Optional[dict]:
    if status not in ALLOWED_REVIEW_STATUSES:
        raise ValueError("Invalid status")

    try:
        now = _now_iso()
        result = (
            get_client()
            .table("applications")
            .update({
                "status": status,
                "reviewed": True,
                "reviewed_at": now,
                "updated_at": now,
            })
            .eq("id", app_id)
            .execute()
        )
        return _to_app_dict(result.data[0]) if result.data else None
    except Exception:
        logger.exception(f"[store] Failed to assign review for {app_id}")
        raise


def archive(app_id: str) -> Optional[dict]:
    try:
        now = _now_iso()
        result = (
            get_client()
            .table("applications")
            .update({"status": "archived", "updated_at": now})
            .eq("id", app_id)
            .execute()
        )
        return _to_app_dict(result.data[0]) if result.data else None
    except Exception:
        logger.exception(f"[store] Failed to archive application {app_id}")
        raise


def get_stats() -> dict:
    try:
        result = (
            get_client()
            .table("applications")
            .select("status,reviewed")
            .neq("status", "archived")
            .execute()
        )
    except Exception:
        logger.exception("[store] Failed to fetch stats")
        raise

    counts: dict[str, int] = {}
    needs_review_count = 0

    for row in result.data:
        key = row.get("status", "unknown")
        counts[key] = counts.get(key, 0) + 1
        if key == "needs_review" and row.get("reviewed") is not True:
            needs_review_count += 1

    return {
        "counts": counts,
        "needs_review": needs_review_count,
        "needsReview": needs_review_count,
        "total": len(result.data),
    }
