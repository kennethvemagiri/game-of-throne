import os

from fastapi import APIRouter, HTTPException, Request

from backend.db import store
from backend.services.notifier import run_scheduled_digest

router = APIRouter()


@router.get("/api/cron/digest")
async def cron_digest(request: Request):
    cron_secret = os.getenv("CRON_SECRET")
    on_vercel = os.getenv("VERCEL") == "1"

    if on_vercel and not cron_secret:
        raise HTTPException(status_code=500, detail="CRON_SECRET not configured")

    if cron_secret:
        auth = request.headers.get("authorization", "")
        if auth != f"Bearer {cron_secret}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    if os.getenv("DIGEST_ENABLED", "true").lower() == "false":
        return {"skipped": True, "reason": "digest disabled"}

    await run_scheduled_digest(store.get_all)
    return {"ok": True}
