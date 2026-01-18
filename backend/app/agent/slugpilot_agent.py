from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.deadline import Deadline
from app.models.study_plan import StudyPlan, StudySession
from app.models.user import User, UserPreferences
from app.services.canvas_service import CanvasService
from app.services.calendar_service import CalendarService
from app.services.piazza_service import PiazzaService
from app.services.slack_service import SlackService


class SlugPilotAgent:
    """
    Core agentic system for SlugPilot.
    Goal: "Keep me academically safe"
    
    Responsibilities:
    - Plans tasks weekly
    - Revises strategy if deadlines shift
    - Asks clarifying questions when priorities conflict
    - Monitors academic health
    """
    
    def __init__(self, user: User):
        self.user = user
        self.preferences = user.preferences
        
        # Initialize services (always create CanvasService, will use mock data if no token)
        self.canvas_service = CanvasService(user.canvas_token)
        self.calendar_service = CalendarService(
            user.google_calendar_token,
            user.apple_calendar_enabled
        ) if user.google_calendar_token else None
        self.piazza_service = PiazzaService(**user.piazza_credentials) if user.piazza_credentials else None
        self.slack_service = SlackService(
            user.slack_bot_token
        ) if user.slack_bot_token else None
        
        # Agent state
        self.weekly_plan: List[Task] = []
        self.last_plan_update: Optional[datetime] = None
        self.conflicts: List[Dict] = []
    
    def gather_all_tasks(self) -> List[Task]:
        """Aggregate tasks from all sources"""
        all_tasks = []
        from app.services.mock_data_service import mock_data_service
        
        # Canvas deadlines (always works - uses mock data if no token)
        try:
            canvas_tasks = self.canvas_service.get_tasks_from_deadlines()
            all_tasks.extend(canvas_tasks)
        except Exception as e:
            print(f"Error getting Canvas tasks: {e}")
            # Fallback: use mock data directly
            deadlines = mock_data_service.generate_canvas_deadlines(10)
            canvas_tasks = self.canvas_service.get_tasks_from_deadlines(deadlines)
            all_tasks.extend(canvas_tasks)
        
        # Calendar events (use mock if no real calendar)
        if self.calendar_service and self.user.google_calendar_token:
            try:
                calendar_tasks = self.calendar_service.get_tasks_from_calendar()
                all_tasks.extend(calendar_tasks)
            except:
                all_tasks.extend(mock_data_service.generate_calendar_events(5))
        else:
            all_tasks.extend(mock_data_service.generate_calendar_events(5))
        
        # Piazza announcements (use mock if no real Piazza)
        if self.piazza_service and self.user.piazza_credentials:
            try:
                piazza_tasks = self.piazza_service.get_tasks_from_announcements()
                all_tasks.extend(piazza_tasks)
            except:
                all_tasks.extend(mock_data_service.generate_piazza_announcements())
        else:
            all_tasks.extend(mock_data_service.generate_piazza_announcements())
        
        # Slack messages (use mock if no real Slack)
        if self.slack_service and self.user.slack_bot_token and self.user.slack_channel_ids:
            try:
                slack_tasks = self.slack_service.get_tasks_from_messages(self.user.slack_channel_ids)
                all_tasks.extend(slack_tasks)
            except:
                all_tasks.extend(mock_data_service.generate_slack_messages())
        else:
            all_tasks.extend(mock_data_service.generate_slack_messages())
        
        # Remove duplicates and sort by due date
        unique_tasks = self._deduplicate_tasks(all_tasks)
        return sorted(unique_tasks, key=lambda t: (t.due_date, t.priority.value))
    
    def _deduplicate_tasks(self, tasks: List[Task]) -> List[Task]:
        """Remove duplicate tasks based on title and due date"""
        seen = set()
        unique = []
        
        for task in tasks:
            key = (task.title.lower(), task.due_date.date())
            if key not in seen:
                seen.add(key)
                unique.append(task)
        
        return unique
    
    def create_weekly_plan(self) -> List[Task]:
        """
        Create a weekly plan prioritizing tasks.
        This is the core planning function.
        """
        all_tasks = self.gather_all_tasks()
        
        # Filter to upcoming week
        week_end = datetime.now() + timedelta(days=7)
        upcoming_tasks = [t for t in all_tasks if t.due_date <= week_end]
        
        # Prioritize tasks
        prioritized = self._prioritize_tasks(upcoming_tasks)
        
        # Check for conflicts
        self.conflicts = self._detect_conflicts(prioritized)
        
        # Distribute tasks across the week
        weekly_plan = self._distribute_tasks(prioritized)
        
        self.weekly_plan = weekly_plan
        self.last_plan_update = datetime.now()
        
        return weekly_plan
    
    def _prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Prioritize tasks based on urgency, importance, and user preferences"""
        now = datetime.now()
        
        for task in tasks:
            days_until_due = (task.due_date - now).days
            
            # Update priority based on time remaining
            if days_until_due <= 1:
                task.priority = TaskPriority.CRITICAL
            elif days_until_due <= self.preferences.nudge_threshold_days:
                if task.priority == TaskPriority.LOW:
                    task.priority = TaskPriority.MEDIUM
                elif task.priority == TaskPriority.MEDIUM:
                    task.priority = TaskPriority.HIGH
            
            # Check if overdue
            if task.due_date < now and task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.OVERDUE
                task.priority = TaskPriority.CRITICAL
        
        # Sort by priority and due date
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        return sorted(tasks, key=lambda t: (
            priority_order[t.priority],
            t.due_date
        ))
    
    def _detect_conflicts(self, tasks: List[Task]) -> List[Dict]:
        """Detect scheduling conflicts and priority conflicts"""
        conflicts = []
        
        # Check for time conflicts (multiple tasks due same day with high estimated hours)
        daily_hours = {}
        for task in tasks:
            day = task.due_date.date()
            hours = task.estimated_hours or 3.0
            daily_hours[day] = daily_hours.get(day, 0) + hours
        
        for day, hours in daily_hours.items():
            if hours > self.preferences.preferred_study_hours_per_day * 2:
                conflicts.append({
                    "type": "time_conflict",
                    "date": day,
                    "total_hours": hours,
                    "message": f"Too many tasks on {day}: {hours:.1f} hours estimated"
                })
        
        # Check for priority conflicts (multiple critical tasks)
        critical_tasks = [t for t in tasks if t.priority == TaskPriority.CRITICAL]
        if len(critical_tasks) > 3:
            conflicts.append({
                "type": "priority_conflict",
                "count": len(critical_tasks),
                "message": f"Too many critical tasks ({len(critical_tasks)}). Consider reprioritizing."
            })
        
        return conflicts
    
    def _distribute_tasks(self, tasks: List[Task]) -> List[Task]:
        """Distribute tasks across the week based on due dates and estimated hours"""
        distributed = []
        daily_capacity = self.preferences.preferred_study_hours_per_day
        
        # Group tasks by day
        tasks_by_day = {}
        for task in tasks:
            day = task.due_date.date()
            if day not in tasks_by_day:
                tasks_by_day[day] = []
            tasks_by_day[day].append(task)
        
        # Distribute tasks ensuring we don't overload any day
        for day, day_tasks in sorted(tasks_by_day.items()):
            day_hours = 0
            for task in sorted(day_tasks, key=lambda t: t.priority.value):
                task_hours = task.estimated_hours or 3.0
                
                # If adding this task would exceed capacity, mark for earlier scheduling
                if day_hours + task_hours > daily_capacity * 1.5:
                    # Suggest moving to previous day if possible
                    prev_day = day - timedelta(days=1)
                    if prev_day >= datetime.now().date():
                        task.due_date = datetime.combine(prev_day, task.due_date.time())
                
                day_hours += task_hours
                distributed.append(task)
        
        return distributed
    
    def revise_plan(self, new_deadlines: Optional[List[Deadline]] = None) -> List[Task]:
        """
        Revise the weekly plan when deadlines shift.
        This is the core revision function.
        """
        # Gather fresh tasks
        all_tasks = self.gather_all_tasks()
        
        # If new deadlines provided, incorporate them
        if new_deadlines and self.canvas_service:
            new_tasks = self.canvas_service.get_tasks_from_deadlines(new_deadlines)
            all_tasks.extend(new_tasks)
        
        # Re-plan
        return self.create_weekly_plan()
    
    def check_academic_health(self) -> Dict:
        """Monitor academic health and identify risks"""
        all_tasks = self.gather_all_tasks()
        now = datetime.now()
        
        overdue = [t for t in all_tasks if t.status == TaskStatus.OVERDUE]
        critical_upcoming = [
            t for t in all_tasks 
            if t.priority == TaskPriority.CRITICAL 
            and t.due_date > now 
            and (t.due_date - now).days <= 2
        ]
        
        # Calculate workload for next 7 days
        week_tasks = [t for t in all_tasks if (t.due_date - now).days <= 7]
        total_hours = sum(t.estimated_hours or 3.0 for t in week_tasks)
        daily_avg = total_hours / 7 if week_tasks else 0
        
        health_score = 100
        warnings = []
        
        if overdue:
            health_score -= len(overdue) * 10
            warnings.append(f"{len(overdue)} overdue task(s)")
        
        if len(critical_upcoming) > 2:
            health_score -= 20
            warnings.append(f"{len(critical_upcoming)} critical tasks due soon")
        
        if daily_avg > self.preferences.preferred_study_hours_per_day * 1.5:
            health_score -= 15
            warnings.append(f"High workload: {daily_avg:.1f} hours/day average")
        
        health_status = "healthy" if health_score >= 80 else "at_risk" if health_score >= 60 else "critical"
        
        return {
            "score": max(0, health_score),
            "status": health_status,
            "warnings": warnings,
            "overdue_count": len(overdue),
            "critical_upcoming": len(critical_upcoming),
            "weekly_hours": total_hours,
            "daily_average": daily_avg
        }
    
    def should_nudge(self) -> bool:
        """Determine if user should be nudged"""
        health = self.check_academic_health()
        
        # Nudge conditions
        if health["status"] == "critical":
            return True
        if health["overdue_count"] > 0:
            return True
        
        # Check for tasks approaching nudge threshold
        all_tasks = self.gather_all_tasks()
        now = datetime.now()
        approaching_deadlines = [
            t for t in all_tasks
            if t.status == TaskStatus.PENDING
            and (t.due_date - now).days <= self.preferences.nudge_threshold_days
            and t.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL]
        ]
        
        return len(approaching_deadlines) > 0
    
    def get_clarifying_questions(self) -> List[str]:
        """
        Generate clarifying questions when priorities conflict.
        This helps the agent ask for user input.
        """
        questions = []
        
        if not self.conflicts:
            return questions
        
        for conflict in self.conflicts:
            if conflict["type"] == "time_conflict":
                questions.append(
                    f"You have {conflict['total_hours']:.1f} hours of work scheduled for {conflict['date']}. "
                    f"Which tasks are most important to complete?"
                )
            elif conflict["type"] == "priority_conflict":
                questions.append(
                    f"You have {conflict['count']} critical tasks. "
                    f"Which ones can be deprioritized or extended?"
                )
        
        return questions
    
    def make_autonomous_decisions(self) -> List[Dict]:
        """
        Make autonomous decisions to keep the user academically safe.
        This is the core agentic decision-making function.
        """
        decisions = []
        all_tasks = self.gather_all_tasks()
        health = self.check_academic_health()
        
        # Decision 1: Auto-prioritize overdue tasks
        overdue_tasks = [t for t in all_tasks if t.status == TaskStatus.OVERDUE]
        if overdue_tasks:
            for task in overdue_tasks:
                if task.priority != TaskPriority.CRITICAL:
                    task.priority = TaskPriority.CRITICAL
                    decisions.append({
                        "type": "auto_prioritize",
                        "task": task.title,
                        "reason": "Task is overdue",
                        "action": f"Set priority to CRITICAL"
                    })
        
        # Decision 2: Auto-adjust priorities based on proximity to deadline
        now = datetime.now()
        for task in all_tasks:
            if task.status == TaskStatus.PENDING:
                days_until = (task.due_date - now).days
                
                # Escalate priority if deadline is very close
                if days_until <= 1 and task.priority != TaskPriority.CRITICAL:
                    old_priority = task.priority
                    task.priority = TaskPriority.CRITICAL
                    decisions.append({
                        "type": "auto_escalate",
                        "task": task.title,
                        "reason": f"Due in {days_until} day(s)",
                        "action": f"Escalated from {old_priority.value} to CRITICAL"
                    })
                elif days_until <= 2 and task.priority == TaskPriority.LOW:
                    task.priority = TaskPriority.MEDIUM
                    decisions.append({
                        "type": "auto_escalate",
                        "task": task.title,
                        "reason": f"Due in {days_until} days",
                        "action": "Escalated from LOW to MEDIUM"
                    })
        
        # Decision 3: Suggest breaking down large tasks
        for task in all_tasks:
            if task.estimated_hours and task.estimated_hours > 8:
                if task.status == TaskStatus.PENDING:
                    decisions.append({
                        "type": "suggest_breakdown",
                        "task": task.title,
                        "reason": f"Large task ({task.estimated_hours}h estimated)",
                        "action": "Consider breaking into smaller subtasks"
                    })
        
        # Decision 4: Auto-create buffer time for critical tasks
        critical_tasks = [t for t in all_tasks if t.priority == TaskPriority.CRITICAL and t.status == TaskStatus.PENDING]
        if len(critical_tasks) > 3:
            decisions.append({
                "type": "suggest_buffer",
                "reason": f"{len(critical_tasks)} critical tasks detected",
                "action": "Consider requesting extensions or reprioritizing"
            })
        
        return decisions
    
    def execute_autonomous_actions(self) -> Dict:
        """
        Execute autonomous actions based on current state.
        Returns summary of actions taken.
        """
        actions_taken = {
            "decisions_made": [],
            "plans_created": False,
            "notifications_sent": False,
            "study_plans_created": False
        }
        
        # Make autonomous decisions
        decisions = self.make_autonomous_decisions()
        actions_taken["decisions_made"] = decisions
        
        # Check if plan needs updating
        if not self.weekly_plan or not self.last_plan_update:
            self.create_weekly_plan()
            actions_taken["plans_created"] = True
        
        # Check health and take action
        health = self.check_academic_health()
        if health["status"] == "critical":
            # Emergency plan already handled in agent loop, but mark as action
            actions_taken["notifications_sent"] = True
        
        return actions_taken

