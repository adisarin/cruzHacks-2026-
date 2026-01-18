from typing import Optional, List
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    notification_frequency: str = "daily"  # real-time, hourly, daily, weekly
    nudge_threshold_days: int = 3  # Days before deadline to start nudging
    preferred_study_hours_per_day: float = 3.0
    preferred_study_times: List[str] = Field(default_factory=lambda: ["09:00-12:00", "14:00-17:00"])
    auto_create_study_plans: bool = True
    study_plan_days_before_exam: int = 7
    
    class Config:
        json_schema_extra = {
            "example": {
                "notification_frequency": "daily",
                "nudge_threshold_days": 3,
                "preferred_study_hours_per_day": 3.0,
                "preferred_study_times": ["09:00-12:00", "14:00-17:00"],
                "auto_create_study_plans": True,
                "study_plan_days_before_exam": 7
            }
        }


class User(BaseModel):
    id: Optional[str] = None
    email: str
    name: str
    canvas_token: Optional[str] = None
    google_calendar_token: Optional[str] = None
    apple_calendar_enabled: bool = False
    piazza_credentials: Optional[dict] = None
    slack_bot_token: Optional[str] = None
    slack_channel_ids: Optional[List[str]] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@ucsc.edu",
                "name": "John Doe",
                "preferences": {}
            }
        }

