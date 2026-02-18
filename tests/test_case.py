"""
Unit tests for EvalCase base class.
"""

import pytest
from flaky import EvalCase, expect, ExpectationError


class SimpleEval(EvalCase):
    """Simple test eval case."""
    
    def __init__(self):
        super().__init__()
        self.setup_called = False
        self.teardown_called = False
    
    def setUp(self):
        self.setup_called = True
    
    def tearDown(self):
        self.teardown_called = True
    
    def test_passing(self):
        expect(1 + 1).to_equal(2)
    
    def test_failing(self):
        expect(1 + 1).to_equal(3)


def test_get_name():
    """Test that get_name returns class name."""
    assert SimpleEval.get_name() == "SimpleEval"


def test_get_test_methods():
    """Test discovery of test methods."""
    eval_case = SimpleEval()
    methods = eval_case.get_test_methods()
    
    assert len(methods) == 2
    assert methods[0][0] == "test_failing"
    assert methods[1][0] == "test_passing"
    assert callable(methods[0][1])
    assert callable(methods[1][1])


def test_run_test_passing():
    """Test running a passing test."""
    eval_case = SimpleEval()
    result = eval_case.run_test("test_passing", eval_case.test_passing)
    
    assert result.name == "test_passing"
    assert result.passed is True
    assert result.error is None
    assert result.duration_ms > 0
    assert eval_case.setup_called
    assert eval_case.teardown_called


def test_run_test_failing():
    """Test running a failing test."""
    eval_case = SimpleEval()
    result = eval_case.run_test("test_failing", eval_case.test_failing)
    
    assert result.name == "test_failing"
    assert result.passed is False
    assert result.error is not None
    assert "Expected 2 to equal 3" in result.error
    assert result.duration_ms > 0
    assert eval_case.setup_called
    assert eval_case.teardown_called


def test_run_all_tests():
    """Test running all tests in an eval case."""
    eval_case = SimpleEval()
    result = eval_case.run_all_tests(generation_num=1)
    
    assert result.generation_num == 1
    assert len(result.test_results) == 2
    assert result.total_count == 2
    assert result.passed_count == 1
    assert result.failed_count == 1
    assert result.duration_ms > 0


def test_generation_result_properties():
    """Test GenerationResult computed properties."""
    eval_case = SimpleEval()
    result = eval_case.run_all_tests(generation_num=5)
    
    assert result.generation_num == 5
    assert result.passed_count == 1
    assert result.failed_count == 1
    assert result.total_count == 2


class EvalWithSetupError(EvalCase):
    """Eval case where setUp raises an error."""
    
    def setUp(self):
        raise ValueError("Setup failed")
    
    def test_something(self):
        expect(True).to_be_truthy()


def test_setup_error_handling():
    """Test that setUp errors are caught and reported."""
    eval_case = EvalWithSetupError()
    result = eval_case.run_test("test_something", eval_case.test_something)
    
    assert result.passed is False
    assert "Setup failed" in result.error


class EvalWithTeardownError(EvalCase):
    """Eval case where tearDown raises an error."""
    
    def tearDown(self):
        raise ValueError("Teardown failed")
    
    def test_something(self):
        expect(True).to_be_truthy()


def test_teardown_error_handling():
    """Test that tearDown errors are caught."""
    eval_case = EvalWithTeardownError()
    result = eval_case.run_test("test_something", eval_case.test_something)
    
    # tearDown errors cause the test to fail
    assert result.passed is False
    assert "Teardown failed" in result.error
