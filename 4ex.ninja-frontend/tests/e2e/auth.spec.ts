import { expect, test } from '@playwright/test';
import { AuthHelpers, CommonHelpers } from '../fixtures/helpers';
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
  let commonHelpers: CommonHelpers;

  test.beforeEach(async ({ page }) => {
    authHelpers = new AuthHelpers(page);
    commonHelpers = new CommonHelpers(page);
  });

  test('should complete successful user registration', async ({ page }) => {
    // Test user can register with valid credentials
    await authHelpers.register(testUsers.newUser);

    // Verify user lands on feed after registration
    await expect(page).toHaveURL('/feed');

    // Check for authenticated user elements in header
    await expect(page.locator('text=Account')).toBeVisible();
    await expect(page.locator('text=Sign Out')).toBeVisible();
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
    // Test error handling for invalid credentials
    await authHelpers.login(testUsers.invalidUser.email, testUsers.invalidUser.password);

    // Should remain on login page with error
    await expect(page).toHaveURL('/login');
    await commonHelpers.checkErrorMessage('Invalid email or password');
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
