import NextAuth from "next-auth";
import { authOptions } from "./auth-options";

console.log("NextAuth route initializing with subscription support");

// Export handler function
const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
