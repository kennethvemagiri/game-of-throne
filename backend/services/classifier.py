import os
import re
from typing import Literal, Optional

KEYWORD_BANKS = {
    "interview": [
        "interview",
        "interview invite",
        "invite you to interview",
        "final interview",
        "phone screen",
        "screening call",
        "hiring manager interview",
        "meet the team",
        "next stage",
        "next round",
        "shortlisted",
        "availability for interview",
        "book a time",
        "schedule a time",
        "calendly",
    ],
    "rejected": [
        "regret to inform",
        "unfortunately",
        "not moving forward",
        "not progressing",
        "not selected",
        "not successful",
        "decided to move forward with other candidates",
        "position has been filled",
        "we will not be proceeding",
        "thank you for your interest",
        "wish you the best",
    ],
    "acknowledged": [
        "application received",
        "received your application",
        "thank you for applying",
        "we have received",
        "application has been submitted",
        "application confirmation",
        "we'll review your application",
        "our team will review",
        "application under review",
    ],
    "assessment": [
        "assessment",
        "online assessment",
        "technical assessment",
        "coding challenge",
        "code challenge",
        "take-home",
        "take home",
        "hackerrank",
        "codility",
        "testgorilla",
        "criteria test",
        "complete this task",
        "submit your solution",
        "deadline to complete",
    ],
    "recruiter_inbound": [
        "came across your profile",
        "reaching out",
        "would you be interested",
        "interesting opportunity",
        "open role",
        "hiring for",
        "looking for a",
        "your background fits",
        "connect regarding",
        "quick chat",
        "intro call",
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
    "application", "applied", "position", "role", "candidate", "job opening",
    "interview", "hiring", "recruiter", "talent acquisition", "assessment",
]

SKIP_HINTS = [
    "unsubscribe", "newsletter", "% off", "promo code", "webinar",
    "black friday", "cyber monday", "order shipped", "invoice", "receipt",
    "security alert", "password reset", "verify your email", "marketing preferences",
]

STRONG_PHRASES = {
    "rejected": [
        "regret to inform",
        "move forward with other candidates",
        "not moving forward",
    ],
    "interview": [
        "invite you to interview",
        "schedule an interview",
    ],
    "assessment": [
        "complete this coding challenge",
        "online assessment",
    ],
}

DEFAULT_SUBJECT_HIT_WEIGHT = 2
DEFAULT_BODY_HIT_WEIGHT = 1
DEFAULT_STRONG_PHRASE_WEIGHT = 2

DEFAULT_AUTO_ASSIGN_MIN_SCORE = 3
DEFAULT_AUTO_ASSIGN_MIN_MARGIN = 1

Confidence = Literal["high", "medium", "low"]


def classify_email(subject: str = "", body: str = "", sender: str = "") -> dict:
    subject_lower = subject.lower()
    body_lower = body.lower()
    combined_lower = f"{subject}\n{body}".strip().lower()
    sender_lower = sender.lower()
    company = _extract_company(sender, subject)
    role = _extract_role(subject, body)

    if _should_skip(combined_lower, sender_lower):
        return {
            "status": "skip",
            "company": company,
            "role": role,
            "confidence": "high",
        }

    ranked = _rank_statuses(_score_statuses(subject_lower, body_lower))

    if not ranked:
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

    top = ranked[0]
    confidence = _score_to_confidence(top["score"])

    if _should_auto_assign(ranked):
        return {
            "status": top["status"],
            "company": company,
            "role": role,
            "confidence": confidence,
            "matched_keywords": top["matched_keywords"],
        }

    return {
        "status": "needs_review",
        "company": company,
        "role": role,
        "confidence": confidence,
        "suggested_status": top["status"],
        "matched_keywords": top["matched_keywords"],
    }


def _should_skip(text_lower: str, sender_lower: str) -> bool:
    if any(hint in text_lower for hint in SKIP_HINTS):
        return True
    has_job = any(h in text_lower for h in JOB_CONTENT_HINTS) or any(
        h in sender_lower for h in JOB_SENDER_HINTS
    )
    return not has_job


def _score_statuses(subject_lower: str, body_lower: str) -> list[dict]:
    subject_hit_weight = _env_int("CLASSIFIER_SUBJECT_HIT_WEIGHT", DEFAULT_SUBJECT_HIT_WEIGHT, min_value=0)
    body_hit_weight = _env_int("CLASSIFIER_BODY_HIT_WEIGHT", DEFAULT_BODY_HIT_WEIGHT, min_value=0)
    strong_phrase_weight = _env_int("CLASSIFIER_STRONG_PHRASE_WEIGHT", DEFAULT_STRONG_PHRASE_WEIGHT, min_value=0)
    combined_lower = f"{subject_lower}\n{body_lower}"
    results = []
    for status, keywords in KEYWORD_BANKS.items():
        matched_keywords = []
        score = 0

        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in subject_lower:
                score += subject_hit_weight
                matched_keywords.append(keyword)
                continue
            if keyword_lower in body_lower:
                score += body_hit_weight
                matched_keywords.append(keyword)

        strong_matched = []
        for phrase in STRONG_PHRASES.get(status, []):
            phrase_lower = phrase.lower()
            if phrase_lower in combined_lower:
                score += strong_phrase_weight
                strong_matched.append(f"strong:{phrase}")

        results.append({
            "status": status,
            "score": score,
            "match_count": len(matched_keywords),
            "matched_keywords": matched_keywords + strong_matched,
        })
    return results


def _rank_statuses(scores: list[dict]) -> list[dict]:
    with_score = [s for s in scores if s["score"] > 0]

    def sort_key(entry: dict):
        return (
            -entry["score"],
            -entry["match_count"],
            STATUS_PRIORITY.index(entry["status"]),
        )

    return sorted(with_score, key=sort_key)


def _should_auto_assign(ranked: list[dict]) -> bool:
    min_score = _env_int("CLASSIFIER_AUTO_ASSIGN_MIN_SCORE", DEFAULT_AUTO_ASSIGN_MIN_SCORE, min_value=0)
    min_margin = _env_int("CLASSIFIER_AUTO_ASSIGN_MIN_MARGIN", DEFAULT_AUTO_ASSIGN_MIN_MARGIN, min_value=0)
    top = ranked[0]
    second_score = ranked[1]["score"] if len(ranked) > 1 else 0
    margin = top["score"] - second_score
    return top["score"] >= min_score and margin >= min_margin


def _score_to_confidence(score: int) -> Confidence:
    high_threshold = _env_int("CLASSIFIER_CONFIDENCE_HIGH_SCORE", 5, min_value=1)
    medium_threshold = _env_int("CLASSIFIER_CONFIDENCE_MEDIUM_SCORE", 2, min_value=0)
    if high_threshold < medium_threshold:
        high_threshold = medium_threshold

    if score >= high_threshold:
        return "high"
    if score >= medium_threshold:
        return "medium"
    return "low"


def _env_int(name: str, default: int, *, min_value: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if min_value is not None and value < min_value:
        return min_value
    return value


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
