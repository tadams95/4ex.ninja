# 4ex.ninja Backend Clean Architecture

This directory implements Clean Architecture principles for the 4ex.ninja backend, ensuring proper separation of concerns and maintainable code organization.

## Directory Structure

```
src/
├── core/                    # Core Business Logic (innermost layer)
│   ├── entities/           # Business entities and domain models
│   ├── interfaces/         # Abstract interfaces and contracts
│   └── use_cases/          # Business use cases and application logic
├── application/            # Application Layer
│   ├── dto/               # Data Transfer Objects
│   └── services/          # Application services
├── infrastructure/        # Infrastructure Layer (outermost layer)
│   ├── database/          # Database implementations
│   ├── external_services/ # External API integrations (OANDA, etc.)
│   └── repositories/      # Repository implementations
├── api/                   # API/Interface Layer
│   ├── dependencies/      # FastAPI dependencies
│   ├── middleware/        # HTTP middleware
│   └── routes/           # API route handlers
├── auth/                 # Authentication utilities (legacy)
├── config/              # Configuration management (legacy)
├── db/                  # Database utilities (legacy)
├── indicators/          # Technical indicators (legacy)
├── models/              # Data models (legacy)
├── strategies/          # Trading strategies (legacy)
├── utils/               # Utility functions (legacy)
└── main.py              # Application entry point
```

## Clean Architecture Layers

### 1. Core Layer (Business Logic)
- **entities/**: Contains the core business entities like Signal, MarketData, Strategy
- **interfaces/**: Defines abstract interfaces for repositories and services
- **use_cases/**: Implements business use cases (e.g., GenerateSignal, AnalyzeMarket)

### 2. Application Layer
- **dto/**: Data Transfer Objects for API communication
- **services/**: Application services that orchestrate use cases

### 3. Infrastructure Layer
- **database/**: Database connection managers and configurations
- **external_services/**: OANDA API, notification services, etc.
- **repositories/**: Concrete implementations of repository interfaces

### 4. API Layer
- **routes/**: FastAPI route handlers
- **middleware/**: HTTP middleware for authentication, CORS, etc.
- **dependencies/**: FastAPI dependency injection

## Migration Strategy

The legacy directories (auth/, config/, db/, etc.) will be gradually migrated to the new clean architecture structure while maintaining backward compatibility. This ensures:

1. No breaking changes during migration
2. Existing functionality continues to work
3. New features use the clean architecture
4. Legacy code is refactored incrementally

## Benefits

1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Testability**: Easy to unit test business logic in isolation
3. **Maintainability**: Clear structure makes code easier to understand and modify
4. **Scalability**: Architecture supports future growth and complexity
5. **Dependency Inversion**: Core logic doesn't depend on external frameworks
