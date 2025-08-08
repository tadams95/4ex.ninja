import { test } from '@playwright/test';
import { AuthHelpers } from '../fixtures/helpers';

test.describe('Registration Debug - Step by Step', () => {
  test('should debug registration flow step by step', async ({ page }) => {
    console.log('=== REGISTRATION DEBUG TEST START ===');

    const auth = new AuthHelpers(page);

    try {
      // Go to register page
      console.log('Step 1: Navigating to /register');
      await page.goto('/register');
      await page.waitForLoadState('networkidle');
      console.log('Step 1 Complete: Page loaded, URL:', page.url());

      // Take screenshot of register page
      await page.screenshot({ path: 'debug-registration-1-page-loaded.png' });

      // Fill form
      console.log('Step 2: Filling registration form');
      const testUser = {
        firstName: 'Test',
        lastName: 'User',
        email: `test-${Date.now()}@example.com`,
        password: 'TestPassword123!',
      };

      const fullName = `${testUser.firstName} ${testUser.lastName}`;
      await page.fill('[data-testid="first-name-input"]', fullName);
      await page.fill('[data-testid="email-input"]', testUser.email);
      await page.fill('[data-testid="password-input"]', testUser.password);
      await page.fill('[data-testid="confirm-password-input"]', testUser.password);
      console.log('Step 2 Complete: Form filled with user:', testUser.email);

      // Take screenshot before submit
      await page.screenshot({ path: 'debug-registration-2-form-filled.png' });

      // Click register button
      console.log('Step 3: Clicking register button');
      await page.click('[data-testid="register-button"]');
      console.log('Step 3 Complete: Register button clicked');

      // Wait a bit to see what happens
      console.log('Step 4: Waiting for response...');
      await page.waitForTimeout(2000);
      console.log('Step 4 Complete: Current URL after 2s:', page.url());

      // Take screenshot after submit
      await page.screenshot({ path: 'debug-registration-3-after-submit.png' });

      // Check for messages
      console.log('Step 5: Checking for success/error messages');
      const successElement = page.locator('.bg-success').first();
      const errorElement = page.locator('.bg-error').first();

      const successVisible = await successElement.isVisible();
      const errorVisible = await errorElement.isVisible();

      console.log('Success message visible:', successVisible);
      console.log('Error message visible:', errorVisible);

      if (successVisible) {
        const successText = await successElement.textContent();
        console.log('Success message:', successText);
      }

      if (errorVisible) {
        const errorText = await errorElement.textContent();
        console.log('Error message:', errorText);
      }

      // Wait longer to see if redirect happens
      console.log('Step 6: Waiting for potential redirect...');
      await page.waitForTimeout(5000);
      console.log('Step 6 Complete: Final URL:', page.url());

      // Take final screenshot
      await page.screenshot({ path: 'debug-registration-4-final.png' });

      console.log('=== REGISTRATION DEBUG TEST END ===');
    } catch (error) {
      console.log('=== REGISTRATION DEBUG TEST ERROR ===');
      console.log('Error:', error.message);
      console.log('Current URL:', page.url());
      await page.screenshot({ path: 'debug-registration-error.png' });
      throw error;
    }
  });

  test('should debug invalid login step by step', async ({ page }) => {
    console.log('=== INVALID LOGIN DEBUG TEST START ===');

    try {
      // Go to login page
      console.log('Step 1: Navigating to /login');
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      console.log('Step 1 Complete: Page loaded, URL:', page.url());

      // Take screenshot
      await page.screenshot({ path: 'debug-invalid-login-1-page-loaded.png' });

      // Fill invalid credentials
      console.log('Step 2: Filling invalid credentials');
      await page.fill('[data-testid="email-input"]', 'invalid@email.com');
      await page.fill('[data-testid="password-input"]', 'wrongpassword');
      console.log('Step 2 Complete: Invalid credentials filled');

      await page.screenshot({ path: 'debug-invalid-login-2-form-filled.png' });

      // Click login
      console.log('Step 3: Clicking login button');
      await page.click('[data-testid="login-button"]');
      console.log('Step 3 Complete: Login button clicked');

      // Wait for response
      console.log('Step 4: Waiting for response...');
      await page.waitForTimeout(3000);
      console.log('Step 4 Complete: Current URL:', page.url());

      await page.screenshot({ path: 'debug-invalid-login-3-after-submit.png' });

      // Check for error message
      console.log('Step 5: Checking for error messages');
      const errorElement = page.locator('.bg-error').first();
      const errorVisible = await errorElement.isVisible();

      console.log('Error message visible:', errorVisible);

      if (errorVisible) {
        const errorText = await errorElement.textContent();
        console.log('Error message:', errorText);
      }

      console.log('=== INVALID LOGIN DEBUG TEST END ===');
    } catch (error) {
      console.log('=== INVALID LOGIN DEBUG TEST ERROR ===');
      console.log('Error:', error.message);
      console.log('Current URL:', page.url());
      await page.screenshot({ path: 'debug-invalid-login-error.png' });
      throw error;
    }
  });
});
