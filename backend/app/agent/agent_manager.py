from typing import Dict, Optional
from app.agent.agent_loop import AgentLoop
from app.agent.slugpilot_agent import SlugPilotAgent
from app.models.user import User
import asyncio


class AgentManager:
    """
    Manages multiple agent instances running autonomously.
    This is the orchestrator for all autonomous agents.
    """
    
    def __init__(self):
        self.agents: Dict[str, SlugPilotAgent] = {}
        self.agent_loops: Dict[str, AgentLoop] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    def register_agent(self, user: User) -> str:
        """Register a new user's agent"""
        agent = SlugPilotAgent(user)
        agent_loop = AgentLoop(agent)
        
        self.agents[user.id] = agent
        self.agent_loops[user.id] = agent_loop
        
        print(f"[AgentManager] Registered agent for user: {user.email}")
        return user.id
    
    async def start_agent(self, user_id: str):
        """Start the autonomous loop for a user's agent"""
        if user_id not in self.agent_loops:
            raise ValueError(f"Agent not registered for user: {user_id}")
        
        if user_id in self.running_tasks:
            print(f"[AgentManager] Agent already running for user: {user_id}")
            return
        
        loop = self.agent_loops[user_id]
        task = asyncio.create_task(loop.start())
        self.running_tasks[user_id] = task
        
        print(f"[AgentManager] Started autonomous agent for user: {user_id}")
    
    async def stop_agent(self, user_id: str):
        """Stop the autonomous loop for a user's agent"""
        if user_id not in self.agent_loops:
            return
        
        loop = self.agent_loops[user_id]
        loop.stop()
        
        if user_id in self.running_tasks:
            task = self.running_tasks[user_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.running_tasks[user_id]
        
        print(f"[AgentManager] Stopped agent for user: {user_id}")
    
    def get_agent(self, user_id: str) -> Optional[SlugPilotAgent]:
        """Get agent instance for a user"""
        return self.agents.get(user_id)
    
    def get_agent_loop(self, user_id: str) -> Optional[AgentLoop]:
        """Get agent loop for a user"""
        return self.agent_loops.get(user_id)
    
    async def start_all_agents(self):
        """Start all registered agents"""
        for user_id in self.agent_loops:
            await self.start_agent(user_id)
    
    async def stop_all_agents(self):
        """Stop all running agents"""
        for user_id in list(self.running_tasks.keys()):
            await self.stop_agent(user_id)
    
    def is_agent_running(self, user_id: str) -> bool:
        """Check if agent is running for a user"""
        return user_id in self.running_tasks


# Global agent manager instance
agent_manager = AgentManager()

