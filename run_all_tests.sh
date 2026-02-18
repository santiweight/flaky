#!/bin/bash

echo "🧪 Flaky Test Suite"
echo "==================="
echo ""

# Track results
total_tests=0
passed_tests=0
failed_tests=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test 1: Library Unit Tests
echo -e "${BLUE}1. Library Unit Tests${NC}"
echo "   Running tests..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
if PYTHONPATH=$PWD:$PYTHONPATH pytest tests/test_expect.py tests/test_case.py tests/test_runner.py tests/test_integration.py -q > /tmp/unit_test_output.txt 2>&1; then
    unit_count=$(grep -o "[0-9]* passed" /tmp/unit_test_output.txt | head -1 | awk '{print $1}')
    echo -e "   ${GREEN}✓ $unit_count tests passed${NC}"
    passed_tests=$((passed_tests + unit_count))
    total_tests=$((total_tests + unit_count))
else
    echo -e "   ${RED}✗ Some tests failed${NC}"
    cat /tmp/unit_test_output.txt
    failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
fi

# Test 2: System Integration
echo ""
echo -e "${BLUE}2. System Integration Tests${NC}"
if ./tests/test_system_integration.sh > /tmp/integration_output.txt 2>&1; then
    integration_count=$(grep -c "✅ PASS" /tmp/integration_output.txt)
    echo -e "   ${GREEN}✓ $integration_count checks passed${NC}"
    passed_tests=$((passed_tests + integration_count))
    total_tests=$((total_tests + integration_count))
else
    echo -e "   ${RED}✗ Some checks failed${NC}"
    cat /tmp/integration_output.txt
    failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
fi

# Test 3: File Structure Validation
echo ""
echo -e "${BLUE}3. File Structure Validation${NC}"
required_files=(
    "flaky/case.py"
    "flaky/expect.py"
    "flaky/runner.py"
    "flaky/reporter.py"
    "flaky/__init__.py"
    "flaky/__main__.py"
    "web/backend/main.py"
    "web/frontend/src/App.tsx"
    "web/frontend/src/App.css"
    "demo/evals/quiz_answering/eval.py"
    "demo/fixtures/quizzes/manifest.json"
    "demo/quiz_app/answer.py"
    "pyproject.toml"
    "README.md"
    ".gitignore"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo -e "   ${GREEN}✓ All ${#required_files[@]} required files present${NC}"
    passed_tests=$((passed_tests + 1))
else
    echo -e "   ${RED}✗ Missing ${#missing_files[@]} files:${NC}"
    for file in "${missing_files[@]}"; do
        echo "     - $file"
    done
    failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))

# Summary
echo ""
echo "==================="
echo -e "${BLUE}Test Summary${NC}"
echo "==================="
echo ""

if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "Results: $passed_tests/$total_tests checks passed"
    echo ""
    echo "System Status:"
    echo "  ✓ Flaky library functional"
    echo "  ✓ Backend API operational"
    echo "  ✓ Frontend serving"
    echo "  ✓ All files present"
    echo ""
    echo "Access:"
    echo "  Frontend: http://localhost:5173"
    echo "  Backend:  http://localhost:8001"
    echo "  API Docs: http://localhost:8001/docs"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Results: $passed_tests/$total_tests checks passed, $failed_tests failed"
    echo ""
    echo "Check logs in /tmp/ for details"
    exit 1
fi
