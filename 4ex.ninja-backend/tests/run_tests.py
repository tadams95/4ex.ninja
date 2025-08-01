#!/usr/bin/env python3
"""
Master Test Runner for 4ex.ninja Backend

Comprehensive test runner that organizes and executes all tests in the backend system.
This script can run tests by category (days, unit, integration) or all tests.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Comprehensive test runner for the backend system."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.results = {}

    def discover_tests(self, category: Optional[str] = None) -> Dict[str, List[Path]]:
        """Discover all test files in the tests directory."""
        test_files = {"days": [], "unit": [], "integration": []}

        if category and category in test_files:
            # Run specific category
            category_dir = self.tests_dir / category
            if category_dir.exists():
                test_files[category] = list(category_dir.glob("test_*.py"))
        elif category is None:
            # Discover all tests
            for cat in test_files.keys():
                cat_dir = self.tests_dir / cat
                if cat_dir.exists():
                    test_files[cat] = list(cat_dir.glob("test_*.py"))

        return test_files

    def run_python_test(self, test_file: Path) -> tuple[bool, str]:
        """Run a Python test file directly."""
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            return success, output

        except subprocess.TimeoutExpired:
            return False, "Test timed out after 5 minutes"
        except Exception as e:
            return False, f"Error running test: {e}"

    def run_pytest_test(self, test_file: Path) -> tuple[bool, str]:
        """Run a test file with pytest."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300,
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            return success, output

        except subprocess.TimeoutExpired:
            return False, "Test timed out after 5 minutes"
        except Exception as e:
            return False, f"Error running pytest: {e}"

    def run_test_file(self, test_file: Path) -> tuple[bool, str]:
        """Run a single test file, trying both direct Python and pytest."""
        print(f"Running {test_file.name}...")

        # First try running directly as Python script
        success, output = self.run_python_test(test_file)

        if not success and "pytest" in test_file.read_text():
            # If direct run failed and file uses pytest, try pytest
            print(f"  Retrying {test_file.name} with pytest...")
            success, output = self.run_pytest_test(test_file)

        return success, output

    def run_category(
        self, category: str, test_files: List[Path]
    ) -> Dict[str, tuple[bool, str]]:
        """Run all tests in a category."""
        if not test_files:
            print(f"No tests found in {category} category")
            return {}

        print(f"\n{'='*20} {category.upper()} TESTS {'='*20}")

        results = {}

        for test_file in test_files:
            success, output = self.run_test_file(test_file)
            results[test_file.name] = (success, output)

            if success:
                print(f"✅ {test_file.name}: PASSED")
            else:
                print(f"❌ {test_file.name}: FAILED")

        return results

    def run_all_tests(
        self, category: Optional[str] = None
    ) -> Dict[str, Dict[str, tuple[bool, str]]]:
        """Run all discovered tests."""
        print("🧪 4ex.ninja Backend Test Runner")
        print("=" * 50)

        test_files = self.discover_tests(category)
        all_results = {}

        for cat, files in test_files.items():
            if files:  # Only run categories that have tests
                cat_results = self.run_category(cat, files)
                all_results[cat] = cat_results

        return all_results

    def print_summary(self, results: Dict[str, Dict[str, tuple[bool, str]]]):
        """Print comprehensive test summary."""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)

        total_passed = 0
        total_failed = 0

        for category, cat_results in results.items():
            if not cat_results:
                continue

            cat_passed = sum(1 for success, _ in cat_results.values() if success)
            cat_failed = len(cat_results) - cat_passed

            print(f"\n{category.upper()} Tests:")
            print(f"  Passed: {cat_passed}")
            print(f"  Failed: {cat_failed}")

            total_passed += cat_passed
            total_failed += cat_failed

            # Show failed tests with brief error info
            if cat_failed > 0:
                print(f"  Failed tests:")
                for test_name, (success, output) in cat_results.items():
                    if not success:
                        # Get first few lines of error
                        error_lines = output.split("\n")[:3]
                        error_preview = " ".join(error_lines).strip()
                        if len(error_preview) > 100:
                            error_preview = error_preview[:100] + "..."
                        print(f"    - {test_name}: {error_preview}")

        print(f"\n{'='*20} OVERALL RESULTS {'='*20}")
        print(f"Total Tests: {total_passed + total_failed}")
        print(f"Passed: {total_passed} ✅")
        print(f"Failed: {total_failed} ❌")

        if total_failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total_failed} test(s) failed.")

        success_rate = (
            (total_passed / (total_passed + total_failed) * 100)
            if (total_passed + total_failed) > 0
            else 0
        )
        print(f"Success Rate: {success_rate:.1f}%")

        return total_failed == 0


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="4ex.ninja Backend Test Runner")
    parser.add_argument(
        "--category",
        "-c",
        choices=["days", "unit", "integration"],
        help="Run tests from specific category only",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output for failed tests",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available tests without running them",
    )

    args = parser.parse_args()

    # Initialize test runner
    project_root = Path(__file__).parent.parent
    runner = TestRunner(project_root)

    if args.list:
        # List available tests
        test_files = runner.discover_tests()
        print("Available Tests:")
        print("=" * 30)

        for category, files in test_files.items():
            if files:
                print(f"\n{category.upper()}:")
                for test_file in files:
                    print(f"  - {test_file.name}")

        return 0

    # Run tests
    results = runner.run_all_tests(args.category)

    # Print summary
    success = runner.print_summary(results)

    # Show detailed output for failed tests if verbose
    if args.verbose:
        print("\n" + "=" * 50)
        print("📝 DETAILED FAILURE OUTPUT")
        print("=" * 50)

        for category, cat_results in results.items():
            for test_name, (test_success, output) in cat_results.items():
                if not test_success:
                    print(f"\n--- {test_name} ---")
                    print(output)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
