# Quick Testing Guide for SlugPilot

## 🚀 Step-by-Step Testing

### Step 1: Start the Server

Open Terminal 1:
```bash
cd backend
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 2: Test the API (Choose one method)

#### Method A: Use the Python Test Script (Easiest)

Open Terminal 2:
```bash
cd backend
python test_agent.py
```

This will automatically:
- ✅ Create a test user
- ✅ Check academic health
- ✅ Create a weekly plan
- ✅ Show autonomous decisions
- ✅ Display agent status
- ✅ Trigger an agent cycle

#### Method B: Use the Interactive Swagger UI (Best for Exploration)

1. Open your browser
2. Go to: **http://localhost:8000/docs**
3. Click "Try it out" on any endpoint
4. Fill in the parameters
5. Click "Execute"
6. See the results!

#### Method C: Use curl Commands (For Quick Tests)

```bash
# 1. Create a user (agent starts automatically)
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@ucsc.edu",
    "name": "Test Student",
    "preferences": {
      "nudge_threshold_days": 3,
      "preferred_study_hours_per_day": 3.0
    }
  }'

# Save the user_id from response, then:

# 2. Check academic health
curl "http://localhost:8000/users/student@ucsc.edu/health"

# 3. Create weekly plan
curl -X POST "http://localhost:8000/users/student@ucsc.edu/plan/weekly"

# 4. View agent status
curl "http://localhost:8000/users/student@ucsc.edu/agent/status"

# 5. See autonomous decisions
curl "http://localhost:8000/users/student@ucsc.edu/agent/decisions"

# 6. Manually trigger agent cycle
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/execute-cycle"

# 7. View agent actions
curl "http://localhost:8000/users/student@ucsc.edu/agent/actions"
```

## 🎯 What to Test

### 1. Basic Functionality
- [ ] Server starts successfully
- [ ] Health endpoint returns status
- [ ] User creation works
- [ ] Agent starts automatically when user is created

### 2. Agentic Features
- [ ] Agent status shows `is_running: true`
- [ ] Autonomous decisions are made
- [ ] Weekly plan is created
- [ ] Action history records activities

### 3. Autonomous Behavior
- [ ] Start agent: `POST /users/{id}/agent/start`
- [ ] Wait 15 minutes OR trigger cycle manually
- [ ] Check actions: `GET /users/{id}/agent/actions`
- [ ] See what agent did autonomously

## 📊 Expected Results

### Health Check Response:
```json
{
  "score": 100,
  "status": "healthy",
  "overdue_count": 0,
  "critical_upcoming": 0,
  "weekly_hours": 0.0,
  "daily_average": 0.0
}
```

### Agent Status Response:
```json
{
  "is_running": true,
  "last_check": "2026-01-15T10:30:00",
  "last_plan_creation": "2026-01-15T10:00:00",
  "recent_actions_count": 5
}
```

### Autonomous Decisions Response:
```json
{
  "decisions": [
    {
      "type": "auto_prioritize",
      "task": "Assignment 1",
      "reason": "Task is overdue",
      "action": "Set priority to CRITICAL"
    }
  ],
  "count": 1
}
```

## 🔍 Testing the Autonomous Loop

### Start the Agent:
```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/start"
```

### Check What It's Doing:
```bash
# View recent actions
curl "http://localhost:8000/users/student@ucsc.edu/agent/actions"

# View status
curl "http://localhost:8000/users/student@ucsc.edu/agent/status"
```

### Manually Trigger a Cycle (for immediate testing):
```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/execute-cycle"
```

### Stop the Agent:
```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/stop"
```

## 🐛 Troubleshooting

### Server won't start?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use a different port
uvicorn app.main:app --reload --port 8001
```

### Import errors?
```bash
# Make sure dependencies are installed
pip install -r requirements.txt
```

### Agent not running?
```bash
# Check status first
curl "http://localhost:8000/users/{user_id}/agent/status"

# Start manually if needed
curl -X POST "http://localhost:8000/users/{user_id}/agent/start"
```

### No tasks showing?
- This is normal if you don't have Canvas/Calendar tokens configured
- The agent still works, it just has no external data sources
- You can still test the agentic logic and decision-making

## 💡 Pro Tips

1. **Use Swagger UI** (`http://localhost:8000/docs`) - It's the easiest way to explore all endpoints
2. **Run the Python script** - It tests everything automatically
3. **Check agent actions** - This shows what the agent did autonomously
4. **Trigger cycles manually** - Don't wait 15 minutes, use `/agent/execute-cycle`

## 🎬 Demo Flow

1. Start server
2. Open Swagger UI: http://localhost:8000/docs
3. Create user → Agent starts automatically
4. Check health → See initial status
5. Create plan → Agent generates weekly plan
6. View decisions → See autonomous choices
7. Trigger cycle → See agent act
8. Check actions → See what agent did

That's it! The agent is now running autonomously! 🚀

