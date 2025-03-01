import CredentialsProvider from "next-auth/providers/credentials";
import { connectToDatabase } from "@/utils/mongodb";
import bcrypt from "bcryptjs";

// Debug logger
const debug = (...args) => {
  console.log('[NextAuth]:', ...args);
};

async function authenticateCredentials(credentials) {
  try {
    // Connect to the database
    const { db } = await connectToDatabase();
    
    // Find the user with case-insensitive email match
    const user = await db.collection("users").findOne({
      email: { $regex: `^${credentials.email}$`, $options: "i" }
    });
    
    if (!user) {
      console.log(`User not found: ${credentials.email}`);
      return null;
    }
    
    // Verify password
    const isValid = await bcrypt.compare(credentials.password, user.password);
    
    if (!isValid) {
      console.log(`Invalid password for user: ${credentials.email}`);
      return null;
    }
    
    // Log the user data (excluding password)
    const { password, ...userWithoutPassword } = user;
    console.log('Authentication successful:', {
      id: user._id,
      email: user.email,
      isSubscribed: !!user.isSubscribed
    });
    
    // Return user with necessary fields
    return {
      id: user._id.toString(),
      name: user.name || "",
      email: user.email,
      isSubscribed: !!user.isSubscribed, // Ensure boolean
    };
  } catch (error) {
    console.error("Authentication error:", error);
    return null;
  }
}

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        // Special case for development login
        if (process.env.NODE_ENV === "development" &&
            credentials.email === process.env.DEV_TEST_EMAIL &&
            credentials.password === process.env.DEV_TEST_PASSWORD) {
          return {
            id: "dev-user-id",
            email: credentials.email,
            name: "Development User",
            isSubscribed: true, // Default to subscribed for dev user
          };
        }
        
        return await authenticateCredentials(credentials);
      },
    }),
  ],
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        // When user first signs in
        token.id = user.id;
        token.email = user.email;
        token.name = user.name || "";
        token.isSubscribed = user.isSubscribed;
        
        console.log('JWT token created with subscription status:', user.isSubscribed);
      }
      console.log('JWT token:', token);
      return token;
    },
    session: async ({ session, token }) => {
      // Send properties to the client
      session.user.id = token.id;
      session.user.email = token.email;
      session.user.name = token.name;
      session.user.isSubscribed = token.isSubscribed;
      
      console.log('Session created with subscription status:', token.isSubscribed);
      console.log('Session:', session);
      return session;
    },
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET,
  pages: {
    signIn: "/login",
  },
  debug: process.env.NODE_ENV === "development",
};
