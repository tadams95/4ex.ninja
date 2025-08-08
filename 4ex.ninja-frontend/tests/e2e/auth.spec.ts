import { expect, test } from '@playwright/test';
import { AuthHelpers, generateTestUser } from '../fixtures/helpers';
import { testUsers } from '../fixtures/testData';

/**
 * LEAN E2E Tests: Authentication Flow
 *
 * Critical Path: User Registration → Login → Protected Route Access
 *
 * This test covers 20% of user actions but 80% of revenue impact:
 * - New user can create account
 * - Existing user can login
 * - Authentication persists across sessions
 * - Unauthenticated users are properly redirected
 *
 * Success Criteria:
 * - All authentication flows work end-to-end
 * - Proper error handling for invalid credentials
 * - Route protection working correctly
 *
 * Estimated Time: 20 minutes
 */

test.describe('Authentication Flow - Critical Path', () => {
  let authHelpers: AuthHelpers;

  test.beforeEach(async ({ page }) => {
    authHelpers = new AuthHelpers(page);
  });

  test('should complete successful user registration', async ({ page }) => {
    const auth = new AuthHelpers(page);
    const newUser = generateTestUser();

    await auth.register(newUser);

    // After registration, user should be redirected to either:
    // 1. /feed (if auto-subscribed)
    // 2. /pricing (needs subscription)
    // 3. Stripe checkout (direct subscription flow)
    const currentUrl = page.url();
    console.log('Registration completed, final URL:', currentUrl);

    expect(
      currentUrl.includes('/feed') ||
        currentUrl.includes('/pricing') ||
        currentUrl.includes('checkout.stripe.com')
    ).toBe(true);
  });

  test('should complete successful user login', async ({ page }) => {
    // Test existing user can login
    await authHelpers.login();

    // Verify successful login state
    await expect(page).toHaveURL('/feed');

    // Check for authenticated user elements in header
    await expect(page.locator('text=Account')).toBeVisible();
    await expect(page.locator('text=Sign Out')).toBeVisible();

    // Verify page title shows we're on the feed page
    await expect(page.locator('h1:has-text("Latest MA Crossover Signals")')).toBeVisible();
  });

  test('should handle invalid login credentials', async ({ page }) => {
    // Go to login page manually and fill invalid credentials
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', testUsers.invalidUser.email);
    await page.fill('[data-testid="password-input"]', testUsers.invalidUser.password);
    await page.click('[data-testid="login-button"]');

    // Wait a bit for any response
    await page.waitForTimeout(3000);

    // Should remain on login page (not redirected to /feed)
    expect(page.url()).toContain('/login');

    // Test passes if we stay on login page (indicating invalid credentials were rejected)
    console.log('Invalid credentials correctly rejected, stayed on login page');
  });

  test('should complete successful logout', async ({ page }) => {
    // Login first
    await authHelpers.login();

    // Then logout
    await authHelpers.logout();

    // Verify logged out state
    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Log in')).toBeVisible();
  });

  test('should redirect unauthenticated users from protected routes', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/feed');

    // Should redirect to login (with possible query parameters)
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });

  test('should persist authentication state across browser refresh', async ({ page }) => {
    // Login and verify state
    await authHelpers.login();
    await expect(page).toHaveURL('/feed');

    // Refresh page
    await page.reload();

    // Should still be authenticated
    await expect(page).toHaveURL('/feed');
    await expect(page.locator('text=Account')).toBeVisible();
    await expect(page.locator('text=Sign Out')).toBeVisible();
  });
});
