import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.db import store
from backend.models.schemas import ClassifyBody, ReviewBody, SyncDemoBody
from backend.services.classifier import classify_email
from backend.services.notifier import handle_classification

router = APIRouter()


def _format_classification(result: dict) -> dict:
    out = {
        "status": result["status"],
        "company": result.get("company"),
        "role": result.get("role"),
        "confidence": result["confidence"],
    }
    if result.get("suggested_status"):
        out["suggestedStatus"] = result["suggested_status"]
    if result.get("matched_keywords"):
        out["matchedKeywords"] = result["matched_keywords"]
    return out


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/api/applications")
def list_applications(status: str | None = None, needsReview: str | None = None):
    return store.get_all(status=status, needs_review=needsReview == "true")


@router.get("/api/stats")
def stats():
    return store.get_stats()


@router.patch("/api/applications/{app_id}/review")
async def review_application(app_id: str, body: ReviewBody):
    try:
        updated = store.assign_review(app_id, body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status") from None
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.patch("/api/applications/{app_id}/archive")
def archive_application(app_id: str):
    updated = store.archive(app_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/api/classify-demo")
def classify_demo(body: ClassifyBody):
    if os.getenv("VERCEL") == "1":
        raise HTTPException(status_code=403, detail="Demo endpoints disabled in production")
    result = classify_email(body.subject, body.body, body.sender)
    return _format_classification(result)


@router.post("/api/sync-demo")
async def sync_demo(body: SyncDemoBody):
    if os.getenv("VERCEL") == "1":
        raise HTTPException(status_code=403, detail="Demo endpoints disabled in production")
    result = classify_email(body.subject, body.body, body.sender)
    formatted = _format_classification(result)

    if result["status"] == "skip":
        return {"skipped": True, "result": formatted}

    now = _now_iso()
    application = store.upsert({
        "emailId": body.email_id or f"demo-{int(time.time() * 1000)}",
        "company": result.get("company"),
        "role": result.get("role"),
        "status": result["status"],
        "suggestedStatus": result.get("suggested_status"),
        "confidence": result["confidence"],
        "subject": body.subject,
        "snippet": (body.body or "")[:200],
        "receivedAt": now,
        "classifiedAt": now,
        "review": {
            "reviewed": result["status"] != "needs_review",
            "reviewedAt": None if result["status"] == "needs_review" else now,
        },
    })

    if result["status"] != "needs_review":
        await handle_classification(formatted, application)

    return {"application": application, "result": formatted}
