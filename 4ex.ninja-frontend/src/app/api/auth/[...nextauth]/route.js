import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { MongoClient } from "mongodb";
import bcrypt from "bcryptjs";

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

    console.log(
      "Found user for authentication:",
      user ? user.email : "not found"
    );

    if (!user) {
      console.log("User not found");
      return null;
    }

    // Compare hashed passwords
    let isValid = false;

    // First check if password is stored as hash
    if (user.password.startsWith("$2a$") || user.password.startsWith("$2b$")) {
      // Password is hashed, use bcrypt compare
      isValid = await bcrypt.compare(credentials.password, user.password);
    } else {
      // For backward compatibility - plain text comparison (remove this in production)
      isValid = user.password === credentials.password;
      console.log("WARNING: Using plain text password comparison");
    }

    if (isValid) {
      // Don't require subscription check during development
      const requireSubscription = process.env.NODE_ENV === "production";

      if (
        (requireSubscription && user.subscriptionStatus === "active") ||
        !requireSubscription
      ) {
        return {
          id: user._id.toString(),
          name: user.name || "User",
          email: user.email,
          subscriptionEnds: user.subscriptionEnds,
        };
      } else {
        console.log("Subscription inactive");
        return null;
      }
    }

    console.log("Password validation failed");
    return null;
  } catch (error) {
    console.error("Authentication error:", error);
    return null;
  } finally {
    await client.close();
  }
}

// // Create NextAuth options object
// const authOptions = {
//   providers: [
//     CredentialsProvider({
//       name: "Credentials",
//       credentials: {
//         email: {
//           label: "Email",
//           type: "email",
//           placeholder: "email@example.com",
//         },
//         password: { label: "Password", type: "password" },
//       },
//       async authorize(credentials) {
//         if (!credentials) return null;

//         // Added debug logs
//         console.log("Attempting to authenticate user:", credentials.email);

//         return await authenticateUser(credentials);
//       },
//     }),
//   ],
//   callbacks: {
//     async jwt({ token, user }) {
//       if (user) {
//         token.id = user.id;
//         token.subscriptionEnds = user.subscriptionEnds;
//       }
//       return token;
//     },
//     async session({ session, token }) {
//       if (session?.user) {
//         session.user.id = token.id;
//         session.user.subscriptionEnds = token.subscriptionEnds;
//       }
//       return session;
//     },
//   },
//   pages: {
//     signIn: "/login",
//     error: "/login",
//   },
//   session: {
//     strategy: "jwt",
//     maxAge: 30 * 24 * 60 * 60, // 30 days
//   },
//   debug: process.env.NODE_ENV === "development",
//   secret: process.env.NEXTAUTH_SECRET,
// };

import { authOptions } from "./auth-options";

// Create handler
const handler = NextAuth(authOptions);

// Export named functions
export { handler as GET, handler as POST };
