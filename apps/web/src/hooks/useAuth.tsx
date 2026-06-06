'use client';

import type { UserPublic } from '@kairox/shared';
import { useRouter } from 'next/navigation';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { authApi } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';

interface AuthContextValue {
  user: UserPublic | null;
  loading: boolean;
  login: (username: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (data: {
    username: string;
    email: string;
    password: string;
    inviteCode: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshSession = useCallback(async () => {
    const { user: current } = await authApi.me();
    setUser(current);
  }, []);

  useEffect(() => {
    authApi
      .me()
      .then(({ user: current }) => setUser(current))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(
    async (username: string, password: string, rememberMe = false) => {
      const { user: loggedIn } = await authApi.login({ username, password, rememberMe });
      setUser(loggedIn);
      router.push('/home');
    },
    [router],
  );

  const register = useCallback(
    async (data: { username: string; email: string; password: string; inviteCode: string }) => {
      const { user: registered } = await authApi.register(data);
      setUser(registered);
      router.push('/home');
    },
    [router],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (e) {
      if (!(e instanceof ApiError)) throw e;
    }
    setUser(null);
    router.push('/login');
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshSession }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
