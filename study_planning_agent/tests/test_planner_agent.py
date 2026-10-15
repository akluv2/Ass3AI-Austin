import logging

import pytest
from pydantic import ValidationError

from agents import planner_agent as planner_module
from models.agent_message import AgentMessage
from models.recommendation import Recommendation

def make_planner_message(
    receiver="planner",
    intent="create_study_plan",
    available_hours=2
):
    return AgentMessage(
        sender="orchestrator",
        receiver=receiver,
        intent=intent,
        content={"available_hours": available_hours}
    )

def test_planner_sends_recommendation_to_reviewer(monkeypatch, caplog):
    class FakeAgent:
        def invoke(self, request):
            assert "2.0 hours available to study" in (
                request["messages"][0]["content"]
            )

            return {
                "structured_response": Recommendation(
                    assessment_name="Web Development Assignment",
                    priority="Medium",
                    reason="It has the earliest due date.",
                    suggested_action="Spend two hours making progress."
                )
            }

    monkeypatch.setattr(
        planner_module,
        "planner_llm_agent",
        FakeAgent()
    )

    with caplog.at_level(logging.INFO):
        result = planner_module.run_planner_agent(
            make_planner_message()
        )

    assert result.sender == "planner"
    assert result.receiver == "reviewer"
    assert result.intent == "review_recommendation"
    assert result.content["available_hours"] == 2
    assert result.content["recommendation"]["assessment_name"] == (
        "Web Development Assignment"
    )

    assert "Planner received message" in caplog.text
    assert "Planner sent message" in caplog.text

def test_planner_rejects_wrong_receiver():
    message = make_planner_message(receiver="unknown_agent")

    with pytest.raises(ValueError, match="cannot receive messages"):
        planner_module.run_planner_agent(message)

def test_planner_rejects_wrong_intent():
    message = make_planner_message(intent="delete_assessment")

    with pytest.raises(ValueError, match="cannot handle intent"):
        planner_module.run_planner_agent(message)

def test_planner_rejects_invalid_study_hours():
    message = make_planner_message(available_hours=0)

    with pytest.raises(ValidationError):
        planner_module.run_planner_agent(message)