"use client";

import { SessionProvider } from "next-auth/react";
import { AuthProvider } from "@/contexts/AuthContext";
import { BaseComponentProps } from "@/types";

interface ProvidersProps extends BaseComponentProps {}

export default function Providers({ children }: ProvidersProps) {
  return (
    <SessionProvider>
      <AuthProvider>
        {children}
      </AuthProvider>
    </SessionProvider>
  );
}
