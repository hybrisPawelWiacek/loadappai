# Manual Tests

This directory contains scripts for manual testing of external APIs and services. These tests are not part of the automated test suite and require proper API credentials to run.

## Available Tests

### API Tests
- `test_gmaps.py` - Tests Google Maps API integration
- `test_openai.py` - Tests OpenAI API integration

## Usage

1. Ensure you have the required API keys in your `.env` file
2. Run tests from the project root:
   ```bash
   python -m tests.manual.api.test_gmaps
   python -m tests.manual.api.test_openai
   ```

## Adding New Tests

When adding new manual tests:
1. Create a new subdirectory if needed (e.g., api/, load/, etc.)
2. Add test files with clear, descriptive names
3. Document usage and requirements in this README
