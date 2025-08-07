// Simple test user setup for E2E tests
// This ensures test users exist in the database

const testUser = {
  email: 'tyrelle@ragestate.com',
  password: 'Password22$',
  name: 'Ty Adams',
};

// For now, we'll use API calls to create the user
export async function ensureTestUserExists(page) {
  try {
    // Try to create the test user via the registration API
    const response = await page.request.post('/api/auth/register', {
      data: {
        name: testUser.name,
        email: testUser.email,
        password: testUser.password,
        confirmPassword: testUser.password,
      },
    });

    // Don't throw error if user already exists (409 conflict)
    if (response.status() === 201 || response.status() === 409) {
      console.log('✅ Test user ready:', testUser.email);
      return true;
    }
  } catch (error) {
    console.log('⚠️ Could not setup test user:', error.message);
  }
  return false;
}

export { testUser };
