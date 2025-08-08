import { expect, test } from '@playwright/test';

/**
 * MANUAL AUTH TESTS - Step-by-step authentication debugging
 * These tests help us understand exactly where authentication is failing
 */

test.describe('Manual Authentication Debugging', () => {
  test('can fill and submit login form manually', async ({ page }) => {
    // Step 1: Navigate to login
    await page.goto('/login');
    console.log('✅ Navigated to login page');

    // Step 2: Check form is present
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    console.log('✅ Login form is visible');

    // Step 3: Fill form fields
    await page.fill('[data-testid="email-input"]', 'tyrelle@ragestate.com');
    console.log('✅ Filled email field');

    await page.fill('[data-testid="password-input"]', 'Password22$');
    console.log('✅ Filled password field');

    // Step 4: Click submit and wait
    console.log('🔄 Clicking login button...');
    await page.click('[data-testid="login-button"]');

    // Step 5: Wait a bit and check what happened
    await page.waitForTimeout(5000);

    const currentUrl = page.url();
    console.log(`🔍 Current URL after login attempt: ${currentUrl}`);

    // Check for error messages
    const errorElement = await page
      .locator('.bg-error, .text-error, .text-red-400, .text-red-500')
      .first();
    if (await errorElement.isVisible()) {
      const errorText = await errorElement.textContent();
      console.log(`❌ Error message found: ${errorText}`);
    } else {
      console.log('✅ No error messages visible');
    }

    // Check for loading states
    const loadingElement = await page.locator('[data-loading="true"], .animate-spin').first();
    if (await loadingElement.isVisible()) {
      console.log('⏳ Loading state still active');
    } else {
      console.log('✅ No loading states active');
    }

    // Don't assert anything - just observe what happens
  });

  test('can submit login form and observe network requests', async ({ page }) => {
    // Monitor network requests
    const requests: any[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        requests.push({
          method: request.method(),
          url: request.url(),
          postData: request.postData(),
        });
        console.log(`📡 API Request: ${request.method()} ${request.url()}`);
      }
    });

    const responses: any[] = [];
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        responses.push({
          status: response.status(),
          url: response.url(),
        });
        console.log(`📨 API Response: ${response.status()} ${response.url()}`);
      }
    });

    // Perform login
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'tyrelle@ragestate.com');
    await page.fill('[data-testid="password-input"]', 'Password22$');
    await page.click('[data-testid="login-button"]');

    // Wait for any network activity to complete
    await page.waitForTimeout(5000);

    console.log(`📊 Total API requests made: ${requests.length}`);
    console.log(`📊 Total API responses received: ${responses.length}`);

    // Log current state
    const currentUrl = page.url();
    console.log(`🔍 Final URL: ${currentUrl}`);
  });

  test('check if user already exists in database', async ({ page }) => {
    // Try to register with the same email to see if user exists
    await page.goto('/register');

    await page.fill('[data-testid="first-name-input"]', 'Test User');
    await page.fill('[data-testid="email-input"]', 'tyrelle@ragestate.com');
    await page.fill('[data-testid="password-input"]', 'Password22$');
    await page.fill('[data-testid="confirm-password-input"]', 'Password22$');

    console.log('🔄 Attempting registration with existing email...');
    await page.click('[data-testid="register-button"]');

    await page.waitForTimeout(3000);

    const currentUrl = page.url();
    console.log(`🔍 URL after registration attempt: ${currentUrl}`);

    // Check for error messages
    const errorElement = await page
      .locator('.bg-error, .text-error, .text-red-400, .text-red-500')
      .first();
    if (await errorElement.isVisible()) {
      const errorText = await errorElement.textContent();
      console.log(`❌ Registration error: ${errorText}`);
    } else {
      console.log('✅ No registration error messages');
    }
  });
});
