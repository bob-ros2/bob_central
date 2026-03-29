#!/usr/bin/env python3
"""Test script for self-evolution skill."""


def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    result = 0
    for num in numbers:
        result += num
    return result


def find_max(numbers):
    """Find the larger number in a list."""
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val


def test_functions():
    """Run tests for the sample functions."""
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