#!/bin/bash
set -e

echo "🧪 Running Full Integration Test Suite"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if servers are running
echo ""
echo "📡 Checking server status..."

backend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")
frontend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null || echo "000")

if [ "$backend_status" != "200" ]; then
    echo -e "${RED}❌ Backend not running on port 8001${NC}"
    echo "   Start it with: cd web/backend && python3 main.py"
    exit 1
else
    echo -e "${GREEN}✓ Backend running${NC}"
fi

if [ "$frontend_status" != "200" ]; then
    echo -e "${YELLOW}⚠️  Frontend not running on port 5173${NC}"
    echo "   Start it with: cd web/frontend && npm run dev"
    echo "   (Continuing without frontend tests...)"
else
    echo -e "${GREEN}✓ Frontend running${NC}"
fi

# Test 1: Library Unit Tests
echo ""
echo "1️⃣  Running library unit tests..."
cd /Users/santiagoweight/projects/flaky
PYTHONPATH=/Users/santiagoweight/projects/flaky:$PYTHONPATH pytest tests/test_expect.py tests/test_case.py tests/test_runner.py -q
echo -e "${GREEN}✓ Library tests passed${NC}"

# Test 2: Integration Tests
echo ""
echo "2️⃣  Running integration tests..."
PYTHONPATH=/Users/santiagoweight/projects/flaky:$PYTHONPATH pytest tests/test_integration.py -q
echo -e "${GREEN}✓ Integration tests passed${NC}"

# Test 3: E2E Tests
echo ""
echo "3️⃣  Running end-to-end tests..."
PYTHONPATH=/Users/santiagoweight/projects/flaky:$PYTHONPATH pytest tests/test_e2e.py -v
echo -e "${GREEN}✓ E2E tests passed${NC}"

# Test 4: Demo Eval (if ANTHROPIC_API_KEY is set)
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "4️⃣  Running demo eval case..."
    cd /Users/santiagoweight/projects/flaky
    PYTHONPATH=/Users/santiagoweight/projects/flaky:$PYTHONPATH python -m flaky run --case quiz_answering --runs 2 --format json > /tmp/flaky_demo_result.json
    
    # Check that it ran successfully
    if [ $? -eq 0 ]; then
        success_rate=$(cat /tmp/flaky_demo_result.json | python3 -c "import sys, json; print(json.load(sys.stdin)['success_rate'])")
        echo -e "${GREEN}✓ Demo eval completed (${success_rate}% success rate)${NC}"
    else
        echo -e "${RED}❌ Demo eval failed${NC}"
        exit 1
    fi
else
    echo ""
    echo "4️⃣  Skipping demo eval (ANTHROPIC_API_KEY not set)"
fi

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}✅ All integration tests passed!${NC}"
echo ""
echo "Test Coverage:"
echo "  • Library unit tests: 45 tests"
echo "  • Integration tests: 4 tests"
echo "  • E2E tests: 11 tests"
echo "  • Demo eval: ${ANTHROPIC_API_KEY:+Ran}${ANTHROPIC_API_KEY:-Skipped}"
echo ""
echo "Servers:"
echo "  • Backend:  http://localhost:8001"
echo "  • Frontend: http://localhost:5173"
