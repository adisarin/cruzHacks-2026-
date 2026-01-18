from datetime import datetime
from typing import List, Dict
from app.models.task import Task
from app.models.user import User
from app.services.slack_service import SlackService
from app.services.calendar_service import CalendarService


class NotificationService:
    """Service for sending nudges and notifications to users"""
    
    def __init__(self, user: User):
        self.user = user
        self.slack_service = SlackService(user.slack_bot_token) if user.slack_bot_token else None
        self.calendar_service = CalendarService(
            user.google_calendar_token,
            user.apple_calendar_enabled
        ) if user.google_calendar_token else None
    
    def send_nudge(self, message: str, priority: str = "medium") -> bool:
        """Send a nudge notification to the user"""
        # In a real implementation, this would:
        # - Send email
        # - Send Slack message
        # - Send push notification
        # - Create calendar reminder
        
        success = True
        
        # Slack notification
        if self.slack_service and self.user.slack_channel_ids:
            # Send to first configured channel (or DM channel if available)
            channel_id = self.user.slack_channel_ids[0]
            self.slack_service.send_notification(channel_id, message)
        
        # Calendar reminder
        if self.calendar_service:
            # Create a reminder event
            reminder_time = datetime.now()
            end_time = reminder_time.replace(minute=reminder_time.minute + 5)
            
            self.calendar_service.create_event(
                title=f"SlugPilot: {message[:50]}",
                start_time=reminder_time,
                end_time=end_time,
                description=message
            )
        
        # Log notification (in real app, would send via email/push/etc)
        print(f"[NOTIFICATION] {priority.upper()}: {message}")
        
        return success
    
    def generate_nudge_message(self, tasks: List[Task], health_status: Dict) -> str:
        """Generate a personalized nudge message"""
        overdue = [t for t in tasks if t.status.value == "overdue"]
        critical = [t for t in tasks if t.priority.value == "critical"]
        
        if overdue:
            return (
                f"⚠️ You have {len(overdue)} overdue task(s)! "
                f"Let's get back on track. Most urgent: {overdue[0].title}"
            )
        
        if critical:
            return (
                f"🚨 {len(critical)} critical task(s) due soon. "
                f"Up next: {critical[0].title} due {critical[0].due_date.strftime('%m/%d')}"
            )
        
        if health_status["status"] == "at_risk":
            return (
                f"📊 Your academic health is at risk. "
                f"Weekly workload: {health_status['weekly_hours']:.1f} hours. "
                f"Consider adjusting your schedule."
            )
        
        # Positive nudge
        upcoming = [t for t in tasks if t.status.value == "pending"][:3]
        if upcoming:
            return (
                f"✅ You're on track! Upcoming: {upcoming[0].title} "
                f"due {upcoming[0].due_date.strftime('%m/%d')}"
            )
        
        return "Keep up the great work! 🎓"
    
    def send_weekly_summary(self, weekly_plan: List[Task], health: Dict) -> bool:
        """Send a weekly summary to the user"""
        message = f"""
📅 Weekly Summary - {datetime.now().strftime('%B %d, %Y')}

Academic Health: {health['status'].upper()} ({health['score']}/100)
• Overdue tasks: {health['overdue_count']}
• Critical upcoming: {health['critical_upcoming']}
• Weekly hours: {health['weekly_hours']:.1f}h ({health['daily_average']:.1f}h/day)

This Week's Plan:
"""
        for i, task in enumerate(weekly_plan[:10], 1):  # Top 10 tasks
            message += f"{i}. {task.title} - Due {task.due_date.strftime('%m/%d')} ({task.priority.value})\n"
        
        if len(weekly_plan) > 10:
            message += f"... and {len(weekly_plan) - 10} more tasks\n"
        
        return self.send_nudge(message, priority="low")

