import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Callable

from models.agent_message import AgentMessage
from models.recommendation import Recommendation
from models.review_result import ReviewResult
from models.study_request import StudyRequest
from agents.planner_agent import run_planner_agent
from agents.reviewer_agent import run_reviewer_agent
from agents.study_agent import agent_state

logger = logging.getLogger(__name__)

AgentRunner = Callable[[AgentMessage], AgentMessage]


class StudyPlanOrchestrator:
    def __init__(
        self,
        max_iterations: int = 2,
        agent_timeout_seconds: float = 30,
        planner_runner: AgentRunner | None = None,
        reviewer_runner: AgentRunner | None = None,
    ):
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")

        if agent_timeout_seconds <= 0:
            raise ValueError("Agent timeout must be greater than zero")

        self.max_iterations = max_iterations
        self.agent_timeout_seconds = agent_timeout_seconds

        self.planner_runner = planner_runner or run_planner_agent
        self.reviewer_runner = reviewer_runner or run_reviewer_agent

        self.last_iteration_count = 0
        self.last_conversation_steps = []
        self.last_error = None

    def _record_message(self, message, history):
        """Record and log a message passing through the orchestrator."""
        record = message.model_dump(mode="json")
        history.append(record)

        logger.info(
            "Orchestrator communication: %s",
            message.model_dump_json()
        )

    def route_message(self, message: AgentMessage) -> str:
        """Validate a message's route and return its destination."""
        if message.receiver not in {
            "planner",
            "reviewer",
            "orchestrator",
        }:
            raise ValueError(
                f"Invalid receiver: {message.receiver}"
            )

        if (
            message.sender == "planner"
            and message.receiver == "reviewer"
            and message.intent == "review_recommendation"
        ):
            return "reviewer"

        if (
            message.sender == "reviewer"
            and message.receiver == "orchestrator"
            and message.intent == "review_result"
        ):
            return "orchestrator"

        raise ValueError(
            f"Unsupported message route: {message.sender} -> "
            f"{message.receiver}, intent={message.intent}"
        )

    def _invoke_with_timeout(self, runner, message, agent_name):
        """Run an agent with a maximum orchestration wait time."""
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(runner, message)

        try:
            result = future.result(
                timeout=self.agent_timeout_seconds
            )
        except TimeoutError as error:
            future.cancel()
            logger.error(
                "%s timed out after %s seconds",
                agent_name,
                self.agent_timeout_seconds,
            )
            raise TimeoutError(
                f"{agent_name} timed out"
            ) from error
        finally:
            # Do not block the orchestrator while shutting down.
            executor.shutdown(
                wait=False,
                cancel_futures=True,
            )

        if not isinstance(result, AgentMessage):
            raise TypeError(
                f"{agent_name} did not return an AgentMessage"
            )

        return result

    def _check_iteration_limit(self):
        if self.last_iteration_count >= self.max_iterations:
            raise RuntimeError(
                "Maximum agent iteration limit reached"
            )

    def _make_fallback(self, reason):
        return Recommendation(
            assessment_name="No recommendation available",
            priority="Unknown",
            reason=reason,
            suggested_action=(
                "Review your stored assessments manually."
            ),
        )

    def _make_result(
        self,
        recommendation,
        history,
        fallback_used,
        error=None,
    ):
        self.last_conversation_steps = list(history)
        self.last_error = error

        return {
            "structured_response": recommendation,
            "conversation_history": list(history),
            "iterations": self.last_iteration_count,
            "fallback_used": fallback_used,
            "error": error,
        }

    def run(self, available_hours: float):
        """Coordinate the Planner and Reviewer for one study request."""
        # Validate input before starting the agent interaction.
        request = StudyRequest(
            available_hours=available_hours
        )

        self.last_iteration_count = 0
        self.last_conversation_steps = []
        self.last_error = None
        history = []
        agent_state.update_available_hours(request.available_hours)
        

        try:
            # Step 1: Send the student's request to the Planner.
            planner_request = AgentMessage(
                sender="orchestrator",
                receiver="planner",
                intent="create_study_plan",
                content={
                    "available_hours": request.available_hours
                },
                constraints={"format": "json"},
            )

            self._record_message(planner_request, history)

            self._check_iteration_limit()
            self.last_iteration_count += 1

            planner_message = self._invoke_with_timeout(
                self.planner_runner,
                planner_request,
                "Planner",
            )

            self._record_message(planner_message, history)
            agent_state.update_tool_call("lookup_assessments")
            agent_state.add_action("Planner sent recommendation")

            destination = self.route_message(planner_message)

            if destination != "reviewer":
                raise ValueError(
                    "Planner response was not routed to the Reviewer"
                )

            # Step 2: Route the recommendation to the Reviewer.
            self._check_iteration_limit()
            self.last_iteration_count += 1

            review_message = self._invoke_with_timeout(
                self.reviewer_runner,
                planner_message,
                "Reviewer",
            )

            self._record_message(review_message, history)

            destination = self.route_message(review_message)

            if destination != "orchestrator":
                raise ValueError(
                    "Review result was not routed to the orchestrator"
                )

            # Step 3: Validate the review and recommendation.
            recommendation = Recommendation.model_validate(
                review_message.content.get("recommendation")
            )

            review = ReviewResult.model_validate(
                review_message.content.get("review")
            )

            if not review.approved:
                logger.warning(
                    "Reviewer rejected the recommendation: %s",
                    review.feedback,
                )

                agent_state.update_recommendation("No recommendation available")
                agent_state.add_action("Reviewer rejected recommendation; fallback used")

                return self._make_result(
                    self._make_fallback(
                        "The Reviewer did not approve the recommendation. "
                        + review.feedback
                    ),
                    history,
                    fallback_used=True,
                    error="Reviewer rejected the recommendation",
                )

            logger.info(
                "Orchestration completed with an approved recommendation"
            )

            agent_state.update_recommendation(recommendation.assessment_name)
            agent_state.add_action("Reviewer approved recommendation")

            return self._make_result(
                recommendation,
                history,
                fallback_used=False,
            )

        except Exception as error:
            logger.exception("Study plan orchestration failed")
            agent_state.error_count += 1
            agent_state.update_error(error)
            agent_state.update_recommendation("No recommendation available")
            agent_state.add_action("Agent orchestration fallback used")

            return self._make_result(
                self._make_fallback(
                    "The multi-agent system could not complete the "
                    "study plan. " + str(error)
                ),
                history,
                fallback_used=True,
                error=str(error),
            )