# Testing Guide

## Test Suite Overview

The project includes comprehensive tests at multiple levels:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions  
3. **System Tests** - Test the full running system
4. **E2E Tests** - Test complete user workflows

## Quick Start

### Run All Tests
```bash
# System integration tests (requires servers running)
./tests/test_system_integration.sh

# Unit tests (no servers required)
PYTHONPATH=$PWD:$PYTHONPATH pytest tests/test_*.py -v
```

### Run Specific Test Suites
```bash
# Just library tests
PYTHONPATH=$PWD:$PYTHONPATH pytest tests/test_expect.py tests/test_case.py tests/test_runner.py -v

# Just integration tests
PYTHONPATH=$PWD:$PYTHONPATH pytest tests/test_integration.py -v

# Backend tests (requires backend dependencies)
cd web/backend && pytest test_main.py -v
```

## Test Categories

### 1. Library Unit Tests (`tests/`)

**test_expect.py** (26 tests)
- Tests all assertion methods: `to_equal`, `to_be_truthy`, `to_contain`, etc.
- Tests error cases and edge conditions
- Fast, no external dependencies

**test_case.py** (8 tests)
- Tests `EvalCase` base class
- Tests `setUp`/`tearDown` lifecycle
- Tests test discovery and execution
- Tests timing capture

**test_runner.py** (7 tests)
- Tests case discovery and loading
- Tests parallel vs sequential execution
- Tests timing statistics
- Tests per-test breakdown

**test_integration.py** (4 tests)
- Tests CLI interface (`flaky run`, `flaky list`)
- Tests subprocess isolation
- Tests JSON output format
- Tests multi-case execution

### 2. Backend Tests (`web/backend/test_main.py`)

**9 tests covering:**
- Health endpoint
- PDF text extraction
- Question parsing (mocked LLM)
- Question answering (mocked LLM)
- `/solve` endpoint
- `/proxy-pdf` endpoint
- Error handling

### 3. System Integration Tests (`tests/test_system_integration.sh`)

**6 tests covering:**
1. Backend health check
2. CORS headers
3. Frontend accessibility
4. CLI functionality
5. File structure integrity
6. API endpoint registration
7. PDF upload (optional, requires API key)

### 4. E2E Tests (`tests/test_e2e.py`)

**9 tests covering:**
- Full PDF upload workflow
- Multiple runs
- Concurrent requests
- Answer sheet generation
- Error handling

## Running Tests in CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/test.yml`) that runs:

1. **Unit tests** - All library tests
2. **Backend tests** - API endpoint tests
3. **E2E tests** - Full workflow tests
4. **Demo eval** - Runs the quiz answering eval and posts results to PRs

## Test Requirements

### Minimal (Unit Tests Only)
- Python 3.10+
- pytest
- No servers required
- No API keys required

### Full (All Tests)
- Python 3.10+
- pytest, requests, reportlab
- Backend running on port 8001
- Frontend running on port 5173
- ANTHROPIC_API_KEY (for LLM tests)

## Test Results

Current status:
```
✅ 45/45 library unit tests passing
✅ 9/9 backend unit tests passing  
✅ 6/6 system integration tests passing
✅ Backend healthy (port 8001)
✅ Frontend serving (port 5173)
```

## Adding New Tests

### For the Library
1. Create `tests/test_yourfeature.py`
2. Import from `flaky`
3. Use pytest conventions (`test_*` functions)
4. Run with `PYTHONPATH=$PWD:$PYTHONPATH pytest tests/test_yourfeature.py`

### For the Backend
1. Add tests to `web/backend/test_main.py`
2. Use `TestClient` from FastAPI
3. Mock external dependencies (LLM, HTTP requests)
4. Run with `cd web/backend && pytest test_main.py`

### For System Integration
1. Add checks to `tests/test_system_integration.sh`
2. Use curl for API testing
3. Check file existence, server health, etc.
4. Make tests idempotent and cleanup after

## Debugging Failed Tests

### Unit Test Failures
```bash
# Run with more verbosity
pytest tests/test_failing.py -vv

# Run specific test
pytest tests/test_file.py::test_function_name -v

# Show print statements
pytest tests/test_file.py -s
```

### Integration Test Failures
```bash
# Check server logs
tail -f /Users/santiagoweight/.cursor/projects/Users-santiagoweight-projects-flaky/terminals/*.txt

# Test endpoints manually
curl -v http://localhost:8001/health
```

### System Test Failures
```bash
# Run with bash debug mode
bash -x ./tests/test_system_integration.sh
```

## Performance Testing

The flaky library includes built-in timing:

```bash
# Run with timing output
flaky run --case quiz_answering --runs 10

# JSON output includes timing stats
flaky run --case quiz_answering --runs 10 --format json | jq '.timing'
```

Timing metrics:
- `duration_ms` per test
- `duration_ms` per generation
- `total_duration_ms` for full run
- `avg_generation_duration_ms`
- Per-test timing stats (min, max, avg, p95)
