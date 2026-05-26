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
    assert result["status"] == "acknowledged"
    assert result["confidence"] == "medium"


def test_auto_assign_assessment_with_multiple_signals():
    result = classify_email(
        "Online assessment for next stage",
        "Please complete this coding challenge before Friday.",
        "jobs@acme.com",
    )
    assert result["status"] == "assessment"
    assert result["confidence"] in ("medium", "high")


def test_ambiguous_status_goes_to_review_with_suggestion():
    result = classify_email(
        "Interview and assessment details",
        "Please prepare for interview and assessment this week.",
        "recruiting@acme.com",
    )
    assert result["status"] == "needs_review"
    assert result["suggested_status"] in ("interview", "assessment")


def test_strong_rejection_phrase_auto_assigns_rejected():
    result = classify_email(
        "Update on your application",
        "We regret to inform you that we decided to move forward with other candidates.",
        "careers@acme.com",
    )
    assert result["status"] == "rejected"
    assert result["confidence"] in ("medium", "high")


def test_env_threshold_can_force_review(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_AUTO_ASSIGN_MIN_SCORE", "10")
    result = classify_email(
        "Online assessment for next stage",
        "Please complete this coding challenge before Friday.",
        "jobs@acme.com",
    )
    assert result["status"] == "needs_review"
    assert result["suggested_status"] == "assessment"
