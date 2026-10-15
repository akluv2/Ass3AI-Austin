import pytest
from pydantic import ValidationError

from models.agent_message import AgentMessage

def test_agent_message_accepts_valid_message():
    message = AgentMessage(
        sender="planner",
        receiver="reviewer",
        intent="review_recommendation",
        content={
            "assessment_name": "Web Development Assignment",
            "priority": "High"
        }
    )

    assert message.sender == "planner"
    assert message.receiver == "reviewer"
    assert message.intent == "review_recommendation"
    assert message.content["assessment_name"] == "Web Development Assignment"
    assert message.constraints == {}

def test_agent_message_rejects_missing_required_field():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender="planner",
            receiver="reviewer",
            content={"assessment_name": "Web Development Assignment"}
        )

def test_agent_message_rejects_empty_sender():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender="",
            receiver="reviewer",
            intent="review_recommendation",
            content={}
        )

def test_agent_message_rejects_empty_receiver():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender="planner",
            receiver="",
            intent="review_recommendation",
            content={}
        )