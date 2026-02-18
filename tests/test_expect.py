"""
Unit tests for the expect assertion library.
"""

import pytest
from flaky import expect, ExpectationError


def test_to_equal_pass():
    """Test to_equal with matching values."""
    expect(5).to_equal(5)
    expect("hello").to_equal("hello")
    expect([1, 2, 3]).to_equal([1, 2, 3])


def test_to_equal_fail():
    """Test to_equal with non-matching values."""
    with pytest.raises(ExpectationError, match="Expected 5 to equal 6"):
        expect(5).to_equal(6)


def test_to_be_truthy_pass():
    """Test to_be_truthy with truthy values."""
    expect(True).to_be_truthy()
    expect(1).to_be_truthy()
    expect("hello").to_be_truthy()
    expect([1]).to_be_truthy()


def test_to_be_truthy_fail():
    """Test to_be_truthy with falsy values."""
    with pytest.raises(ExpectationError, match="to be truthy"):
        expect(False).to_be_truthy()
    
    with pytest.raises(ExpectationError, match="to be truthy"):
        expect("").to_be_truthy()


def test_to_be_falsy_pass():
    """Test to_be_falsy with falsy values."""
    expect(False).to_be_falsy()
    expect(0).to_be_falsy()
    expect("").to_be_falsy()
    expect([]).to_be_falsy()


def test_to_be_none_pass():
    """Test to_be_none with None."""
    expect(None).to_be_none()


def test_to_be_none_fail():
    """Test to_be_none with non-None value."""
    with pytest.raises(ExpectationError, match="to be None"):
        expect(5).to_be_none()


def test_to_not_be_none_pass():
    """Test to_not_be_none with non-None values."""
    expect(5).to_not_be_none()
    expect("").to_not_be_none()


def test_to_not_be_none_fail():
    """Test to_not_be_none with None."""
    with pytest.raises(ExpectationError, match="to not be None"):
        expect(None).to_not_be_none()


def test_to_have_length_pass():
    """Test to_have_length with correct length."""
    expect([1, 2, 3]).to_have_length(3)
    expect("hello").to_have_length(5)


def test_to_have_length_fail():
    """Test to_have_length with incorrect length."""
    with pytest.raises(ExpectationError, match="Expected length 5, got 3"):
        expect([1, 2, 3]).to_have_length(5)


def test_to_contain_pass():
    """Test to_contain with item in collection."""
    expect([1, 2, 3]).to_contain(2)
    expect("hello").to_contain("ell")


def test_to_contain_fail():
    """Test to_contain with item not in collection."""
    with pytest.raises(ExpectationError, match="to contain"):
        expect([1, 2, 3]).to_contain(5)


def test_to_be_instance_of_pass():
    """Test to_be_instance_of with correct type."""
    expect(5).to_be_instance_of(int)
    expect("hello").to_be_instance_of(str)
    expect([1, 2]).to_be_instance_of(list)


def test_to_be_instance_of_fail():
    """Test to_be_instance_of with incorrect type."""
    with pytest.raises(ExpectationError, match="to be instance of str"):
        expect(5).to_be_instance_of(str)


def test_to_be_greater_than_pass():
    """Test to_be_greater_than with larger value."""
    expect(10).to_be_greater_than(5)
    expect(5.5).to_be_greater_than(5.0)


def test_to_be_greater_than_fail():
    """Test to_be_greater_than with smaller or equal value."""
    with pytest.raises(ExpectationError, match="to be greater than"):
        expect(5).to_be_greater_than(10)


def test_to_be_less_than_pass():
    """Test to_be_less_than with smaller value."""
    expect(5).to_be_less_than(10)
    expect(5.0).to_be_less_than(5.5)


def test_to_be_less_than_fail():
    """Test to_be_less_than with larger or equal value."""
    with pytest.raises(ExpectationError, match="to be less than"):
        expect(10).to_be_less_than(5)


def test_to_be_close_to_pass():
    """Test to_be_close_to within tolerance."""
    expect(5.001).to_be_close_to(5.0, tolerance=0.01)
    expect(5.009).to_be_close_to(5.0, tolerance=0.01)


def test_to_be_close_to_fail():
    """Test to_be_close_to outside tolerance."""
    with pytest.raises(ExpectationError, match="to be close to"):
        expect(5.02).to_be_close_to(5.0, tolerance=0.01)


def test_to_raise_pass():
    """Test to_raise with correct exception."""
    def raises_value_error():
        raise ValueError("test error")
    
    expect(raises_value_error).to_raise(ValueError)


def test_to_raise_wrong_exception():
    """Test to_raise with wrong exception type."""
    def raises_value_error():
        raise ValueError("test error")
    
    with pytest.raises(ExpectationError, match="Expected TypeError"):
        expect(raises_value_error).to_raise(TypeError)


def test_to_raise_no_exception():
    """Test to_raise when no exception is raised."""
    def no_error():
        return 42
    
    with pytest.raises(ExpectationError, match="nothing was raised"):
        expect(no_error).to_raise(ValueError)


def test_to_not_equal_pass():
    """Test to_not_equal with different values."""
    expect(5).to_not_equal(6)
    expect("hello").to_not_equal("world")


def test_to_not_equal_fail():
    """Test to_not_equal with same values."""
    with pytest.raises(ExpectationError, match="to not equal"):
        expect(5).to_not_equal(5)
