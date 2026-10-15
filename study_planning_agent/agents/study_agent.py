from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from models.recommendation import Recommendation
from tools.assessment_tools import lookup_assessments
from agents.prompts import study_planning_system_prompt
from state.agent_state import AgentState

import logging

logger = logging.getLogger(__name__)
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0
)

study_agent = create_agent(
    model=llm,
    tools=[lookup_assessments],
    response_format=Recommendation,
    system_prompt=study_planning_system_prompt
)

agent_state = AgentState()

def run_study_agent(available_hours: float):
    agent_state.update_available_hours(available_hours)

    try:
        response = study_agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"I have {available_hours} hours available to study. "
                        "Which assessment should I focus on next?"
                    )
                }
            ]
        })

        agent_state.update_tool_call("lookup_assessments")

        recommendation = response["structured_response"]

        agent_state.update_recommendation(
            recommendation.assessment_name
        )
        agent_state.add_action(
            f"Recommended {recommendation.assessment_name}"
        )

        return response

    except Exception as error:
        agent_state.error_count += 1
        agent_state.update_error(error)
        logger.error(f"Study agent failed: {error}")

        agent_state.add_action("Study agent fallback used")

        fallback = Recommendation(
            assessment_name="No recommendation available",
            priority="Unknown",
            reason="The study planning agent was unable to process the request.",
            suggested_action="Review your stored assessments manually."
        )

        agent_state.update_recommendation(
            fallback.assessment_name
        )

        return {
            "structured_response": fallback
        }