#!/usr/bin/env python3
# Copyright 2026 Bob Ros
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple Evolver script for testing."""def calculate_sum(numbers):."""Calculate the sum of a list of numbers."""
    result = 0
    for num in numbers:
        result += num
    return result


def find_max(numbers):
    """Find the maximum value in a list of numbers."""
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val


def test_functions():
    """Run tests for simple functions."""
    nums = [1, 2, 3, 4, 5]

    sum_res = calculate_sum(nums)
    assert sum_res == 15, f'Expected 15, got {sum_res}'

    max_res = find_max(nums)
    assert max_res == 5, f'Expected 5, got {max_res}'

    empty_res = find_max([])
    assert empty_res is None, f'Expected None, got {empty_res}'

    print('Simple Evolver tests passed!')


if __name__ == '__main__':
    test_functions()
    print('Simple Evolver loaded.')
