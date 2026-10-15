from datetime import date
from pydantic import BaseModel

class Assessment(BaseModel):
    id: int
    name: str
    subject: str
    due_date: date
    priority: str
    estimated_hours: float