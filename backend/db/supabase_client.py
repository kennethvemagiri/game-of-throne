import logging
import os

from supabase import create_client, Client

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    """Return a lazily-initialised Supabase client (singleton)."""
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set"
        )

    try:
        _client = create_client(url, key)
    except Exception:
        logger.exception("[supabase] Failed to create client")
        raise

    return _client


def get_sync_value(key: str) -> str | None:
    """Read a value from the sync_metadata table."""
    try:
        result = (
            get_client()
            .table("sync_metadata")
            .select("value")
            .eq("key", key)
            .execute()
        )
        return result.data[0]["value"] if result.data else None
    except Exception:
        logger.exception(f"[supabase] Failed to read sync_metadata key={key}")
        return None


def set_sync_value(key: str, value: str) -> None:
    """Write a value to the sync_metadata table (upsert)."""
    try:
        get_client().table("sync_metadata").upsert(
            {"key": key, "value": value}, on_conflict="key"
        ).execute()
    except Exception:
        logger.exception(f"[supabase] Failed to write sync_metadata key={key}")
