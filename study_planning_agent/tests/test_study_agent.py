from agents import study_agent
from models.recommendation import Recommendation
from state.agent_state import AgentState


def test_study_agent_with_mocked_response(monkeypatch):
    study_agent.agent_state = AgentState()

    fake_recommendation = Recommendation(
        assessment_name="Web Development Assignment",
        priority="High",
        reason="It has the earliest due date and high priority.",
        suggested_action="Work on the Web Development Assignment next."
    )

    def fake_invoke(_):
        return {
            "structured_response": fake_recommendation
        }

    monkeypatch.setattr(
        study_agent.study_agent,
        "invoke",
        fake_invoke
    )

    response = study_agent.run_study_agent(5)

    assert response["structured_response"] == fake_recommendation
    assert study_agent.agent_state.last_tool_call == "lookup_assessments"
    assert study_agent.agent_state.last_recommendation == "Web Development Assignment"
    assert study_agent.agent_state.action_history[-1] == (
        "Recommended Web Development Assignment"
    )

def test_study_agent_updates_state(monkeypatch):
    study_agent.agent_state = AgentState()

    fake_recommendation = Recommendation(
        assessment_name="Web Development Assignment",
        priority="High",
        reason="It has the earliest due date and high priority.",
        suggested_action="Work on the Web Development Assignment next."
    )

    def fake_invoke(_):
        return {
            "structured_response": fake_recommendation
        }

    monkeypatch.setattr(
        study_agent.study_agent,
        "invoke",
        fake_invoke
    )

    study_agent.run_study_agent(5)

    assert study_agent.agent_state.last_tool_call == "lookup_assessments"
    assert study_agent.agent_state.last_recommendation == "Web Development Assignment"
    assert study_agent.agent_state.action_history[-1] == (
        "Recommended Web Development Assignment"
    )

def test_study_agent_fallback(monkeypatch):
    study_agent.agent_state = AgentState()

    def fake_agent_failure(_):
        raise Exception("Simulated agent failure")

    monkeypatch.setattr(
        study_agent.study_agent,
        "invoke",
        fake_agent_failure
    )

    response = study_agent.run_study_agent(5)

    recommendation = response["structured_response"]

    assert recommendation.assessment_name == "No recommendation available"
    assert study_agent.agent_state.error_count == 1
    assert study_agent.agent_state.last_error == "Simulated agent failure"
    assert study_agent.agent_state.action_history[-1] == (
        "Study agent fallback used"
    )

def test_study_agent_handles_malformed_response(monkeypatch):
    study_agent.agent_state = AgentState()

    def fake_invoke(_):
        return {}

    monkeypatch.setattr(
        study_agent.study_agent,
        "invoke",
        fake_invoke
    )

    response = study_agent.run_study_agent(5)

    recommendation = response["structured_response"]

    assert recommendation.assessment_name == "No recommendation available"
    assert study_agent.agent_state.error_count == 1
    assert study_agent.agent_state.action_history[-1] == (
        "Study agent fallback used"
    )