import logging

from fastapi import APIRouter

from agents.orchestrator import StudyPlanOrchestrator
from models.study_request import StudyRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent")

orchestrator = StudyPlanOrchestrator(
    agent_timeout_seconds=90
)

@router.post("/study-plan")
def create_study_plan(request: StudyRequest):
    logger.info(
        "Study plan request received: %s hours available",
        request.available_hours,
    )

    response = orchestrator.run(request.available_hours)
    recommendation = response["structured_response"]

    logger.info(
        "Study plan recommendation: %s",
        recommendation.assessment_name,
    )
    logger.info(
        "Orchestration completed: iterations=%s, fallback_used=%s",
        response["iterations"],
        response["fallback_used"],
    )

    return recommendation