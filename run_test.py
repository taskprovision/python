#!/usr/bin/env python3
"""
Direct test runner to bypass pytest command line issues.
"""
import pytest
import sys

def main():
    # Run the tests in simple_test.py
    sys.exit(pytest.main(['simple_test.py', '-v']))

if __name__ == '__main__':
    main()
