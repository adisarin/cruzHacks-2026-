import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.agent.slugpilot_agent import SlugPilotAgent
from app.agent.study_plan_generator import StudyPlanGenerator
from app.agent.notification_service import NotificationService
from app.models.user import User


class AgentLoop:
    """
    Autonomous agent loop that runs continuously.
    This is the core agentic component that makes SlugPilot autonomous.
    
    The agent:
    - Runs continuously in the background
    - Monitors deadlines and academic health
    - Creates and revises plans autonomously
    - Sends proactive nudges
    - Auto-creates study plans
    - Makes decisions without user input
    """
    
    def __init__(self, agent: SlugPilotAgent):
        self.agent = agent
        self.is_running = False
        self.last_check: Optional[datetime] = None
        self.last_plan_creation: Optional[datetime] = None
        self.last_nudge: Optional[datetime] = None
        self.action_history: List[Dict] = []
        self.notification_service = NotificationService(agent.user)
    
    async def start(self):
        """Start the autonomous agent loop"""
        self.is_running = True
        print(f"[AgentLoop] Starting autonomous agent for user: {self.agent.user.email}")
        
        while self.is_running:
            try:
                await self._run_cycle()
                # Run cycle every 15 minutes (configurable)
                await asyncio.sleep(900)  # 15 minutes
            except Exception as e:
                print(f"[AgentLoop] Error in cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop(self):
        """Stop the autonomous agent loop"""
        self.is_running = False
        print(f"[AgentLoop] Stopping agent for user: {self.agent.user.email}")
    
    async def _run_cycle(self):
        """Execute one cycle of the agent loop"""
        cycle_start = datetime.now()
        print(f"[AgentLoop] Running cycle at {cycle_start}")
        
        actions_taken = []
        
        # 1. Gather current state
        all_tasks = self.agent.gather_all_tasks()
        health = self.agent.check_academic_health()
        
        # 2. Make autonomous decisions
        autonomous_decisions = self.agent.make_autonomous_decisions()
        if autonomous_decisions:
            print(f"[AgentLoop] Made {len(autonomous_decisions)} autonomous decisions")
            actions_taken.append({
                "action": "autonomous_decisions",
                "decisions": autonomous_decisions,
                "count": len(autonomous_decisions),
                "timestamp": cycle_start.isoformat()
            })
        
        # 3. Check if plan needs updating (daily or if deadlines changed)
        should_update_plan = self._should_update_plan()
        if should_update_plan:
            print("[AgentLoop] Updating weekly plan...")
            plan = self.agent.create_weekly_plan()
            self.last_plan_creation = cycle_start
            actions_taken.append({
                "action": "plan_updated",
                "tasks_count": len(plan),
                "timestamp": cycle_start.isoformat()
            })
        
        # 4. Check for deadline shifts and revise plan if needed
        deadline_shifts = self._detect_deadline_shifts(all_tasks)
        if deadline_shifts:
            print(f"[AgentLoop] Detected {len(deadline_shifts)} deadline shifts, revising plan...")
            revised_plan = self.agent.revise_plan()
            actions_taken.append({
                "action": "plan_revised",
                "reason": "deadline_shifts",
                "shifts": deadline_shifts,
                "timestamp": cycle_start.isoformat()
            })
        
        # 5. Auto-create study plans for upcoming exams
        if self.agent.user.preferences.auto_create_study_plans:
            study_plans_created = await self._auto_create_study_plans()
            if study_plans_created:
                actions_taken.append({
                    "action": "study_plans_created",
                    "count": len(study_plans_created),
                    "timestamp": cycle_start.isoformat()
                })
        
        # 6. Check academic health and take autonomous actions
        health_actions = await self._handle_academic_health(health, all_tasks)
        actions_taken.extend(health_actions)
        
        # 7. Send proactive nudges if needed
        nudge_actions = await self._send_proactive_nudges(all_tasks, health)
        actions_taken.extend(nudge_actions)
        
        # 8. Handle conflicts autonomously
        conflict_actions = await self._handle_conflicts_autonomously()
        actions_taken.extend(conflict_actions)
        
        # 8. Record cycle
        self.last_check = cycle_start
        if actions_taken:
            self.action_history.extend(actions_taken)
            # Keep only last 100 actions
            self.action_history = self.action_history[-100:]
        
        print(f"[AgentLoop] Cycle complete. Actions taken: {len(actions_taken)}")
    
    def _should_update_plan(self) -> bool:
        """Determine if weekly plan should be updated"""
        # Update daily, or if plan is older than 24 hours
        if self.last_plan_creation is None:
            return True
        
        hours_since_update = (datetime.now() - self.last_plan_creation).total_seconds() / 3600
        return hours_since_update >= 24
    
    def _detect_deadline_shifts(self, current_tasks: List) -> List[Dict]:
        """Detect if deadlines have shifted (simplified - would compare with stored state)"""
        # In a real implementation, would compare with stored previous state
        # For now, return empty list (would need state persistence)
        return []
    
    async def _auto_create_study_plans(self) -> List:
        """Automatically create study plans for upcoming exams"""
        if not self.agent.canvas_service:
            return []
        
        try:
            deadlines = self.agent.canvas_service.get_deadlines()
            generator = StudyPlanGenerator(self.agent.preferences)
            study_plans = generator.auto_create_for_upcoming_exams(deadlines)
            
            # Sync to calendar
            if study_plans and self.agent.calendar_service:
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
                    self.agent.calendar_service.sync_study_sessions(sessions_data)
            
            return study_plans
        except Exception as e:
            print(f"[AgentLoop] Error creating study plans: {e}")
            return []
    
    async def _handle_academic_health(self, health: Dict, tasks: List) -> List[Dict]:
        """Autonomously handle academic health issues"""
        actions = []
        
        # If health is critical, take immediate action
        if health["status"] == "critical":
            # Create emergency plan
            print("[AgentLoop] Critical health detected - creating emergency plan")
            emergency_plan = self.agent.create_weekly_plan()
            
            # Send urgent notification
            message = (
                f"🚨 URGENT: Your academic health is critical ({health['score']}/100). "
                f"I've created an emergency plan with {len(emergency_plan)} prioritized tasks. "
                f"Focus on overdue items first!"
            )
            self.notification_service.send_nudge(message, priority="critical")
            
            actions.append({
                "action": "emergency_plan_created",
                "health_score": health["score"],
                "timestamp": datetime.now().isoformat()
            })
        
        # If at risk, send warning and suggest adjustments
        elif health["status"] == "at_risk":
            if health["overdue_count"] > 0:
                message = (
                    f"⚠️ You have {health['overdue_count']} overdue task(s). "
                    f"Let's prioritize getting caught up. "
                    f"I've updated your plan to focus on these first."
                )
                self.notification_service.send_nudge(message, priority="high")
                
                actions.append({
                    "action": "overdue_warning_sent",
                    "overdue_count": health["overdue_count"],
                    "timestamp": datetime.now().isoformat()
                })
        
        return actions
    
    async def _send_proactive_nudges(self, tasks: List, health: Dict) -> List[Dict]:
        """Send proactive nudges based on agent's decision"""
        actions = []
        
        # Check if nudge is needed
        if not self.agent.should_nudge():
            return actions
        
        # Don't nudge too frequently (at most once per 6 hours)
        if self.last_nudge:
            hours_since_nudge = (datetime.now() - self.last_nudge).total_seconds() / 3600
            if hours_since_nudge < 6:
                return actions
        
        # Generate and send nudge
        message = self.notification_service.generate_nudge_message(tasks, health)
        success = self.notification_service.send_nudge(message, priority=health["status"])
        
        if success:
            self.last_nudge = datetime.now()
            actions.append({
                "action": "nudge_sent",
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        
        return actions
    
    async def _handle_conflicts_autonomously(self) -> List[Dict]:
        """Autonomously resolve conflicts when possible"""
        actions = []
        
        if not self.agent.conflicts:
            return actions
        
        # Get clarifying questions
        questions = self.agent.get_clarifying_questions()
        
        # For time conflicts, agent can autonomously redistribute
        for conflict in self.agent.conflicts:
            if conflict["type"] == "time_conflict":
                # Agent autonomously redistributes tasks
                print(f"[AgentLoop] Resolving time conflict on {conflict['date']}")
                revised_plan = self.agent.revise_plan()
                
                message = (
                    f"I detected a scheduling conflict on {conflict['date']} "
                    f"({conflict['total_hours']:.1f} hours). "
                    f"I've redistributed your tasks to balance the workload."
                )
                self.notification_service.send_nudge(message, priority="medium")
                
                actions.append({
                    "action": "conflict_resolved",
                    "conflict_type": "time_conflict",
                    "timestamp": datetime.now().isoformat()
                })
        
        return actions
    
    def get_action_history(self, limit: int = 20) -> List[Dict]:
        """Get recent action history"""
        return self.action_history[-limit:]
    
    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "is_running": self.is_running,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_plan_creation": self.last_plan_creation.isoformat() if self.last_plan_creation else None,
            "last_nudge": self.last_nudge.isoformat() if self.last_nudge else None,
            "recent_actions_count": len(self.action_history),
            "weekly_plan_tasks": len(self.agent.weekly_plan)
        }

