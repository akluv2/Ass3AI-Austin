from pydantic import BaseModel

class ReviewResult(BaseModel):
    approved: bool
    assessment_exists: bool
    priority_matches: bool
    reasoning_is_consistent: bool
    feedback: str
    suggested_revision: str