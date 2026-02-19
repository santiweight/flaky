"""
Expectation helpers for eval cases.

Provides a simple, readable API for making assertions in eval tests.
"""

from typing import Any


class ExpectationError(AssertionError):
    """Raised when an expectation fails."""
    pass


class Expectation:
    """Wrapper for making assertions on a value."""

    def __init__(self, value: Any):
        self.value = value

    def to_equal(self, expected: Any) -> None:
        """Assert that value equals expected."""
        if self.value != expected:
            raise ExpectationError(
                f"Expected {self.value!r} to equal {expected!r}"
            )

    def to_be(self, expected: Any) -> None:
        """Assert that value is identical to expected (using 'is')."""
        if self.value is not expected:
            raise ExpectationError(
                f"Expected {self.value!r} to be {expected!r}"
            )

    def to_be_truthy(self) -> None:
        """Assert that value is truthy."""
        if not self.value:
            raise ExpectationError(
                f"Expected {self.value!r} to be truthy"
            )

    def to_be_falsy(self) -> None:
        """Assert that value is falsy."""
        if self.value:
            raise ExpectationError(
                f"Expected {self.value!r} to be falsy"
            )

    def to_be_none(self) -> None:
        """Assert that value is None."""
        if self.value is not None:
            raise ExpectationError(
                f"Expected {self.value!r} to be None"
            )

    def to_not_be_none(self) -> None:
        """Assert that value is not None."""
        if self.value is None:
            raise ExpectationError(
                "Expected value to not be None"
            )

    def to_have_attr(self, attr_name: str) -> None:
        """Assert that value has the specified attribute."""
        if not hasattr(self.value, attr_name):
            raise ExpectationError(
                f"Expected {self.value!r} to have attribute '{attr_name}'"
            )

    def to_be_instance_of(self, cls: type) -> None:
        """Assert that value is an instance of the specified class."""
        if not isinstance(self.value, cls):
            raise ExpectationError(
                f"Expected {self.value!r} to be instance of {cls.__name__}, "
                f"got {type(self.value).__name__}"
            )

    def to_not_be_instance_of(self, cls: type) -> None:
        """Assert that value is NOT an instance of the specified class."""
        if isinstance(self.value, cls):
            raise ExpectationError(
                f"Expected {self.value!r} to NOT be instance of {cls.__name__}"
            )

    def to_have_length(self, expected_length: int) -> None:
        """Assert that value has the specified length."""
        actual_length = len(self.value)
        if actual_length != expected_length:
            raise ExpectationError(
                f"Expected length {expected_length}, got {actual_length}"
            )

    def to_contain(self, item: Any) -> None:
        """Assert that value contains the specified item."""
        if item not in self.value:
            raise ExpectationError(
                f"Expected {self.value!r} to contain {item!r}"
            )

    def to_raise(self, exception_type: type[Exception]) -> None:
        """Assert that calling value raises the specified exception."""
        if not callable(self.value):
            raise ExpectationError(
                f"Expected a callable, got {type(self.value).__name__}"
            )
        try:
            self.value()
        except exception_type:
            return
        except Exception as e:
            raise ExpectationError(
                f"Expected {exception_type.__name__}, got {type(e).__name__}: {e}"
            )
        else:
            raise ExpectationError(
                f"Expected {exception_type.__name__} to be raised, but nothing was raised"
            )

    def to_not_equal(self, expected: Any) -> None:
        """Assert that value does not equal expected."""
        if self.value == expected:
            raise ExpectationError(
                f"Expected {self.value!r} to not equal {expected!r}"
            )

    def to_be_close_to(self, expected: float, tolerance: float = 0.01) -> None:
        """Assert that value is close to expected within tolerance."""
        if abs(self.value - expected) > tolerance:
            raise ExpectationError(
                f"Expected {self.value!r} to be close to {expected!r} (within {tolerance})"
            )

    def to_be_greater_than(self, expected: Any) -> None:
        """Assert that value is greater than expected."""
        if not (self.value > expected):
            raise ExpectationError(
                f"Expected {self.value!r} to be greater than {expected!r}"
            )

    def to_be_less_than(self, expected: Any) -> None:
        """Assert that value is less than expected."""
        if not (self.value < expected):
            raise ExpectationError(
                f"Expected {self.value!r} to be less than {expected!r}"
            )


def expect(value: Any) -> Expectation:
    """Create an expectation wrapper for making assertions."""
    return Expectation(value)
