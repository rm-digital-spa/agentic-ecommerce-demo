"use client";

import { createContext, useCallback, useContext, useState } from "react";

interface AuthContextValue {
  isAuthenticated: boolean;
  username: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
  initialUsername,
}: {
  children: React.ReactNode;
  initialUsername: string | null;
}) {
  const [username, setUsername] = useState<string | null>(initialUsername);

  const login = useCallback(async (username: string, password: string) => {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) return false;
    const data: { username: string } = await response.json();
    setUsername(data.username);
    return true;
  }, []);

  const logout = useCallback(async () => {
    await fetch("/api/logout", { method: "POST" });
    setUsername(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ isAuthenticated: !!username, username, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
