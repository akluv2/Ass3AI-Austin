import logging

from langchain.agents import create_agent
from pydantic import ValidationError

from agents.study_agent import llm
from models.agent_message import AgentMessage
from models.recommendation import Recommendation
from models.review_result import ReviewResult
from models.study_request import StudyRequest
from services.assessment_service import get_assessments
from tools.assessment_tools import lookup_assessments

logger = logging.getLogger(__name__)

reviewer_system_prompt = """
You are a study recommendation reviewer.

Your role is to review a recommendation produced by the Planner Agent.

You must use the lookup_assessments tool to retrieve the current
stored assessment information before reviewing the recommendation.

Check:
- Whether the recommended assessment exists.
- Whether its priority matches the stored assessment.
- Whether the explanation reasonably considers the due date,
  priority, workload and available study hours.
- Whether the suggested action is realistic for the available hours.

Do not approve a recommendation if its explanation is inconsistent
with the available assessment information.

Return your findings using the required structured output.
Explain your decision in feedback and suggest corrections if needed.
"""

reviewer_llm_agent = create_agent(
    model=llm,
    tools=[lookup_assessments],
    response_format=ReviewResult,
    system_prompt=reviewer_system_prompt
)

def run_reviewer_agent(message: AgentMessage) -> AgentMessage:
    """Review the Planner Agent's recommendation."""

    logger.info(
        "Reviewer received message: %s",
        message.model_dump_json()
    )

    if message.receiver != "reviewer":
        raise ValueError(
            f"Reviewer cannot receive messages addressed to "
            f"'{message.receiver}'"
        )

    if message.sender != "planner":
        raise ValueError(
            f"Reviewer cannot accept messages from '{message.sender}'"
        )

    if message.intent != "review_recommendation":
        raise ValueError(
            f"Reviewer cannot handle intent '{message.intent}'"
        )

    # Validate the information passed by the Planner.
    request = StudyRequest.model_validate({
        "available_hours": message.content.get("available_hours")
    })

    recommendation = Recommendation.model_validate(
        message.content.get("recommendation")
    )

    try:
        response = reviewer_llm_agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Available study hours: {request.available_hours}\n"
                        f"Planner recommendation: "
                        f"{recommendation.model_dump_json()}\n\n"
                        "Review this recommendation against the stored "
                        "assessment information."
                    )
                }
            ]
        })

        proposed_review = ReviewResult.model_validate(
            response["structured_response"]
        )

        # Verify assessment existence and priority against actual data.
        assessments = get_assessments()

        matched_assessment = next(
            (
                assessment
                for assessment in assessments
                if assessment.name.casefold()
                == recommendation.assessment_name.casefold()
            ),
            None
        )

        assessment_exists = matched_assessment is not None

        priority_matches = (
            matched_assessment is not None
            and matched_assessment.priority.casefold()
            == recommendation.priority.casefold()
        )

        # Do not approve if deterministic checks fail.
        final_review = ReviewResult(
            approved=(
                proposed_review.approved
                and assessment_exists
                and priority_matches
                and proposed_review.reasoning_is_consistent
            ),
            assessment_exists=assessment_exists,
            priority_matches=priority_matches,
            reasoning_is_consistent=(
                proposed_review.reasoning_is_consistent
            ),
            feedback=proposed_review.feedback,
            suggested_revision=proposed_review.suggested_revision
        )

        outgoing_message = AgentMessage(
            sender="reviewer",
            receiver="orchestrator",
            intent="review_result",
            content={
                "recommendation": recommendation.model_dump(),
                "review": final_review.model_dump(),
                "available_hours": request.available_hours
            },
            constraints={
                "approved": final_review.approved
            }
        )

        logger.info(
            "Reviewer sent message: %s",
            outgoing_message.model_dump_json()
        )

        return outgoing_message

    except Exception:
        logger.exception("Reviewer agent failed")
        raise