#!/bin/bash
# Run load tests using Locust

set -e

echo "🚀 Starting load tests..."

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo "Installing Locust..."
    pip install locust
fi

# Default values
HOST="${HOST:-http://localhost:8501}"
USERS="${USERS:-10}"
SPAWN_RATE="${SPAWN_RATE:-2}"
DURATION="${DURATION:-60s}"

echo "Configuration:"
echo "  Host: $HOST"
echo "  Users: $USERS"
echo "  Spawn Rate: $SPAWN_RATE users/second"
echo "  Duration: $DURATION"
echo ""

# Run Locust
locust -f locustfile.py \
    --host="$HOST" \
    --users="$USERS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="$DURATION" \
    --headless \
    --html=load_test_report.html \
    --csv=load_test_results

echo ""
echo "✅ Load test complete!"
echo "📊 Results saved to:"
echo "  - load_test_report.html"
echo "  - load_test_results.csv"
