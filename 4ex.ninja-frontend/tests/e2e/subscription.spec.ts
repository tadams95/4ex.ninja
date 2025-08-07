import { expect, test } from '@playwright/test';
import { AuthHelpers, CommonHelpers, SubscriptionHelpers } from '../fixtures/helpers';

/**
 * Critical User Path #2: Subscription Flow
 * Revenue Impact: HIGHEST - Direct revenue generation
 * Test Coverage: Plan selection, Payment processing, Subscription activation
 * Estimated Time: 30 minutes
 */

test.describe('Subscription Flow - Critical Path', () => {
  let authHelpers: AuthHelpers;
  let subscriptionHelpers: SubscriptionHelpers;
  let commonHelpers: CommonHelpers;

  test.beforeEach(async ({ page }) => {
    authHelpers = new AuthHelpers(page);
    subscriptionHelpers = new SubscriptionHelpers(page);
    commonHelpers = new CommonHelpers(page);

    // Ensure user is authenticated for subscription tests
    await authHelpers.login();
  });

  test('should display available subscription plans', async ({ page }) => {
    await page.goto('/pricing');

    // Verify both plans are displayed
    await expect(page.locator('[data-testid="basic-plan"]')).toBeVisible();
    await expect(page.locator('[data-testid="premium-plan"]')).toBeVisible();

    // Check plan details
    await expect(page.locator('[data-testid="basic-plan-price"]')).toContainText('$29');
    await expect(page.locator('[data-testid="premium-plan-price"]')).toContainText('$99');
  });

  test('should complete premium subscription purchase', async ({ page }) => {
    // Select premium plan
    await subscriptionHelpers.selectPlan('premium');

    // Enter payment details
    await subscriptionHelpers.enterPaymentDetails();

    // Complete purchase
    await subscriptionHelpers.completePurchase();

    // Verify subscription activation
    await expect(page.locator('[data-testid="subscription-status"]')).toContainText('Premium');
    await expect(page.locator('[data-testid="premium-features"]')).toBeVisible();
  });

  test('should complete basic subscription purchase', async ({ page }) => {
    // Select basic plan
    await subscriptionHelpers.selectPlan('basic');

    // Enter payment details
    await subscriptionHelpers.enterPaymentDetails();

    // Complete purchase
    await subscriptionHelpers.completePurchase();

    // Verify subscription activation
    await expect(page.locator('[data-testid="subscription-status"]')).toContainText('Basic');
  });

  test('should handle invalid payment information', async ({ page }) => {
    await subscriptionHelpers.selectPlan('premium');

    // Enter invalid card details
    await subscriptionHelpers.enterPaymentDetails({
      number: '4000000000000002', // Declined card
      expiry: '12/25',
      cvc: '123',
      name: 'Test User',
    });

    await page.click('[data-testid="complete-purchase-button"]');

    // Should show payment error
    await commonHelpers.checkErrorMessage('Your card was declined');
  });

  test('should allow subscription plan upgrade', async ({ page }) => {
    // First subscribe to basic plan
    await subscriptionHelpers.selectPlan('basic');
    await subscriptionHelpers.enterPaymentDetails();
    await subscriptionHelpers.completePurchase();

    // Navigate to account settings
    await page.goto('/account/subscription');

    // Upgrade to premium
    await page.click('[data-testid="upgrade-to-premium-button"]');
    await subscriptionHelpers.enterPaymentDetails();
    await subscriptionHelpers.completePurchase();

    // Verify upgrade
    await expect(page.locator('[data-testid="subscription-status"]')).toContainText('Premium');
  });

  test('should display subscription benefits after purchase', async ({ page }) => {
    // Complete premium subscription
    await subscriptionHelpers.selectPlan('premium');
    await subscriptionHelpers.enterPaymentDetails();
    await subscriptionHelpers.completePurchase();

    // Check premium features are unlocked
    await page.goto('/trading');
    await expect(page.locator('[data-testid="advanced-charts"]')).toBeVisible();
    await expect(page.locator('[data-testid="api-access-panel"]')).toBeVisible();

    // Check basic features are still available
    await expect(page.locator('[data-testid="basic-trading-panel"]')).toBeVisible();
  });

  test('should handle subscription cancellation flow', async ({ page }) => {
    // First complete a subscription
    await subscriptionHelpers.selectPlan('premium');
    await subscriptionHelpers.enterPaymentDetails();
    await subscriptionHelpers.completePurchase();

    // Navigate to subscription management
    await page.goto('/account/subscription');

    // Cancel subscription
    await page.click('[data-testid="cancel-subscription-button"]');
    await page.click('[data-testid="confirm-cancellation-button"]');

    // Verify cancellation
    await commonHelpers.checkSuccessMessage('Subscription cancelled successfully');
    await expect(page.locator('[data-testid="subscription-status"]')).toContainText('Cancelled');
  });
});
