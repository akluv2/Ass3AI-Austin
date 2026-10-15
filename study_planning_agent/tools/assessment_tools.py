from langchain_core.tools import tool
from services.assessment_service import get_assessments

@tool
def lookup_assessments() -> str:
    """Retrieve the student's stored assessment information."""
    assessments = get_assessments()

    return "\n".join(
        f"ID: {assessment.id}, "
        f"Name: {assessment.name}, "
        f"Subject: {assessment.subject}, "
        f"Due: {assessment.due_date}, "
        f"Priority: {assessment.priority}, "
        f"Estimated hours: {assessment.estimated_hours}"
        for assessment in assessments
    )