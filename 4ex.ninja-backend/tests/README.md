# 4ex.ninja Backend Testing Framework

This directory contains the comprehensive testing framework for the 4ex.ninja backend system, organized into logical categories for better maintainability and execution.

## Directory Structure

```
tests/
├── __init__.py                 # Package initialization
├── run_tests.py               # Master test runner script
├── days/                      # Day-specific milestone tests
│   ├── __init__.py
│   ├── test_day6_logging.py   # Day 6: Logging infrastructure tests
│   ├── test_day7_monitoring.py # Day 7: Monitoring system tests
│   ├── test_day8_simple.py    # Day 8: Simple critical system tests
│   └── test_day8_critical_systems.py # Day 8: Comprehensive critical system tests
├── unit/                      # Unit tests for individual components
│   ├── __init__.py
│   ├── test_api.py           # FastAPI application tests
│   ├── test_market_data.py   # Market data fetching tests
│   └── test_trend_strat.py   # Trend strategy tests
└── integration/               # Integration tests for system workflows
    ├── __init__.py
    ├── test_strategies.py     # Strategy integration tests
    └── test_oanda_connection.py # OANDA API integration tests
```

## Test Categories

### 📅 Days Tests (`tests/days/`)
Day-specific milestone tests that validate major development objectives:

- **Day 6**: Comprehensive logging infrastructure with structured logging, correlation IDs, and middleware
- **Day 7**: Monitoring system with health checks, performance metrics, and error tracking
- **Day 8**: Critical system error handling and alerting with circuit breakers, recovery strategies, and multi-channel alerts

### 🧪 Unit Tests (`tests/unit/`)
Individual component tests that validate specific functionality:

- **API Tests**: FastAPI application endpoints, middleware, and request/response handling
- **Market Data Tests**: OANDA data fetching, pagination, and storage functionality
- **Strategy Tests**: Individual trading strategy logic and signal generation

### 🔄 Integration Tests (`tests/integration/`)
End-to-end workflow tests that validate system interactions:

- **Strategy Integration**: Complete strategy execution workflows
- **OANDA Connection**: External API integration and data flow

## Running Tests

### Master Test Runner

Use the comprehensive test runner for maximum flexibility:

```bash
# Run all tests
python tests/run_tests.py

# Run specific category
python tests/run_tests.py --category days
python tests/run_tests.py --category unit
python tests/run_tests.py --category integration

# List available tests
python tests/run_tests.py --list

# Verbose output for debugging
python tests/run_tests.py --verbose
```

### Individual Test Files

Run specific test files directly:

```bash
# Day milestone tests
python tests/days/test_day6_logging.py
python tests/days/test_day7_monitoring.py
python tests/days/test_day8_simple.py

# Unit tests
python tests/unit/test_api.py
python tests/unit/test_market_data.py
python tests/unit/test_trend_strat.py

# Integration tests
python tests/integration/test_strategies.py
python tests/integration/test_oanda_connection.py
```

### Using pytest

For advanced testing features, use pytest:

```bash
# Run all tests with pytest
pytest tests/ -v

# Run specific category
pytest tests/days/ -v
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Test Implementation Guidelines

### Day Tests
- **Purpose**: Validate major development milestones
- **Scope**: Comprehensive feature validation
- **Dependencies**: May require external services (MongoDB, OANDA API)
- **Execution**: Can be run independently or as part of milestone validation

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Scope**: Single function or class validation
- **Dependencies**: Minimal external dependencies, use mocks when needed
- **Execution**: Fast execution, suitable for continuous integration

### Integration Tests
- **Purpose**: Validate component interactions and workflows
- **Scope**: Multi-component system validation
- **Dependencies**: May require external services and configuration
- **Execution**: Longer execution time, suitable for deployment validation

## Test Output and Reporting

### Console Output
All tests provide structured console output with:
- ✅ Success indicators
- ❌ Failure indicators
- 📊 Summary statistics
- 🎉 Celebration messages for full success

### Error Handling
Tests include comprehensive error handling:
- Graceful fallbacks for missing dependencies
- Clear error messages with context
- Timeout protection for long-running operations
- Resource cleanup after test completion

### Logging Integration
Tests leverage the logging infrastructure:
- Structured log output for debugging
- Correlation ID tracking across test operations
- Performance metrics collection
- Error tracking and alerting validation

## Continuous Integration

### GitHub Actions
The test framework is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run Backend Tests
  run: |
    cd 4ex.ninja-backend
    python tests/run_tests.py --category unit
    python tests/run_tests.py --category integration
```

### Test Dependencies
Required packages for full test execution:
- `pytest` - Advanced testing framework
- `fastapi` - API framework testing
- `httpx` - HTTP client for API tests
- `pandas` - Data manipulation for strategy tests
- `pymongo` - Database testing (optional)

### Environment Variables
Some tests require environment configuration:
```bash
export OANDA_API_KEY="your_api_key"
export OANDA_ACCOUNT_ID="your_account_id"
export MONGODB_URI="mongodb://localhost:27017"
```

## Test Development

### Adding New Tests

1. **Choose Category**: Determine if the test is a day milestone, unit test, or integration test
2. **Follow Naming**: Use `test_*.py` naming convention
3. **Use Template**: Follow existing test structure and patterns
4. **Include Documentation**: Add docstrings and comments for clarity
5. **Test Independence**: Ensure tests can run independently
6. **Clean Resources**: Include proper cleanup in tests

### Test Structure Template

```python
"""
Test Description - Brief description of what this test validates

Detailed description of the test purpose and scope.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / ".." / ".." / "src"))

def test_function_name():
    """Test specific functionality."""
    print("Testing functionality...")
    
    try:
        # Test implementation
        assert condition, "Test condition failed"
        print("✓ Test passed")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def main():
    """Run all tests in this file."""
    print("Test File Name")
    print("=" * 40)
    
    tests = [
        ("Test Description", test_function_name),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Print summary
    print("\n" + "=" * 40)
    print("Test Results Summary")
    print("=" * 40)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    for test_name, success, error in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
        if error:
            print(f"   Error: {error}")
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src` directory is in Python path
2. **Missing Dependencies**: Install required packages with `pip install -r requirements.txt`
3. **API Failures**: Check network connectivity and API credentials
4. **Database Errors**: Ensure MongoDB is running if required
5. **Timeout Issues**: Increase timeout values for slow operations

### Debug Mode

For detailed debugging:
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with maximum output
python tests/run_tests.py --verbose

# Use pytest with detailed output
pytest tests/ -v -s --tb=long
```

### Performance Optimization

For faster test execution:
- Run unit tests first (fastest)
- Use parallel execution with `pytest -n auto`
- Skip integration tests during development
- Use test fixtures for expensive setup operations

## Contributing

When contributing tests:
1. Follow the existing directory structure
2. Include comprehensive error handling
3. Add appropriate documentation
4. Test on multiple environments
5. Update this README if adding new categories

---

This testing framework provides comprehensive validation of the 4ex.ninja backend system while maintaining organization, maintainability, and ease of use for both development and CI/CD environments.
