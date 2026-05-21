import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";

import { fetchMe } from "./api";
import type { User } from "./types";

const STORAGE_KEY = "drivesight.userId";

type AuthState = {
  user: User | null;
  loading: boolean;
  login: (userId: string) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const id = localStorage.getItem(STORAGE_KEY);
    if (!id) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(async (userId: string) => {
    localStorage.setItem(STORAGE_KEY, userId);
    const me = await fetchMe();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

export function getStoredUserId(): string | null {
  return localStorage.getItem(STORAGE_KEY);
}
