from datetime import datetime, timezone

from backend.services.gmail_service import _normalize_received_at


def test_normalize_received_at_prefers_internal_date():
    msg = {"internalDate": "1715989200000"}
    value = _normalize_received_at(msg, "Fri, 17 May 2024 10:59:00 -0400")
    expected = datetime.fromtimestamp(1715989200, tz=timezone.utc).isoformat()
    assert value == expected


def test_normalize_received_at_uses_header_when_internal_date_invalid():
    msg = {"internalDate": "not-a-number"}
    value = _normalize_received_at(msg, "Fri, 17 May 2024 10:59:00 -0400")
    assert value == "2024-05-17T14:59:00+00:00"


def test_normalize_received_at_falls_back_to_now_iso():
    value = _normalize_received_at({}, "")
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo == timezone.utc
