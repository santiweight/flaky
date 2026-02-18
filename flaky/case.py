"""
Base class for eval cases.
"""

import time
from abc import ABC
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class TestResult:
    """Result of running a single test."""

    name: str
    passed: bool
    error: str | None = None
    exception: Exception | None = None
    duration_ms: float = 0.0


@dataclass
class GenerationResult:
    """Result of running all tests for a single generation."""

    generation_num: int
    test_results: list[TestResult] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.test_results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.test_results if not r.passed)

    @property
    def total_count(self) -> int:
        return len(self.test_results)


class EvalCase(ABC):
    """
    Base class for eval cases.

    Subclasses define test methods starting with `test_` and use
    `expect()` for assertions. Each test is binary: pass or fail.

    Example:
        class MyAgentEval(EvalCase):
            def test_answers_correctly(self):
                result = my_agent.run("What is 2+2?")
                expect(result).to_equal("4")
    """

    @classmethod
    def get_name(cls) -> str:
        """Get the name of this eval case."""
        return cls.__name__

    def get_test_methods(self) -> list[tuple[str, Callable[[], None]]]:
        """Get all test methods (methods starting with 'test_')."""
        methods = []
        for name in dir(self):
            if name.startswith("test_"):
                method = getattr(self, name)
                if callable(method):
                    methods.append((name, method))
        return sorted(methods, key=lambda x: x[0])

    def setUp(self):
        """Optional setup method called before each test."""
        pass

    def tearDown(self):
        """Optional teardown method called after each test."""
        pass

    def run_test(self, test_name: str, test_method: Callable[[], None]) -> TestResult:
        """Run a single test method and return the result."""
        start_time = time.perf_counter()
        try:
            self.setUp()
            test_method()
            self.tearDown()
            duration_ms = (time.perf_counter() - start_time) * 1000
            return TestResult(name=test_name, passed=True, duration_ms=duration_ms)
        except Exception as e:
            try:
                self.tearDown()
            except Exception:
                pass
            duration_ms = (time.perf_counter() - start_time) * 1000
            return TestResult(
                name=test_name,
                passed=False,
                error=str(e),
                exception=e,
                duration_ms=duration_ms,
            )

    def run_all_tests(self, generation_num: int) -> GenerationResult:
        """Run all test methods and return the results."""
        start_time = time.perf_counter()
        result = GenerationResult(generation_num=generation_num)

        for test_name, test_method in self.get_test_methods():
            test_result = self.run_test(test_name, test_method)
            result.test_results.append(test_result)

        result.duration_ms = (time.perf_counter() - start_time) * 1000
        return result
