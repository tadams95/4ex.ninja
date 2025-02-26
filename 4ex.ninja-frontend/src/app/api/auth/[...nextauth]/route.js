import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { MongoClient } from "mongodb";

// Setup MongoDB connection
const uri = process.env.MONGO_CONNECTION_STRING;

// User authentication function
async function authenticateUser(credentials) {
  const client = new MongoClient(uri);

  try {
    await client.connect();
    const db = client.db("users");
    const usersCollection = db.collection("subscribers");

    // Find user by email
    const user = await usersCollection.findOne({ email: credentials.email });
    
    console.log('Found user:', user);
    
    // In a real app, you'd also hash and verify the password
    if (user && user.password === credentials.password && user.subscriptionStatus === "active") {
      return {
        id: user._id.toString(),
        name: user.name || "User",
        email: user.email,
        subscriptionEnds: user.subscriptionEnds,
      };
    }
    
    console.log('Authentication failed');
    return null;
  } catch (error) {
    console.error("Authentication error:", error);
    return null;
  } finally {
    await client.close();
  }
}

// Create NextAuth options object
const authOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "email@example.com" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials) return null;
        
        // Added debug logs
        console.log('Attempting to authenticate:', credentials.email);
        
        return await authenticateUser(credentials);
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // If user is found during sign in, add subscription data to the token
      if (user) {
        token.id = user.id;
        token.subscriptionEnds = user.subscriptionEnds;
      }
      return token;
    },
    async session({ session, token }) {
      // Make subscription data available in the client session
      if (session?.user) {
        session.user.id = token.id;
        session.user.subscriptionEnds = token.subscriptionEnds;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  debug: process.env.NODE_ENV === "development",
  secret: process.env.NEXTAUTH_SECRET,
};

// Create handler
const handler = NextAuth(authOptions);

// Export named functions instead of default export
export { handler as GET, handler as POST };
