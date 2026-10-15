from pydantic import BaseModel

class Recommendation(BaseModel):
    assessment_name: str
    priority: str
    reason: str
    suggested_action: str