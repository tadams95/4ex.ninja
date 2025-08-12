import bcrypt from 'bcryptjs';
import { MongoClient } from 'mongodb';
import CredentialsProvider from 'next-auth/providers/credentials';

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const client = new MongoClient(process.env.MONGO_CONNECTION_STRING);

        try {
          await client.connect();
          const db = client.db('users');
          const usersCollection = db.collection('subscribers');

          const user = await usersCollection.findOne({
            email: credentials.email,
          });

          if (!user) {
            return null;
          }

          // Check password
          let passwordValid;
          if (user.password.startsWith('$2a$') || user.password.startsWith('$2b$')) {
            passwordValid = await bcrypt.compare(credentials.password, user.password);
          } else {
            // Legacy plain text support
            passwordValid = user.password === credentials.password;
          }

          if (!passwordValid) {
            return null;
          }

          return {
            id: user._id.toString(),
            email: user.email,
            name: user.name,
            isSubscribed: user.subscriptionStatus === 'active',
            subscriptionEnds: user.subscriptionEnds,
          };
        } catch (error) {
          console.error('Auth error:', error);
          return null;
        } finally {
          await client.close();
        }
      },
    }),
  ],
  pages: {
    signIn: '/login',
    signUp: '/register',
  },
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  jwt: {
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.isSubscribed = user.isSubscribed;
        token.subscriptionEnds = user.subscriptionEnds;
      }
      return token;
    },
    async session({ session, token }) {
      if (token) {
        session.user.id = token.id;
        session.user.isSubscribed = token.isSubscribed;
        session.user.subscriptionEnds = token.subscriptionEnds;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};
