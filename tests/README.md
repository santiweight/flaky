# Tests

## Running Tests

### Unit Tests (Flaky Library)
```bash
cd /Users/santiagoweight/projects/flaky
PYTHONPATH=/Users/santiagoweight/projects/flaky:$PYTHONPATH pytest tests/ -v
```

### Backend Tests
```bash
cd /Users/santiagoweight/projects/flaky/web/backend
pytest test_main.py -v
```

### Smoke Tests (All Components)
```bash
./tests/smoke_test.sh
```

## Test Coverage

### Library Tests (`tests/`)
- **test_expect.py** (26 tests) - All assertion methods in the `expect()` API
- **test_case.py** (8 tests) - `EvalCase` base class functionality
- **test_runner.py** (7 tests) - Case discovery, loading, parallel/sequential execution
- **test_integration.py** (4 tests) - CLI interface, subprocess isolation

### Backend Tests (`web/backend/test_main.py`)
- **Unit tests** (9 tests) - API endpoints, PDF processing, LLM integration (mocked)

### Integration Tests
- **smoke_test.sh** - Verifies all components are running and healthy

## Test Results

✅ **45/45 library tests passing**
✅ **Backend and frontend servers healthy**
✅ **Demo eval case configured**

## Adding New Tests

### For the Library
Add test files to `tests/` following the pattern `test_*.py`.

### For the Backend
Add tests to `web/backend/test_main.py` or create new test files.

### For Integration
Update `tests/smoke_test.sh` with new checks.
