import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { logAuthResponse, logAuthError } from "@/lib/auth-debug";

// Add debug logging
const debug = (...args) => {
  if (process.env.NODE_ENV === 'development') {
    console.log('[NextAuth Debug]:', ...args);
  }
};

// Helper function for API URL - only use environment variable, no fallbacks
const getApiBaseUrl = () => {
  // Only use explicit environment variable
  return process.env.NEXT_PUBLIC_API_URL || '';
};

// Add debug output for auth API calls
async function authenticateUser(credentials) {
  console.log('Attempting API login with:', { 
    email: credentials.email,
    passwordProvided: !!credentials.password
  });
  
  // For production authentication, we'll use internal DB checking
  // instead of trying to call an external API that doesn't exist
  
  // Bypass external API completely in production
  if (process.env.NODE_ENV === 'production') {
    // This is a placeholder - we'll implement direct DB auth
    console.log('In production - using direct DB auth instead of API');
    // Use MongoDB directly - we'll implement below
    return await directDbAuthentication(credentials);
  }
  
  // Only in development try to use API
  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    throw new Error('API URL not configured');
  }
  
  const loginUrl = `${apiBaseUrl}/auth/login`;
  console.log('Using login URL:', loginUrl);

  try {
    // Only make API call in development
    const response = await fetch(loginUrl, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; ProductionApp/1.0)",
        "Referer": process.env.NEXT_PUBLIC_URL || ''
      },
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password,
      }),
    })
    .then(logAuthResponse);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API login failed with status:', response.status, "Body:", errorText);
      throw new Error(`Authentication failed: ${response.status} ${errorText}`);
    }

    const userData = await response.json();
    return userData;
  } catch (error) {
    await logAuthError(error);
    throw error;
  }
}

// Direct DB authentication for production
async function directDbAuthentication(credentials) {
  try {
    const { connectToDatabase } = await import('@/utils/mongodb');
    const { db } = await connectToDatabase();
    const bcrypt = await import('bcryptjs');
    
    // Find user by email (case-insensitive)
    const user = await db.collection('users').findOne({
      email: { $regex: `^${credentials.email}$`, $options: 'i' }
    });

    if (!user) {
      throw new Error('User not found');
    }

    // Verify password
    const passwordValid = await bcrypt.compare(credentials.password, user.password);
    
    if (!passwordValid) {
      throw new Error('Invalid password');
    }

    // Return user with token format expected by NextAuth
    return {
      success: true,
      token: 'direct-db-auth', // Just a placeholder token
      user: {
        id: user._id.toString(),
        firstName: user.name?.split(' ')[0] || '',
        lastName: user.name?.split(' ').slice(1).join(' ') || '',
        email: user.email,
        isSubscribed: user.isSubscribed
      }
    };
  } catch (error) {
    console.error('Direct DB authentication error:', error);
    throw error;
  }
}

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        debug('Auth attempt with:', {
          email: credentials.email,
          hasPassword: !!credentials.password,
          nodeEnv: process.env.NODE_ENV,
          apiUrl: getApiBaseUrl(), // Use our helper function here too
        });
        
        // DEVELOPMENT MODE: Bypass external API
        if (process.env.NODE_ENV === 'development') {
          if (
            credentials.email === process.env.DEV_TEST_EMAIL &&
            credentials.password === process.env.DEV_TEST_PASSWORD
          ) {
            console.log('Development login bypass successful');
            return {
              id: "1",
              name: "Dev User",
              email: credentials.email,
              token: "dev-token",
            };
          } else {
            console.error("Invalid dev credentials. Use the test credentials defined.");
            return null;
          }
        }
        
        // PRODUCTION MODE: Use external API
        try {
          const userData = await authenticateUser(credentials);
          debug('Auth response data:', {
            success: userData.success,
            hasToken: !!userData.token,
            hasUser: !!userData.user,
          });
          if (userData.token) {
            return {
              id: userData.user.id.toString(),
              name: `${userData.user.firstName} ${userData.user.lastName}`.trim(),
              email: userData.user.email,
              token: userData.token,
              isSubscribed: userData.user.isSubscribed,
            };
          }
          return null;
        } catch (error) {
          debug('Auth error:', error.message);
          console.error("Authorization error:", error);
          return null;
        }
      },
    }),
  ],
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
        token.accessToken = user.token;
      }
      return token;
    },
    session: async ({ session, token }) => {
      if (token) {
        session.user.id = token.id;
        session.user.accessToken = token.accessToken;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  debug: process.env.NODE_ENV === "development",
});

export { handler as GET, handler as POST };
