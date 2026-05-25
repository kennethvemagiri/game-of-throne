from fastapi import APIRouter, HTTPException

from backend.db import suggested_store
from backend.models.schemas import SuggestedJobSyncBody

router = APIRouter()


@router.get("/api/suggested-jobs")
def list_suggested_jobs(status: str | None = "pending"):
    if status == "all":
        return suggested_store.get_all()
    return suggested_store.get_all(status=status)


@router.patch("/api/suggested-jobs/{job_id}/reject")
def reject_suggested_job(job_id: str):
    updated = suggested_store.reject(job_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.patch("/api/suggested-jobs/{job_id}/viewed")
def mark_suggested_job_viewed(job_id: str):
    updated = suggested_store.mark_viewed(job_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/api/suggested-jobs/sync-demo")
def sync_suggested_job_demo(body: SuggestedJobSyncBody):
    job = suggested_store.upsert({
        "source": body.source,
        "company": body.company,
        "role": body.role,
        "url": body.url,
        "snippet": body.snippet,
        "status": "pending",
    })
    return {"job": job}
