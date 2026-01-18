from typing import List, Optional
from datetime import datetime, timedelta
from app.models.task import Task, TaskPriority
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackService:
    """Service for monitoring Slack channels for announcements"""
    
    def __init__(self, bot_token: str, workspace: Optional[str] = None):
        self.bot_token = bot_token
        self.workspace = workspace
        self.client = WebClient(token=bot_token)
    
    def get_recent_messages(self, channel_ids: List[str], hours: int = 24) -> List[dict]:
        """Fetch recent messages from specified Slack channels"""
        messages = []
        cutoff_time = (datetime.now() - timedelta(hours=hours)).timestamp()
        
        for channel_id in channel_ids:
            try:
                response = self.client.conversations_history(
                    channel=channel_id,
                    oldest=str(cutoff_time),
                    limit=100
                )
                
                for message in response.get('messages', []):
                    message['channel_id'] = channel_id
                    messages.append(message)
            except SlackApiError as e:
                print(f"Error fetching messages from channel {channel_id}: {e}")
                continue
        
        return messages
    
    def get_tasks_from_messages(self, channel_ids: List[str]) -> List[Task]:
        """Convert Slack messages to tasks if they contain deadline information"""
        messages = self.get_recent_messages(channel_ids)
        tasks = []
        
        deadline_keywords = ['due', 'deadline', 'due date', 'submit', 'assignment', 'homework']
        
        for message in messages:
            text = message.get('text', '').lower()
            
            # Check if message mentions deadlines
            if any(keyword in text for keyword in deadline_keywords):
                # Extract course name from channel or message
                channel_name = message.get('channel_id', 'unknown')
                
                task = Task(
                    title=f"Slack: {message.get('text', '')[:50]}",
                    description=message.get('text', ''),
                    course=channel_name,
                    due_date=datetime.now() + timedelta(days=2),  # Placeholder - would parse actual date
                    priority=TaskPriority.MEDIUM,
                    source="slack"
                )
                tasks.append(task)
        
        return tasks
    
    def send_notification(self, channel_id: str, message: str) -> bool:
        """Send a notification message to a Slack channel"""
        try:
            self.client.chat_postMessage(
                channel=channel_id,
                text=message
            )
            return True
        except SlackApiError as e:
            print(f"Error sending Slack notification: {e}")
            return False

