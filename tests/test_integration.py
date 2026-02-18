"""
Integration tests for the full flaky workflow.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess
import json

from flaky.runner import EvalRunner


def test_cli_run_case():
    """Test running a case via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir) / "evals"
        cases_dir.mkdir()
        
        case_dir = cases_dir / "simple_test"
        case_dir.mkdir()
        
        eval_code = """
from flaky import EvalCase, expect

class SimpleEval(EvalCase):
    def test_math(self):
        expect(2 + 2).to_equal(4)
"""
        (case_dir / "eval.py").write_text(eval_code)
        
        # Run via CLI
        result = subprocess.run(
            ["python", "-m", "flaky", "run", "--case", "simple_test", "--runs", "2", "--dir", str(cases_dir), "--format", "json"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        data = json.loads(result.stdout)
        
        assert data["case_name"] == "simple_test"
        assert data["num_generations"] == 2
        assert data["total_tests"] == 2
        assert data["total_passed"] == 2
        assert data["success_rate"] == 100.0


def test_cli_list_cases():
    """Test listing cases via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir) / "evals"
        cases_dir.mkdir()
        
        # Create two cases
        for case_name in ["case1", "case2"]:
            case_dir = cases_dir / case_name
            case_dir.mkdir()
            (case_dir / "eval.py").write_text("from flaky import EvalCase\nclass E(EvalCase): pass")
        
        result = subprocess.run(
            ["python", "-m", "flaky", "list", "--dir", str(cases_dir)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert "case1" in result.stdout
        assert "case2" in result.stdout


def test_cli_run_all():
    """Test running all cases via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir) / "evals"
        cases_dir.mkdir()
        
        # Create two cases
        for i, case_name in enumerate(["case1", "case2"]):
            case_dir = cases_dir / case_name
            case_dir.mkdir()
            
            eval_code = f"""
from flaky import EvalCase, expect

class TestEval{i}(EvalCase):
    def test_pass(self):
        expect(True).to_be_truthy()
"""
            (case_dir / "eval.py").write_text(eval_code)
        
        result = subprocess.run(
            ["python", "-m", "flaky", "run", "--all", "--runs", "2", "--dir", str(cases_dir), "--format", "json"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        data = json.loads(result.stdout)
        
        assert data["total_cases"] == 2
        assert data["total_generations"] == 4  # 2 cases * 2 runs
        assert data["total_tests"] == 4  # 2 cases * 2 runs * 1 test


def test_parallel_isolation():
    """Test that parallel runs are truly isolated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir) / "evals"
        cases_dir.mkdir()
        
        case_dir = cases_dir / "stateful_test"
        case_dir.mkdir()
        
        # This test would fail if state leaked between runs
        eval_code = """
from flaky import EvalCase, expect

# Global state that should NOT leak
_counter = 0

class StatefulEval(EvalCase):
    def test_isolation(self):
        global _counter
        _counter += 1
        # Should always be 1 if properly isolated
        expect(_counter).to_equal(1)
"""
        (case_dir / "eval.py").write_text(eval_code)
        
        runner = EvalRunner(cases_dir)
        report = runner.run_case("stateful_test", num_runs=5, verbose=False, parallel=True)
        
        # All runs should pass if isolation works
        assert report.total_passed == 5
        assert report.success_rate == 100.0
