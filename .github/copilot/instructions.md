# GitHub Copilot Project Instructions

## Project Context

This is a forex trading strategy project named 4ex.ninja, focusing on algorithmic trading using moving average crossover strategies and other technical indicators. The system fetches price data from MongoDB, analyzes it, and generates trading signals.

## Code Style Guidelines

- Use Google-style docstrings for all functions and classes
- Variable naming: snake_case for variables and functions, PascalCase for classes
- Maximum line length is 88 characters (Black formatter standard)
- Include type hints for all function parameters and return values
- Prefer async/await patterns for I/O operations
- Use meaningful variable names that reflect financial/trading concepts

## Domain-Specific Knowledge

- The project deals with forex trading pairs (e.g., "EURUSD", "GBPJPY")
- ATR = Average True Range, a volatility indicator
- SL = Stop Loss, TP = Take Profit
- MA = Moving Average
- Pip = Price Interest Point, a standard unit of price movement
- JPY pairs use different pip calculation (×100 vs ×10000)

## Project Structure

- `/config/`: Configuration settings for strategies and database connections
- `/src/strategies/`: Contains strategy implementation classes
- `/src/data/`: Data fetching and processing components
- `/src/utils/`: Utility functions for calculations and helpers
- `/tests/`: Unit and integration tests

## Code Generation Priorities

1. Error handling: Include comprehensive error handling for network/database operations
2. Logging: Implement detailed logging for debugging and monitoring
3. Performance: Optimize for speed in data processing functions
4. Testing: Consider testability in function design
5. Security: Ensure secure handling of API keys and connection strings

## Common Patterns

- Use decorator pattern for timing and logging operations
- For database operations, always include error handling and connection pooling
- For numerical calculations, use Decimal type for financial values to avoid floating-point errors
- For asynchronous operations, use asyncio for concurrent processing
