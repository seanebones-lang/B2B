#!/bin/bash
# Measure test coverage and generate reports

set -e

echo "🔍 Measuring test coverage..."

# Install coverage tools if not already installed
pip install -q pytest pytest-cov coverage

# Run tests with coverage
pytest tests/ \
    --cov=. \
    --cov-report=html \
    --cov-report=xml \
    --cov-report=term-missing \
    --cov-fail-under=90 \
    -v

# Display coverage summary
echo ""
echo "📊 Coverage Summary:"
coverage report

# Check if coverage meets threshold
COVERAGE=$(coverage report | tail -1 | awk '{print $NF}' | sed 's/%//')
if (( $(echo "$COVERAGE < 90" | bc -l) )); then
    echo "❌ Coverage ($COVERAGE%) is below threshold (90%)"
    exit 1
else
    echo "✅ Coverage ($COVERAGE%) meets threshold (90%)"
fi

echo ""
echo "📈 Coverage report generated in htmlcov/index.html"
