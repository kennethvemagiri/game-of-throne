import os
from datetime import datetime, timezone
from typing import Any

import httpx

INSTANT_STATUSES = {"interview", "assessment", "recruiter_inbound"}

STATUS_META = {
    "interview": {"title": "🔥 Interview invite!", "color": 0x10B981},
    "assessment": {"title": "📝 Assessment received", "color": 0xF59E0B},
    "recruiter_inbound": {"title": "👋 Recruiter inbound", "color": 0x3B82F6},
    "needs_review": {"title": "📋 Needs review — daily digest", "color": 0x6B7280},
}

_notified_ids: set[str] = set()


def _webhook_url() -> str:
    return os.getenv("DISCORD_WEBHOOK_URL", "")


async def notify_instant(application: dict) -> dict:
    status = application.get("status")
    if status not in INSTANT_STATUSES:
        return {"sent": False, "reason": "status_not_instant"}

    dedupe_key = application.get("email_id") or application.get("emailId") or application.get("id")
    if dedupe_key and dedupe_key in _notified_ids:
        return {"sent": False, "reason": "already_notified"}

    meta = STATUS_META[status]
    embed = _build_embed(
        title=meta["title"],
        color=meta["color"],
        company=application.get("company") or "Unknown",
        role=application.get("role") or "—",
        status=status,
        snippet=application.get("snippet") or application.get("subject") or "—",
    )

    result = await _post_webhook({"embeds": [embed]})
    if result.get("ok") and dedupe_key:
        _notified_ids.add(str(dedupe_key))
    return result


async def send_daily_digest(items: list[dict]) -> dict:
    if not items:
        return {"sent": False, "reason": "empty_digest"}

    lines = []
    for index, item in enumerate(items[:15], start=1):
        company = item.get("company") or "Unknown company"
        role = item.get("role")
        role_part = f" — {role}" if role else ""
        suggested = item.get("suggested_status") or item.get("suggestedStatus")
        hint = f" (suggested: {suggested})" if suggested else ""
        snippet = _truncate(item.get("snippet") or item.get("subject") or "No preview", 80)
        lines.append(f"**{index}.** {company}{role_part}{hint}\n> {snippet}")

    if len(items) > 15:
        lines.append(f"\n_…and {len(items) - 15} more_")

    embed = {
        "title": STATUS_META["needs_review"]["title"],
        "description": "\n\n".join(lines),
        "color": STATUS_META["needs_review"]["color"],
        "footer": {"text": f"{len(items)} item(s) need review"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return await _post_webhook({"embeds": [embed]})


async def handle_classification(classification: dict, application: dict) -> dict:
    payload = {
        **application,
        "status": classification.get("status"),
        "company": application.get("company") or classification.get("company"),
        "role": application.get("role") or classification.get("role"),
    }
    if payload.get("status") in INSTANT_STATUSES:
        return await notify_instant(payload)
    return {"sent": False, "reason": "silent_status"}


def filter_today_needs_review(applications: list[dict]) -> list[dict]:
    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    result = []
    for app in applications:
        if app.get("status") != "needs_review":
            continue
        review = app.get("review") or {}
        if review.get("reviewed") is True:
            continue
        classified_at = (
            app.get("classified_at")
            or app.get("classifiedAt")
            or app.get("received_at")
            or app.get("receivedAt")
            or app.get("created_at")
            or app.get("createdAt")
        )
        if not classified_at:
            result.append(app)
            continue
        if datetime.fromisoformat(classified_at.replace("Z", "+00:00")).replace(tzinfo=None) >= start_of_day:
            result.append(app)
    return result


async def run_scheduled_digest(get_applications) -> None:
    if os.getenv("DIGEST_ENABLED", "true").lower() == "false":
        return
    items = filter_today_needs_review(get_applications())
    await send_daily_digest(items)


def _build_embed(*, title: str, color: int, company: str, role: str, status: str, snippet: str) -> dict:
    return {
        "title": title,
        "color": color,
        "fields": [
            {"name": "Company", "value": str(company), "inline": True},
            {"name": "Role", "value": str(role), "inline": True},
            {"name": "Status", "value": str(status), "inline": True},
            {"name": "Snippet", "value": _truncate(snippet, 300)},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _post_webhook(body: dict) -> dict:
    url = _webhook_url()
    if not url:
        print("[notifier] DISCORD_WEBHOOK_URL not set — skipping")
        return {"sent": False, "reason": "missing_webhook"}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body)
        if response.status_code >= 400:
            raise RuntimeError(f"Discord webhook failed ({response.status_code}): {response.text}")
    return {"sent": True, "ok": True}


def _truncate(value: Any, max_len: int) -> str:
    text = str(value)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
