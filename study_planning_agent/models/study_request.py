from pydantic import BaseModel, Field

class StudyRequest(BaseModel):
    available_hours: float = Field(gt=0)