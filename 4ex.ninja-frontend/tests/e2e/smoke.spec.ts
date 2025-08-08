import { expect, test } from '@playwright/test';

/**
 * SMOKE TESTS - Basic functionality validation
 * These should always pass and catch major regressions
 */

test.describe('Smoke Tests - Basic App Functionality', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');

    // Check basic page structure with more specific selectors
    await expect(page.locator('a').filter({ hasText: '4ex.ninja' }).first()).toBeVisible();
    await expect(page.locator('text=Log in')).toBeVisible();

    // Check page loads without errors
    await expect(page).toHaveTitle(/4ex\.ninja/);
  });

  test('login page loads successfully', async ({ page }) => {
    await page.goto('/login');

    // Check form elements exist
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible();
  });

  test('register page loads successfully', async ({ page }) => {
    await page.goto('/register');

    // Check form elements exist
    await expect(page.locator('[data-testid="register-form"]')).toBeVisible();
    await expect(page.locator('[data-testid="first-name-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="register-button"]')).toBeVisible();
  });

  test('protected route redirects unauthenticated users', async ({ page }) => {
    await page.goto('/feed');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });
});
