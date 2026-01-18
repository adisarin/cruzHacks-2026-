"""
Mock Data Service for Demo Purposes
Generates realistic student data to demonstrate SlugPilot functionality
"""
from datetime import datetime, timedelta
from typing import List
import random
from app.models.deadline import Deadline
from app.models.task import Task, TaskPriority, TaskStatus


class MockDataService:
    """Generates realistic mock data for demo purposes"""
    
    COURSES = [
        "CS101 - Introduction to Computer Science",
        "MATH19A - Calculus for Science",
        "PHYS5A - Physics for Scientists",
        "CSE30 - Programming Abstractions",
        "STAT5 - Statistics",
    ]
    
    ASSIGNMENT_TYPES = [
        "homework", "assignment", "project", "lab", "quiz", "exam", "midterm", "final"
    ]
    
    def __init__(self):
        self.base_date = datetime.now()
    
    def generate_canvas_deadlines(self, num_assignments: int = 10) -> List[Deadline]:
        """Generate realistic Canvas deadlines"""
        deadlines = []
        
        for i in range(num_assignments):
            course = random.choice(self.COURSES)
            assignment_type = random.choice(self.ASSIGNMENT_TYPES)
            
            # Vary due dates - some past, some upcoming
            days_offset = random.randint(-5, 14)  # -5 to +14 days
            due_date = self.base_date + timedelta(days=days_offset, hours=random.randint(9, 23))
            
            # Generate realistic assignment names
            if assignment_type == "homework":
                title = f"Homework {random.randint(1, 10)}"
            elif assignment_type == "project":
                title = f"Project {random.randint(1, 3)}: {random.choice(['Web App', 'Data Analysis', 'Algorithm Design'])}"
            elif assignment_type in ["midterm", "exam", "final"]:
                title = f"{assignment_type.capitalize()} Exam"
            elif assignment_type == "quiz":
                title = f"Quiz {random.randint(1, 5)}"
            else:
                title = f"{assignment_type.capitalize()} {random.randint(1, 5)}"
            
            # Points based on type
            if assignment_type in ["midterm", "exam", "final"]:
                points = 100.0
            elif assignment_type == "project":
                points = random.choice([50.0, 75.0, 100.0])
            else:
                points = random.choice([10.0, 15.0, 20.0, 25.0])
            
            deadline = Deadline(
                title=title,
                course=course,
                due_date=due_date,
                assignment_type=assignment_type,
                points=points,
                description=f"Complete {title} for {course}",
                canvas_assignment_id=f"mock_{i}"
            )
            deadlines.append(deadline)
        
        return sorted(deadlines, key=lambda d: d.due_date)
    
    def generate_calendar_events(self, num_events: int = 5) -> List[Task]:
        """Generate realistic calendar events that are deadlines"""
        tasks = []
        
        event_types = [
            ("Study Session", "Study for upcoming exam"),
            ("Group Meeting", "Project group meeting"),
            ("Office Hours", "Professor office hours"),
            ("Review Session", "Exam review session"),
        ]
        
        for i in range(num_events):
            event_name, description = random.choice(event_types)
            course = random.choice(self.COURSES)
            days_offset = random.randint(0, 7)
            event_time = self.base_date + timedelta(days=days_offset, hours=random.randint(9, 17))
            
            task = Task(
                title=f"{event_name}: {course}",
                description=description,
                course=course,
                due_date=event_time,
                priority=TaskPriority.MEDIUM,
                source="calendar",
                estimated_hours=1.0
            )
            tasks.append(task)
        
        return tasks
    
    def generate_piazza_announcements(self) -> List[Task]:
        """Generate Piazza-style announcements with deadlines"""
        tasks = []
        
        announcements = [
            ("Deadline Extended", "The deadline for Assignment 3 has been extended to Friday"),
            ("New Assignment Posted", "Assignment 4 is now available, due next Monday"),
            ("Exam Date Changed", "Midterm exam moved to next Wednesday"),
            ("Office Hours Cancelled", "This week's office hours cancelled, rescheduled for Friday"),
        ]
        
        for title, content in announcements:
            course = random.choice(self.COURSES)
            # Parse approximate date from content or use near future
            days_offset = random.randint(1, 5)
            due_date = self.base_date + timedelta(days=days_offset)
            
            task = Task(
                title=f"Piazza: {title}",
                description=content,
                course=course,
                due_date=due_date,
                priority=TaskPriority.MEDIUM,
                source="piazza"
            )
            tasks.append(task)
        
        return tasks
    
    def generate_slack_messages(self) -> List[Task]:
        """Generate Slack-style messages with deadlines"""
        tasks = []
        
        messages = [
            ("Assignment Due", "Don't forget Assignment 2 is due tomorrow at 11:59pm"),
            ("Project Update", "Project milestone due Friday, make sure to submit"),
            ("Study Group", "Study group meeting tomorrow at 3pm for midterm prep"),
        ]
        
        for title, content in messages:
            course = random.choice(self.COURSES)
            days_offset = random.randint(1, 3)
            due_date = self.base_date + timedelta(days=days_offset, hours=23, minutes=59)
            
            task = Task(
                title=f"Slack: {title}",
                description=content,
                course=course,
                due_date=due_date,
                priority=TaskPriority.HIGH,
                source="slack"
            )
            tasks.append(task)
        
        return tasks
    
    def get_all_mock_tasks(self) -> List[Task]:
        """Get all mock tasks from all sources"""
        all_tasks = []
        
        # Convert deadlines to tasks
        deadlines = self.generate_canvas_deadlines(10)
        for deadline in deadlines:
            days_until = (deadline.due_date - self.base_date).days
            
            if days_until < 0:
                priority = TaskPriority.CRITICAL
                status = TaskStatus.OVERDUE
            elif days_until <= 1:
                priority = TaskPriority.CRITICAL
                status = TaskStatus.PENDING
            elif days_until <= 3:
                priority = TaskPriority.HIGH
                status = TaskStatus.PENDING
            elif days_until <= 7:
                priority = TaskPriority.MEDIUM
                status = TaskStatus.PENDING
            else:
                priority = TaskPriority.LOW
                status = TaskStatus.PENDING
            
            # Estimate hours
            if deadline.assignment_type in ["midterm", "exam", "final"]:
                estimated_hours = 0  # Exams don't need prep time in task form
            elif deadline.assignment_type == "project":
                estimated_hours = random.choice([8.0, 10.0, 12.0])
            elif deadline.assignment_type == "homework":
                estimated_hours = random.choice([2.0, 3.0, 4.0])
            else:
                estimated_hours = random.choice([1.0, 2.0, 3.0])
            
            task = Task(
                title=deadline.title,
                description=deadline.description,
                course=deadline.course,
                due_date=deadline.due_date,
                priority=priority,
                status=status,
                source="canvas",
                estimated_hours=estimated_hours
            )
            all_tasks.append(task)
        
        # Add calendar events
        all_tasks.extend(self.generate_calendar_events(5))
        
        # Add Piazza announcements
        all_tasks.extend(self.generate_piazza_announcements())
        
        # Add Slack messages
        all_tasks.extend(self.generate_slack_messages())
        
        return sorted(all_tasks, key=lambda t: t.due_date)


# Global instance
mock_data_service = MockDataService()

