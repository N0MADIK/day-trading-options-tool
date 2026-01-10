import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { api, clearSession } from '@/lib/api';

/**
 * User type matching the backend User model
 */
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active?: boolean;
  created_at?: string;
}

/**
 * Session stored in localStorage
 */
interface AuthSession {
  access_token: string;
  token_type: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (email: string, password: string, fullName?: string) => Promise<{ error: Error | null }>;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const SESSION_KEY = 'auth_session';
const USER_KEY = 'user';

function saveSession(session: AuthSession): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function getStoredSession(): AuthSession | null {
  const session = localStorage.getItem(SESSION_KEY);
  if (!session) return null;
  try {
    return JSON.parse(session);
  } catch {
    return null;
  }
}

function saveUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getStoredUser(): User | null {
  const user = localStorage.getItem(USER_KEY);
  if (!user) return null;
  try {
    return JSON.parse(user);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    const initializeAuth = async () => {
      const storedSession = getStoredSession();
      const storedUser = getStoredUser();

      if (storedSession && storedUser) {
        // Validate the session by fetching current user
        try {
          const currentUser = await api.get<User>('/auth/me');
          setUser(currentUser);
          saveUser(currentUser);
        } catch {
          // Token is invalid, clear session
          clearSession();
          setUser(null);
        }
      }

      setLoading(false);
    };

    initializeAuth();
  }, []);

  const signUp = async (email: string, password: string, fullName?: string) => {
    try {
      // Register the user
      const registerPayload: { email: string; password: string; full_name?: string } = {
        email,
        password,
      };
      if (fullName) {
        registerPayload.full_name = fullName;
      }

      await api.post('/auth/register', registerPayload, { skipAuth: true });

      // Auto-login after registration
      const loginResponse = await api.post<{ access_token: string; token_type: string }>(
        '/auth/login',
        new URLSearchParams({ username: email, password }).toString(),
        {
          skipAuth: true,
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
      );

      const session: AuthSession = {
        access_token: loginResponse.access_token,
        token_type: loginResponse.token_type,
      };
      saveSession(session);

      // Fetch user details
      const currentUser = await api.get<User>('/auth/me');
      setUser(currentUser);
      saveUser(currentUser);

      return { error: null };
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Registration failed');
      return { error };
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      // OAuth2 password flow expects form-urlencoded data
      const loginResponse = await api.post<{ access_token: string; token_type: string }>(
        '/auth/login',
        new URLSearchParams({ username: email, password }).toString(),
        {
          skipAuth: true,
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
      );

      const session: AuthSession = {
        access_token: loginResponse.access_token,
        token_type: loginResponse.token_type,
      };
      saveSession(session);

      // Fetch user details
      const currentUser = await api.get<User>('/auth/me');
      setUser(currentUser);
      saveUser(currentUser);

      return { error: null };
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Invalid login credentials');
      return { error };
    }
  };

  const signOut = async () => {
    clearSession();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
