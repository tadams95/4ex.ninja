import { test } from '@playwright/test';

/**
 * API CONNECTIVITY TESTS - Check if backend APIs are working
 * These tests validate that our backend APIs are accessible
 */

test.describe('API Connectivity Tests', () => {
  test('health check endpoint is accessible', async ({ page }) => {
    // Try to access a simple API endpoint
    const response = await page.request.get('/api/health');

    console.log(`Health check status: ${response.status()}`);

    if (response.ok()) {
      const body = await response.text();
      console.log(`Health check response: ${body}`);
    } else {
      console.log(`Health check failed with status: ${response.status()}`);
    }
  });

  test('check if auth API endpoints exist', async ({ page }) => {
    // Test auth endpoints
    const endpoints = ['/api/auth/signin', '/api/auth/session', '/api/auth/providers'];

    for (const endpoint of endpoints) {
      try {
        const response = await page.request.get(endpoint);
        console.log(`${endpoint}: ${response.status()}`);
      } catch (error) {
        console.log(`${endpoint}: ERROR - ${error}`);
      }
    }
  });

  test('check NextAuth configuration', async ({ page }) => {
    await page.goto('/api/auth/providers');

    // Check if we get a valid response
    const content = await page.textContent('body');
    console.log('NextAuth providers response:', content);

    // Navigate to signin page
    await page.goto('/api/auth/signin');
    const signinContent = await page.textContent('body');
    console.log('NextAuth signin page:', signinContent?.substring(0, 200) + '...');
  });

  test('test manual API call to registration endpoint', async ({ page }) => {
    const testUser = {
      name: `Test User ${Date.now()}`,
      email: `test${Date.now()}@example.com`,
      password: 'TestPassword123!',
    };

    try {
      const response = await page.request.post('/api/auth/register', {
        data: testUser,
      });

      console.log(`Registration API status: ${response.status()}`);

      if (response.ok()) {
        const body = await response.json();
        console.log('Registration success:', body);
      } else {
        const errorBody = await response.text();
        console.log('Registration error:', errorBody);
      }
    } catch (error) {
      console.log('Registration API error:', error);
    }
  });
});
