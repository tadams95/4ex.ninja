// NextAuth type extensions for 4ex.ninja

declare module 'next-auth' {
  interface User {
    id?: string;
    email?: string | null;
    name?: string | null;
    image?: string | null;
    isSubscribed?: boolean;
    subscriptionEnds?: string | Date;
  }

  interface Session {
    user: User;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    isSubscribed?: boolean;
    subscriptionEnds?: string | Date;
  }
}
