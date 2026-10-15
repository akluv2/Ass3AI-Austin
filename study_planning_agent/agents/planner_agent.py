import logging

from pydantic import ValidationError

from agents.study_agent import study_agent as planner_llm_agent
from models.agent_message import AgentMessage
from models.recommendation import Recommendation
from models.study_request import StudyRequest

logger = logging.getLogger(__name__)

def run_planner_agent(message: AgentMessage) -> AgentMessage:
    """Process a study-planning request and send its recommendation to the reviewer."""

    logger.info(
        "Planner received message: %s",
        message.model_dump_json()
    )

    if message.receiver != "planner":
        raise ValueError(
            f"Planner cannot receive messages addressed to '{message.receiver}'"
        )

    if message.intent != "create_study_plan":
        raise ValueError(
            f"Planner cannot handle intent '{message.intent}'"
        )

    # Validate the message content using the existing request model.
    request = StudyRequest.model_validate(message.content)

    try:
        # Reuse the existing LangChain agent and its assessment lookup tool.
        response = planner_llm_agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"I have {request.available_hours} hours available "
                        "to study. Which assessment should I focus on next?"
                    )
                }
            ]
        })

        # Validate the agent's structured recommendation.
        recommendation = Recommendation.model_validate(
            response["structured_response"]
        )

        # Pass the recommendation to the Reviewer using the message schema.
        outgoing_message = AgentMessage(
            sender="planner",
            receiver="reviewer",
            intent="review_recommendation",
            content={
                "available_hours": request.available_hours,
                "recommendation": recommendation.model_dump()
            },
            constraints={
                "check_assessment_exists": True,
                "check_available_hours": True
            }
        )

        logger.info(
            "Planner sent message: %s",
            outgoing_message.model_dump_json()
        )

        return outgoing_message

    except Exception:
        logger.exception("Planner agent failed")
        raise