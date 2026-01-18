import requests
from typing import List, Optional
from datetime import datetime
from app.models.deadline import Deadline
from app.models.task import Task, TaskPriority


class CanvasService:
    """Service for interacting with Canvas LMS API"""
    
    def __init__(self, api_token: Optional[str] = None, base_url: str = "https://canvas.ucsc.edu/api/v1"):
        self.api_token = api_token
        self.base_url = base_url
        if api_token:
            self.headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
        else:
            self.headers = {}
    
    def get_courses(self) -> List[dict]:
        """Fetch all enrolled courses"""
        try:
            response = requests.get(
                f"{self.base_url}/courses",
                headers=self.headers,
                params={"enrollment_state": "active"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching courses: {e}")
            return []
    
    def get_assignments(self, course_id: Optional[str] = None) -> List[dict]:
        """Fetch assignments from all courses or a specific course"""
        assignments = []
        
        if course_id:
            courses = [{"id": course_id}]
        else:
            courses = self.get_courses()
        
        for course in courses:
            try:
                response = requests.get(
                    f"{self.base_url}/courses/{course['id']}/assignments",
                    headers=self.headers,
                    params={"bucket": "upcoming"}
                )
                response.raise_for_status()
                course_assignments = response.json()
                for assignment in course_assignments:
                    assignment["course_name"] = course.get("name", "Unknown")
                assignments.extend(course_assignments)
            except Exception as e:
                print(f"Error fetching assignments for course {course.get('id')}: {e}")
                continue
        
        return assignments
    
    def get_deadlines(self, days_ahead: int = 30) -> List[Deadline]:
        """Convert Canvas assignments to Deadline objects"""
        assignments = self.get_assignments()
        
        # If no API token or no assignments, use mock data for demo
        if not self.api_token or not assignments:
            from app.services.mock_data_service import mock_data_service
            return mock_data_service.generate_canvas_deadlines(10)
        
        deadlines = []
        cutoff_date = datetime.now().replace(hour=23, minute=59, second=59)
        # Note: In real implementation, add days_ahead days to cutoff_date
        
        for assignment in assignments:
            if assignment.get("due_at"):
                due_date = datetime.fromisoformat(assignment["due_at"].replace("Z", "+00:00"))
                
                deadline = Deadline(
                    title=assignment.get("name", "Untitled Assignment"),
                    course=assignment.get("course_name", "Unknown Course"),
                    due_date=due_date,
                    assignment_type=assignment.get("submission_types", ["none"])[0] if assignment.get("submission_types") else None,
                    points=assignment.get("points_possible"),
                    description=assignment.get("description"),
                    canvas_assignment_id=str(assignment.get("id"))
                )
                deadlines.append(deadline)
        
        return sorted(deadlines, key=lambda d: d.due_date)
    
    def get_tasks_from_deadlines(self, deadlines: Optional[List[Deadline]] = None) -> List[Task]:
        """Convert deadlines to tasks"""
        if deadlines is None:
            deadlines = self.get_deadlines()
        
        tasks = []
        for deadline in deadlines:
            # Determine priority based on days until due date
            days_until_due = (deadline.due_date - datetime.now()).days
            
            if days_until_due <= 1:
                priority = TaskPriority.CRITICAL
            elif days_until_due <= 3:
                priority = TaskPriority.HIGH
            elif days_until_due <= 7:
                priority = TaskPriority.MEDIUM
            else:
                priority = TaskPriority.LOW
            
            task = Task(
                title=deadline.title,
                description=deadline.description,
                course=deadline.course,
                due_date=deadline.due_date,
                priority=priority,
                source="canvas",
                estimated_hours=self._estimate_hours(deadline)
            )
            tasks.append(task)
        
        return tasks
    
    def _estimate_hours(self, deadline: Deadline) -> float:
        """Estimate hours needed based on assignment type and points"""
        base_hours = {
            "homework": 3.0,
            "assignment": 4.0,
            "project": 10.0,
            "exam": 0.0,  # Exams don't need prep time in task form
            "quiz": 1.0,
        }
        
        assignment_type = (deadline.assignment_type or "assignment").lower()
        base = base_hours.get(assignment_type, 3.0)
        
        # Adjust based on points
        if deadline.points:
            if deadline.points > 50:
                base *= 1.5
            elif deadline.points > 100:
                base *= 2.0
        
        return base

