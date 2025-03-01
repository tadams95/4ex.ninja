/**
 * Utility functions for debugging authentication issues
 */

export function logAuthAttempt(data) {
  console.group('Auth Attempt Debug');
  console.log('Credentials provided:', {
    email: data.email,
    password: data.password ? '********' : 'empty',
    hasPassword: !!data.password,
    passwordLength: data.password?.length
  });
  console.groupEnd();
}

export function logAuthResponse(response) {
  console.group('Auth Response Debug');
  console.log('Status:', response.status);
  console.log('OK:', response.ok);
  console.log('URL:', response.url);
  console.log('Headers:', Object.fromEntries([...response.headers.entries()]));
  console.groupEnd();
  
  return response;
}

export async function logAuthError(error) {
  console.group('Auth Error Debug');
  console.error('Error type:', error.constructor.name);
  console.error('Message:', error.message);
  console.error('Stack:', error.stack);
  
  if (error.response) {
    try {
      const errorData = await error.response.json();
      console.error('Response data:', errorData);
    } catch (e) {
      console.error('Could not parse error response');
    }
  }
  
  console.groupEnd();
}

export const logAuthDebug = (stage, data) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Auth Debug ${stage}]:`, JSON.stringify(data, null, 2));
  }
};
