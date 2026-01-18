from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.deadline import Deadline
from app.models.study_plan import StudyPlan
from app.models.user import User, UserPreferences
from app.agent.slugpilot_agent import SlugPilotAgent
from app.agent.study_plan_generator import StudyPlanGenerator
from app.agent.notification_service import NotificationService
from app.agent.agent_manager import agent_manager
import asyncio

app = FastAPI(
    title="SlugPilot API",
    description="An Autonomous Student Life Agent - AI chief of staff for college students",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (in production, use a database)
users_db = {}
agents_db = {}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Start all registered agents on startup"""
    print("[Startup] SlugPilot API starting...")
    # Agents will be started when users are created/registered


@app.on_event("shutdown")
async def shutdown_event():
    """Stop all agents on shutdown"""
    print("[Shutdown] Stopping all agents...")
    await agent_manager.stop_all_agents()


# Request/Response models
class UserCreate(BaseModel):
    email: str
    name: str
    canvas_token: Optional[str] = None
    google_calendar_token: Optional[str] = None
    apple_calendar_enabled: bool = False
    slack_bot_token: Optional[str] = None
    slack_channel_ids: Optional[List[str]] = None
    piazza_credentials: Optional[dict] = None
    preferences: Optional[UserPreferences] = None


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None


class StudyPlanCreate(BaseModel):
    course: str
    exam_date: datetime
    exam_title: str
    topics: Optional[List[str]] = None
    total_study_hours: Optional[float] = None


# Dependency to get user agent
def get_agent(user_id: str) -> SlugPilotAgent:
    if user_id not in agents_db:
        raise HTTPException(status_code=404, detail="User not found")
    return agents_db[user_id]


# Helper function to start agent in background
def start_agent_background(user_id: str):
    """Start agent in background using asyncio"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the task
            asyncio.create_task(agent_manager.start_agent(user_id))
        else:
            # If no loop, create one
            loop.run_until_complete(agent_manager.start_agent(user_id))
    except RuntimeError:
        # No event loop, create one in a thread
        import threading
        def run_agent():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(agent_manager.start_agent(user_id))
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()

# User Management Endpoints
@app.post("/users", response_model=User)
def create_user(user_data: UserCreate):
    """Create a new user and initialize their SlugPilot agent"""
    user = User(
        email=user_data.email,
        name=user_data.name,
        canvas_token=user_data.canvas_token,
        google_calendar_token=user_data.google_calendar_token,
        apple_calendar_enabled=user_data.apple_calendar_enabled,
        slack_bot_token=user_data.slack_bot_token,
        slack_channel_ids=user_data.slack_channel_ids,
        piazza_credentials=user_data.piazza_credentials,
        preferences=user_data.preferences or UserPreferences()
    )
    user.id = user_data.email  # Simple ID for demo
    
    # Initialize agent
    agent = SlugPilotAgent(user)
    agents_db[user.id] = agent
    users_db[user.id] = user
    
    # Register agent (but don't auto-start - user can start via endpoint)
    agent_manager.register_agent(user)
    
    return user


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    """Get user information"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]


# Task Management Endpoints
@app.get("/users/{user_id}/tasks", response_model=List[Task])
def get_all_tasks(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Get all tasks from all sources"""
    tasks = agent.gather_all_tasks()
    return tasks


@app.get("/users/{user_id}/tasks/upcoming", response_model=List[Task])
def get_upcoming_tasks(user_id: str, days: int = 7, agent: SlugPilotAgent = Depends(get_agent)):
    """Get upcoming tasks within specified days"""
    all_tasks = agent.gather_all_tasks()
    cutoff = datetime.now() + timedelta(days=days)
    upcoming = [t for t in all_tasks if t.due_date <= cutoff]
    return sorted(upcoming, key=lambda t: t.due_date)


@app.get("/users/{user_id}/tasks/overdue", response_model=List[Task])
def get_overdue_tasks(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Get all overdue tasks"""
    all_tasks = agent.gather_all_tasks()
    overdue = [t for t in all_tasks if t.status == TaskStatus.OVERDUE]
    return overdue


@app.patch("/users/{user_id}/tasks/{task_id}")
def update_task(user_id: str, task_id: str, update: TaskUpdate, agent: SlugPilotAgent = Depends(get_agent)):
    """Update a task's status or priority"""
    # In a real implementation, would update task in database
    # For now, return success
    return {"message": "Task updated", "task_id": task_id, **update.dict(exclude_unset=True)}


# Planning Endpoints
@app.post("/users/{user_id}/plan/weekly", response_model=List[Task])
def create_weekly_plan(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Create or update the weekly plan"""
    plan = agent.create_weekly_plan()
    return plan


@app.get("/users/{user_id}/plan/weekly", response_model=List[Task])
def get_weekly_plan(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Get the current weekly plan"""
    if not agent.weekly_plan:
        agent.create_weekly_plan()
    return agent.weekly_plan


@app.post("/users/{user_id}/plan/revise", response_model=List[Task])
def revise_plan(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Revise the weekly plan (called when deadlines shift)"""
    revised_plan = agent.revise_plan()
    return revised_plan


# Academic Health Endpoints
@app.get("/users/{user_id}/health")
def get_academic_health(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Get academic health status"""
    health = agent.check_academic_health()
    return health


@app.get("/users/{user_id}/conflicts")
def get_conflicts(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Get detected conflicts and clarifying questions"""
    if not agent.weekly_plan:
        agent.create_weekly_plan()
    
    questions = agent.get_clarifying_questions()
    return {
        "conflicts": agent.conflicts,
        "clarifying_questions": questions
    }


# Study Plan Endpoints
@app.post("/users/{user_id}/study-plans", response_model=StudyPlan)
def create_study_plan(user_id: str, plan_data: StudyPlanCreate, agent: SlugPilotAgent = Depends(get_agent)):
    """Create a study plan for an exam"""
    generator = StudyPlanGenerator(agent.preferences)
    study_plan = generator.generate_study_plan(
        course=plan_data.course,
        exam_date=plan_data.exam_date,
        exam_title=plan_data.exam_title,
        topics=plan_data.topics,
        total_study_hours=plan_data.total_study_hours
    )
    
    # Auto-sync to calendar if enabled
    if agent.user.preferences.auto_create_study_plans and agent.calendar_service:
        sessions_data = [
            {
                "course": s.course,
                "topic": s.topic,
                "duration_hours": s.duration_hours,
                "scheduled_time": s.scheduled_time.isoformat(),
                "materials": s.materials
            }
            for s in study_plan.sessions
        ]
        agent.calendar_service.sync_study_sessions(sessions_data)
    
    return study_plan


@app.post("/users/{user_id}/study-plans/auto-create", response_model=List[StudyPlan])
def auto_create_study_plans(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Automatically create study plans for upcoming exams"""
    if not agent.canvas_service:
        raise HTTPException(status_code=400, detail="Canvas service not configured")
    
    deadlines = agent.canvas_service.get_deadlines()
    generator = StudyPlanGenerator(agent.preferences)
    study_plans = generator.auto_create_for_upcoming_exams(deadlines)
    
    # Sync to calendar
    if agent.calendar_service:
        for plan in study_plans:
            sessions_data = [
                {
                    "course": s.course,
                    "topic": s.topic,
                    "duration_hours": s.duration_hours,
                    "scheduled_time": s.scheduled_time.isoformat(),
                    "materials": s.materials
                }
                for s in plan.sessions
            ]
            agent.calendar_service.sync_study_sessions(sessions_data)
    
    return study_plans


# Notification Endpoints
@app.post("/users/{user_id}/nudge")
def send_nudge(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Check if user should be nudged and send notification"""
    if not agent.should_nudge():
        return {"should_nudge": False, "message": "No nudge needed"}
    
    all_tasks = agent.gather_all_tasks()
    health = agent.check_academic_health()
    
    notification_service = NotificationService(agent.user)
    message = notification_service.generate_nudge_message(all_tasks, health)
    
    success = notification_service.send_nudge(message, priority=health["status"])
    
    return {
        "should_nudge": True,
        "message": message,
        "sent": success,
        "health_status": health["status"]
    }


@app.post("/users/{user_id}/notifications/weekly-summary")
def send_weekly_summary(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Send weekly summary notification"""
    if not agent.weekly_plan:
        agent.create_weekly_plan()
    
    health = agent.check_academic_health()
    notification_service = NotificationService(agent.user)
    
    success = notification_service.send_weekly_summary(agent.weekly_plan, health)
    
    return {
        "sent": success,
        "summary": {
            "tasks_count": len(agent.weekly_plan),
            "health_score": health["score"],
            "health_status": health["status"]
        }
    }


# Canvas Integration Endpoints
@app.get("/users/{user_id}/canvas/deadlines", response_model=List[Deadline])
def get_canvas_deadlines(user_id: str, days_ahead: int = 30, agent: SlugPilotAgent = Depends(get_agent)):
    """Get deadlines from Canvas"""
    if not agent.canvas_service:
        raise HTTPException(status_code=400, detail="Canvas service not configured")
    
    deadlines = agent.canvas_service.get_deadlines(days_ahead=days_ahead)
    return deadlines


@app.get("/users/{user_id}/canvas/courses")
def get_canvas_courses(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Get enrolled courses from Canvas"""
    if not agent.canvas_service:
        raise HTTPException(status_code=400, detail="Canvas service not configured")
    
    courses = agent.canvas_service.get_courses()
    return {"courses": courses}


# Agent Control Endpoints (Autonomous Agent Management)
@app.post("/users/{user_id}/agent/start")
async def start_agent(user_id: str):
    """Start the autonomous agent loop for a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    await agent_manager.start_agent(user_id)
    return {
        "status": "started",
        "message": "Autonomous agent loop started",
        "user_id": user_id
    }


@app.post("/users/{user_id}/agent/stop")
async def stop_agent(user_id: str):
    """Stop the autonomous agent loop for a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    await agent_manager.stop_agent(user_id)
    return {
        "status": "stopped",
        "message": "Autonomous agent loop stopped",
        "user_id": user_id
    }


@app.get("/users/{user_id}/agent/status")
def get_agent_status(user_id: str):
    """Get the status of the autonomous agent"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    agent_loop = agent_manager.get_agent_loop(user_id)
    if not agent_loop:
        return {
            "status": "not_registered",
            "message": "Agent not registered for this user"
        }
    
    status = agent_loop.get_status()
    status["is_running"] = agent_manager.is_agent_running(user_id)
    
    return status


@app.get("/users/{user_id}/agent/actions")
def get_agent_actions(user_id: str, limit: int = 20):
    """Get recent actions taken by the autonomous agent"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    agent_loop = agent_manager.get_agent_loop(user_id)
    if not agent_loop:
        return {"actions": []}
    
    actions = agent_loop.get_action_history(limit=limit)
    return {
        "actions": actions,
        "count": len(actions)
    }


@app.post("/users/{user_id}/agent/execute-cycle")
async def execute_agent_cycle(user_id: str):
    """Manually trigger an agent cycle (for testing/demo)"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    agent_loop = agent_manager.get_agent_loop(user_id)
    if not agent_loop:
        raise HTTPException(status_code=404, detail="Agent not registered")
    
    await agent_loop._run_cycle()
    return {
        "status": "completed",
        "message": "Agent cycle executed",
        "actions": agent_loop.get_action_history(limit=5)
    }


@app.get("/users/{user_id}/agent/decisions")
def get_autonomous_decisions(user_id: str, agent: SlugPilotAgent = Depends(get_agent)):
    """Get recent autonomous decisions made by the agent"""
    decisions = agent.make_autonomous_decisions()
    return {
        "decisions": decisions,
        "count": len(decisions),
        "timestamp": datetime.now().isoformat()
    }


# Health Check
@app.get("/")
def health():
    """Health check endpoint"""
    return {
        "status": "backend running",
        "service": "SlugPilot API",
        "version": "1.0.0",
        "agentic": True,
        "description": "Autonomous student life agent - runs continuously in the background"
    }
