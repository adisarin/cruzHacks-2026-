# SlugPilot - Autonomous Student Life Agent

**"AI chief of staff for college students"**

SlugPilot is an autonomous agent that keeps students academically safe by monitoring deadlines, creating study plans, and proactively managing academic workload.

## 🎯 Features

### Agentic Capabilities
- **Autonomous Planning**: Creates and revises weekly plans automatically
- **Proactive Monitoring**: Continuously checks deadlines, health, and conflicts
- **Autonomous Decision-Making**: Makes decisions about priorities and task management
- **Auto Study Plans**: Creates study plans before exams automatically
- **Smart Nudging**: Sends proactive notifications when falling behind

### Integrations
- **Canvas LMS**: Reads assignments and deadlines
- **Google Calendar**: Syncs events and creates study sessions
- **Piazza**: Monitors announcements for deadline changes
- **Slack**: Watches channels for assignment updates

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 3. API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Run the Test Script

```bash
python test_agent.py
```

This will:
1. Create a test user
2. Check academic health
3. Create a weekly plan
4. View autonomous decisions
5. Test agent status and actions
6. Manually trigger an agent cycle

### Manual API Testing

#### 1. Create a User

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@ucsc.edu",
    "name": "John Doe",
    "preferences": {
      "nudge_threshold_days": 3,
      "preferred_study_hours_per_day": 3.0
    }
  }'
```

#### 2. Check Academic Health

```bash
curl "http://localhost:8000/users/student@ucsc.edu/health"
```

#### 3. Create Weekly Plan

```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/plan/weekly"
```

#### 4. Start Autonomous Agent

```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/start"
```

#### 5. Check Agent Status

```bash
curl "http://localhost:8000/users/student@ucsc.edu/agent/status"
```

#### 6. View Autonomous Decisions

```bash
curl "http://localhost:8000/users/student@ucsc.edu/agent/decisions"
```

#### 7. View Agent Actions

```bash
curl "http://localhost:8000/users/student@ucsc.edu/agent/actions"
```

#### 8. Manually Trigger Agent Cycle

```bash
curl -X POST "http://localhost:8000/users/student@ucsc.edu/agent/execute-cycle"
```

## 📡 Key API Endpoints

### User Management
- `POST /users` - Create user (starts agent automatically)
- `GET /users/{user_id}` - Get user info

### Task Management
- `GET /users/{user_id}/tasks` - Get all tasks
- `GET /users/{user_id}/tasks/upcoming` - Get upcoming tasks
- `GET /users/{user_id}/tasks/overdue` - Get overdue tasks

### Planning
- `POST /users/{user_id}/plan/weekly` - Create weekly plan
- `GET /users/{user_id}/plan/weekly` - Get current plan
- `POST /users/{user_id}/plan/revise` - Revise plan

### Academic Health
- `GET /users/{user_id}/health` - Get health status
- `GET /users/{user_id}/conflicts` - Get conflicts

### Study Plans
- `POST /users/{user_id}/study-plans` - Create study plan
- `POST /users/{user_id}/study-plans/auto-create` - Auto-create for exams

### Agent Control (Autonomous)
- `POST /users/{user_id}/agent/start` - Start autonomous agent
- `POST /users/{user_id}/agent/stop` - Stop autonomous agent
- `GET /users/{user_id}/agent/status` - Get agent status
- `GET /users/{user_id}/agent/actions` - View action history
- `GET /users/{user_id}/agent/decisions` - View autonomous decisions
- `POST /users/{user_id}/agent/execute-cycle` - Manually trigger cycle

### Notifications
- `POST /users/{user_id}/nudge` - Send nudge
- `POST /users/{user_id}/notifications/weekly-summary` - Send weekly summary

## 🤖 How the Agent Works

### Autonomous Loop

The agent runs continuously in the background, executing cycles every 15 minutes:

1. **Gather State**: Collects tasks from all sources (Canvas, Calendar, Piazza, Slack)
2. **Make Decisions**: Autonomously adjusts priorities, escalates urgent tasks
3. **Update Plans**: Creates/updates weekly plan if needed
4. **Check Health**: Monitors academic health score
5. **Take Actions**: 
   - Creates emergency plans if health is critical
   - Sends proactive nudges
   - Auto-creates study plans for upcoming exams
   - Resolves conflicts autonomously

### Decision-Making

The agent makes autonomous decisions:
- **Auto-prioritizes** overdue tasks to CRITICAL
- **Escalates** tasks approaching deadlines
- **Suggests** breaking down large tasks
- **Identifies** when too many critical tasks exist

### Goal: "Keep me academically safe"

The agent works toward this goal by:
- Preventing academic crises proactively
- Balancing workload automatically
- Creating study plans before exams
- Sending timely reminders
- Adjusting priorities based on urgency

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── agent/              # Core agentic system
│   │   ├── slugpilot_agent.py      # Main agent
│   │   ├── agent_loop.py           # Autonomous loop
│   │   ├── agent_manager.py        # Agent orchestration
│   │   ├── study_plan_generator.py # Study plan creation
│   │   └── notification_service.py # Nudging system
│   ├── models/             # Data models
│   ├── services/           # Integration services
│   └── main.py             # FastAPI app
├── test_agent.py           # Test script
└── requirements.txt        # Dependencies
```

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file:

```env
CANVAS_API_TOKEN=your_token
CANVAS_BASE_URL=https://canvas.ucsc.edu/api/v1
GOOGLE_CALENDAR_CREDENTIALS=path_to_credentials
SLACK_BOT_TOKEN=xoxb-your-token
```

## 📝 Example Usage Flow

1. **User Registration**: Create user → Agent automatically starts
2. **Agent Runs**: Continuously monitors and plans (every 15 min)
3. **User Checks**: View health, tasks, plans via API
4. **Agent Acts**: Sends nudges, creates plans, resolves conflicts
5. **User Benefits**: Stays on track, never misses deadlines

## 🎓 Demo Scenarios

### Scenario 1: New User
- User registers → Agent starts automatically
- Agent creates initial weekly plan
- Agent monitors academic health

### Scenario 2: Approaching Deadline
- Agent detects task due in 2 days
- Agent escalates priority to HIGH
- Agent sends proactive nudge
- Agent adjusts weekly plan

### Scenario 3: Exam Coming Up
- Agent detects exam in 7 days
- Agent auto-creates study plan
- Agent syncs study sessions to calendar
- Agent distributes study time across days

### Scenario 4: Academic Health Critical
- Agent detects overdue tasks
- Agent creates emergency plan
- Agent sends urgent notification
- Agent reprioritizes all tasks

## 🐛 Troubleshooting

### Server won't start
- Check if port 8000 is available
- Ensure all dependencies are installed
- Check Python version (3.8+)

### Agent not running
- Check agent status: `GET /users/{user_id}/agent/status`
- Start agent manually: `POST /users/{user_id}/agent/start`
- Check server logs for errors

### No tasks showing
- Ensure Canvas/Calendar tokens are configured
- Check service initialization in agent
- Verify API endpoints are accessible

## 📚 Next Steps

- Add database persistence
- Implement real Canvas/Piazza/Slack integrations
- Add frontend dashboard
- Enhance decision-making with ML
- Add user preferences learning

## 🤝 Contributing

This is a hackathon project for CruzHacks 2026!

## 📄 License

MIT

