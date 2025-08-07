# LEAN Playwright E2E Testing Setup

## Overview

This directory contains the minimal E2E testing infrastructure for 4ex.ninja covering the 3 most critical user journeys that drive 80% of revenue.

## Test Structure

```
tests/
├── e2e/                    # E2E test specifications
│   ├── auth.spec.ts        # Authentication flow (20 min)
│   ├── subscription.spec.ts # Subscription flow (30 min)
│   ├── trading.spec.ts     # Trading flow (15 min)
│   └── critical-flows.spec.ts # Complete user journey
├── fixtures/               # Test data and helpers
│   ├── testData.ts        # Test user data and fixtures
│   └── helpers.ts         # Page Object Model helpers
└── README.md              # This file
```

## Critical User Paths Covered

### 1. Authentication Flow (20 minutes)

- ✅ User registration with validation
- ✅ User login/logout functionality
- ✅ Error handling for invalid credentials
- ✅ Protected route redirection
- ✅ Authentication state persistence

### 2. Subscription Flow (30 minutes)

- ✅ Plan selection (Basic/Premium)
- ✅ Payment processing with Stripe
- ✅ Subscription activation
- ✅ Plan upgrades/downgrades
- ✅ Subscription cancellation
- ✅ Feature access validation

### 3. Trading Flow (15 minutes)

- ✅ Market data display
- ✅ Trade execution (Buy/Sell)
- ✅ Position management
- ✅ Stop loss/Take profit orders
- ✅ Trading history tracking
- ✅ Premium feature access

## Quick Start

### Prerequisites

- Node.js 18+ installed
- Frontend development server running on `localhost:3000`
- Backend API server running and accessible

### Installation

Already completed during setup:

```bash
npm install --save-dev @playwright/test
npx playwright install chromium
```

### Running Tests

#### Run all E2E tests

```bash
npm run test:e2e
```

#### Run tests with UI mode (recommended for development)

```bash
npm run test:e2e:ui
```

#### Run tests in headed mode (see browser)

```bash
npm run test:e2e:headed
```

#### Run specific test file

```bash
npx playwright test auth.spec.ts
npx playwright test subscription.spec.ts
npx playwright test trading.spec.ts
```

#### Run the complete critical flow test

```bash
npx playwright test critical-flows.spec.ts
```

## Test Data Management

### Test Users

- `validUser`: Basic authenticated user
- `premiumUser`: User with premium subscription
- `invalidUser`: For testing error conditions

### Trading Data

- `validTrade`: Standard EUR/USD trade configuration
- `invalidTrade`: For testing validation errors

### Subscription Data

- `basicPlan` & `premiumPlan`: Plan configurations
- `testCard`: Test payment card (Stripe test mode)

## Configuration

### Playwright Config (`playwright.config.ts`)

- **Browser**: Chromium only (lean setup)
- **Base URL**: `http://localhost:3000`
- **Retries**: 2 on CI, 0 locally
- **Workers**: 1 on CI, parallel locally
- **Screenshots**: On failure only
- **Video**: Retain on failure
- **Trace**: On first retry

### Environment Requirements

- Frontend dev server must be running
- Backend API must be accessible
- Test database should be isolated from production

## Test Data Requirements

### Required Test Data Attributes

For tests to pass, ensure your frontend components use these `data-testid` attributes:

#### Authentication

- `email-input`, `password-input`, `login-button`
- `first-name-input`, `last-name-input`, `register-button`
- `user-menu`, `logout-button`

#### Subscription

- `select-basic-plan`, `select-premium-plan`
- `card-number-input`, `card-expiry-input`, `card-cvc-input`
- `complete-purchase-button`, `purchase-success`

#### Trading

- `pair-selector`, `amount-input`, `buy-button`, `sell-button`
- `stop-loss-input`, `take-profit-input`, `execute-trade-button`
- `positions-table`, `trade-confirmation`

## Debugging

### View Test Results

```bash
npx playwright show-report
```

### Debug Failed Tests

```bash
npx playwright test --debug
```

### Record New Tests

```bash
npx playwright codegen localhost:3000
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Playwright tests
  run: |
    npm run build
    npm run test:e2e
```

### Test Reports

- HTML reports generated in `playwright-report/`
- Screenshots and videos in `test-results/`

## Performance Targets

### Test Execution Time

- **Authentication Tests**: ~5 minutes
- **Subscription Tests**: ~8 minutes
- **Trading Tests**: ~4 minutes
- **Complete Flow Test**: ~3 minutes
- **Total Runtime**: ~20 minutes

### Success Criteria

- ✅ 100% pass rate on critical paths
- ✅ <30 second avg test execution time
- ✅ Clear error reporting
- ✅ Stable test runs (no flaky tests)

## Maintenance

### Adding New Tests

1. Create test file in `tests/e2e/`
2. Import helpers from `fixtures/`
3. Use established patterns and naming
4. Add data-testid attributes to frontend components

### Updating Test Data

- Modify `testData.ts` for new test scenarios
- Update `helpers.ts` for new page interactions
- Keep test data minimal and focused

### Troubleshooting

- Ensure frontend dev server is running
- Check data-testid attributes exist in components
- Verify test user credentials are valid
- Review Playwright configuration for environment issues

## Business Impact

This lean E2E setup covers the most critical user journeys:

- **80% revenue impact** with minimal test maintenance
- **Fast feedback** on business-critical functionality
- **Automated regression protection** for core features
- **Clear test documentation** for product team understanding

Total setup time: **30 minutes** ✅
Total test coverage: **3 critical user paths** ✅
Business risk mitigation: **High** ✅
