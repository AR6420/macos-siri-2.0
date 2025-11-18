#!/bin/bash

# =============================================================================
# Voice Assistant - Comprehensive Test Runner
# =============================================================================
#
# This script runs all tests for the Voice Assistant project with comprehensive
# reporting, coverage analysis, and error checking.
#
# Usage:
#   ./scripts/run_tests.sh [options]
#
# Options:
#   --unit          Run only unit tests
#   --integration   Run only integration tests
#   --performance   Run only performance tests
#   --coverage      Generate coverage report
#   --verbose       Verbose output
#   --fast          Skip slow tests
#   --parallel      Run tests in parallel
#   --html          Generate HTML report
#   --help          Show this help message
#
# Examples:
#   ./scripts/run_tests.sh                    # Run all tests
#   ./scripts/run_tests.sh --unit --coverage  # Unit tests with coverage
#   ./scripts/run_tests.sh --fast --parallel  # Fast parallel execution
#
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_PERFORMANCE=false
RUN_ALL=true
GENERATE_COVERAGE=false
VERBOSE=false
SKIP_SLOW=false
PARALLEL=false
HTML_REPORT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --performance)
            RUN_PERFORMANCE=true
            RUN_ALL=false
            shift
            ;;
        --coverage)
            GENERATE_COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fast)
            SKIP_SLOW=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        --help|-h)
            grep '^#' "$0" | grep -v '#!/bin/bash' | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Print header
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}              Voice Assistant - Comprehensive Test Suite${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Installing dependencies...${NC}"
    if command -v poetry &> /dev/null; then
        poetry install --with dev
    else
        pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-timeout
    fi
fi

# Build pytest command
PYTEST_CMD="pytest"
PYTEST_ARGS="-v"

# Add coverage if requested
if [ "$GENERATE_COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=voice_assistant --cov-report=term-missing"

    if [ "$HTML_REPORT" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS --cov-report=html --cov-report=xml"
    fi
fi

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -s"
fi

# Skip slow tests if requested
if [ "$SKIP_SLOW" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
fi

# Parallel execution
if [ "$PARALLEL" = true ]; then
    if command -v pytest-xdist &> /dev/null || pip show pytest-xdist &> /dev/null; then
        PYTEST_ARGS="$PYTEST_ARGS -n auto"
    else
        echo -e "${YELLOW}pytest-xdist not installed, skipping parallel execution${NC}"
    fi
fi

# Create test output directory
mkdir -p test-results
mkdir -p htmlcov

# Run tests based on options
EXIT_CODE=0

# Function to run tests and capture results
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    local marker=$3

    echo -e "${BLUE}Running $suite_name...${NC}"
    echo ""

    local cmd="$PYTEST_CMD $PYTEST_ARGS"

    if [ -n "$marker" ]; then
        cmd="$cmd -m $marker"
    fi

    cmd="$cmd $test_path"

    # Run tests and capture output
    if eval "$cmd"; then
        echo -e "${GREEN}✓ $suite_name PASSED${NC}"
        echo ""
    else
        echo -e "${RED}✗ $suite_name FAILED${NC}"
        echo ""
        EXIT_CODE=1
    fi
}

# Run selected test suites
if [ "$RUN_ALL" = true ]; then
    echo -e "${BLUE}Running all test suites...${NC}"
    echo ""

    run_test_suite "Unit Tests - Audio" "tests/audio" "unit"
    run_test_suite "Unit Tests - STT" "tests/stt" "unit"
    run_test_suite "Unit Tests - LLM" "tests/llm" "unit"
    run_test_suite "Unit Tests - MCP" "tests/mcp" "unit"
    run_test_suite "Integration Tests - Pipeline" "tests/integration/test_pipeline.py" "integration"
    run_test_suite "Integration Tests - Edge Cases" "tests/integration/test_edge_cases.py" "integration"
    run_test_suite "Integration Tests - Workflows" "tests/integration/test_workflows.py" "integration"
    run_test_suite "Performance Tests" "tests/integration/test_performance.py" "slow"
else
    if [ "$RUN_UNIT" = true ]; then
        run_test_suite "Unit Tests" "tests/" "unit"
    fi

    if [ "$RUN_INTEGRATION" = true ]; then
        run_test_suite "Integration Tests" "tests/integration/" "integration"
    fi

    if [ "$RUN_PERFORMANCE" = true ]; then
        run_test_suite "Performance Tests" "tests/integration/test_performance.py" "slow"
    fi
fi

# Print summary
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}                            Test Summary${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests PASSED${NC}"
else
    echo -e "${RED}✗ Some tests FAILED${NC}"
fi

# Print coverage summary if generated
if [ "$GENERATE_COVERAGE" = true ]; then
    echo ""
    echo -e "${BLUE}Coverage Report:${NC}"
    echo ""

    if [ -f ".coverage" ]; then
        coverage report --skip-empty --sort=cover | tail -20
    fi

    if [ "$HTML_REPORT" = true ] && [ -d "htmlcov" ]; then
        echo ""
        echo -e "${BLUE}HTML coverage report generated: ${GREEN}htmlcov/index.html${NC}"
        echo -e "${BLUE}XML coverage report generated: ${GREEN}coverage.xml${NC}"
    fi
fi

# Print test results location
echo ""
echo -e "${BLUE}Test artifacts:${NC}"
echo "  - Test logs: test-results/"
echo "  - Coverage: htmlcov/"
echo ""

exit $EXIT_CODE
