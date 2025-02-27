"use client";

import { createContext, useContext, useState, useEffect } from "react";
import { useSession } from "next-auth/react";

const AuthContext = createContext({
  isAuthenticated: false,
  isSubscribed: false,
  loading: true,
});

export function AuthProvider({ children }) {
  const { data: session, status } = useSession();
  const [isSubscribed, setIsSubscribed] = useState(false);
  
  useEffect(() => {
    if (session?.user) {
      // Check if user has an active subscription
      const subscriptionEnds = session.user.subscriptionEnds 
        ? new Date(session.user.subscriptionEnds) 
        : null;
        
      const isActive = subscriptionEnds && subscriptionEnds > new Date();
      setIsSubscribed(isActive);
    } else {
      setIsSubscribed(false);
    }
  }, [session]);

  const value = {
    isAuthenticated: !!session,
    isSubscribed,
    loading: status === "loading",
    user: session?.user || null,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
