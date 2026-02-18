# Testing Guide

## Test Suite Overview

The project includes comprehensive tests at multiple levels:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Test complete user workflows

## Quick Start

### Run All Tests

```bash
# All library tests
pytest tests/ -v

# Backend tests
cd web/backend && pytest test_main.py -v

# All tests with coverage
pytest tests/ --cov=flaky --cov-report=html
```

### Run Specific Test Suites

```bash
# Library unit tests
pytest tests/test_expect.py tests/test_case.py tests/test_runner.py -v

# Integration tests
pytest tests/test_integration.py -v

# E2E tests (requires servers running)
pytest tests/test_e2e.py -v
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

### 3. E2E Tests (`tests/test_e2e.py`)

**9 tests covering:**
- Full PDF upload workflow
- Multiple runs
- Concurrent requests
- Answer sheet generation
- Error handling

## Test Requirements

### Unit Tests
- Python 3.10+
- pytest
- No servers or API keys required

### Backend Tests
- Python 3.10+
- pytest, fastapi, anthropic, pdfplumber, reportlab
- Tests use mocked LLM responses

### E2E Tests
- Backend server running on port 8001
- Frontend server running on port 5173
- ANTHROPIC_API_KEY environment variable (for actual LLM calls)

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

### For E2E Tests
1. Add tests to `tests/test_e2e.py`
2. Use `requests` library for API testing
3. Ensure servers are running before tests
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

### E2E Test Failures
```bash
# Check if servers are running
curl -v http://localhost:8001/health
curl -v http://localhost:5173

# Check server logs in terminals
# Test endpoints manually
curl -X POST http://localhost:8001/solve \
  -H "Content-Type: application/json" \
  -d '{"url": "test.pdf", "runs": 1}'
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
