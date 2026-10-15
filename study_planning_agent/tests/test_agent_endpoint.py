from fastapi.testclient import TestClient

from api import agent_routes
from main import app
from models.recommendation import Recommendation

client = TestClient(app)

def make_orchestrator_result(recommendation, fallback_used=False, error=None):
    """Create the response structure returned by the orchestrator."""
    return {
        "structured_response": recommendation,
        "conversation_history": [],
        "iterations": 2,
        "fallback_used": fallback_used,
        "error": error,
    }

def test_study_plan_endpoint(monkeypatch):
    def fake_run(available_hours):
        assert available_hours == 5

        recommendation = Recommendation(
            assessment_name="Web Development Assignment",
            priority="Medium",
            reason=(
                "It has the earliest deadline and can be worked on "
                "within the available study time."
            ),
            suggested_action=(
                "Spend five hours making progress on the assignment."
            ),
        )

        return make_orchestrator_result(recommendation)

    monkeypatch.setattr(
        agent_routes.orchestrator,
        "run",
        fake_run,
    )

    response = client.post(
        "/api/agent/study-plan",
        json={"available_hours": 5},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["assessment_name"] == "Web Development Assignment"
    assert data["priority"] == "Medium"
    assert "earliest deadline" in data["reason"]
    assert "five hours" in data["suggested_action"]

def test_study_plan_endpoint_rejects_invalid_hours():
    response = client.post(
        "/api/agent/study-plan",
        json={"available_hours": 0},
    )

    assert response.status_code == 422

def test_study_plan_endpoint_handles_agent_failure(monkeypatch):
    def fake_run(available_hours):
        fallback = Recommendation(
            assessment_name="No recommendation available",
            priority="Unknown",
            reason=(
                "The multi-agent system could not complete the study plan."
            ),
            suggested_action="Review your stored assessments manually.",
        )

        return make_orchestrator_result(
            fallback,
            fallback_used=True,
            error="Simulated agent failure",
        )

    monkeypatch.setattr(
        agent_routes.orchestrator,
        "run",
        fake_run,
    )

    response = client.post(
        "/api/agent/study-plan",
        json={"available_hours": 5},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["assessment_name"] == "No recommendation available"
    assert data["priority"] == "Unknown"
    assert "could not complete" in data["reason"]
    assert "manually" in data["suggested_action"]