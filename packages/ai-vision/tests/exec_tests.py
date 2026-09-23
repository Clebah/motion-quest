"""Explicit test runner using unittest."""
import sys
import unittest

# Ensure root package is in path
sys.path.insert(0, ".")

from tests.run_tests import TestAiVisionWorker


def run():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAiVisionWorker))
    # Auto-discover any other tests/test_*.py containing unittest.TestCase classes,
    # so new suites are picked up without editing this runner again.
    suite.addTests(loader.discover(start_dir="tests", pattern="test_*.py"))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("ALL_TESTS_PASSED_SUCCESSFULLY")


if __name__ == "__main__":
    run()
