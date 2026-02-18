#!/bin/bash
set -e

echo "🧪 Running Flaky Smoke Tests"
echo "=============================="

# Test 1: Library unit tests
echo ""
echo "✓ Running library unit tests..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
PYTHONPATH=$PWD:$PYTHONPATH pytest tests/ -q

# Test 2: Backend health check
echo ""
echo "✓ Testing backend health..."
response=$(curl -s http://localhost:8001/health)
if [[ "$response" == *"ok"* ]]; then
    echo "  Backend is healthy"
else
    echo "  ❌ Backend health check failed"
    exit 1
fi

# Test 3: Frontend is running
echo ""
echo "✓ Testing frontend..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173)
if [[ "$response" == "200" ]]; then
    echo "  Frontend is serving"
else
    echo "  ❌ Frontend not responding"
    exit 1
fi

# Test 4: Demo eval case exists
echo ""
echo "✓ Testing demo eval..."
if [ -f "$SCRIPT_DIR/../demo/evals/quiz_answering/eval.py" ]; then
    echo "  Demo eval case exists"
else
    echo "  ❌ Demo eval case missing"
    exit 1
fi

echo ""
echo "=============================="
echo "✅ All smoke tests passed!"
echo ""
echo "Access the app at:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8001"
