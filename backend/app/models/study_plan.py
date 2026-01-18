from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StudySession(BaseModel):
    id: Optional[str] = None
    course: str
    topic: str
    duration_hours: float
    scheduled_time: datetime
    materials: List[str] = Field(default_factory=list)
    completed: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "course": "CS101",
                "topic": "Binary Trees",
                "duration_hours": 2.0,
                "scheduled_time": "2026-02-10T10:00:00",
                "materials": ["Chapter 5", "Practice problems 1-10"],
                "completed": False
            }
        }


class StudyPlan(BaseModel):
    id: Optional[str] = None
    course: str
    exam_date: datetime
    exam_title: str
    sessions: List[StudySession] = Field(default_factory=list)
    total_hours: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"  # active, completed, cancelled
    
    class Config:
        json_schema_extra = {
            "example": {
                "course": "CS101",
                "exam_date": "2026-02-15T14:00:00",
                "exam_title": "Midterm Exam",
                "total_hours": 12.0,
                "status": "active"
            }
        }

