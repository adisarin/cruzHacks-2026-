from typing import List, Optional
from datetime import datetime, timedelta
from app.models.task import Task, TaskPriority
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json


class CalendarService:
    """Service for syncing with Google Calendar and Apple Calendar"""
    
    def __init__(self, google_credentials: Optional[dict] = None, apple_calendar_enabled: bool = False):
        self.google_credentials = google_credentials
        self.apple_calendar_enabled = apple_calendar_enabled
        self.service = None
        
        if google_credentials:
            self._initialize_google_calendar()
    
    def _initialize_google_calendar(self):
        """Initialize Google Calendar API service"""
        try:
            creds = Credentials.from_authorized_user_info(self.google_credentials)
            self.service = build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"Error initializing Google Calendar: {e}")
            self.service = None
    
    def get_upcoming_events(self, days_ahead: int = 30) -> List[dict]:
        """Fetch upcoming events from Google Calendar"""
        if not self.service:
            return []
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            return []
    
    def get_tasks_from_calendar(self) -> List[Task]:
        """Convert calendar events to tasks"""
        events = self.get_upcoming_events()
        tasks = []
        
        for event in events:
            start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
            if not start:
                continue
            
            # Parse datetime
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                start_dt = datetime.fromisoformat(start)
            
            # Skip past events
            if start_dt < datetime.now():
                continue
            
            # Determine if it's a deadline or event
            summary = event.get('summary', 'Untitled Event')
            description = event.get('description', '')
            
            # Check if it looks like a deadline/assignment
            is_deadline = any(keyword in summary.lower() for keyword in 
                            ['due', 'deadline', 'assignment', 'homework', 'project', 'exam'])
            
            if is_deadline or 'due' in description.lower():
                priority = TaskPriority.HIGH if is_deadline else TaskPriority.MEDIUM
                
                task = Task(
                    title=summary,
                    description=description,
                    due_date=start_dt,
                    priority=priority,
                    source="calendar",
                    estimated_hours=1.0  # Default for calendar events
                )
                tasks.append(task)
        
        return tasks
    
    def create_event(self, title: str, start_time: datetime, end_time: datetime, 
                    description: Optional[str] = None) -> Optional[dict]:
        """Create a new event in Google Calendar"""
        if not self.service:
            return None
        
        try:
            event = {
                'summary': title,
                'description': description or '',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Los_Angeles',
                },
            }
            
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return created_event
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None
    
    def sync_study_sessions(self, study_sessions: List[dict]) -> List[dict]:
        """Sync study sessions to calendar"""
        created_events = []
        for session in study_sessions:
            start_time = datetime.fromisoformat(session['scheduled_time'])
            end_time = start_time + timedelta(hours=session['duration_hours'])
            
            event = self.create_event(
                title=f"Study: {session['course']} - {session['topic']}",
                start_time=start_time,
                end_time=end_time,
                description=f"Materials: {', '.join(session.get('materials', []))}"
            )
            
            if event:
                created_events.append(event)
        
        return created_events

