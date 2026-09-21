"""Explicit test runner using unittest."""
import sys
import unittest

# Ensure root package is in path
sys.path.insert(0, ".")

from tests.run_tests import TestAiVisionWorker


def run():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAiVisionWorker)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("ALL_TESTS_PASSED_SUCCESSFULLY")


if __name__ == "__main__":
    run()
