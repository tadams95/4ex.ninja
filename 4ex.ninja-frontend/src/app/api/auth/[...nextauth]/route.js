import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { logAuthResponse, logAuthError } from "@/lib/auth-debug";

// Add debug logging
const debug = (...args) => {
  if (process.env.NODE_ENV === 'development') {
    console.log('[NextAuth Debug]:', ...args);
  }
};

// Add debug output for auth API calls
async function authenticateUser(credentials) {
  console.log('Attempting API login with:', { 
    email: credentials.email,
    passwordProvided: !!credentials.password
  });
  
  // Use the external API URL in development; use relative path in production.
  const apiUrl =
    process.env.NODE_ENV === 'development'
      ? process.env.NEXT_PUBLIC_API_URL
      : ""; // empty string to use relative path in production

  try {
    const response = await fetch(`${apiUrl}/auth/login`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        // Mimic production headers
        "User-Agent": "Mozilla/5.0 (compatible; ProductionApp/1.0)",
        "Referer": process.env.NEXT_PUBLIC_URL
      },
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password,
      }),
    })
    .then(logAuthResponse);

    if (!response.ok) {
      // Get full error details from response text
      const errorText = await response.text();
      console.error('API login failed with status:', response.status, "Body:", errorText);
      throw new Error(`Authentication failed: ${response.status} ${errorText}`);
    }

    const userData = await response.json();
    console.log('API login successful, user data:', { 
      id: userData.user?.id || 'N/A',
      email: userData.user?.email || 'N/A',
      hasToken: !!userData.token
    });
    
    return userData;
  } catch (error) {
    await logAuthError(error);
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
          apiUrl: process.env.NEXT_PUBLIC_API_URL || process.env.API_URL,
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
