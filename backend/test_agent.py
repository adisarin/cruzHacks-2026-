"""
Test script for SlugPilot Agentic System
This demonstrates the autonomous agent functionality
"""
import asyncio
import requests
import json
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_EMAIL = "test@ucsc.edu"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def create_test_user():
    """Create a test user"""
    print_section("Creating Test User")
    
    user_data = {
        "email": USER_EMAIL,
        "name": "Test Student",
        "canvas_token": None,  # Would be real token in production
        "google_calendar_token": None,  # Would be real token in production
        "preferences": {
            "notification_frequency": "daily",
            "nudge_threshold_days": 3,
            "preferred_study_hours_per_day": 3.0,
            "preferred_study_times": ["09:00-12:00", "14:00-17:00"],
            "auto_create_study_plans": True,
            "study_plan_days_before_exam": 7
        }
    }
    
    response = requests.post(f"{API_BASE_URL}/users", json=user_data)
    if response.status_code == 200:
        user = response.json()
        print(f"✅ User created: {user['email']}")
        print(f"   User ID: {user['id']}")
        return user['id']
    else:
        print(f"❌ Error creating user: {response.status_code}")
        print(response.text)
        return None

def test_agent_status(user_id):
    """Test agent status"""
    print_section("Checking Agent Status")
    
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/agent/status")
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Agent Status:")
        print(f"   Running: {status.get('is_running', False)}")
        print(f"   Last Check: {status.get('last_check', 'Never')}")
        print(f"   Last Plan: {status.get('last_plan_creation', 'Never')}")
        print(f"   Recent Actions: {status.get('recent_actions_count', 0)}")
        return status
    else:
        print(f"❌ Error getting status: {response.status_code}")
        return None

def test_academic_health(user_id):
    """Test academic health check"""
    print_section("Checking Academic Health")
    
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/health")
    if response.status_code == 200:
        health = response.json()
        print(f"✅ Academic Health:")
        print(f"   Score: {health['score']}/100")
        print(f"   Status: {health['status'].upper()}")
        print(f"   Overdue Tasks: {health['overdue_count']}")
        print(f"   Critical Upcoming: {health['critical_upcoming']}")
        print(f"   Weekly Hours: {health['weekly_hours']:.1f}h")
        print(f"   Daily Average: {health['daily_average']:.1f}h/day")
        if health.get('warnings'):
            print(f"   ⚠️  Warnings: {', '.join(health['warnings'])}")
        return health
    else:
        print(f"❌ Error checking health: {response.status_code}")
        return None

def test_weekly_plan(user_id):
    """Test weekly plan creation"""
    print_section("Creating Weekly Plan")
    
    response = requests.post(f"{API_BASE_URL}/users/{user_id}/plan/weekly")
    if response.status_code == 200:
        plan = response.json()
        print(f"✅ Weekly Plan Created:")
        print(f"   Tasks: {len(plan)}")
        if plan:
            print(f"\n   Top 5 Tasks:")
            for i, task in enumerate(plan[:5], 1):
                print(f"   {i}. {task['title']}")
                print(f"      Due: {task['due_date']}")
                print(f"      Priority: {task['priority']}")
                print(f"      Source: {task['source']}")
        return plan
    else:
        print(f"❌ Error creating plan: {response.status_code}")
        print(response.text)
        return None

def test_autonomous_decisions(user_id):
    """Test autonomous decision-making"""
    print_section("Viewing Autonomous Decisions")
    
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/agent/decisions")
    if response.status_code == 200:
        result = response.json()
        decisions = result.get('decisions', [])
        print(f"✅ Autonomous Decisions Made: {len(decisions)}")
        if decisions:
            for i, decision in enumerate(decisions[:5], 1):
                print(f"\n   {i}. {decision.get('type', 'unknown').upper()}")
                print(f"      Task: {decision.get('task', 'N/A')}")
                print(f"      Reason: {decision.get('reason', 'N/A')}")
                print(f"      Action: {decision.get('action', 'N/A')}")
        else:
            print("   No decisions needed at this time")
        return decisions
    else:
        print(f"❌ Error getting decisions: {response.status_code}")
        return None

def test_agent_actions(user_id):
    """Test agent action history"""
    print_section("Viewing Agent Action History")
    
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/agent/actions")
    if response.status_code == 200:
        result = response.json()
        actions = result.get('actions', [])
        print(f"✅ Recent Actions: {len(actions)}")
        if actions:
            for i, action in enumerate(actions[:5], 1):
                print(f"\n   {i}. {action.get('action', 'unknown').upper()}")
                print(f"      Time: {action.get('timestamp', 'N/A')}")
                if 'tasks_count' in action:
                    print(f"      Tasks: {action['tasks_count']}")
                if 'decisions' in action:
                    print(f"      Decisions: {len(action.get('decisions', []))}")
        else:
            print("   No actions recorded yet")
        return actions
    else:
        print(f"❌ Error getting actions: {response.status_code}")
        return None

def test_manual_cycle(user_id):
    """Manually trigger an agent cycle"""
    print_section("Manually Triggering Agent Cycle")
    
    print("   Triggering agent cycle...")
    response = requests.post(f"{API_BASE_URL}/users/{user_id}/agent/execute-cycle")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cycle Completed")
        print(f"   Status: {result.get('status')}")
        actions = result.get('actions', [])
        if actions:
            print(f"   Actions taken: {len(actions)}")
            for action in actions[:3]:
                print(f"   - {action.get('action', 'unknown')}")
        return result
    else:
        print(f"❌ Error executing cycle: {response.status_code}")
        print(response.text)
        return None

def test_tasks(user_id):
    """Test getting all tasks"""
    print_section("Getting All Tasks")
    
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/tasks")
    if response.status_code == 200:
        tasks = response.json()
        print(f"✅ Total Tasks: {len(tasks)}")
        if tasks:
            print(f"\n   Sample Tasks:")
            for i, task in enumerate(tasks[:5], 1):
                print(f"   {i}. {task['title']}")
                print(f"      Course: {task.get('course', 'N/A')}")
                print(f"      Due: {task['due_date']}")
                print(f"      Priority: {task['priority']}")
                print(f"      Status: {task['status']}")
        return tasks
    else:
        print(f"❌ Error getting tasks: {response.status_code}")
        return None

async def test_autonomous_loop(user_id, duration_seconds=30):
    """Test the autonomous agent loop"""
    print_section(f"Testing Autonomous Agent Loop ({duration_seconds}s)")
    
    # Start the agent
    print("   Starting autonomous agent...")
    response = requests.post(f"{API_BASE_URL}/users/{user_id}/agent/start")
    if response.status_code != 200:
        print(f"❌ Error starting agent: {response.status_code}")
        return
    
    print("✅ Agent started")
    print(f"   Waiting {duration_seconds} seconds for agent to run cycles...")
    
    # Wait and check status periodically
    for i in range(3):
        await asyncio.sleep(duration_seconds / 3)
        status = test_agent_status(user_id)
        if status and status.get('is_running'):
            actions = test_agent_actions(user_id)
    
    print("\n   Stopping agent...")
    requests.post(f"{API_BASE_URL}/users/{user_id}/agent/stop")
    print("✅ Agent stopped")

def main():
    """Main test function"""
    print("\n" + "🚀"*30)
    print("  SLUGPILOT AGENTIC SYSTEM TEST")
    print("🚀"*30)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"\n✅ Server is running: {response.json()}")
    except:
        print(f"\n❌ Server is not running at {API_BASE_URL}")
        print("   Please start the server with: uvicorn app.main:app --reload")
        return
    
    # Create user
    user_id = create_test_user()
    if not user_id:
        return
    
    # Basic tests
    test_academic_health(user_id)
    test_tasks(user_id)
    test_weekly_plan(user_id)
    test_autonomous_decisions(user_id)
    test_agent_status(user_id)
    test_agent_actions(user_id)
    
    # Test manual cycle
    test_manual_cycle(user_id)
    
    # Test autonomous loop (optional - takes time)
    print("\n" + "="*60)
    print("  Would you like to test the autonomous loop?")
    print("  (This will run the agent for 30 seconds)")
    print("="*60)
    # Uncomment to test autonomous loop:
    # asyncio.run(test_autonomous_loop(user_id, duration_seconds=30))
    
    print("\n" + "✅"*30)
    print("  TESTING COMPLETE")
    print("✅"*30 + "\n")

if __name__ == "__main__":
    main()

