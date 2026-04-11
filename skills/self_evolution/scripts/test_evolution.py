#!/usr/bin/env python3
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

"""Test script for self-evolution skill."""


def calculate_sum(numbers):
    """
    Calculate the sum of a list of numbers.

    :param numbers: List of numbers.
    :return: Sum of numbers.
    """
    return sum(numbers)


if __name__ == '__main__':
    # Test
    test_data = [1, 2, 3, 4, 5]
    print(f'Test Sum: {calculate_sum(test_data)}')
