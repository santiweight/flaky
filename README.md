# flaky

Binary eval framework for non-deterministic workloads.

Write tests with pass/fail outcomes, run them N times in parallel, get reliability percentages. No fuzzy scoring, no LLM-as-judge.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from flaky import EvalCase, expect

class MyAgentEval(EvalCase):
    def test_extracts_answer(self):
        result = my_agent.run("What is 2+2?")
        expect(result).to_equal("4")
    
    def test_handles_ambiguity(self):
        result = my_agent.run("What's the best color?")
        expect(result).to_be_truthy()
```

Run it:

```bash
flaky run --case my_agent --runs 50
```

## CLI Usage

```bash
# Run one case 50 times
flaky run --case my_agent --runs 50

# Run all cases
flaky run --all --runs 20

# Sequential mode (for debugging)
flaky run --case my_agent --runs 5 --sequential

# JSON output (for CI)
flaky run --case my_agent --runs 50 --format json

# List available cases
flaky list
```

## Configuration

Add to `pyproject.toml`:

```toml
[tool.flaky]
evals_dir = "evals"  # default directory for eval cases
runs = 5             # default number of runs
```

## Testing

```bash
# Run unit tests
pytest tests/

# Run backend tests
pytest web/backend/

# Run all tests
pytest
```
