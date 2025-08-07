import { expect, test } from '@playwright/test';
import { AuthHelpers, CommonHelpers } from '../fixtures/helpers';
import { testUsers } from '../fixtures/testData';

/**
 * Critical User Path #1: Authentication Flow
 * Revenue Impact: HIGH - Users must authenticate to access paid features
 * Test Coverage: Login, Registration, Logout, Error handling
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
    await authHelpers.register();

    // Verify user lands on dashboard after registration
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
  });

  test('should complete successful user login', async ({ page }) => {
    // Test existing user can login
    await authHelpers.login();

    // Verify successful login state
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="user-profile"]')).toBeVisible();
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
    await expect(page.locator('[data-testid="login-link"]')).toBeVisible();
  });

  test('should redirect unauthenticated users from protected routes', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL('/login');
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });

  test('should persist authentication state across browser refresh', async ({ page }) => {
    // Login and verify state
    await authHelpers.login();
    await expect(page).toHaveURL('/dashboard');

    // Refresh page
    await page.reload();
    await commonHelpers.waitForPageLoad();

    // Should still be authenticated
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="user-profile"]')).toBeVisible();
  });
});
