# Voice Assistant - Testing Quick Reference Guide

## Quick Start

### Run All Tests
```bash
cd python-service
./scripts/run_tests.sh
```

### Run with Coverage
```bash
./scripts/run_tests.sh --coverage --html
# View report: open htmlcov/index.html
```

---

## Common Test Commands

### By Test Type

```bash
# Unit tests only
./scripts/run_tests.sh --unit

# Integration tests only
./scripts/run_tests.sh --integration

# Performance tests only
./scripts/run_tests.sh --performance
```

### By Component

```bash
# Audio pipeline tests
pytest tests/audio/ -v

# Speech-to-text tests
pytest tests/stt/ -v

# LLM client tests
pytest tests/llm/ -v

# MCP server tests
pytest tests/mcp/ -v

# Integration tests
pytest tests/integration/ -v
```

### Specific Test Files

```bash
# Pipeline integration
pytest tests/integration/test_pipeline.py -v

# Edge cases
pytest tests/integration/test_edge_cases.py -v

# Workflows
pytest tests/integration/test_workflows.py -v

# Performance
pytest tests/integration/test_performance.py -v
```

---

## Test Markers

### Run tests by marker

```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v

# Slow tests (performance benchmarks)
pytest -m slow -v

# Skip slow tests
pytest -m "not slow" -v

# macOS-specific tests
pytest -m macos -v
```

---

## Coverage Reports

### Generate Coverage

```bash
# Terminal report
pytest --cov=voice_assistant --cov-report=term-missing

# HTML report
pytest --cov=voice_assistant --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=voice_assistant --cov-report=xml
```

### Coverage for specific module

```bash
# Audio module only
pytest tests/audio/ --cov=voice_assistant.audio --cov-report=term

# LLM module only
pytest tests/llm/ --cov=voice_assistant.llm --cov-report=term
```

---

## Debugging Tests

### Show print statements

```bash
pytest -s tests/integration/test_pipeline.py
```

### Verbose failure output

```bash
pytest -vv tests/integration/test_pipeline.py
```

### Drop into debugger on failure

```bash
pytest --pdb tests/integration/test_pipeline.py
```

### Show local variables on failure

```bash
pytest -l tests/integration/test_pipeline.py
```

### Run specific test function

```bash
pytest tests/integration/test_pipeline.py::test_pipeline_with_tool_calls -v
```

### Run tests matching pattern

```bash
# All tests with "tool" in name
pytest -k tool -v

# All tests with "error" in name
pytest -k error -v
```

---

## Performance Testing

### Run all performance tests

```bash
pytest tests/integration/test_performance.py -v -s
```

### Run specific performance test

```bash
pytest tests/integration/test_performance.py::test_e2e_simple_query -v -s
```

### With timing information

```bash
pytest tests/integration/test_performance.py -v -s --durations=10
```

---

## CI/CD Testing

### Python test runner

```bash
# Run all tests with JSON output
python scripts/run_tests.py --coverage --json test-results.json

# Fast mode (skip slow tests)
python scripts/run_tests.py --fast --parallel
```

### GitHub Actions locally (using act)

```bash
# Install act: https://github.com/nektos/act
act -j test
```

---

## Generating Test Fixtures

### Create all audio fixtures

```bash
cd tests/fixtures
python audio_fixtures.py

# Generates:
# - silence_2s.wav
# - noise_2s.wav
# - wake_word_hey_claude.wav
# - command_*.wav (10 commands)
# - full_*_wakeword_plus_command.wav (5 complete samples)
```

### Use fixtures in tests

```python
from tests.fixtures import (
    generate_silence,
    generate_wake_word_audio,
    generate_command_audio,
)

# Generate audio on the fly
audio = generate_wake_word_audio()

# Or load from file
from tests.fixtures import load_wav
audio, sample_rate = load_wav("tests/fixtures/audio/wake_word_hey_claude.wav")
```

---

## Mock Data

### Use mock data in tests

```python
from tests.fixtures import (
    get_mock_transcription,
    get_mock_llm_response,
    get_mock_tool_result,
)

# Get mock transcription
transcription = get_mock_transcription("weather_query")

# Get mock LLM response
response = get_mock_llm_response("time")

# Get mock tool result
result = get_mock_tool_result("execute_applescript_safari")
```

---

## Common Issues

### Import errors

```bash
# Make sure you're in the python-service directory
cd python-service

# Install dependencies
poetry install

# Or activate virtual environment
poetry shell
pytest
```

### Missing dependencies

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-timeout

# Or with Poetry
poetry install --with dev
```

### Tests fail due to missing files

```bash
# Generate test fixtures
cd tests/fixtures
python audio_fixtures.py
```

### Permission errors on macOS

Some tests require macOS permissions:
- Microphone access
- Accessibility access
- Full Disk Access (for Messages)

Grant permissions in System Settings > Privacy & Security

---

## Test Organization

### Test Structure

```
tests/
├── Unit Tests (test core functionality in isolation)
│   ├── audio/          # Audio pipeline components
│   ├── stt/            # Speech-to-text
│   ├── llm/            # LLM clients
│   └── mcp/            # MCP server and tools
│
├── Integration Tests (test components working together)
│   ├── test_pipeline.py      # Full pipeline
│   ├── test_performance.py   # Performance benchmarks
│   ├── test_edge_cases.py    # Edge cases and errors
│   └── test_workflows.py     # User scenarios
│
└── Fixtures (test data and utilities)
    ├── audio_fixtures.py     # Audio generation
    └── mock_data.py          # Mock responses
```

### Test Naming Convention

- `test_*.py` - Test files
- `test_*()` - Test functions
- `Test*` - Test classes

---

## Best Practices

### Writing New Tests

1. **Use fixtures for setup**
   ```python
   @pytest.fixture
   def my_fixture():
       return setup_data()

   def test_something(my_fixture):
       assert my_fixture.value == expected
   ```

2. **Use async for async code**
   ```python
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_operation()
       assert result is not None
   ```

3. **Use markers for categorization**
   ```python
   @pytest.mark.integration
   @pytest.mark.slow
   async def test_integration():
       pass
   ```

4. **Mock external dependencies**
   ```python
   from unittest.mock import AsyncMock

   mock_llm = AsyncMock()
   mock_llm.complete.return_value = expected_response
   ```

### Running Tests Efficiently

1. **Use fast mode during development**
   ```bash
   pytest -m "not slow" -v
   ```

2. **Run specific tests while debugging**
   ```bash
   pytest tests/integration/test_pipeline.py::test_specific -v
   ```

3. **Use parallel execution for full suite**
   ```bash
   pytest -n auto
   ```

---

## Continuous Integration

### Pre-commit Checks

```bash
# Run before committing
./scripts/run_tests.sh --fast --coverage
```

### GitHub Actions

Tests run automatically on:
- Push to main/develop/claude/* branches
- Pull requests
- Daily at 2 AM UTC

View results: https://github.com/yourorg/repo/actions

---

## Getting Help

### View test documentation

```python
# In Python
import pytest
help(pytest)

# View specific test
pytest tests/integration/test_pipeline.py --help
```

### Common pytest options

```
-v, --verbose        Verbose output
-s, --capture=no     Show print statements
-x, --exitfirst      Exit on first failure
-k EXPRESSION        Run tests matching expression
-m MARKER            Run tests with marker
--pdb                Drop into debugger on failure
--lf, --last-failed  Run only last failed tests
--ff, --failed-first Run failed tests first
--durations=N        Show N slowest tests
```

---

## Summary Commands

```bash
# Development workflow
pytest -m "not slow" -v -s        # Fast development testing
pytest -k "pipeline" -v           # Test specific component
pytest --lf -v                    # Re-run last failures

# Pre-commit
./scripts/run_tests.sh --fast --coverage

# Full test suite
./scripts/run_tests.sh --coverage --html

# CI/CD
python scripts/run_tests.py --coverage --json results.json
```

---

For detailed information, see [TEST_REPORT.md](TEST_REPORT.md)
