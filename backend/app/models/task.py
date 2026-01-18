from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class Task(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    course: Optional[str] = None
    due_date: datetime
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    estimated_hours: Optional[float] = None
    source: str = Field(description="Source: canvas, calendar, piazza, slack, or agent")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "CS101 Assignment 3",
                "description": "Implement binary search tree",
                "course": "CS101",
                "due_date": "2026-01-20T23:59:00",
                "priority": "high",
                "status": "pending",
                "estimated_hours": 5.0,
                "source": "canvas"
            }
        }

