import base64
import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from backend.db import store
from backend.services import gmail_service
from backend.services.classifier import classify_email
from backend.services.notifier import handle_classification

logger = logging.getLogger(__name__)
router = APIRouter()


async def run_fetch_and_classify() -> dict:
    """Fetch new Gmail messages, classify, store, and notify. Returns summary."""
    emails = gmail_service.fetch_new_emails()
    now = datetime.now(timezone.utc).isoformat()

    classified = 0
    skipped = 0
    errors = 0

    for email in emails:
        try:
            result = classify_email(
                subject=email["subject"],
                body=email["body"],
                sender=email["sender"],
            )

            if result["status"] == "skip":
                skipped += 1
                continue

            application = store.upsert({
                "emailId": email["message_id"],
                "company": result.get("company"),
                "role": result.get("role"),
                "status": result["status"],
                "suggestedStatus": result.get("suggested_status"),
                "confidence": result["confidence"],
                "subject": email["subject"],
                "snippet": email["body"][:200],
                "receivedAt": email.get("date") or now,
                "classifiedAt": now,
                "review": {
                    "reviewed": result["status"] != "needs_review",
                    "reviewedAt": None if result["status"] == "needs_review" else now,
                },
            })

            formatted = {
                "status": result["status"],
                "company": result.get("company"),
                "role": result.get("role"),
                "confidence": result["confidence"],
            }
            await handle_classification(formatted, application)
            classified += 1

        except Exception:
            logger.exception(f"[gmail] Failed to process email {email.get('message_id')}")
            errors += 1
            continue

    gmail_service.set_last_fetch(now)

    logger.info(
        f"[gmail] Fetch complete: {len(emails)} fetched, "
        f"{classified} classified, {skipped} skipped, {errors} errors"
    )
    return {
        "fetched": len(emails),
        "classified": classified,
        "skipped": skipped,
        "errors": errors,
    }


@router.post("/api/gmail/fetch")
async def gmail_fetch(request: Request):
    try:
        cron_secret = os.getenv("CRON_SECRET")
        on_vercel = os.getenv("VERCEL") == "1"

        if on_vercel and not cron_secret:
            raise HTTPException(status_code=500, detail="CRON_SECRET not configured")

        if cron_secret:
            auth = request.headers.get("authorization", "")
            if auth != f"Bearer {cron_secret}":
                raise HTTPException(status_code=401, detail="Unauthorized")
            if not gmail_service.is_authenticated():
                return {"skipped": True, "reason": "gmail_not_authenticated"}
            return await run_fetch_and_classify()

        if not gmail_service.is_authenticated():
            raise HTTPException(status_code=401, detail="Gmail not authenticated")

        return await run_fetch_and_classify()
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}


@router.post("/api/gmail/webhook")
async def gmail_webhook(request: Request):
    """Receives push notifications from Gmail via Google Cloud Pub/Sub."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON") from None

    message = body.get("message", {})
    if not message:
        return {"status": "no_message"}

    try:
        data = base64.b64decode(message.get("data", "")).decode("utf-8")
        payload = json.loads(data)
        history_id = payload.get("historyId")
    except Exception:
        logger.warning("[gmail-webhook] Failed to decode Pub/Sub message")
        return {"status": "decode_error"}

    logger.info(f"[gmail-webhook] Push received, historyId={history_id}")

    if not gmail_service.is_authenticated():
        logger.warning("[gmail-webhook] Gmail not authenticated, skipping")
        return {"status": "not_authenticated"}

    result = await run_fetch_and_classify()
    return {"status": "processed", **result}


@router.get("/api/gmail/status")
def gmail_status():
    return {
        "authenticated": gmail_service.is_authenticated(),
        "lastFetch": gmail_service.get_last_fetch(),
    }
