import { Page, expect } from '@playwright/test';
import { subscriptionData, testUsers, tradingData } from './testData';

/**
 * Page Object Model helpers for critical E2E flows
 * Keeps tests DRY and maintainable
 */
export class AuthHelpers {
  constructor(private page: Page) {}

  async login(
    email: string = testUsers.validUser.email,
    password: string = testUsers.validUser.password
  ) {
    await this.page.goto('/login');
    await this.page.fill('[data-testid="email-input"]', email);
    await this.page.fill('[data-testid="password-input"]', password);
    await this.page.click('[data-testid="login-button"]');

    // Wait for successful login redirect
    await expect(this.page).toHaveURL('/dashboard');
  }

  async logout() {
    await this.page.click('[data-testid="user-menu"]');
    await this.page.click('[data-testid="logout-button"]');
    await expect(this.page).toHaveURL('/');
  }

  async register(user = testUsers.validUser) {
    await this.page.goto('/register');
    await this.page.fill('[data-testid="first-name-input"]', user.firstName);
    await this.page.fill('[data-testid="last-name-input"]', user.lastName);
    await this.page.fill('[data-testid="email-input"]', user.email);
    await this.page.fill('[data-testid="password-input"]', user.password);
    await this.page.click('[data-testid="register-button"]');

    // Wait for successful registration
    await expect(this.page).toHaveURL('/dashboard');
  }
}

export class TradingHelpers {
  constructor(private page: Page) {}

  async placeTrade(trade = tradingData.validTrade) {
    await this.page.goto('/trading');

    // Select currency pair
    await this.page.click('[data-testid="pair-selector"]');
    await this.page.click(`[data-testid="pair-option-${trade.pair}"]`);

    // Enter trade details
    await this.page.fill('[data-testid="amount-input"]', trade.amount);
    await this.page.click(`[data-testid="${trade.direction}-button"]`);

    if (trade.stopLoss) {
      await this.page.fill('[data-testid="stop-loss-input"]', trade.stopLoss);
    }

    if (trade.takeProfit) {
      await this.page.fill('[data-testid="take-profit-input"]', trade.takeProfit);
    }

    // Execute trade
    await this.page.click('[data-testid="execute-trade-button"]');

    // Verify trade confirmation
    await expect(this.page.locator('[data-testid="trade-confirmation"]')).toBeVisible();
  }

  async viewPositions() {
    await this.page.goto('/trading/positions');
    await expect(this.page.locator('[data-testid="positions-table"]')).toBeVisible();
  }
}

export class SubscriptionHelpers {
  constructor(private page: Page) {}

  async selectPlan(planType: 'basic' | 'premium' = 'premium') {
    await this.page.goto('/pricing');

    const plan = planType === 'premium' ? subscriptionData.premiumPlan : subscriptionData.basicPlan;
    await this.page.click(`[data-testid="select-${planType}-plan"]`);

    // Verify plan selection
    await expect(this.page).toHaveURL('/checkout');
    await expect(this.page.locator('[data-testid="selected-plan-name"]')).toContainText(plan.name);
  }

  async enterPaymentDetails(card = subscriptionData.testCard) {
    // Fill payment form
    await this.page.fill('[data-testid="card-number-input"]', card.number);
    await this.page.fill('[data-testid="card-expiry-input"]', card.expiry);
    await this.page.fill('[data-testid="card-cvc-input"]', card.cvc);
    await this.page.fill('[data-testid="card-name-input"]', card.name);
  }

  async completePurchase() {
    await this.page.click('[data-testid="complete-purchase-button"]');

    // Wait for success confirmation
    await expect(this.page.locator('[data-testid="purchase-success"]')).toBeVisible();
    await expect(this.page).toHaveURL('/dashboard');
  }
}

export class CommonHelpers {
  constructor(private page: Page) {}

  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  async checkErrorMessage(expectedMessage: string) {
    await expect(this.page.locator('[data-testid="error-message"]')).toContainText(expectedMessage);
  }

  async checkSuccessMessage(expectedMessage: string) {
    await expect(this.page.locator('[data-testid="success-message"]')).toContainText(
      expectedMessage
    );
  }
}
