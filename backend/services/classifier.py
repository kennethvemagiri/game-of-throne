import re
from typing import Literal, Optional

KEYWORD_BANKS = {
    "interview": [
        "interview",
        "invite you",
        "schedule a call",
        "meet the team",
        "next stage",
        "shortlisted",
    ],
    "rejected": [
        "unfortunately",
        "regret to inform",
        "not progressing",
        "other candidates",
        "not successful",
        "wish you well",
    ],
    "acknowledged": [
        "received your application",
        "thank you for applying",
        "application has been submitted",
        "confirmation",
    ],
    "assessment": [
        "coding challenge",
        "technical test",
        "assessment",
        "complete this task",
        "take-home",
    ],
    "recruiter_inbound": [
        "came across your profile",
        "reaching out",
        "opportunity",
        "would you be interested",
    ],
}

STATUS_PRIORITY = [
    "interview",
    "assessment",
    "rejected",
    "recruiter_inbound",
    "acknowledged",
]

GENERIC_EMAIL_DOMAINS = {
    "gmail", "googlemail", "yahoo", "hotmail", "outlook",
    "live", "icloud", "me", "aol", "protonmail", "mail",
}

JOB_SENDER_HINTS = [
    "hr@", "careers@", "jobs@", "recruiting@", "talent@", "hiring@",
    "noreply@", "greenhouse.io", "lever.co", "workday", "icims",
    "smartrecruiters", "ashbyhq",
]

JOB_CONTENT_HINTS = [
    "application", "applied", "position", "role", "candidate",
    "interview", "hiring", "recruiter", "opportunity",
]

SKIP_HINTS = [
    "unsubscribe", "newsletter", "% off", "promo code", "webinar", "black friday",
]

Confidence = Literal["high", "medium", "low"]


def classify_email(subject: str = "", body: str = "", sender: str = "") -> dict:
    combined = f"{subject}\n{body}".strip()
    combined_lower = combined.lower()
    sender_lower = sender.lower()

    if _should_skip(combined_lower, sender_lower):
        return {
            "status": "skip",
            "company": _extract_company(sender, subject),
            "role": _extract_role(subject, body),
            "confidence": "high",
        }

    scores = _score_statuses(combined_lower)
    best = _pick_best_status(scores)
    company = _extract_company(sender, subject)
    role = _extract_role(subject, body)

    if not best or best["match_count"] == 0:
        if _is_job_related(sender_lower, combined_lower):
            return {
                "status": "needs_review",
                "company": company,
                "role": role,
                "confidence": "low",
            }
        return {
            "status": "skip",
            "company": company,
            "role": role,
            "confidence": "high",
        }

    confidence = _match_count_to_confidence(best["match_count"])

    if confidence in ("low", "medium"):
        return {
            "status": "needs_review",
            "company": company,
            "role": role,
            "confidence": confidence,
            "suggested_status": best["status"],
            "matched_keywords": best["matched_keywords"],
        }

    return {
        "status": best["status"],
        "company": company,
        "role": role,
        "confidence": confidence,
        "matched_keywords": best["matched_keywords"],
    }


def _should_skip(text_lower: str, sender_lower: str) -> bool:
    if any(hint in text_lower for hint in SKIP_HINTS):
        return True
    has_job = any(h in text_lower for h in JOB_CONTENT_HINTS) or any(
        h in sender_lower for h in JOB_SENDER_HINTS
    )
    return not has_job


def _score_statuses(text_lower: str) -> list[dict]:
    results = []
    for status, keywords in KEYWORD_BANKS.items():
        matched = [kw for kw in keywords if kw.lower() in text_lower]
        results.append({
            "status": status,
            "match_count": len(matched),
            "matched_keywords": matched,
        })
    return results


def _pick_best_status(scores: list[dict]) -> Optional[dict]:
    with_matches = [s for s in scores if s["match_count"] > 0]
    if not with_matches:
        return None

    def sort_key(entry: dict):
        return (
            -entry["match_count"],
            STATUS_PRIORITY.index(entry["status"]),
        )

    return sorted(with_matches, key=sort_key)[0]


def _match_count_to_confidence(match_count: int) -> Confidence:
    if match_count >= 3:
        return "high"
    if match_count >= 1:
        return "medium"
    return "low"


def _is_job_related(sender_lower: str, text_lower: str) -> bool:
    return any(h in sender_lower for h in JOB_SENDER_HINTS) or any(
        h in text_lower for h in JOB_CONTENT_HINTS
    )


def _extract_company(sender: str, subject: str) -> Optional[str]:
    from_domain = _company_from_sender(sender)
    if from_domain:
        return from_domain
    return _company_from_subject(subject)


def _company_from_sender(sender: str) -> Optional[str]:
    bracketed = re.search(r"<([^>]+)>", sender)
    email = bracketed.group(1) if bracketed else None
    if not email:
        match = re.search(r"[\w.+-]+@[\w.-]+\.\w{2,}", sender)
        email = match.group(0) if match else None
    if not email or "@" not in email:
        return None

    domain = email.split("@")[1].lower()
    parts = domain.split(".")
    root = (
        parts[-2]
        if len(parts) >= 2 and len(parts[-1]) == 2 and len(parts) > 2
        else parts[0]
    )
    if not root or root in GENERIC_EMAIL_DOMAINS:
        return None
    return _format_company_name(root)


def _company_from_subject(subject: str) -> Optional[str]:
    patterns = [
        r"(?:at|@|to|from)\s+([A-Z][\w&.-]*(?:\s+[A-Z][\w&.-]*)*)",
        r"application\s+(?:to|at|for)\s+([A-Z][\w&.-]*(?:\s+[A-Z][\w&.-]*)*)",
        r"(?:position|role)\s+(?:at|with)\s+([A-Z][\w&.-]*(?:\s+[A-Z][\w&.-]*)*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _format_company_name(slug: str) -> str:
    parts = [p for p in re.split(r"[-_]", slug) if p]
    formatted = []
    for part in parts:
        if len(part) <= 3:
            formatted.append(part.upper())
        else:
            formatted.append(part[0].upper() + part[1:].lower())
    return " ".join(formatted)


def _extract_role(subject: str, body: str) -> Optional[str]:
    text = f"{subject}\n{body}"
    patterns = [
        r"for the (.+?) position",
        r"for (?:the )?(.+?) role",
        r"(?:position|role):\s*(.+?)(?:\.|$|\n)",
        r"RE:\s*(.+?)\s+application",
        r"application for (?:the )?(.+?)(?: position| role| at|\.|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            if 2 <= len(role) <= 80:
                return role
    return None
