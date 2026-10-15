import logging
import pytest

from agents import reviewer_agent as reviewer_module
from models.agent_message import AgentMessage
from models.review_result import ReviewResult

def make_review_message(
    receiver="reviewer",
    sender="planner",
    intent="review_recommendation",
    assessment_name="Web Development Assignment",
    priority="Medium"
):
    return AgentMessage(
        sender=sender,
        receiver=receiver,
        intent=intent,
        content={
            "available_hours": 2,
            "recommendation": {
                "assessment_name": assessment_name,
                "priority": priority,
                "reason": "It has the earliest due date.",
                "suggested_action": "Spend two hours making progress."
            }
        }
    )

class FakeReviewer:
    def __init__(self, result):
        self.result = result

    def invoke(self, request):
        return {"structured_response": self.result}

def make_approved_review():
    return ReviewResult(
        approved=True,
        assessment_exists=True,
        priority_matches=True,
        reasoning_is_consistent=True,
        feedback="The recommendation is reasonable.",
        suggested_revision="No changes required."
    )

def test_reviewer_approves_valid_recommendation(
    monkeypatch, caplog
):
    monkeypatch.setattr(
        reviewer_module,
        "reviewer_llm_agent",
        FakeReviewer(make_approved_review())
    )

    with caplog.at_level(logging.INFO):
        result = reviewer_module.run_reviewer_agent(
            make_review_message()
        )

    assert result.sender == "reviewer"
    assert result.receiver == "orchestrator"
    assert result.intent == "review_result"
    assert result.content["review"]["approved"] is True
    assert result.content["review"]["assessment_exists"] is True
    assert result.content["review"]["priority_matches"] is True

    assert "Reviewer received message" in caplog.text
    assert "Reviewer sent message" in caplog.text

def test_reviewer_rejects_unknown_assessment(monkeypatch):
    monkeypatch.setattr(
        reviewer_module,
        "reviewer_llm_agent",
        FakeReviewer(make_approved_review())
    )

    result = reviewer_module.run_reviewer_agent(
        make_review_message(
            assessment_name="Nonexistent Assessment"
        )
    )

    assert result.content["review"]["assessment_exists"] is False
    assert result.content["review"]["approved"] is False
    assert result.constraints["approved"] is False

def test_reviewer_rejects_priority_mismatch(monkeypatch):
    monkeypatch.setattr(
        reviewer_module,
        "reviewer_llm_agent",
        FakeReviewer(make_approved_review())
    )

    result = reviewer_module.run_reviewer_agent(
        make_review_message(priority="High")
    )

    assert result.content["review"]["priority_matches"] is False
    assert result.content["review"]["approved"] is False

def test_reviewer_rejects_wrong_receiver():
    with pytest.raises(ValueError, match="cannot receive messages"):
        reviewer_module.run_reviewer_agent(
            make_review_message(receiver="unknown_agent")
        )

def test_reviewer_rejects_wrong_sender():
    with pytest.raises(ValueError, match="cannot accept messages"):
        reviewer_module.run_reviewer_agent(
            make_review_message(sender="unknown_agent")
        )

def test_reviewer_rejects_wrong_intent():
    with pytest.raises(ValueError, match="cannot handle intent"):
        reviewer_module.run_reviewer_agent(
            make_review_message(intent="create_study_plan")
        )