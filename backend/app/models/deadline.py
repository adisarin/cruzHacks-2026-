from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Deadline(BaseModel):
    id: Optional[str] = None
    title: str
    course: str
    due_date: datetime
    assignment_type: Optional[str] = None  # homework, exam, project, etc.
    points: Optional[float] = None
    description: Optional[str] = None
    canvas_assignment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Midterm Exam",
                "course": "CS101",
                "due_date": "2026-02-15T14:00:00",
                "assignment_type": "exam",
                "points": 100.0,
                "canvas_assignment_id": "12345"
            }
        }

