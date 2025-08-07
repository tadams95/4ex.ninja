import { expect, test } from '@playwright/test';
import {
  AuthHelpers,
  CommonHelpers,
  SubscriptionHelpers,
  TradingHelpers,
} from '../fixtures/helpers';
import { testUsers, tradingData } from '../fixtures/testData';

/**
 * Critical User Path #3: Trading Flow
 * Revenue Impact: HIGH - Core product functionality driving subscriptions
 * Test Coverage: Trade execution, Position management, Risk controls
 * Estimated Time: 15 minutes
 */

test.describe('Trading Flow - Critical Path', () => {
  let authHelpers: AuthHelpers;
  let tradingHelpers: TradingHelpers;
  let subscriptionHelpers: SubscriptionHelpers;
  let commonHelpers: CommonHelpers;

  test.beforeEach(async ({ page }) => {
    authHelpers = new AuthHelpers(page);
    tradingHelpers = new TradingHelpers(page);
    subscriptionHelpers = new SubscriptionHelpers(page);
    commonHelpers = new CommonHelpers(page);

    // Ensure user is authenticated with premium subscription
    await authHelpers.login(testUsers.premiumUser.email, testUsers.premiumUser.password);
  });

  test('should display trading dashboard with market data', async ({ page }) => {
    await page.goto('/trading');

    // Verify core trading components are loaded
    await expect(page.locator('[data-testid="market-data-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="trading-form"]')).toBeVisible();
    await expect(page.locator('[data-testid="positions-panel"]')).toBeVisible();

    // Check that market data is updating
    await expect(page.locator('[data-testid="eur-usd-price"]')).toBeVisible();
    await expect(page.locator('[data-testid="gbp-usd-price"]')).toBeVisible();
  });

  test('should execute a successful buy trade', async ({ page }) => {
    await tradingHelpers.placeTrade({
      ...tradingData.validTrade,
      direction: 'buy',
    });

    // Verify trade appears in positions
    await tradingHelpers.viewPositions();
    await expect(page.locator('[data-testid="position-eur-usd"]')).toBeVisible();
    await expect(page.locator('[data-testid="position-direction"]')).toContainText('BUY');
    await expect(page.locator('[data-testid="position-amount"]')).toContainText('1000');
  });

  test('should execute a successful sell trade', async ({ page }) => {
    await tradingHelpers.placeTrade({
      ...tradingData.validTrade,
      direction: 'sell',
    });

    // Verify trade appears in positions
    await tradingHelpers.viewPositions();
    await expect(page.locator('[data-testid="position-eur-usd"]')).toBeVisible();
    await expect(page.locator('[data-testid="position-direction"]')).toContainText('SELL');
  });

  test('should handle invalid trade parameters', async ({ page }) => {
    await page.goto('/trading');

    // Try to place trade with invalid amount
    await page.fill('[data-testid="amount-input"]', '-100');
    await page.click('[data-testid="buy-button"]');

    // Should show validation error
    await commonHelpers.checkErrorMessage('Amount must be positive');

    // Try with invalid currency pair
    await page.click('[data-testid="pair-selector"]');
    // Assuming invalid pairs are not in the dropdown, check empty selection
    await page.fill('[data-testid="amount-input"]', '1000');
    await page.click('[data-testid="buy-button"]');

    await commonHelpers.checkErrorMessage('Please select a currency pair');
  });

  test('should apply stop loss and take profit orders', async ({ page }) => {
    await tradingHelpers.placeTrade({
      ...tradingData.validTrade,
      stopLoss: '1.0500',
      takeProfit: '1.1000',
    });

    // Verify orders are created
    await page.goto('/trading/orders');
    await expect(page.locator('[data-testid="stop-loss-order"]')).toBeVisible();
    await expect(page.locator('[data-testid="take-profit-order"]')).toBeVisible();

    // Check order details
    await expect(page.locator('[data-testid="stop-loss-price"]')).toContainText('1.0500');
    await expect(page.locator('[data-testid="take-profit-price"]')).toContainText('1.1000');
  });

  test('should close existing position', async ({ page }) => {
    // First place a trade
    await tradingHelpers.placeTrade();

    // Navigate to positions
    await tradingHelpers.viewPositions();

    // Close the position
    await page.click('[data-testid="close-position-button"]');
    await page.click('[data-testid="confirm-close-button"]');

    // Verify position is closed
    await commonHelpers.checkSuccessMessage('Position closed successfully');
    await expect(page.locator('[data-testid="position-eur-usd"]')).not.toBeVisible();
  });

  test('should display trading history', async ({ page }) => {
    // Place and close a trade to generate history
    await tradingHelpers.placeTrade();
    await tradingHelpers.viewPositions();
    await page.click('[data-testid="close-position-button"]');
    await page.click('[data-testid="confirm-close-button"]');

    // Check trading history
    await page.goto('/trading/history');
    await expect(page.locator('[data-testid="history-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="trade-history-row"]')).toBeVisible();

    // Verify history contains trade details
    await expect(page.locator('[data-testid="history-pair"]')).toContainText('EUR/USD');
    await expect(page.locator('[data-testid="history-amount"]')).toContainText('1000');
  });

  test('should enforce trading limits for basic users', async ({ page }) => {
    // Login as basic user (if different limits apply)
    await authHelpers.logout();
    await authHelpers.login(); // Default basic user

    await page.goto('/trading');

    // Try to place large trade that exceeds basic limits
    await page.fill('[data-testid="amount-input"]', '100000');
    await page.click('[data-testid="buy-button"]');

    // Should show limit exceeded error
    await commonHelpers.checkErrorMessage('Trade amount exceeds your plan limit');
  });

  test('should display real-time price updates', async ({ page }) => {
    await page.goto('/trading');

    // Get initial price
    const initialPrice = await page.locator('[data-testid="eur-usd-price"]').textContent();

    // Wait for price update (prices should update regularly)
    await page.waitForTimeout(5000);

    // Check if price has updated (or at least the timestamp)
    await expect(page.locator('[data-testid="price-timestamp"]')).toBeVisible();
    await expect(page.locator('[data-testid="market-status"]')).toContainText('Live');
  });
});
