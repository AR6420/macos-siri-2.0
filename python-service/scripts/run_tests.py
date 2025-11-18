#!/usr/bin/env python3
"""
Voice Assistant - Python Test Runner

A Python-based test runner for CI/CD environments that don't support bash scripts.
This provides the same functionality as run_tests.sh but in pure Python.
"""

import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime


class TestRunner:
    """Comprehensive test runner with reporting"""

    def __init__(self):
        self.project_dir = Path(__file__).parent.parent
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_command(self, cmd: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run a shell command"""
        if capture_output:
            return subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True)
        else:
            return subprocess.run(cmd, cwd=self.project_dir)

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print("Checking dependencies...")

        try:
            result = self.run_command(["pytest", "--version"], capture_output=True)
            if result.returncode != 0:
                print("❌ pytest not installed")
                return False
            print(f"✓ {result.stdout.strip()}")
            return True
        except FileNotFoundError:
            print("❌ pytest not found")
            return False

    def run_test_suite(
        self,
        suite_name: str,
        test_path: str,
        marker: Optional[str] = None,
        extra_args: Optional[List[str]] = None
    ) -> bool:
        """Run a test suite and return success status"""
        print(f"\n{'=' * 80}")
        print(f"Running {suite_name}...")
        print(f"{'=' * 80}\n")

        cmd = ["pytest", "-v", test_path]

        if marker:
            cmd.extend(["-m", marker])

        if extra_args:
            cmd.extend(extra_args)

        start = datetime.now()
        result = self.run_command(cmd)
        end = datetime.now()

        duration = (end - start).total_seconds()
        success = result.returncode == 0

        self.results[suite_name] = {
            "success": success,
            "duration": duration,
            "returncode": result.returncode,
        }

        if success:
            print(f"\n✓ {suite_name} PASSED ({duration:.2f}s)")
        else:
            print(f"\n✗ {suite_name} FAILED ({duration:.2f}s)")

        return success

    def run_all_tests(
        self,
        coverage: bool = False,
        verbose: bool = False,
        skip_slow: bool = False,
        parallel: bool = False,
        html: bool = False
    ) -> bool:
        """Run all test suites"""
        self.start_time = datetime.now()

        # Build common arguments
        extra_args = []

        if coverage:
            extra_args.extend([
                "--cov=voice_assistant",
                "--cov-report=term-missing",
            ])
            if html:
                extra_args.extend([
                    "--cov-report=html",
                    "--cov-report=xml",
                ])

        if verbose:
            extra_args.append("-s")

        if skip_slow:
            extra_args.extend(["-m", "not slow"])

        if parallel:
            # Check if pytest-xdist is available
            try:
                subprocess.run(["pytest", "--version"], capture_output=True, check=True)
                extra_args.extend(["-n", "auto"])
            except:
                print("⚠ pytest-xdist not available, skipping parallel execution")

        # Run test suites
        all_passed = True

        # Unit tests
        all_passed &= self.run_test_suite(
            "Unit Tests - Audio",
            "tests/audio",
            "unit",
            extra_args
        )

        all_passed &= self.run_test_suite(
            "Unit Tests - STT",
            "tests/stt",
            "unit",
            extra_args
        )

        all_passed &= self.run_test_suite(
            "Unit Tests - LLM",
            "tests/llm",
            "unit",
            extra_args
        )

        all_passed &= self.run_test_suite(
            "Unit Tests - MCP",
            "tests/mcp",
            "unit",
            extra_args
        )

        # Integration tests
        all_passed &= self.run_test_suite(
            "Integration Tests - Pipeline",
            "tests/integration/test_pipeline.py",
            "integration",
            extra_args
        )

        all_passed &= self.run_test_suite(
            "Integration Tests - Edge Cases",
            "tests/integration/test_edge_cases.py",
            "integration",
            extra_args
        )

        all_passed &= self.run_test_suite(
            "Integration Tests - Workflows",
            "tests/integration/test_workflows.py",
            "integration",
            extra_args
        )

        # Performance tests (unless skipping slow tests)
        if not skip_slow:
            all_passed &= self.run_test_suite(
                "Performance Tests",
                "tests/integration/test_performance.py",
                "slow",
                extra_args
            )

        self.end_time = datetime.now()

        return all_passed

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'=' * 80}")
        print("Test Summary")
        print(f"{'=' * 80}\n")

        if not self.results:
            print("No tests were run.")
            return

        total_duration = (self.end_time - self.start_time).total_seconds()

        # Print individual results
        passed_count = 0
        failed_count = 0

        for suite_name, result in self.results.items():
            status = "✓ PASSED" if result["success"] else "✗ FAILED"
            duration = result["duration"]
            print(f"  {status:12} {suite_name:40} ({duration:.2f}s)")

            if result["success"]:
                passed_count += 1
            else:
                failed_count += 1

        # Print overall summary
        print(f"\n{'=' * 80}")
        print(f"Total: {len(self.results)} test suites")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print(f"Total time: {total_duration:.2f}s")
        print(f"{'=' * 80}\n")

        # Check for coverage report
        coverage_file = self.project_dir / "htmlcov" / "index.html"
        if coverage_file.exists():
            print(f"📊 HTML coverage report: {coverage_file}")

        xml_coverage = self.project_dir / "coverage.xml"
        if xml_coverage.exists():
            print(f"📊 XML coverage report: {xml_coverage}")

        print()

    def save_results_json(self, output_path: Path):
        """Save test results as JSON"""
        data = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
            "results": self.results,
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"📄 Test results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Voice Assistant Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run only performance tests"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML reports"
    )
    parser.add_argument(
        "--json",
        type=str,
        metavar="PATH",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    # Create test runner
    runner = TestRunner()

    # Check dependencies
    if not runner.check_dependencies():
        print("\n❌ Required dependencies not installed")
        print("Run: pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-timeout")
        return 1

    # Run tests
    print("\n" + "=" * 80)
    print("Voice Assistant - Comprehensive Test Suite")
    print("=" * 80 + "\n")

    all_passed = runner.run_all_tests(
        coverage=args.coverage,
        verbose=args.verbose,
        skip_slow=args.fast,
        parallel=args.parallel,
        html=args.html
    )

    # Print summary
    runner.print_summary()

    # Save JSON results if requested
    if args.json:
        runner.save_results_json(Path(args.json))

    # Return exit code
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
