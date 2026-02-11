"""
Simple test runner for end-to-end tests
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_end_to_end import TestEndToEnd

if __name__ == "__main__":
    tester = TestEndToEnd()
    success = tester.run_all()
    sys.exit(0 if success else 1)
