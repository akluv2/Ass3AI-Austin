from datetime import date
from models.assessment import Assessment

assessments = [
    Assessment(
        id=1,
        name="AI Application",
        subject="COIT12204",
        due_date=date(2026, 10, 20),
        priority="High",
        estimated_hours=8
    ),
    Assessment(
        id=2,
        name="Database Project",
        subject="COIT12205",
        due_date=date(2026, 10, 30),
        priority="Medium",
        estimated_hours=5
    ),
    Assessment(
        id=3,
        name="Web Development Assignment",
        subject="COIT12206",
        due_date=date(2026, 10, 15),
        priority="Medium",
        estimated_hours=4
    )
]

def get_assessments() -> list[Assessment]:
    return assessments