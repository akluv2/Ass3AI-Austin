import logging

logger = logging.getLogger(__name__)

class AgentState:
    def __init__(self):
        self.last_recommendation = None
        self.last_tool_call = None
        self.action_history = []
        self.error_count = 0
        self.last_available_hours = None
        self.last_error = None

    def update_available_hours(self, hours):
        self.last_available_hours = hours
        logger.info(f"State transition: last_available_hours = {hours}")

    def update_tool_call(self, tool_name):
        self.last_tool_call = tool_name
        logger.info(f"State transition: last_tool_call = {tool_name}")

    def update_recommendation(self, recommendation):
        self.last_recommendation = recommendation
        logger.info(
            f"State transition: last_recommendation = {recommendation}"
        )

    def add_action(self, action):
        self.action_history.append(action)
        logger.info(f"State transition: action_history updated")

    def update_error(self, error):
        self.last_error = str(error)
        logger.info(f"State transition: last_error = {self.last_error}")