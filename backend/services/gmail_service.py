import base64
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.db import store
from backend.db.supabase_client import get_sync_value, set_sync_value

logger = logging.getLogger(__name__)

_LOCAL_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_TMP_DATA_DIR = Path("/tmp/got_data")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MAX_RESULTS = 100
MAX_RETRIES = 3


def _data_dir() -> Path:
    if os.environ.get("VERCEL") == "1":
        _TMP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        return _TMP_DATA_DIR
    return _LOCAL_DATA_DIR


def _token_path() -> Path:
    return _data_dir() / "token.json"


def _last_fetch_path() -> Path:
    return _data_dir() / "last_fetch.json"


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = StringIO()

    def handle_data(self, data: str):
        self._text.write(data)

    def get_text(self) -> str:
        return self._text.getvalue()


def _strip_html(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


def get_credentials() -> Optional[Credentials]:
    if not _token_path().exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(_token_path()), SCOPES)
    except Exception:
        logger.warning("[gmail] Failed to load token.json")
        return None

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleAuthRequest())
            _save_credentials(creds)
            return creds
        except Exception:
            logger.warning("[gmail] Token refresh failed — re-auth required")
            return None

    return None


def _save_credentials(creds: Credentials) -> None:
    path = _token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")


def save_credentials_from_flow(creds: Credentials) -> None:
    _save_credentials(creds)


def is_authenticated() -> bool:
    return get_credentials() is not None


def _build_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def get_last_fetch() -> Optional[str]:
    value = get_sync_value("last_fetch")
    if value:
        return value

    path = _last_fetch_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("last_fetch")
    except Exception:
        return None


def set_last_fetch(iso_timestamp: str) -> None:
    set_sync_value("last_fetch", iso_timestamp)


def _get_since_epoch() -> int:
    last = get_last_fetch()
    if last:
        try:
            dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except Exception:
            pass
    return int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())


def _get_existing_email_ids() -> set[str]:
    apps = store.get_all()
    ids: set[str] = set()
    for app in apps:
        eid = app.get("emailId") or app.get("email_id")
        if eid:
            ids.add(str(eid))
    return ids


def _extract_header(headers: list[dict], name: str) -> str:
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value", "")
    return ""


def _extract_body(payload: dict) -> str:
    """Extract plain text body, falling back to stripped HTML."""
    mime = payload.get("mimeType", "")

    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    if mime == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            raw = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            return _strip_html(raw)

    parts = payload.get("parts", [])
    plain = ""
    html = ""
    for part in parts:
        part_mime = part.get("mimeType", "")
        if part_mime == "text/plain" and not plain:
            data = part.get("body", {}).get("data", "")
            if data:
                plain = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        elif part_mime == "text/html" and not html:
            data = part.get("body", {}).get("data", "")
            if data:
                raw = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                html = _strip_html(raw)
        elif part.get("parts"):
            nested = _extract_body(part)
            if nested and not plain:
                plain = nested

    return plain or html


def _list_messages_with_retry(service, query: str) -> list[str]:
    """List message IDs with pagination and retry on transient errors."""
    message_ids: list[str] = []
    page_token: Optional[str] = None

    while True:
        for attempt in range(MAX_RETRIES):
            try:
                kwargs = {
                    "userId": "me",
                    "q": query,
                    "maxResults": MAX_RESULTS,
                }
                if page_token:
                    kwargs["pageToken"] = page_token

                result = service.users().messages().list(**kwargs).execute()
                messages = result.get("messages", [])
                message_ids.extend(m["id"] for m in messages)
                page_token = result.get("nextPageToken")
                break
            except HttpError as e:
                if e.resp.status in (429, 500, 503) and attempt < MAX_RETRIES - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"[gmail] Rate limited/server error, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

        if not page_token:
            break

    return message_ids


def start_watch(topic_name: str | None = None) -> dict:
    """Register Gmail push notifications via Pub/Sub. Must renew every 7 days."""
    if not topic_name:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        if not project_id:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT_ID not set")
        topic_name = f"projects/{project_id}/topics/gmail-notifications"

    creds = get_credentials()
    if not creds:
        raise RuntimeError("Gmail not authenticated")

    service = _build_service(creds)
    result = service.users().watch(
        userId="me",
        body={"topicName": topic_name, "labelIds": ["INBOX"]},
    ).execute()

    logger.info(f"[gmail] Watch registered, historyId={result.get('historyId')}, "
                f"expiration={result.get('expiration')}")
    return result


def fetch_new_emails() -> list[dict]:
    creds = get_credentials()
    if not creds:
        raise RuntimeError("Gmail not authenticated")

    service = _build_service(creds)
    since_epoch = _get_since_epoch()
    query = f"after:{since_epoch}"

    logger.info(f"[gmail] Fetching emails with query: {query}")
    message_ids = _list_messages_with_retry(service, query)

    existing_ids = _get_existing_email_ids()
    new_ids = [mid for mid in message_ids if mid not in existing_ids]
    logger.info(f"[gmail] Found {len(message_ids)} messages, {len(new_ids)} new")

    emails: list[dict] = []
    for msg_id in new_ids:
        try:
            msg = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()

            headers = msg.get("payload", {}).get("headers", [])
            subject = _extract_header(headers, "Subject")
            sender = _extract_header(headers, "From")
            date = _extract_header(headers, "Date")
            body = _extract_body(msg.get("payload", {}))

            emails.append({
                "message_id": msg_id,
                "subject": subject,
                "sender": sender,
                "body": body[:2000],
                "date": date,
            })
        except Exception:
            logger.exception(f"[gmail] Failed to fetch message {msg_id}, skipping")
            continue

    return emails
