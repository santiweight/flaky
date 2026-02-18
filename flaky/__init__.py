"""
flaky: Binary eval framework for non-deterministic workloads.

Write tests with pass/fail outcomes, run them N times in parallel,
get reliability percentages. No fuzzy scoring, no LLM-as-judge.
"""

from flaky.case import EvalCase, GenerationResult, TestResult
from flaky.expect import Expectation, ExpectationError, expect

__all__ = [
    "EvalCase",
    "TestResult",
    "GenerationResult",
    "expect",
    "Expectation",
    "ExpectationError",
]
__version__ = "0.1.0"
