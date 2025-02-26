"use client";

import { createContext, useContext } from "react";
import { useSession } from "next-auth/react";

const AuthContext = createContext({});

export function AuthProvider({ children }) {
  const { data: session, status } = useSession();
  const loading = status === "loading";
  const isAuthenticated = !!session?.user;
  const isSubscribed = session?.user?.isSubscribed || false;

  return (
    <AuthContext.Provider
      value={{ session, loading, isAuthenticated, isSubscribed }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
