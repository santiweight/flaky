"""
Integration tests for the eval runner.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from flaky.runner import EvalRunner
from flaky import EvalCase, expect


def test_discover_cases():
    """Test case discovery in a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir)
        
        # Create some eval case directories
        (cases_dir / "case1").mkdir()
        (cases_dir / "case1" / "eval.py").write_text("# test")
        
        (cases_dir / "case2").mkdir()
        (cases_dir / "case2" / "test.py").write_text("# test")
        
        # Create a non-case directory
        (cases_dir / "not_a_case").mkdir()
        
        runner = EvalRunner(cases_dir)
        cases = runner.discover_cases()
        
        assert len(cases) == 2
        assert "case1" in cases
        assert "case2" in cases
        assert "not_a_case" not in cases


def test_load_case():
    """Test loading an eval case from a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir)
        case_dir = cases_dir / "test_case"
        case_dir.mkdir()
        
        # Write a simple eval case
        eval_code = """
from flaky import EvalCase, expect

class TestEval(EvalCase):
    def test_simple(self):
        expect(1 + 1).to_equal(2)
"""
        (case_dir / "eval.py").write_text(eval_code)
        
        runner = EvalRunner(cases_dir)
        eval_cases = runner.load_case("test_case")
        
        assert len(eval_cases) == 1
        assert eval_cases[0].get_name() == "TestEval"


def test_run_case_sequential():
    """Test running a case sequentially."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir)
        case_dir = cases_dir / "test_case"
        case_dir.mkdir()
        
        eval_code = """
from flaky import EvalCase, expect

class TestEval(EvalCase):
    def test_always_pass(self):
        expect(True).to_be_truthy()
    
    def test_always_fail(self):
        expect(False).to_be_truthy()
"""
        (case_dir / "eval.py").write_text(eval_code)
        
        runner = EvalRunner(cases_dir)
        report = runner.run_case("test_case", num_runs=3, verbose=False, parallel=False)
        
        assert report.case_name == "test_case"
        assert report.num_generations == 3
        assert report.total_tests == 6  # 2 tests * 3 runs
        assert report.total_passed == 3  # test_always_pass * 3
        assert report.total_failed == 3  # test_always_fail * 3
        assert report.success_rate == 50.0


def test_run_case_parallel():
    """Test running a case in parallel."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir)
        case_dir = cases_dir / "test_case"
        case_dir.mkdir()
        
        eval_code = """
from flaky import EvalCase, expect

class TestEval(EvalCase):
    def test_one(self):
        expect(1).to_equal(1)
    
    def test_two(self):
        expect(2).to_equal(2)
"""
        (case_dir / "eval.py").write_text(eval_code)
        
        runner = EvalRunner(cases_dir)
        report = runner.run_case("test_case", num_runs=5, verbose=False, parallel=True, max_workers=2)
        
        assert report.case_name == "test_case"
        assert report.num_generations == 5
        assert report.total_tests == 10  # 2 tests * 5 runs
        assert report.total_passed == 10  # all pass
        assert report.success_rate == 100.0


def test_per_test_breakdown():
    """Test per-test breakdown in report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir)
        case_dir = cases_dir / "test_case"
        case_dir.mkdir()
        
        eval_code = """
from flaky import EvalCase, expect
import random

class TestEval(EvalCase):
    def test_deterministic(self):
        expect(1).to_equal(1)
    
    def test_flaky(self):
        # Fails 50% of the time
        expect(random.random() > 0.5).to_be_truthy()
"""
        (case_dir / "eval.py").write_text(eval_code)
        
        runner = EvalRunner(cases_dir)
        report = runner.run_case("test_case", num_runs=10, verbose=False, parallel=True)
        
        breakdown = report.per_test_breakdown()
        
        assert "test_deterministic" in breakdown
        assert "test_flaky" in breakdown
        
        # test_deterministic should pass 100%
        passed, total, rate = breakdown["test_deterministic"]
        assert passed == 10
        assert total == 10
        assert rate == 100.0
        
        # test_flaky should be somewhere between 0-100%
        passed, total, rate = breakdown["test_flaky"]
        assert total == 10
        assert 0 <= passed <= 10


def test_timing_captured():
    """Test that timing information is captured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir)
        case_dir = cases_dir / "test_case"
        case_dir.mkdir()
        
        eval_code = """
from flaky import EvalCase, expect
import time

class TestEval(EvalCase):
    def test_with_delay(self):
        time.sleep(0.01)  # 10ms
        expect(True).to_be_truthy()
"""
        (case_dir / "eval.py").write_text(eval_code)
        
        runner = EvalRunner(cases_dir)
        report = runner.run_case("test_case", num_runs=2, verbose=False, parallel=False)
        
        # Check that timing was captured
        assert report.total_duration_ms > 0
        assert report.avg_generation_duration_ms > 0
        
        # Check per-test timing
        timing = report.per_test_timing()
        assert "test_with_delay" in timing
        assert timing["test_with_delay"]["avg_ms"] >= 10  # At least 10ms


def test_load_case_not_found():
    """Test loading a non-existent case."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cases_dir = Path(tmpdir)
        runner = EvalRunner(cases_dir)
        
        with pytest.raises(ValueError, match="No Python files found"):
            runner.load_case("nonexistent")
