# Testing SlugPilot

## Quick Start Testing

### Option 1: Python Test Script (Recommended)

```bash
# Make sure server is running first
uvicorn app.main:app --reload

# In another terminal, run:
python test_agent.py
```

This will:
- ✅ Create a test user
- ✅ Check academic health
- ✅ Create weekly plan
- ✅ View autonomous decisions
- ✅ Test agent status
- ✅ Manually trigger agent cycle

### Option 2: Bash Script

```bash
# Make sure you have jq installed: brew install jq
./test_api.sh
```

### Option 3: Manual API Testing

#### Step 1: Start the Server

```bash
cd backend
uvicorn app.main:app --reload
```

Server will be at: `http://localhost:8000`

#### Step 2: Open API Docs

Visit: http://localhost:8000/docs

This gives you an interactive Swagger UI to test all endpoints!

#### Step 3: Test Key Endpoints

**Create User** (Agent starts automatically):
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@ucsc.edu",
    "name": "Test Student"
  }'
```

**Check Health**:
```bash
curl "http://localhost:8000/users/student@ucsc.edu/health"
```

**Create Plan**:
```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/plan/weekly"
```

**View Agent Status**:
```bash
curl "http://localhost:8000/users/student@ucsc.edu/agent/status"
```

**See Autonomous Decisions**:
```bash
curl "http://localhost:8000/users/student@ucsc.edu/agent/decisions"
```

**Trigger Agent Cycle**:
```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/execute-cycle"
```

## Testing the Autonomous Agent

### Start the Agent

```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/start"
```

The agent will now run autonomously every 15 minutes!

### Check What It's Doing

```bash
# View recent actions
curl "http://localhost:8000/users/student@ucsc.edu/agent/actions"

# View status
curl "http://localhost:8000/users/student@ucsc.edu/agent/status"
```

### Stop the Agent

```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/stop"
```

## Demo Scenarios

### Scenario 1: New User Flow

1. Create user → Agent auto-starts
2. Check health → See initial status
3. Create plan → Agent generates weekly plan
4. View decisions → See what agent decided

### Scenario 2: Autonomous Behavior

1. Start agent
2. Wait 15 minutes (or trigger cycle manually)
3. Check actions → See what agent did autonomously
4. Check health → See if agent improved situation

### Scenario 3: Study Plan Creation

1. Create user with Canvas token (if available)
2. Call auto-create study plans endpoint
3. Check calendar (if Google Calendar configured)
4. See study sessions scheduled

## Expected Behavior

### When Agent Runs:

1. **Gathers Tasks**: From Canvas, Calendar, Piazza, Slack
2. **Makes Decisions**: Auto-prioritizes, escalates urgent tasks
3. **Updates Plan**: Creates/revises weekly plan if needed
4. **Checks Health**: Monitors academic health score
5. **Takes Actions**: 
   - Creates emergency plans if critical
   - Sends nudges if needed
   - Creates study plans for exams
   - Resolves conflicts

### What to Look For:

- ✅ Agent status shows `is_running: true`
- ✅ Action history shows recent activities
- ✅ Decisions show autonomous priority adjustments
- ✅ Health score updates based on tasks
- ✅ Weekly plan gets created/updated

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :8000

# Use different port
uvicorn app.main:app --reload --port 8001
```

### Agent not running
```bash
# Check status
curl "http://localhost:8000/users/{user_id}/agent/status"

# Start manually
curl -X POST "http://localhost:8000/users/{user_id}/agent/start"
```

### No tasks showing
- Without Canvas/Calendar tokens, tasks will be empty
- This is expected - agent still works, just has no data sources
- You can still test the agentic logic with manual task creation

### Import errors
```bash
# Make sure dependencies are installed
pip install -r requirements.txt
```

## Interactive Testing with Swagger UI

The easiest way to test is using the Swagger UI:

1. Start server: `uvicorn app.main:app --reload`
2. Open: http://localhost:8000/docs
3. Click "Try it out" on any endpoint
4. Fill in parameters
5. Click "Execute"
6. See results!

## Testing Checklist

- [ ] Server starts successfully
- [ ] Health endpoint works
- [ ] User creation works
- [ ] Agent starts automatically
- [ ] Weekly plan creation works
- [ ] Autonomous decisions are made
- [ ] Agent status shows running
- [ ] Action history records activities
- [ ] Manual cycle execution works
- [ ] Agent can be stopped/started

## Next Steps After Testing

1. Connect real Canvas API (get token from Canvas settings)
2. Connect Google Calendar (OAuth flow)
3. Set up Slack bot (create Slack app)
4. Test with real data
5. Build frontend to visualize agent actions

