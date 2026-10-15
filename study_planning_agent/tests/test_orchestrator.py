import logging
import time

import pytest
from pydantic import ValidationError

from agents.orchestrator import StudyPlanOrchestrator
from agents.study_agent import agent_state
from models.agent_message import AgentMessage
from models.recommendation import Recommendation
from models.review_result import ReviewResult

def make_recommendation():
    return Recommendation(
        assessment_name="Web Development Assignment",
        priority="Medium",
        reason="It has the earliest due date.",
        suggested_action="Spend two hours making progress.",
    ).model_dump()

def make_planner_response(receiver="reviewer"):
    return AgentMessage(
        sender="planner",
        receiver=receiver,
        intent="review_recommendation",
        content={
            "available_hours": 2,
            "recommendation": make_recommendation(),
        },
    )

def make_reviewer_response(approved=True):
    return AgentMessage(
        sender="reviewer",
        receiver="orchestrator",
        intent="review_result",
        content={
            "recommendation": make_recommendation(),
            "review": ReviewResult(
                approved=approved,
                assessment_exists=True,
                priority_matches=True,
                reasoning_is_consistent=True,
                feedback=(
                    "Recommendation is reasonable."
                    if approved
                    else "Recommendation needs revision."
                ),
                suggested_revision="Review the assessment priority.",
            ).model_dump(),
        },
    )

def fake_planner(message):
    assert message.receiver == "planner"
    return make_planner_response()

def fake_reviewer(message):
    assert message.receiver == "reviewer"
    return make_reviewer_response()

def test_orchestrator_completes_agent_pipeline(caplog):
    orchestrator = StudyPlanOrchestrator(
        planner_runner=fake_planner,
        reviewer_runner=fake_reviewer,
    )

    with caplog.at_level(logging.INFO):
        result = orchestrator.run(2)

    assert result["fallback_used"] is False
    assert (
        result["structured_response"].assessment_name
        == "Web Development Assignment"
    )
    assert result["iterations"] == 2
    assert len(result["conversation_history"]) == 3
    assert "Orchestrator communication" in caplog.text

def test_orchestrator_handles_invalid_receiver():
    from agents.study_agent import agent_state

    previous_error_count = agent_state.error_count

    def invalid_planner(message):
        return make_planner_response(receiver="unknown_agent")

    orchestrator = StudyPlanOrchestrator(
        planner_runner=invalid_planner,
        reviewer_runner=fake_reviewer,
    )

    result = orchestrator.run(2)

    assert result["fallback_used"] is True
    assert "Invalid receiver" in result["error"]

    # Confirm the failure was recorded in the application state.
    assert agent_state.error_count == previous_error_count + 1
    assert "Invalid receiver" in agent_state.last_error
    assert (
        agent_state.last_recommendation
        == "No recommendation available"
    )
    assert (
        agent_state.action_history[-1]
        == "Agent orchestration fallback used"
    )

def test_orchestrator_enforces_max_iterations():
    def reviewer_should_not_run(message):
        raise AssertionError("Reviewer should not run")

    orchestrator = StudyPlanOrchestrator(
        max_iterations=1,
        planner_runner=fake_planner,
        reviewer_runner=reviewer_should_not_run,
    )

    result = orchestrator.run(2)

    assert result["fallback_used"] is True
    assert result["iterations"] == 1
    assert "Maximum agent iteration limit" in result["error"]

def test_orchestrator_handles_rejected_review():
    def rejecting_reviewer(message):
        return make_reviewer_response(approved=False)

    orchestrator = StudyPlanOrchestrator(
        planner_runner=fake_planner,
        reviewer_runner=rejecting_reviewer,
    )

    result = orchestrator.run(2)

    assert result["fallback_used"] is True
    assert (
        result["structured_response"].assessment_name
        == "No recommendation available"
    )
    assert result["error"] == "Reviewer rejected the recommendation"

def test_orchestrator_handles_timeout():
    def slow_planner(message):
        time.sleep(0.2)
        return make_planner_response()

    orchestrator = StudyPlanOrchestrator(
        agent_timeout_seconds=0.03,
        planner_runner=slow_planner,
        reviewer_runner=fake_reviewer,
    )

    result = orchestrator.run(2)

    assert result["fallback_used"] is True
    assert "timed out" in result["error"].lower()

def test_orchestrator_rejects_invalid_study_hours():
    orchestrator = StudyPlanOrchestrator(
        planner_runner=fake_planner,
        reviewer_runner=fake_reviewer,
    )

    with pytest.raises(ValidationError):
        orchestrator.run(0)

def test_orchestrator_handles_malformed_reviewer_output():
    def malformed_reviewer(message):
        return AgentMessage(
            sender="reviewer",
            receiver="orchestrator",
            intent="review_result",
            content={
                "recommendation": make_recommendation(),
                "review": {
                    "approved": True
                },
                "available_hours": 2,
            },
        )

    orchestrator = StudyPlanOrchestrator(
        planner_runner=fake_planner,
        reviewer_runner=malformed_reviewer,
    )

    result = orchestrator.run(2)

    assert result["fallback_used"] is True
    assert (
        result["structured_response"].assessment_name
        == "No recommendation available"
    )
    assert result["error"]
    assert "validation" in result["error"].lower()