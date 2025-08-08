import { Page } from '@playwright/test';
import { testUsers } from './testData';

// Types for test data
type TestUser = {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  subscriptionTier?: string;
};

/**
 * Page Object Model helpers for critical E2E flows
 * Keeps tests DRY and maintainable
 */
export class AuthHelpers {
  constructor(private page: Page) {}

  async login(email = testUsers.validUser.email, password = testUsers.validUser.password) {
    await this.page.goto('/login');
    await this.page.fill('[data-testid="email-input"]', email);
    await this.page.fill('[data-testid="password-input"]', password);
    await this.page.click('[data-testid="login-button"]');

    // Wait for response - either success or error
    try {
      await this.page.waitForURL('/feed', { timeout: 8000 });
    } catch (error) {
      // Check if we got an error message instead - try multiple error selectors
      const errorElement = await this.page
        .locator('.bg-error, .text-red-500, .error-message, [data-testid="error-message"]')
        .first();
      if (await errorElement.isVisible()) {
        const errorText = await errorElement.textContent();
        console.log('Login failed with error:', errorText);
        throw new Error(`Login failed: ${errorText}`);
      }
      console.log('Login did not complete successfully. Current URL:', this.page.url());
      throw error;
    }
  }

  async register(user: TestUser) {
    await this.page.goto('/register');
    // Combine firstName and lastName since the form uses a single name field
    const fullName = `${user.firstName} ${user.lastName}`;
    await this.page.fill('[data-testid="first-name-input"]', fullName);
    await this.page.fill('[data-testid="email-input"]', user.email);
    await this.page.fill('[data-testid="password-input"]', user.password);
    await this.page.fill('[data-testid="confirm-password-input"]', user.password);
    await this.page.click('[data-testid="register-button"]');

    // Wait for response - either redirect to feed, pricing, or stripe checkout
    try {
      // Registration can redirect to:
      // 1. /feed (if already subscribed)
      // 2. /pricing (subscription needed)
      // 3. stripe checkout (direct subscription flow)
      await this.page.waitForURL(
        (url: URL) =>
          url.pathname === '/feed' ||
          url.pathname === '/pricing' ||
          url.hostname.includes('checkout.stripe.com'),
        { timeout: 8000 }
      );
      console.log('Registration successful, redirected to:', this.page.url());
    } catch (error) {
      // Check for success or error messages
      const successElement = await this.page.locator('.bg-success').first();
      const errorElement = await this.page.locator('.bg-error').first();

      if (await successElement.isVisible()) {
        console.log('Registration successful but did not redirect');
        return;
      }
      if (await errorElement.isVisible()) {
        const errorText = await errorElement.textContent();
        console.log('Registration failed with error:', errorText);
        throw new Error(`Registration failed: ${errorText}`);
      }
      console.log('Registration did not complete. Current URL:', this.page.url());
      throw error;
    }
  }

  async logout() {
    await this.page.click('[data-testid="sign-out-button"]');
    await this.page.waitForURL('/', { timeout: 8000 }); // Wait for redirect to home page
  }
}

export class TradingHelpers {
  constructor(private page: Page) {}

  async navigateToFeed() {
    await this.page.goto('/feed');
    await this.page.waitForSelector('[data-testid="crossover-feed"]', { timeout: 8000 });
  }

  async waitForSignals() {
    // Wait for crossover signals to load
    await this.page.waitForSelector('[data-testid="crossover-item"]', { timeout: 8000 });
  }

  async getCrossoverCount() {
    const crossovers = await this.page.locator('[data-testid="crossover-item"]');
    return await crossovers.count();
  }

  async getFirstCrossover() {
    const firstCrossover = await this.page.locator('[data-testid="crossover-item"]').first();
    return {
      pair: await firstCrossover.locator('[data-testid="crossover-pair"]').textContent(),
      type: await firstCrossover.locator('[data-testid="crossover-type"]').textContent(),
      confidence: await firstCrossover
        .locator('[data-testid="crossover-confidence"]')
        .textContent(),
    };
  }
}

export class SubscriptionHelpers {
  constructor(private page: Page) {}

  async navigateToAccount() {
    await this.page.goto('/account');
    await this.page.waitForSelector('[data-testid="subscription-section"]', { timeout: 8000 });
  }

  async getSubscriptionStatus() {
    const statusElement = await this.page.locator('[data-testid="subscription-status"]');
    return await statusElement.textContent();
  }

  async clickSubscribe() {
    await this.page.click('[data-testid="subscribe-button"]');
    // This will redirect to Stripe - we don't follow through in tests
    await this.page.waitForTimeout(2000); // Short wait to confirm redirect started
  }

  async hasAccessToFeed() {
    try {
      await this.page.goto('/feed');
      await this.page.waitForSelector('[data-testid="crossover-feed"]', { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }
}

// Test data helpers
export function generateTestUser(): TestUser {
  return {
    email: `test.${Date.now()}@example.com`,
    password: 'TestPassword123!',
    firstName: 'Test',
    lastName: 'User',
  };
}

export function generatePremiumTestUser(): TestUser {
  return {
    email: `premium.${Date.now()}@example.com`,
    password: 'TestPassword123!',
    firstName: 'Premium',
    lastName: 'User',
    subscriptionTier: 'premium',
  };
}

// Wait helpers
export async function waitForStableDOM(page: Page, selector: string, timeout = 5000) {
  let lastCount = -1;
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      const elements = await page.locator(selector);
      const currentCount = await elements.count();

      if (currentCount === lastCount && currentCount > 0) {
        // DOM is stable for this selector
        await page.waitForTimeout(500); // Extra buffer
        return;
      }

      lastCount = currentCount;
      await page.waitForTimeout(500);
    } catch {
      // Continue waiting
      await page.waitForTimeout(500);
    }
  }

  throw new Error(`DOM never stabilized for selector: ${selector}`);
}
