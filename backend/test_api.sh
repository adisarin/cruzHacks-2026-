#!/bin/bash

# SlugPilot API Test Script
# Quick test of all major endpoints

API_BASE="http://localhost:8000"
USER_EMAIL="test@ucsc.edu"

echo "🚀 SlugPilot API Test"
echo "===================="
echo ""

# Check server
echo "1. Checking server..."
curl -s "$API_BASE/" | jq .
echo ""

# Create user
echo "2. Creating user..."
USER_RESPONSE=$(curl -s -X POST "$API_BASE/users" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"name\": \"Test Student\",
    \"preferences\": {
      \"nudge_threshold_days\": 3,
      \"preferred_study_hours_per_day\": 3.0
    }
  }")

USER_ID=$(echo $USER_RESPONSE | jq -r '.id')
echo "User ID: $USER_ID"
echo ""

# Check health
echo "3. Checking academic health..."
curl -s "$API_BASE/users/$USER_ID/health" | jq .
echo ""

# Get tasks
echo "4. Getting tasks..."
curl -s "$API_BASE/users/$USER_ID/tasks" | jq '. | length' | xargs echo "Total tasks:"
echo ""

# Create weekly plan
echo "5. Creating weekly plan..."
curl -s -X POST "$API_BASE/users/$USER_ID/plan/weekly" | jq '. | length' | xargs echo "Tasks in plan:"
echo ""

# Check agent status
echo "6. Checking agent status..."
curl -s "$API_BASE/users/$USER_ID/agent/status" | jq .
echo ""

# Get autonomous decisions
echo "7. Getting autonomous decisions..."
curl -s "$API_BASE/users/$USER_ID/agent/decisions" | jq .
echo ""

# Start agent
echo "8. Starting autonomous agent..."
curl -s -X POST "$API_BASE/users/$USER_ID/agent/start" | jq .
echo ""

# Execute cycle
echo "9. Manually triggering agent cycle..."
curl -s -X POST "$API_BASE/users/$USER_ID/agent/execute-cycle" | jq .
echo ""

# Get actions
echo "10. Getting agent actions..."
curl -s "$API_BASE/users/$USER_ID/agent/actions" | jq .
echo ""

echo "✅ Test complete!"

