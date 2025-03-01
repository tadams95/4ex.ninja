import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { logAuthResponse, logAuthError } from "@/lib/auth-debug";

// Add debug output for auth API calls
async function authenticateUser(credentials) {
  console.log('Attempting API login with:', { 
    email: credentials.email,
    passwordProvided: !!credentials.password
  });

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password,
      }),
    })
    .then(logAuthResponse);

    if (!response.ok) {
      console.error('API login failed with status:', response.status);
      throw new Error(`Authentication failed: ${response.status}`);
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
        try {
          const userData = await authenticateUser(credentials);
          
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
