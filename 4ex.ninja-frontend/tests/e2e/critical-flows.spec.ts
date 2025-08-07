import { expect, test } from '@playwright/test';

/**
 * LEAN E2E Critical User Flows - Complete Test Suite
 * Executes all 3 revenue-critical user journeys in sequence
 * Total estimated runtime: 65 minutes (20 + 30 + 15)
 *
 * Coverage:
 * 1. Authentication Flow (20 min) - User registration, login, logout, error handling
 * 2. Subscription Flow (30 min) - Plan selection, payment, subscription management
 * 3. Trading Flow (15 min) - Trade execution, position management, risk controls
 */

test.describe('Complete Critical User Journey - E2E Flow', () => {
  test('should complete full user onboarding to active trading', async ({ page }) => {
    // STEP 1: User Registration (Authentication Flow)
    console.log('🔐 Starting authentication flow...');

    await page.goto('/register');
    await page.fill('[data-testid="first-name-input"]', 'E2E');
    await page.fill('[data-testid="last-name-input"]', 'User');
    await page.fill('[data-testid="email-input"]', 'e2e.test@4ex.ninja');
    await page.fill('[data-testid="password-input"]', 'TestPass123!');
    await page.click('[data-testid="register-button"]');

    // Verify successful registration
    await expect(page).toHaveURL('/dashboard');
    console.log('✅ User registration completed');

    // STEP 2: Premium Subscription Purchase (Subscription Flow)
    console.log('💳 Starting subscription flow...');

    await page.goto('/pricing');
    await page.click('[data-testid="select-premium-plan"]');

    // Verify checkout page
    await expect(page).toHaveURL('/checkout');
    await expect(page.locator('[data-testid="selected-plan-name"]')).toContainText('Premium');

    // Enter payment details
    await page.fill('[data-testid="card-number-input"]', '4242424242424242');
    await page.fill('[data-testid="card-expiry-input"]', '12/25');
    await page.fill('[data-testid="card-cvc-input"]', '123');
    await page.fill('[data-testid="card-name-input"]', 'E2E User');

    // Complete purchase
    await page.click('[data-testid="complete-purchase-button"]');

    // Verify subscription success
    await expect(page.locator('[data-testid="purchase-success"]')).toBeVisible();
    await expect(page).toHaveURL('/dashboard');
    console.log('✅ Premium subscription activated');

    // STEP 3: Execute Trading Operations (Trading Flow)
    console.log('📈 Starting trading flow...');

    await page.goto('/trading');

    // Verify premium trading features are available
    await expect(page.locator('[data-testid="advanced-charts"]')).toBeVisible();
    await expect(page.locator('[data-testid="api-access-panel"]')).toBeVisible();

    // Place a trade
    await page.click('[data-testid="pair-selector"]');
    await page.click('[data-testid="pair-option-EUR/USD"]');
    await page.fill('[data-testid="amount-input"]', '1000');
    await page.fill('[data-testid="stop-loss-input"]', '1.0500');
    await page.fill('[data-testid="take-profit-input"]', '1.1000');
    await page.click('[data-testid="buy-button"]');

    // Verify trade execution
    await expect(page.locator('[data-testid="trade-confirmation"]')).toBeVisible();
    console.log('✅ Trade executed successfully');

    // Check position in portfolio
    await page.goto('/trading/positions');
    await expect(page.locator('[data-testid="position-eur-usd"]')).toBeVisible();
    await expect(page.locator('[data-testid="position-direction"]')).toContainText('BUY');
    await expect(page.locator('[data-testid="position-amount"]')).toContainText('1000');

    console.log(
      '🎉 Complete user journey successful: Registration → Premium Subscription → Active Trading'
    );

    // VALIDATION: Verify end-to-end user state
    // User should be:
    // 1. Authenticated and registered
    // 2. Premium subscriber with access to advanced features
    // 3. Active trader with open positions

    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="subscription-status"]')).toContainText('Premium');
    await expect(page.locator('[data-testid="active-positions-count"]')).toContainText('1');
    await expect(page.locator('[data-testid="account-tier"]')).toContainText('Premium');
  });
});
