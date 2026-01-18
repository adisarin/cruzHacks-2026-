from datetime import datetime, timedelta
from typing import List, Optional
from app.models.study_plan import StudyPlan, StudySession
from app.models.deadline import Deadline
from app.models.user import UserPreferences


class StudyPlanGenerator:
    """Generates study plans for exams and major assignments"""
    
    def __init__(self, preferences: UserPreferences):
        self.preferences = preferences
    
    def generate_study_plan(
        self,
        course: str,
        exam_date: datetime,
        exam_title: str,
        topics: Optional[List[str]] = None,
        total_study_hours: Optional[float] = None
    ) -> StudyPlan:
        """
        Generate a study plan for an upcoming exam.
        
        Args:
            course: Course name
            exam_date: Date/time of the exam
            exam_title: Title of the exam
            topics: List of topics to study (optional)
            total_study_hours: Total hours to allocate (optional, will estimate if not provided)
        """
        # Calculate days until exam
        days_until_exam = (exam_date - datetime.now()).days
        
        # Estimate total study hours if not provided
        if total_study_hours is None:
            total_study_hours = self._estimate_study_hours(exam_title, days_until_exam)
        
        # Generate study sessions
        sessions = self._create_study_sessions(
            course=course,
            exam_date=exam_date,
            topics=topics or [],
            total_hours=total_study_hours
        )
        
        study_plan = StudyPlan(
            course=course,
            exam_date=exam_date,
            exam_title=exam_title,
            sessions=sessions,
            total_hours=total_study_hours,
            status="active"
        )
        
        return study_plan
    
    def _estimate_study_hours(self, exam_title: str, days_until: int) -> float:
        """Estimate total study hours needed"""
        # Base hours based on exam type
        base_hours = {
            "midterm": 12.0,
            "final": 20.0,
            "quiz": 3.0,
            "exam": 10.0,
        }
        
        exam_lower = exam_title.lower()
        base = 10.0  # default
        
        for exam_type, hours in base_hours.items():
            if exam_type in exam_lower:
                base = hours
                break
        
        # Adjust based on days available
        if days_until < 3:
            # Cram mode - more hours per day
            return base * 1.2
        elif days_until >= 7:
            # Spread out - can be more efficient
            return base * 0.9
        
        return base
    
    def _create_study_sessions(
        self,
        course: str,
        exam_date: datetime,
        topics: List[str],
        total_hours: float
    ) -> List[StudySession]:
        """Create study sessions distributed before the exam"""
        sessions = []
        days_until = (exam_date - datetime.now()).days
        
        if days_until <= 0:
            # Exam is today or past - create immediate session
            session = StudySession(
                course=course,
                topic="Final review",
                duration_hours=min(2.0, total_hours),
                scheduled_time=datetime.now() + timedelta(hours=1),
                materials=["All topics"]
            )
            sessions.append(session)
            return sessions
        
        # Distribute sessions across available days
        hours_per_session = 2.0  # Ideal session length
        num_sessions = max(1, int(total_hours / hours_per_session))
        
        # Don't schedule more sessions than days available
        num_sessions = min(num_sessions, days_until)
        
        # Distribute topics across sessions
        if topics:
            topics_per_session = max(1, len(topics) // num_sessions)
        else:
            topics_per_session = 1
        
        # Create sessions
        for i in range(num_sessions):
            # Calculate session date (spread evenly before exam)
            days_before_exam = days_until - (i * days_until // num_sessions)
            session_date = exam_date - timedelta(days=days_before_exam)
            
            # Set preferred study time
            preferred_time = self._get_preferred_time(session_date)
            
            # Determine topic
            if topics:
                start_idx = i * topics_per_session
                end_idx = min(start_idx + topics_per_session, len(topics))
                session_topics = topics[start_idx:end_idx]
                topic = ", ".join(session_topics)
                materials = [f"Review: {t}" for t in session_topics]
            else:
                topic = f"Study session {i+1}"
                materials = ["Course materials", "Practice problems"]
            
            # Calculate duration (last session might be shorter)
            if i == num_sessions - 1:
                remaining_hours = total_hours - sum(s.duration_hours for s in sessions)
                duration = max(1.0, min(hours_per_session, remaining_hours))
            else:
                duration = hours_per_session
            
            session = StudySession(
                course=course,
                topic=topic,
                duration_hours=duration,
                scheduled_time=preferred_time,
                materials=materials
            )
            sessions.append(session)
        
        return sessions
    
    def _get_preferred_time(self, date: datetime) -> datetime:
        """Get preferred study time based on user preferences"""
        # Parse preferred times (format: "09:00-12:00")
        preferred_times = self.preferences.preferred_study_times
        
        if preferred_times:
            # Use first preferred time slot
            time_str = preferred_times[0].split("-")[0]  # "09:00"
            hour, minute = map(int, time_str.split(":"))
        else:
            # Default to 10 AM
            hour, minute = 10, 0
        
        return datetime.combine(date.date(), datetime.min.time().replace(hour=hour, minute=minute))
    
    def auto_create_for_upcoming_exams(
        self,
        deadlines: List[Deadline],
        days_before: Optional[int] = None
    ) -> List[StudyPlan]:
        """Automatically create study plans for upcoming exams"""
        if days_before is None:
            days_before = self.preferences.study_plan_days_before_exam
        
        now = datetime.now()
        study_plans = []
        
        # Find exam deadlines
        exam_keywords = ["exam", "midterm", "final", "test", "quiz"]
        exam_deadlines = [
            d for d in deadlines
            if any(keyword in d.title.lower() for keyword in exam_keywords)
            and d.due_date > now
            and (d.due_date - now).days <= days_before + 1
        ]
        
        for deadline in exam_deadlines:
            # Check if we should create a plan (within threshold)
            days_until = (deadline.due_date - now).days
            
            if days_until <= days_before:
                plan = self.generate_study_plan(
                    course=deadline.course,
                    exam_date=deadline.due_date,
                    exam_title=deadline.title
                )
                study_plans.append(plan)
        
        return study_plans

