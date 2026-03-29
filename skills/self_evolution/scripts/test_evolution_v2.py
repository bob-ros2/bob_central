# Copyright 2026 Bob Ros
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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