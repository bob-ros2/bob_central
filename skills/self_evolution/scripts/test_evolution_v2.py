#!/usr/bin/env python3
"""Test script for self-evolution skill v2."""


def calculate_sum(numbers):
    """Calculate the sum using the built-in sum() function."""
    return sum(numbers)


def find_max(numbers):
    """Find the max value in a list of numbers."""
    if not numbers:
        return None
    return max(numbers)


def test_functions():
    """Run tests for optimized functions."""
    test_nums = [1, 2, 3, 4, 5]

    sum_result = calculate_sum(test_nums)
    assert sum_result == 15, f'Expected 15, got {sum_result}'

    max_result = find_max(test_nums)
    assert max_result == 5, f'Expected 5, got {max_result}'

    empty_result = find_max([])
    assert empty_result is None, f'Expected None, got {empty_result}'

    print('All tests passed!')


if __name__ == '__main__':
    test_functions()