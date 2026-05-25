from backend.services.classifier import classify_email


def test_interview_high():
    result = classify_email(
        "Interview invite — next stage",
        "invite you for an interview schedule a call meet the team",
        "HR <hr@fanduel.com>",
    )
    assert result["status"] == "interview"
    assert result["confidence"] == "high"


def test_skip_newsletter():
    result = classify_email(
        "50% off",
        "Unsubscribe from our newsletter",
        "news@marketing.com",
    )
    assert result["status"] == "skip"


def test_medium_goes_to_review():
    result = classify_email(
        "Application received",
        "Thank you for applying.",
        "careers@acme.com",
    )
    assert result["status"] == "needs_review"
    assert result["confidence"] == "medium"
    assert result.get("suggested_status") == "acknowledged"
